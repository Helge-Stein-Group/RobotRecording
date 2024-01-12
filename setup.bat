@echo off
cd %~dp0
python -m venv .venv
call .venv\Scripts\activate
pip install -r requirements.txt

cd %USERPROFILE%\Desktop
echo cd %~dp0 >> RobotRecording.bat
echo call .venv\Scripts\activate >> RobotRecording.bat
echo set PYTHONPATH=%PYTHONPATH%;%~dp0 >> RobotRecording.bat
echo cd src >> RobotRecording.bat
echo start cmd /k python main.py >> RobotRecording.bat
echo start firefox http://localhost:8050 >> RobotRecording.bat