FROM python:3.12-slim
WORKDIR /srv
# Shared scoring library
COPY scoring-engine /srv/affinitree
RUN pip install --no-cache-dir ./affinitree fastapi "uvicorn[standard]" httpx
COPY services/brand-innovation-service/app /srv/app
ENV PYTHONUNBUFFERED=1
EXPOSE 8104
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8104"]
