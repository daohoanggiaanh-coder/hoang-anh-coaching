# Atlas Academy v3.64 (2026-10-22) — tiến độ đạt mục tiêu của khách PT: so mục tiêu với InBody / số đo (chỉ quản lý + PT xem)
"""
Mục tiêu đo được của khách:
- loại mục tiêu: ô `muc_tieu_loai` (mã trong tu_van.GOALS); để trống → đoán từ chữ ở ô Mục tiêu.
- con số đích: `muc_tieu_can` (kg) · `muc_tieu_mo` (% mỡ) · `muc_tieu_co` (khối cơ SMM, kg) · `muc_tieu_eo` (vòng eo, cm),
  hạn `muc_tieu_ngay`. Ô nào để trống → tự đặt mục tiêu 12 tuần an toàn từ lần đo đầu:
  cân giảm 6 % (≈ 0,5 %/tuần) · % mỡ giảm 4 điểm (không thấp hơn mức khoẻ: nam 15 %, nữ 23 %) · eo giảm 5 cm ·
  cơ tăng 1,5 kg (mục tiêu tăng cơ: 2 kg) · cân tăng 3 % khi tăng cơ · mỡ nội tạng về ≤ 9.
- % hoàn thành = (hiện tại − ban đầu) ÷ (đích − ban đầu). So với % thời gian đã qua tới hạn → đúng / chậm tiến độ.
"""
from __future__ import annotations

from datetime import date, timedelta

import pandas as pd

from core import tu_van as tv

TUAN_MAC_DINH = 12
CHI_SO = {  # mã: (tên, đơn vị, số lẻ)
    "can_nang": ("Cân nặng", "kg", 1), "pbf": ("% mỡ", "%", 1), "smm": ("Khối cơ (SMM)", "kg", 1),
    "v_eo": ("Vòng eo", "cm", 1), "mo_noi_tang": ("Mỡ nội tạng", "", 0),
}
THEO_LOAI = {   # loại mục tiêu → các chỉ số theo dõi (chỉ số đầu là chính)
    "giam_mo": ["pbf", "can_nang", "v_eo", "mo_noi_tang"],
    "tang_co": ["smm", "can_nang", "pbf"],
    "recomp": ["pbf", "smm", "v_eo"],
    "suc_khoe": ["v_eo", "mo_noi_tang", "pbf"],
    "suc_manh": ["smm", "pbf"],
}
O_DICH = {"can_nang": "muc_tieu_can", "pbf": "muc_tieu_mo", "smm": "muc_tieu_co", "v_eo": "muc_tieu_eo"}


def doan_loai(text: str) -> str:
    t = str(text or "").lower()
    if "săn" in t or ("mỡ" in t and "cơ" in t and "tăng" in t):
        return "recomp"
    if any(w in t for w in ("tăng cơ", "tăng cân", "to lên", "cơ bắp", "body")):
        return "tang_co"
    if any(w in t for w in ("sức mạnh", "khoẻ hơn", "khỏe hơn", "nâng tạ")):
        return "suc_manh"
    if any(w in t for w in ("đau", "sức khoẻ", "sức khỏe", "huyết áp", "tiểu đường", "xương", "khớp")):
        return "suc_khoe"
    return "giam_mo"


def loai(k: dict) -> str:
    v = str(k.get("muc_tieu_loai") or "").strip()
    return v if v in THEO_LOAI else doan_loai(k.get("muc_tieu"))


def _d(v) -> date | None:
    try:
        return date.fromisoformat(str(v)[:10])
    except ValueError:
        return None


def _dich_mac_dinh(ma: str, goc: float, lo: str, nu: bool) -> float | None:
    if ma == "can_nang":
        return round(goc * (1.03 if lo == "tang_co" else 0.94), 1)
    if ma == "pbf":
        san = 23.0 if nu else 15.0
        return round(max(goc - 4, san), 1) if goc > san else round(goc - 1, 1)
    if ma == "smm":
        return round(goc + (2.0 if lo == "tang_co" else 1.5), 1)
    if ma == "v_eo":
        return round(goc - 5, 1)
    if ma == "mo_noi_tang":
        return min(9.0, goc - 2) if goc > 9 else None
    return None


def du_doan(s: pd.DataFrame, ma: str, dich: float, today: date) -> dict:
    """v3.64: tốc độ thay đổi thật (hồi quy tuyến tính các lần đo) → ngày dự kiến đạt đích nếu giữ nhịp hiện tại.
    {toc_do_tuan, du_kien (date | None), dung_huong (bool | None)}."""
    out = {"toc_do_tuan": None, "du_kien": None, "dung_huong": None}
    if s is None or len(s) < 2:
        return out
    x = (s["ngay"] - s["ngay"].iloc[0]).dt.days.astype(float)
    if x.iloc[-1] < 7:
        return out
    y = s[ma].astype(float)
    xm, ym = x.mean(), y.mean()
    den = ((x - xm) ** 2).sum()
    if den <= 0:
        return out
    slope = ((x - xm) * (y - ym)).sum() / den                    # đơn vị / ngày
    out["toc_do_tuan"] = round(slope * 7, 2)
    hien = float(y.iloc[-1])
    can = dich - hien
    if abs(can) < 1e-9:
        out.update(dung_huong=True, du_kien=today)
        return out
    out["dung_huong"] = slope != 0 and (can > 0) == (slope > 0)
    if out["dung_huong"]:
        ngay = can / slope
        if ngay <= 730:
            out["du_kien"] = s["ngay"].iloc[-1].date() + timedelta(days=int(round(ngay)))
    return out


