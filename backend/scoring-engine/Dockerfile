FROM python:3.12-slim
WORKDIR /srv
COPY backend/scoring-engine /srv/scoring-engine
RUN pip install --no-cache-dir \
    ./scoring-engine \
    "fastapi>=0.111" \
    "uvicorn[standard]>=0.30" \
    httpx
COPY backend/scoring-engine/app /srv/app
ENV PYTHONUNBUFFERED=1
EXPOSE 8200
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8200"]
