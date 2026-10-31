# Atlas Academy v3.28 (2026-10-14) — Tư vấn F1·F2: chấm theo thang chuẩn nam/nữ (có biến thể khi thiếu dụng cụ),
# tuổi cơ thể, đọc phiếu InBody từ ảnh, phân tích OHS, sinh lộ trình 12 tuần và đề xuất gói tập
"""
Nguyên tắc "Python tính số": mọi xếp loại so với thang chuẩn trong data/chuan_danh_gia.json.
Hồ sơ khách là 1 dict phẳng (lưu được vào Google Sheets 1 dòng).
"""
from __future__ import annotations

import json
from datetime import date, datetime

from core import config

PACKAGES = [  # giá Atlas (anh Peach cung cấp 03/10/2026)
    {"id": "g12", "ten": "Gói 12 buổi Toàn diện", "buoi": 12, "gia": 5_000_000},
    {"id": "g24", "ten": "Gói 24 buổi Toàn diện", "buoi": 24, "gia": 9_500_000},
]
BONUS_F2 = "Đăng ký ngay sau buổi F1: buổi F2 miễn phí được cộng vào gói."
GOALS = {
    "giam_mo": "Giảm mỡ, gọn dáng",
    "tang_co": "Tăng cơ, tăng cân nạc",
    "recomp": "Săn chắc (giảm mỡ – tăng cơ)",
    "suc_khoe": "Sức khoẻ, giảm đau mỏi",
    "suc_manh": "Tăng sức mạnh",
}
PARQ = [
    "Bác sĩ có từng nói bạn bị bệnh tim và chỉ nên tập thể dục khi có sự giám sát của y tế không?",
    "Bạn có cảm thấy đau ngực khi tham gia các hoạt động thể chất không?",
    "Trong tháng qua, bạn có bị đau ngực khi không tham gia hoạt động thể chất (đau khi nghỉ ngơi) không?",
    "Bạn có bao giờ bị mất thăng bằng do chóng mặt hoặc từng bị ngất xỉu không?",
    "Bạn có vấn đề về xương khớp (lưng, đầu gối, hông...) có thể trở nên tồi tệ hơn do thay đổi hoạt động thể chất không?",
    "Bạn có đang dùng thuốc điều trị huyết áp hoặc bệnh tim không?",
    "Bạn có biết lý do nào khác khiến bạn không nên tham gia hoạt động thể chất không?",
]
VONG = [("co", "Cổ"), ("nguc", "Ngực"), ("eo", "Eo (hẹp nhất)"), ("bung", "Bụng (ngang rốn)"),
        ("hong", "Hông / mông"), ("dui_t", "Đùi trái"), ("dui_p", "Đùi phải"),
        ("tay_t", "Bắp tay trái"), ("tay_p", "Bắp tay phải"), ("bap_chan", "Bắp chân")]


def norms() -> dict:
    return config.load_json("chuan_danh_gia.json")


def num(v, default=None):
    try:
        if v is None or str(v).strip() == "":
            return default
        return float(str(v).replace(",", "."))
    except ValueError:
        return default


def _scale(levels: list[dict], v):
    if v is None:
        return None
    for lv in levels:
        if v >= lv["tu"]:
            return {"nhan": lv["nhan"], "diem": lv["diem"]}
    return {"nhan": levels[-1]["nhan"], "diem": levels[-1]["diem"]}


def sex_key(gioi: str) -> str:
    return "nam" if str(gioi).lower().startswith("nam") else "nu"


def age(ngay_sinh, tuoi=None) -> int | None:
    if tuoi:
        return int(num(tuoi, 0)) or None
    try:
        d = ngay_sinh if isinstance(ngay_sinh, date) else datetime.strptime(str(ngay_sinh)[:10], "%Y-%m-%d").date()
    except ValueError:
        return None
    t = date.today()
    return t.year - d.year - ((t.month, t.day) < (d.month, d.day))


# ------------------------------------------------------------------ chấm từng chỉ số
def rate_bmi(kg, cm):
    kg, cm = num(kg), num(cm)
    if not kg or not cm:
        return None
    v = round(kg / (cm / 100) ** 2, 1)
    return {"gia_tri": v, **_scale(norms()["bmi"], v)}


def rate_pbf(pbf, gioi):
    v = num(pbf)
    return None if v is None else {"gia_tri": v, **_scale(norms()["pbf"][sex_key(gioi)], v)}


def rate_visceral(lv):
    v = num(lv)
    return None if v is None else {"gia_tri": v, **_scale(norms()["mo_noi_tang"], v)}


def variants(kind: str) -> list[dict]:
    return norms()["bien_the"][kind]


