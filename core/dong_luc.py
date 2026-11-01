# Hoàng Anh Coaching v1.5 (2026-10-31) — động lực & cam kết: nhiệm vụ mỗi ngày, chuỗi lửa (có khiên bảo vệ),
# điểm, cấp độ, huy hiệu, check-in ăn / ngủ / nước. Mục đích: khách báo cáo đều để HLV theo sát và khách giữ cam kết.
# Nguyên tắc: thưởng cho việc làm đều, KHÔNG phạt nặng — ngày nghỉ vẫn giữ được lửa, lỡ 1 ngày có khiên đỡ.
from __future__ import annotations

from datetime import date, timedelta

from core import cardio as cd, db, giao_an as ga, store, tien_do as td

DIEM = {"can": 10, "tap": 30, "cardio": 20, "checkin": 15, "so_do": 25, "anh": 40}
TEN_NV = {"can": ("⚖️", "Cân buổi sáng"), "tap": ("🏋️", "Ghi buổi tập"), "cardio": ("🏃", "Cardio đạt target"),
          "checkin": ("📝", "Check-in ăn · ngủ · nước"), "so_do": ("📏", "Đo vòng tuần này"), "anh": ("📸", "Chụp ảnh 4 tuần")}
THU_DO = 0                    # thứ Hai: ngày đo vòng hằng tuần
CHU_KY_ANH = 28
CAP = [(0, "Tân binh", "🌱"), (300, "Chiến binh", "⚔️"), (800, "Bền bỉ", "🛡️"), (1600, "Kỷ luật thép", "🔩"),
       (3000, "Tinh anh", "💎"), (5000, "Huyền thoại", "👑")]
NGUONG_LUA = 2 / 3            # làm ≥ 2/3 nhiệm vụ của ngày → giữ lửa
LOI_HLV = [  # câu động lực HLV (tự viết, không gán cho người nổi tiếng)
    "Không cần hoàn hảo, chỉ cần không bỏ cuộc. Hôm nay làm đủ việc nhỏ là thắng.",
    "Cơ thể thay đổi bằng những ngày bình thường làm đúng, không phải một ngày cố quá sức.",
    "Số cân dao động mỗi ngày là bình thường — đường trung bình 7 ngày mới nói thật.",
    "Ghi lại là để HLV chỉnh đúng cho bạn. Không có số liệu thì chỉ là đoán.",
    "Mệt thì tập nhẹ, nhưng vẫn tập. Giữ thói quen quan trọng hơn giữ mức tạ.",
    "Ăn đủ đạm hôm nay là đang xây cơ cho tuần sau.",
    "Bạn không cần động lực mỗi ngày — bạn cần chuỗi lửa. Đừng để nó tắt.",
    "Tuần này chỉ cần tốt hơn tuần trước một chút.",
    "Ngủ đủ cũng là tập luyện. Cơ phát triển lúc bạn nghỉ.",
    "Mỗi lần tick xong nhiệm vụ là một lần giữ lời hứa với chính mình.",
]


# ------------------------------------------------------------------ check-in hằng ngày
def checkins(ma: str) -> dict[date, dict]:
    out = {}
    for k, v in db.latest("DinhDuong", ma).items():
        if k.startswith(f"checkin|{ma}|") and not v.get("xoa"):
            try:
                out[date.fromisoformat(str(v["ngay"])[:10])] = v
            except (KeyError, ValueError):
                pass
    return out


def luu_checkin(ma: str, ngay: date, r: dict, nguoi: str) -> bool:
    return db.append("DinhDuong", f"checkin|{ma}|{ngay.isoformat()}", {**r, "ngay": ngay.isoformat(), "ma_kh": ma}, nguoi, ma)


def da_xem(ma: str) -> dict:
    return db.latest("DinhDuong", ma).get(f"da_xem|{ma}") or {}


def danh_dau_xem(ma: str, muc: str, nguoi: str) -> bool:
    v = {k: x for k, x in da_xem(ma).items() if not k.startswith("_")}
    v[muc] = db.now_str()
    return db.append("DinhDuong", f"da_xem|{ma}", {**v, "ma_kh": ma}, nguoi, ma)


# ------------------------------------------------------------------ dữ liệu theo ngày
def _d(x) -> date | None:
    try:
        return date.fromisoformat(str(x)[:10])
    except ValueError:
        return None


