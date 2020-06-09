.PHONY: build run clean push dbuild drun dclean dpush

# PRODUCTION BUILD
build:
	git submodule sync
	git submodule update --init --recursive --remote
	docker build . -f Dockerfile -t turingcropapp/webapp:cropapp
run:
	docker run -p 5005:5005 turingcropapp/webapp:cropapp
clean:
	docker image rm turingcropapp/webapp:cropapp
push:
	docker push turingcropapp/webapp:cropapp
	
# DEVELOPMENT BUILD
dbuild:
	git submodule sync
	git submodule update --init --recursive --remote
	docker build . -f Dockerfile -t turingcropapp/webapp:cropapptest
drun:
	docker run -p 5000:5000 turingcropapp/webapp:cropapptest
dclean:
	docker image rm turingcropapp/webapp:cropapptest
dpush:
	docker push turingcropapp/webapp:cropapptest