def variant(kind: str, vid=None, gioi=None) -> dict:
    """Biến thể đang chọn; mặc định: hít đất nam = chuẩn, nữ = quỳ gối; còn lại = biến thể đầu."""
    vs = variants(kind)
    if not vid and kind == "hit_dat":
        vid = "chuan" if sex_key(gioi) == "nam" else "quy_goi"
    return next((v for v in vs if v["id"] == vid), vs[0])


def rate_pushup(reps, gioi, tuoi, bt=None):
    v = num(reps)
    if v is None:
        return None
    t = norms()["hit_dat"]
    tb = t[sex_key(gioi)]
    base = variant("hit_dat", None, gioi)            # bài chuẩn của thang theo giới
    cur = variant("hit_dat", bt, gioi)
    eq = round(v * cur["he_so"] / base["he_so"], 1) if cur["id"] != base["id"] else v
    a = tuoi or 30
    row = next((i for i, (lo, hi) in enumerate(tb["tuoi"]) if lo <= a <= hi), 1)
    extra = {"bt": cur["ten"], "quy_doi": eq if eq != v else None, "bai_chuan": base["ten"].lower()}
    for i, th in enumerate(tb["tu"][row]):
        if eq >= th:
            return {"gia_tri": v, "nhan": t["nhan"][i], "diem": t["diem"][i],
                    "moc": dict(zip(t["nhan"], tb["tu"][row])), **extra}
    return {"gia_tri": v, "nhan": t["nhan"][-1], "diem": t["diem"][-1], "moc": {}, **extra}


def rate_plank(sec, bt=None, gioi=None):
    v = num(sec)
    if v is None:
        return None
    cur = variant("plank", bt)
    if cur.get("bang"):                                 # side plank: thang riêng theo giới
        return {"gia_tri": v, "bt": cur["ten"], "quy_doi": None, "bang": cur["bang"],
                **_scale(norms()[cur["bang"]][sex_key(gioi)], v)}
    eq = round(v * cur["he_so"]) if cur["he_so"] != 1 else v
    return {"gia_tri": v, "bt": cur["ten"], "quy_doi": eq if eq != v else None, **_scale(norms()["plank"], eq)}


def one_rm(kg, reps):
    """Epley: 1RM = tạ × (1 + reps/30); reps > 12 kém chính xác nên chặn ở 12."""
    kg, reps = num(kg), num(reps)
    if not kg or not reps:
        return None
    return round(kg * (1 + min(reps, 12) / 30), 1)


def rate_pulldown(kg, reps, can_nang, gioi, bt=None):
    """Sức kéo theo biến thể: máy kéo xô / cáp / tạ đơn → tỉ lệ 1RM ÷ cân nặng; dây, xà thấp, hít xà → số lần."""
    if not bt and num(kg):            # hồ sơ cũ (trước v3.1) không lưu biến thể, có số kg → ngồi kéo xô
        bt = "lat_pulldown"
    cur = variant("keo", bt)
    tbl = norms()[cur["bang"]][sex_key(gioi)]
    if cur["kieu"] == "so_lan":
        v = num(reps)
        return None if v is None else {"gia_tri": v, "bt": cur["ten"], "kieu": "so_lan", **_scale(tbl, v)}
    rm, bw = one_rm(kg, reps), num(can_nang)
    if not rm or not bw:
        return None
    ratio = round(rm / bw, 2)
    return {"gia_tri": ratio, "rm": rm, "bt": cur["ten"], "kieu": "ti_le", **_scale(tbl, ratio)}


def _age_table(tbl: dict, gioi, tuoi, v, lower_better=False):
    """Bảng chuẩn theo tuổi/giới (dạng hít đất / YMCA). lower_better: dùng 'max' (nhịp tim càng thấp càng tốt)."""
    t = tbl[sex_key(gioi)]
    a = tuoi or 30
    row = next((i for i, (lo, hi) in enumerate(t["tuoi"]) if lo <= a <= hi), 1)
    if lower_better:
        cuts = t["max"][row]
        for i, th in enumerate(cuts):
            if v <= th:
                return {"nhan": tbl["nhan"][i], "diem": tbl["diem"][i], "moc": dict(zip(tbl["nhan"], cuts))}
        return {"nhan": tbl["nhan"][-1], "diem": tbl["diem"][-1], "moc": dict(zip(tbl["nhan"], cuts))}
    cuts = t["tu"][row]
    for i, th in enumerate(cuts):
        if v >= th:
            return {"nhan": tbl["nhan"][i], "diem": tbl["diem"][i], "moc": dict(zip(tbl["nhan"], cuts))}
    return {"nhan": tbl["nhan"][-1], "diem": tbl["diem"][-1], "moc": dict(zip(tbl["nhan"], cuts))}


