@echo off
chcp 65001 > nul
cd /d "%~dp0"

echo =====================================================================
echo   THIET LAP MOI TRUONG DARK MYTH STICKMAN AUTO-STUDIO
echo =====================================================================
echo.

:: 1. Kiem tra Python
where python >nul 2>nul
if %errorlevel% neq 0 goto NO_PYTHON
goto HAS_PYTHON

:NO_PYTHON
echo [X] LOI: Khong tim thay lenh python trong he thong!
echo     Vui long cai dat Python 3.10 tro len tu https://python.org
echo     va nho tich chon Add Python to PATH.
echo.
pause
exit /b 1

:HAS_PYTHON
for /f "tokens=*" %%i in ('python -V 2^>^&1') do set PYTHON_VERSION=%%i
echo [*] Phat hien: %PYTHON_VERSION%

:: 2. Khoi tao .venv
if exist ".venv\Scripts\python.exe" goto VENV_OK
echo [*] Chua co moi truong ao .venv. Dang tao .venv moi...
python -m venv .venv
if %errorlevel% neq 0 goto VENV_FAIL
echo [v] Da tao thanh cong .venv!
goto VENV_OK

:VENV_FAIL
echo [X] LOI: Khong the tao moi truong ao .venv.
pause
exit /b 1

:VENV_OK
echo [v] Moi truong ao .venv da san sang.

:: 3. Cai dat thu vien
echo.
echo [*] Dang cai dat va kiem tra cac thu vien trong requirements.txt...
".venv\Scripts\python.exe" -m pip install --upgrade pip >nul 2>nul
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [!] Co canh bao khi cai dat requirements.
) else (
    echo [v] Cai dat thu vien hoan tat.
)

:: 4. Tao .env
if exist ".env" goto ENV_OK
if exist ".env.example" (
    echo [*] Dang tao tep .env tu .env.example...
    copy ".env.example" ".env" > nul
    echo [v] Da tao tep .env mac dinh.
)
:ENV_OK

:: 5. Chay kiem tra tong the
echo.
echo [*] Dang chay kiem tra he thong tong the...
echo.
".venv\Scripts\python.exe" scripts\preflight_check.py

echo.
echo =====================================================================
echo   CAI DAT HOAN TAT!
echo   Ban co the khoi chay ung dung bang cach nhap dup:
echo     - run_studio.bat : Mo giao dien Web Studio
echo     - run_bot.bat    : Khoi dong Telegram Bot
echo     - run_all.bat    : Chay ca hai dich vu
echo =====================================================================
echo.
pause
