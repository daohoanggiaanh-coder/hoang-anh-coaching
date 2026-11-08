# Hoàng Anh Coaching v2.6 (2026-11-06) — LỊCH TẬP THEO GIÁO ÁN: ngày tập (tick ở trang Khách) × thứ tự buổi trong giáo án.
"""Buổi được xếp nối tiếp theo thứ tự giáo án (VD Push → Pull → Leg → Push 2 → Pull 2 → Leg 2), bắt đầu từ buổi kế tiếp sau buổi
khách tập gần nhất — nghỉ 1 buổi thì lịch tự lùi, không bỏ sót buổi nào trong chu kỳ."""
from __future__ import annotations

from datetime import date, timedelta

from core import buoi as bt, db, ga_atlas as ga, store


def sap_toi(k: dict, so_ngay: int = 21, tu: date | None = None) -> list[dict]:
    tu = tu or db.now_vn().date()
    P = ga.current(k["ma"])
    hist = bt.sessions(k["ma"])
    B = [b for b in store.buoi([k], tu, tu + timedelta(days=so_ngay)) if b["trang_thai"] in ("hen", "da_tap", "hoan_thanh")]
    da_hom_nay = any(s["ngay"] == tu for s in hist)
    out = []
    if not P or not P.get("buoi"):
        return [{"ngay": b["ngay"], "gio": b["gio"], "buoi": None} for b in B]
    mas = [x["ma"] for x in P["buoi"]]
    nx = ga.buoi_tiep(P, hist)
    i = mas.index(nx["ma"]) if nx else 0
    for b in sorted(B, key=lambda x: (x["ngay"], x["gio"])):
        if b["ngay"] == tu and da_hom_nay:
            continue
        doi = b.get("buoi_ga") in mas
        if doi:                       # v3.5: HLV đổi buổi riêng ngày này → các buổi sau nối tiếp từ buổi đã đổi
            i = mas.index(b["buoi_ga"])
        bu = P["buoi"][i % len(mas)]
        out.append({"ngay": b["ngay"], "gio": b["gio"], "buoi": bu["ma"], "ten": bu["ten"], "id": b["id"], "doi": doi})
        i += 1
    return out


def chu_ky(k: dict) -> list[str]:
    """Thứ tự buổi trong giáo án: ['A · Push', 'B · Pull', …]."""
    P = ga.current(k["ma"])
    return [f"{x['ma']} · {x['ten']}" for x in (P or {}).get("buoi", [])]
