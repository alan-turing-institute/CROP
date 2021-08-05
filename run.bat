title local server from conda
echo runing the webapp
call "C:\ProgramData\Anaconda3\Scripts\activate.bat" activate crop
cd "C:\Users\froumpani\OneDrive - The Alan Turing Institute\Turing\1.Projects\2.UrbanAgriculture\CROP\webapp"
set FLASK_ENV=development
flask run --host=0.0.0.0 --port 5000
