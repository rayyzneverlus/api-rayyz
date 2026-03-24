from fastapi import APIRouter, HTTPException, UploadFile, File, Form
import httpx

router = APIRouter(tags=["tools"])

BASE_URL = "https://farel.rf.gd/api"

# ===== UPLOAD FILE =====
@router.post("/cdn/upload", summary="Upload File ke Farel CDN")
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

        async with httpx.AsyncClient(timeout=60) as client:
            res = await client.post(f"{BASE_URL}/upload.php", files=files, data=data)

        result = res.json()

        if not result.get("success"):
            raise HTTPException(status_code=500, detail="Upload gagal")

        return {
            "success": True,
            "result": {
                "url": result.get("url"),
                "short_url": result.get("short_url"),
                "size": result.get("size"),
                "type": result.get("mime_type")
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ===== SHORT URL =====
@router.post("/cdn/short", summary="Short URL Farel CDN")
async def shorten_url(url: str, alias: str = None):
    try:
        payload = {
            "url": url
        }

        if alias:
            payload["alias"] = alias

        async with httpx.AsyncClient(timeout=30) as client:
            res = await client.post(
                f"{BASE_URL}/shorten.php",
                json=payload,
                headers={"Content-Type": "application/json"}
            )

        result = res.json()

        if not result.get("success"):
            raise HTTPException(status_code=500, detail="Short URL gagal")

        return {
            "success": True,
            "result": {
                "short_url": result.get("short_url"),
                "original_url": result.get("original_url")
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ===== LIST FILE =====
@router.get("/cdn/files", summary="List File CDN")
async def list_files():
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            res = await client.get(f"{BASE_URL}/files.php")

        return res.json()

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ===== LIST SHORT URL =====
@router.get("/cdn/urls", summary="List Short URL")
async def list_urls():
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            res = await client.get(f"{BASE_URL}/urls.php")

        return res.json()

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
