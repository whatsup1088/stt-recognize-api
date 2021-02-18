FROM tiangolo/uvicorn-gunicorn-fastapi:python3.7

COPY ./app /app
WORKDIR /app
RUN pip install -r requirements.txt

USER root
RUN apt-get update \
 && apt install -y ffmpeg
