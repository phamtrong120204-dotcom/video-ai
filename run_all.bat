@echo off
chcp 65001 > nul
cd /d "%~dp0"

echo =====================================================================
echo   KHOI DONG CẢ GRADIO LOCAL STUDIO VA TELEGRAM BOT
echo =====================================================================
echo.

if exist ".venv\Scripts\python.exe" goto RUN_VENV

echo [!] Khong tim thay .venv\Scripts\python.exe.
echo     Vui long chay setup_environment.bat truoc.
echo.
pause
exit /b 1

:RUN_VENV
".venv\Scripts\python.exe" app\main.py --all
if %errorlevel% neq 0 (
    echo.
    echo [!] Ung dung da dung voi ma loi %errorlevel%.
)
pause
