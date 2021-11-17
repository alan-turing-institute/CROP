title local server from conda
//conda create --name crop python=3.8
//pip3 install -r./requirements.txt
echo runing the webapp
call "C:\ProgramData\Anaconda3\Scripts\activate.bat" activate crop
cd "C:\Users\froumpani\OneDrive - The Alan Turing Institute\Turing\1.Projects\2.UrbanAgriculture\CROP\webapp"
set FLASK_ENV=development
flask run --host=0.0.0.0 --port 5000