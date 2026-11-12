#!/bin/bash
# ==========================================
# MISA Auto Checkin - Random Time Wrapper
# ==========================================
# Script này sẽ sleep random trước khi chạy checkin
# Dùng cho cron để tránh bị phát hiện pattern

# Tham số: MIN_DELAY MAX_DELAY (tính bằng giây)
# VD: ./random_checkin.sh 0 900  → random 0-15 phút

MIN_DELAY=${1:-0}
MAX_DELAY=${2:-600}

# Tính delay ngẫu nhiên
RANDOM_DELAY=$((RANDOM % (MAX_DELAY - MIN_DELAY + 1) + MIN_DELAY))
MINUTES=$((RANDOM_DELAY / 60))
SECONDS=$((RANDOM_DELAY % 60))

echo "🕐 Sẽ chấm công sau ${MINUTES} phút ${SECONDS} giây..."
sleep $RANDOM_DELAY

# Chuyển đến thư mục chứa script
cd "$(dirname "$0")"

# Chạy script Python
if command -v python3 &> /dev/null; then
    python3 auto_checkin.py
elif command -v python &> /dev/null; then
    python auto_checkin.py
else
    echo "❌ Lỗi: Không tìm thấy Python"
    exit 1
fi
