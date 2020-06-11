.PHONY: bbuild bclean bpush build run clean push pbuild prun pclean ppush dbuild drun dclean dpush

# BASE IMAGE BUILD
bbuild:
	docker build -f utils/Dockerfile.cropbase -t turingcropapp/webappbase:latest .
bclean:
	docker image rm turingcropapp/webappbase:latest
bpush:
	docker push turingcropapp/webappbase:latest

# TEST BUILD 
build:
	git submodule sync
	git submodule update --init --recursive --remote
	docker build -f Dockerfile -t turingcropapp/webapp:cropapp .
run:
	docker run -p 5000:5000 turingcropapp/webapp:latest
clean:
	docker image rm turingcropapp/webapp:latest
push:
	docker push turingcropapp/webapp:latest

# DEVELOPMENT BUILD
pbuild:
	git submodule sync
	git submodule update --init --recursive --remote
	docker build . -f Dockerfile -t turingcropapp/webapp:cropapp
prun:
	docker run -p 5000:5000 turingcropapp/webapp:cropapp
pclean:
	docker image rm turingcropapp/webapp:cropapp
ppush:
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