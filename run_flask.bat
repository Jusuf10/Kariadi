@echo off
cd C:\Users\acer\Desktop\Kariadi
py -m venv env
CALL env\Scripts\activate
set FLASK_APP=main.py
set FLASK_ENV=development
start flask run --host=0.0.0.0
timeout /t 5 /nobreak
start http://127.0.0.1:5000/