def du_lieu(k: dict, q: dict | None = None) -> dict:
    """Gom 1 lần mọi nguồn: ngày có cân, có ghi tập, phút cardio, check-in, target cardio từng thứ."""
    ma = k["ma"]
    q = q or store.quyen(k)
    CAN = td.can_ngay(ma)
    L = ga.logs(ma)
    c = cd.cai_dat(ma)
    hs = db.latest("DinhDuong").get(f"hs|{ma}", {})
    tap = cd.ngay_tap(c, k, hs)
    goc = cd.target_goc(c, tap)
    cardio: dict[date, float] = {}
    for r in cd.logs(ma):
        d = _d(r.get("ngay"))
        if d:
            cardio[d] = cardio.get(d, 0) + float(r.get("phut") or 0)
    SD = td.so_do(ma)
    ANH = td.anh(ma)
    return {"so_do": {x for x in SD["ngay"]} if len(SD) else set(), "anh": sorted({_d(v.get("ngay")) for v in ANH if _d(v.get("ngay"))}),
            "can": {_d(x) for x in CAN["ngay"]} if len(CAN) else set(), "tap_log": {_d(x.get("ngay")) for x in L if not x.get("xoa")},
            "cardio": cardio, "checkin": checkins(ma), "ngay_tap": set(tap), "goc": goc, "q": q, "L": L, "CAN": CAN,
            "bat_dau": _d(k.get("ngay_bat_dau")) or None}


def nhiem_vu(D: dict, d: date) -> list[dict]:
    """Nhiệm vụ của ngày d (chỉ những mục khách được mở) + đã xong chưa."""
    q, out = D["q"], []
    if q.get("can"):
        out.append({"id": "can", "xong": d in D["can"]})
    if d.weekday() in D["ngay_tap"] and (q.get("ghi_buoi") or q.get("giao_an")):
        out.append({"id": "tap", "xong": d in D["tap_log"]})
    tg = D["goc"][d.weekday()]["phut"]
    if tg and (q.get("cardio") or q.get("ghi_cardio")):
        lam = D["cardio"].get(d, 0)
        out.append({"id": "cardio", "xong": lam >= tg * 0.9, "phan": min(lam / tg, 1), "lam": round(lam), "tg": tg})
    out.append({"id": "checkin", "xong": d in D["checkin"]})
    if q.get("so_do"):                                   # nhiệm vụ THƯỞNG: không tính vào giữ lửa
        t2 = d - timedelta(days=d.weekday())
        da_tuan = any(t2 <= x < d for x in D.get("so_do", ()))      # đã đo từ đầu tuần tới hôm qua → hôm nay không nhắc
        if d.weekday() >= THU_DO and not da_tuan:
            out.append({"id": "so_do", "xong": d in D.get("so_do", ()), "phu": True})
        truoc = [x for x in D.get("anh", []) if x < d]
        if d in D.get("anh", []) or not truoc or (d - truoc[-1]).days >= CHU_KY_ANH:
            out.append({"id": "anh", "xong": d in D.get("anh", []), "phu": True})
    for x in out:
        x["icon"], x["ten"] = TEN_NV[x["id"]]
        x["diem"] = DIEM[x["id"]] if x["xong"] else round(DIEM[x["id"]] * x.get("phan", 0) * 0.5)
    return out


def _ty_le(nv: list[dict]) -> float:
    nv = [x for x in nv if not x.get("phu")]               # nhiệm vụ thưởng không tính vào giữ lửa
    return sum(1 for x in nv if x["xong"]) / len(nv) if nv else 0


