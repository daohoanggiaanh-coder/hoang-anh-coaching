# Hoàng Anh Coaching v1.4 (2026-10-31) — cardio: HLV đặt target theo ngày tập / ngày nghỉ, khách (hoặc HLV từ ảnh) nhập kết quả,
# cộng thành target tuần, ngày thiếu được BÙ CHIA ĐỀU cho các ngày còn lại (có trần mỗi ngày; khách "rảnh" mới cho dồn quá trần).
# Lưu trong bảng DinhDuong (khoá cardio_muc|<mã> và cardio|<mã>|…) để không phải thêm trang tính mới.
from __future__ import annotations

import uuid
from datetime import date, timedelta

from core import db

MAY = {"bo_doc": "Máy chạy bộ (đi dốc)", "chay": "Máy chạy bộ (chạy)", "xe_dap": "Xe đạp tập", "elip": "Máy elip",
       "leo_thang": "Máy leo cầu thang", "ngoai_troi": "Đi bộ / chạy ngoài trời", "khac": "Khác"}
CO_DOC = {"bo_doc", "chay", "ngoai_troi"}           # máy có độ dốc + tốc độ km/h
MET_MAY = {"xe_dap": 6.8, "elip": 5.0, "leo_thang": 9.0, "khac": 5.0}   # Compendium 2011, mức vừa — ước lượng

MAC_DINH = {
    "tap": {"may": "bo_doc", "doc": 8.0, "toc_do": 5.0, "phut": 25, "toi_da": 35},       # ngày tập tạ: 20–30 phút sau buổi tạ
    "nghi": {"may": "bo_doc", "doc": 10.0, "toc_do": 5.0, "phut": 60, "toi_da": 90},     # ngày nghỉ: 45–90 phút
    "ngay_tap": [],          # thứ có tập tạ (0 = T2); rỗng → lấy từ lịch cố định / thông số dinh dưỡng
    "ngay_off": [],          # thứ nghỉ hẳn, không cardio
    "ranh": False,           # khách rảnh: phần bù vượt trần được dồn tiếp
    "ghi_chu": "",
}
KHOANG = {"tap": (20, 30), "nghi": (45, 90)}


# ------------------------------------------------------------------ cài đặt target
def cai_dat(ma: str) -> dict:
    v = db.latest("DinhDuong", ma).get(f"cardio_muc|{ma}") or {}
    out = {k: (dict(v0) if isinstance(v0, dict) else v0) for k, v0 in MAC_DINH.items()}
    for k in ("tap", "nghi"):
        out[k].update({x: y for x, y in (v.get(k) or {}).items() if x in MAC_DINH[k]})
    for k in ("ngay_tap", "ngay_off", "ranh", "ghi_chu"):
        if k in v:
            out[k] = v[k]
    out["_co"] = bool(v)
    return out


def luu_cai_dat(ma: str, c: dict, nguoi: str) -> bool:
    return db.append("DinhDuong", f"cardio_muc|{ma}", {k: v for k, v in c.items() if not k.startswith("_")} | {"ma_kh": ma}, nguoi, ma)


def ngay_tap(c: dict, k: dict | None = None, hs: dict | None = None) -> list[int]:
    if c.get("ngay_tap"):
        return sorted({int(x) for x in c["ngay_tap"]})
    if hs and hs.get("ngay_tap"):
        return sorted({int(x) for x in hs["ngay_tap"]})
    if k:
        from core import store
        ds = sorted({int(x["thu"]) for x in store.lich_co_dinh(k)})
        if ds:
            return ds
    return [0, 1, 3, 4]


# ------------------------------------------------------------------ nhật ký
def logs(ma: str) -> list[dict]:
    out = [v for kk, v in db.latest("DinhDuong", ma).items() if kk.startswith(f"cardio|{ma}|") and not v.get("xoa")]
    return sorted(out, key=lambda x: (str(x.get("ngay")), str(x.get("_luc", ""))))


def ghi(ma: str, r: dict, nguoi: str, vai: str) -> bool:
    lid = r.get("id") or f"cardio|{ma}|{r['ngay']}|{uuid.uuid4().hex[:6]}"
    data = {**r, "id": lid, "ma_kh": ma, "ngay": str(r["ngay"]), "nguon": vai}
    return db.append("DinhDuong", lid, data, nguoi, ma)


