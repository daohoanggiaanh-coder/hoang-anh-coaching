# Atlas Academy v3.28 (2026-10-14) — lớp gọi AI dùng chung cho mọi nhà cung cấp
"""
Một hàm duy nhất `chat()` cho 3 nhà cung cấp (gọi thẳng REST, không cần SDK):
  - gemini    : Google AI Studio — có gói MIỄN PHÍ (khuyên dùng để chạy 0 đồng)
  - anthropic : Claude API — trả theo token, chất lượng tiếng Việt tốt nhất
  - openai    : OpenAI API — trả theo token
  - offline   : không có key → app vẫn chạy bằng kịch bản soạn sẵn + chấm theo luật
"""
from __future__ import annotations

import base64
import json
import re
import time

import requests

from core import config

DEFAULT_MODELS = {
    "gemini": "gemini-flash-latest",   # bí danh luôn trỏ tới bản Flash mới nhất của Google
    "anthropic": "claude-haiku-4-5-20251001",
    "openai": "gpt-4o-mini",
}
TIMEOUT = 60


class LLMError(RuntimeError):
    pass


def provider() -> str:
    p = (config.get("LLM_PROVIDER") or "").strip().lower()
    if p in {"gemini", "anthropic", "openai", "offline"}:
        return p
    # tự nhận diện theo key đã khai báo
    if config.get("GEMINI_API_KEY"):
        return "gemini"
    if config.get("ANTHROPIC_API_KEY"):
        return "anthropic"
    if config.get("OPENAI_API_KEY"):
        return "openai"
    return "offline"


def is_online() -> bool:
    return provider() != "offline"


_RESOLVED: dict[str, str] = {}   # model Gemini tự dò được khi model cấu hình bị Google khai tử


def model_name() -> str:
    p = provider()
    return _RESOLVED.get(p) or config.get("LLM_MODEL") or DEFAULT_MODELS.get(p, "offline")


_MODEL_LIST: dict[str, object] = {}   # bộ nhớ tạm danh sách model Gemini (1 giờ)


def _gemini_models(exclude: str = "") -> list[str]:
    """Danh sách model Gemini key này dùng được, xếp theo ưu tiên: Flash/Pro mới nhất trước,
    bản Lite xếp cuối (chỉ dùng dự phòng khi Google quá tải)."""
    now = time.time()
    if not _MODEL_LIST or now - _MODEL_LIST["t"] > 3600:
        try:
            r = requests.get("https://generativelanguage.googleapis.com/v1beta/models?pageSize=200",
                             timeout=20, headers={"x-goog-api-key": config.get("GEMINI_API_KEY", "")})
        except requests.RequestException:
            return []
        if r.status_code != 200:
            return []
        _MODEL_LIST.update(t=now, names=[m["name"].split("/", 1)[-1] for m in r.json().get("models", [])
                                         if "generateContent" in m.get("supportedGenerationMethods", [])])
    names = _MODEL_LIST["names"]
    want = "pro" if "pro" in (config.get("LLM_MODEL") or "") else "flash"
    bad = ("image", "tts", "audio", "live", "thinking", "exp", "preview", "embedding", "learnlm")

    def ver(n):
        m = re.match(r"gemini-(\d+)(?:\.(\d+))?", n)
        return (int(m.group(1)), int(m.group(2) or 0)) if m else (0, 0)
    ok = [n for n in names if n.startswith("gemini-") and n != exclude and not any(x in n for x in bad)]
    main = sorted([n for n in ok if want in n and "lite" not in n], key=lambda n: (ver(n), "latest" in n), reverse=True)
    other = sorted([n for n in ok if "flash" in n and n not in main], key=lambda n: ("lite" in n, [-v for v in ver(n)]))
    return main + other


def _gemini_pick_model(exclude: str) -> str | None:
    c = _gemini_models(exclude)
    return c[0] if c else None


def _normalize(messages: list[dict]) -> list[dict]:
    """Chuẩn hoá hội thoại: bắt đầu bằng user, không có 2 lượt liền cùng vai."""
    out: list[dict] = []
    for m in messages:
        role = "assistant" if m["role"] == "assistant" else "user"
        text = str(m["content"]).strip()
        if not text:
            continue
        if out and out[-1]["role"] == role:
            out[-1]["content"] += "\n" + text
        else:
            out.append({"role": role, "content": text})
    if not out or out[0]["role"] != "user":
        out.insert(0, {"role": "user", "content": "(Bắt đầu)"})
    return out


