FROM python:3.12-slim
WORKDIR /srv
COPY scoring-engine /srv/affinitree
RUN pip install --no-cache-dir \
    ./affinitree \
    fastapi \
    "uvicorn[standard]" \
    httpx \
    redis \
    "psycopg[binary]" \
    asyncpg \
    langdetect \
    langgraph
COPY orchestrator/app /srv/app
ENV PYTHONUNBUFFERED=1
EXPOSE 8001
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
