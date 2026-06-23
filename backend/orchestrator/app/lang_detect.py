"""Language detection + Tunisian-Derja translation helpers.

Moufida classifies every inbound message into one of three buckets -- French,
Tunisian Arabic (Derja), or other. Derja is detected as generic Arabic by
``langdetect`` and then routed through a small Ollama-backed translator so the
rest of the pipeline can reason in French.
"""
from __future__ import annotations

from typing import Literal

import httpx
from langdetect import DetectorFactory, detect
from langdetect.lang_detect_exception import LangDetectException

# Deterministic results -- langdetect is seeded from a random source otherwise.
DetectorFactory.seed = 0

Lang = Literal["fr", "ar-TN", "other"]

OLLAMA_TRANSLATE_MODEL = "llama3.1"
_TRANSLATE_TIMEOUT = 60.0

# Five-shot Derja -> French priming pairs.
_DERJA_SHOTS: list[tuple[str, str]] = [
    ("عندي مشروع جديد نحب نبدا بيه", "J'ai un nouveau projet que je veux lancer."),
    ("الفلوس متاع المشروع وفاو", "Le budget du projet est épuisé."),
    ("ما عندناش حرفاء يخلصو", "Nous n'avons pas de clients payants."),
    ("نحب نعمل دراسة سوق", "Je veux faire une étude de marché."),
    ("الفريق متاعنا فيه خمسة نفرات", "Notre équipe compte cinq personnes."),
]


def detect_language(text: str) -> Lang:
    """Classify ``text`` as ``fr``, ``ar-TN`` (any Arabic), or ``other``.

    Falls back to ``fr`` when langdetect cannot decide (empty/garbage input).
    """
    try:
        code = detect(text)
    except LangDetectException:
        return "fr"
    if code == "ar":
        return "ar-TN"
    if code == "fr":
        return "fr"
    return "other"


def _build_translation_prompt(text: str) -> str:
    shots = "\n".join(
        f"Derja: {derja}\nFrançais: {fr}" for derja, fr in _DERJA_SHOTS
    )
    return (
        "Tu es un traducteur du dialecte tunisien (Derja) vers le français. "
        "Traduis fidèlement, sans rien ajouter. Réponds uniquement par la traduction française.\n\n"
        f"{shots}\n"
        f"Derja: {text}\nFrançais:"
    )


async def translate_derja_to_french(text: str, ollama_base_url: str) -> str:
    """Translate Tunisian Derja to French via Llama 3.1 on Ollama.

    Only meaningful for ``ar-TN`` input. Persisting the original alongside the
    translation is the caller's responsibility.
    """
    prompt = _build_translation_prompt(text)
    async with httpx.AsyncClient(timeout=_TRANSLATE_TIMEOUT) as client:
        resp = await client.post(
            f"{ollama_base_url}/api/generate",
            json={"model": OLLAMA_TRANSLATE_MODEL, "prompt": prompt, "stream": False},
        )
        resp.raise_for_status()
        return resp.json().get("response", "").strip()
