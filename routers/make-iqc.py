from fastapi import APIRouter, HTTPException
import httpx
import uuid

router = APIRouter(tags=["maker"])

IQC_API = "https://fareldeveloper-iqc.hf.space/api"
ZLR_UPLOAD = "https://zlr.my.id/upload"  # sesuaikan endpoint lu

# ===== UPLOAD KE ZLR =====
async def upload_zlr(buffer: bytes, filename: str):
    try:
        files = {
            "file": (filename, buffer, "image/png")
        }

        async with httpx.AsyncClient(timeout=60) as client:
            res = await client.post(ZLR_UPLOAD, files=files)

        data = res.json()

        # fleksibel (biar ga error beda format)
        return data.get("url") or data.get("result") or data

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload ZLR gagal: {e}")

# ===== ENDPOINT IQC =====
@router.get("/iqc", summary="Generate IQC Image + Upload CDN")
async def iqc_maker(text: str, time: str = "12.00", battery: str = "100"):
    if not text:
        raise HTTPException(status_code=400, detail="Text is required")

    try:
        # build URL
        api_url = f"{IQC_API}?text={text}&time={time}&battery={battery}"

        async with httpx.AsyncClient(timeout=60) as client:
            res = await client.get(api_url)

        if res.status_code != 200:
            raise HTTPException(status_code=500, detail="Gagal generate IQC")

        image_bytes = res.content

        # generate nama file random
        filename = f"iqc_{uuid.uuid4().hex}.png"

        # upload ke CDN lu
        uploaded_url = await upload_zlr(image_bytes, filename)

        return {
            "success": True,
            "creator": "Muhammad Farel",
            "result": {
                "url": uploaded_url,
                "metadata": {
                    "text": text,
                    "time": time,
                    "battery": battery
                }
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
