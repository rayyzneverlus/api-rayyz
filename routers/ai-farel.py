import base64
import json
import os
import random
import re
from typing import Optional
from fastapi import APIRouter, HTTPException
import httpx
from Crypto.Cipher import PKCS1_v1.5
from Crypto.PublicKey import RSA

router = APIRouter(tags=["ai"])

API = "https://aga-api.aichatting.net/aigc/chat/v2/professional/stream"
SESSION_FILE = "./aichatting-session.json"
MODEL = "gpt-4o-mini"
FORCE_NEW_SESSION = True

PUBLIC_KEY_BASE64 = (
    "MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQDCAdf/EyIbLBxjGqmh7qLU6/CPCzru+75+8"
    "2OSPZ+nf4BFvg88drpZ6KigNW0J8TNgxe6Yms1irCZNVDyu+RXsl4y/7c2KOHc4OGTzHB5fUM"
    "iMasFUvcEs2P70e6yA/sKHZfBLG1XPhlb84Ibs3nhD3W5e2SuC+4EuVkaqzN08LQIDAQAB"
)

UA = (
    "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/147.0.0.0 Mobile Safari/537.36"
)


def make_public_key():
    # Membungkus public key per 64 karakter seperti pada Node.js
    wrapped = "\n".join(
        PUBLIC_KEY_BASE64[i : i + 64] for i in range(0, len(PUBLIC_KEY_BASE64), 64)
    )
    return f"-----BEGIN PUBLIC KEY-----\n{wrapped}\n-----END PUBLIC KEY-----"


def encrypt_visitor_id(visitor_id: str) -> str:
    try:
        key_text = make_public_key()
        pub_key = RSA.import_key(key_text)
        cipher = PKCS1_v1.5.new(pub_key)
        encrypted = cipher.encrypt(visitor_id.encode("utf-8"))
        return base64.b64encode(encrypted).decode("utf-8")
    except Exception as e:
        raise Exception(f"Encryption failed: {str(e)}")


def make_visitor_id() -> str:
    return os.urandom(16).hex()


def make_conversation_id() -> int:
    return random.randint(10000000, 99999999)


def get_mime_type_from_path(file_path: str) -> str:
    ext = os.path.splitext(file_path)[1].lower()
    if ext in [".jpg", ".jpeg"]:
        return "image/jpeg"
    if ext == ".png":
        return "image/png"
    raise HTTPException(
        status_code=400,
        detail="Format gambar tidak didukung. Gunakan JPG/JPEG/PNG saja.",
    )


def get_mime_type_from_url(image_url: str, content_type: str = "") -> str:
    mime_type = content_type.split(";")[0].strip().lower()
    if mime_type in ["image/jpeg", "image/png"]:
        return mime_type

    clean_url = image_url.split("?")[0].lower()
    if clean_url.endswith(".jpg") or clean_url.endswith(".jpeg"):
        return "image/jpeg"
    if clean_url.endswith(".png"):
        return "image/png"
    raise HTTPException(
        status_code=400,
        detail="Format gambar URL tidak didukung. Gunakan JPG/JPEG/PNG saja.",
    )


async def url_to_data_url(image_url: str) -> str:
    headers = {
        "user-agent": UA,
        "accept": "image/jpeg,image/png,*/*;q=0.8",
        "referer": "https://www.google.com/",
    }
    async with httpx.AsyncClient(timeout=30) as client:
        try:
            res = await client.get(image_url, headers=headers)
            if res.status_code != 200:
                raise Exception(f"Status code {res.status_code}")
        except Exception as e:
            raise HTTPException(
                status_code=400, detail=f"Gagal download image URL: {str(e)}"
            )

    content_type = res.headers.get("content-type", "")
    mime = get_mime_type_from_url(image_url, content_type)
    b64_data = base64.b64encode(res.content).decode("utf-8")
    return f"data:{mime};base64,{b64_data}"


def create_new_session():
    visitor_id = make_visitor_id()
    return {
        "visitorId": visitor_id,
        "vtoken": encrypt_visitor_id(visitor_id),
        "conversationId": make_conversation_id(),
        "messages": [],
    }


