.PHONY: bbuild bclean bpush build run clean push dbuild drun dclean dpush

# BASE IMAGE BUILD
bbuild:
	docker build -f utils/Dockerfile.cropbase -t turingcropapp/webappbase:latest .
bclean:
	docker image rm turingcropapp/webappbase:latest
bpush:
	docker push turingcropapp/webappbase:latest

# PRODUCTION BUILD
build:
	git submodule sync
	git submodule update --init --recursive --remote
	docker build . -f Dockerfile -t turingcropapp/webapp:cropapp
run:
	docker run -p 5000:5000 turingcropapp/webapp:cropapp
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