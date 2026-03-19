from fastapi import APIRouter, HTTPException
import httpx
from bs4 import BeautifulSoup
import re

router = APIRouter(tags=["downloader"])

headers = {
    "user-agent": "Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Mobile Safari/537.36"
}

def normalize(url: str):
    return url.replace("/view/", "/file/")

async def scrape_mediafire(url: str):
    url = normalize(url)

    async with httpx.AsyncClient(timeout=40, follow_redirects=True) as client:
        res = await client.get(url, headers=headers)

    soup = BeautifulSoup(res.text, "html.parser")

    # ambil direct link (WAJIB valid)
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
        raise HTTPException(status_code=404, detail="Direct link tidak ditemukan")

    # file name
    file_name = None
    name_tag = soup.find("div", {"class": "dl-btn-label"})
    if name_tag:
        file_name = name_tag.get("title") or name_tag.text.strip()

    # file size
    file_size = None
    text_all = soup.get_text()
    match = re.search(r"(\\d+(\\.\\d+)?\\s?(KB|MB|GB))", text_all)
    if match:
        file_size = match.group(1)

    return {
        "fileName": file_name or "Unknown File",
        "fileSize": file_size or "Unknown Size",
        "download": download,  # Direct Link
        "source": url
    }


@router.get("/mediafire", summary="MediaFire Direct Link")
async def mediafire_dl(url: str):
    if not url:
        raise HTTPException(status_code=400, detail="URL is required")

    try:
        data = await scrape_mediafire(url)

        return {
            "success": True,
            "result": data
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