def vo2_rockport(phut, giay, hr, can_nang, gioi, tuoi):
    """Rockport (Kline 1987): VO₂max = 132,853 − 0,0769·cân(lb) − 0,3877·tuổi + 6,315·nam − 3,2649·phút − 0,1565·nhịp tim."""
    t, hr, kg = (num(phut) or 0) + (num(giay) or 0) / 60, num(hr), num(can_nang)
    if not t or not hr or not kg or not tuoi:
        return None
    v = 132.853 - 0.0769 * kg * 2.20462 - 0.3877 * tuoi + 6.315 * (sex_key(gioi) == "nam") - 3.2649 * t - 0.1565 * hr
    return round(v, 1)


def rate_cardio(h: dict, gioi, tuoi):
    """Sức bền tim mạch theo biến thể: YMCA (nhịp tim hồi phục) · Rockport (VO₂max) · bước tại chỗ 2 phút (≥ 60 tuổi)."""
    cur = variant("tim_mach", h.get("bt_ymca"))
    if cur["id"] == "rockport":
        v = vo2_rockport(h.get("rp_phut"), h.get("rp_giay"), h.get("rp_hr"), h.get("can_nang"), gioi, tuoi)
        if v is None:
            return None
        return {"gia_tri": v, "bt": cur["ten"], "kieu": "vo2", **_age_table(norms()["vo2max"], gioi, tuoi, v)}
    if cur["id"] == "buoc_2phut":
        v = num(h.get("step2_reps"))
        if v is None:
            return None
        t = norms()["buoc_2phut"]
        a = tuoi or 70
        row = next((i for i, (lo, hi) in enumerate(t["tuoi"]) if lo <= a <= hi), 0)
        lo, hi = t[sex_key(gioi)][row]
        lab, dm = ("Trên chuẩn", 5) if v > hi else ("Đạt chuẩn", 4) if v >= lo else ("Dưới chuẩn", 2)
        return {"gia_tri": v, "bt": cur["ten"], "kieu": "buoc", "nhan": lab, "diem": dm, "khoang": [lo, hi]}
    r = rate_ymca(h.get("ymca_hr"), gioi, tuoi)
    return {**r, "bt": cur["ten"], "kieu": "ymca"} if r else None


def rate_ymca(hr, gioi, tuoi):
    """YMCA 3 phút bước bục: nhịp tim 1 phút sau test, càng thấp càng tốt."""
    v = num(hr)
    if not v:
        return None
    return {"gia_tri": v, **_age_table(norms()["ymca"], gioi, tuoi, v, lower_better=True)}


def rate_squat(h: dict, gioi, tuoi):
    """Squat theo biến thể: OHS → số điểm bù trừ (thẻ ③); tay không / goblet → số lần 60 giây theo tuổi/giới."""
    cur = variant("squat", h.get("bt_squat"))
    if cur["kieu"] == "ohs":
        o = ohs_findings(h)
        if o["so_loi"] is None:
            return None
        return {"gia_tri": o["so_loi"], "bt": cur["ten"], "kieu": "ohs", **_scale(norms()["ohs_diem"][::-1], o["so_loi"])}
    v = num(h.get("squat_reps"))
    if v is None:
        return None
    eq = round(v * cur.get("he_so", 1), 1)
    return {"gia_tri": v, "bt": cur["ten"], "kieu": "so_lan", "quy_doi": eq if eq != v else None,
            **_age_table(norms()["squat_1phut"], gioi, tuoi, eq)}


def rate_flex(cm):
    v = num(cm)
    return None if v is None else {"gia_tri": v, **_scale(norms()["deo_dai"], v)}


def rate_bp(sys_, dia):
    s, d = num(sys_), num(dia)
    if not s or not d:
        return None
    if s >= 180 or d >= 110:
        return {"gia_tri": f"{s:.0f}/{d:.0f}", "nhan": "Rất cao — HOÃN TẬP, khuyên đi khám", "diem": 1, "hoan": True}
    if s >= 140 or d >= 90:
        return {"gia_tri": f"{s:.0f}/{d:.0f}", "nhan": "Tăng huyết áp độ 2", "diem": 1, "hoan": False}
    if s >= 130 or d >= 80:
        return {"gia_tri": f"{s:.0f}/{d:.0f}", "nhan": "Tăng huyết áp độ 1", "diem": 2, "hoan": False}
    if s >= 120:
        return {"gia_tri": f"{s:.0f}/{d:.0f}", "nhan": "Huyết áp hơi cao", "diem": 3, "hoan": False}
    return {"gia_tri": f"{s:.0f}/{d:.0f}", "nhan": "Bình thường", "diem": 5, "hoan": False}


