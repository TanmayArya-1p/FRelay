FROM ubuntu:latest
FROM python:3.9.6
EXPOSE 3000
WORKDIR /code
RUN pip install --upgrade pip
COPY ./requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt
COPY ./api /code/api
CMD cd api && fastapi run server.py --port 3000