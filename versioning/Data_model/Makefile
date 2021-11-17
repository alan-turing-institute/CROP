infrastructure:
	snap install docker
	docker pull turingcropapp/static-models:1
	sudo apt-get install subversion
container:
	docker pull turingcropapp/static-models:1
code:
	svn checkout https://github.com/alan-turing-institute/CROP/branches/output-to-database/versioning/Data_model/models/static
prediction:
	docker run -dt -v $(pwd)/static/code:/models turingcropapp/static-models:1
help: 
	$(info infrastructure : Set up docker and subversion)
	$(info container : Get model container)
	$(info code : Get model code)
	$(info prediction : )