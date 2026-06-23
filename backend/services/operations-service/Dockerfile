FROM python:3.12-slim
WORKDIR /srv
# Shared scoring library
COPY backend/scoring-engine /srv/affinitree
RUN pip install --no-cache-dir ./affinitree fastapi "uvicorn[standard]" httpx
COPY backend/services/operations-service/app /srv/app
ENV PYTHONUNBUFFERED=1
EXPOSE 8109
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8109"]
