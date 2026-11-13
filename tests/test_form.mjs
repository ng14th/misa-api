import assert from 'node:assert/strict';
import fs from 'node:fs';
import test from 'node:test';
import vm from 'node:vm';

const script = fs.readFileSync(new URL('../static/app.js', import.meta.url), 'utf8');

async function setup(storage = new Map(), failRequest = false, blockStorage = false, browserInfo = {userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) Safari/605.1.15', platform: 'MacIntel'}, url = 'https://example.test/misa/') {
  const elements = new Map();
  const element = selector => {
    if (!elements.has(selector)) elements.set(selector, {
      value: '', checked: false, disabled: false, textContent: '', listeners: {}, options: [],
      classList: {toggle() {}, add() {}},
      addEventListener(type, handler) { this.listeners[type] = handler; },
      add(option) { this.options.push(option); },
      setAttribute(name, value) { this[name] = value; },
    });
    return elements.get(selector);
  };
  element('#password').type = 'password';
  let sent;
  const context = vm.createContext({
    document: {querySelector: element}, Intl, Date, setInterval() {}, navigator: browserInfo,
    window: {location: new URL(url)}, URLSearchParams,
    Option: function(text, value) { this.text = text; this.value = value; },
    localStorage: {
      getItem: key => storage.get(key) ?? null,
      setItem(key, value) { if (blockStorage) throw new Error(); storage.set(key, value); },
      removeItem(key) { if (blockStorage) throw new Error(); storage.delete(key); },
    },
    fetch: async (url, options) => {
      if (url === 'api/locations') return {ok: true, json: async () => [{name: 'VP', label: 'Văn phòng', latitude: 10, longitude: 106}]};
      sent = JSON.parse(options.body);
      if (failRequest) throw new TypeError('network');
      return {ok: true, json: async () => ({employee_code: 'NV1', check_time: '2026-11-12T08:00:00+07:00'})};
    },
  });
  vm.runInContext(script, context);
  await new Promise(setImmediate);
  const fill = () => {
    for (const [id, value] of Object.entries({username: 'account', password: 'test-password', 'secret-key': 'test-secret', 'employee-code': 'NV1'})) element(`#${id}`).value = value;
    element('#location').value = 'VP';
    element('#location').listeners.change();
  };
  return {element, fill, submit: () => element('#checkin-form').listeners.submit({preventDefault() {}}), sent: () => sent};
}

test('opt-in remembers every field and restores location and credentials on reload', async () => {
  const storage = new Map();
  const first = await setup(storage);
  first.fill();
  assert.equal(storage.size, 0);
  first.element('#remember-inputs').checked = true;
  first.element('#remember-inputs').listeners.change();
  // Input edits after enabling remember must also persist.
  first.element('#password').value = 'updated-password';
  first.element('#checkin-form').listeners.input();
  await first.submit();
  assert.equal(first.element('#password').value, 'updated-password');
  const restored = await setup(storage);
  for (const id of ['username', 'password', 'secret-key', 'employee-code', 'gps-name', 'location']) {
    assert.equal(restored.element(`#${id}`).value, first.element(`#${id}`).value);
  }
  await restored.submit();
  assert.equal(restored.sent().latitude, 10);
  assert.equal(restored.sent().longitude, 106);
  restored.element('#remember-inputs').checked = false;
  restored.element('#remember-inputs').listeners.change();
  assert.equal(storage.size, 0);
  await restored.submit();
  assert.equal(restored.element('#password').value, '');
  assert.equal(restored.element('#secret-key').value, '');
});

test('without remember, network errors clear secrets and never write storage', async () => {
  const storage = new Map();
  const page = await setup(storage, true);
  page.fill();
  await page.submit();
  assert.equal(page.element('#password').value, '');
  assert.equal(page.element('#secret-key').value, '');
  assert.equal(storage.size, 0);
});

test('URL parameters autofill mobile credentials and configured location without submitting', async () => {
  const storage = new Map();
  const page = await setup(storage, false, false, undefined,
    'https://example.test/misa/?username=%2B84901234567&employee_code=NV%2001&location=VP#secret_key=TEST%20KEY');
  assert.equal(page.element('#username').value, '+84901234567');
  assert.equal(page.element('#employee-code').value, 'NV 01');
  assert.equal(page.element('#secret-key').value, 'TEST KEY');
  assert.equal(page.element('#location').value, 'VP');
  assert.equal(page.element('#gps-name').value, 'VP');
  assert.equal(page.element('#password').value, '');
  assert.equal(page.sent(), undefined);
  assert.equal(storage.size, 0);
  page.element('#password').value = 'test-password';
  await page.submit();
  assert.equal(page.sent().latitude, 10);
  assert.equal(page.sent().longitude, 106);
  assert.equal(page.sent().gps_name, 'VP');
  assert.equal(page.sent().username, '+84901234567');
  assert.equal(page.sent().employee_code, 'NV 01');
  assert.equal(page.sent().secret_key, 'TEST KEY');
});

