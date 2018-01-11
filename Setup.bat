@echo off
setlocal enableextensions

echo The following Python packages will be installed: uptime, pypiwin32, pyyaml
pause

pip install uptime
pip install pypiwin32
pip install pyyaml

if NOT %ERRORLEVEL% EQU 0 goto: NotAdmin

goto :Startup 

:NotAdmin
echo Installation failed. Please run this script as administrator.
pause
exit

:StartupInvalid
echo.
echo Invalid entry. Enter Y or N.

:Startup
echo.
Set /P _start=Start IdleMiner on Windows startup? [Y/N] || Set _start=NOTHING
if /I "%_start%" EQU "Y" goto :Add_Startup
if /I "%_start%" EQU "N" goto :End
if "%_start%" EQU "NOTHING" goto :StartupInvalid

:Add_Startup
cd /d "%~dp0"
move .\IdleMiner.lnk "%AppData%\Microsoft\Windows\Start Menu\Programs\Startup" > nul
if NOT %ERRORLEVEL% EQU 0 goto: NotAdmin

echo Shortcut to IdleMiner.bat added to startup folder.

:End
echo.
echo Installation finished.
pause