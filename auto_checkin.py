import os
import requests
import pyotp
import json
import base64
import random
from datetime import datetime
from dotenv import load_dotenv

# Load cấu hình từ file .env vào biến môi trường
load_dotenv()

# ==============================================================================
# MISA AMIS - TOOL AUTO CHẤM CÔNG (V3 - ANTI BLOCK)
# ==============================================================================

# Đọc thông tin nhạy cảm từ file .env thay vì fix cứng trong code
USERNAME = os.getenv("MISA_USERNAME")
PASSWORD = os.getenv("MISA_PASSWORD")
SECRET_KEY = os.getenv("MISA_SECRET_KEY")

TARGET_GPS_NAME = os.getenv("TARGET_GPS_NAME")
# Cần ép kiểu float cho tọa độ vì biến môi trường mặc định là string
TARGET_LATITUDE = float(os.getenv("TARGET_LATITUDE", 0.0))
TARGET_LONGITUDE = float(os.getenv("TARGET_LONGITUDE", 0.0))

session = requests.Session()

# Pool các thiết bị iOS phổ biến để random
IOS_DEVICES = [
    {
        "name": "iPhone 15 Pro Max",
        "os_version": "26.5",
        "cfnetwork": "3860.600.12",
        "darwin": "25.5.0"
    },
    {
        "name": "iPhone 15 Pro",
        "os_version": "26.4",
        "cfnetwork": "3860.500.11",
        "darwin": "25.4.0"
    },
    {
        "name": "iPhone 14 Pro Max",
        "os_version": "25.6",
        "cfnetwork": "3850.600.10",
        "darwin": "24.6.0"
    },
    {
        "name": "iPhone 14 Pro",
        "os_version": "25.5",
        "cfnetwork": "3850.500.9",
        "darwin": "24.5.0"
    },
    {
        "name": "iPhone 13 Pro Max",
        "os_version": "24.7",
        "cfnetwork": "3840.600.8",
        "darwin": "23.7.0"
    },
    {
        "name": "iPhone 13 Pro",
        "os_version": "24.6",
        "cfnetwork": "3840.500.7",
        "darwin": "23.6.0"
    }
]

def get_random_device_headers():
    """Random device headers để tránh bị phát hiện pattern"""
    device = random.choice(IOS_DEVICES)
    return {
        "Accept": "*/*",
        "AppCode": "System",
        "AppVersion": "100.7",
        "Connection": "keep-alive",
        "Content-Type": "application/json",
        "DeviceName": device["name"],
        "DeviceOS": "IOS",
        "DeviceType": "Smartphone",
        "Host": "amisapp.misa.vn",
        "OSVersion": device["os_version"],
        "User-Agent": f"MISA AMIS/1 CFNetwork/{device['cfnetwork']} Darwin/{device['darwin']}",
        "x-culture": "vi"
    }

# Khởi tạo session với random device
session.headers.update(get_random_device_headers())

user_id = ""

def generate_response_token(challenge_token):
    salt_suffix = "_MISA-AMIS-TK-PROD-2025-x9VbN4mK8tL2wPc7YqH5RgF3JzS6aWdE"
    raw_token = f"{challenge_token}{salt_suffix}"
    encoded_bytes = base64.b64encode(raw_token.encode("utf-8"))
    return encoded_bytes.decode("utf-8")

def do_checkin(shift_info):
    global user_id
    print("\n[*] BƯỚC 4: Bắt đầu quá trình Chấm Công (Gửi tọa độ GPS)...")
    
    challenge_token = shift_info.get("ChallengeToken")
    shift_code = shift_info.get("WorkingShiftCode")
    shift_name = shift_info.get("WorkingShiftName")
    shift_id = shift_info.get("WorkingShiftID")
    
    response_token = generate_response_token(challenge_token)
    url_submit = f"https://amisapp.misa.vn/APIS/TimekeeperAPI/api/TimeKeepingRemote/timekeeping-now-token?userId={user_id}"
    
    payload = {
        "ChallengeToken": challenge_token,
        "GPSName": TARGET_GPS_NAME,
        "Latitude": TARGET_LATITUDE,
        "Longitude": TARGET_LONGITUDE,
        "WorkingShiftCode": shift_code,
        "WorkingShiftName": shift_name,
        "WorkingShiftID": shift_id,
        "IsWorkRemote": False,
        "IsMobile": True,
        "Documents": "[]",
        "IsGPSFixed": True,
        "TimeZone": "(UTC +07:00) Asia/Ho_Chi_Minh",
        "ApprovalName": "",
        "IsRequireFaceIdentifi": False,
        "IsManagerConfirmTimekeeping": False,
        "ResponseToken": response_token,
        "ApprovalToID": 0
    }
    
    try:
        res = session.post(url_submit, json=payload, timeout=15)
        if res.status_code == 200:
            data = res.json()
            if data.get("Success"):
                info = data.get("Data", {})
                print("\n[========================================================]")
                print("   🎉 CHẤM CÔNG THÀNH CÔNG RỰC RỠ! 🎉")
                print(f"    Thời gian: {info.get('CheckTime')}")
                print(f"    Vị trí: {info.get('GPSName')}")
                print(f"    Ca làm: {info.get('WorkingShiftName')}")
                print("[========================================================]")
            else:
                print("[-] Bị từ chối chấm công:", data.get("UserMessage"))
        else:
            print("[-] Lỗi HTTP chấm công:", res.status_code, res.text)
    except Exception as e:
        print("[-] Lỗi mạng Bước 4:", str(e))

