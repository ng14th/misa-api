const form = document.querySelector('#checkin-form');
const submit = document.querySelector('#submit-button');
const result = document.querySelector('#result');
const locationSelect = document.querySelector('#location');
const locationStatus = document.querySelector('#location-status');
let locations = [];
let coordinates = {};
const remember = document.querySelector('#remember-inputs');
const rememberStatus = document.querySelector('#remember-status');
const storageKey = 'misa-checkin-inputs';
const rememberedFields = ['username', 'password', 'secret-key', 'employee-code', 'gps-name'];
let savedLocation = '';

document.querySelector('#toggle-password').addEventListener('click', () => {
  const password = document.querySelector('#password');
  const button = document.querySelector('#toggle-password');
  const show = password.type === 'password';
  password.type = show ? 'text' : 'password';
  button.textContent = show ? 'Ẩn' : 'Hiện';
  button.setAttribute('aria-label', show ? 'Ẩn mật khẩu' : 'Hiện mật khẩu');
  button.setAttribute('aria-pressed', String(show));
});

async function collectDeviceInfo() {
  const ua = navigator.userAgent || '';
  const uaData = navigator.userAgentData;
  let hints = {};
  if (uaData?.getHighEntropyValues) {
    try {
      hints = await uaData.getHighEntropyValues(['model', 'platformVersion']);
    } catch {
      // Browsers may restrict device details; use the information still available.
    }
  }
  const ipad = /iPad/.test(ua) || (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1);
  const os = uaData?.platform || (ipad || /iPhone|iPod/.test(ua) ? 'iOS'
    : /Android/.test(ua) ? 'Android' : /Windows/.test(ua) ? 'Windows'
    : /Mac OS X/.test(ua) ? 'macOS' : /Linux/.test(ua) ? 'Linux' : 'Unknown');
  const version = ipad ? ua.match(/CPU (?:iPhone )?OS ([\d_]+)/)
    : ua.match(/(?:Android |(?:iPhone )?OS |Mac OS X |Windows NT )([\d._]+)/);
  const mobile = uaData?.mobile ?? /Mobile|iPhone|iPod/.test(ua);
  return {
    name: hints.model || navigator.platform || os,
    os,
    os_version: hints.platformVersion || (version ? version[1].replaceAll('_', '.') : ''),
    device_type: ipad || (/Android/.test(ua) && !mobile) ? 'Tablet' : mobile ? 'Smartphone' : ua ? 'Desktop' : 'Unknown',
    user_agent: ua,
  };
}

const deviceInfo = collectDeviceInfo();
deviceInfo.then(device => {
  document.querySelector('#device-status').textContent = `Thiết bị trình duyệt báo: ${device.name} · ${device.os} ${device.os_version} · ${device.device_type}`;
});

function saveInputs() {
  try {
    if (!remember.checked) {
      localStorage.removeItem(storageKey);
      return true;
    }
    const fields = Object.fromEntries(rememberedFields.map(id => [id, document.querySelector(`#${id}`).value]));
    localStorage.setItem(storageKey, JSON.stringify({fields, location: locationSelect.value, coordinates}));
    rememberStatus.textContent = 'Đã lưu tất cả, gồm mật khẩu và SECRET_KEY, trên trình duyệt này. Bỏ chọn để xóa.';
    return true;
  } catch {
    rememberStatus.textContent = 'Trình duyệt không cho phép lưu/xóa dữ liệu. Kiểm tra quyền lưu trữ của trang.';
    return false;
  }
}

try {
  const saved = JSON.parse(localStorage.getItem(storageKey) || 'null');
  if (saved && typeof saved.fields === 'object' && saved.fields !== null) {
    remember.checked = true;
    for (const id of rememberedFields) {
      if (typeof saved.fields[id] === 'string') document.querySelector(`#${id}`).value = saved.fields[id];
    }
    savedLocation = typeof saved.location === 'string' ? saved.location : '';
    if (Number.isFinite(saved.coordinates?.latitude) && Number.isFinite(saved.coordinates?.longitude)) {
      coordinates = {latitude: saved.coordinates.latitude, longitude: saved.coordinates.longitude};
    }
    rememberStatus.textContent = 'Đã khôi phục thông tin đã lưu, gồm mật khẩu và SECRET_KEY. Bỏ chọn để xóa.';
  }
} catch {
  rememberStatus.textContent = 'Không đọc được thông tin đã lưu. Bạn có thể nhập lại thông tin trên form.';
}

