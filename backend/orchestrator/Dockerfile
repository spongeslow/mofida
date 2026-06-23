FROM python:3.12-slim
WORKDIR /srv
COPY backend/scoring-engine /srv/affinitree
COPY moufida-tools /srv/moufida-tools
RUN pip install --no-cache-dir \
    ./affinitree \
    ./moufida-tools \
    fastapi \
    "uvicorn[standard]" \
    httpx \
    redis \
    "psycopg[binary]" \
    asyncpg \
    langdetect \
    langgraph \
    "pypdf>=4.0" \
    "python-multipart>=0.0.9" \
    "composio>=0.7"
COPY backend/orchestrator/app /srv/app
ENV PYTHONUNBUFFERED=1
EXPOSE 8001
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
