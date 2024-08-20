FROM python:3.9-buster

COPY requirements.txt /tmp
RUN pip install -r /tmp/requirements.txt

WORKDIR /app
COPY ./app /app

EXPOSE 8000

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]