@echo off
setlocal
cd /d "%~dp0"
where node >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo Node.js is required but not installed. Please install Node.js.
    pause
    exit
)
:: Start in the background inside LocalGitRepo
start "" /B node server.js

:: Wait a moment for server to start
timeout /t 1 /nobreak > nul

start http://localhost:8081/
endlocal
