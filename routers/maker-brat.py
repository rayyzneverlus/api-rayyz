from fastapi import APIRouter, HTTPException
import httpx

router = APIRouter(tags=["maker"])

BRAT_API = "https://fareldeveloper-brat.hf.space/api"

@router.get("/brat", summary="Generate Brat Image")
async def brat_maker(text: str):
    if not text:
        raise HTTPException(status_code=400, detail="Text is required")

    try:
        url = f"{BRAT_API}?text={text}"

        async with httpx.AsyncClient(timeout=60) as client:
            res = await client.get(url)

        if res.status_code != 200:
            raise HTTPException(status_code=500, detail="Failed generate brat")

        return {
            "success": True,
            "result": {
                "type": "image",
                "direct": url
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
