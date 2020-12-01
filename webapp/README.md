### Run the application (Unix)
    ./run.sh

# Running the application on Windows

1.	Download Python 3.7. Can download through Anaconda suite
2.	Clone the GitHub repository. 
3.	Create an environment & install relevant packages. For demonstration it is called here "myenv".

        conda create -n myenv python=3.7
        conda update conda
        conda install pip
        conda update pip

4.	Install the required python modules
        activate myenv
        d "C:\Users\...\CROP\"
        conda install --file requirements.txt

5.	Add the CROP folder to the PYTHONPATH
In windows what you can do is type environmental variables in your startup. It should point you to “edit the system environmental variables”. Click on advanced from the top menu and environment variables. Within the system variables, click on “NEW” and name it “PYTHONPATH”. As path enter the path to the project, e.g. C:\Users\...\CROP\
6.	Run the activate.bat file
        call "C:\Users\...\anaconda3\Scripts\activate.bat" activate cropdb
        cd "C:\Users\...\Documents\GitHub\CROP\webapp"
        flask run --host=0.0.0.0 --port 5000

7.	Download Visual Studio Code

8.  Open the CROP folder

9.  Load the environment variables 

        call "C:\Users\...\Scripts\activate.bat" activate myenv
        cd .secrets
        load_environment_variables.bat
        cd "C:\Users\...\CROP\webapp"
        flask run --host=0.0.0.0 --port 5000

