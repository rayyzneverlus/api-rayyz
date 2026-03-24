from fastapi import APIRouter, HTTPException, UploadFile, File, Form
import httpx

router = APIRouter(tags=["tools"])

BASE = "https://farel.rf.gd"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36",
    "Accept": "*/*",
    "Origin": BASE,
    "Referer": BASE + "/"
}

# ===== BUAT SESSION DULU =====
async def create_client():
    client = httpx.AsyncClient(headers=HEADERS, follow_redirects=True)

    # 🔥 hit homepage biar dapet cookie
    await client.get(BASE)

    return client

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

        client = await create_client()

        res = await client.post(
            f"{BASE}/api/upload.php",
            files=files,
            data=data
        )

        text = res.text

        # 🔥 DETEKSI HTML PROTEKSI
        if "<html" in text.lower():
            raise HTTPException(
                status_code=403,
                detail="Masih kena proteksi (butuh JS execution)"
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

        client = await create_client()

        res = await client.post(
            f"{BASE}/api/shorten.php",
            json=payload
        )

        text = res.text

        if "<html" in text.lower():
            raise HTTPException(
                status_code=403,
                detail="Terblokir proteksi JS"
            )

        return res.json()

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
