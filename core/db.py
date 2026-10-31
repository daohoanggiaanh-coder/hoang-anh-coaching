# Hoàng Anh Coaching v1.0 (2026-10-31) — lưu dữ liệu: Google Sheets riêng (qua Apps Script) hoặc file cục bộ khi chạy thử
"""
Mọi bảng cùng 1 dạng, CHỈ GHI THÊM (không sửa / xoá dòng cũ):
    thoi_gian · khoa · ma_kh · nguoi · du_lieu (JSON)
Đọc: mỗi `khoa` lấy bản ghi mới nhất; du_lieu có "xoa": 1 → coi như đã xoá.

Bảng: KhachHang · TaiKhoan · LichHen · CanNang · SoDo · Anh · GiaoAn · NhatKy · DinhDuong · HangCho

Khách KHÔNG BAO GIỜ gọi thẳng Google Sheets: máy chủ Streamlit đọc rồi lọc đúng mã khách đang đăng nhập.
"""
from __future__ import annotations

import base64
import json
import threading
import time as _time
import uuid
from datetime import datetime, timedelta, timezone

import requests

from core import config

VN_TZ = timezone(timedelta(hours=7))
BANG = ("KhachHang", "TaiKhoan", "LichHen", "CanNang", "SoDo", "Anh", "GiaoAn", "NhatKy", "DinhDuong", "HangCho")
CELL_LIMIT = 45000
TTL = 30


def now_vn() -> datetime:
    return datetime.now(VN_TZ).replace(tzinfo=None)


def now_str() -> str:
    return now_vn().strftime("%Y-%m-%d %H:%M:%S")


def _url() -> str | None:
    return config.get("SHEETS_WEBAPP_URL")


def _token() -> str:
    return str(config.get("SHEETS_TOKEN", "") or "")


def backend() -> str:
    return "Google Sheets" if _url() else "Chạy thử (file cục bộ)"


# ------------------------------------------------------------------ bộ nhớ đệm
_CACHE: dict[str, tuple[float, list[dict]]] = {}
_LOCK = threading.Lock()


def _local_path(bang: str):
    config.LOCAL_DIR.mkdir(parents=True, exist_ok=True)
    return config.LOCAL_DIR / f"{bang}.jsonl"


def _fetch(bang: str) -> list[dict] | None:
    url = _url()
    if not url:
        p = _local_path(bang)
        if not p.exists():
            return []
        return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()]
    try:
        r = requests.get(url, timeout=30, params={"token": _token(), "action": "read", "sheet": bang})
        data = r.json()
    except (requests.RequestException, ValueError):
        return None
    if not data.get("ok"):
        return None
    return list(data.get("rows") or [])


def rows(bang: str, max_age: float = TTL) -> list[dict]:
    """Mọi dòng thô của 1 bảng (đã đệm)."""
    assert bang in BANG, bang
    with _LOCK:
        hit = _CACHE.get(bang)
    if hit and _time.time() - hit[0] < max_age:
        return list(hit[1])
    got = _fetch(bang)
    if got is None:
        got = hit[1] if hit else []
    with _LOCK:
        _CACHE[bang] = (_time.time(), got)
    return list(got)


def clear(bang: str | None = None):
    with _LOCK:
        if bang:
            _CACHE.pop(bang, None)
        else:
            _CACHE.clear()


def append(bang: str, khoa: str, du_lieu: dict, nguoi: str = "", ma_kh: str = "") -> bool:
    assert bang in BANG, bang
    row = {"thoi_gian": now_str(), "khoa": str(khoa), "ma_kh": str(ma_kh or du_lieu.get("ma_kh") or ""),
           "nguoi": str(nguoi or ""), "du_lieu": json.dumps(du_lieu, ensure_ascii=False, default=str)}
    if len(row["du_lieu"]) > CELL_LIMIT:
        return False
    url = _url()
    if url:
        try:
            r = requests.post(url, timeout=30, json={"token": _token(), "action": "append", "sheet": bang, "row": row})
            ok = r.status_code == 200 and '"ok":true' in r.text.replace(" ", "")
        except requests.RequestException:
            ok = False
    else:
        with open(_local_path(bang), "a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
        ok = True
    if ok:
        with _LOCK:
            hit = _CACHE.get(bang)
            if hit:
                _CACHE[bang] = (hit[0], hit[1] + [row])
    return ok


def _parse(r: dict) -> dict | None:
    try:
        v = r.get("du_lieu")
        d = json.loads(v) if isinstance(v, str) else (v or {})
    except (TypeError, ValueError):
        return None
    if not isinstance(d, dict):
        return None
    return {**d, "_khoa": str(r.get("khoa") or ""), "_luc": str(r.get("thoi_gian") or ""),
            "_nguoi": str(r.get("nguoi") or ""), "_ma_kh": str(r.get("ma_kh") or "")}


def latest(bang: str, ma_kh: str | None = None, ca_xoa: bool = False) -> dict[str, dict]:
    """{khoa: bản mới nhất}. ma_kh: chỉ lấy dòng của đúng khách (lọc ở máy chủ — dùng cho trang khách)."""
    out: dict[str, dict] = {}
    for r in rows(bang):
        if ma_kh is not None and str(r.get("ma_kh") or "") != str(ma_kh):
            continue
        d = _parse(r)
        if d is not None:
            out[d["_khoa"]] = d
    if not ca_xoa:
        out = {k: v for k, v in out.items() if str(v.get("xoa") or "") not in ("1", "True", "true")}
    return out


# ------------------------------------------------------------------ ảnh trên Google Drive
_IMG: dict[str, bytes] = {}


def upload_images(files: dict[str, bytes], prefix: str = "") -> dict[str, str] | None:
    if not files:
        return {}
    names = list(files)
    url = _url()
    if url:
        try:
            r = requests.post(url, timeout=90, json={
                "token": _token(), "action": "upload",
                "files": [{"name": f"{prefix}{k}_{now_str()[:10]}.jpg", "data": base64.b64encode(files[k]).decode()}
                          for k in names]})
            data = r.json()
        except (requests.RequestException, ValueError):
            return None
        if not data.get("ok") or len(data.get("ids", [])) != len(names):
            return None
        return dict(zip(names, data["ids"]))
    folder = config.LOCAL_DIR / "anh"
    folder.mkdir(parents=True, exist_ok=True)
    out = {}
    for k in names:
        fid = uuid.uuid4().hex
        (folder / f"{fid}.jpg").write_bytes(files[k])
        out[k] = fid
    return out


def get_images(ids: list[str]) -> dict[str, bytes]:
    ids = list(dict.fromkeys(str(i) for i in ids if i))
    if not ids:
        return {}
    url = _url()
    if url:
        need = [i for i in ids if i not in _IMG]
        for j in range(0, len(need), 20):
            try:
                r = requests.get(url, timeout=90, params={"token": _token(), "action": "images",
                                                          "ids": ",".join(need[j:j + 20])})
                data = r.json()
            except (requests.RequestException, ValueError):
                continue
            for k, v in (data.get("images") or {}).items():
                if len(_IMG) > 300:
                    _IMG.pop(next(iter(_IMG)))
                _IMG[k] = base64.b64decode(v)
        return {i: _IMG[i] for i in ids if i in _IMG}
    folder = config.LOCAL_DIR / "anh"
    return {i: (folder / f"{i}.jpg").read_bytes() for i in ids if (folder / f"{i}.jpg").exists()}
