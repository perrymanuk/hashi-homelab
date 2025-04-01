FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY sync_secrets.py .

ENTRYPOINT ["python", "sync_secrets.py"]
