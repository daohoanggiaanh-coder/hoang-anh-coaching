# Hoàng Anh Coaching v2.1 (2026-11-05) — VOLUME TUẦN theo nhóm cơ + bản đồ cơ thể + đánh giá theo mục tiêu ưu tiên.
"""Cách đếm (khung thực hành, không phải chân lý tuyệt đối):
- 1 "hiệp nặng" = hiệp làm gần thất bại (chừa ≤ 3–4 lần). Hiệp khởi động, bài kích hoạt / giãn cơ, bật nhảy, thể lực, strongman không tính.
- Cơ chính của bài tính 1 hiệp, cơ phụ tính ½ hiệp (cách đếm "hiệp quy đổi", ví dụ đẩy ngực: ngực 1, tay sau ½, vai trước ½).
- Mốc volume / tuần (duy trì · tối thiểu hiệu quả · vùng tăng cơ tốt · trần) dựa trên khái niệm MV / MEV / MAV / MRV của
  Renaissance Periodization (Israetel) và tổng quan liều – đáp ứng (Schoenfeld & cs. 2017: ≥ 10 hiệp / nhóm cơ / tuần tăng cơ
  nhiều hơn < 5 hiệp). Con số cụ thể là mức HLV chọn, cần chỉnh theo khả năng hồi phục của từng khách.
"""
from __future__ import annotations

from datetime import date, timedelta

from core import buoi, db, ga_atlas as ga, tu_van as tv

# id → {cơ: hệ số}
MAP: dict[str, dict[str, float]] = {}


def _m(ids: str, **co: float) -> None:
    for i in ids.split():
        MAP[i] = co


_m("smith_squat db_goblet leg_press", dui_truoc=1, mong=0.5, khep_dui=0.5)
_m("smith_sumo", dui_truoc=1, khep_dui=1, mong=0.5)
_m("db_rdl bb_rdl b_stance_rdl", dui_sau=1, mong=1, lung_duoi=0.5)
_m("bb_deadlift", mong=1, lung_duoi=1, dui_sau=0.5, dui_truoc=0.5, lung_giua=0.5)
_m("bb_hip_thrust glute_trainer sl_hip_thrust cable_pull_through", mong=1, dui_sau=0.5)
_m("back_ext", lung_duoi=1, mong=0.5, dui_sau=0.5)
_m("db_reverse_lunge db_walking_lunge db_bulgarian db_stepup curtsy_lunge", dui_truoc=1, mong=1, khep_dui=0.5)
_m("bb_bench db_bench chest_press push_up", nguc=1, tay_sau=0.5, vai_truoc=0.5)
_m("bb_incline db_incline", nguc=1, vai_truoc=0.5, tay_sau=0.5)
_m("db_row bb_row cable_row smith_inverted", lung_giua=1, xo=0.5, vai_sau=0.5, tay_truoc=0.5)
_m("lat_pulldown assisted_pullup pull_up", xo=1, lung_giua=0.5, tay_truoc=0.5)
_m("db_shoulder smith_ohp shoulder_press", vai_truoc=1, vai_giua=0.5, tay_sau=0.5)
_m("leg_curl", dui_sau=1)
_m("leg_ext", dui_truoc=1)
_m("abduction cable_kickback frog_pump", mong=1)
_m("db_lateral", vai_giua=1)
_m("rear_delt cable_face_pull", vai_sau=1, lung_giua=0.5)
_m("pec_deck cable_crossover", nguc=1)
_m("db_curl db_hammer", tay_truoc=1)
_m("cable_pushdown cable_overhead_ext", tay_sau=1)
_m("weighted_plank lying_leg_raise cable_crunch dead_bug mcgill_curl_up hang_knee_raise", bung=1)
_m("side_plank", lien_suon=1)
_m("pallof_press", lien_suon=1, bung=0.5)
_m("bird_dog_core", lung_duoi=1)