def xoa(ma: str, lid: str, nguoi: str) -> bool:
    return db.append("DinhDuong", lid, {"id": lid, "ma_kh": ma, "xoa": 1}, nguoi, ma)


def kcal(r: dict, kg: float | None) -> float | None:
    """Ước tính kcal. Máy chạy / đi bộ: phương trình ACSM (đi bộ ≤ 6,4 km/h, chạy ≥ 8 km/h, ở giữa nội suy). Máy khác: MET.
    Sai số thường ±10–20 % — số máy hiện cũng chỉ là ước lượng."""
    try:
        phut, kg = float(r.get("phut") or 0), float(kg or 0)
    except (TypeError, ValueError):
        return None
    if not phut or not kg:
        return None
    if r.get("may") in CO_DOC and r.get("toc_do"):
        s = float(r["toc_do"]) * 1000 / 60                      # m/phút
        g = float(r.get("doc") or 0) / 100
        di, chay = 0.1 * s + 1.8 * s * g + 3.5, 0.2 * s + 0.9 * s * g + 3.5
        t = min(max((float(r["toc_do"]) - 6.4) / 1.6, 0), 1)
        vo2 = di * (1 - t) + chay * t                          # ml/kg/phút
        return round(vo2 * kg / 1000 * 5 * phut)
    met = MET_MAY.get(r.get("may"), 5.0)
    return round(met * 3.5 * kg / 200 * phut)


def quang_duong(r: dict) -> float | None:
    if r.get("quang_duong"):
        return float(r["quang_duong"])
    if r.get("may") in CO_DOC and r.get("toc_do") and r.get("phut"):
        return round(float(r["toc_do"]) * float(r["phut"]) / 60, 2)
    return None


# ------------------------------------------------------------------ tuần: target gốc, đã làm, bù chia đều
def dau_tuan(d: date) -> date:
    return d - timedelta(days=d.weekday())


def target_goc(c: dict, tap: list[int]) -> dict[int, dict]:
    out = {}
    for t in range(7):
        if t in {int(x) for x in c.get("ngay_off") or []}:
            out[t] = {"loai": "off", "phut": 0, "toi_da": 0, "may": "", "doc": 0, "toc_do": 0}
        else:
            loai = "tap" if t in tap else "nghi"
            out[t] = {"loai": loai, **{x: c[loai][x] for x in ("phut", "toi_da", "may", "doc", "toc_do")}}
    return out


def _chia_deu(thieu: float, ngay: list[int], tran: dict[int, float], ranh: bool) -> tuple[dict[int, float], float]:
    """Chia `thieu` phút cho các ngày theo kiểu rót nước: mỗi ngày nhận phần BẰNG NHAU, ngày nào chạm trần thì phần dư chia tiếp
    cho ngày còn chỗ. Khách rảnh → phần còn dư sau cùng chia đều tiếp (vượt trần). Trả ({thu: phút thêm}, phút không bù được)."""
    them = {t: 0.0 for t in ngay}
    con = float(thieu)
    mo = [t for t in ngay if tran[t] > 0]
    while con > 0.5 and mo:
        phan = con / len(mo)
        con = 0.0
        moi = []
        for t in mo:
            cho = tran[t] - them[t]
            if cho <= phan:
                them[t] += cho
                con += phan - cho
            else:
                them[t] += phan
                moi.append(t)
        mo = moi
    if con > 0.5 and ranh and ngay:
        for t in ngay:
            them[t] += con / len(ngay)
        con = 0.0
    return them, con


