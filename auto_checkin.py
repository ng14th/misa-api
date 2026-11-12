"""Account-based check-in adapted from vuvanthe64/Misa-Auto-Checkin.

Reference: https://github.com/vuvanthe64/Misa-Auto-Checkin/blob/main/auto_checkin.py
"""
import base64
from typing import Literal

import httpx
import pyotp
from fastapi import HTTPException
from pydantic import BaseModel, ConfigDict, Field, SecretStr, field_validator

BASE_URL = "https://amisapp.misa.vn/APIS"


def generate_response_token(challenge_token):
    salt_suffix = "_MISA-AMIS-TK-PROD-2025-x9VbN4mK8tL2wPc7YqH5RgF3JzS6aWdE"
    raw_token = f"{challenge_token}{salt_suffix}"
    encoded_bytes = base64.b64encode(raw_token.encode("utf-8"))
    return encoded_bytes.decode("utf-8")


class DeviceInfo(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    name: str = Field(min_length=1, max_length=255, pattern=r"^[\x20-\x7E]+$")
    os: str = Field(min_length=1, max_length=100, pattern=r"^[\x20-\x7E]+$")
    os_version: str = Field(default="", max_length=100, pattern=r"^[\x20-\x7E]*$")
    device_type: Literal["Desktop", "Smartphone", "Tablet", "Unknown"]
    user_agent: str = Field(min_length=1, max_length=2048, pattern=r"^[\x20-\x7E]+$")


class CheckInRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    device: DeviceInfo
    username: str = Field(min_length=1, max_length=255)
    password: SecretStr
    secret_key: SecretStr = SecretStr("")
    employee_code: str = Field(min_length=1, max_length=255)
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    gps_name: str = Field(min_length=1, max_length=255)


    @field_validator("password")
    @classmethod
    def validate_password(cls, value):
        if not value.get_secret_value():
            raise ValueError("Mật khẩu không được để trống.")
        return value


async def run_workflow(entry: CheckInRequest, client: httpx.AsyncClient):

    # Keep authentication local to this workflow; never share account sessions between requests.
    headers = {
        "Accept": "*/*", "AppCode": "System", "AppVersion": "100.7", "x-culture": "vi",
        "DeviceName": entry.device.name, "DeviceOS": entry.device.os,
        "DeviceType": entry.device.device_type, "User-Agent": entry.device.user_agent,
    }
    if entry.device.os_version:
        headers["OSVersion"] = entry.device.os_version

    async def request(method, path, *, step, **kwargs):
        try:
            response = await client.request(method, f"{BASE_URL}/{path}", headers=headers, **kwargs)
            response.raise_for_status()
            data = response.json()
        except httpx.TimeoutException:
            raise HTTPException(504, f"MISA phản hồi quá hạn ở bước {step}. Kiểm tra trên AMIS trước khi gửi lại.") from None
        except (httpx.HTTPError, ValueError):
            raise HTTPException(502, f"Phản hồi MISA không hợp lệ ở bước {step}. Kiểm tra trên AMIS trước khi gửi lại.") from None
        if not isinstance(data, dict) or not isinstance(data.get("Success"), bool):
            raise HTTPException(502, f"Sai định dạng phản hồi MISA ở bước {step}.")
        return data

    def require_success(data, step):
        if not data["Success"]:
            # Do not expose authentication responses or tokens to the browser.
            raise HTTPException(502, f"MISA từ chối bước {step}. Kiểm tra tài khoản và cấu hình chấm công trên AMIS.")

    login = await request("POST", "AuthenAPI/api/account/login", step="đăng nhập", json={
        "UserName": entry.username,
        "Password": entry.password.get_secret_value(),
    })
    login_data = login.get("Data")
    user = login_data.get("User") if isinstance(login_data, dict) else None
    if not (login["Success"] and isinstance(user, dict)):
        token = None
        if login["Success"]:
            token = login_data.get("Token") if isinstance(login_data, dict) else login_data
        elif login.get("SubCode") == 8 and isinstance(login_data, dict):
            access = login_data.get("AccessToken")
            token = access.get("Token") if isinstance(access, dict) else None
        if not isinstance(token, str) or not token:
            raise HTTPException(502, "Đăng nhập MISA thất bại hoặc không nhận được token OTP.")
        secret = "".join(entry.secret_key.get_secret_value().split()).upper()
        if not secret:
            raise HTTPException(422, "Tài khoản yêu cầu OTP. Nhập SECRET_KEY (khóa TOTP) trên giao diện.")
        if len(secret) == 6 and secret.isdigit():
            raise HTTPException(422, "SECRET_KEY cần khóa TOTP Base32 của tài khoản, không phải mã OTP 6 số đang hiển thị trên ứng dụng xác thực.")
        try:
            otp = pyotp.TOTP(secret).now()
        except (ValueError, TypeError):
            raise HTTPException(422, "SECRET_KEY không đúng định dạng Base32 (A–Z, 2–7). Hãy nhập khóa thiết lập ứng dụng xác thực của tài khoản MISA.") from None
        login = await request("POST", "AuthenAPI/api/Account/loginwithotp", step="xác thực OTP", json={
            "Token": token, "OTP": otp, "UseAppAuthenticator": True,
            "DeviceToken": "", "Remember": False, "IsTrusted": False,
        })
        require_success(login, "xác thực OTP")
        login_data = login.get("Data")
        user = login_data.get("User") if isinstance(login_data, dict) else None
    if not isinstance(user, dict) or not all(user.get(key) for key in ("UserID", "SessionID", "TenantID")):
        raise HTTPException(502, "MISA không trả đủ thông tin phiên đăng nhập.")
    if user.get("EmployeeCode") and user["EmployeeCode"] != entry.employee_code:
        raise HTTPException(409, "Mã nhân viên không khớp tài khoản MISA vừa đăng nhập.")
    headers.update({"x-sessionid": str(user["SessionID"]), "x-tenantid": str(user["TenantID"])})

    shift_result = await request("GET", "TimekeeperAPI/api/TimeKeepingRemote/validate-working-shift", step="lấy ca làm")
    require_success(shift_result, "lấy ca làm")
    shift = shift_result.get("Data")
    if not isinstance(shift, dict) or not all(shift.get(key) for key in ("ChallengeToken", "WorkingShiftCode", "WorkingShiftName", "WorkingShiftID")):
        raise HTTPException(502, "MISA không trả đủ thông tin ca làm và challenge token.")
    if shift.get("IsRequireFaceIdentifi") or shift.get("IsManagerConfirmTimekeeping"):
        raise HTTPException(409, "Ca làm yêu cầu nhận diện khuôn mặt hoặc xác nhận quản lý. Hãy chấm công bằng ứng dụng MISA AMIS.")
    response_token = generate_response_token(shift["ChallengeToken"])
    payload = {
        "ChallengeToken": shift["ChallengeToken"], "ResponseToken": response_token,
        "GPSName": entry.gps_name, "Latitude": entry.latitude, "Longitude": entry.longitude,
        "WorkingShiftCode": shift["WorkingShiftCode"], "WorkingShiftName": shift["WorkingShiftName"],
        "WorkingShiftID": shift["WorkingShiftID"], "IsMobile": entry.device.device_type in ("Smartphone", "Tablet"), "IsWorkRemote": False,
        "IsGPSFixed": True, "Documents": "[]", "TimeZone": "(UTC +07:00) Asia/Ho_Chi_Minh",
        "ApprovalName": "", "ApprovalToID": 0,
        "IsRequireFaceIdentifi": False, "IsManagerConfirmTimekeeping": False,
    }
    result = await request("POST", "TimekeeperAPI/api/TimeKeepingRemote/timekeeping-now-token",
                           step="chấm công", params={"userId": str(user["UserID"])}, json=payload)
    require_success(result, "chấm công")
    data = result.get("Data")
    if not isinstance(data, dict) or not data.get("CheckTime"):
        raise HTTPException(502, "MISA báo thành công nhưng thiếu thời gian. Kiểm tra bản ghi trên AMIS trước khi gửi lại.")
    return {
        "success": True, "employee_code": user.get("EmployeeCode") or entry.employee_code,
        "check_time": data["CheckTime"], "gps_name": data.get("GPSName") or entry.gps_name,
        "working_shift_name": data.get("WorkingShiftName") or shift["WorkingShiftName"],
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8000)
