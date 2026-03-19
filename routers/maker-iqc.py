from fastapi import APIRouter, HTTPException
import httpx
import uuid
import random

router = APIRouter(tags=["maker"])

IQC_API = "https://fareldeveloper-iqc.hf.space/api"
ZLR_UPLOAD = "https://zlr.my.id/upload"  # sesuaikan API lu

# generate nama random tapi readable
def generate_filename(prefix: str, ext: str = "png"):
    rand = random.randint(100000, 999999)
    return f"{prefix}-{rand}.{ext}"

# upload ke zlr dengan folder
async def upload_zlr(buffer: bytes, filename: str, folder: str):
    try:
        files = {
            "file": (filename, buffer, "image/png")
        }

        data = {
            "path": f"/maker/{folder}"  # 🔥 folder custom
        }

        async with httpx.AsyncClient(timeout=60) as client:
            res = await client.post(ZLR_UPLOAD, files=files, data=data)

        result = res.json()

        return result.get("url") or result.get("result") or result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload gagal: {e}")

# endpoint iqc
@router.get("/iqc", summary="IQC Maker + Folder CDN")
async def iqc_maker(text: str, time: str = "12.00", battery: str = "100"):
    if not text:
        raise HTTPException(status_code=400, detail="Text is required")

    try:
        api_url = f"{IQC_API}?text={text}&time={time}&battery={battery}"

        async with httpx.AsyncClient(timeout=60) as client:
            res = await client.get(api_url)

        if res.status_code != 200:
            raise HTTPException(status_code=500, detail="Gagal generate IQC")

        image_bytes = res.content

        filename = generate_filename("iqc")

        uploaded = await upload_zlr(image_bytes, filename, "iqc")

        return {
            "success": True,
            "result": {
                "url": uploaded,
                "path": f"/maker/iqc/{filename}"
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
