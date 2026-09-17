"""Telegram delivery: send-only bot (no polling, no inbound commands). Token and chat id come from the environment."""
from __future__ import annotations

import html
import json
import logging
import mimetypes
import os
import urllib.request
import uuid

log = logging.getLogger("po3.notify")
API = "https://api.telegram.org/bot{token}/{method}"
MAX_TEXT = 4096


def _creds() -> tuple[str, str]:
    token, chat = os.environ.get("TELEGRAM_BOT_TOKEN", ""), os.environ.get("TELEGRAM_CHAT_ID", "")
    if not token or not chat:
        raise RuntimeError("TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID not set")
    return token, chat


def esc(s: str) -> str:
    return html.escape(str(s), quote=False)


def send_message(text_html: str) -> None:
    token, chat = _creds()
    if len(text_html) > MAX_TEXT:
        text_html = text_html[: MAX_TEXT - 20] + "\n…(cắt bớt)"
    body = json.dumps({"chat_id": chat, "text": text_html, "parse_mode": "HTML", "disable_web_page_preview": True}).encode()
    req = urllib.request.Request(API.format(token=token, method="sendMessage"), data=body,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        resp = json.loads(r.read())
    if not resp.get("ok"):
        raise RuntimeError(f"telegram sendMessage failed: {resp}")
    log.info("telegram message sent (%d chars)", len(text_html))


def send_document(path: str, caption: str = "") -> None:
    token, chat = _creds()
    boundary = uuid.uuid4().hex
    fname = os.path.basename(path)
    ctype = mimetypes.guess_type(fname)[0] or "application/octet-stream"
    with open(path, "rb") as f:
        data = f.read()
    parts = []
    for k, v in (("chat_id", chat), ("caption", caption[:1024])):
        parts.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"{k}\"\r\n\r\n{v}\r\n".encode())
    parts.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"document\"; filename=\"{fname}\"\r\n"
                 f"Content-Type: {ctype}\r\n\r\n".encode() + data + b"\r\n")
    parts.append(f"--{boundary}--\r\n".encode())
    req = urllib.request.Request(API.format(token=token, method="sendDocument"), data=b"".join(parts),
                                 headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
    with urllib.request.urlopen(req, timeout=120) as r:
        resp = json.loads(r.read())
    if not resp.get("ok"):
        raise RuntimeError(f"telegram sendDocument failed: {resp}")
    log.info("telegram document sent: %s (%d bytes)", fname, len(data))
