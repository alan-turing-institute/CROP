.PHONY: build clean push 

build:
	docker build . -f Dockerfile -t turingcropapp/webapp:funcapp
clean:
	docker image rm turingcropapp/webapp:funcapp
push:
	docker push turingcropapp/webapp:funcapp