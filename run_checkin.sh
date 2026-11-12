#!/bin/bash
# ==========================================
# MISA Auto Checkin - macOS/Linux Script
# ==========================================

# Chuyển đến thư mục chứa script
cd "$(dirname "$0")"

echo "============================================"
echo "   MISA Auto Checkin Tool"
echo "============================================"
echo ""

# Chạy script Python (tự động dùng python3)
if command -v python3 &> /dev/null; then
    python3 auto_checkin.py
elif command -v python &> /dev/null; then
    python auto_checkin.py
else
    echo "Lỗi: Không tìm thấy Python. Vui lòng cài đặt Python 3."
    exit 1
fi

echo ""
echo "Hoàn thành!"
