"""v2.9 — Nhắc đo InBody định kỳ cho từng khách (mặc định mỗi 7 ngày).

Lần đo gần nhất = ngày số đo gần nhất có % mỡ / khối cơ / khối mỡ (chỉ số của máy InBody).
Hạn đo tiếp = lần cuối + chu kỳ của khách (trường `inbody_ky`: 7 / 14 / 30 ngày, 0 = không nhắc).
Khách chưa đo lần nào → cần đo ngay.
"""
from __future__ import annotations

from datetime import date, timedelta

from core import tien_do

KY = {7: "Mỗi tuần", 14: "2 tuần / lần", 30: "Mỗi tháng", 0: "Không nhắc"}
CHI_SO_INBODY = ("pbf", "smm", "khoi_mo")


def ky(k: dict) -> int:
    v = str(k.get("inbody_ky") if k.get("inbody_ky") is not None else "").strip()
    if v == "":
        return 7
    try:
        return max(int(float(v)), 0)
    except ValueError:
        return 7


def lan_cuoi(ma: str) -> date | None:
    sd = tien_do.so_do(ma)
    if sd.empty:
        return None
    co = sd[sd[list(CHI_SO_INBODY)].notna().any(axis=1)]
    return co["ngay"].max() if not co.empty else None


def trang_thai(k: dict, hom: date, cuoi: date | None = None, da_tinh: bool = False) -> dict | None:
    """None nếu khách tắt nhắc. Ngược lại {cuoi, han, con (ngày còn lại, âm = trễ), can (đến hạn chưa)}."""
    n = ky(k)
    if not n:
        return None
    cuoi = cuoi if da_tinh else lan_cuoi(k["ma"])
    han = (cuoi + timedelta(days=n)) if cuoi else hom
    con = (han - hom).days
    return {"cuoi": cuoi, "han": han, "con": con, "can": con <= 0, "ky": n}


def can_do(DS: list[dict], hom: date, trong: int = 0) -> list[dict]:
    """Khách đang tập đến hạn đo trong `trong` ngày tới, trễ nhất xếp trước."""
    out = []
    for k in DS:
        if (k.get("trang_thai") or "Đang tập") != "Đang tập":
            continue
        t = trang_thai(k, hom)
        if t and t["con"] <= trong:
            out.append({**t, "k": k})
    return sorted(out, key=lambda x: x["con"])


def buoi_do(k: dict, t: dict, B: list[dict], hom: date) -> dict | None:
    """Buổi hẹn gần nhất kể từ ngày đến hạn (đã trễ → buổi sắp tới gần nhất) — đo ngay buổi đó."""
    tu = max(t["han"], hom)
    return next((b for b in B if b["ma"] == k["ma"] and b["trang_thai"] != "huy" and b["ngay"] >= tu), None)


def mo_ta(t: dict) -> str:
    if not t["cuoi"]:
        return "chưa đo lần nào"
    if t["con"] < 0:
        return f"trễ {-t['con']} ngày (lần cuối {t['cuoi']:%d/%m})"
    if t["con"] == 0:
        return f"đến hạn hôm nay (lần cuối {t['cuoi']:%d/%m})"
    return f"còn {t['con']} ngày (hạn {t['han']:%d/%m})"


def nhan(k: dict) -> str:
    return KY.get(ky(k), f"{ky(k)} ngày / lần")