test('URL values override remembered fields and fragment overrides query', async () => {
  const storage = new Map();
  const first = await setup(storage);
  first.fill();
  first.element('#remember-inputs').checked = true;
  first.element('#remember-inputs').listeners.change();
  const page = await setup(storage, false, false, undefined,
    'https://example.test/misa/?username=query&employee_code=NEW&secret_key=QUERY#username=fragment&secret_key=');
  assert.equal(page.element('#username').value, 'fragment');
  assert.equal(page.element('#employee-code').value, 'NEW');
  assert.equal(page.element('#secret-key').value, '');
  assert.equal(page.element('#password').value, 'test-password');
  assert.equal(page.element('#location').value, 'VP');
});

test('unknown or empty URL location clears remembered GPS and blocks check-in', async () => {
  for (const location of ['UNKNOWN', '']) {
    const storage = new Map();
    const first = await setup(storage);
    first.fill();
    first.element('#remember-inputs').checked = true;
    first.element('#remember-inputs').listeners.change();
    const page = await setup(storage, false, false, undefined,
      `https://example.test/misa/?location=${location}`);
    assert.equal(page.element('#gps-name').value, '');
    await page.submit();
    assert.equal(page.sent(), undefined);
    assert.equal(page.element('#result').className, 'error');
  }
});

test('storage failures are displayed honestly for save and removal', async () => {
  const page = await setup(new Map(), false, true);
  page.fill();
  for (const checked of [true, false]) {
    page.element('#remember-inputs').checked = checked;
    page.element('#remember-inputs').listeners.change();
    assert.match(page.element('#remember-status').textContent, /không cho phép/);
  }
});

test('desktop sends browser-reported device and actual user agent', async () => {
  const page = await setup();
  page.fill();
  await page.submit();
  assert.deepEqual(page.sent().device, {
    name: 'MacIntel', os: 'macOS', os_version: '14.0', device_type: 'Desktop',
    user_agent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) Safari/605.1.15',
  });
});

test('password visibility toggles without changing value or submitting', async () => {
  const page = await setup();
  page.fill();
  const password = page.element('#password');
  const toggle = page.element('#toggle-password');
  toggle.listeners.click();
  assert.equal(password.type, 'text');
  assert.equal(password.value, 'test-password');
  assert.equal(toggle['aria-pressed'], 'true');
  assert.equal(toggle['aria-label'], 'Ẩn mật khẩu');
  toggle.listeners.click();
  assert.equal(password.type, 'password');
  assert.equal(password.value, 'test-password');
  assert.equal(toggle['aria-pressed'], 'false');
  assert.equal(page.sent(), undefined);
});

test('Client Hints supplies model and platform version for smartphone', async () => {
  const browser = {
    userAgent: 'Mozilla/5.0 (Linux; Android 10) Mobile', platform: 'Linux armv8l',
    userAgentData: {platform: 'Android', mobile: true, async getHighEntropyValues() {
      return {model: 'Reported model', platformVersion: '16.0.0'};
    }},
  };
  const page = await setup(new Map(), false, false, browser);
  page.fill();
  await page.submit();
  assert.deepEqual(page.sent().device, {
    name: 'Reported model', os: 'Android', os_version: '16.0.0', device_type: 'Smartphone', user_agent: browser.userAgent,
  });
});

test('restricted Client Hints falls back to browser platform without inventing model', async () => {
  const browser = {
    userAgent: 'Mozilla/5.0 (Linux; Android 14) Mobile', platform: 'Linux armv8l',
    userAgentData: {platform: 'Android', mobile: true, async getHighEntropyValues() { throw new Error('blocked'); }},
  };
  const page = await setup(new Map(), false, false, browser);
  page.fill();
  await page.submit();
  assert.equal(page.sent().device.name, 'Linux armv8l');
  assert.equal(page.sent().device.os_version, '14');
  assert.equal(page.sent().device.device_type, 'Smartphone');
});

test('iPad desktop user agent with touch reports Tablet', async () => {
  const page = await setup(new Map(), false, false, {
    userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15) Safari/605.1.15',
    platform: 'MacIntel', maxTouchPoints: 5,
  });
  page.fill();
  await page.submit();
  assert.equal(page.sent().device.device_type, 'Tablet');
  assert.equal(page.sent().device.os, 'iOS');
  assert.equal(page.sent().device.os_version, '');
});
