FROM python:3.7-slim

WORKDIR /code
COPY requirements.txt .
RUN pip3 install -r requirements.txt
COPY . .
CMD gunicorn shop.wsgi:application --bind 0.0.0.0:8000