def rate_waist(eo, hong, cao, gioi):
    eo, hong, cao = num(eo), num(hong), num(cao)
    if not eo:
        return None
    sk = sex_key(gioi)
    out = {"eo": eo, "eo_vuot": eo >= norms()["vong_eo_nguong"][sk], "nguong_eo": norms()["vong_eo_nguong"][sk]}
    if hong:
        out["whr"] = round(eo / hong, 2)
        out["whr_vuot"] = out["whr"] >= norms()["whr_nguong"][sk]
    if cao:
        out["whtr"] = round(eo / cao, 2)
    out["diem"] = 2 if out["eo_vuot"] or out.get("whr_vuot") else 5
    out["nhan"] = "Béo bụng — nguy cơ chuyển hoá" if out["diem"] == 2 else "Đạt chuẩn"
    return out


# ------------------------------------------------------------------ tổng hợp
def evaluate(h: dict) -> dict:
    """h = hồ sơ phẳng → kết quả xếp loại từng chỉ số + điểm tổng 0–100 + cờ an toàn."""
    tuoi = age(h.get("ngay_sinh"), h.get("tuoi"))
    gioi = h.get("gioi_tinh", "Nam")
    r = {
        "tuoi": tuoi,
        "bmi": rate_bmi(h.get("can_nang"), h.get("chieu_cao")),
        "pbf": rate_pbf(h.get("pbf"), gioi),
        "mo_noi_tang": rate_visceral(h.get("mo_noi_tang")),
        "huyet_ap": rate_bp(h.get("ha_tam_thu"), h.get("ha_tam_truong")),
        "hit_dat": rate_pushup(h.get("hit_dat"), gioi, tuoi, h.get("bt_hit_dat")),
        "plank": rate_plank(h.get("plank"), h.get("bt_plank"), gioi),
        "keo_xo": rate_pulldown(h.get("keo_xo_kg"), h.get("keo_xo_reps"), h.get("can_nang"), gioi, h.get("bt_keo")),
        "deo_dai": rate_flex(h.get("deo_dai")),
        "ymca": rate_cardio(h, gioi, tuoi),
        "squat": rate_squat(h, gioi, tuoi),
        "vong_eo": rate_waist(h.get("v_eo"), h.get("v_hong"), h.get("chieu_cao"), gioi),
    }
    parq_yes = [i + 1 for i in range(len(PARQ)) if str(h.get(f"parq_{i+1}", "")).lower() in ("có", "co", "true", "1")]
    r["parq_co"] = parq_yes
    r["can_bac_si"] = bool(parq_yes)
    r["hoan_tap"] = bool(r["huyet_ap"] and r["huyet_ap"].get("hoan"))
    # điểm tổng: trung bình các chỉ số có dữ liệu (thang 1–5 → 0–100)
    keys = ["bmi", "pbf", "mo_noi_tang", "huyet_ap", "ymca", "hit_dat", "plank", "keo_xo", "deo_dai"]
    if r["squat"] and r["squat"].get("kieu") != "ohs":
        keys.append("squat")
    pts = [r[k]["diem"] for k in keys if r[k]]
    ohs = ohs_findings(h)
    if pts or ohs["so_loi"] is not None:
        mv = max(1, 5 - ohs["so_loi"]) if ohs["so_loi"] is not None else None
        allp = pts + ([mv] if mv else [])
        r["diem_tong"] = round((sum(allp) / len(allp) - 1) / 4 * 100)
    else:
        r["diem_tong"] = None
    r["ohs"] = ohs
    r["radar"] = radar(r, ohs)
    r["tuoi_co_the"] = body_age(h, r)
    return r