def process_step_3_and_4():
    print("\n[*] BƯỚC 3: Đang lấy thông tin ca làm việc (Shift ID & Token)...")
    res_shift = session.get("https://amisapp.misa.vn/APIS/TimekeeperAPI/api/TimeKeepingRemote/validate-working-shift")
    data_shift = res_shift.json()
    
    if data_shift.get("Success"):
        shift_info = data_shift.get("Data", {})
        print(f"[+] Lấy ca thành công: {shift_info.get('WorkingShiftName')} (ID: {shift_info.get('WorkingShiftID')})")
        do_checkin(shift_info)
    else:
        print("[-] Lỗi Bước 3 - Không lấy được ca làm việc:", data_shift)

def run_workflow():
    global user_id
    print("=" * 60)
    print("    TOOL AUTO CHẤM CÔNG MISA AMIS - V3 (ANTI BLOCK)")
    print("=" * 60)
    
    print("\n[*] BƯỚC 1: Gửi request đăng nhập cơ bản...")
    url_login = "https://amisapp.misa.vn/APIS/AuthenAPI/api/account/login"
    res_login = session.post(url_login, json={"Password": PASSWORD, "UserName": USERNAME})
    data_login = res_login.json()
    
    # ---------------- XỬ LÝ LOGIC ĐĂNG NHẬP MỚI ----------------
    step1_token = ""
    is_login_success = False

    # Trường hợp 1: Vào thẳng không cần OTP
    if data_login.get("Success") and isinstance(data_login.get("Data"), dict) and "User" in data_login.get("Data"):
        print("[+] Đăng nhập thành công (Bỏ qua OTP).")
        user_info = data_login["Data"]["User"]
        user_id = user_info.get("UserID")
        session.headers.update({
            "x-sessionid": user_info.get("SessionID"),
            "x-tenantid": user_info.get("TenantID")
        })
        is_login_success = True

    # Trường hợp 2: Trả về Token ở cấu trúc cũ
    elif data_login.get("Success") and "Token" in str(data_login.get("Data", "")):
        step1_token = data_login.get("Data", {}).get("Token") if isinstance(data_login.get("Data"), dict) else data_login.get("Data")
    
    # Trường hợp 3: Bị chặn (SubCode 8) - Bắt buộc nhập OTP
    elif not data_login.get("Success") and data_login.get("SubCode") == 8:
        print("[-] Hệ thống yêu cầu mã xác thực 2FA (SubCode 8).")
        step1_token = data_login.get("Data", {}).get("AccessToken", {}).get("Token")

    else:
        print("[-] Lỗi không xác định ở Bước 1:")
        print(json.dumps(data_login, ensure_ascii=False, indent=2))
        return

    # ---------------- XỬ LÝ BƯỚC 2 (NẾU CẦN) ----------------
    if not is_login_success:
        if not step1_token:
            print("[-] Lỗi: Không trích xuất được Token để tiếp tục.")
            return

        print("\n[*] BƯỚC 2: Bắt đầu gửi mã OTP...")
        totp = pyotp.TOTP(SECRET_KEY)
        res_otp = session.post(
            "https://amisapp.misa.vn/APIS/AuthenAPI/api/Account/loginwithotp", 
            json={
                "DeviceToken": "", 
                "Remember": True, 
                "Token": step1_token, 
                "UseAppAuthenticator": True, 
                "OTP": totp.now(), 
                "IsTrusted": True
            }
        )
        
        data_otp = res_otp.json()
        if data_otp.get("Success"):
            print("[+] Đăng nhập 2FA thành công!")
            user_info = data_otp.get("Data", {}).get("User", {})
            user_id = user_info.get("UserID")
            session.headers.update({
                "x-sessionid": user_info.get("SessionID"),
                "x-tenantid": user_info.get("TenantID")
            })
        else:
            print("[-] Thất bại xác thực OTP:", data_otp.get("UserMessage"))
            return

    # Chạy tiếp bước 3 và 4
    process_step_3_and_4()

if __name__ == "__main__":
    run_workflow()