def chat(system: str, messages: list[dict], *, json_mode: bool = False,
         temperature: float = 0.7, max_tokens: int = 1200, images: list[bytes] | None = None,
         timeout: int | None = None) -> str:
    """images: ảnh JPEG gắn vào lượt user cuối (đọc phiếu InBody...). timeout: giây chờ mỗi lần gọi (ảnh chữ viết tay cần lâu hơn)."""
    p = provider()
    if p == "offline":
        raise LLMError("Chưa cấu hình API key — đang chạy chế độ offline.")
    msgs = _normalize(messages)
    try:
        if p == "gemini":
            return _gemini(system, msgs, json_mode, temperature, max_tokens, images, timeout)
        if p == "anthropic":
            return _anthropic(system, msgs, json_mode, temperature, max_tokens, images)
        return _openai(system, msgs, json_mode, temperature, max_tokens, images)
    except requests.RequestException as e:
        raise LLMError(f"Lỗi kết nối {p}: {e}") from e


BUSY = {429, 500, 503, 504}   # Google quá tải / lỗi tạm thời → thử lại
RETRY_WAIT = 2                 # giây chờ trước khi thử lại
GEMINI_TIMEOUT = 30            # mỗi lần gọi chờ tối đa 30 giây
GEMINI_DEADLINE = 80           # tổng thời gian tối đa cho 1 câu trả lời (kể cả thử lại)
_NO_THINK_CFG: set[str] = set()  # model không nhận tham số giảm "suy nghĩ"


class _Timeout:
    status_code = 0
    text = "timeout"


def _gemini_post(model, body, timeout=None):
    b = dict(body)
    if "flash" in model and not model.startswith("gemini-3") and model not in _NO_THINK_CFG:
        # Gemini 2.5 Flash / flash-latest: tắt "suy nghĩ" (nhanh hơn, không ăn mất phần chữ trả lời)
        g = body["generationConfig"]
        b["generationConfig"] = {**g, "thinkingConfig": {"thinkingBudget": 0}}
    elif model.startswith("gemini-3") and model not in _NO_THINK_CFG:
        # model Gemini 3 mặc định "suy nghĩ" rất lâu → hạ xuống mức thấp để trả lời nhanh
        # phần "suy nghĩ" cũng tính vào giới hạn chữ → cộng thêm để câu trả lời không bị cụt
        g = body["generationConfig"]
        b["generationConfig"] = {**g, "maxOutputTokens": g["maxOutputTokens"] + 2048,
                                 "thinkingConfig": {"thinkingLevel": "low"}}
    try:
        r = requests.post(f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
                          json=b, timeout=timeout or GEMINI_TIMEOUT,
                          headers={"x-goog-api-key": config.get("GEMINI_API_KEY", "")})
    except (requests.Timeout, requests.ConnectionError):
        return _Timeout()
    if r.status_code == 400 and "thinking" in r.text.lower() and "thinkingConfig" in b["generationConfig"]:
        _NO_THINK_CFG.add(model)
        return _gemini_post(model, body, timeout)
    return r


def _b64(b: bytes) -> str:
    return base64.b64encode(b).decode()


