from fastapi import APIRouter, HTTPException, UploadFile, File, Form
import httpx

router = APIRouter(tags=["tools"])

BASE_URL = "https://farel.rf.gd/api"

# HEADER BIAR MIRIP BROWSER
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36",
    "Accept": "*/*",
    "Origin": "https://farel.rf.gd",
    "Referer": "https://farel.rf.gd/",
}

def is_html(res):
    return "text/html" in res.headers.get("content-type", "")

# ===== UPLOAD =====
@router.post("/cdn/upload")
async def upload_file(
    file: UploadFile = File(...),
    custom_name: str = Form(None),
    password: str = Form(None)
):
    try:
        file_bytes = await file.read()

        files = {
            "file": (file.filename, file_bytes, file.content_type)
        }

        data = {}
        if custom_name:
            data["custom_name"] = custom_name
        if password:
            data["password"] = password

        async with httpx.AsyncClient(timeout=60, headers=HEADERS) as client:
            res = await client.post(f"{BASE_URL}/upload.php", files=files, data=data)

        # 🔥 DETEKSI PROTEKSI
        if is_html(res):
            raise HTTPException(
                status_code=403,
                detail="Terblokir oleh proteksi server (anti-bot / JS challenge)"
            )

        return res.json()

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ===== SHORT URL =====
@router.post("/cdn/short")
async def shorten_url(url: str, alias: str = None):
    try:
        payload = {"url": url}
        if alias:
            payload["alias"] = alias

        async with httpx.AsyncClient(timeout=30, headers=HEADERS) as client:
            res = await client.post(
                f"{BASE_URL}/shorten.php",
                json=payload
            )

        if is_html(res):
            raise HTTPException(
                status_code=403,
                detail="Terblokir oleh proteksi server (anti-bot)"
            )

        return res.json()

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ===== LIST FILE =====
@router.get("/cdn/files")
async def list_files():
    async with httpx.AsyncClient(headers=HEADERS) as client:
        res = await client.get(f"{BASE_URL}/files.php")

    if is_html(res):
        raise HTTPException(status_code=403, detail="Blocked by server")

    return res.json()


# ===== LIST URL =====
@router.get("/cdn/urls")
async def list_urls():
    async with httpx.AsyncClient(headers=HEADERS) as client:
        res = await client.get(f"{BASE_URL}/urls.php")

    if is_html(res):
        raise HTTPException(status_code=403, detail="Blocked by server")

    return res.json()