# ------------------------------------------------------------------ tuổi cơ thể
def body_age(h: dict, r: dict) -> dict | None:
    """Tuổi cơ thể Atlas = tuổi thật + Δ mỡ + Δ mỡ nội tạng + Δ cơ + Δ thể lực (hệ số trong chuan_danh_gia.json).
    Cần tuổi + ít nhất 1 chỉ số InBody. Trả từng thành phần để PT giải thích cho khách."""
    tuoi = r.get("tuoi")
    if not tuoi:
        return None
    c = norms()["tuoi_co_the"]
    sk = sex_key(h.get("gioi_tinh"))
    parts = []
    pbf = num(h.get("pbf"))
    if pbf is not None:
        d = max(-c["tran_mo"], min(c["tran_mo"], (pbf - c["pbf_chuan"][sk]) * c["nam_moi_diem_pbf"]))
        parts.append(("Tỉ lệ mỡ", d, f"{pbf:g}% so với mức khoẻ {c['pbf_chuan'][sk]}%"))
    vf = num(h.get("mo_noi_tang"))
    if vf is not None:
        d = (vf - c["noi_tang_nguong"]) * c["nam_moi_muc_noi_tang"] if vf > c["noi_tang_nguong"] else \
            (c["thuong_noi_tang_tot"] if vf <= c["noi_tang_tot"] else 0)
        parts.append(("Mỡ nội tạng", d, f"mức {vf:g} (bình thường 1–{c['noi_tang_nguong']})"))
    smm, kg = num(h.get("smm")), num(h.get("can_nang"))
    if smm and kg:
        ratio = smm / kg
        d = max(-c["tran_co"], min(c["tran_co"], (c["smm_ti_le_chuan"][sk] - ratio) * 100 * c["nam_moi_1pt_smm"]))
        parts.append(("Khối cơ", d, f"cơ chiếm {ratio * 100:.0f}% cân nặng (chuẩn {c['smm_ti_le_chuan'][sk] * 100:.0f}%)"))
    if not parts:
        return None
    fit = [r[k]["diem"] for k in ("ymca", "squat", "hit_dat", "plank", "keo_xo", "deo_dai") if r.get(k)]
    if fit:
        avg = sum(fit) / len(fit)
        d = max(-c["tran_the_luc"], min(c["tran_the_luc"], (c["the_luc_moc"] - avg) * c["nam_moi_bac_the_luc"]))
        parts.append(("Thể lực", d, f"điểm bài test trung bình {avg:.1f}/5"))
    total = sum(p[1] for p in parts)
    total = max(-c["bien_do"], min(c["bien_do"], total))
    val = max(c["toi_thieu"], round(tuoi + total))
    may = num(h.get("tuoi_may"))
    return {"tuoi": tuoi, "gia_tri": val, "chenh": val - tuoi,
            "chi_tiet": [{"ten": a, "delta": round(b, 1), "giai_thich": e} for a, b, e in parts],
            "tuoi_may": int(may) if may else None,
            "diem": 5 if val - tuoi <= -3 else 4 if val - tuoi <= 0 else 3 if val - tuoi <= 3 else 2 if val - tuoi <= 7 else 1}


# ------------------------------------------------------------------ đọc phiếu InBody từ ảnh
INBODY_FIELDS = {  # khoá: (nhãn, min, max)
    "chieu_cao": ("Chiều cao (cm)", 120, 220), "can_nang": ("Cân nặng (kg)", 30, 200),
    "smm": ("Khối cơ xương SMM (kg)", 5, 80), "khoi_mo": ("Khối mỡ (kg)", 1, 120),
    "pbf": ("% mỡ cơ thể (PBF)", 3, 60), "mo_noi_tang": ("Mức mỡ nội tạng", 1, 30),
    "bmr": ("BMR (kcal)", 600, 3500), "diem_inbody": ("Điểm InBody", 30, 120),
    "nuoc": ("Tổng nước cơ thể (lít)", 10, 80), "protein": ("Protein (kg)", 2, 30),
    "khoang_chat": ("Khoáng chất (kg)", 0.5, 10), "tuoi": ("Tuổi", 12, 90), "tuoi_may": ("Tuổi cơ thể (máy in)", 10, 100),
}
INBODY_PROMPT = (
    "Ảnh là phiếu kết quả máy đo InBody (có thể tiếng Anh, tiếng Việt hoặc tiếng Hàn; có thể chụp nghiêng, loá). "
    "Đọc ĐÚNG số in trên phiếu, KHÔNG suy đoán. Trả về JSON với các khoá sau (số thập phân dùng dấu chấm; "
    "không thấy thì để null): chieu_cao (Height, cm), can_nang (Weight, kg), smm (Skeletal Muscle Mass, kg), "
    "khoi_mo (Body Fat Mass, kg), pbf (PBF / Percent Body Fat, %), mo_noi_tang (Visceral Fat Level, số nguyên), "
    "bmr (Basal Metabolic Rate, kcal), diem_inbody (InBody Score), nuoc (Total Body Water, L), protein (Protein, kg), "
    "khoang_chat (Minerals, kg), tuoi (Age), gioi_tinh (\"Nam\" hoặc \"Nữ\" nếu phiếu ghi Male/Female), "
    "tuoi_may (Body Age / Metabolic Age nếu phiếu có in), ngay_do (ngày đo YYYY-MM-DD nếu có). "
    "Lấy giá trị đo của khách, không lấy khoảng chuẩn (Normal range) in bên cạnh.")


def clean_inbody(raw: dict) -> dict:
    """Chỉ giữ số hợp lệ trong khoảng cho phép (chặn AI đọc nhầm khoảng chuẩn / số lạ)."""
    out = {}
    for k, (_, lo, hi) in INBODY_FIELDS.items():
        v = num(raw.get(k))
        if v is not None and lo <= v <= hi:
            out[k] = int(round(v)) if k in ("mo_noi_tang", "bmr", "diem_inbody", "tuoi", "tuoi_may") else round(v, 1)
    g = str(raw.get("gioi_tinh") or "").strip().lower()
    if g in ("nam", "male", "m"):
        out["gioi_tinh"] = "Nam"
    elif g in ("nữ", "nu", "female", "f"):
        out["gioi_tinh"] = "Nữ"
    if out.get("khoi_mo") and out.get("can_nang") and not out.get("pbf"):
        out["pbf"] = round(out["khoi_mo"] / out["can_nang"] * 100, 1)
    return out


