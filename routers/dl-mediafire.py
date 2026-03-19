from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
import httpx
from bs4 import BeautifulSoup

router = APIRouter(tags=["downloader"])

headers = {
    "user-agent": "Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Mobile Safari/537.36"
}

def normalize(url: str):
    return url.replace("/view/", "/file/")

async def get_direct_link(url: str):
    url = normalize(url)

    async with httpx.AsyncClient(timeout=40, follow_redirects=True) as client:
        res = await client.get(url, headers=headers)

    soup = BeautifulSoup(res.text, "html.parser")

    download = None

    btn = soup.find("a", {"id": "downloadButton"})
    if btn and btn.get("href"):
        download = btn.get("href")

    if not download:
        alt = soup.find("a", {"aria-label": "Download file"})
        if alt:
            download = alt.get("href")

    if not download:
        alt2 = soup.find("a", {"class": "input"})
        if alt2:
            download = alt2.get("href")

    if not download:
        raise HTTPException(status_code=404, detail="Download link not found")

    return download


@router.get("/mediafire", summary="Direct Download MediaFire")
async def mediafire_dl(url: str):
    if not url:
        raise HTTPException(status_code=400, detail="URL is required")

    try:
        direct_url = await get_direct_link(url)

        async def stream():
            async with httpx.AsyncClient(timeout=None) as client:
                async with client.stream("GET", direct_url, headers=headers) as r:
                    async for chunk in r.aiter_bytes():
                        yield chunk

        return StreamingResponse(
            stream(),
            media_type="application/octet-stream",
            headers={
                "Content-Disposition": "attachment"
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
