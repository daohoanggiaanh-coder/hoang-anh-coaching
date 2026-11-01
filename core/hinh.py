# Hoàng Anh Coaching v1.8 (2026-11-01) — ảnh đại diện (khách: tự cắt từ ảnh đầu khoá · HLV: ảnh tải lên),
# hồ sơ HLV và thành quả học viên (transform) cho khách xem.
from __future__ import annotations

import base64
import io
import uuid

from core import db, tien_do as td

KHOA_HLV = "hlv|ho_so"


# ------------------------------------------------------------------ cắt ảnh tròn
def cat_vuong(data: bytes, y_pct: float = 14, rong_pct: float = 62, canh: int = 320) -> bytes | None:
    """Cắt ô vuông quanh khuôn mặt: ảnh toàn thân thường có mặt ở ~10–20 % chiều cao từ trên xuống.
    y_pct = tâm ô cắt theo % chiều cao, rong_pct = cạnh ô theo % chiều rộng ảnh."""
    try:
        from PIL import Image, ImageOps
        im = ImageOps.exif_transpose(Image.open(io.BytesIO(data))).convert("RGB")
    except Exception:  # noqa: BLE001
        return None
    w, h = im.size
    c = max(40, min(w, h, int(w * rong_pct / 100)))
    cy = int(h * y_pct / 100)
    top = max(0, min(h - c, cy - c // 2))
    left = max(0, (w - c) // 2)
    im = im.crop((left, top, left + c, top + c)).resize((canh, canh))
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=84)
    return buf.getvalue()


def data_uri(b: bytes | None) -> str:
    return "data:image/jpeg;base64," + base64.b64encode(b).decode() if b else ""


_CACHE: dict[tuple, str] = {}


def _uri(anh_id: str, y: float, r: float, cat: bool = True) -> str:
    key = (anh_id, y, r, cat)
    if key not in _CACHE:
        raw = db.get_images([anh_id]).get(anh_id)
        _CACHE[key] = data_uri(cat_vuong(raw, y, r) if cat else raw) if raw else ""
        if len(_CACHE) > 200:
            _CACHE.pop(next(iter(_CACHE)))
    return _CACHE[key]


# ------------------------------------------------------------------ ảnh đại diện khách
def anh_goc_khach(k: dict) -> str | None:
    """Id ảnh dùng làm đại diện: ảnh HLV chọn riêng, nếu không có → ảnh mặt trước đợt đầu khoá."""
    if k.get("anh_dai_dien"):
        return str(k["anh_dai_dien"])
    ds = td.anh(k["ma"])
    if not ds:
        return None
    bo = td.bo_anh(ds, True)
    v = bo.get("truoc") or next(iter(bo.values()), None)
    return v["id"] if v else None


def avatar_khach(k: dict) -> str:
    i = anh_goc_khach(k)
    if not i:
        return ""
    y = float(k.get("avatar_y") or 14)
    r = float(k.get("avatar_r") or 62)
    return _uri(i, y, r, cat=not k.get("anh_dai_dien_vuong"))


def chu_cai(ten: str) -> str:
    p = [x for x in str(ten or "").split() if x]
    return (p[-1][:1] if p else "?").upper()


def the_avatar(uri: str, ten: str, size: int = 56, vien: str = "#C8A24A") -> str:
    if uri:
        return (f'<img src="{uri}" style="width:{size}px;height:{size}px;border-radius:50%;object-fit:cover;'
                f'border:2px solid {vien};flex:none" alt="">')
    return (f'<div style="width:{size}px;height:{size}px;border-radius:50%;background:#2a251d;color:#E8C76A;display:grid;'
            f'place-items:center;font-weight:800;font-size:{size * .42:.0f}px;border:2px solid {vien};flex:none">{chu_cai(ten)}</div>')


# ------------------------------------------------------------------ hồ sơ HLV
MAC_DINH_HLV = {"ten": "Hoàng Anh", "chuc_danh": "Huấn luyện viên cá nhân · Founder Atlas Fitness",
                "gioi_thieu": "", "chung_chi": [], "zalo": "", "anh": "", "y": 30, "r": 70}


def ho_so_hlv() -> dict:
    v = db.latest("DinhDuong").get(KHOA_HLV) or {}
    return {**MAC_DINH_HLV, **{k: x for k, x in v.items() if not k.startswith("_")}}


def luu_ho_so_hlv(hs: dict, nguoi: str) -> bool:
    return db.append("DinhDuong", KHOA_HLV, hs, nguoi)


def avatar_hlv(hs: dict | None = None) -> str:
    hs = hs or ho_so_hlv()
    return _uri(hs["anh"], float(hs.get("y") or 30), float(hs.get("r") or 70)) if hs.get("anh") else ""


# ------------------------------------------------------------------ thành quả học viên
def transforms(ca_an: bool = False) -> list[dict]:
    ds = [v for k, v in db.latest("DinhDuong").items() if k.startswith("transform|") and not v.get("xoa")]
    if not ca_an:
        ds = [v for v in ds if v.get("hien") and v.get("dong_y")]
    return sorted(ds, key=lambda v: (int(v.get("thu_tu") or 99), str(v.get("_luc", ""))))


def luu_transform(t: dict, nguoi: str) -> bool:
    tid = t.get("id") or f"transform|{uuid.uuid4().hex[:8]}"
    return db.append("DinhDuong", tid, {**{k: v for k, v in t.items() if not k.startswith("_")}, "id": tid}, nguoi)


def xoa_transform(tid: str, nguoi: str) -> bool:
    return db.append("DinhDuong", tid, {"id": tid, "xoa": 1}, nguoi)


def anh_full(anh_id: str) -> str:
    return _uri(anh_id, 0, 0, cat=False) if anh_id else ""
