@echo off
REM ==========================================
REM MISA Auto Checkin - Random Time Wrapper
REM ==========================================
REM Script nay se sleep random truoc khi chay checkin
REM Dung cho Task Scheduler de tranh bi phat hien pattern

REM Tham so: MIN_DELAY MAX_DELAY (tinh bang giay)
REM VD: random_checkin.bat 0 900  -> random 0-15 phut

setlocal enabledelayedexpansion

set MIN_DELAY=%1
set MAX_DELAY=%2

REM Mac dinh: 0-10 phut
if "%MIN_DELAY%"=="" set MIN_DELAY=0
if "%MAX_DELAY%"=="" set MAX_DELAY=600

REM Tinh delay ngau nhien (dung %RANDOM%)
set /a RANGE=%MAX_DELAY% - %MIN_DELAY% + 1
set /a RANDOM_DELAY=%RANDOM% %% !RANGE! + %MIN_DELAY%
set /a MINUTES=%RANDOM_DELAY% / 60
set /a SECONDS=%RANDOM_DELAY% %% 60

echo.
echo Se cham cong sau %MINUTES% phut %SECONDS% giay...
echo.

REM Sleep (dung timeout thay vi sleep)
timeout /t %RANDOM_DELAY% /nobreak >nul

REM Chuyen den thu muc chua script
cd /d "%~dp0"

REM Chay script Python
python auto_checkin.py

endlocal
