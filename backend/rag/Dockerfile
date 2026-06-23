FROM python:3.12-slim
WORKDIR /srv
RUN pip install --no-cache-dir fastapi "uvicorn[standard]" httpx qdrant-client rank-bm25
COPY backend/rag/app /srv/app
ENV PYTHONUNBUFFERED=1
EXPOSE 8300
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8300"]