# cơ: (tên, hệ số mốc, mặt trước / sau)
CO = {
    "nguc": ("Ngực", 1.0), "vai_truoc": ("Vai trước", 0.6), "vai_giua": ("Vai giữa", 1.0), "vai_sau": ("Vai sau", 0.8),
    "xo": ("Xô (lưng rộng)", 1.0), "lung_giua": ("Lưng giữa · cầu vai", 1.0), "tay_truoc": ("Tay trước", 0.8),
    "tay_sau": ("Tay sau", 0.8), "bung": ("Bụng", 0.7), "lien_suon": ("Cơ liên sườn (eo)", 0.5),
    "lung_duoi": ("Lưng dưới", 0.5), "mong": ("Mông", 1.0), "dui_truoc": ("Đùi trước", 1.0), "dui_sau": ("Đùi sau", 0.9),
    "khep_dui": ("Đùi trong (khép)", 0.5), "bap_chan": ("Bắp chân", 0.8),
}
NHOM_TD = ["moi", "tb", "tb", "cao", "cao"]              # theo ga.LEVELS (0 Người mới … 4 Chuyên nghiệp)
TEN_TD = {"moi": "Người mới (< 6–12 tháng tập đều)", "tb": "Trung cấp (1–3 năm)", "cao": "Nâng cao (> 3 năm)"}
MOC = {  # hiệp nặng / tuần cho nhóm cơ hệ số 1: (duy trì, tối thiểu hiệu quả, vùng tốt — cận trên, trần nên vượt)
    "moi": (4, 6, 12, 16), "tb": (6, 8, 16, 20), "cao": (6, 10, 20, 24),
}
UU_TIEN = {  # mục tiêu hình thể → (tên, cơ ưu tiên, cơ hỗ trợ, ghi chú)
    "mong": ("🍑 Tăng mông", ["mong"], ["dui_sau", "khep_dui"],
             "Mông cần nhiều volume nhất trong tuần: hip thrust / glute trainer + RDL + bài 1 chân + dạng háng."),
    "nguc": ("💪 Tăng ngực", ["nguc"], ["vai_truoc", "tay_sau"], "Đẩy ngang + đẩy dốc + ép ngực; tập ngực 2 lần / tuần."),
    "vai": ("🔷 Vai tròn, to", ["vai_giua", "vai_sau"], ["vai_truoc"], "Vai trước đã có từ bài đẩy — dồn volume cho vai giữa và vai sau."),
    "lung": ("🦅 Lưng chữ V", ["xo", "lung_giua"], ["vai_sau", "tay_truoc"], "Cả kéo dọc (xô) và kéo ngang (lưng giữa) mỗi tuần."),
    "tay": ("💪 Tay to, săn", ["tay_truoc", "tay_sau"], [], "Tay đã nhận ½ hiệp từ bài kéo / đẩy — thêm 4–8 hiệp cô lập mỗi bên."),
    "chan": ("🦵 Đùi săn / to", ["dui_truoc", "dui_sau"], ["mong", "khep_dui"], "Squat / leg press + RDL / leg curl, 2 lần / tuần."),
    "bung": ("🔥 Giảm mỡ bụng, eo thon", [], ["bung", "lien_suon"],
             "Không đốt mỡ tại chỗ được — mỡ bụng giảm theo thâm hụt năng lượng cả ngày + bước chân + cardio. "
             "Bụng chỉ cần 6–10 hiệp / tuần để săn và khoẻ lưng."),
    "toan_than": ("⚖️ Cân đối toàn thân", [], [], "Mọi nhóm cơ chính ở vùng hiệu quả, không nhóm nào bị bỏ."),
}
TRANG_THAI = {  # mã: (tên, màu)
    "chua": ("Chưa tập", "#B9B1A0"), "thieu": ("Thiếu", "#B4442F"), "duy_tri": ("Duy trì", "#E08A3C"),
    "hieu_qua": ("Hiệu quả", "#7FB069"), "tot": ("Tối ưu", "#2E7D4F"), "qua": ("Quá nhiều", "#6B4BA3"), "na": ("Không có bài", "#E7E1D4"),
}
CHINH = ["nguc", "xo", "lung_giua", "vai_giua", "vai_sau", "tay_truoc", "tay_sau", "mong", "dui_truoc", "dui_sau", "bung"]


def nhom_td(level: int | None) -> str:
    return NHOM_TD[max(0, min(4, int(level or 0)))]


def moc(co: str, td: str) -> tuple[float, float, float, float]:
    f = CO[co][1]
    return tuple(round(x * f * 2) / 2 for x in MOC[td])           # làm tròn 0,5 hiệp


def tinh_bai(eid: str, so_hiep: float, out: dict[str, float]) -> bool:
    m = MAP.get(eid)
    if not m:
        return False
    for co, h in m.items():
        out[co] = out.get(co, 0.0) + so_hiep * h
    return True


