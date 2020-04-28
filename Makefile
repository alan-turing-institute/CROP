.PHONY: build run clean push

build:
	# checking out submodules
	#git submodule update --remote

	git submodule sync
	git submodule update --init --recursive --remote

	docker build . -f Dockerfile -t turingcropapp/webapp:latest
run:
	docker run -p 5005:5005 turingcropapp/webapp:latest

clean:
	docker image rm turingcropapp/webapp:latest

push:
	docker push turingcropapp/webapp:latest