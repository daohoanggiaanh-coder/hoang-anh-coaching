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


_DANG_TAI: set[str] = set()


def _tai_nen(bang: str) -> None:
    """v2.7: làm mới bảng ở luồng nền — trang vẫn dùng bản cũ (≤ vài chục giây) nên không phải chờ mạng."""
    try:
        got = _fetch(bang)
        if got is not None:
            with _LOCK:
                cu = _CACHE.get(bang)
                # giữ dòng vừa ghi mà bảng tải về chưa kịp có (Apps Script ghi chậm vài giây)
                if cu:
                    da = {(r.get("thoi_gian"), r.get("khoa")) for r in got}
                    got = got + [r for r in cu[1][-20:] if (r.get("thoi_gian"), r.get("khoa")) not in da and r.get("_moi")]
                _CACHE[bang] = (_time.time(), got)
    finally:
        _DANG_TAI.discard(bang)


def rows(bang: str, max_age: float = TTL) -> list[dict]:
    """Mọi dòng thô của 1 bảng (đã đệm). Hết hạn đệm → trả bản cũ ngay + tải lại ở nền (stale-while-revalidate)."""
    assert bang in BANG, bang
    with _LOCK:
        hit = _CACHE.get(bang)
    if hit and _time.time() - hit[0] < max_age:
        return hit[1]
    if hit and _url() and _time.time() - hit[0] < 600:
        if bang not in _DANG_TAI:
            _DANG_TAI.add(bang)
            threading.Thread(target=_tai_nen, args=(bang,), daemon=True).start()
        return hit[1]
    got = _fetch(bang)
    if got is None:
        got = hit[1] if hit else []
    with _LOCK:
        _CACHE[bang] = (_time.time(), got)
    return got


def tai_truoc(bangs: tuple[str, ...] = BANG) -> None:
    """Tải song song các bảng chưa có trong đệm (lần mở web đầu tiên nhanh hơn ~ số bảng lần)."""
    if not _url():
        return
    can = [b for b in bangs if b not in _CACHE]
    if not can:
        return
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=min(8, len(can))) as ex:
        kq = dict(zip(can, ex.map(_fetch, can)))
    with _LOCK:
        for b, got in kq.items():
            if got is not None and b not in _CACHE:
                _CACHE[b] = (_time.time(), got)


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
                _CACHE[bang] = (hit[0], hit[1] + [{**row, "_moi": 1}])
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


_MEMO: dict[tuple, tuple[list, int, dict]] = {}


def latest(bang: str, ma_kh: str | None = None, ca_xoa: bool = False) -> dict[str, dict]:
    """{khoa: bản mới nhất}. ma_kh: chỉ lấy dòng của đúng khách (lọc ở máy chủ — dùng cho trang khách).
    v2.7: nhớ kết quả theo (bảng, khách) — chỉ tính lại khi bảng đổi (1 trang gọi hàm này hàng chục lần)."""
    rs = rows(bang)
    key = (bang, ma_kh, ca_xoa)
    m = _MEMO.get(key)
    if m and m[0] is rs and m[1] == len(rs):
        out = m[2]
    else:
        out = _latest(rs, ma_kh, ca_xoa)
        if len(_MEMO) > 400:
            _MEMO.clear()
        _MEMO[key] = (rs, len(rs), out)
    return {k: dict(v) for k, v in out.items()}          # bản sao nông: trang có sửa dict cũng không làm hỏng bộ nhớ đệm


def _latest(rs: list[dict], ma_kh: str | None, ca_xoa: bool) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for r in rs:
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
