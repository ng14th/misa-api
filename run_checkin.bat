@echo off
REM ==========================================
REM MISA Auto Checkin - Windows Batch Script
REM ==========================================

REM Chuyển đến thư mục chứa script
cd /d "%~dp0"

echo ============================================
echo   MISA Auto Checkin Tool
echo ============================================
echo.

REM Chạy script Python
python auto_checkin.py

REM Tạm dừng để xem kết quả (bỏ dòng này nếu chạy tự động)
echo.
echo Nhan phim bat ky de dong cua so...
pause