def _so_hiep_log(b: dict) -> int:
    n = 0
    for s in b.get("hiep") or []:
        if (tv.num(s.get("lan"), 0) or 0) > 0 or (tv.num(s.get("kg"), 0) or 0) > 0 or str(s.get("giay") or "").strip():
            n += 1
    return n


def tuan(ma: str, thu_hai: date) -> dict:
    """Volume ĐÃ TẬP trong tuần (thứ 2 → CN) từ nhật ký buổi."""
    cn = thu_hai + timedelta(days=6)
    out: dict[str, float] = {}
    bo: dict[str, int] = {}
    so_buoi = 0
    for s in buoi.sessions(ma):
        if not (thu_hai <= s["ngay"] <= cn):
            continue
        so_buoi += 1
        for b in s["bai"]:
            n = _so_hiep_log(b)
            if n and not tinh_bai(str(b.get("id") or ""), n, out):
                bo[b.get("ten") or str(b.get("id"))] = bo.get(b.get("ten") or str(b.get("id")), 0) + n
    return {"co": out, "khong_ro": bo, "so_buoi": so_buoi}


def ke_hoach(g: dict | None, tuan_so: int | None = None) -> dict:
    """Volume THEO GIÁO ÁN đang dùng, quy về 1 tuần (chu kỳ buổi có thể dài hơn số buổi / tuần)."""
    if not g or not g.get("buoi"):
        return {"co": {}, "khong_ro": {}, "so_buoi": 0}
    goal, lv = g.get("muc_tieu", "giam_mo"), int(g.get("trinh_do") or 0)
    wk = tuan_so or ga.week_no(g.get("ngay_bat_dau"))
    ds = g["buoi"]
    he = int(g.get("buoi_tuan") or len(ds)) / max(len(ds), 1)
    out: dict[str, float] = {}
    for bu in ds:
        for it in bu.get("bai", []):
            x = ga.rx({**it, **({"circuit": True} if bu.get("circuit") else {})}, goal, wk, lv)
            if bu.get("circuit"):
                continue
            tinh_bai(it["id"], ga._so_hiep(x["lieu"]) * he, out)
    return {"co": out, "khong_ro": {}, "so_buoi": int(g.get("buoi_tuan") or len(ds))}


def muc_tieu_co(co: str, td: str, uu: list[str], giam_mo: bool) -> tuple[float, float]:
    """(mức cần đạt, mức nên dừng) cho 1 nhóm cơ theo mục tiêu ưu tiên của khách."""
    mv, mev, mav, mrv = moc(co, td)
    pri = {c for u in uu for c in UU_TIEN.get(u, ("", [], [], ""))[1]}
    if co in pri:
        return round(((mev + mav) / 2) * 2) / 2, mrv
    if co in ("bung", "lien_suon", "lung_duoi", "khep_dui", "vai_truoc"):
        return mv, mav
    return (mv if giam_mo else mev), mav


def danh_gia(vol: dict[str, float], td: str, uu: list[str], giam_mo: bool) -> list[dict]:
    out = []
    pri = {c for u in uu for c in UU_TIEN.get(u, ("", [], [], ""))[1]}
    ho_tro = {c for u in uu for c in UU_TIEN.get(u, ("", [], [], ""))[2]}
    for co, (ten, _f) in CO.items():
        v = round(vol.get(co, 0.0), 1)
        mv, mev, mav, mrv = moc(co, td)
        can, tran = muc_tieu_co(co, td, uu, giam_mo)
        if co not in {c for m in MAP.values() for c in m}:
            tt = "na"
        elif v <= 0:
            tt = "chua"
        elif v > mrv:
            tt = "qua"
        elif v < mv:
            tt = "thieu"
        elif v < mev:
            tt = "duy_tri"
        elif v < (mev + mav) / 2:
            tt = "hieu_qua"
        else:
            tt = "tot"
        dat = v >= can and v <= tran * 1.2
        out.append({"co": co, "ten": ten, "hiep": v, "tt": tt, "moc": (mv, mev, mav, mrv), "can": can, "tran": tran,
                    "dat": dat, "uu_tien": co in pri, "ho_tro": co in ho_tro})
    return out


