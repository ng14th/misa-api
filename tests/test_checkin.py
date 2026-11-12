import base64
import json

import httpx
import pytest
from fastapi.testclient import TestClient

from main import app, get_http_client

USER = {
    "UserID": "user-1",
    "TenantID": "tenant-1",
    "SessionID": "session-1",
    "EmployeeCode": "NV1",
}
SHIFT = {
    "ChallengeToken": "challenge",
    "WorkingShiftID": 7,
    "WorkingShiftCode": "HC",
    "WorkingShiftName": "Hành chính",
}
ENTRY = {
    "username": "account",
    "password": "private-password",
    "secret_key": "JBSWY3DPEHPK3PXP",
    "employee_code": "NV1",
    "gps_name": "VPTRAKHUC",
    "latitude": 10.805939,
    "longitude": 106.665093,
    "device": {
        "name": "MacIntel",
        "os": "macOS",
        "os_version": "14.0",
        "device_type": "Desktop",
        "user_agent": "test-browser/1.0",
    },
}


@pytest.fixture
def client():
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


def mock_misa(handler):
    async def dependency():
        async with httpx.AsyncClient(
            transport=httpx.MockTransport(handler)
        ) as client:
            yield client

    app.dependency_overrides[get_http_client] = dependency


@pytest.mark.parametrize(
    "otp_mode", [None, "subcode8", "old_token", "string_token"]
)
def test_request_credentials_login_shift_submit(client, otp_mode):
    calls = []

    def handler(request):
        path = request.url.path
        calls.append(path)
        assert request.headers["DeviceName"] == "MacIntel"
        assert request.headers["DeviceOS"] == "macOS"
        assert request.headers["OSVersion"] == "14.0"
        assert request.headers["DeviceType"] == "Desktop"
        assert request.headers["User-Agent"] == "test-browser/1.0"
        if path.endswith("/account/login"):
            assert json.loads(request.content) == {
                "UserName": "account",
                "Password": "private-password",
            }
            assert "x-sessionid" not in request.headers
            if otp_mode == "subcode8":
                return httpx.Response(
                    200,
                    json={
                        "Success": False,
                        "SubCode": 8,
                        "Data": {"AccessToken": {"Token": "otp-token"}},
                    },
                )
            if otp_mode:
                return httpx.Response(
                    200,
                    json={
                        "Success": True,
                        "Data": {"Token": "otp-token"}
                        if otp_mode == "old_token"
                        else "otp-token",
                    },
                )
            return httpx.Response(
                200, json={"Success": True, "Data": {"User": USER}}
            )
        if path.endswith("/Account/loginwithotp"):
            payload = json.loads(request.content)
            assert payload["Token"] == "otp-token"
            assert len(payload["OTP"]) == 6 and payload["OTP"].isdigit()
            return httpx.Response(
                200, json={"Success": True, "Data": {"User": USER}}
            )
        assert request.headers["x-sessionid"] == "session-1"
        if path.endswith("/validate-working-shift"):
            return httpx.Response(200, json={"Success": True, "Data": SHIFT})
        assert request.url.params["userId"] == "user-1"
        payload = json.loads(request.content)
        assert payload["IsMobile"] is False
        assert payload["GPSName"] == "VPTRAKHUC"
        assert payload["Latitude"] == ENTRY["latitude"]
        assert payload["Longitude"] == ENTRY["longitude"]
        assert (
            base64.b64decode(payload["ResponseToken"])
            .decode()
            .startswith("challenge_MISA-AMIS-TK-PROD")
        )
        return httpx.Response(
            200,
            json={
                "Success": True,
                "Data": {"CheckTime": "2026-11-12T08:00:00+07:00"},
            },
        )

    mock_misa(handler)
    for _ in range(2):
        response = client.post("/api/checkins", json=ENTRY)
        assert response.status_code == 200
        assert response.json()["employee_code"] == "NV1"
        assert response.json()["working_shift_name"] == "Hành chính"
        assert "session-1" not in response.text
    assert len(calls) == (8 if otp_mode else 6)


@pytest.mark.parametrize(
    "failure",
    [
        "login",
        "otp",
        "shift",
        "face",
        "employee",
        "submit",
        "timeout",
        "json",
        "missing_time",
    ],
)
def test_failure_stops_workflow_without_retry_or_leaking_secrets(
    client, failure
):
    calls = []

    def handler(request):
        path = request.url.path
        calls.append(path)
        if path.endswith("/account/login"):
            if failure == "login":
                return httpx.Response(
                    200,
                    json={"Success": False, "UserMessage": "private-password"},
                )
            if failure == "otp":
                return httpx.Response(
                    200, json={"Success": True, "Data": {"Token": "otp-token"}}
                )
            return httpx.Response(
                200,
                json={
                    "Success": True,
                    "Data": {
                        "User": {
                            **USER,
                            "EmployeeCode": "OTHER"
                            if failure == "employee"
                            else "NV1",
                        }
                    },
                },
            )
        if path.endswith("/Account/loginwithotp"):
            return httpx.Response(200, json={"Success": False})
        if path.endswith("/validate-working-shift"):
            return httpx.Response(
                200,
                json={
                    "Success": failure != "shift",
                    "Data": {
                        **SHIFT,
                        "IsRequireFaceIdentifi": failure == "face",
                    },
                },
            )
        if failure == "timeout":
            raise httpx.ReadTimeout("private-password", request=request)
        if failure == "json":
            return httpx.Response(200, text="private-password")
        return httpx.Response(
            200, json={"Success": failure != "submit", "Data": {}}
        )

    mock_misa(handler)
    response = client.post("/api/checkins", json=ENTRY)
    assert response.status_code == (
        409
        if failure in ("face", "employee")
        else 504
        if failure == "timeout"
        else 502
    )
    assert "private-password" not in response.text
    assert len(calls) == len(set(calls))
    if failure in ("login", "otp", "shift", "face", "employee"):
        assert not any(
            path.endswith("/timekeeping-now-token") for path in calls
        )


