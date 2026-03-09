FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY url_shortener_service /app/url_shortener_service
COPY url_shortener_service_run.py /app/url_shortener_service_run.py

EXPOSE 8000

CMD ["python", "url_shortener_service_run.py"]