def bai_cho_co(co: str, limits: list[str] | None = None, level: int = 4) -> list[str]:
    """Tên bài có cơ chính = co (để gợi ý thêm hiệp)."""
    out = []
    for i, m in MAP.items():
        if m.get(co) == 1 and ga.allowed(i, level, limits or []):
            e = tv.exercise(i)
            if e:
                out.append(e["ten"])
    return out[:4]


def nhan_xet(rows: list[dict], uu: list[str], limits: list[str] | None = None, level: int = 4,
             so_buoi: int = 0, ke_hoach_buoi: int = 0) -> list[str]:
    R = {r["co"]: r for r in rows}
    out = []
    if ke_hoach_buoi and so_buoi == 0:
        return [f"Tuần này chưa ghi buổi nào (kế hoạch {ke_hoach_buoi} buổi). Xem \"Theo giáo án\" để biết volume dự kiến."]
    if ke_hoach_buoi and so_buoi < ke_hoach_buoi:
        out.append(f"Mới tập {so_buoi}/{ke_hoach_buoi} buổi tuần này — volume thấp chủ yếu do thiếu buổi, chưa phải do giáo án.")
    for u in uu:
        ten, chinh, _ht, ghi = UU_TIEN.get(u, ("", [], [], ""))
        for c in chinh:
            r = R[c]
            if r["hiep"] < r["can"]:
                thieu = r["can"] - r["hiep"]
                out.append(f"{ten}: {r['ten'].lower()} {r['hiep']:g}/{r['can']:g} hiệp — thiếu khoảng {thieu:.0f} hiệp. "
                           f"Thêm: {', '.join(bai_cho_co(c, limits, level)[:3])}.")
            elif r["hiep"] > r["tran"]:
                out.append(f"{ten}: {r['ten'].lower()} {r['hiep']:g} hiệp — vượt trần {r['tran']:g}, dễ quá tải; bớt 2–4 hiệp hoặc theo dõi hồi phục.")
            else:
                out.append(f"{ten}: {r['ten'].lower()} {r['hiep']:g} hiệp — ĐỦ cho mục tiêu ✅")
        if u == "bung":
            out.append("🔥 " + ghi)
    yeu = [r for r in rows if r["co"] in CHINH and not r["uu_tien"] and r["tt"] in ("chua", "thieu")]
    if yeu:
        out.append("Nhóm cơ dưới mức duy trì: " + ", ".join(f"{r['ten'].lower()} ({r['hiep']:g})" for r in yeu)
                   + " — để lâu có thể mất cơ / mất cân đối.")
    qua = [r for r in rows if r["tt"] == "qua" and not r["uu_tien"]]
    if qua:
        out.append("Vượt trần: " + ", ".join(r["ten"].lower() for r in qua) + " — cân nhắc bớt để dành sức hồi phục cho nhóm ưu tiên.")
    return out or ["Volume các nhóm cơ đang cân đối."]


# ------------------------------------------------------------------ cài đặt mục tiêu hình thể (lưu bảng DinhDuong)
def cai_dat(ma: str) -> dict:
    v = db.latest("DinhDuong", ma).get(f"vol|{ma}") or {}
    return {"uu_tien": [x for x in (v.get("uu_tien") or []) if x in UU_TIEN], "trinh_do": v.get("trinh_do")}


def luu_cai_dat(ma: str, v: dict, nguoi: str) -> bool:
    return db.append("DinhDuong", f"vol|{ma}", v | {"ma_kh": ma}, nguoi, ma)


def muc_giai_doan(co: str, td: str, uu: list[str], gd: int, so_gd: int) -> str:
    """Volume gợi ý theo giai đoạn: đầu khoá gần mức tối thiểu, tăng dần, giai đoạn cuối gần cận trên vùng tốt."""
    mv, mev, mav, mrv = moc(co, td)
    pri = {c for u in uu for c in UU_TIEN.get(u, ("", [], [], ""))[1]}
    if so_gd <= 1:
        a, b = mev, (mev + mav) / 2
    elif gd == 0:
        a, b = (mv, mev) if co not in pri else (mev, (mev + mav) / 2)
    elif gd == so_gd - 1:
        a, b = ((mev + mav) / 2, mav) if co in pri else (mev, (mev + mav) / 2)
    else:
        a, b = (mev, (mev + mav) / 2) if co not in pri else ((mev + mav) / 2, mav)
    r = lambda x: f"{round(x):g}"   # noqa: E731
    return f"{r(a)}–{r(b)}"
