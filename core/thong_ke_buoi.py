"""v4.3 — THỐNG KÊ BUỔI TẬP + LỊCH THÁNG.

Nguồn "đã tập" của một ngày:
  · buổi ✅ trên Lịch hẹn (trạng thái "xong")  → buổi PT, trừ vào gói
  · nhật ký buổi tập (HLV / khách ghi bài)      → biết TÊN buổi
Ngày tương lai: buổi hẹn + tên buổi theo thứ tự giáo án (lich_tap.sap_toi).
"""
from __future__ import annotations

import calendar
from datetime import date, timedelta

from core import buoi as bt, db, goi, lich_tap, store

MOC = (1, 5, 10, 20, 30, 50, 75, 100, 150, 200, 250, 300)

NEAT = [
    "🚶 Đi bộ 8.000–10.000 bước — chia nhỏ 3 lần 15 phút sau bữa ăn.",
    "🪜 Đi thang bộ thay thang máy, đứng dậy đi lại 2–3 phút mỗi giờ ngồi.",
    "🚴 Cardio nhẹ 20–30 phút (đạp xe, đi bộ nhanh) — vẫn nói chuyện được là vừa.",
    "🍽 Ngày nghỉ ăn bớt tinh bột ~⅓ so với ngày tập, giữ đủ đạm và rau.",
    "💧 Uống đủ nước, ngủ sớm — hồi phục tốt thì buổi sau tập khoẻ hơn.",
    "🧹 Việc nhà, dắt chó đi dạo, đi chợ bộ… đều là NEAT — cộng dồn đốt calo nhiều hơn bạn nghĩ.",
    "🧘 Giãn cơ / lăn foam 10 phút cho nhóm cơ còn mỏi.",
]


def _ten_log(s: dict) -> str:
    t = str(s.get("buoi") or "").strip()
    return t or "Buổi tập"


def ngay_da_tap(k: dict, H: dict | None = None, hist: list[dict] | None = None) -> dict[date, dict]:
    """{ngày: {ten, pt (buổi ✅ lịch), log (có ghi bài), so (số thứ tự buổi), moc}} — từ ngày bắt đầu gói trở đi có đánh số."""
    H = store.hens(k["ma"]) if H is None else H
    hist = bt.sessions(k["ma"]) if hist is None else hist
    out: dict[date, dict] = {}
    for h in H.values():
        d = store._d(h.get("ngay"))
        if h.get("ma") == k["ma"] and h.get("trang_thai") == "xong" and d:
            out.setdefault(d, {"ten": "", "pt": False, "log": False})["pt"] = True
    for s in hist:
        if s.get("ngay"):
            x = out.setdefault(s["ngay"], {"ten": "", "pt": False, "log": False})
            x["log"] = True
            x["ten"] = x["ten"] or _ten_log(s)
            x["rpe"] = s.get("rpe")
    # đánh số buổi: gói theo buổi → chỉ buổi ✅ lịch (khớp số trừ gói); gói thời gian → mọi ngày có tập
    bd = store._d(k.get("ngay_bat_dau")) or date.min
    theo_buoi = store.loai_goi(k) == "buoi" and any(v["pt"] for v in out.values())
    n = goi._i(k.get("da_tap_truoc"))
    tong = goi._i(k.get("goi_buoi")) if store.loai_goi(k) == "buoi" else 0
    for d in sorted(out):
        v = out[d]
        if d < bd or (theo_buoi and not v["pt"]):
            continue
        n += 1
        v["so"] = n
        v["moc"] = _moc(n, tong)
    return out


def _moc(n: int, tong: int) -> str:
    if tong and n == tong:
        return "🏁 Buổi cuối gói"
    if tong and n == (tong + 1) // 2 and tong >= 8:
        return "🔥 Nửa chặng gói"
    if n in MOC:
        return "🎉 Buổi đầu tiên" if n == 1 else f"🏆 Mốc {n} buổi"
    return ""


