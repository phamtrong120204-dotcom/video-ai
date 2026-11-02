@echo off
chcp 65001 > nul
cd /d "%~dp0"

echo =====================================================================
echo   DUNG UNG DUNG DARK MYTH STICKMAN AUTO-STUDIO
echo =====================================================================
echo.
echo Dang tim va dong cac tien trinh Python chay tu thu muc du an...

powershell -NoProfile -Command "Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like '*app\main.py*' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }" >nul 2>nul

echo [v] Da gui tin hieu dung toi cac dich vu Studio va Bot.
echo.
pause
