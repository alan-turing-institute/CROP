.PHONY: build clean push

build:
	docker build . -f Dockerfile -t turingcropapp/functions:local-build
clean:
	docker image rm turingcropapp/functions:local-build
push:
	docker push turingcropapp/functions:local-build
