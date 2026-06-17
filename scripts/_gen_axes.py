#!/usr/bin/env python3
"""One-shot scaffolder for the ten axis FastAPI services.

Run from the repo root: ``python scripts/_gen_axes.py``. Idempotent — it
overwrites the generated stub files but never touches hand-written logic added
later (it only writes main.py, Dockerfile, pyproject.toml and __init__.py).
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# (number, slug, port, affinitree_score_or_None, has_metric_update, service_dir)
AXES = [
    (1, "ideation", 8101, None, True, "ideation-service"),
    (2, "market", 8102, "market", True, "market-intelligence-service"),
    (3, "product", 8103, "commercial_offer", False, "product-offering-service"),
    (4, "brand", 8104, "innovation", False, "brand-innovation-service"),
    (5, "business-model", 8105, "scalability", True, "business-model-service"),
    (6, "legal", 8106, "green", True, "legal-compliance-service"),
    (7, "marketing", 8107, None, False, "marketing-service"),
    (8, "sales", 8108, None, False, "sales-service"),
    (9, "operations", 8109, "scalability", True, "operations-service"),
    (10, "gtm", 8110, None, True, "go-to-market-service"),
]

DOCKERFILE = """FROM python:3.12-slim
WORKDIR /srv
# Shared scoring library
COPY scoring-engine /srv/affinitree
RUN pip install --no-cache-dir ./affinitree fastapi "uvicorn[standard]" httpx
COPY services/{dir}/app /srv/app
ENV PYTHONUNBUFFERED=1
EXPOSE {port}
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "{port}"]
"""

PYPROJECT = """[project]
name = "moufida-{dir}"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = ["fastapi", "uvicorn[standard]", "httpx", "affinitree"]
"""


def main_py(num, slug, port, score, has_metric) -> str:
    title = slug.replace("-", " ").title()
    lines = [
        '"""Axis %02d -- %s. FastAPI microservice (port %d)."""' % (num, title, port),
        "from __future__ import annotations",
        "",
        "from fastapi import FastAPI",
        "from pydantic import BaseModel",
    ]
    if score:
        lines += [
            "from affinitree import StartupProfile, detect, score as affinitree_score",
        ]
    lines += [
        "",
        f'AXIS = {num}',
        f'SLUG = "{slug}"',
        f'app = FastAPI(title="Moufida Axis {num:02d} - {title}")',
        "",
        "",
        "class DiagnoseRequest(BaseModel):",
        "    profile: dict",
        "",
        "",
        '@app.get("/health")',
        "def health():",
        '    return {"status": "ok", "axis": AXIS, "slug": SLUG}',
        "",
        "",
        '@app.post("/execute")',
        "def execute(payload: dict | None = None):",
        '    """STATE_NEW guided step (Phase 4). Stubbed for now."""',
        '    return {"axis": AXIS, "mode": "execute", "status": "not_implemented"}',
        "",
    ]
    # diagnose
    if score:
        lines += [
            "",
            '@app.post("/diagnose")',
            "def diagnose(req: DiagnoseRequest):",
            f'    """STATE_EXISTING: compute the {score} score via Affinitree."""',
            "    profile = StartupProfile(**req.profile)",
            f'    result = affinitree_score(profile, "{score}")',
            "    anomalies = [a.to_dict() for a in detect(profile)]",
            "    return {",
            '        "axis": AXIS,',
            f'        "score_name": "{score}",',
            '        "score": result.score,',
            '        "explanation": result.explanation_tree(),',
            '        "missing_fields": result.missing_fields,',
            '        "anomalies": anomalies,',
            "    }",
            "",
        ]
    else:
        lines += [
            "",
            '@app.post("/diagnose")',
            "def diagnose(req: DiagnoseRequest):",
            '    """STATE_EXISTING diagnostic stub (filled in Phase 2)."""',
            f'    return {{"axis": AXIS, "mode": "diagnose", "status": "not_implemented"}}',
            "",
        ]
    if has_metric:
        lines += [
            "",
            '@app.post("/metric_update")',
            "def metric_update(payload: dict):",
            '    """Receive a Go-daemon signal routed by the orchestrator (Phase 5)."""',
            '    return {"axis": AXIS, "received": payload, "status": "not_implemented"}',
            "",
        ]
    return "\n".join(lines) + "\n"


def write(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


for num, slug, port, score, has_metric, service_dir in AXES:
    base = ROOT / "services" / service_dir
    write(base / "app" / "__init__.py", "")
    write(base / "app" / "main.py", main_py(num, slug, port, score, has_metric))
    write(base / "Dockerfile", DOCKERFILE.format(dir=service_dir, port=port))
    write(base / "pyproject.toml", PYPROJECT.format(dir=service_dir))
    print("generated", d)

print("done")