def read_inbody(img: bytes) -> dict:
    """Ảnh phiếu InBody (JPEG) → dict số đã kiểm tra. Lỗi AI → ném llm.LLMError."""
    from core import llm
    raw = llm.chat_json("Bạn là trợ lý nhập liệu phòng gym, đọc số chính xác từ ảnh phiếu đo.",
                        [{"role": "user", "content": INBODY_PROMPT}], images=[img], max_tokens=600, timeout=60)
    return clean_inbody(raw)


def radar(r: dict, ohs: dict) -> dict:
    """8 trục 0–100: Thành phần cơ thể · Tim mạch · Thân dưới · Kéo · Đẩy · Lõi · Dẻo dai · Vận động."""
    def p(x):
        return None if not x else round((x["diem"] - 1) / 4 * 100)
    comp = [v for v in (p(r["pbf"]), p(r["mo_noi_tang"]), p(r["bmi"])) if v is not None]
    return {
        "Thành phần cơ thể": round(sum(comp) / len(comp)) if comp else None,
        "Sức bền tim mạch": p(r.get("ymca")),
        "Sức bền thân dưới": p(r["squat"]) if r.get("squat") and r["squat"].get("kieu") != "ohs" else None,
        "Sức mạnh kéo": p(r["keo_xo"]),
        "Sức mạnh đẩy": p(r["hit_dat"]),
        "Sức bền lõi": p(r["plank"]),
        "Dẻo dai": p(r["deo_dai"]),
        "Chất lượng vận động": None if ohs["so_loi"] is None else max(0, 100 - ohs["so_loi"] * 20),
    }


def ohs_findings(h: dict) -> dict:
    tbl = norms()["ohs"]
    hit = [k for k in tbl if str(h.get(f"ohs_{k}", "")).lower() in ("true", "1", "có")]
    any_marked = any(str(h.get(f"ohs_{k}", "")) != "" for k in tbl) or h.get("ohs_da_lam")
    cang, yeu, sua = [], [], []
    for k in hit:
        for x in tbl[k]["cang"]:
            cang.append(x) if x not in cang else None
        for x in tbl[k]["yeu"]:
            yeu.append(x) if x not in yeu else None
        for x in tbl[k]["sua"]:
            sua.append(x) if x not in sua else None
    return {"loi": hit, "ten": [tbl[k]["ten"] for k in hit], "cang": cang, "yeu": yeu, "sua": sua[:6],
            "so_loi": len(hit) if any_marked else None}


# ------------------------------------------------------------------ lộ trình 12 tuần
def roadmap(h: dict, r: dict) -> dict:
    goal = h.get("muc_tieu", "giam_mo")
    kg = num(h.get("can_nang"), 0) or 0
    pbf = num(h.get("pbf"))
    per_week = int(num(h.get("buoi_tuan"), 3) or 3)
    weeks = 12
    # tốc độ thay đổi an toàn
    if goal == "giam_mo":
        d_kg, d_pbf = -0.006 * kg, -0.35       # ~0,6 % cân nặng / tuần, ~0,35 điểm % mỡ / tuần
    elif goal == "tang_co":
        d_kg, d_pbf = 0.0035 * kg, 0.0
    elif goal == "recomp":
        d_kg, d_pbf = -0.002 * kg, -0.25
    else:
        d_kg, d_pbf = -0.002 * kg, -0.15
    proj = []
    for w in range(0, weeks + 1):
        proj.append({"tuan": w, "can_nang": round(kg + d_kg * w, 1) if kg else None,
                     "pbf": round(pbf + d_pbf * w, 1) if pbf is not None else None})
    focus = []
    if r.get("ohs", {}).get("ten"):
        focus.append("Sửa vận động: " + ", ".join(r["ohs"]["ten"][:3]).lower())
    weak = [k for k, v in r.get("radar", {}).items() if v is not None and v < 50]
    if weak:
        focus.append("Ưu tiên cải thiện: " + ", ".join(weak).lower())
    if r.get("can_bac_si"):
        focus.append("Tập trong phạm vi bác sĩ cho phép, theo dõi huyết áp / mức đau mỗi buổi")
    phases = [
        {"ten": "Giai đoạn 1 · Nền tảng", "tuan": "Tuần 1–4",
         "muc_tieu": "Học kỹ thuật chuẩn, sửa lỗi vận động, tạo thói quen tập và ăn uống.",
         "noi_dung": ["Khởi động + bài sửa tư thế 10 phút mỗi buổi", "Toàn thân, 2–3 hiệp × 12–15 lần, RIR 3",
                      "Cardio nhẹ 15–20 phút (vẫn nói chuyện được)", "Thực đơn đầu khoá + nhắn tin theo dõi mỗi ngày"],
         "do": "Đo InBody tuần 4"},
        {"ten": "Giai đoạn 2 · Phát triển", "tuan": "Tuần 5–8",
         "muc_tieu": "Tăng tải dần, tăng sức mạnh và khối lượng tập.",
         "noi_dung": ["Chia buổi theo nhóm cơ", "3–4 hiệp × 8–12 lần, RIR 2",
                      "Cardio 20–25 phút, thêm 1 buổi cường độ cao nếu phù hợp", "Điều chỉnh calo theo InBody"],
         "do": "Đo InBody + vòng tuần 8, test lại hít đất / plank"},
        {"ten": "Giai đoạn 3 · Bứt phá", "tuan": "Tuần 9–12",
         "muc_tieu": "Đạt mục tiêu 12 tuần, chốt thói quen tự duy trì.",
         "noi_dung": ["Tăng cường độ, bài phức hợp nặng hơn", "3–4 hiệp × 6–10 lần, RIR 1–2",
                      "Cardio theo mục tiêu", "Tuần 12 đánh giá lại toàn bộ như F1"],
         "do": "Đánh giá tổng kết tuần 12 + chụp ảnh so sánh"},
    ]
    sessions = per_week * weeks
    return {"proj": proj, "phases": phases, "focus": focus, "buoi_tuan": per_week,
            "tong_buoi": sessions, "goi": recommend_package(per_week), "muc_tieu_ten": GOALS.get(goal, goal),
            "dich": {"can_nang": proj[-1]["can_nang"], "pbf": proj[-1]["pbf"]}}


