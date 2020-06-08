.PHONY: build run clean push dbuild drun dclean dpush

# PRODUCTION BUILD
build:
	git submodule sync
	git submodule update --init --recursive --remote
	docker build . -f Dockerfile -t turingcropapp/webapp:latest
run:
	docker run -p 5005:5005 turingcropapp/webapp:latest
clean:
	docker image rm turingcropapp/webapp:latest
push:
	docker push turingcropapp/webapp:latest
# DEVELOPMENT BUILD
dbuild:
	git submodule sync
	git submodule update --init --recursive --remote
	docker build . -f Dockerfile -t turingcropapp/webapp:dev
drun:
	docker run -p 5000:5000 turingcropapp/webapp:dev
dclean:
	docker image rm turingcropapp/webapp:dev
dpush:
	docker push turingcropapp/webapp:dev