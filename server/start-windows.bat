@echo off
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe py -3 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 goto failed
.venv\Scripts\python.exe run-local.py
pause
exit /b
:failed
echo Installation failed. Check Python 3.12+ and Internet connection.
pause