def week_split(per_week: int) -> list[tuple[str, str]]:
    return {
        2: [("Buổi A", "Toàn thân · đẩy + squat + core"), ("Buổi B", "Toàn thân · kéo + hinge + cardio")],
        3: [("Buổi A", "Toàn thân · trọng tâm thân dưới"), ("Buổi B", "Toàn thân · trọng tâm thân trên"),
            ("Buổi C", "Toàn thân · sức bền + cardio")],
        4: [("Buổi A", "Thân dưới · đùi trước, mông"), ("Buổi B", "Thân trên · đẩy"),
            ("Buổi C", "Thân dưới · đùi sau, mông"), ("Buổi D", "Thân trên · kéo + core")],
    }.get(min(max(per_week, 2), 4))


def recommend_package(per_week: int) -> dict:
    need = per_week * 8  # tối thiểu 8 tuần để thấy thay đổi rõ
    best = PACKAGES[1] if need > 12 else PACKAGES[0]
    out = []
    for p in PACKAGES:
        out.append({**p, "gia_buoi": round(p["gia"] / p["buoi"]), "tuan": round(p["buoi"] / max(per_week, 1), 1),
                    "goi_y": p["id"] == best["id"]})
    base = PACKAGES[0]["gia"] / PACKAGES[0]["buoi"]
    for p in out:
        p["tiet_kiem"] = max(0, round(base * p["buoi"] - p["gia"], -3))
    return {"ds": out, "goi_y": best["id"], "bonus": BONUS_F2}


def vnd(x) -> str:
    return f"{int(round(x)):,}".replace(",", ".") + "đ"


def to_row(h: dict) -> dict:
    """Hồ sơ → 1 dòng Google Sheets (bỏ ảnh, giữ chữ/số). SĐT thêm dấu ' để Sheets giữ số 0 đầu."""
    row = {k: (json.dumps(v, ensure_ascii=False) if isinstance(v, (list, dict)) else v)
           for k, v in h.items() if not k.startswith("_")}
    if row.get("sdt"):
        row["sdt"] = "'" + str(row["sdt"]).strip().lstrip("'")
    return row


# ------------------------------------------------------------------ giáo án mẫu buổi F2 (theo mục tiêu)
def library() -> dict:
    return config.load_json("thu_vien_bai_tap.json")


def exercise(eid: str) -> dict | None:
    """Tra bài theo id → {id, ten, loai, dung_cu, nhom, nhom_ten}."""
    for nk, n in library()["nhom"].items():
        for b in n["bai"]:
            if b["id"] == eid:
                return {**b, "nhom": nk, "nhom_ten": n["ten"]}
    return None


def exercise_choices(nhom: str) -> list[str]:
    """Biến thể cùng nhóm trước, rồi toàn bộ thư viện (để PT đổi hẳn bài khác)."""
    lib = library()["nhom"]
    first = [b["id"] for b in lib[nhom]["bai"]]
    rest = [b["id"] for k, n in lib.items() if k != nhom for b in n["bai"]]
    return first + rest