const autofillParams = new URLSearchParams(window.location.search);
for (const [key, value] of new URLSearchParams(window.location.hash.slice(1))) {
  autofillParams.set(key, value);
}
for (const [param, id] of Object.entries({username: 'username', employee_code: 'employee-code', secret_key: 'secret-key'})) {
  if (autofillParams.has(param)) document.querySelector(`#${id}`).value = autofillParams.get(param);
}
if (autofillParams.has('location')) {
  savedLocation = autofillParams.get('location');
  coordinates = {};
  document.querySelector('#gps-name').value = '';
}

remember.addEventListener('change', () => {
  if (saveInputs() && !remember.checked) rememberStatus.textContent = 'Đã tắt ghi nhớ. Mật khẩu và SECRET_KEY sẽ được xóa khỏi form sau khi gửi.';
});
form.addEventListener('input', () => { if (remember.checked) saveInputs(); });

async function loadLocations() {
  try {
    const response = await fetch('api/locations');
    if (!response.ok) throw new Error();
    locations = await response.json();
    for (const location of locations) {
      locationSelect.add(new Option(location.label, location.name));
    }
    locationSelect.disabled = false;
    locationStatus.textContent = 'Chọn vị trí để sử dụng tọa độ đã cấu hình.';
    const restored = locations.find(location => location.name === savedLocation);
    if (restored) {
      locationSelect.value = restored.name;
      coordinates = {latitude: restored.latitude, longitude: restored.longitude};
      if (autofillParams.has('location')) document.querySelector('#gps-name').value = restored.name;
      locationStatus.textContent = `Vĩ độ: ${restored.latitude} · Kinh độ: ${restored.longitude}`;
    } else if (savedLocation) {
      coordinates = {};
      locationStatus.textContent = 'Vị trí không có trong cấu hình. Hãy chọn lại vị trí.';
    } else if (coordinates.latitude !== undefined) {
      locationStatus.textContent = `Đã khôi phục GPS: ${coordinates.latitude}, ${coordinates.longitude}`;
    }
  } catch {
    locationStatus.textContent = 'Không tải được danh sách vị trí. Tải lại trang để thử lại.';
  }
}
loadLocations();

locationSelect.addEventListener('change', () => {
  const selected = locations.find(location => location.name === locationSelect.value);
  coordinates = selected ? {latitude: selected.latitude, longitude: selected.longitude} : {};
  document.querySelector('#gps-name').value = selected?.name || '';
  document.querySelector('#gps-status').textContent = 'Không bắt buộc';
  locationStatus.textContent = selected ? `Vĩ độ: ${selected.latitude} · Kinh độ: ${selected.longitude}` : 'Chọn vị trí để sử dụng tọa độ đã cấu hình.';
  if (remember.checked) saveInputs();
});

function updateClock() {
  const now = new Date();
  const parts = new Intl.DateTimeFormat('en-GB', {timeZone: 'Asia/Ho_Chi_Minh', hour: '2-digit', minute: '2-digit', second: '2-digit', hourCycle: 'h23'}).formatToParts(now);
  const part = type => parts.find(p => p.type === type).value;
  document.querySelector('#clock').innerHTML = `${part('hour')}:${part('minute')}<span>:${part('second')}</span>`;
  document.querySelector('#date').textContent = new Intl.DateTimeFormat('vi-VN', {timeZone: 'Asia/Ho_Chi_Minh', weekday: 'long', day: '2-digit', month: 'long', year: 'numeric'}).format(now);
}
updateClock();
setInterval(updateClock, 1000);