def tuan(c: dict, tap: list[int], L: list[dict], hom: date, kg: float | None = None, tu: date | None = None) -> dict:
    """Tổng hợp 1 tuần (T2 → CN; mặc định tuần chứa `hom`): target gốc, đã làm, target đã bù cho hôm nay → CN, % hoàn thành."""
    d0 = tu or dau_tuan(hom)
    goc = target_goc(c, tap)
    lam = {t: 0.0 for t in range(7)}
    kc = {t: 0.0 for t in range(7)}
    buoi: dict[int, list[dict]] = {t: [] for t in range(7)}
    for r in L:
        try:
            d = date.fromisoformat(str(r["ngay"])[:10])
        except ValueError:
            continue
        if d0 <= d <= d0 + timedelta(days=6):
            t = (d - d0).days
            lam[t] += float(r.get("phut") or 0)
            kc[t] += float(r.get("kcal") or kcal(r, kg) or 0)
            buoi[t].append(r)
    W = sum(x["phut"] for x in goc.values())
    hi = min(max((hom - d0).days, 0), 7)                       # ngày đã qua: 0 .. hi-1
    thieu = sum(goc[t]["phut"] - lam[t] for t in range(hi))     # >0 thiếu, <0 làm dư
    con_ngay = [t for t in range(hi, 7) if goc[t]["phut"] > 0]
    tran = {t: max(goc[t]["toi_da"] - goc[t]["phut"], 0) for t in con_ngay}
    them, khong_bu = _chia_deu(max(thieu, 0), con_ngay, tran, bool(c.get("ranh"))) if thieu > 0 else ({t: 0.0 for t in con_ngay}, 0.0)
    if thieu < 0 and con_ngay:                                 # làm dư → giảm đều, không dưới mức thấp nhất của khoảng
        giam = -thieu / len(con_ngay)
        for t in con_ngay:
            san = KHOANG[goc[t]["loai"]][0]
            them[t] = -min(giam, max(goc[t]["phut"] - san, 0))
    ngay = []
    for t in range(7):
        g = goc[t]
        moi = round((g["phut"] + them.get(t, 0)) / 5) * 5 if t >= hi else g["phut"]
        ngay.append({"thu": t, "ngay": d0 + timedelta(days=t), **g, "target": moi,
                     "bu": moi - g["phut"], "lam": round(lam[t]), "kcal": round(kc[t]), "buoi": buoi[t],
                     "qua": t < hi, "hom_nay": t == hi and hom < d0 + timedelta(days=7)})
    da = sum(lam.values())
    return {"tu": d0, "den": d0 + timedelta(days=6), "ngay": ngay, "W": W, "da": round(da), "con": max(round(W - da), 0),
            "pct": round(min(da / W, 1.5) * 100) if W else 0, "thieu": round(max(thieu, 0)), "khong_bu": round(khong_bu),
            "kcal": round(sum(kc.values()))}


def lich_su_tuan(c: dict, tap: list[int], L: list[dict], hom: date, kg: float | None = None, so: int = 8) -> list[dict]:
    out = []
    for i in range(so - 1, -1, -1):
        d = dau_tuan(hom) - timedelta(weeks=i)
        w = tuan(c, tap, L, hom, kg, d)
        out.append({"tu": d, "W": w["W"], "da": w["da"], "pct": w["pct"]})
    return out


# ------------------------------------------------------------------ đọc ảnh màn hình máy (cần khoá AI)
PROMPT_ANH = ("Ảnh chụp màn hình máy cardio (máy chạy bộ / xe đạp / elip / leo thang) hoặc ứng dụng đồng hồ. Đọc các số và trả JSON: "
              '{"may": một trong ["bo_doc","chay","xe_dap","elip","leo_thang","ngoai_troi","khac"], "phut": tổng thời gian (phút, số thập phân), '
              '"doc": độ dốc % (số, null nếu không có), "toc_do": tốc độ km/h (trung bình nếu có, null nếu không), '
              '"quang_duong": km (null nếu không), "kcal": số kcal máy hiện (null nếu không), "nhip_tim": nhịp tim TB (null nếu không)}. '
              "Thời gian dạng mm:ss hoặc hh:mm:ss phải đổi ra phút. Đơn vị dặm (mile) đổi ra km (× 1,609). Không đoán số không có trên ảnh.")


def doc_anh(img: bytes) -> dict:
    from core import llm
    raw = llm.chat_json("Bạn là trợ lý nhập liệu phòng gym, đọc số chính xác từ ảnh.", [{"role": "user", "content": PROMPT_ANH}],
                        images=[img], max_tokens=400, timeout=60)
    out = {}
    if raw.get("may") in MAY:
        out["may"] = raw["may"]
    for k, lo, hi in (("phut", 1, 300), ("doc", 0, 40), ("toc_do", 1, 25), ("quang_duong", 0.1, 60), ("kcal", 5, 3000), ("nhip_tim", 50, 220)):
        try:
            v = float(raw.get(k))
        except (TypeError, ValueError):
            continue
        if lo <= v <= hi:
            out[k] = round(v, 1)
    return out
