from fastapi import APIRouter, HTTPException, UploadFile, File, Form
import cloudscraper
import json

router = APIRouter(tags=["tools"])

BASE = "https://farel.rf.gd/api"

# ===== BUAT SCRAPER =====
def create_scraper():
    scraper = cloudscraper.create_scraper(
        browser={
            'browser': 'chrome',
            'platform': 'windows',
            'mobile': False
        }
    )
    return scraper


# ===== UPLOAD FILE =====
@router.post("/cdn/upload", summary="Upload File (Bypass Proteksi)")
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

        scraper = create_scraper()

        res = scraper.post(
            f"{BASE}/upload.php",
            files=files,
            data=data
        )

        text = res.text

        # 🔥 DETEKSI ERROR HTML
        if "<html" in text.lower():
            raise HTTPException(
                status_code=403,
                detail="Masih kena proteksi / challenge gagal"
            )

        result = res.json()

        return {
            "success": True,
            "result": result
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ===== SHORT URL =====
@router.post("/cdn/short", summary="Short URL (Bypass)")
async def shorten_url(url: str, alias: str = None):
    try:
        payload = {"url": url}
        if alias:
            payload["alias"] = alias

        scraper = create_scraper()

        res = scraper.post(
            f"{BASE}/shorten.php",
            json=payload
        )

        text = res.text

        if "<html" in text.lower():
            raise HTTPException(
                status_code=403,
                detail="Proteksi masih aktif"
            )

        result = res.json()

        return {
            "success": True,
            "result": result
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ===== LIST FILE =====
@router.get("/cdn/files", summary="List Files")
async def list_files():
    try:
        scraper = create_scraper()

        res = scraper.get(f"{BASE}/files.php")

        if "<html" in res.text.lower():
            raise HTTPException(status_code=403, detail="Blocked")

        return res.json()

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ===== LIST URL =====
@router.get("/cdn/urls", summary="List URLs")
async def list_urls():
    try:
        scraper = create_scraper()

        res = scraper.get(f"{BASE}/urls.php")

        if "<html" in res.text.lower():
            raise HTTPException(status_code=403, detail="Blocked")

        return res.json()

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
