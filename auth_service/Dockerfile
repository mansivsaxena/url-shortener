FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY auth_service /app/auth_service
COPY auth_service_run.py /app/auth_service_run.py

EXPOSE 8001
COPY . .
ENV PYTHONPATH=/app

CMD ["python", "auth_service_run.py"]
