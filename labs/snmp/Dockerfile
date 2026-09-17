FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/

EXPOSE 8087 16161/udp

CMD ["python3", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8087", "--app-dir", "app"]
