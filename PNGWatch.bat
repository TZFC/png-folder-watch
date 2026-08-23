@echo off
setlocal
cd /d "%~dp0"

:: Check if self-contained runtime exists
if not exist "runtime\python.exe" (
    echo ==========================================================
    echo   First time launch: Setting up PNG Folder Watch...
    echo   Downloading lightweight self-contained runtime (~11MB)
    echo ==========================================================
    powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0setup_runtime.ps1"
    if errorlevel 1 (
        echo.
        echo Setup encountered an issue. Press any key to exit.
        pause
        exit /b 1
    )
)

:: Launch PNG Folder Watch in background (pythonw prevents terminal window from staying open)
if exist "%~dp0runtime\pythonw.exe" (
    start "" "%~dp0runtime\pythonw.exe" "%~dp0src\main.py" %*
) else if exist "%~dp0runtime\python.exe" (
    start "" "%~dp0runtime\python.exe" "%~dp0src\main.py" %*
) else (
    start "" python "%~dp0src\main.py" %*
)

exit /b 0
