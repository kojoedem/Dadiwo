FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

EXPOSE 8090

ENV PYTHONPATH=/app/app

CMD ["uvicorn", "main:app", "--host", "::", "--port", "8090", "--app-dir", "app"]
