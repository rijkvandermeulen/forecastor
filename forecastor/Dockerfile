FROM python:3.9-buster

# Update the package list
RUN apt-get update \
    # Install SQLite3
    && apt-get install -y \
       sqlite3 \
    # Clean up the apt cache to reduce image size
    && rm -rf /var/lib/apt/lists/*

COPY ./forecastor/requirements.txt /tmp
RUN pip install -r /tmp/requirements.txt

WORKDIR /app
#COPY ./app /app
COPY ./forecastor/app /app

EXPOSE 8000

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]