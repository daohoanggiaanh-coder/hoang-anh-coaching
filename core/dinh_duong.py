# Hoàng Anh Coaching v1.0 (2026-10-31) — tính năng lượng, macro, phân bữa và thực đơn 7 ngày theo lịch tập thật
"""
CÁCH TÍNH (mọi bước đều hiện cho khách xem ở mục "Cách tính"):

1. Năng lượng nền (BMR)
   - Mifflin-St Jeor (1990): 10·kg + 6,25·cm − 5·tuổi + 5 (nam) / − 161 (nữ).
   - Có % mỡ (InBody) → thêm Katch-McArdle: 370 + 21,6 · khối nạc (kg); dùng Katch-McArdle làm số chính
     vì tính theo khối nạc, sát hơn với người nhiều cơ hoặc nhiều mỡ.
2. Vận động ngoài giờ tập (hệ số nhân BMR, đã gồm năng lượng tiêu hoá thức ăn):
   ngồi nhiều 1,2 · nhẹ 1,35 · vừa 1,5 · nhiều 1,65  (hệ số thực hành, ước lượng — không phải đo).
3. Năng lượng buổi tập: (MET − 1) × kg × giờ. MET tập tạ: vừa ≈ 3,5 · nặng ≈ 6,0; cardio vừa ≈ 6,0
   (Compendium of Physical Activities, Ainsworth et al. 2011). Trừ 1 MET vì phần nghỉ đã tính ở bước 2.
4. Mục tiêu:
   - Giảm mỡ: giảm 0,5 / 0,75 / 1,0 % cân nặng mỗi tuần (Helms et al. 2014, JISSN), quy đổi ≈ 7.700 kcal / kg
     (quy tắc gần đúng — cơ thể thích nghi nên thực tế thường chậm hơn về sau). Thâm hụt tối đa 25 % TDEE,
     không thấp hơn BMR và không dưới 1.200 kcal (nữ) / 1.500 kcal (nam).
   - Tăng cơ: dư +150 / +250 / +400 kcal / ngày (mức thực hành "lean bulk"; người mới tập tăng được nhanh hơn).
   - Recomp: −10 % TDEE (vừa đủ thâm hụt để giảm mỡ chậm, vẫn đủ năng lượng tập nặng).
   - Giữ dáng: = TDEE.
   Ngày tập ăn nhiều hơn ngày nghỉ đúng bằng năng lượng buổi tập (phần chênh dồn vào tinh bột).
5. Macro
   - Đạm: Morton et al. 2018 (BJSM): ~1,6 g/kg/ngày là mức tối ưu trung bình, cận trên ~2,2 g/kg.
     Đang thâm hụt nên cao hơn — Helms et al. 2014: 2,3–3,1 g/kg khối nạc. Có % mỡ → tính theo khối nạc;
     không có → theo cân "tham chiếu" (người BMI ≥ 25 dùng cân ở BMI 25 để không dư đạm vô ích).
   - Béo: 25 % năng lượng (giảm mỡ) / 28 % (khác); không dưới 0,6 g/kg tham chiếu; trong khoảng
     20–35 % năng lượng (AMDR, Institute of Medicine 2005).
   - Tinh bột: phần còn lại.
   - Chất xơ: 14 g / 1.000 kcal (IOM 2005). Rau + trái cây ≥ 400 g / ngày (WHO).
   - Nước: ≈ 35 ml / kg + 500 ml mỗi giờ tập (ước lượng thực hành; ra mồ hôi nhiều cần thêm).
6. Phân bữa: đạm chia đều các bữa chính (~0,3–0,4 g/kg mỗi bữa — Schoenfeld & Aragon 2018);
   ngày tập dồn tinh bột vào bữa trước / sau tập, giảm béo quanh giờ tập.
7. Thực đơn: mỗi bữa chọn 1 món đạm + 1 tinh bột + 1 chất béo (+ rau / trái cây cố định), giải bài toán
   bình phương tối thiểu có chặn (scipy lsq_linear) để ra số gram khớp macro bữa đó nhất, làm tròn 5 g
   hoặc theo đơn vị (quả trứng, muỗng whey, thìa dầu).

Đây là ƯỚC TÍNH ban đầu. Cách chỉnh đúng nhất: theo dõi cân trung bình 7 ngày 2–3 tuần rồi chỉnh ±100–200 kcal.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field

from core import config

VAN_DONG = {"ngoi": ("Ngồi nhiều (< 5.000 bước / ngày, làm văn phòng)", 1.2),
            "nhe": ("Đi lại nhẹ (5.000–7.500 bước)", 1.35),
            "vua": ("Đi lại vừa (7.500–10.000 bước, đứng nhiều)", 1.5),
            "nhieu": ("Vận động nhiều (> 10.000 bước / lao động chân tay)", 1.65)}
CUONG_DO = {"vua": ("Vừa — nghỉ nhiều giữa hiệp", 3.5), "nang": ("Nặng — tạ nặng, nghỉ ngắn, superset", 6.0)}
MUC_TIEU = {"giam_mo": "Giảm mỡ", "recomp": "Giảm mỡ + tăng cơ (recomp)", "giu": "Giữ dáng", "tang_co": "Tăng cơ"}
TOC_DO = {"cham": "Chậm — dễ giữ", "vua": "Vừa", "nhanh": "Nhanh — kỷ luật cao"}
GIAM_PCT = {"cham": 0.5, "vua": 0.75, "nhanh": 1.0}          # % cân / tuần
TANG_KCAL = {"cham": 150, "vua": 250, "nhanh": 400}
GIO_TAP = {"sang": "Sáng (trước 9h)", "trua": "Trưa (11h–13h)", "chieu": "Chiều (15h–18h)", "toi": "Tối (sau 18h)"}
CHE_DO = {"thuong": "Ăn bình thường", "khong_bo": "Không ăn bò", "khong_hai_san": "Không hải sản (tôm, cua…)",
          "khong_sua": "Không sữa / bất dung nạp lactose", "khong_hat": "Dị ứng các loại hạt",
          "chay_trung_sua": "Chay (có trứng, sữa)", "thuan_chay": "Thuần chay"}
CHAN_TAG = {"khong_bo": {"bo"}, "khong_hai_san": {"hai_san"}, "khong_sua": {"sua"}, "khong_hat": {"hat"},
            "chay_trung_sua": {"thit", "bo", "ca", "hai_san"}, "thuan_chay": {"thit", "bo", "ca", "hai_san", "trung", "sua"}}
KCAL_KG = 7700
# v1.2: khách tập tạ → mặc định "Cao". Morton 2018: lợi ích tăng cơ chững lại quanh 1,6 g/kg (cận trên ~2,2 g/kg);
# đang thâm hụt cần cao hơn — Helms 2014: 2,3–3,1 g/kg khối nạc. "Rất cao" dùng khi giảm mỡ sâu / người tập lâu năm.
MUC_DAM = {   # v1.4: g đạm / kg CÂN NẶNG THẬT (HLV chọn 2 g/kg làm chuẩn cho khách tập tạ)
    "vua":     {"ten": "Vừa · 1,6 g/kg", "g": 1.6},
    "cao":     {"ten": "Chuẩn tập tạ · 2,0 g/kg", "g": 2.0},
    "rat_cao": {"ten": "Rất cao · 2,2 g/kg", "g": 2.2},
}


def foods() -> dict[str, dict]:
    base = {k: dict(v) for k, v in config.load_json("thuc_pham.json")["mon"].items()}
    try:                                                    # HLV sửa / thêm món ở trang Dinh dưỡng
        from core import db
        for k, v in db.latest("DinhDuong").items():
            if k.startswith("mon|"):
                base[k[4:]] = {kk: vv for kk, vv in v.items() if not kk.startswith("_")}
    except Exception:  # noqa: BLE001
        pass
    return base


# ------------------------------------------------------------------ năng lượng
@dataclass
class HoSo:
    gioi_tinh: str = "Nam"
    tuoi: int = 30
    cao: float = 170.0
    kg: float = 70.0
    pbf: float | None = None
    van_dong: str = "nhe"
    buoi_tuan: int = 3
    phut_buoi: int = 60
    cuong_do: str = "vua"
    cardio_phut_tuan: int = 0
    muc_tieu: str = "giam_mo"
    toc_do: str = "vua"
    so_bua: int = 4
    gio_tap: str = "chieu"
    che_do: list[str] = field(default_factory=lambda: ["thuong"])
    kcal_tay: int | None = None          # HLV ghi đè tổng kcal trung bình
    dam_g_kg: float | None = None        # HLV ghi đè đạm g/kg cân nặng
    muc_dam: str = "cao"                 # v1.4: vua 1,6 · cao 2,0 (mặc định) · rat_cao 2,2 g/kg cân nặng
    kieu_td: str = "viet"                # v1.4: viet = món Việt (phở, cơm phần…) · tach = món tách (meal-prep)
    ngay_tap: list[int] | None = None    # thứ có tập (0 = Thứ 2) — lấy từ lịch cố định nếu có
    bmr_inbody: int | None = None        # v2.6: BMR in trên phiếu InBody — có thì dùng thay công thức

    @staticmethod
    def tu_dict(d: dict) -> "HoSo":
        h = HoSo()
        for k in h.__dataclass_fields__:
            if k in d and d[k] not in (None, ""):
                setattr(h, k, d[k])
        h.tuoi, h.buoi_tuan, h.phut_buoi, h.so_bua = int(h.tuoi), int(h.buoi_tuan), int(h.phut_buoi), int(h.so_bua)
        h.cao, h.kg = float(h.cao), float(h.kg)
        h.pbf = float(h.pbf) if h.pbf not in (None, "", 0, 0.0) else None
        h.cardio_phut_tuan = int(h.cardio_phut_tuan or 0)
        h.kcal_tay = int(h.kcal_tay) if h.kcal_tay else None
        h.bmr_inbody = int(float(h.bmr_inbody)) if h.bmr_inbody else None
        h.dam_g_kg = float(h.dam_g_kg) if h.dam_g_kg else None
        if isinstance(h.che_do, str):
            h.che_do = [h.che_do]
        return h

    @property
    def nu(self) -> bool:
        return str(self.gioi_tinh).strip().lower() in ("nữ", "nu", "female")


def tinh(h: HoSo) -> dict:
    """Toàn bộ số liệu năng lượng + macro, kèm từng bước để hiển thị."""
    s = -161 if h.nu else 5
    bmr_m = 10 * h.kg + 6.25 * h.cao - 5 * h.tuoi + s
    lbm = h.kg * (1 - h.pbf / 100) if h.pbf else None
    bmr_k = 370 + 21.6 * lbm if lbm else None
    bmr = h.bmr_inbody if h.bmr_inbody else (bmr_k if bmr_k else bmr_m)
    he_so = VAN_DONG.get(h.van_dong, VAN_DONG["nhe"])[1]
    nghi = bmr * he_so
    met = CUONG_DO.get(h.cuong_do, CUONG_DO["vua"])[1]
    e_buoi = (met - 1) * h.kg * h.phut_buoi / 60
    e_cardio_ngay = (6.0 - 1) * h.kg * (h.cardio_phut_tuan / 60) / 7
    tap = nghi + e_buoi
    nghi += e_cardio_ngay
    tap += e_cardio_ngay
    tdee_tb = (tap * h.buoi_tuan + nghi * (7 - h.buoi_tuan)) / 7

    san = max(1200 if h.nu else 1500, bmr)
    ghi = []
    if h.muc_tieu == "giam_mo":
        pct = GIAM_PCT.get(h.toc_do, 0.75)
        delta = -pct / 100 * h.kg * KCAL_KG / 7
        if -delta > 0.25 * tdee_tb:
            delta = -0.25 * tdee_tb
            ghi.append("Thâm hụt bị giới hạn ở 25 % TDEE để giữ cơ và sức tập.")
    elif h.muc_tieu == "tang_co":
        delta = TANG_KCAL.get(h.toc_do, 250)
    elif h.muc_tieu == "recomp":
        delta = -0.10 * tdee_tb
    else:
        delta = 0.0
    muc_tb = tdee_tb + delta
    if h.kcal_tay:
        muc_tb, delta = float(h.kcal_tay), float(h.kcal_tay) - tdee_tb
        ghi.append("Tổng năng lượng do HLV đặt tay.")
    if muc_tb < san:
        ghi = [g for g in ghi if not g.startswith("Thâm hụt")]
        ghi.append(f"Đã nâng lên mức sàn {san:,.0f} kcal (không thấp hơn BMR / mức tối thiểu an toàn).".replace(",", "."))
        delta += san - muc_tb
        muc_tb = san
    kcal_tap, kcal_nghi = tap + delta, nghi + delta
    if kcal_nghi < san:                                   # ngày nghỉ cũng không xuống dưới mức sàn
        kcal_nghi = san
        kcal_tap = max(kcal_tap, san)

    # ---- đạm
    bmi = h.kg / (h.cao / 100) ** 2
    can_tc = min(h.kg, 25 * (h.cao / 100) ** 2)
    gkg = h.dam_g_kg or MUC_DAM.get(h.muc_dam, MUC_DAM["cao"])["g"]
    dam = gkg * h.kg
    cach_dam = f"{gkg:g} g / kg cân nặng ({h.kg:g} kg)" + (" — HLV đặt" if h.dam_g_kg else "")
    if bmi >= 30 and not h.dam_g_kg:
        ghi.append(f"BMI {bmi:.1f} ≥ 30: {gkg:g} g/kg cân thật = {dam:.0f} g đạm/ngày, khá cao. Nhiều tài liệu khuyên tính theo cân "
                   f"mục tiêu / cân ở BMI 25 ({can_tc:.0f} kg → {gkg * can_tc:.0f} g) — HLV cân nhắc ghi đè.")

    def _macro(kcal: float) -> dict:
        # v2.0: nữ cần đủ béo (nội tiết, hấp thu vitamin tan trong dầu) → 30 % năng lượng, sàn 0,8 g/kg (mức thực hành)
        pct_beo = 0.30 if h.nu else (0.25 if h.muc_tieu == "giam_mo" else 0.28)
        beo = max(pct_beo * kcal / 9, (0.8 if h.nu else 0.6) * can_tc)
        beo = min(beo, 0.35 * kcal / 9)
        bot = max((kcal - dam * 4 - beo * 9) / 4, 0)
        return {"kcal": round(kcal), "p": round(dam), "f": round(beo), "c": round(bot),
                "xo": round(14 * kcal / 1000), "pct": {"p": dam * 4 / kcal, "f": beo * 9 / kcal, "c": bot * 4 / kcal}}

    m_tap, m_nghi = _macro(kcal_tap), _macro(kcal_nghi)
    if m_nghi["c"] < 80:
        ghi.append("Tinh bột ngày nghỉ khá thấp (< 80 g) — theo dõi sức tập và giấc ngủ.")
    nuoc = 35 * h.kg / 1000
    toc = (delta * 7 / KCAL_KG) if h.muc_tieu != "giu" else 0.0
    return {
        "bmr_m": round(bmr_m), "bmr_k": round(bmr_k) if bmr_k else None, "bmr": round(bmr), "bmr_inbody": h.bmr_inbody, "lbm": round(lbm, 1) if lbm else None,
        "he_so": he_so, "neat": round(bmr * he_so - bmr), "e_buoi": round(e_buoi), "e_cardio": round(e_cardio_ngay),
        "tdee_nghi": round(nghi), "tdee_tap": round(tap), "tdee_tb": round(tdee_tb), "delta": round(delta), "muc_tb": round(muc_tb),
        "tap": m_tap, "nghi": m_nghi, "dam": round(dam), "cach_dam": cach_dam, "dam_g_kg": round(dam / h.kg, 2),
        "bmi": round(bmi, 1), "can_tc": round(can_tc, 1), "nuoc_nghi": round(nuoc, 1),
        "nuoc_tap": round(nuoc + 0.5 * h.phut_buoi / 60, 1), "kg_tuan": round(toc, 2), "ghi": ghi, "san": round(san),
    }


def tuan_toi_dich(h: HoSo, kq: dict, can_dich: float | None) -> float | None:
    if not can_dich or not kq["kg_tuan"]:
        return None
    ch = float(can_dich) - h.kg
    if ch * kq["kg_tuan"] <= 0:
        return None
    return round(ch / kq["kg_tuan"], 1)


# ------------------------------------------------------------------ phân bữa
BUA = {"sang": "Bữa sáng", "phu_sang": "Bữa phụ sáng", "trua": "Bữa trưa", "phu_chieu": "Bữa phụ chiều", "toi": "Bữa tối",
       "phu_toi": "Bữa phụ tối"}
LICH_BUA = {3: ["sang", "trua", "toi"], 4: ["sang", "trua", "phu_chieu", "toi"],
            5: ["sang", "phu_sang", "trua", "phu_chieu", "toi"], 6: ["sang", "phu_sang", "trua", "phu_chieu", "toi", "phu_toi"]}
# bữa trước / sau tập theo giờ tập (nếu bữa có trong lịch)
QUANH_TAP = {"sang": ("sang", "phu_sang"), "trua": ("phu_sang", "trua"), "chieu": ("phu_chieu", "toi"), "toi": ("phu_chieu", "toi")}
GIO_BUA = {"sang": "7:00", "phu_sang": "10:00", "trua": "12:00", "phu_chieu": "15:30", "toi": "19:00", "phu_toi": "21:30"}


def phan_bua(h: HoSo, m: dict, ngay_tap: bool) -> list[dict]:
    ds = LICH_BUA.get(int(h.so_bua), LICH_BUA[4])
    truoc, sau = QUANH_TAP.get(h.gio_tap, QUANH_TAP["chieu"])
    if h.gio_tap == "sang" and "phu_sang" not in ds:
        sau = "trua"
    if h.gio_tap == "toi" and ngay_tap:
        sau = "phu_toi" if "phu_toi" in ds else "toi"
    out = []
    for b in ds:
        chinh = not b.startswith("phu")
        w = {"p": 1.0 if chinh else 0.6, "c": 1.0 if chinh else 0.5, "f": 1.0 if chinh else 0.6}
        vai = ""
        if ngay_tap and b == truoc:
            w["c"] *= 1.3
            w["f"] *= 0.5
            vai = "truoc"
        if ngay_tap and b == sau:
            w["c"] *= 1.5
            w["f"] *= 0.6
            w["p"] *= 1.1
            vai = "sau"
        out.append({"bua": b, "ten": BUA[b], "gio": GIO_BUA[b], "w": w, "vai": vai})
    for k in ("p", "c", "f"):
        tong = sum(x["w"][k] for x in out)
        for x in out:
            x[k] = m[k] * x["w"][k] / tong
    for x in out:
        x["kcal"] = x["p"] * 4 + x["c"] * 4 + x["f"] * 9
    return out


# ------------------------------------------------------------------ thực đơn
MAU_BUA = {
    "sang":  {"dam": ["trung", "sua_chua_hy_lap", "whey", "long_trang", "uc_ga", "dau_phu", "sua_dau_nanh"],
              "tinh_bot": ["yen_mach", "banh_mi", "khoai_lang", "com"], "beo": ["bo_dau_phong", "hanh_nhan", "qua_bo"],
              "kem": [("trai_cay", 100)]},
    "trua":  {"dam": ["uc_ga", "than_heo", "bo_nac", "ca_ro_phi", "tom", "dui_ga", "ca_hoi", "dau_phu", "trung", "dau_lang"],
              "tinh_bot": ["com", "com_gao_lut", "bun", "khoai_lang", "mi_y", "khoai_tay"], "beo": ["dau_an", "qua_bo"],
              "kem": [("rau", 150), ("trai_cay", 120)]},
    "toi":   {"dam": ["ca_ro_phi", "uc_ga", "bo_nac", "tom", "than_heo", "ca_hoi", "dui_ga", "dau_phu", "trung", "edamame"],
              "tinh_bot": ["com", "khoai_lang", "com_gao_lut", "bun", "khoai_tay", "bap"], "beo": ["dau_an", "qua_bo"],
              "kem": [("rau", 200)]},
    "phu":   {"dam": ["sua_chua_hy_lap", "whey", "trung", "ca_ngu_hop", "edamame", "sua_dau_nanh"],
              "tinh_bot": ["chuoi", "tao", "khoai_lang", "cam", "du_du", "yen_mach"], "beo": ["hanh_nhan", "hat_dieu", "dau_phong", "qua_bo"],
              "kem": [("trai_cay", 120)]},
    "truoc": {"dam": ["sua_chua_hy_lap", "whey", "long_trang", "sua_dau_nanh", "edamame"],
              "tinh_bot": ["chuoi", "banh_mi", "khoai_lang", "yen_mach", "com"], "beo": [], "kem": []},   # trước tập: nhẹ bụng
    "sau":   {"dam": ["whey", "sua_chua_hy_lap", "sua_dau_nanh", "edamame"],
              "tinh_bot": ["chuoi", "banh_mi", "khoai_lang", "yen_mach"], "beo": [], "kem": [("trai_cay", 100)]},
}
GIOI_HAN = {"whey": 45, "trung": 200, "long_trang": 264, "dau_an": 10, "bo_dau_phong": 32, "dau_phong": 40, "hanh_nhan": 40,
            "hat_dieu": 40, "qua_bo": 120, "sua_dau_nanh": 500, "sua_tuoi": 400, "sua_tach_beo": 400, "edamame": 250, "dau_lang": 300, "yen_mach": 100, "banh_mi": 150, "com": 400, "com_gao_lut": 400, "bun": 400,
            "mi_y": 350, "khoai_lang": 450, "khoai_tay": 450, "bap": 300, "chuoi": 240, "tao": 300, "cam": 300, "du_du": 300,
            "dua_hau": 400, "sua_chua_hy_lap": 300, "ca_ngu_hop": 150, "dau_phu": 300,
            "chao": 700, "banh_pho": 450, "hu_tieu": 450, "xoi": 300, "hat_chia": 15, "kefir": 300}


# v1.4 — MÓN VIỆT cho bữa chính: tên món thật, web vẫn giải số gram từng thành phần để khớp macro.
# dam: các món đạm của món ăn · tb: tinh bột · beo: dầu nấu (None = món nước / luộc / nướng) · rau: [(món rau, gram cố định)]
MON_VIET = {
    "pho_bo":      {"ten": "Phở bò tái / nạm (ít mỡ)", "bua": {"sang", "trua", "toi"}, "dam": ["bo_nac"], "tb": "banh_pho", "beo": None, "rau": [("gia_do", 100)], "nuoc": 1},
    "pho_ga":      {"ten": "Phở gà", "bua": {"sang", "trua", "toi"}, "dam": ["uc_ga"], "tb": "banh_pho", "beo": None, "rau": [("gia_do", 100)], "nuoc": 1},
    "bun_bo":      {"ten": "Bún bò (thịt bắp, ít mỡ)", "bua": {"sang", "trua"}, "dam": ["bo_nac"], "tb": "bun", "beo": None, "rau": [("rau_song", 100)], "nuoc": 1},
    "hu_tieu_tom": {"ten": "Hủ tiếu tôm thịt", "bua": {"sang", "trua"}, "dam": ["tom", "than_heo"], "tb": "hu_tieu", "beo": None,
                    "rau": [("gia_do", 100)], "nuoc": 1},
    "banh_mi_trung": {"ten": "Bánh mì ốp la + dưa leo", "bua": {"sang"}, "dam": ["trung", "long_trang"], "tb": "banh_mi", "beo": "dau_an",
                      "rau": [("rau_song", 50)]},
    "banh_mi_bo":  {"ten": "Bánh mì trứng ốp + trái bơ", "bua": {"sang"}, "dam": ["trung", "long_trang"], "tb": "banh_mi", "beo": "qua_bo",
                    "rau": [("rau_song", 50)]},
    "salad_ga_bo": {"ten": "Salad ức gà + trái bơ + khoai lang", "bua": {"trua", "toi"}, "dam": ["uc_ga"], "tb": "khoai_lang", "beo": "qua_bo",
                    "rau": [("dua_leo_ca_chua", 150), ("cai_bo_xoi", 50)]},
    "ca_hoi_bo":   {"ten": "Cơm gạo lứt + cá hồi áp chảo + bơ", "bua": {"trua", "toi"}, "dam": ["ca_hoi"], "tb": "com_gao_lut", "beo": "qua_bo",
                    "rau": [("bong_cai", 150)]},
    "banh_mi_ga":  {"ten": "Bánh mì gà xé + rau", "bua": {"sang"}, "dam": ["uc_ga"], "tb": "banh_mi", "beo": None, "rau": [("rau_song", 50)]},
    "xoi_ga":      {"ten": "Xôi gà xé", "bua": {"sang"}, "dam": ["uc_ga"], "tb": "xoi", "beo": None, "rau": [("rau_song", 40)]},
    "chao_ga":     {"ten": "Cháo gà xé hành gừng", "bua": {"sang", "toi"}, "dam": ["uc_ga"], "tb": "chao", "beo": None, "rau": [("rau_song", 50)], "nuoc": 1},
    "yen_mach_sc": {"ten": "Yến mạch sữa chua Hy Lạp + hạt", "bua": {"sang"}, "dam": ["sua_chua_hy_lap", "whey"], "tb": "yen_mach",
                    "beo": "hanh_nhan", "rau": []},
    "banh_mi_dau": {"ten": "Bánh mì đậu hũ + sữa đậu nành", "bua": {"sang"}, "dam": ["dau_phu", "sua_dau_nanh"], "tb": "banh_mi",
                    "beo": None, "rau": [("rau_song", 50)]},
    "com_ga_xe":   {"ten": "Cơm gà xé + dưa leo cà chua", "bua": {"trua", "toi"}, "dam": ["uc_ga"], "tb": "com", "beo": "dau_an",
                    "rau": [("dua_leo_ca_chua", 150)]},
    "com_ca_kho":  {"ten": "Cơm cá basa kho + rau muống luộc", "bua": {"trua", "toi"}, "dam": ["ca_ro_phi"], "tb": "com", "beo": "dau_an",
                    "rau": [("rau_muong", 200)]},
    "canh_chua":   {"ten": "Cơm + canh chua cá lóc", "bua": {"trua", "toi"}, "dam": ["ca_loc"], "tb": "com", "beo": "dau_an",
                    "rau": [("ca_chua_dua_chua", 200)]},
    "thit_kho_trung": {"ten": "Cơm thịt nạc kho trứng + cải luộc", "bua": {"trua", "toi"}, "dam": ["than_heo", "trung"], "tb": "com",
                       "beo": None, "rau": [("cai_xao", 200)]},
    "bo_xao":      {"ten": "Cơm bò xào bông cải", "bua": {"trua", "toi"}, "dam": ["bo_nac"], "tb": "com", "beo": "dau_an", "rau": [("bong_cai", 200)]},
    "tom_rim":     {"ten": "Cơm tôm rim + canh bí", "bua": {"trua", "toi"}, "dam": ["tom"], "tb": "com", "beo": "dau_an", "rau": [("canh_bi", 200)]},
    "muc_xao":     {"ten": "Cơm mực xào cải ngọt", "bua": {"trua", "toi"}, "dam": ["muc"], "tb": "com", "beo": "dau_an", "rau": [("cai_xao", 200)]},
    "bun_cha":     {"ten": "Bún chả (thịt nạc nướng) + rau sống", "bua": {"trua"}, "dam": ["than_heo"], "tb": "bun", "beo": None,
                    "rau": [("rau_song", 150)]},
    "ga_nuong":    {"ten": "Cơm gạo lứt + đùi gà nướng + salad", "bua": {"trua", "toi"}, "dam": ["dui_ga"], "tb": "com_gao_lut", "beo": None,
                    "rau": [("dua_leo_ca_chua", 150)]},
    "ca_thu_sot":  {"ten": "Cơm cá thu sốt cà + rau muống", "bua": {"toi"}, "dam": ["ca_thu"], "tb": "com", "beo": None,
                    "rau": [("rau_muong", 200)]},
    "dau_hu_sot":  {"ten": "Cơm đậu hũ sốt cà + trứng hấp + cải", "bua": {"trua", "toi"}, "dam": ["dau_phu", "trung"], "tb": "com",
                    "beo": "dau_an", "rau": [("cai_xao", 200)]},
    "ga_khoai":    {"ten": "Ức gà áp chảo + khoai lang + bông cải", "bua": {"toi"}, "dam": ["uc_ga"], "tb": "khoai_lang", "beo": "dau_an",
                    "rau": [("bong_cai", 200)]},
}


# phần tinh bột tối thiểu của 1 món Việt (gram chín) — dưới mức này nhìn không ra món (VD 40 g cơm = 1/3 chén)
SAN_TB_VIET = {"com": 80, "com_gao_lut": 80, "bun": 100, "banh_pho": 100, "hu_tieu": 100, "xoi": 70, "chao": 200, "banh_mi": 45,
               "khoai_lang": 80, "yen_mach": 30}


def mon_viet_duoc(bua: str, F: dict, che_do: list[str], bo: set[str]) -> dict[str, dict]:
    """Món Việt hợp bữa + chế độ ăn. Món nhiều nguồn đạm: bỏ nguồn bị kiêng, còn ≥ 1 nguồn thì vẫn dùng được."""
    out = {}
    for mid, m in MON_VIET.items():
        if bua not in m["bua"]:
            continue
        dam = [x for x in m["dam"] if x in F and duoc_an(F[x], che_do) and x not in bo]
        tb, beo = m["tb"], m["beo"]
        if not dam or tb not in F or not duoc_an(F[tb], che_do) or tb in bo:
            continue
        if beo and (beo not in F or not duoc_an(F[beo], che_do) or beo in bo):
            beo = None
        rau = [(x, g) for x, g in m["rau"] if x in F and duoc_an(F[x], che_do) and x not in bo]
        out[mid] = {**m, "dam": dam, "beo": beo, "rau": rau}
    return out


def _mau(b: dict) -> str:
    """Bữa chính giữ mẫu bữa chính (chỉ đổi tỉ lệ macro); bữa phụ quanh giờ tập dùng mẫu trước / sau tập."""
    if b["bua"].startswith("phu"):
        return b["vai"] if b["vai"] in ("truoc", "sau") else "phu"
    return b["bua"]


TOI_THIEU = {"whey": 15, "trung": 50, "long_trang": 66, "yen_mach": 20, "dau_an": 5, "bo_dau_phong": 8, "hanh_nhan": 10,
             "hat_dieu": 10, "dau_phong": 10, "qua_bo": 30}
TOI_THIEU_NHOM = {"dam": 50, "sua": 100, "tinh_bot": 40, "trai_cay": 60, "beo": 5, "rau": 50}


def duoc_an(f: dict, che_do: list[str]) -> bool:
    chan = set().union(*[CHAN_TAG.get(c, set()) for c in (che_do or [])]) if che_do else set()
    return not (set(f.get("tag", [])) & chan)


def _seed(*a) -> int:
    return int(hashlib.md5("|".join(map(str, a)).encode()).hexdigest(), 16)


def lua_chon(mau: str, vai_tro: str, F: dict, che_do: list[str], bo: set[str]) -> list[str]:
    ds = MAU_BUA[mau].get(vai_tro, [])
    return [x for x in ds if x in F and duoc_an(F[x], che_do) and x not in bo]


def _giai(mon: list[str], F: dict, muc: dict, san: dict[str, float] | None = None) -> dict[str, float]:
    """Gram từng món sao cho (đạm, tinh bột, béo) gần mục tiêu nhất — sai số tính theo kcal."""
    import numpy as np
    from scipy.optimize import lsq_linear
    if not mon:
        return {}
    A = np.array([[F[m]["p"] * 4 / 100 for m in mon], [F[m]["c"] * 4 / 100 for m in mon], [F[m]["f"] * 9 / 100 for m in mon]])
    b = np.array([max(muc["p"], 0) * 4, max(muc["c"], 0) * 4, max(muc["f"], 0) * 9])
    ub = np.array([GIOI_HAN.get(m, 300) for m in mon], dtype=float)
    lb = np.array([min((san or {}).get(m, 0), u - 1) for m, u in zip(mon, ub)], dtype=float)
    r = lsq_linear(A, b, bounds=(lb, ub))
    return {m: float(x) for m, x in zip(mon, r.x)}


def _tron(m: str, g: float, F: dict) -> float:
    dv = F[m].get("don_vi")
    if dv and m in ("trung", "long_trang", "whey"):
        n = round(g / dv["g"])
        return n * dv["g"]
    return 5 * round(g / 5)


def mo_ta_luong(m: str, g: float, F: dict) -> str:
    dv = F[m].get("don_vi")
    if not dv or g <= 0:
        return ""
    if m == "dau_an":                                     # dầu: 1 thìa cà phê = 5 ml ≈ 4,6 g
        return f"≈ {g / 0.92:.0f} ml · {g / 0.92 / 5:.1f} thìa cà phê".replace(".0 ", " ").replace(".", ",")
    n = g / dv["g"]
    if m in ("trung", "long_trang", "whey"):
        return f"{n:.0f} {dv['ten']}"
    return f"≈ {n:.1f} {dv['ten']}".replace(".0 ", " ")


def tong(mon: dict[str, float], F: dict) -> dict:
    """kcal = 4·đạm + 4·tinh bột + 9·béo (cùng cách với mục tiêu, để so khớp); kcal_nhan = theo bảng thực phẩm."""
    t = {"p": 0.0, "c": 0.0, "f": 0.0, "xo": 0.0, "kcal_nhan": 0.0}
    for m, g in mon.items():
        for k in ("p", "c", "f", "xo"):
            t[k] += F[m].get(k, 0) * g / 100
        t["kcal_nhan"] += F[m].get("kcal", 0) * g / 100
    t["kcal"] = 4 * t["p"] + 4 * t["c"] + 9 * t["f"]
    return t


def bua_an(b: dict, F: dict, che_do: list[str], seed: int, chon: dict | None = None, bo: set[str] | None = None,
           tranh_kem: set[str] | None = None, viet: bool = True, tranh_mon: set[str] | None = None, it_tb: bool = False,
           uu_trai: list[str] | None = None) -> dict:
    """1 bữa: bữa chính kiểu Việt → chọn 1 món Việt (xoay vòng, không lặp trong ngày); còn lại chọn món theo mẫu
    (xoay vòng theo seed, hoặc theo `chon` người dùng đổi) rồi tính gram."""
    bo = bo or set()
    mau = _mau(b)
    chon = chon or {}
    mon, kem = [], {}
    mv = None
    if viet and mau in ("sang", "trua", "toi") and not any(chon.get(x) for x in ("dam", "tinh_bot", "beo")):
        DS = mon_viet_duoc(mau, F, che_do, bo)
        if DS:
            ids = list(DS)
            uu = [x for x in ids if x not in (tranh_mon or set())] or ids
            mid = chon.get("mon") if chon.get("mon") in DS else uu[seed % len(uu)]
            mv = {"id": mid, **DS[mid]}
            bot_tb = it_tb and mau == "toi" and b["c"] < 25          # ngày ít tinh bột: bữa tối bỏ cơm, thêm rau
            mon = list(mv["dam"]) + ([] if bot_tb else [mv["tb"]]) + ([mv["beo"]] if mv["beo"] else [])
            for x, g in mv["rau"]:
                kem[x] = float(g) + (100 if bot_tb else 0)
            if bot_tb:
                mv = {**mv, "ten": mv["ten"] + " · tối nay bỏ cơm, thêm rau", "tb": None}
    for i, vt in enumerate(("dam", "tinh_bot", "beo")):
        if mv:
            break
        ds = lua_chon(mau, vt, F, che_do, bo)
        if not ds:
            continue
        x = chon.get(vt) if chon.get(vt) in ds else ds[(seed >> (i * 5)) % len(ds)]
        if x not in mon:
            mon.append(x)
    for nhom, g in MAU_BUA[mau]["kem"]:
        if mv and nhom == "rau":
            continue
        if it_tb and nhom == "trai_cay" and mau != "trua":              # ngày ít tinh bột: chỉ giữ trái cây bữa trưa
            continue
        ds = [k for k, v in F.items() if v.get("nhom") == nhom and duoc_an(v, che_do) and k not in bo and k not in mon
              and k not in (tranh_kem or set())] or \
             [k for k, v in F.items() if v.get("nhom") == nhom and duoc_an(v, che_do) and k not in bo and k not in mon]
        ds = [x for x in ds if "len_men" not in F[x].get("tag", [])] or ds     # kim chi / dưa chua chỉ thêm lượng nhỏ (xem _them_loi_khuan)
        if nhom == "trai_cay":                                            # v3.2: trái cây theo mục tiêu; quanh giờ tập ưu tiên chuối
            pref = ["chuoi"] if mau in ("truoc", "sau") else (uu_trai or [])
            ds = [x for x in ds if x in pref] or ds
        if ds:
            x = chon.get(nhom) if chon.get(nhom) in ds else ds[(seed >> 17) % len(ds)]
            dv = F[x].get("don_vi")
            kem[x] = float(dv["g"]) if dv and nhom == "trai_cay" and abs(dv["g"] - g) <= 40 else float(g)
    t_kem = tong(kem, F)
    muc = {k: b[k] - t_kem[k] for k in ("p", "c", "f")}
    du_phong = {vt: [x for x in lua_chon(mau, vt, F, che_do, bo) if x not in mon] for vt in ("dam", "tinh_bot", "beo")}
    if mv:                                     # món Việt: thiếu đạm thì thêm trứng luộc / lòng trắng, không chèn món lạ
        du_phong = {"dam": [x for x in ("trung", "long_trang") if x in F and x not in mon and duoc_an(F[x], che_do) and x not in bo],
                    "tinh_bot": [], "beo": []}
    gram: dict[str, float] = {}
    for _ in range(4):
        gram = _giai(mon, F, muc, {mv["tb"]: SAN_TB_VIET.get(mv["tb"], 0)} if mv and mv.get("tb") else None)
        nho = [m for m, g in gram.items() if g < TOI_THIEU.get(m, TOI_THIEU_NHOM.get(F[m]["nhom"], 10)) * 0.8]
        if mv:                                         # món Việt giữ đủ thành phần chính (trừ dầu / món đạm phụ quá ít)
            nho = [m for m in nho if m == mv["beo"] or (m in mv["dam"][1:])]
        if nho and len(mon) > 1:                       # khẩu phần quá nhỏ (VD 5 g yến mạch) → bỏ món đó, giải lại
            mon = [m for m in mon if m not in nho]
            continue
        t = tong(gram, F)
        thieu = {"dam": (muc["p"] - t["p"]) * 4, "tinh_bot": (muc["c"] - t["c"]) * 4, "beo": (muc["f"] - t["f"]) * 9}
        vt, kc = max(thieu.items(), key=lambda x: x[1])
        if kc > 0.08 * b["kcal"] and du_phong.get(vt):  # chạm giới hạn khẩu phần → thêm 1 món cùng nhóm
            mon.append(du_phong[vt].pop(0))
            continue
        break
    gram = {m: _tron(m, g, F) for m, g in gram.items()}
    gram = {m: g for m, g in gram.items() if g >= 5}
    tat_ca = {**gram, **kem}
    t = tong(tat_ca, F)
    lech = abs(t["kcal"] - b["kcal"]) / max(b["kcal"], 1)
    return {**b, "mon": tat_ca, "vai_tro": {vt: next((m for m in mon if F[m]["nhom"] in _NHOM[vt]), None) for vt in _NHOM},
            "kem": list(kem), "mau": mau, "thuc": t, "lech": lech, "mon_viet": mv["ten"] if mv else None,
            "mon_id": mv["id"] if mv else None}


_NHOM = {"dam": {"dam", "sua"}, "tinh_bot": {"tinh_bot", "trai_cay"}, "beo": {"beo"}}


def thuc_don_ngay(h: HoSo, kq: dict, ngay_tap: bool, thu: int, ma: str = "", chon: dict | None = None,
                  bo: set[str] | None = None) -> list[dict]:
    F = foods()
    m = kq["tap"] if ngay_tap else kq["nghi"]
    out = []
    da_an: set[str] = set()                               # trái cây / rau không lặp trong ngày
    da_mon: set[str] = set()                              # món Việt không lặp trong ngày
    for b in phan_bua(h, m, ngay_tap):
        x = bua_an(b, F, h.che_do, _seed(ma, thu, b["bua"]), (chon or {}).get(b["bua"]), bo, da_an,
                   viet=h.kieu_td != "tach", tranh_mon=da_mon, it_tb=m["c"] < 160, uu_trai=TRAI_CAY_MT.get(h.muc_tieu))
        da_an |= {k for k in x["kem"] if F[k]["nhom"] == "trai_cay"}
        if x.get("mon_id"):
            da_mon.add(x["mon_id"])
            if MON_VIET[x["mon_id"]].get("nuoc"):            # đã có 1 món nước trong ngày → bữa sau ưu tiên món cơm
                da_mon |= {i for i, v in MON_VIET.items() if v.get("nuoc")}
        out.append(x)
    _them_loi_khuan(out, F, h.che_do, bo or set())
    _them_xo(out, F, h.che_do, bo or set(), m["kcal"])
    _can_ngay(out, m, F)
    _them_loi_khuan(out, F, h.che_do, bo or set())       # món lên men bị làm tròn mất khi cân ngày → thêm lại
    _bu_beo(out, m, F, h.che_do, bo or set(), h.nu)
    return out


# ------------------------------------------------------------------ v3.2: chất lượng khẩu phần (ngoài macro)
# Trái cây theo mục tiêu — giảm mỡ: ít năng lượng, nhiều xơ / nước, no lâu; tăng cơ: dễ ăn, nhiều năng lượng.
TRAI_CAY_MT = {
    "giam_mo": ["oi", "buoi", "tao", "kiwi", "dau_tay", "du_du", "dua_hau", "thanh_long", "cam", "viet_quat"],
    "recomp": ["oi", "buoi", "tao", "kiwi", "cam", "du_du", "thanh_long", "dau_tay", "viet_quat", "chuoi"],
    "tang_co": ["chuoi", "xoai", "nho", "du_du", "cam", "tao", "kiwi", "thanh_long", "viet_quat"],
    "giu": [],
}
CA_BEO = {"ca_hoi", "ca_thu"}


def _len_men(x: str, F: dict) -> bool:
    return "len_men" in F.get(x, {}).get("tag", [])


def _them_loi_khuan(ds: list[dict], F: dict, che_do: list[str], bo: set[str]) -> None:
    """Mỗi ngày ít nhất 1 món lên men (sữa chua / kefir; không ăn sữa → kim chi lượng nhỏ) — thêm vào bữa phụ hoặc bữa sáng."""
    if any(_len_men(x, F) for b in ds for x in b["mon"]):
        return
    chon = next(((x, g) for x, g in (("sua_chua_thuong", 100), ("kefir", 200), ("kim_chi", 50), ("dua_cai_chua", 50))
                 if x in F and duoc_an(F[x], che_do) and x not in bo), None)
    if not chon:
        return
    x, g = chon
    if F[x]["nhom"] == "rau":                                   # kim chi / dưa chua: ăn kèm bữa chính
        dich = next((b for b in ds if b["bua"] in ("trua", "toi")), ds[0] if ds else None)
    else:
        dich = next((b for b in ds if b["bua"].startswith("phu") and b.get("vai") != "truoc"), None) or \
            next((b for b in ds if b["bua"] == "sang"), ds[0] if ds else None)
    if dich is None:
        return
    dich["mon"][x] = float(g)
    dich["kem"] = list(dich.get("kem", [])) + [x]
    dich["loi_khuan"] = x


def _them_xo(ds: list[dict], F: dict, che_do: list[str], bo: set[str], kcal: float) -> None:
    """Thiếu xơ (< 80 % mức 14 g / 1.000 kcal) → thêm rau vào bữa chính, rồi 1 thìa hạt chia vào bữa có sữa chua."""
    def xo():
        return sum(tong(b["mon"], F)["xo"] for b in ds)
    mt = 0.8 * 14 * kcal / 1000
    for b in ds:
        if xo() >= mt:
            return
        rau = [x for x in b["mon"] if F[x]["nhom"] == "rau" and not _len_men(x, F)]
        if b["bua"] in ("trua", "toi") and rau:
            b["mon"][rau[0]] += 100.0
    if xo() < mt and "hat_chia" in F and duoc_an(F["hat_chia"], che_do) and "hat_chia" not in bo:
        dich = next((b for b in ds if any(_len_men(x, F) and F[x]["nhom"] in ("sua", "dam") for x in b["mon"])), None) or \
            next((b for b in ds if b["bua"] == "sang"), None)
        if dich is not None:
            dich["mon"]["hat_chia"] = 10.0
            dich["kem"] = list(dich.get("kem", [])) + ["hat_chia"]


def chat_luong_ngay(ngay: list[dict], h: "HoSo", la_tap: bool) -> list[dict]:
    """Đánh giá 1 ngày ăn ngoài calo / macro. Trả [{ok: True/False/None, ten, ct}]."""
    F = foods()
    mon = [x for b in ngay for x in b["mon"]]
    kcal = sum(b["thuc"]["kcal"] for b in ngay)
    xo = sum(b["thuc"]["xo"] for b in ngay)
    rq = rau_qua(ngay)
    out = []
    out.append({"ok": rq >= 400, "ten": "Rau + trái cây ≥ 400 g",
                "ct": f"{rq:.0f} g — WHO khuyến nghị tối thiểu 400 g rau quả / ngày. Thiếu thì thêm 1 chén rau luộc hoặc 1 phần trái cây."})
    mt_xo = 14 * kcal / 1000
    out.append({"ok": xo >= 0.8 * mt_xo, "ten": f"Chất xơ ≈ {mt_xo:.0f} g",
                "ct": f"Thực đơn có ~{xo:.0f} g (mức tham khảo 14 g / 1.000 kcal — Hướng dẫn dinh dưỡng Mỹ 2020–2025). "
                      "Tăng bằng rau, gạo lứt, yến mạch, đậu, ổi, hạt chia; uống thêm nước khi tăng xơ."})
    lm = [F[x]["ten"] for x in mon if _len_men(x, F)]
    out.append({"ok": bool(lm), "ten": "Lợi khuẩn (thực phẩm lên men)",
                "ct": ("Có: " + ", ".join(dict.fromkeys(lm)) + ". ") if lm else "Chưa có món lên men. "
                      "Sữa chua không đường / kefir có men sống hỗ trợ hệ vi sinh đường ruột; ăn cùng rau, chuối, yến mạch, hành tỏi "
                      "(chất xơ ‘nuôi’ lợi khuẩn). Kim chi, dưa chua nhiều muối — ăn lượng nhỏ."})
    tc = [x for x in dict.fromkeys(mon) if F[x]["nhom"] == "trai_cay"]
    pref = TRAI_CAY_MT.get(h.muc_tieu) or []
    if tc:
        hop = all(x in pref or x == "chuoi" for x in tc) if pref else True
        out.append({"ok": hop, "ten": "Trái cây hợp mục tiêu",
                    "ct": ", ".join(F[x]["ten"] for x in tc) + (" — " + GHI_TRAI.get(h.muc_tieu, "") if GHI_TRAI.get(h.muc_tieu) else "")})
    nguong = 0.3 * h.kg
    bua_chinh = [b for b in ngay if not b["bua"].startswith("phu")]
    it = [b["ten"] for b in bua_chinh if b["thuc"]["p"] < nguong]
    out.append({"ok": not it, "ten": f"Đạm chia đều (≥ {nguong:.0f} g mỗi bữa chính)",
                "ct": ("Thiếu ở: " + ", ".join(it) + ". " if it else "") +
                      "Mức tham khảo ~0,3–0,4 g/kg mỗi bữa, chia 3–5 bữa (Schoenfeld & Aragon, JISSN 2018) giúp tổng hợp cơ tốt hơn dồn 1 bữa."})
    if la_tap:
        sau = [b for b in ngay if b.get("vai") == "sau"]
        out.append({"ok": bool(sau), "ten": "Bữa sau tập có đạm + tinh bột",
                    "ct": "Trong ~2 giờ sau tập: 20–40 g đạm + tinh bột để hồi phục (khuyến nghị ISSN về thời điểm ăn — Kerksick et al., 2017)."})
    return out


GHI_TRAI = {"giam_mo": "ưu tiên trái cây nhiều xơ, nhiều nước, ít ngọt (ổi, bưởi, táo, dâu, thanh long) — no lâu, ít calo; nước ép không thay được trái cây nguyên quả.",
            "tang_co": "chuối, xoài, nho dễ ăn, nhiều năng lượng — hợp bữa phụ và quanh giờ tập.",
            "recomp": "chủ yếu trái cây nhiều xơ; chuối / xoài để quanh giờ tập."}


def chat_luong_tuan(tuan: list[dict]) -> list[dict]:
    F = foods()
    ca = sum(1 for d in tuan if any(x in CA_BEO for b in d["bua"] for x in b["mon"]))
    loai = {x for d in tuan for b in d["bua"] for x in b["mon"] if F[x]["nhom"] in ("rau", "trai_cay")}
    lm = sum(1 for d in tuan if any(_len_men(x, F) for b in d["bua"] for x in b["mon"]))
    return [
        {"ok": ca >= 2, "ten": f"Cá béo {ca} bữa / tuần (nên ≥ 2)",
         "ct": "Cá hồi, cá thu, cá trích, cá nục… cho omega-3 (EPA/DHA) — Hiệp hội Tim mạch Mỹ khuyến nghị ăn cá ~2 lần/tuần. "
               "Thiếu thì đổi món ở bữa trưa / tối sang cá hồi / cá thu, hoặc cân nhắc omega-3 (tab Bổ sung)."},
        {"ok": len(loai) >= 10, "ten": f"{len(loai)} loại rau / trái cây khác nhau trong tuần",
         "ct": "Càng đa dạng màu sắc (xanh, đỏ, cam, tím) càng nhiều loại vi chất & chất xơ khác nhau — mục tiêu tham khảo ≥ 10 loại / tuần."},
        {"ok": lm >= 5, "ten": f"Thực phẩm lên men {lm}/7 ngày", "ct": "Duy trì đều đặn quan trọng hơn ăn nhiều 1 lần."},
    ]


def vi_chat(h: "HoSo") -> list[tuple[str, str]]:
    """Điểm cần chú ý về vi chất / thói quen theo hồ sơ (gợi ý chung — không thay xét nghiệm, khám bác sĩ)."""
    cd = set(h.che_do or [])
    out = []
    if h.nu:
        out.append(("🩸 Sắt", "Phụ nữ trong tuổi sinh sản dễ thiếu sắt: thịt bò nạc, gan (1 lần/tuần), rau lá xanh đậm; ăn kèm trái cây "
                              "nhiều vitamin C (ổi, cam, kiwi) để hấp thu tốt hơn; trà / cà phê cách bữa ăn ~1 giờ."))
        out.append(("🦴 Canxi", "Sữa, sữa chua, đậu phụ làm với muối canxi, cá nhỏ ăn cả xương, rau cải — 2–3 phần mỗi ngày."))
    if cd & {"khong_sua"}:
        out.append(("🦴 Canxi (không dùng sữa)", "Đậu phụ, sữa đậu nành có bổ sung canxi, cá nhỏ cả xương, mè, rau cải xanh đậm."))
    if cd & {"chay_trung_sua", "thuan_chay"}:
        out.append(("🌱 Ăn chay", "Kết hợp đậu + ngũ cốc để đủ axit amin; chú ý B12 (thuần chay gần như luôn cần bổ sung), sắt, kẽm, "
                                 "omega-3 (hạt chia, hạt lanh, óc chó). Nên xét nghiệm định kỳ."))
    if h.tuoi >= 50:
        out.append(("👵 Trên 50 tuổi", "Giữ đạm cao mỗi bữa để chống mất cơ; chú ý canxi, vitamin D (ít ra nắng), vitamin B12."))
    if h.muc_tieu == "giam_mo":
        out.append(("🥗 Giảm mỡ mà vẫn no", "Ăn rau trước, rồi đạm, tinh bột sau cùng; uống 1 ly nước trước bữa; ưu tiên món luộc / hấp / canh; "
                                         "hạn chế nước ngọt, trà sữa, rượu bia (calo ‘vô hình’)."))
    if h.muc_tieu in ("tang_co", "recomp"):
        out.append(("🌙 Bữa tối muộn / trước ngủ", "Khó đủ đạm thì thêm sữa chua Hy Lạp hoặc sữa trước ngủ — một số nghiên cứu "
                                                  "cho thấy đạm trước ngủ hỗ trợ hồi phục; quan trọng nhất vẫn là đủ tổng đạm cả ngày."))
    out.append(("🧂 Muối & đường", "Hạn chế nước chấm, mì gói, đồ chế biến sẵn (nhiều muối); WHO khuyến nghị muối < 5 g/ngày, "
                                  "đường tự do < 10 % năng lượng."))
    out.append(("😴 Ngủ & nước", "Ngủ 7–9 tiếng; ngủ thiếu dễ thèm ăn và khó giữ cơ. Uống nước rải đều, nước tiểu vàng nhạt là đủ."))
    return out


def _bu_beo(ds: list[dict], m: dict, F: dict, che_do: list[str], bo: set[str], nu: bool = False) -> None:
    """Ngày nhiều món nước (phở, bún, cháo) thường thiếu béo. Thứ tự bù: dầu nấu cho món cơm / áp chảo → hạt ở bữa phụ
    (không phải bữa ngay trước tập) → dầu / mỡ hành cho các món còn lại."""
    thieu = m["f"] - sum(tong(b["mon"], F)["f"] for b in ds)
    if thieu * 9 < 45:
        return
    thu_tu = ("qua_bo", "hanh_nhan", "dau_phong", "hat_dieu") if nu else ("hanh_nhan", "dau_phong", "hat_dieu", "qua_bo")
    hat = [x for x in thu_tu if x in F and duoc_an(F[x], che_do) and x not in bo]
    co_dau = "dau_an" in F and "dau_an" not in bo
    nuoc = ("banh_pho", "bun", "hu_tieu", "chao", "xoi")

    def chinh(b):
        return not b["bua"].startswith("phu")

    buoc = [(lambda b: co_dau and chinh(b) and (not b.get("mon_id") or MON_VIET[b["mon_id"]]["tb"] not in nuoc), "dau_an"),
            (lambda b: bool(hat) and not chinh(b) and b.get("vai") != "truoc", "hat"),
            (lambda b: co_dau and chinh(b), "dau_an")]
    if nu:                                                 # nữ: ưu tiên béo từ trái bơ / hạt trước, dầu nấu sau
        co_bo = "qua_bo" in hat
        buoc = [(lambda b: bool(hat) and not chinh(b) and b.get("vai") != "truoc", "hat"),
                (lambda b: co_bo and chinh(b) and b["bua"] in ("sang", "trua"), "qua_bo")] + buoc
    for dk, loai in buoc:
        for b in ds:
            if thieu * 9 < 45:
                break
            if not dk(b):
                continue
            x = "dau_an" if loai == "dau_an" else "qua_bo" if loai == "qua_bo" else next((h for h in hat if h in b["mon"]), hat[0])
            g0 = b["mon"].get(x, 0)
            g1 = max(min(_tron(x, g0 + thieu / F[x]["f"] * 100, F), GIOI_HAN.get(x, 40)), TOI_THIEU.get(x, 5))
            if g1 > g0:
                b["mon"][x] = g1
                thieu -= (g1 - g0) * F[x]["f"] / 100
    for b in ds:
        b["thuc"] = tong(b["mon"], F)
        b["lech"] = abs(b["thuc"]["kcal"] - b["kcal"]) / max(b["kcal"], 1)


def _can_ngay(ds: list[dict], m: dict, F: dict) -> None:
    """Làm tròn từng bữa làm cả ngày hụt / dư → bù lại vào món đạm, tinh bột, béo của các bữa (tôn trọng giới hạn khẩu phần)."""
    for macro, vt, nhom in (("p", "dam", {"dam", "sua"}), ("c", "tinh_bot", {"tinh_bot", "trai_cay"}), ("f", "beo", {"beo"})):
        for _ in range(3):
            t = sum(tong(b["mon"], F)[macro] for b in ds)
            r = m[macro] - t
            if abs(r) * (9 if macro == "f" else 4) < 25:
                break
            cho = [(b, x) for b in ds for x in b["mon"] if (x not in b.get("kem", []) or (r < 0 and F[x]["nhom"] == "trai_cay"))
                   and F[x]["nhom"] in nhom and F[x][macro] > 0]                # dư tinh bột → được bớt cả trái cây (tối thiểu 60 g)
            if not cho:
                break
            phan = r / len(cho)
            doi = False
            for b, x in cho:
                g0 = b["mon"][x]
                san = SAN_TB_VIET.get(x, 0) if b.get("mon_id") and macro == "c" else 0
                if x in b.get("kem", []):
                    san = 60
                g1 = min(max(_tron(x, g0 + phan / F[x][macro] * 100, F), san), GIOI_HAN.get(x, 300))
                if g1 != g0:
                    b["mon"][x] = g1
                    doi = True
            if not doi:
                break
    for b in ds:
        for x, g in list(b["mon"].items()):           # khẩu phần lẻ (VD 5 g hạnh nhân) → làm tròn lên mức tối thiểu hoặc bỏ
            mn = TOI_THIEU.get(x, TOI_THIEU_NHOM.get(F[x]["nhom"], 5))
            if 0 < g < mn and x not in b.get("kem", []):
                b["mon"][x] = mn if g >= mn / 2 else 0
        b["mon"] = {x: g for x, g in b["mon"].items() if g >= 5}
        b["thuc"] = tong(b["mon"], F)
        b["lech"] = abs(b["thuc"]["kcal"] - b["kcal"]) / max(b["kcal"], 1)


def ngay_tap_tuan(h: HoSo) -> list[int]:
    if h.ngay_tap:
        return sorted({int(x) for x in h.ngay_tap})[:7]
    mac_dinh = {1: [2], 2: [1, 4], 3: [0, 2, 4], 4: [0, 1, 3, 4], 5: [0, 1, 2, 3, 4], 6: [0, 1, 2, 3, 4, 5], 7: list(range(7))}
    return mac_dinh.get(max(0, min(7, h.buoi_tuan)), [0, 2, 4])


def thuc_don_tuan(h: HoSo, kq: dict, ma: str = "", bo: set[str] | None = None) -> list[dict]:
    tap = set(ngay_tap_tuan(h))
    return [{"thu": t, "tap": t in tap, "bua": thuc_don_ngay(h, kq, t in tap, t, ma, bo=bo)} for t in range(7)]


def di_cho(tuan: list[dict]) -> list[tuple[str, float]]:
    F = foods()
    g: dict[str, float] = {}
    for d in tuan:
        for b in d["bua"]:
            for m, x in b["mon"].items():
                g[m] = g.get(m, 0) + x
    return sorted(((F[m]["ten"], v) for m, v in g.items()), key=lambda x: -x[1])


def quy_doi(nhom: str, gram_macro: float, macro: str, che_do: list[str]) -> list[tuple[str, float, str]]:
    """Bảng đổi tương đương: muốn `gram_macro` g (đạm / tinh bột) thì cần bao nhiêu g mỗi món."""
    F = foods()
    out = []
    for k, v in F.items():
        if v["nhom"] in nhom and v.get(macro, 0) > 0 and duoc_an(v, che_do):
            g = gram_macro / v[macro] * 100
            out.append((v["ten"], round(g / 5) * 5, mo_ta_luong(k, g, F)))
    return sorted(out, key=lambda x: x[1])


# ------------------------------------------------------------------ v1.2: thực phẩm bổ sung (KHÔNG bắt buộc — khuyến nghị)
BO_SUNG = {
    "whey": {"ten": "Whey protein", "icon": "🥛", "lieu": "1 muỗng (~25 g đạm) khi khó ăn đủ đạm — thường sau tập hoặc bữa phụ",
             "vi_sao": "Tiện để đạt đủ đạm mục tiêu; không hơn thịt cá về tác dụng, chỉ là tiện.",
             "luu_y": "Không dung nạp lactose → chọn whey isolate hoặc đạm thực vật.", "muc_tieu": {"giam_mo", "recomp", "tang_co", "giu"},
             "bang_chung": "Mạnh (ISSN 2017 về đạm — Jäger et al.)"},
    "creatine": {"ten": "Creatine monohydrate", "icon": "⚡", "lieu": "3–5 g mỗi ngày, uống lúc nào cũng được, không cần nạp liều",
                 "vi_sao": "Tăng sức mạnh, khối lượng tập và khối cơ khi tập tạ; giữ cơ khi giảm mỡ.",
                 "luu_y": "Cân có thể tăng 0,5–1,5 kg nước trong 2–4 tuần đầu (không phải mỡ). Bệnh thận → hỏi bác sĩ.",
                 "muc_tieu": {"tang_co", "recomp", "giam_mo", "giu"}, "bang_chung": "Mạnh (ISSN 2017 về creatine — Kreider et al.)"},
    "caffeine": {"ten": "Caffeine (cà phê đen / viên)", "icon": "☕", "lieu": "3–6 mg/kg, 30–60 phút trước tập (≈ 1–2 ly cà phê đen)",
                 "vi_sao": "Tăng sức tập, giảm cảm giác mệt.",
                 "luu_y": "Không dùng sau 15h nếu khó ngủ; huyết áp cao, tim mạch, mang thai → hỏi bác sĩ.",
                 "muc_tieu": {"giam_mo", "recomp", "tang_co"}, "bang_chung": "Mạnh (ISSN 2021 về caffeine — Guest et al.)"},
    "omega3": {"ten": "Omega-3 (dầu cá EPA + DHA)", "icon": "🐟", "lieu": "≈ 1–2 g EPA + DHA mỗi ngày khi ăn ít cá béo (< 2 bữa/tuần)",
               "vi_sao": "Sức khoẻ tim mạch chung; ăn đủ cá béo thì không cần.",
               "luu_y": "Đang dùng thuốc chống đông → hỏi bác sĩ.", "muc_tieu": {"giam_mo", "recomp", "tang_co", "giu"},
               "bang_chung": "Vừa — lợi ích chủ yếu cho sức khoẻ chung, không trực tiếp cho tăng cơ / giảm mỡ"},
    "vitamin_d": {"ten": "Vitamin D3", "icon": "☀️", "lieu": "Theo xét nghiệm / bác sĩ — thường 1.000–2.000 IU/ngày khi thiếu",
                  "vi_sao": "Người ít ra nắng, làm văn phòng dễ thiếu.", "luu_y": "Nên xét nghiệm trước; không tự uống liều cao kéo dài.",
                  "muc_tieu": {"giam_mo", "recomp", "tang_co", "giu"}, "bang_chung": "Chỉ có lợi khi đang thiếu"},
    "xo": {"ten": "Chất xơ hoà tan (psyllium)", "icon": "🌾", "lieu": "5 g pha nước trước bữa chính, uống thêm nước",
           "vi_sao": "No lâu hơn, hỗ trợ tiêu hoá khi ăn ít rau.", "luu_y": "Tăng dần liều để tránh đầy hơi.",
           "muc_tieu": {"giam_mo"}, "bang_chung": "Vừa"},
    "dien_giai": {"ten": "Điện giải (muối, kali)", "icon": "💧", "lieu": "Trong ngày tập ra nhiều mồ hôi / tập > 60 phút ngoài trời nóng",
                  "vi_sao": "Bù muối khoáng mất qua mồ hôi, đỡ chuột rút, mệt.", "luu_y": "Huyết áp cao → hỏi bác sĩ, chọn loại ít natri.",
                  "muc_tieu": {"giam_mo", "recomp", "tang_co", "giu"}, "bang_chung": "Tuỳ tình huống"},
}
GOI_Y_BO_SUNG = {"giam_mo": ["whey", "creatine", "caffeine", "xo"], "recomp": ["whey", "creatine", "caffeine"],
                 "tang_co": ["creatine", "whey"], "giu": ["whey", "omega3"]}


def bo_sung(h: HoSo, chon: list[str] | None = None) -> list[dict]:
    """Danh sách bổ sung HLV đã chọn cho khách (để trống → gợi ý mặc định theo mục tiêu); bỏ món xung đột chế độ ăn."""
    ids = chon if chon else GOI_Y_BO_SUNG.get(h.muc_tieu, ["whey", "creatine"])
    if "khong_sua" in (h.che_do or []) or "thuan_chay" in (h.che_do or []):
        ids = [i for i in ids if i != "whey"]
    return [{"id": i, **BO_SUNG[i]} for i in ids if i in BO_SUNG]


def rau_qua(ngay: list[dict]) -> float:
    F = foods()
    return sum(g for b in ngay for m, g in b["mon"].items() if F[m]["nhom"] in ("rau", "trai_cay"))
