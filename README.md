# 🎯 MISA AMIS Auto Checkin Tool

Tool tự động chấm công cho hệ thống MISA AMIS với khả năng chống block và hỗ trợ xác thực 2FA (OTP).

## ✨ Tính năng

- ✅ Tự động đăng nhập MISA AMIS
- ✅ Hỗ trợ xác thực 2FA với Google Authenticator
- ✅ Tự động lấy ca làm việc
- ✅ Gửi tọa độ GPS để chấm công
- ✅ Chống block với token mã hóa
- ✅ **Random device headers** - Tự động đổi thiết bị iOS để tránh bị phát hiện
- ✅ **Random thời gian chấm công** - Không chấm đúng giờ cố định, tránh pattern
- ✅ Hỗ trợ đa nền tảng (Windows, macOS, Linux)

## 📋 Yêu cầu hệ thống

- Python 3.7 trở lên
- Kết nối Internet

## 🚀 Hướng dẫn cài đặt

### 1. Clone repository

```bash
git clone https://github.com/yourusername/Misa-Auto-Checkin.git
cd Misa-Auto-Checkin
```

### 2. Cài đặt Python

#### Windows:
1. Tải Python từ https://www.python.org/downloads/
2. **Quan trọng**: Chọn "Add Python to PATH" khi cài đặt
3. Kiểm tra cài đặt thành công:
   ```cmd
   python --version
   ```

#### macOS:
Python thường đã có sẵn. Nếu chưa có, cài đặt bằng Homebrew:
```bash
brew install python3
```

Kiểm tra:
```bash
python3 --version
```

#### Linux (Ubuntu/Debian):
```bash
sudo apt update
sudo apt install python3 python3-pip
```

### 3. Cài đặt thư viện phụ thuộc

#### Windows:
```cmd
pip install -r requirements.txt
```

#### macOS/Linux:
```bash
pip3 install -r requirements.txt
```

## ⚙️ Cấu hình

### 1. Lấy Secret Key cho 2FA

1. Đăng nhập MISA AMIS trên web
2. Vào **Cài đặt** → **Bảo mật** → **Xác thực hai yếu tố**
3. Chọn **Cài đặt ứng dụng xác thực**
4. Copy **Secret Key** (dạng: `UPQXZRDKNZY2OJJZLF7A5RQKEV6IHDCX`)

### 2. Tạo file cấu hình

1. Copy file mẫu:

   **Windows (CMD):**
   ```cmd
   copy .env.example .env
   ```

   **macOS/Linux:**
   ```bash
   cp .env.example .env
   ```

2. Mở file `.env` bằng text editor yêu thích (Notepad++, VSCode, nano, vim...)

3. Điền thông tin của bạn:

```env
# Thông tin đăng nhập
MISA_USERNAME=0973103206          # Số điện thoại hoặc username MISA
MISA_PASSWORD=your_password       # Mật khẩu đăng nhập
MISA_SECRET_KEY=UPQXZRDKNZY2OJJZ  # Secret key từ bước 1

# Thông tin GPS
TARGET_GPS_NAME=VP Trà Khúc       # Tên địa điểm chấm công
TARGET_LATITUDE=10.805944         # Vĩ độ
TARGET_LONGITUDE=106.665083       # Kinh độ
```

### 3. Lấy tọa độ GPS

**Cách 1: Dùng Google Maps**
1. Truy cập https://www.google.com/maps
2. Nhấp chuột phải vào địa điểm công ty
3. Chọn tọa độ hiển thị ở đầu menu (vd: `10.805944, 106.665083`)
4. Copy vào file `.env`

**Cách 2: Dùng điện thoại**
1. Mở Google Maps trên điện thoại
2. Nhấn giữ vào vị trí công ty
3. Xem tọa độ ở thanh tìm kiếm

## 🧪 Test chạy thử ngay (sau khi cài đặt xong)

Sau khi cấu hình file `.env` xong, test thử để đảm bảo mọi thứ hoạt động:

### Windows:
```cmd
# Cách 1: Chạy trực tiếp
python auto_checkin.py

# Cách 2: Dùng batch file
run_checkin.bat

# Cách 3: Test random (sẽ sleep 30-60 giây trước khi chấm)
random_checkin.bat 30 60
```

### macOS/Linux:
```bash
# Cách 1: Chạy trực tiếp
python3 auto_checkin.py

# Cách 2: Dùng shell script
./run_checkin.sh

# Cách 3: Test random (sẽ sleep 30-60 giây trước khi chấm)
./random_checkin.sh 30 60
```

