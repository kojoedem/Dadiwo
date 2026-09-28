FROM python:3.11-slim

WORKDIR /app

COPY labs/bitroot/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY labs/bitroot /app/labs/bitroot

EXPOSE 8091

ENV PYTHONPATH=/app/labs/bitroot/app
ENV DIFFICULTY_LEVEL=beginner
ENV ENVIRONMENT_PURPOSE=cybersecurity

CMD ["python3", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8091", "--app-dir", "/app/labs/bitroot/app", "--ssl-keyfile", "/app/labs/bitroot/certs/bitroot.key", "--ssl-certfile", "/app/labs/bitroot/certs/bitroot.crt"]