def f2_template(goal: str) -> dict:
    g = library()["giao_an"]
    t = g.get(goal) or g["giam_mo"]
    return {**t, "slots": [{"nhom": n, "mac_dinh": b, "hl": hl} for n, b, hl in t["bai"]]}


def order_rank(loai: str) -> int:
    return library()["loai"].get(loai, {"thu_tu": 9})["thu_tu"]


def sort_plan(rows: list[dict]) -> list[dict]:
    """Xếp compound → multi → isolate → core; cùng loại giữ thứ tự giáo án."""
    return sorted(rows, key=lambda r: order_rank(r.get("Loại_ma", "")))


# ------------------------------------------------------------------ nạp lại hồ sơ đã lưu từ Google Sheets
TEXT_KEYS = {"ho_ten", "sdt", "email", "khan_cap", "hlv", "lich_co_dinh", "loi_song", "ghi_chu_kh", "ohs_ghi_chu", "video_f1",
             "video_f2", "ghi_chu_hlv", "ket_qua", "parq_xac_nhan", "muc_tieu", "gioi_tinh", "cardio_may", "anh_dai_dien",
             "sm_ket_qua", "sm_ghi_chu"}
SKIP_KEYS = {"thoi_gian", "phien_ban_app", "pt", "diem_tong"}


def _is_text_key(k: str) -> bool:
    return (k in TEXT_KEYS or k.startswith(("tt_", "bt_"))
            or (k.startswith("f2_") and k.endswith(("_hl", "_gc", "_bai"))))


def as_text(k: str, v) -> str:
    """Sheets tự đổi '0912345678' thành số 912345678 → trả lại chữ, thêm số 0 đầu cho SĐT."""
    if isinstance(v, float) and v.is_integer():
        v = int(v)
    s = str(v).strip().lstrip("'")
    if s.lower() == "nan":
        return ""
    if k == "sdt" and s.isdigit() and len(s) in (9, 10) and not s.startswith("0"):
        s = "0" + s
    return s


def restore_profile(row: dict) -> dict:
    """1 dòng Google Sheets → giá trị đúng kiểu cho từng ô nhập (chữ / số / ngày / đúng-sai / danh sách)."""
    out = {}
    for k, v in row.items():
        if k in SKIP_KEYS or v is None or (isinstance(v, float) and v != v) or str(v).strip() == "":
            continue
        if k in ("ngay_f1", "ngay_f2", "ngay_sinh"):
            try:
                v = date.fromisoformat(str(v)[:10])
            except ValueError:
                continue
        elif k in ("f2_tap", "f2_them"):
            try:
                v = json.loads(v) if isinstance(v, str) else list(v)
            except (TypeError, ValueError):
                v = []
        elif k == "anh_ids":
            try:
                v = json.loads(v) if isinstance(v, str) else dict(v)
            except (TypeError, ValueError):
                continue
        elif (k.startswith("ohs_") and k not in ("ohs_ghi_chu", "ohs_da_lam")) or k in ("da_gian_co", "sm_co"):
            v = str(v).strip().lower() in ("true", "1", "1.0", "có")
        elif k.startswith("parq_") and k != "parq_xac_nhan":
            v = "Có" if str(v).strip() in ("Có", "True", "true", "1") else "Không"
        elif k in ("buoi_tuan", "cardio_rpe", "sm_rpe"):
            try:
                v = int(float(v))
            except (TypeError, ValueError):
                continue
        elif _is_text_key(k):
            v = as_text(k, v)
        out[k] = v
    return out


# ------------------------------------------------------------------ ảnh khách lưu kèm hồ sơ (v2.9)
IMAGE_SLOTS = {"inbody": "Phiếu InBody", "truoc": "Tư thế góc trước", "ben": "Tư thế góc bên", "sau": "Tư thế góc sau",
               "t_ymca": "Bài YMCA", "t_squat": "Form squat", "t_keo": "Form sức kéo", "t_hit_dat": "Form hít đất",
               "t_plank": "Form plank", "t_deo": "Form độ dẻo", "t_sm": "Bài strongman"}


def image_hash(data: bytes) -> str:
    import hashlib
    return hashlib.md5(data).hexdigest()[:12]


def file_prefix(h: dict) -> str:
    """Tiền tố tên ảnh trên Drive: tên khách không dấu + SĐT, dễ tìm."""
    import unicodedata
    name = unicodedata.normalize("NFD", str(h.get("ho_ten") or "khach")).encode("ascii", "ignore").decode()
    name = "".join(ch if ch.isalnum() else "_" for ch in name).strip("_") or "khach"
    return f"{name}_{str(h.get('sdt') or '').lstrip(chr(39))}_"
