# Atlas Academy v3.28 (2026-10-14) — xử lý ảnh: thu nhỏ ảnh điện thoại, cắt khung, tự cắt ảnh đại diện từ ảnh tư thế
"""
- shrink(): ảnh điện thoại 4–8 MB → JPEG ≤ 1400 px (báo cáo PDF nhẹ, tải nhanh).
- crop_ratio(): cắt giữa theo tỉ lệ (ảnh khách đặt cạnh ảnh mẫu 4:3 cho đều).
- face_crop(): tìm khuôn mặt bằng YuNet (OpenCV, chạy offline) → ảnh vuông quanh đầu.
  Không thấy mặt → lấy vùng đầu theo vị trí thường gặp của ảnh đứng toàn thân.
- to_b64()/from_b64(): ảnh đại diện nhỏ (≈ 10 KB) lưu được vào 1 ô Google Sheets.
"""
from __future__ import annotations

import base64
import io

from PIL import Image, ImageOps

from core import config

MODEL = config.ROOT / "assets" / "models" / "face_detection_yunet_2023mar.onnx"


def _open(data: bytes) -> Image.Image:
    im = Image.open(io.BytesIO(data))
    im = ImageOps.exif_transpose(im)          # ảnh iPhone chụp dọc có cờ xoay
    return im.convert("RGB")


def _jpg(im: Image.Image, q: int = 82) -> bytes:
    out = io.BytesIO()
    im.save(out, "JPEG", quality=q, optimize=True)
    return out.getvalue()


def shrink(data: bytes, side: int = 1400) -> bytes:
    try:
        im = _open(data)
    except Exception:  # noqa: BLE001 — file hỏng: trả nguyên
        return data
    im.thumbnail((side, side), Image.LANCZOS)
    return _jpg(im)


def crop_ratio(data: bytes, rw: float = 4, rh: float = 3, side: int = 900) -> bytes:
    im = _open(data)
    w, h = im.size
    if w / h > rw / rh:
        nw = int(h * rw / rh)
        im = im.crop(((w - nw) // 2, 0, (w - nw) // 2 + nw, h))
    else:
        nh = int(w * rh / rw)
        top = max(0, min(h - nh, int((h - nh) * 0.35)))   # ảnh dọc: lệch lên trên một chút
        im = im.crop((0, top, w, top + nh))
    im.thumbnail((side, side), Image.LANCZOS)
    return _jpg(im)


def find_face(im: Image.Image):
    """(x, y, w, h) khuôn mặt rõ nhất hoặc None."""
    try:
        import cv2
        import numpy as np
    except ImportError:
        return None
    if not MODEL.exists():
        return None
    arr = cv2.cvtColor(np.asarray(im), cv2.COLOR_RGB2BGR)
    h, w = arr.shape[:2]
    try:
        det = cv2.FaceDetectorYN.create(str(MODEL), "", (w, h), 0.6)
        det.setInputSize((w, h))
        faces = det.detect(arr)[1]
    except Exception:  # noqa: BLE001
        return None
    if faces is None or not len(faces):
        return None
    best = max(faces, key=lambda f: f[2] * f[3] * f[-1])
    return tuple(int(v) for v in best[:4])


def face_crop(data: bytes, side: int = 220) -> tuple[bytes, bool]:
    """Ảnh vuông quanh khuôn mặt. Trả (jpeg, có_tìm_thấy_mặt)."""
    im = _open(data)
    im.thumbnail((1400, 1400), Image.LANCZOS)
    w, h = im.size
    f = find_face(im)
    if f:
        x, y, fw, fh = f
        cx, cy = x + fw / 2, y + fh * 0.55
        s = max(fw, fh) * 2.1                 # lấy cả tóc, cằm, một chút vai
    else:                                     # ảnh đứng toàn thân: đầu ở khoảng 3–15 % chiều cao
        cx, cy, s = w / 2, h * 0.11, min(w, h) * 0.32
    s = min(s, w, h)
    x0 = int(max(0, min(w - s, cx - s / 2)))
    y0 = int(max(0, min(h - s, cy - s / 2)))
    out = im.crop((x0, y0, x0 + int(s), y0 + int(s))).resize((side, side), Image.LANCZOS)
    return _jpg(out, 80), bool(f)


def to_b64(data: bytes, side: int = 160) -> str:
    im = _open(data)
    im.thumbnail((side, side), Image.LANCZOS)
    return base64.b64encode(_jpg(im, 78)).decode()


def from_b64(s) -> bytes | None:
    if not s or not isinstance(s, str) or len(s) < 100:
        return None
    try:
        return base64.b64decode(s)
    except ValueError:
        return None


def data_uri(data: bytes | None) -> str:
    return "data:image/jpeg;base64," + base64.b64encode(data).decode() if data else ""
