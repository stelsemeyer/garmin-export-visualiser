FROM python:3.8-slim

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip install --trusted-host pypi.python.org -r requirements.txt

COPY app.py app.py

EXPOSE 8050

CMD exec gunicorn --bind 0.0.0.0:8050 --log-level info --workers 1 --threads 1 --timeout 0 app:server
