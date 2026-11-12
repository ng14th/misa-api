from pathlib import Path

import httpx
from fastapi import Depends, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from auto_checkin import CheckInRequest, run_workflow
from constant import location

ROOT = Path(__file__).resolve().parent
app = FastAPI(title="MISA Auto Checkin", version="2.0.0")
app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")


@app.exception_handler(RequestValidationError)
async def validation_error(request: Request, exc: RequestValidationError):
    # Do not echo credential input in validation errors.
    return JSONResponse(status_code=422, content={"detail": [
        {"loc": error["loc"], "type": error["type"], "msg": "Dữ liệu không hợp lệ."}
        for error in exc.errors()
    ]})


@app.middleware("http")
async def prevent_caching(request: Request, call_next):
    response = await call_next(request)
    response.headers["Cache-Control"] = "no-store"
    return response


async def get_http_client():
    async with httpx.AsyncClient(timeout=20.0) as client:
        yield client


@app.get("/", include_in_schema=False)
async def home():
    return FileResponse(ROOT / "static" / "index.html")


@app.get("/healthz", include_in_schema=False)
async def health():
    return {"status": "ok"}


@app.get("/api/locations")
async def locations():
    return [
        {"name": name, "label": location.MAPPING_NAME_LOCALTION.get(name, name),
         "latitude": coordinates[0], "longitude": coordinates[1]}
        for name, coordinates in vars(location).items()
        if name.isupper() and isinstance(coordinates, tuple) and len(coordinates) == 2
    ]


@app.post("/api/checkins")
async def check_in(entry: CheckInRequest, client: httpx.AsyncClient = Depends(get_http_client)):
    return await run_workflow(entry, client)