### Kết quả mong đợi

```
============================================================
    TOOL AUTO CHẤM CÔNG MISA AMIS - V3 (ANTI BLOCK)
============================================================

[*] BƯỚC 1: Gửi request đăng nhập cơ bản...
[+] Đăng nhập thành công (Bỏ qua OTP).

[*] BƯỚC 3: Đang lấy thông tin ca làm việc (Shift ID & Token)...
[+] Lấy ca thành công: Ca sáng (ID: 12345)

[*] BƯỚC 4: Bắt đầu quá trình Chấm Công (Gửi tọa độ GPS)...

[========================================================]
   🎉 CHẤM CÔNG THÀNH CÔNG RỰC RỠ! 🎉
    Thời gian: 2024-01-15 08:30:00
    Vị trí: VP Trà Khúc
    Ca làm: Ca sáng
[========================================================]
```

## 🤖 Tự động hóa (Quan trọng: Dùng random để tránh bị phát hiện)

### 🎲 Chấm công với thời gian ngẫu nhiên (Khuyến nghị)

Thay vì chấm công đúng 8:00 sáng mỗi ngày (dễ bị phát hiện), nên random thời gian trong khoảng:
- **Sáng**: 8:00 - 8:15 (random 0-15 phút)
- **Chiều**: 17:45 - 18:15 (random 0-30 phút)

Tool cung cấp script `random_checkin.sh` / `random_checkin.bat` để làm điều này.

### Windows Task Scheduler (với Random)

#### Cách 1: Dùng random script (Khuyến nghị)

1. Mở **Task Scheduler** (Tìm kiếm trong Start Menu)
2. Chọn **Create Basic Task**
3. Đặt tên: `MISA Auto Checkin Morning`
4. Trigger: **Daily** → Chọn **8:00 AM** (script sẽ tự random thêm 0-15 phút)
5. Action: **Start a program**
   - Program: `C:\Windows\System32\cmd.exe`
   - Add arguments: `/c "cd /d C:\Users\YourName\Misa-Auto-Checkin && random_checkin.bat 0 900"`
     - `0 900` = random từ 0-900 giây (0-15 phút)
   - Start in: `C:\Users\YourName\Misa-Auto-Checkin`
6. Finish

**Tạo task cho buổi chiều:**
- Tên: `MISA Auto Checkin Evening`
- Trigger: **Daily** → **5:45 PM**
- Arguments: `/c "cd /d C:\Users\YourName\Misa-Auto-Checkin && random_checkin.bat 0 1800"`
  - `0 1800` = random từ 0-1800 giây (0-30 phút)

#### Cách 2: Chạy trực tiếp (không random)

Nếu muốn chấm công đúng giờ cố định:
- Program: `python.exe` hoặc `C:\Python3X\python.exe`
- Add arguments: `auto_checkin.py`
- Start in: `C:\Users\YourName\Misa-Auto-Checkin`

### macOS/Linux Cron (với Random)

#### Cách 1: Dùng random script (Khuyến nghị)

1. Mở terminal và chỉnh sửa crontab:
   ```bash
   crontab -e
   ```

2. Thêm các dòng sau:
   ```cron
   # Chấm công sáng: 8:00-8:15 (random 0-900 giây = 0-15 phút), thứ 2-6
   0 8 * * 1-5 cd /Users/yourname/Misa-Auto-Checkin && ./random_checkin.sh 0 900 >> /tmp/misa.log 2>&1
   
   # Chấm công chiều: 17:45-18:15 (random 0-1800 giây = 0-30 phút), thứ 2-6
   45 17 * * 1-5 cd /Users/yourname/Misa-Auto-Checkin && ./random_checkin.sh 0 1800 >> /tmp/misa.log 2>&1
   ```

3. Lưu file:
   - Vim/Vi: Nhấn `Esc`, gõ `:wq`, Enter
   - Nano: `Ctrl+X`, `Y`, Enter

4. Kiểm tra cron đã thêm:
   ```bash
   crontab -l
   ```

**Giải thích:**
- `0 8 * * 1-5` → 8:00 sáng, thứ 2-6
- `./random_checkin.sh 0 900` → Script sẽ sleep random 0-900 giây (0-15 phút) trước khi chấm công
- `>> /tmp/misa.log 2>&1` → Lưu log để debug

**Tùy chỉnh khoảng thời gian random:**
```bash
./random_checkin.sh <MIN_SECONDS> <MAX_SECONDS>

# Ví dụ:
./random_checkin.sh 0 600    # Random 0-10 phút
./random_checkin.sh 0 1200   # Random 0-20 phút
./random_checkin.sh 300 900  # Random 5-15 phút
```