@pytest.mark.parametrize(
    "changes",
    [
        {"employee_code": ""},
        {"password": ""},
        {"username": " "},
        {"latitude": 91},
        {"longitude": None},
        {"gps_name": ""},
        {"password": {"secret": "private-password"}},
        {"device": None},
        {
            "device": {
                **ENTRY["device"],
                "user_agent": "bad\r\nInjected: header",
            }
        },
    ],
)
def test_invalid_request_does_not_echo_credentials_or_contact_misa(
    client, changes
):
    mock_misa(
        lambda request: pytest.fail("Invalid data must not contact MISA")
    )
    response = client.post("/api/checkins", json={**ENTRY, **changes})
    assert response.status_code == 422
    assert "private-password" not in response.text
    assert ENTRY["secret_key"] not in response.text


@pytest.mark.parametrize(
    "device_type, mobile",
    [("Smartphone", True), ("Tablet", True), ("Desktop", False)],
)
def test_device_from_request_controls_headers_and_mobile_flag(
    client, device_type, mobile
):
    def handler(request):
        assert request.headers["DeviceName"] == "Reported device"
        assert request.headers["DeviceType"] == device_type
        assert request.headers["User-Agent"] == "current-browser/2.0"
        assert "OSVersion" not in request.headers
        if request.url.path.endswith("/account/login"):
            return httpx.Response(
                200, json={"Success": True, "Data": {"User": USER}}
            )
        if request.url.path.endswith("/validate-working-shift"):
            return httpx.Response(200, json={"Success": True, "Data": SHIFT})
        assert json.loads(request.content)["IsMobile"] is mobile
        return httpx.Response(
            200,
            json={
                "Success": True,
                "Data": {"CheckTime": "2026-11-12T08:00:00+07:00"},
            },
        )

    mock_misa(handler)
    assert (
        client.post(
            "/api/checkins",
            json={
                **ENTRY,
                "device": {
                    **ENTRY["device"],
                    "name": "Reported device",
                    "device_type": device_type,
                    "os_version": "",
                    "user_agent": "current-browser/2.0",
                },
            },
        ).status_code
        == 200
    )


@pytest.mark.parametrize("secret", ["", "not base32!!", "123456"])
def test_otp_requires_valid_form_secret(client, secret):
    calls = []

    def handler(request):
        calls.append(request)
        return httpx.Response(
            200, json={"Success": True, "Data": {"Token": "otp-token"}}
        )

    mock_misa(handler)
    assert (
        client.post(
            "/api/checkins", json={**ENTRY, "secret_key": secret}
        ).status_code
        == 422
    )
    assert len(calls) == 1


@pytest.mark.parametrize(
    "secret", ["jbswy3dpehpk3pxp", " JBSW Y3DP\nEHPK\t3PXP "]
)
def test_totp_accepts_grouped_or_lowercase_keys(client, monkeypatch, secret):
    import pyotp

    monkeypatch.setattr(pyotp.TOTP, "now", lambda self: self.at(0))
    expected = pyotp.TOTP(ENTRY["secret_key"]).at(0)
    calls = []

    def handler(request):
        calls.append(request)
        if request.url.path.endswith("/account/login"):
            return httpx.Response(
                200, json={"Success": True, "Data": {"Token": "otp-token"}}
            )
        assert json.loads(request.content)["OTP"] == expected
        return httpx.Response(200, json={"Success": False})

    mock_misa(handler)
    response = client.post(
        "/api/checkins", json={**ENTRY, "secret_key": secret}
    )
    assert (
        response.status_code == 502
    )  # Mock rejection proves the OTP step was reached.
    assert len(calls) == 2


def test_locations_home_and_no_old_api(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    for field in ("username", "password", "secret-key", "employee-code"):
        assert f'id="{field}"' in response.text
    assert client.get("/api/locations").json()[0]["label"] == "VP Trà Khúc"
    assert client.get("/api/status").status_code == 404
    assert client.post("/api/mobile/checkins", json=ENTRY).status_code == 404


def test_proxy_prefix_keeps_assets_api_and_health_accessible():
    with TestClient(app, root_path="/misa") as client:
        home = client.get("/misa/")
        assert 'href="static/style.css"' in home.text
        assert 'src="static/app.js"' in home.text
        assert client.get("/misa/static/app.js").status_code == 200
        assert client.get("/misa/api/locations").status_code == 200
        assert client.get("/misa/healthz").json() == {"status": "ok"}
