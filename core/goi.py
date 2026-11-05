# Hoàng Anh Coaching v2.2 (2026-11-05) — GÓI KHÁCH: giá, thanh toán / công nợ, ngày bắt đầu – kết thúc, bảo lưu, khoá truy cập.
"""Lưu ngay trong hồ sơ khách (bảng KhachHang), không thêm trang tính:
  ngay_ket_thuc  — HLV tự đặt (để trống = tính từ gói: bắt đầu + số tuần / tháng)
  thanh_toan     — [{ngay, so_tien, ghi_chu}]
  bao_luu        — [{tu, den, ly_do}] — mỗi ngày bảo lưu cộng thêm 1 ngày vào hạn gói; trong thời gian bảo lưu không xếp lịch,
                   khách không vào web
  cho_vao        — True: HLV cho khách vào web dù gói đã hết (VD đang gia hạn, chờ chuyển khoản)
Luật khoá: Ngưng tập · đang bảo lưu · quá ngày kết thúc · gói buổi đã dùng hết buổi → khách không đăng nhập được."""
from __future__ import annotations

import json
import re
from datetime import date, timedelta

from core import db, store


def _ds(v) -> list[dict]:
    try:
        v = json.loads(v) if isinstance(v, str) and v.strip() else (v or [])
        return [x for x in v if isinstance(x, dict)]
    except (TypeError, ValueError):
        return []


def tien(v) -> int:
    """'6.000.000', '6tr', '2tr5', 6000000 → số đồng."""
    if isinstance(v, (int, float)):
        return int(v)
    s = str(v or "").lower().replace(" ", "").replace("đ", "").replace("vnd", "")
    m = re.fullmatch(r"(\d+)(?:tr|triệu)(\d*)", s)
    if m:
        dv = m.group(2)
        return int(m.group(1)) * 1_000_000 + (int(dv) * 10 ** (6 - len(dv)) if dv else 0)
    m = re.fullmatch(r"(\d+)(?:k|nghìn|ngàn)", s)
    if m:
        return int(m.group(1)) * 1000
    so = re.sub(r"[^\d]", "", s)
    return int(so) if so else 0


def vnd(x: float) -> str:
    return f"{x:,.0f} đ".replace(",", ".")


def thanh_toan(k: dict) -> list[dict]:
    return sorted(_ds(k.get("thanh_toan")), key=lambda x: str(x.get("ngay")))


def bao_luu(k: dict) -> list[dict]:
    out = []
    for x in _ds(k.get("bao_luu")):
        tu, den = store._d(x.get("tu")), store._d(x.get("den"))
        if tu and den and den >= tu:
            out.append({**x, "tu": tu, "den": den, "ngay": (den - tu).days + 1})
    return sorted(out, key=lambda x: x["tu"])


def cong_no(k: dict) -> dict:
    gia = tien(k.get("gia"))
    da = sum(tien(x.get("so_tien")) for x in thanh_toan(k))
    return {"gia": gia, "da_tra": da, "con_no": max(gia - da, 0), "du": max(da - gia, 0)}


def ngay_bat_dau(k: dict) -> date | None:
    return store._d(k.get("ngay_bat_dau"))


def ngay_ket_thuc(k: dict) -> date | None:
    """Ngày cuối được tập: HLV tự đặt, hoặc tính từ gói tuần / tháng (+ số ngày bảo lưu)."""
    tay = store._d(k.get("ngay_ket_thuc"))
    if tay:
        return tay
    h = store.han_goi(k)
    if not h:
        return None
    return h - timedelta(days=1) + timedelta(days=sum(x["ngay"] for x in bao_luu(k)))


def dang_bao_luu(k: dict, hom: date) -> dict | None:
    return next((x for x in bao_luu(k) if x["tu"] <= hom <= x["den"]), None)


def trang_thai(k: dict, hom: date | None = None, H: dict | None = None) -> dict:
    """{ma, ten, mau, vao (khách vào web được không), ly_do}."""
    hom = hom or db.now_vn().date()
    bl = dang_bao_luu(k, hom)
    kt = ngay_ket_thuc(k)
    con = store.con_lai(k, H)
    tt = k.get("trang_thai") or "Đang tập"
    if tt == "Ngưng tập":
        out = ("ngung", "Ngưng tập", "#8b8577", False, "Khoá tập đã kết thúc.")
    elif bl:
        out = ("bao_luu", f"Bảo lưu đến {bl['den']:%d/%m}", "#6B4BA3", False,
               f"Gói đang bảo lưu từ {bl['tu']:%d/%m/%Y} đến {bl['den']:%d/%m/%Y}.")
    elif kt and hom > kt:
        out = ("het_han", f"Hết hạn {kt:%d/%m}", "#B4442F", False, f"Gói đã hết hạn ngày {kt:%d/%m/%Y}.")
    elif con is not None and con <= 0:
        out = ("het_buoi", "Hết buổi", "#B4442F", False, "Gói đã dùng hết số buổi.")
    elif kt and (kt - hom).days <= 7:
        out = ("sap_het", f"Còn {(kt - hom).days + 1} ngày", "#E08A3C", True, "")
    elif con is not None and con <= 2:
        out = ("sap_het", f"Còn {con} buổi", "#E08A3C", True, "")
    elif ngay_bat_dau(k) and hom < ngay_bat_dau(k):
        out = ("chua_bd", f"Bắt đầu {ngay_bat_dau(k):%d/%m}", "#4B6A88", True, "")
    else:
        out = ("dang", "Đang tập", "#2E7D4F", True, "")
    ma, ten, mau, vao, ly_do = out
    if not vao and k.get("cho_vao") and ma != "ngung":
        vao, ten = True, ten + " · HLV mở tạm"
    return {"ma": ma, "ten": ten, "mau": mau, "vao": vao, "ly_do": ly_do}


def ngay_bao_luu(k: dict, d: date) -> bool:
    return any(x["tu"] <= d <= x["den"] for x in bao_luu(k))


def luu(k: dict, thay: dict, nguoi: str) -> bool:
    return store.save_client({**k, **thay}, nguoi)