def tong_hop(k: dict, hom: date | None = None, q: dict | None = None) -> dict:
    hom = hom or db.now_vn().date()
    D = du_lieu(k, q)
    co = [x for x in D["can"] | D["tap_log"] | set(D["cardio"]) | set(D["checkin"]) if x]
    dau = min([D["bat_dau"]] + co if D["bat_dau"] else co) if co else hom
    dau = max(dau, hom - timedelta(days=365))
    # ---- điểm & lịch sử
    ngay, xp = [], 0
    d = dau
    while d <= hom:
        nv = nhiem_vu(D, d)
        tl = _ty_le(nv)
        xp += sum(x["diem"] for x in nv) + (20 if nv and tl == 1 else 0)          # thưởng hoàn thành đủ cả ngày
        ngay.append({"ngay": d, "tl": tl, "lua": tl >= NGUONG_LUA, "nv": nv})
        d += timedelta(days=1)
    # ---- chuỗi lửa: hôm nay chưa xong vẫn chưa mất lửa; lỡ 1 ngày dùng khiên (mỗi 7 ngày lửa được 1 khiên, giữ tối đa 2)
    khien, chuoi, dai_nhat, dung_khien = 0, 0, 0, 0
    for x in ngay[:-1] if ngay and not ngay[-1]["lua"] else ngay:
        if x["lua"]:
            chuoi += 1
            if chuoi % 7 == 0:
                khien = min(khien + 1, 2)
        elif khien and chuoi:
            khien -= 1
            dung_khien += 1
        else:
            chuoi = 0
        dai_nhat = max(dai_nhat, chuoi)
    hn = ngay[-1] if ngay else {"nv": nhiem_vu(D, hom), "tl": 0, "lua": False}
    # ---- tuần
    d0 = hom - timedelta(days=hom.weekday())
    tuan = [x for x in ngay if x["ngay"] >= d0]
    tuan_truoc = [x for x in ngay if d0 - timedelta(days=7) <= x["ngay"] < d0]
    diem_tuan = round(sum(x["tl"] for x in tuan) / len(tuan) * 100) if tuan else 0
    diem_tt = round(sum(x["tl"] for x in tuan_truoc) / 7 * 100) if tuan_truoc else None
    cap = max([c for c in CAP if xp >= c[0]], key=lambda c: c[0])
    i = CAP.index(cap)
    sau = CAP[i + 1] if i + 1 < len(CAP) else None
    return {"hom": hom, "nv": hn["nv"], "tl_hom": hn["tl"], "lua_hom": hn["lua"], "chuoi": chuoi, "dai_nhat": dai_nhat, "khien": khien,
            "dung_khien": dung_khien, "xp": xp, "cap": cap, "cap_sau": sau,
            "pct_cap": round((xp - cap[0]) / (sau[0] - cap[0]) * 100) if sau else 100, "diem_tuan": diem_tuan, "diem_tt": diem_tt,
            "ngay": ngay, "huy_hieu": huy_hieu(k, D, ngay, dai_nhat), "loi": LOI_HLV[hom.toordinal() % len(LOI_HLV)]}


# ------------------------------------------------------------------ huy hiệu
def huy_hieu(k: dict, D: dict, ngay: list[dict], dai_nhat: int) -> list[dict]:
    so_buoi = len(D["tap_log"])
    so_ci = len(D["checkin"])
    giam = None
    CAN = D["CAN"]
    if len(CAN) >= 2:
        giam = round(float(CAN["kg"].iloc[0]) - float(CAN["tb7"].iloc[-1]), 1)
    tuan_full = 0
    for i in range(0, len(ngay) - 6):
        w = ngay[i:i + 7]
        if w[0]["ngay"].weekday() == 0 and all(x["tl"] == 1 for x in w):
            tuan_full += 1
    ds = [
        ("🔥", "Khởi động", "Giữ lửa 3 ngày liền", dai_nhat >= 3),
        ("🗓️", "Một tuần kỷ luật", "Giữ lửa 7 ngày liền", dai_nhat >= 7),
        ("⚡", "21 ngày thành thói quen", "Giữ lửa 21 ngày liền", dai_nhat >= 21),
        ("🏆", "Tháng thép", "Giữ lửa 30 ngày liền", dai_nhat >= 30),
        ("🏋️", "10 buổi", "Ghi đủ 10 buổi tập", so_buoi >= 10),
        ("💪", "50 buổi", "Ghi đủ 50 buổi tập", so_buoi >= 50),
        ("📝", "Báo cáo viên", "Check-in 14 ngày", so_ci >= 14),
        ("💯", "Tuần hoàn hảo", "Làm đủ 100% nhiệm vụ cả 1 tuần (T2–CN)", tuan_full >= 1),
        ("📉", "−1 kg", "Cân TB 7 ngày giảm 1 kg so với lần cân đầu", giam is not None and giam >= 1),
        ("🎯", "−3 kg", "Cân TB 7 ngày giảm 3 kg", giam is not None and giam >= 3),
        ("👑", "−5 kg", "Cân TB 7 ngày giảm 5 kg", giam is not None and giam >= 5),
    ]
    return [{"icon": a, "ten": b, "mo_ta": c, "co": bool(d)} for a, b, c, d in ds]


def cam_ket_tat_ca(DS: list[dict], hom: date | None = None) -> list[dict]:
    """Bảng cho HLV: chuỗi lửa, điểm tuần, lần báo cáo gần nhất, việc hôm nay còn thiếu."""
    out = []
    for k in DS:
        t = tong_hop(k, hom)
        lan_cuoi = max((x["ngay"] for x in t["ngay"] if x["tl"] > 0), default=None)
        out.append({"k": k, "t": t, "lan_cuoi": lan_cuoi})
    return out