def _gemini(system, msgs, json_mode, temperature, max_tokens, images=None, timeout=None):
    body = {
        "system_instruction": {"parts": [{"text": system}]},
        "contents": [{"role": "model" if m["role"] == "assistant" else "user",
                      "parts": [{"text": m["content"]}]} for m in msgs],
        "generationConfig": {"temperature": temperature, "maxOutputTokens": max_tokens},
    }
    for im in images or []:
        body["contents"][-1]["parts"].insert(0, {"inline_data": {"mime_type": "image/jpeg", "data": _b64(im)}})
    if json_mode:
        body["generationConfig"]["responseMimeType"] = "application/json"

    start = time.monotonic()
    model = model_name()
    to = timeout or GEMINI_TIMEOUT
    deadline = max(GEMINI_DEADLINE, to * 2 + 10)
    r = _gemini_post(model, body, to)
    if r.status_code == 404:
        # model đã bị Google ngừng/không có cho key này → tự chọn model khác (nhớ luôn)
        new = _gemini_pick_model(exclude=model)
        if new:
            _RESOLVED["gemini"] = model = new
            r = _gemini_post(model, body, to)

    def busy(x):
        return x.status_code in BUSY or isinstance(x, _Timeout)

    # quá tải / quá chậm: thử lại 1 lần, rồi mượn tạm tối đa 2 model dự phòng
    queue = [model] + _gemini_models(exclude=model)[:2] if busy(r) else []
    for i, m in enumerate(queue):
        if not busy(r) or time.monotonic() - start > deadline - to:
            break
        if i == 0:
            time.sleep(RETRY_WAIT)
        r = _gemini_post(m, body, to)
    if isinstance(r, _Timeout):
        raise LLMError("Google Gemini đang phản hồi quá chậm (đã tự thử lại và đổi model dự phòng). "
                       "Chờ khoảng 1 phút rồi gửi lại câu trả lời.")
    if r.status_code in BUSY:
        raise LLMError("Máy chủ Google Gemini đang quá tải (đã tự thử lại và đổi model dự phòng). "
                       "Chờ khoảng 1 phút rồi gửi lại câu trả lời.")
    if r.status_code != 200:
        raise LLMError(f"Gemini {r.status_code}: {r.text[:300]}")
    data = r.json()
    try:
        parts = data["candidates"][0]["content"]["parts"]
        text = "".join(p.get("text", "") for p in parts if not p.get("thought")).strip()
    except (KeyError, IndexError) as e:
        raise LLMError(f"Gemini trả về rỗng: {str(data)[:300]}") from e
    if not text:
        raise LLMError("Gemini trả về rỗng — thử gửi lại.")
    return text


def _anthropic(system, msgs, json_mode, temperature, max_tokens, images=None):
    sys_text = system + ("\n\nCHỈ trả về một object JSON hợp lệ, không thêm chữ nào khác."
                         if json_mode else "")
    if images:
        msgs = msgs[:-1] + [{"role": "user", "content": [
            *({"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": _b64(im)}} for im in images),
            {"type": "text", "text": msgs[-1]["content"]}]}]
    r = requests.post(
        "https://api.anthropic.com/v1/messages",
        timeout=TIMEOUT,
        headers={"x-api-key": config.get("ANTHROPIC_API_KEY", ""),
                 "anthropic-version": "2023-06-01",
                 "content-type": "application/json"},
        json={"model": model_name(), "max_tokens": max_tokens, "temperature": temperature,
              "system": sys_text, "messages": msgs},
    )
    if r.status_code != 200:
        raise LLMError(f"Claude {r.status_code}: {r.text[:300]}")
    return "".join(b.get("text", "") for b in r.json().get("content", [])).strip()


def _openai(system, msgs, json_mode, temperature, max_tokens, images=None):
    if images:
        msgs = msgs[:-1] + [{"role": "user", "content": [
            *({"type": "image_url", "image_url": {"url": "data:image/jpeg;base64," + _b64(im)}} for im in images),
            {"type": "text", "text": msgs[-1]["content"]}]}]
    body = {"model": model_name(), "temperature": temperature, "max_tokens": max_tokens,
            "messages": [{"role": "system", "content": system}] + msgs}
    if json_mode:
        body["response_format"] = {"type": "json_object"}
    r = requests.post("https://api.openai.com/v1/chat/completions", json=body,
                      timeout=TIMEOUT,
                      headers={"Authorization": f"Bearer {config.get('OPENAI_API_KEY', '')}"})
    if r.status_code != 200:
        raise LLMError(f"OpenAI {r.status_code}: {r.text[:300]}")
    return r.json()["choices"][0]["message"]["content"].strip()


def parse_json(text: str) -> dict:
    """Bóc JSON kể cả khi model bọc trong ```json ... ``` hoặc thêm chữ thừa."""
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    start, end = text.find("{"), text.rfind("}")
    if start != -1 and end > start:
        return json.loads(text[start:end + 1])
    raise LLMError("AI không trả về JSON hợp lệ.")


def chat_json(system: str, messages: list[dict], **kw) -> dict:
    raw = chat(system, messages, json_mode=True, temperature=kw.pop("temperature", 0.2), **kw)
    try:
        return parse_json(raw)
    except (json.JSONDecodeError, LLMError):
        # thử lại 1 lần, nhắc model sửa định dạng
        raw = chat(system, messages + [{"role": "assistant", "content": raw},
                                       {"role": "user", "content": "Trả lại đúng JSON hợp lệ."}],
                   json_mode=True, temperature=0.0, **kw)
        return parse_json(raw)
