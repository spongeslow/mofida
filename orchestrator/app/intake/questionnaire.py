"""Adaptive, branch-aware intake questionnaire.

The questionnaire is data-driven (``branches.json``) and fully stateless: the
client replays the full ``answers`` map (keyed by question id) on every turn and
the server walks the branch graph to find the next unanswered node. Answers are
finally folded into a nested ``profile_patch`` via dotted ``field`` paths.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

_BRANCHES_PATH = Path(__file__).parent / "branches.json"


class AdaptiveQuestionnaire:
    def __init__(self, language: str):
        self.language = language
        self.is_arabic = language.lower().startswith("ar")
        nodes = json.loads(_BRANCHES_PATH.read_text(encoding="utf-8"))
        self._nodes: dict[str, dict] = {n["id"]: n for n in nodes}
        # First declared node is the entry point.
        self._start_id: str = nodes[0]["id"]

    # ----- public API -----------------------------------------------------

    def start(self) -> dict:
        """Return the first question, translated to ``language``."""
        return self._translate(self._nodes[self._start_id])

    def next(self, current_id: str, answer: Any) -> Optional[dict]:
        """Resolve the next question given an answer to ``current_id``.

        Branches are evaluated first (value match), falling back to the node's
        default ``next``. Returns ``None`` when the flow is complete or the id
        is unknown.
        """
        node = self._nodes.get(current_id)
        if node is None:
            return None
        target_id = self._resolve_next_id(node, answer)
        if target_id is None:
            return None
        target = self._nodes.get(target_id)
        return self._translate(target) if target else None

    def resume(self, answers: dict) -> Optional[dict]:
        """Replay ``answers`` from the start and return the next unanswered
        question (translated), or ``None`` when the flow is complete.

        This is what the stateless endpoints use: there is no server-side
        session, only the answers the client has gathered so far.
        """
        node = self._nodes[self._start_id]
        while node is not None:
            if node["id"] not in answers:
                return self._translate(node)
            target_id = self._resolve_next_id(node, answers[node["id"]])
            node = self._nodes.get(target_id) if target_id else None
        return None

    def merge_to_profile(self, answers: dict) -> dict:
        """Fold ``{question_id: answer}`` into a nested StartupProfile patch.

        Answers whose id is unknown are ignored; values are coerced to match the
        node's declared ``type``.
        """
        patch: dict = {}
        for qid, raw in answers.items():
            node = self._nodes.get(qid)
            if node is None or raw is None:
                continue
            value = self._coerce(node["type"], raw)
            self._set_dotted(patch, node["field"], value)
        return patch

    # ----- internals ------------------------------------------------------

    def _resolve_next_id(self, node: dict, answer: Any) -> Optional[str]:
        answer_norm = self._norm(answer)
        for branch in node.get("branches") or []:
            if self._norm(branch["if_value"]) == answer_norm:
                return branch["goto"]
        return node.get("next")

    def _translate(self, node: dict) -> dict:
        return {
            "id": node["id"],
            "field": node["field"],
            "type": node["type"],
            "choices": node.get("choices"),
            "question": node["question_ar"] if self.is_arabic else node["question_fr"],
            "lang": "ar" if self.is_arabic else "fr",
        }

    @staticmethod
    def _norm(value: Any) -> str:
        """Case/space-insensitive string form used for branch matching."""
        return str(value).strip().lower()

    @staticmethod
    def _coerce(qtype: str, raw: Any) -> Any:
        if qtype == "number":
            try:
                num = float(raw)
                return int(num) if num.is_integer() else num
            except (TypeError, ValueError):
                return raw
        if qtype == "boolean":
            if isinstance(raw, bool):
                return raw
            return str(raw).strip().lower() in {"true", "1", "yes", "oui", "نعم"}
        return raw

    @staticmethod
    def _set_dotted(target: dict, dotted_path: str, value: Any) -> None:
        parts = dotted_path.split(".")
        for part in parts[:-1]:
            target = target.setdefault(part, {})
        target[parts[-1]] = value