#### Cách 2: Chạy trực tiếp (không random)

Nếu muốn chấm công đúng giờ cố định:
```cron
# Sáng 8:00, chiều 18:00
0 8 * * 1-5 cd /Users/yourname/Misa-Auto-Checkin && python3 auto_checkin.py >> /tmp/misa.log 2>&1
0 18 * * 1-5 cd /Users/yourname/Misa-Auto-Checkin && python3 auto_checkin.py >> /tmp/misa.log 2>&1
```

**Xem log để kiểm tra:**
```bash
tail -f /tmp/misa.log
```

## 🔧 Xử lý lỗi thường gặp

### ❌ `ModuleNotFoundError: No module named 'requests'`
**Nguyên nhân:** Chưa cài đặt thư viện
**Giải pháp:**
```bash
pip install -r requirements.txt
# hoặc cài từng cái
pip install requests pyotp python-dotenv
```

### ❌ `KeyError: 'MISA_USERNAME'` hoặc biến môi trường None
**Nguyên nhân:** File `.env` chưa tạo hoặc sai định dạng
**Giải pháp:**
1. Kiểm tra file `.env` có tồn tại trong cùng thư mục với `auto_checkin.py`
2. Đảm bảo không có khoảng trắng thừa: `MISA_USERNAME=value` (không phải `MISA_USERNAME = value`)
3. Không có dấu ngoặc kép thừa

### ❌ `[-] Thất bại xác thực OTP`
**Nguyên nhân:** Secret key sai hoặc thời gian hệ thống không chính xác
**Giải pháp:**
1. Kiểm tra lại `MISA_SECRET_KEY` trong file `.env`
2. Đồng bộ thời gian hệ thống:
   - **Windows:** Settings → Time & Language → Sync now
   - **macOS:** System Preferences → Date & Time → Set date and time automatically
   - **Linux:** `sudo ntpdate pool.ntp.org`

### ❌ `[-] Bị từ chối chấm công: GPS không hợp lệ`
**Nguyên nhân:** Tọa độ GPS sai hoặc ngoài phạm vi cho phép
**Giải pháp:**
1. Kiểm tra lại `TARGET_LATITUDE` và `TARGET_LONGITUDE`
2. Đảm bảo tọa độ là số thập phân (float), không phải độ/phút/giây
3. Thử lấy lại tọa độ từ Google Maps

### ❌ Windows Task Scheduler không chạy
**Giải pháp:**
1. Kiểm tra đường dẫn Python đầy đủ: `where python` trong CMD
2. Dùng đường dẫn tuyệt đối cho cả Python và script
3. Hoặc tạo file `.bat` như hướng dẫn ở phần Tự động hóa
4. Đảm bảo Task chạy với quyền user hiện tại (không cần Administrator)

## 📝 Lưu ý quan trọng

⚠️ **Bảo mật:**
- File `.env` chứa thông tin nhạy cảm, **KHÔNG** commit lên Git
- File `.gitignore` đã được cấu hình để bỏ qua `.env`
- Không share Secret Key với người khác

⚠️ **Tính năng chống phát hiện:**
- **Random Device Headers**: Mỗi lần chạy, tool tự động random thiết bị iOS (iPhone 13/14/15 Pro/Max) với version khác nhau để tránh bị phát hiện pattern
- **Random Time**: Dùng `random_checkin.sh`/`random_checkin.bat` để random thời gian chấm công trong khoảng bạn chọn
- Hai tính năng này giúp giảm rủi ro bị hệ thống phát hiện bot

⚠️ **Sử dụng:**
- Tool chỉ nên dùng cho mục đích cá nhân
- Tuân thủ quy định nội bộ công ty về chấm công
- Kiểm tra kỹ trước khi chạy tự động hằng ngày

⚠️ **Thời gian:**
- Đặt thời gian chạy trước giờ vào ca 5-10 phút để đề phòng lỗi mạng
- Tránh chạy quá sớm (hệ thống có thể chưa mở ca)
- Khuyến nghị dùng random time thay vì chấm đúng giờ cố định

## 📄 License

MIT License - Tự do sử dụng và chỉnh sửa

## 🙏 Credits

Tool được phát triển dựa trên reverse engineering API của MISA AMIS.

---

**⭐ Nếu tool hữu ích, hãy cho repo một ngôi sao nhé! ⭐**
