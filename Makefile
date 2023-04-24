LOCAL_PORT=8081
IMAGE_NAME=fastapi
CONTAINER_NAME=fastapi

serve:
	cd app;gunicorn -k uvicorn.workers.UvicornWorker main:app

build:
	docker build -t $(IMAGE_NAME) .

run:
	docker run -d -p $(LOCAL_PORT):80 -it -v "$(CURDIR)/app:/app" --name $(CONTAINER_NAME) $(IMAGE_NAME)

restart:
	docker restart $(CONTAINER_NAME)