document.querySelector('#gps-button').addEventListener('click', () => {
  const status = document.querySelector('#gps-status');
  const button = document.querySelector('#gps-button');
  if (!navigator.geolocation) {
    status.textContent = 'Trình duyệt không hỗ trợ GPS.';
    return;
  }
  status.textContent = 'Đang lấy vị trí…';
  button.disabled = true;
  locationSelect.disabled = true;
  navigator.geolocation.getCurrentPosition(position => {
    coordinates = {latitude: position.coords.latitude, longitude: position.coords.longitude};
    locationSelect.value = '';
    document.querySelector('#gps-name').value = '';
    locationStatus.textContent = 'Đang sử dụng vị trí hiện tại từ GPS.';
    status.textContent = `${coordinates.latitude.toFixed(5)}, ${coordinates.longitude.toFixed(5)}`;
    button.disabled = false;
    locationSelect.disabled = locations.length === 0;
    if (remember.checked) saveInputs();
  }, () => {
    const selected = locations.find(location => location.name === locationSelect.value);
    coordinates = selected ? {latitude: selected.latitude, longitude: selected.longitude} : {};
    status.textContent = 'Không lấy được vị trí. Kiểm tra quyền GPS và dùng HTTPS hoặc localhost.';
    button.disabled = false;
    locationSelect.disabled = locations.length === 0;
  }, {enableHighAccuracy: true, timeout: 10000, maximumAge: 0});
});

form.addEventListener('submit', async event => {
  event.preventDefault();
  if (submit.disabled) return;
  const employeeCode = document.querySelector('#employee-code').value.trim();
  if (!employeeCode) return;
  if (coordinates.latitude === undefined || !document.querySelector('#gps-name').value.trim()) {
    result.hidden = false;
    result.className = 'error';
    result.textContent = 'Chọn vị trí cấu hình hoặc lấy GPS hiện tại và nhập tên GPS trước khi chấm công.';
    return;
  }
  submit.disabled = true;
  document.querySelector('#checkin-fields').disabled = true;
  submit.textContent = 'Đang gửi chấm công…';
  result.hidden = true;
  const body = {
    username: document.querySelector('#username').value.trim(),
    password: document.querySelector('#password').value,
    secret_key: document.querySelector('#secret-key').value.trim(),
    employee_code: employeeCode,
    ...coordinates,
    gps_name: document.querySelector('#gps-name').value.trim(),
  };
  if (remember.checked) saveInputs();
  try {
    body.device = await deviceInfo;
    const response = await fetch('api/checkins', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(body)});
    const data = await response.json();
    if (!response.ok) {
      const detail = data.detail;
      const message = typeof detail === 'string' ? detail : Array.isArray(detail) ? 'Dữ liệu không hợp lệ. Kiểm tra mã nhân viên, thời gian và vị trí.' : `${detail?.message || 'Không gửi được chấm công.'} (Code: ${detail?.code ?? '—'}, SubCode: ${detail?.subcode ?? '—'})`;
      throw new Error(message);
    }
    const formatted = new Intl.DateTimeFormat('vi-VN', {timeZone: 'Asia/Ho_Chi_Minh', dateStyle: 'short', timeStyle: 'medium'}).format(new Date(data.check_time));
    result.className = 'success';
    result.textContent = `Đã ghi nhận chấm công!\nNhân viên: ${data.employee_code}\nThời gian: ${formatted} (UTC+7)`;
    if (data.working_shift_name) result.textContent += `\nCa làm: ${data.working_shift_name}`;
  } catch (error) {
    result.className = 'error';
    result.textContent = error instanceof TypeError || error instanceof SyntaxError ? 'Mất kết nối hoặc phản hồi không hợp lệ; chưa xác định kết quả. Kiểm tra trên AMIS trước khi gửi lại.' : error.message;
  } finally {
    result.hidden = false;
    submit.disabled = false;
    document.querySelector('#checkin-fields').disabled = false;
    if (!remember.checked) {
      document.querySelector('#password').value = '';
      document.querySelector('#secret-key').value = '';
    }
    body.password = '';
    body.secret_key = '';
    submit.textContent = 'Ghi nhận chấm công →';
  }
});