async def load_session() -> dict:
    if FORCE_NEW_SESSION:
        return create_new_session()

    if not os.path.exists(SESSION_FILE):
        return create_new_session()

    try:
        with open(SESSION_FILE, "r", encoding="utf-8") as f:
            session = json.load(f)

        if "visitorId" not in session:
            session["visitorId"] = make_visitor_id()
        if "vtoken" not in session:
            session["vtoken"] = encrypt_visitor_id(session["visitorId"])
        if "conversationId" not in session:
            session["conversationId"] = make_conversation_id()
        if "messages" not in session or not isinstance(session["messages"], list):
            session["messages"] = []

        return session
    except:
        return create_new_session()


def save_session(session: dict):
    if FORCE_NEW_SESSION:
        return
    try:
        with open(SESSION_FILE, "w", encoding="utf-8") as f:
            json.dump(session, f, indent=2, ensure_ascii=False)
    except:
        pass


def create_user_content(prompt: str, image_data_url: str = "") -> list:
    content = [{"type": "text", "text": prompt}]
    if image_data_url:
        content.append({"type": "image_url", "image_url": {"url": image_data_url}})
    return content


def clean_answer(text: str) -> str:
    text = String = text or ""
    text = re.sub(r"-=-\s*--", " ", text)
    text = text.replace("--@DONE@--", "")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


@router.get("/farel", summary="AI Chatting Scraping Endpoint")
async def farel_ai(
    prompt: str, image: Optional[str] = None, imageurl: Optional[str] = None
):
    if not prompt:
        raise HTTPException(status_code=400, detail="Prompt wajib diisi")

    session = await load_session()
    image_data_url = ""

    # Prioritaskan local image path (jika ada file lokal), lalu imageurl
    if image and os.path.exists(image):
        try:
            mime = get_mime_type_from_path(image)
            with open(image, "rb") as img_file:
                b64_data = base64.b64encode(img_file.read()).decode("utf-8")
                image_data_url = f"data:{mime};base64,{b64_data}"
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Gagal membaca file gambar: {str(e)}")
    elif imageurl:
        image_data_url = await url_to_data_url(imageurl)

    user_message = {
        "role": "user",
        "content": create_user_content(prompt, image_data_url),
    }

    # Ambil 12 pesan terakhir untuk history bawaan request
    history_messages = session["messages"][-12:] if session["messages"] else []
    body = {
        "spaceHandle": True,
        "roleId": 0,
        "messages": history_messages + [user_message],
        "conversationId": session["conversationId"],
        "model": MODEL,
    }

    headers = {
        "sec-ch-ua-platform": '"Android"',
        "lang": "en",
        "sec-ch-ua": '"Google Chrome";v="147", "Not.A/Brand";v="8", "Chromium";v="147"',
        "sec-ch-ua-mobile": "?1",
        "vtoken": session["vtoken"],
        "source": "web",
        "user-agent": UA,
        "accept": "text/event-stream,application/json, text/event-stream",
        "content-type": "application/json",
        "origin": "https://www.aichatting.net",
        "referer": "https://www.aichatting.net/",
        "sec-fetch-site": "same-site",
        "sec-fetch-mode": "cors",
        "sec-fetch-dest": "empty",
        "accept-language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
        "priority": "u=1, i",
    }

    async with httpx.AsyncClient(timeout=60) as client:
        try:
            # Karena aslinya stream, di backend python kita baca per baris (SSE stream chunks)
            async with client.stream(
                "POST", API, headers=headers, json=body
            ) as response:
                if response.status_code != 200:
                    error_text = await response.aread()
                    return {
                        "status": False,
                        "code": response.status_code,
                        "question": prompt,
                        "answer": "",
                        "error": error_text.decode("utf-8", errors="ignore"),
                    }

                raw_answer = ""
                async for line in response.aiter_lines():
                    line = line.strip()
                    if not line.startswith("data:"):
                        continue

                    data_content = line[5:]  # hapus 'data:'
                    if not data_content.strip() or "--@DONE@--" in data_content:
                        continue

                    raw_answer += data_content

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Sistem Error: {str(e)}")

    answer = clean_answer(raw_answer)

    if answer:
        session["messages"].append(user_message)
        session["messages"].append(
            {"role": "assistant", "content": [{"type": "text", "text": answer}]}
        )
        # Batasi log lokal maksimal 20 pesan
        session["messages"] = session["messages"][-20:]
        save_session(session)

    return {
        "status": bool(answer),
        "code": 200,
        "question": prompt,
        "answer": answer,
    }
