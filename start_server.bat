@echo off
echo Spoustim publikacni server...
start /B pythonw "%~dp0server.py"
echo Server bezi na pozadi na portu 5555.
echo Pro zastaveni otevri Spravce uloh a ukonci pythonw.exe
pause
