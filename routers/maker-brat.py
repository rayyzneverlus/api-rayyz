from fastapi import APIRouter, HTTPException
import httpx
import random

router = APIRouter(tags=["maker"])

BRAT_API = "https://fareldeveloper-brat.hf.space/api"
ZLR_UPLOAD = "https://zlr.my.id/upload"

def generate_filename(prefix: str, ext: str = "png"):
    rand = random.randint(100000, 999999)
    return f"{prefix}-{rand}.{ext}"

async def upload_zlr(buffer: bytes, filename: str, folder: str):
    try:
        files = {
            "file": (filename, buffer, "image/png")
        }

        data = {
            "path": f"/maker/{folder}"
        }

        async with httpx.AsyncClient(timeout=60) as client:
            res = await client.post(ZLR_UPLOAD, files=files, data=data)

        result = res.json()
        return result.get("url") or result.get("result") or result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/brat", summary="Brat Maker + Folder CDN")
async def brat_maker(text: str):
    if not text:
        raise HTTPException(status_code=400, detail="Text is required")

    try:
        api_url = f"{BRAT_API}?text={text}"

        async with httpx.AsyncClient(timeout=60) as client:
            res = await client.get(api_url)

        if res.status_code != 200:
            raise HTTPException(status_code=500, detail="Gagal generate brat")

        filename = generate_filename("brat")

        uploaded = await upload_zlr(res.content, filename, "brat")

        return {
            "success": True,
            "result": {
                "url": uploaded,
                "path": f"/maker/brat/{filename}"
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
