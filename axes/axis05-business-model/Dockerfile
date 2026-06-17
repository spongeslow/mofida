FROM python:3.12-slim
WORKDIR /srv
# Shared scoring library
COPY affinitree /srv/affinitree
RUN pip install --no-cache-dir ./affinitree fastapi "uvicorn[standard]" httpx
COPY axes/axis05-business-model/app /srv/app
ENV PYTHONUNBUFFERED=1
EXPOSE 8105
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8105"]