def tien_do(k: dict, M: pd.DataFrame, today: date | None = None) -> dict | None:
    """M = khach.measurements(ma). None nếu chưa đủ 1 lần đo có chỉ số liên quan."""
    today = today or date.today()
    if M is None or M.empty:
        return None
    lo = loai(k)
    nu = str(k.get("gioi_tinh") or "").lower() in ("nữ", "nu")
    bd = _d(k.get("ngay_bat_dau"))
    rows, pcts = [], []
    d0 = None
    for ma in THEO_LOAI[lo]:
        s = M[["ngay", ma]].dropna() if ma in M.columns else pd.DataFrame()
        if s.empty:
            continue
        if bd is not None:                                   # mốc = lần đo gần ngày bắt đầu gói nhất (không sau quá 14 ngày)
            truoc = s[s["ngay"].dt.date <= bd + timedelta(days=14)]
            s0 = truoc.iloc[-1] if not truoc.empty else s.iloc[0]
        else:
            s0 = s.iloc[0]
        goc, hien = float(s0[ma]), float(s.iloc[-1][ma])
        tu_nhap = tv.num(k.get(O_DICH.get(ma, ""))) if ma in O_DICH else None
        dich = float(tu_nhap) if tu_nhap is not None and tu_nhap == tu_nhap else _dich_mac_dinh(ma, goc, lo, nu)
        if dich is None or abs(dich - goc) < 1e-9:
            continue
        pct = (hien - goc) / (dich - goc) * 100
        d0 = min(d0, s0["ngay"].date()) if d0 else s0["ngay"].date()
        ten, dv, nd = CHI_SO[ma]
        dk = du_doan(s[s["ngay"] >= s0["ngay"]], ma, dich, today)                  # v3.64: dự đoán ngày đạt đích
        rows.append({"ma": ma, "ten": ten, "dv": dv, "nd": nd, "goc": goc, "hien_tai": hien, "dich": dich, **dk,
                     "pct": round(pct), "tu_dat": tu_nhap is not None, "so_lan": len(s),
                     "ngay_goc": s0["ngay"].date(), "ngay_cuoi": s.iloc[-1]["ngay"].date()})
        pcts.append(max(min(pct, 100), -50))
    if not rows:
        return None
    han = _d(k.get("muc_tieu_ngay")) or (d0 + timedelta(weeks=TUAN_MAC_DINH))
    tg = max((han - d0).days, 1)
    tg_pct = max(0, min(100, round((today - d0).days / tg * 100)))
    tong = round(sum(pcts) / len(pcts))
    for r in rows:
        r["trang_thai"] = ("✅ Đạt" if r["pct"] >= 100 else "↩ Ngược hướng" if r["pct"] < 0
                           else "🟢 Đúng tiến độ" if r["pct"] >= tg_pct - 15 else "🟠 Chậm")
    chinh = rows[0]
    if tong >= 100:
        nx = "Đã đạt mục tiêu — đặt mục tiêu giai đoạn mới."
    elif r_ng := [r for r in rows if r["pct"] < 0]:
        nx = "Chỉ số đi ngược mục tiêu: " + ", ".join(r["ten"] for r in r_ng) + " — xem lại ăn uống, chuyên cần, giấc ngủ."
    elif tong >= tg_pct - 15:
        nx = "Đúng tiến độ — giữ nhịp tập và ăn hiện tại."
    else:
        nx = "Chậm hơn kế hoạch — kiểm tra số buổi / tuần, nhật ký ăn, bước chân mỗi ngày."
    for r in rows:
        if r["pct"] >= 100:
            r["du_doan"] = "Đã đạt đích"
        elif r.get("du_kien"):
            r["du_doan"] = (f"giữ nhịp này: đạt {r['dich']:g}{(' ' + r['dv']) if r['dv'] else ''} khoảng {r['du_kien']:%d/%m/%Y}"
                            + (" (sớm hơn hạn)" if r["du_kien"] <= han else " (trễ hơn hạn — cần tăng tốc)"))
        elif r.get("dung_huong") is False:
            r["du_doan"] = "đang đi ngược hướng mục tiêu"
        else:
            r["du_doan"] = "cần thêm ≥ 2 lần đo cách nhau 1 tuần để dự đoán"
    return {"loai": lo, "ten_loai": tv.GOALS.get(lo, lo), "rows": rows, "tong": tong, "tg_pct": tg_pct,
            "han": han, "bat_dau": d0, "chinh": chinh, "nhan_xet": nx,
            "da_dat_dich": any(r["tu_dat"] for r in rows)}
