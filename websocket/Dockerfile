FROM python:3.8-slim

RUN apt-get update 

COPY ./ /app
WORKDIR /app
RUN pip install -r requirements.txt

CMD ["python3", "server.py"]