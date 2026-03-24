from fastapi import APIRouter, HTTPException, UploadFile, File, Form
import httpx

router = APIRouter(tags=["tools"])

BASE_URL = "https://farel.rf.gd/api"

# ===== SAFE JSON PARSER =====
def safe_json(res):
    try:
        return res.json()
    except:
        return {
            "success": False,
            "raw": res.text[:300]  # ambil sebagian biar ga kepanjangan
        }

# ===== UPLOAD FILE =====
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

        async with httpx.AsyncClient(timeout=60) as client:
            res = await client.post(f"{BASE_URL}/upload.php", files=files, data=data)

        result = safe_json(res)

        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=f"Upload gagal | Status: {res.status_code} | Response: {result}"
            )

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ===== SHORT URL =====
@router.post("/cdn/short")
async def shorten_url(url: str, alias: str = None):
    try:
        payload = {"url": url}
        if alias:
            payload["alias"] = alias

        async with httpx.AsyncClient(timeout=30) as client:
            res = await client.post(
                f"{BASE_URL}/shorten.php",
                json=payload,
                headers={"Content-Type": "application/json"}
            )

        result = safe_json(res)

        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=f"Short URL gagal | Status: {res.status_code} | Response: {result}"
            )

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ===== LIST FILE =====
@router.get("/cdn/files")
async def list_files():
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            res = await client.get(f"{BASE_URL}/files.php")

        return safe_json(res)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ===== LIST URL =====
@router.get("/cdn/urls")
async def list_urls():
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            res = await client.get(f"{BASE_URL}/urls.php")

        return safe_json(res)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
