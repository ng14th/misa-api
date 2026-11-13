# MISA API — Webapp chấm công

Webapp FastAPI để đăng nhập tài khoản MISA AMIS, xác thực TOTP nếu cần và chấm công theo ca làm hiện tại. Giao diện tiếng Việt, nhập tài khoản trực tiếp, chọn vị trí và gửi thông tin thiết bị mà trình duyệt đang sử dụng cung cấp.

- Mã nguồn: https://github.com/ng14th/misa-api
- Dựa trên [vuvanthe64/Misa-Auto-Checkin](https://github.com/vuvanthe64/Misa-Auto-Checkin), giữ lịch sử Git và giấy phép MIT.

## 1. Chuẩn bị

- Tài khoản MISA có quyền chấm công và mã nhân viên tương ứng.
- Điện thoại có Google Authenticator nếu tài khoản bật xác thực hai yếu tố bằng ứng dụng.
- Python 3.11+ để chạy trực tiếp, hoặc Docker Engine/Desktop.
- Node.js 18+ chỉ cần khi chạy kiểm thử giao diện.

Ứng dụng không đọc `.env` và không cần `X_CLIENTID`/`X_SECRET_KEY`. Không đưa mật khẩu hoặc khóa TOTP vào mã nguồn.

## 2. Lấy SECRET_KEY cho TOTP

### Phân biệt khóa và mã OTP

**SECRET_KEY** là khóa thiết lập ứng dụng xác thực, thường gồm chữ A–Z và số 2–7. **OTP** là mã 6 số thay đổi theo thời gian mà Authenticator sinh ra. Ô SECRET_KEY cần khóa thiết lập; không nhập mã OTP 6 số vào ô này.

### Thiết lập trên MISA ID

1. Mở [MISA ID](https://id.misa.vn) và đăng nhập tài khoản MISA của bạn.
2. Vào mục **Bảo mật / Bảo vệ tài khoản → Xác thực hai yếu tố → Ứng dụng xác thực / Google Authenticator → Thiết lập**. Tên mục có thể khác theo giao diện tài khoản. Có thể truy cập từ avatar trong AMIS → **Thiết lập bảo mật**.
3. Nhập mật khẩu khi được yêu cầu.
4. Tại màn hình **Thiết lập Ứng dụng xác thực**, ở **B2: Quét mã QR**, chọn **Không thể quét mã này?** nếu khóa chưa hiển thị.
5. Tìm ô chứa chuỗi ký tự ngay dưới dòng hướng dẫn **Nhập tên tài khoản, mã bên dưới và nhấn Thêm**. Nhấn biểu tượng copy cạnh ô: đó là khóa cần điền vào SECRET_KEY của webapp.
6. Trên Google Authenticator, nhấn **+ → Quét mã QR**, hoặc **Nhập khóa thiết lập**, nhập tên tài khoản và khóa vừa lấy, chọn loại dựa trên thời gian nếu ứng dụng yêu cầu.
7. Trở lại MISA, tại **B3: Nhập mã xác nhận**, nhập mã 6 số hiện trong Authenticator rồi nhấn **Tiếp theo** để hoàn tất liên kết.
8. Điền khóa thiết lập đã copy ở bước 5 vào ô **SECRET_KEY (TOTP)** trên webapp. Chấp nhận chữ thường và khoảng trắng giữa các nhóm ký tự; server tự chuẩn hóa trước khi sinh OTP.

Tham khảo chính thức: [MISA — thiết lập phương thức xác thực](https://helpamis.misa.vn/amis-cham-cong/kb/huong-dan-nguoi-dung-truy-cap-misa-id-thiet-lap-them-phuong-thuc-xac-thuc-du-phong/).

### Đã liên kết Authenticator nhưng không lưu khóa

Không thể suy ngược SECRET_KEY từ mã OTP 6 số. Nếu không còn màn hình hiển thị khóa, dùng phần bảo mật MISA ID để thiết lập lại phương thức Google Authenticator theo hướng dẫn MISA. Trước khi làm, bảo đảm còn quyền truy cập email/số điện thoại xác thực dự phòng. Sau khi thiết lập lại, quét QR mới, hoàn tất xác nhận và cập nhật khóa mới trong webapp; mục Authenticator cũ có thể không còn hợp lệ.

Nếu không thể đăng nhập bằng phương thức dự phòng, liên hệ MISA để khôi phục. Xem [FAQ bảo mật hai lớp MISA ID](https://helpid.misa.vn/kb/cau-hoi-thuong-gap-khi-thiet-lap-bao-mat-2-lop-2fa-tren-misa-id/).

QR và SECRET_KEY đều là bí mật xác thực: không gửi vào issue, commit, ảnh README hay chat. Nếu đã lộ, thiết lập lại để đổi khóa. Có thể để trống SECRET_KEY khi tài khoản đăng nhập không yêu cầu TOTP.

## 3. Chạy trực tiếp

```bash
git clone https://github.com/ng14th/misa-api.git
cd misa-api
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python auto_checkin.py
```

Windows PowerShell: thay lệnh kích hoạt bằng `.\.venv\Scripts\Activate.ps1`, dùng `python` thay `python3` nếu phù hợp với cài đặt Python của máy.

Mở http://127.0.0.1:8000. Chế độ phát triển tự reload:

```bash
uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

Các script `run_checkin.*`, `random_checkin.*` giữ từ repo gốc gọi `auto_checkin.py`; file này hiện mở webserver. Chúng không còn tự chấm công từ `.env`; không cần dùng script random để vận hành webapp.

## 4. Sử dụng giao diện

1. Nhập **Username** (tài khoản/số điện thoại MISA), **Password**, **SECRET_KEY** nếu cần, và **Mã nhân viên**.
   Nút **Hiện/Ẩn** cạnh ô Password cho phép bật/tắt hiển thị mật khẩu.
2. Kiểm tra dòng thông tin thiết bị do trình duyệt báo.
3. Chọn **Vị trí chấm công**, hoặc mở **Sử dụng GPS hiện tại**, cấp quyền vị trí và nhập tên địa điểm GPS. GPS trình duyệt cần HTTPS hoặc localhost.
4. Tùy chọn bật **Nhớ tất cả thông tin đã nhập**.
5. Bấm **Ghi nhận chấm công** và chờ kết quả. Thời gian, ca làm lấy từ MISA, không đặt thời gian thủ công.

API chấm công theo `userId` của tài khoản đăng nhập. Mã nhân viên dùng đối chiếu khi MISA trả `EmployeeCode`; nếu không khớp thì dừng. Nếu MISA không trả mã, mã nhập chỉ dùng hiển thị kết quả, không chuyển sang tài khoản nhân viên khác.

Checkbox ghi nhớ mặc định tắt. Khi bật, username, password, SECRET_KEY, mã nhân viên, vị trí, tọa độ và tên GPS được lưu vào **localStorage trên trình duyệt này**, gồm bí mật ở dạng JavaScript cùng origin có thể đọc. Chỉ bật trên máy cá nhân. Bỏ chọn để xóa dữ liệu đã lưu. Khi không bật ghi nhớ, password và SECRET_KEY bị xóa khỏi form sau lần gửi. Dữ liệu ghi nhớ chỉ áp dụng cho trình duyệt và địa chỉ local đang sử dụng.

### Tự điền bằng link trên điện thoại

Thêm các tham số `username`, `employee_code`, `secret_key`, `location` vào link để tự điền form. `location` là key vị trí trong cấu hình, ví dụ `VPTRAKHUC`. Ví dụ với dữ liệu minh họa:

```text
http://127.0.0.1:8000/?username=0901234567&employee_code=NV000001&location=VPTRAKHUC#secret_key=YOUR_TOTP_SECRET
```

Thay địa chỉ localhost bằng địa chỉ webapp đang dùng khi mở trên điện thoại. Hỗ trợ tham số sau `?` và sau `#`; giá trị sau `#` ưu tiên nếu trùng tên. Nên đặt `secret_key` sau `#` để khóa không được gửi lên server trong URL request. Link vẫn chứa khóa bí mật, chỉ lưu riêng trên điện thoại cá nhân và không chia sẻ.

Các trường có trong link ưu tiên hơn dữ liệu ghi nhớ; trường vắng mặt giữ nguyên. Giá trị rỗng sẽ xóa trường tương ứng. Vị trí không hợp lệ yêu cầu chọn lại, không dùng tọa độ cũ. Mã hóa ký tự đặc biệt trong giá trị (ví dụ dấu `+` là `%2B`, khoảng trắng là `%20`). Link không tự gửi chấm công, không tự bật ghi nhớ và không hỗ trợ truyền password; nhập mật khẩu rồi bấm **Ghi nhận chấm công**.

### Cấu hình danh sách vị trí

Sửa `constant/location.py`, tuple theo thứ tự **(latitude, longitude)**:

```python
VPTRAKHUC = (10.805939, 106.665093)

MAPPING_NAME_LOCALTION = {
    "VPTRAKHUC": "VP Trà Khúc",
}
```

Dropdown hiển thị **VP Trà Khúc**, gửi `GPSName` là **VPTRAKHUC**. Giữ đúng tên biến `MAPPING_NAME_LOCALTION` hiện có. Khởi động lại server hoặc rebuild container sau khi sửa, rồi tải lại trang.

### Thông tin thiết bị

Frontend lấy `navigator.userAgent`, `navigator.platform` và User-Agent Client Hints nếu trình duyệt hỗ trợ, gửi object `device` cùng request. Backend dùng dữ liệu đó cho `DeviceName`, `DeviceOS`, `OSVersion` (nếu có), `DeviceType` và `User-Agent` trong các request tới MISA. Không còn danh sách iPhone hoặc chọn thiết bị ngẫu nhiên trong code. `IsMobile` được đặt theo loại thiết bị trình duyệt báo: smartphone/tablet là true, desktop là false.

Đây là thông tin do trình duyệt cung cấp, không phải chứng thực phần cứng. Trình duyệt có thể giới hạn model/version; nếu không cung cấp model, ứng dụng dùng tên nền tảng được báo, không tự suy đoán model máy. Thiết bị được đọc lại khi mở trang và không nằm trong dữ liệu ghi nhớ. Tham khảo [MDN User-Agent Client Hints](https://developer.mozilla.org/en-US/docs/Web/API/Navigator/userAgentData).

## 5. Docker

### Chạy thử độc lập trên máy

```bash
docker build -t misa-amis:local .
docker run --rm --name misa-local -p 127.0.0.1:8000:8000 misa-amis:local uvicorn main:app --host 0.0.0.0 --port 8000
```

Mở http://127.0.0.1:8000. Lệnh trên chạy backend trực tiếp trên cổng 8000.

Sau khi cập nhật code hoặc vị trí, dừng container bằng `Ctrl+C`, build lại image và chạy lại lệnh trên. `.dockerignore` loại `.env`, `.git` và dữ liệu local khỏi image.

## 6. API và cấu trúc mã

| Endpoint | Mục đích |
| --- | --- |
| `GET /` | Giao diện |
| `GET /healthz` | Tình trạng ứng dụng |
| `GET /api/locations` | Key, tên hiển thị và tọa độ |
| `POST /api/checkins` | Tài khoản, mã nhân viên, GPS và device từ form |

Swagger local ở http://127.0.0.1:8000/docs; JSON schema ở `/openapi.json`. API POST yêu cầu `username`, `password`, `employee_code`, `latitude`, `longitude`, `gps_name`, `device`; `secret_key` chỉ cần nếu MISA yêu cầu OTP. Device gồm `name`, `os`, `os_version` (có thể trống), `device_type` (Desktop/Smartphone/Tablet/Unknown), `user_agent`.

- `auto_checkin.py`: model dữ liệu, đăng nhập, TOTP, ca làm, ký response token và chấm công.
- `main.py`: FastAPI, static, API vị trí, validation và HTTP client riêng mỗi request.
- `static/`: giao diện, thu thập device, ghi nhớ trên trình duyệt.
- `constant/location.py`: các địa điểm cấu hình.
- `Dockerfile`, `.dockerignore`: đóng gói ứng dụng để chạy local bằng Docker.
- `tests/`: mock MISA và kiểm thử frontend.

## 7. Lỗi thường gặp

| Thông báo / triệu chứng | Cách xử lý |
| --- | --- |
| Tài khoản yêu cầu OTP | Điền khóa TOTP từ màn hình thiết lập MISA, không nhập OTP 6 số. |
| SECRET_KEY không đúng Base32 | Copy lại khóa; khoảng trắng/chữ thường được xử lý tự động. Không dán toàn bộ URL QR vào ô khóa. |
| MISA từ chối xác thực OTP | Kiểm tra khóa thuộc đúng tài khoản, đã hoàn tất liên kết và đồng hồ hệ thống đồng bộ. |
| Mã nhân viên không khớp | Dùng mã nhân viên thuộc tài khoản vừa đăng nhập. |
| Không lấy được GPS | Mở ứng dụng bằng localhost và cấp quyền vị trí trong trình duyệt/hệ điều hành. |
| Timeout / mất kết nối / thiếu kết quả | Kiểm tra bản ghi trên AMIS trước khi gửi lại; ứng dụng không tự retry. |
| Thiếu thông tin device sau cập nhật | Tải lại trang để frontend mới gửi đủ dữ liệu. |

API ứng dụng tham khảo từ repo gốc, không thuộc hợp đồng OpenAPI trong PDF; có thể thay đổi từ phía MISA. Không đảm bảo server MISA ghi nguồn `DataSourceID = 3`. Backend không ghi mật khẩu/khóa vào file hoặc database, không tái sử dụng phiên giữa người dùng. Nếu ca làm trả yêu cầu nhận diện khuôn mặt/xác nhận quản lý, app dừng và hướng dẫn dùng ứng dụng MISA. Bản này chưa có lớp đăng nhập riêng cho webapp; mặc định chỉ chạy trên địa chỉ local `127.0.0.1`.

## 8. Kiểm thử

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
node --test tests/test_form.mjs
ruff check .
ruff format --check .
```

Kiểm thử dùng HTTP mock, không đăng nhập/chấm công thật. Bao gồm đăng nhập/OTP, chuẩn hóa khóa, mã nhân viên, header thiết bị, tọa độ, lỗi kết nối, không lộ bí mật trong lỗi, lưu/khôi phục dữ liệu form và bật/tắt hiển thị mật khẩu.

Python dùng Ruff để format và kiểm tra PEP 8, giới hạn 79 ký tự/dòng, sắp xếp import. Chạy `ruff check --fix .` và `ruff format .` trước khi commit; cấu hình nằm trong `ruff.toml`.

## Giấy phép

MIT — xem `LICENSE`. Giữ thông tin tác giả và giấy phép của repo gốc khi phân phối.
