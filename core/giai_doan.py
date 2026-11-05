# Hoàng Anh Coaching v2.0 (2026-11-03) — LỘ TRÌNH TỔNG THEO GIAI ĐOẠN (khách + HLV cùng xem).
"""Mỗi giai đoạn gom đủ 5 mảng: tập tạ · cardio · bước chân · dinh dưỡng · mốc đo.
Số liệu lấy từ thiết lập thật của khách (buổi / tuần, target cardio HLV đặt, bước chân mục tiêu, đạm g/kg) — giai đoạn đầu
"lên dần" về mức đó, giai đoạn cuối chốt thói quen tự duy trì. Đây là khung thực hành của HLV, không phải cam kết kết quả."""
from __future__ import annotations

from datetime import date, timedelta

from core import buoi as bu, cardio as cd, db, dinh_duong as dd, ga_atlas as ga, muc_tieu as mt, store, tu_van as tv, volume as vo

TEN_MT = {"giam_mo": "Giảm mỡ", "recomp": "Giảm mỡ + tăng cơ", "tang_co": "Tăng cơ", "giu": "Giữ dáng / sức khoẻ"}
_TU_MT = {"suc_khoe": "giu", "suc_manh": "tang_co"}


def _chia(n: int) -> list[tuple[int, int]]:
    """Chia n tuần thành các giai đoạn (tuần đầu, tuần cuối)."""
    if n <= 5:
        a = max(1, n // 2)
        return [(1, a), (a + 1, n)] if n > 1 else [(1, 1)]
    a, b = round(n / 3), round(2 * n / 3)
    return [(1, a), (a + 1, b), (b + 1, n)]


def _tron(x: float, buoc: int = 500) -> int:
    return int(round(x / buoc) * buoc)


def ke_hoach(muc_tieu: str, tong_tuan: int, buoi_tuan: int, c: dict, buoc: int, dam_gkg: float, nu: bool) -> list[dict]:
    mt_ = muc_tieu if muc_tieu in TEN_MT else "giam_mo"
    giam = mt_ in ("giam_mo", "recomp")
    tap_p, nghi_p = int(c["tap"]["phut"]), int(c["nghi"]["phut"])
    tap_max, nghi_max = int(c["tap"].get("toi_da") or tap_p), int(c["nghi"].get("toi_da") or nghi_p)
    khoang = _chia(max(int(tong_tuan), 1))
    so = len(khoang)
    out = []
    for i, (a, b) in enumerate(khoang):
        cuoi, dau = i == so - 1, i == 0
        g = {"so": i + 1, "tu": a, "den": b}
        if dau:
            g |= {"ten": "Nền tảng", "muc_tieu": "Học kỹ thuật chuẩn, làm quen tạ, tạo thói quen ăn – tập – ghi chép đều mỗi ngày."}
            g["tap"] = [f"{buoi_tuan} buổi / tuần · 2–3 hiệp × 10–15 lần · chừa 3 lần (RIR 3 · RPE ~7)",
                        "Nghỉ giữa hiệp 60–90 giây · ưu tiên tư thế, nhịp chậm có kiểm soát",
                        "Mỗi buổi có khởi động + core / lưng dưới (theo chuỗi buổi trước – sau)",
                        "Ghi kg × lần từng hiệp trên web để HLV tăng tạ đúng lúc"]
            cd_tap, cd_nghi = max(15, tap_p - 10), max(30, nghi_p - 20)
            buoc_gd = max(5000, _tron(buoc - 2000))
        elif not cuoi or so == 2:
            g |= {"ten": "Tăng tải", "muc_tieu": "Tăng dần mức tạ / số lần mỗi tuần, tập đủ khối lượng — giai đoạn ra kết quả nhiều nhất."}
            g["tap"] = [f"{buoi_tuan} buổi / tuần · 3–4 hiệp × 8–12 lần · chừa 1–2 lần (RIR 1–2 · RPE 8–9)",
                        "Nghỉ 90–120 giây bài lớn (squat, đẩy, kéo), 60–90 giây bài phụ",
                        "Tăng tải kép: đủ số lần trên cả hiệp → tuần sau thêm 1–2,5 kg (thân trên) / 2,5–5 kg (thân dưới)",
                        "Tăng volume nhóm ưu tiên 1–2 hiệp / tuần nếu hồi phục tốt (xem bảng volume bên dưới)"]
            cd_tap, cd_nghi = tap_p, nghi_p
            buoc_gd = buoc
            if so == 2:
                g["tap"].append("Tuần cuối: test lại mức tạ / số lần đầu khoá để thấy tiến bộ")
        else:
            g |= {"ten": "Bứt phá & tự duy trì", "muc_tieu": "Chốt kết quả, tự tập – tự ăn đúng mà không cần nhắc."}
            g["tap"] = [f"{buoi_tuan} buổi / tuần · 3–4 hiệp × 6–10 lần bài lớn, 10–15 lần bài phụ · RIR 1–2",
                        "Nghỉ 2–3 phút bài nặng · giữ kỹ thuật, không gồng thêm lần khi form xấu",
                        "Tuần cuối: test lại mức tạ / số lần so với đầu khoá",
                        "Khách tự soạn được 1 buổi theo nguyên tắc đã học"]
            cd_tap = min(tap_max, tap_p + 5) if giam else tap_p
            cd_nghi = min(nghi_max, nghi_p + 15) if mt_ == "giam_mo" else nghi_p
            buoc_gd = buoc + 1000 if mt_ == "giam_mo" else buoc
        if mt_ == "tang_co":
            g["cardio"] = [f"Ngày tập: {min(cd_tap, 20)} phút đi dốc nhẹ sau tạ (không bắt buộc)",
                           "Ngày nghỉ: 2–3 buổi / tuần × 20–30 phút nhẹ — đủ cho tim mạch, không lấn sức hồi phục"]
        else:
            g["cardio"] = [f"Ngày tập: {cd_tap} phút đi dốc sau tạ (khoảng 20–30 phút)",
                           f"Ngày nghỉ: {cd_nghi} phút vùng nhẹ – vừa (thở hơi nhanh, vẫn nói được câu ngắn)",
                           "Thiếu hôm nào → web chia đều phần thiếu cho các ngày còn lại trong tuần"]
        g["buoc"] = int(buoc_gd)
        dam = f"Đạm {dam_gkg:g} g / kg cân mỗi ngày, chia đều các bữa"
        if dau:
            g["an"] = [dam, "Ăn đúng thực đơn ≥ 80 % số bữa · cân đồ chín 1–2 tuần đầu để quen khẩu phần",
                       "Học áng chừng bằng bàn tay cho bữa ăn ngoài (tab 🍜 Ăn ngoài)",
                       "Nữ: đủ béo từ bơ, hạt, cá, trứng — dầu nấu tối đa 10 ml / bữa" if nu else "Dầu nấu tối đa 10 ml / bữa, béo từ cá, trứng, hạt"]
        elif not cuoi or so == 2:
            g["an"] = [dam, "HLV chỉnh ±100–200 kcal nếu cân TB 7 ngày đứng / đi sai hướng 2–3 tuần liền",
                       "Ghi bữa ăn ngoài vào 📝 Đã ăn · còn lại — các bữa sau tự cân đối lại",
                       "Ngày nghỉ ít tinh bột hơn ngày tập (web đã tính sẵn)"]
        else:
            g["an"] = [dam, "Tự chọn món theo áng chừng; dùng thực đơn web làm mốc kiểm tra",
                       "1–2 tuần cuối: nâng dần lên mức duy trì (+100–200 kcal / tuần) để không tăng lại sau khoá" if giam
                       else "Giữ mức ăn hiện tại, chỉnh theo cân TB 7 ngày",
                       "Ăn ngoài / tiệc: chọn đúng 80 % là đủ, không bỏ bữa để bù"]
        g["do"] = ["Cân mỗi sáng (sau vệ sinh, trước ăn) — xem đường TB 7 ngày, không xem từng ngày",
                   "Số đo vòng eo / mông / đùi mỗi tuần"]
        if dau:
            g["do"].insert(0, "Đầu khoá: InBody + số đo + ảnh 3 góc (trước, nghiêng, sau)")
        g["do"].append(("Cuối giai đoạn" if not cuoi else "Kết khoá") + f" (tuần {b}): InBody + ảnh 3 góc"
                       + (" + so sánh trước / sau" if cuoi else ""))
        out.append(g)
    return out


def tong_tuan(k: dict) -> int:
    bd, han = store._d(k.get("ngay_bat_dau")), store.han_goi(k)
    if bd and han:
        return max(1, round((han - bd).days / 7))
    return 12


def cua_khach(k: dict, hom: date | None = None, hs: dict | None = None) -> dict:
    """hs: thông số dinh dưỡng đã điền sẵn cân / chiều cao (views.common.ho_so_dd) — thiếu thì chỉ lấy bản đã lưu."""
    hom = hom or db.now_vn().date()
    hs = hs if hs is not None else db.latest("DinhDuong").get(f"hs|{k['ma']}", {})
    mt_ = hs.get("muc_tieu") or _TU_MT.get(mt.loai(k), mt.loai(k))
    lich = store.lich_co_dinh(k)
    buoi = len(lich) or int(hs.get("buoi_tuan") or 3)
    c = cd.cai_dat(k["ma"])
    buoc = cd.buoc_muc_tieu(c, mt_)
    dam = float(hs.get("dam_g_kg") or dd.MUC_DAM.get(hs.get("muc_dam") or "cao", dd.MUC_DAM["cao"])["g"])
    nu = str(hs.get("gioi_tinh") or k.get("gioi_tinh") or "") == "Nữ"
    n = tong_tuan(k)
    bd = store._d(k.get("ngay_bat_dau")) or hom
    tuan = max(1, min(n, (hom - bd).days // 7 + 1))
    gd = ke_hoach(mt_, n, buoi, c, buoc, dam, nu)
    for g in gd:
        g["ngay_tu"], g["ngay_den"] = bd + timedelta(weeks=g["tu"] - 1), bd + timedelta(weeks=g["den"], days=-1)
    dang = next((i for i, g in enumerate(gd) if g["tu"] <= tuan <= g["den"]), len(gd) - 1)
    out = {"gd": gd, "tuan": tuan, "tong": n, "dang": dang, "bat_dau": bd, "muc_tieu": TEN_MT.get(mt_, mt_),
           "da_qua": hom > bd + timedelta(weeks=n), "chua_bd": hom < bd}
    them(out, k, hs, mt_, nu)
    return out


# ------------------------------------------------------------------ v2.1: chi tiết từng giai đoạn
def tuan_deload(n: int, gd: list[dict]) -> list[int]:
    """Tuần giảm tải: khoá ≥ 8 tuần → tuần cuối giai đoạn tăng tải; khoá dài hơn → thêm mỗi ~6 tuần."""
    if n < 8:
        return []
    w = [gd[1]["den"]] if len(gd) >= 3 else [round(n / 2)]
    x = w[0] + 6
    while x < n - 1:
        w.append(x)
        x += 6
    return w


def vi_chat(kq: dict | None, nu: bool) -> list[str]:
    xo = f"≥ {kq['tap']['xo']} g" if kq else "14 g / 1.000 kcal"
    nuoc = f"{kq['nuoc_nghi']:g}–{kq['nuoc_tap']:g} lít" if kq else "35 ml / kg + 0,5 L mỗi giờ tập"
    return [f"Chất xơ {xo} / ngày (14 g / 1.000 kcal — IOM)", "Rau + trái cây ≥ 400 g / ngày, đổi màu, đổi loại (WHO)",
            f"Nước {nuoc} / ngày (ước lượng)", "Muối: natri < 2.000 mg / ngày ≈ 1 thìa cà phê muối, gồm cả nước mắm, nước chấm (WHO)",
            "Canxi ~1.000 mg / ngày: sữa, sữa chua, đậu hũ, cá nhỏ ăn cả xương, rau xanh đậm",
            "Vitamin D: nắng sáng 10–20 phút, cá béo, trứng — nếu ít ra nắng, hỏi bác sĩ xét nghiệm trước khi uống liều cao",
            ("Sắt ~18 mg / ngày (nữ): thịt bò, gan, huyết, rau xanh + vitamin C; mệt, rụng tóc, kinh nhiều → xét nghiệm"
             if nu else "Sắt ~8 mg / ngày (nam): thịt đỏ 2–3 bữa / tuần là đủ"),
            "Omega-3: cá béo (cá hồi, cá thu, cá nục) ≥ 2 bữa / tuần"]


def them(L: dict, k: dict, hs: dict, mt_: str, nu: bool) -> None:
    """Gắn thêm: giáo án + liều theo giai đoạn, volume mục tiêu, tạ hiện tại, deload, macro, vi chất, phục hồi, bổ sung."""
    ma = k["ma"]
    G, n = L["gd"], L["tong"]
    g_an = ga.current(ma)
    vc = vo.cai_dat(ma)
    from core import thong_tin as ttin
    lv = ttin.trinh_do(k, vc["trinh_do"] if vc["trinh_do"] is not None else (g_an or {}).get("trinh_do", 0))
    td, uu = vo.nhom_td(lv), vc["uu_tien"]
    goal = (g_an or {}).get("muc_tieu", "giam_mo")
    dl = tuan_deload(n, G)
    L.update({"deload": dl, "uu_tien": uu, "trinh_do": ga.LEVELS[int(lv or 0)], "co_giao_an": bool(g_an)})
    # macro
    kq = None
    try:
        h = dd.HoSo.tu_dict(hs) if hs.get("kg") and hs.get("cao") else None
        kq = dd.tinh(h) if h else None
    except Exception:  # noqa: BLE001 — thiếu số liệu thì bỏ phần macro
        kq = None
    L["macro"] = None if not kq else {"tap": kq["tap"], "nghi": kq["nghi"], "dam_g_kg": kq["dam_g_kg"]}
    L["vi_chat"] = vi_chat(kq, nu)
    L["bo_sung"] = [f"{x['icon']} {x['ten']} — {x['lieu']}" for x in dd.bo_sung(dd.HoSo.tu_dict(hs), hs.get("bo_sung"))] if hs else []
    L["phuc_hoi"] = ["Ngủ 7–9 tiếng / đêm, giờ ngủ cố định — ngủ thiếu làm giảm sức tập và khó giữ cơ khi giảm mỡ",
                     "Mỗi nhóm cơ nghỉ ≥ 48 giờ trước khi tập nặng lại",
                     "Ngày nghỉ: đi bộ, giãn cơ 10 phút; đau khớp nhói / sưng → báo HLV, không tập xuyên đau",
                     "Theo dõi hằng tuần: tạ có tăng không, ngủ, đau mỏi, cân TB 7 ngày → HLV chỉnh volume / năng lượng"]
    # tạ hiện tại của bài chính
    ta = []
    if g_an:
        hist = bu.sessions(ma)
        ids = []
        for b in g_an["buoi"]:
            for it in b.get("bai", []):
                if it.get("loai") in ("C", "M") and it["id"] not in ids:
                    ids.append(it["id"])
        for eid in ids:
            last = bu.last_for(ma, eid, hist)
            if not last:
                continue
            hs_ = [x for x in last["hiep"] if (tv.num(x.get("kg"), 0) or 0) > 0 and (tv.num(x.get("lan"), 0) or 0) > 0]
            if not hs_:
                continue
            top = max(hs_, key=lambda x: tv.num(x.get("kg"), 0) or 0)
            e = bu.best_1rm(last)
            ta.append({"bai": ga.ex(eid)["ten"], "ngay": last["ngay"], "top": f"{tv.num(top['kg']):g} kg × {int(tv.num(top['lan']))}",
                       "e1rm": e})
    L["ta"] = ta
    for i, g in enumerate(G):
        g["deload"] = [w for w in dl if g["tu"] <= w <= g["den"]]
        g["volume"] = [{"co": c, "ten": vo.CO[c][0], "uu_tien": c in {x for u in uu for x in vo.UU_TIEN[u][1]},
                        "hiep": vo.muc_giai_doan(c, td, uu, i, len(G))} for c in vo.CHINH]
        g["giao_an"] = []
        if g_an:
            for b in g_an["buoi"]:
                rows = []
                for it in b.get("bai", []):
                    x = ga.rx({**it, **({"circuit": True} if b.get("circuit") else {})}, goal, g["tu"], int(lv or 0))
                    rows.append({"bai": it["ten"], "lieu": x["lieu"], "rir": x.get("rpe") or x.get("rir") or "", "nghi": x.get("nghi", "")})
                g["giao_an"].append({"ten": f"Buổi {b.get('ma', '')} · {b.get('ten', '')}", "bai": rows})
        if L["macro"]:
            m = L["macro"]
            g["an"].insert(1, f"Ngày tập ≈ {m['tap']['kcal']:,} kcal · đạm {m['tap']['p']} · tinh bột {m['tap']['c']} · béo {m['tap']['f']} g".replace(",", ".")
                           + f" — ngày nghỉ ≈ {m['nghi']['kcal']:,} kcal · đạm {m['nghi']['p']} · tinh bột {m['nghi']['c']} · béo {m['nghi']['f']} g".replace(",", ".")
                           + (" (số hiện tại — HLV chỉnh theo tiến độ)" if i else ""))
