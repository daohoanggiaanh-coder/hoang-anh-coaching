# Hoàng Anh Coaching v2.3 (2026-11-05) — MỘT NGUỒN THÔNG TIN CHUNG cho mọi trang.
"""Hồ sơ khách (bảng KhachHang) là nguồn gốc của: mục tiêu chính (muc_tieu_loai), trình độ (trinh_do), giới tính, chiều cao,
ngày sinh, cân mục tiêu, chấn thương. Trang nào sửa các mục này cũng ghi ngược về hồ sơ khách → trang khác tự cập nhật
(Khách & tài khoản · Hồ sơ khách tự điền · Dinh dưỡng · Giáo án · Volume · Lộ trình)."""
from __future__ import annotations

from core import muc_tieu as mt, store

# mục tiêu chính (5 loại) ↔ mục tiêu dinh dưỡng (4 loại)
SANG_DD = {"giam_mo": "giam_mo", "tang_co": "tang_co", "recomp": "recomp", "suc_khoe": "giu", "suc_manh": "giu"}
TEN = {"giam_mo": "Giảm mỡ, gọn dáng", "tang_co": "Tăng cơ, tăng cân nạc", "recomp": "Săn chắc (giảm mỡ – tăng cơ)",
       "suc_khoe": "Sức khoẻ, giảm đau mỏi", "suc_manh": "Tăng sức mạnh"}
KINH_NGHIEM_TD = {"Chưa tập bao giờ": 0, "Dưới 6 tháng": 0, "6–12 tháng": 1, "1–3 năm": 2, "Trên 3 năm": 3}


def muc_tieu(k: dict) -> str:
    return mt.loai(k)


def tu_dd(muc_dd: str, k: dict) -> str:
    """Mục tiêu dinh dưỡng → mục tiêu chính (giữ 'sức mạnh' nếu khách đang là sức mạnh)."""
    if muc_dd == "giu":
        return muc_tieu(k) if muc_tieu(k) in ("suc_khoe", "suc_manh") else "suc_khoe"
    return muc_dd


def trinh_do(k: dict, mac_dinh: int | None = None) -> int:
    try:
        if str(k.get("trinh_do") or "").strip() != "":
            return max(0, min(4, int(float(k["trinh_do"]))))
    except (TypeError, ValueError):
        pass
    if k.get("kinh_nghiem") in KINH_NGHIEM_TD:
        return KINH_NGHIEM_TD[k["kinh_nghiem"]]
    return 0 if mac_dinh is None else int(mac_dinh)


def dong_bo(k: dict, nguoi: str, **thay) -> bool:
    """Ghi các mục chung về hồ sơ khách (chỉ khi có thay đổi)."""
    k0 = store.client(k["ma"]) or k
    moi = {x: v for x, v in thay.items() if v not in (None, "") and str(k0.get(x) or "") != str(v)}
    if not moi:
        return True
    ok = store.save_client({**k0, **moi}, nguoi)
    if ok:
        k.update(moi)
    return ok