def lich_thang(k: dict, nam: int, thang: int, hom: date | None = None, H: dict | None = None) -> dict:
    """Ô lịch của 1 tháng: [{ngay, loai: da|hen|lo|nghi|ngoai, ten, so, moc, gio, meo}] + tóm tắt."""
    hom = hom or db.now_vn().date()
    H = store.hens(k["ma"]) if H is None else H
    da = ngay_da_tap(k, H)
    dau = date(nam, thang, 1)
    cuoi = date(nam, thang, calendar.monthrange(nam, thang)[1])
    B = store.buoi([k], dau, cuoi, H)
    hen = {}
    for b in B:
        if b["trang_thai"] == "hen":
            hen.setdefault(b["ngay"], b)
    ke = {}
    if cuoi >= hom:
        try:
            for x in lich_tap.sap_toi(k, (cuoi - hom).days + 1, hom):
                ke.setdefault(x["ngay"], x)
        except Exception:  # noqa: BLE001
            pass
    # dự kiến số thứ tự cho buổi tương lai (để báo trước "buổi cuối gói")
    tq = goi.tong_quan(k, H, hom)
    tong = tq["tong"]
    so_tiep = max([v.get("so", 0) for v in da.values()] + [goi._i(k.get("da_tap_truoc"))])
    tuong_lai = sorted(d for d in set(hen) | set(ke) if d > hom or (d == hom and d not in da))
    so_du = {}
    if so_tiep:
        fut = {b["ngay"] for b in store.buoi([k], hom, hom + timedelta(days=150), H)
               if b["trang_thai"] == "hen" and (b["ngay"] > hom or b["ngay"] not in da)}
        for d in sorted(fut):
            so_tiep += 1
            so_du[d] = so_tiep
    o = []
    for i in range(cuoi.day):
        d = dau + timedelta(days=i)
        if d in da:
            v = da[d]
            o.append({"ngay": d, "loai": "da", "ten": v["ten"] or ("Buổi PT" if v["pt"] else "Buổi tập"), "so": v.get("so"),
                      "moc": v.get("moc", ""), "pt": v["pt"]})
        elif d in tuong_lai:
            x = ke.get(d) or {}
            b = hen.get(d) or {}
            sd = so_du.get(d)
            o.append({"ngay": d, "loai": "hen", "ten": (f"{x['buoi']} · {x['ten']}" if x.get("buoi") else "Buổi tập"),
                      "gio": store.gio_s(x.get("gio") or b.get("gio", "")), "so": sd, "moc": _moc(sd, tong) if sd else ""})
        elif d < hom and d in hen:
            o.append({"ngay": d, "loai": "lo", "ten": "Lỡ buổi"})
        else:
            o.append({"ngay": d, "loai": "nghi", "meo": NEAT[d.toordinal() % len(NEAT)]})
    trong = [x for x in o if x["loai"] == "da"]
    return {"o": o, "nam": nam, "thang": thang, "da_thang": len(trong), "hen_thang": sum(x["loai"] == "hen" for x in o),
            "lo_thang": sum(x["loai"] == "lo" for x in o), "goi": tq, "hom": hom}


def theo_tuan(k: dict, so_tuan: int = 12, hom: date | None = None, H: dict | None = None) -> list[dict]:
    """[{tuan (thứ 2), so, ke_hoach}] cho biểu đồ cột."""
    hom = hom or db.now_vn().date()
    da = ngay_da_tap(k, H)
    t0 = hom - timedelta(days=hom.weekday())
    kh = len(store.lich_co_dinh(k))
    out = []
    for i in range(so_tuan - 1, -1, -1):
        a = t0 - timedelta(weeks=i)
        out.append({"tuan": a, "so": sum(1 for d in da if a <= d < a + timedelta(days=7)), "ke_hoach": kh})
    return out


def tong_hop_khach(ds: list[dict], hom: date | None = None) -> list[dict]:
    """Một dòng / khách cho biểu đồ tổng quan."""
    hom = hom or db.now_vn().date()
    H = store.hens()
    out = []
    for k in ds:
        try:
            tq = goi.tong_quan(k, H, hom)
            da = ngay_da_tap(k, H)
        except Exception:  # noqa: BLE001
            continue
        bon_tuan = sum(1 for d in da if hom - timedelta(days=28) < d <= hom)
        out.append({"ma": k["ma"], "ten": str(k.get("ho_ten") or k["ma"]), "phong": store.phong(k), "loai": tq["loai"],
                    "goi": tq["ten"], "tong": tq["tong"], "da": tq["da"] if tq["tong"] else len([d for d in da
                                                                                                  if d >= (tq["bat_dau"] or date.min)]),
                    "con": tq["con"], "bon_tuan": bon_tuan, "ke_hoach_4t": len(store.lich_co_dinh(k)) * 4,
                    "cuoi": max(da) if da else None, "het_han": tq["het_han"]})
    return out


def buoi_tiep_theo(k: dict) -> str | None:
    """Tên buổi kế tiếp theo thứ tự giáo án (cho khách tự tập, không có lịch cố định)."""
    try:
        from core import ga_atlas as ga
        P = ga.current(k["ma"])
        if not P or not P.get("buoi"):
            return None
        nx = ga.buoi_tiep(P, bt.sessions(k["ma"]))
        return f"{nx['ma']} · {nx['ten']}" if nx else None
    except Exception:  # noqa: BLE001
        return None
