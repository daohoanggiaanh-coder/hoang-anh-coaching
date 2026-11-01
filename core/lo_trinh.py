# Hoàng Anh Coaching v1.1 (2026-10-31) — lộ trình & tốc độ đạt mục tiêu (CHỈ HLV XEM)
"""Ghép số đo (SoDo) + cân hằng ngày (CanNang) → bảng đo theo thời gian, rồi dùng muc_tieu.tien_do (Atlas v3.64):
% hoàn thành so với % thời gian, tốc độ thật (hồi quy tuyến tính) → ngày dự kiến đạt đích.
Thêm: tốc độ cân 14 ngày gần nhất theo đường TB 7 ngày, chuyên cần 4 tuần, gợi ý điều chỉnh."""
from __future__ import annotations

from datetime import date, timedelta

import pandas as pd

from core import buoi, muc_tieu as mt, store, tien_do as td

CHI = ["can_nang", "pbf", "smm", "v_eo", "mo_noi_tang"]


def bang_do(ma: str) -> pd.DataFrame:
    SD, CAN = td.so_do(ma), td.can_ngay(ma)
    parts = []
    if not SD.empty:
        parts.append(SD[["ngay"] + [c for c in CHI if c in SD.columns]])
    if not CAN.empty:
        parts.append(CAN.rename(columns={"kg": "can_nang"})[["ngay", "can_nang"]])
    if not parts:
        return pd.DataFrame(columns=["ngay"] + CHI)
    M = pd.concat(parts, ignore_index=True)
    M["ngay"] = pd.to_datetime(M["ngay"])
    M = M.groupby("ngay", as_index=False).agg({c: "mean" for c in CHI if c in M.columns})   # 1 dòng / ngày
    for c in CHI:
        if c not in M.columns:
            M[c] = float("nan")
    return M.sort_values("ngay").reset_index(drop=True)


def ho_so_muc_tieu(k: dict) -> dict:
    return {**k, "muc_tieu_can": k.get("can_muc_tieu") or k.get("muc_tieu_can")}


def tien_do(k: dict, hom: date) -> dict | None:
    return mt.tien_do(ho_so_muc_tieu(k), bang_do(k["ma"]), hom)


def toc_do_can(ma: str, ngay_xet: int = 14) -> float | None:
    """kg / tuần theo đường trung bình 7 ngày trong `ngay_xet` ngày gần nhất (cần ≥ 2 điểm cách nhau ≥ 6 ngày)."""
    CAN = td.can_ngay(ma)
    if len(CAN) < 2:
        return None
    d = CAN.assign(ngay=pd.to_datetime(CAN["ngay"]))
    d = d[d["ngay"] >= d["ngay"].iloc[-1] - pd.Timedelta(days=ngay_xet)]
    if len(d) < 2 or (d["ngay"].iloc[-1] - d["ngay"].iloc[0]).days < 6:
        return None
    x = (d["ngay"] - d["ngay"].iloc[0]).dt.days.astype(float)
    y = d["tb7"].astype(float)
    den = ((x - x.mean()) ** 2).sum()
    return round(float(((x - x.mean()) * (y - y.mean())).sum() / den * 7), 2) if den else None


def chuyen_can(k: dict, hom: date, so_tuan: int = 4) -> dict:
    """Số buổi đã tập mỗi tuần (lịch đánh dấu Đã tập + nhật ký buổi, mỗi ngày tính 1) so với kế hoạch."""
    tu = hom - timedelta(days=hom.weekday()) - timedelta(weeks=so_tuan - 1)
    ngay = {date.fromisoformat(str(h.get("ngay"))[:10]) for h in store.hens(k["ma"]).values()
            if h.get("trang_thai") == "xong" and str(h.get("ngay"))[:10] >= tu.isoformat()}
    ngay |= {s["ngay"] for s in buoi.sessions(k["ma"]) if s["ngay"] >= tu}
    tuans = []
    for i in range(so_tuan):
        a = tu + timedelta(weeks=i)
        tuans.append({"tuan": f"{a:%d/%m}", "buoi": sum(a <= d <= a + timedelta(days=6) for d in ngay)})
    ke_hoach = len(store.lich_co_dinh(k)) or None
    tb = round(sum(t["buoi"] for t in tuans[:-1]) / max(so_tuan - 1, 1), 1) if so_tuan > 1 else tuans[0]["buoi"]
    return {"tuans": tuans, "ke_hoach": ke_hoach, "tb": tb,
            "ty_le": round(tb / ke_hoach * 100) if ke_hoach else None}


def goi_y(tdo: dict | None, cc: dict, toc: float | None, muc_tieu_loai: str) -> list[str]:
    """Gợi ý điều chỉnh theo luật đơn giản — HLV quyết định cuối cùng."""
    out = []
    if cc.get("ty_le") is not None and cc["ty_le"] < 75:
        out.append(f"Chuyên cần mới đạt ~{cc['ty_le']} % kế hoạch ({cc['tb']:g}/{cc['ke_hoach']} buổi/tuần) — ưu tiên giữ lịch "
                   "trước khi chỉnh ăn.")
    if tdo:
        nguoc = [r for r in tdo["rows"] if r["pct"] < 0]
        cham = tdo["tong"] < tdo["tg_pct"] - 15
        if nguoc:
            out.append("Chỉ số đi ngược mục tiêu: " + ", ".join(r["ten"] for r in nguoc)
                       + " — hỏi lại khách về ăn uống, giấc ngủ, căng thẳng 2 tuần qua.")
        elif cham and (cc.get("ty_le") is None or cc["ty_le"] >= 75):
            if muc_tieu_loai in ("giam_mo", "recomp"):
                out.append("Đi tập đều nhưng chậm tiến độ → cân nhắc giảm 100–200 kcal/ngày (bớt tinh bột ngày nghỉ) "
                           "hoặc thêm 2.000–3.000 bước/ngày; đo lại sau 2 tuần.")
            elif muc_tieu_loai == "tang_co":
                out.append("Đi tập đều nhưng cơ / cân tăng chậm → thêm 150–200 kcal/ngày, kiểm tra đủ đạm và tăng tạ đều.")
    if toc is not None and muc_tieu_loai == "giam_mo" and toc < -1.2:
        out.append(f"Cân đang giảm nhanh ({toc:g} kg/tuần) — nguy cơ mất cơ; cân nhắc tăng nhẹ năng lượng.")
    if toc is not None and muc_tieu_loai == "giam_mo" and toc > 0.1:
        out.append(f"Đường cân TB 7 ngày đang tăng ({toc:+g} kg/tuần) trong 2 tuần gần nhất.")
    if not out:
        out.append("Chưa thấy điểm cần chỉnh — giữ kế hoạch, đo lại theo lịch.")
    return out


def ke_hoach_line(goc: float, dich: float, d0: date, han: date) -> pd.DataFrame:
    return pd.DataFrame({"ngay": pd.to_datetime([d0, han]), "v": [goc, dich]})


# ------------------------------------------------------------------ v1.6: đánh giá mục tiêu cân — khả thi, tốc độ, lời khuyên
# Mốc tham chiếu: giảm mỡ giữ cơ ~0,5–1,0 % cân nặng / tuần (Helms et al. 2014, JISSN); tăng cơ "sạch" ~0,25–0,5 % / tuần
# (mức thực hành phổ biến). Người BMI ≥ 30 thường giảm nhanh hơn được mà vẫn an toàn → nới ngưỡng 0,25 %.
def danh_gia_can(k: dict, CAN: pd.DataFrame, hom: date) -> dict | None:
    import math
    if len(CAN) < 1:
        return None
    t = td._so(k.get("can_muc_tieu"))
    d0, kg0 = CAN["ngay"].iloc[0], float(CAN["kg"].iloc[0])
    now = float(CAN["tb7"].iloc[-1])
    span = (CAN["ngay"].iloc[-1] - d0).days
    cao = td._so(k.get("chieu_cao"))
    bmi = now / (cao / 100) ** 2 if cao else None
    toc14 = toc_do_can(k["ma"], 14)
    toc_all = round((now - kg0) / (span / 7), 2) if span >= 6 else None
    toc = toc14 if toc14 is not None else toc_all
    pct = round(toc / now * 100, 2) if toc is not None else None
    nho14 = int((CAN["ngay"] >= CAN["ngay"].iloc[-1] - timedelta(days=13)).sum())
    out = {"kg0": kg0, "d0": d0, "now": round(now, 1), "span": span, "toc": toc, "pct": pct, "toc_all": toc_all, "bmi": bmi,
           "muc_tieu": t, "loi_khuyen": [], "so_lan_14": nho14}
    if not t:
        out["loi_khuyen"].append("Chưa đặt **cân mục tiêu** — đặt ở trang Khách hoặc Lộ trình để web đánh giá tính khả thi.")
        return out
    giam = t < kg0
    con = round(now - t, 1) if giam else round(t - now, 1)
    da = round(kg0 - now, 1) if giam else round(now - kg0, 1)
    tong = abs(kg0 - t)
    out.update({"giam": giam, "con": con, "da": da, "pct_xong": max(0, min(100, round(da / tong * 100))) if tong else 100})
    nguong = (0.5, 1.0) if giam else (0.25, 0.5)
    if giam and bmi and bmi >= 30:
        nguong = (0.5, 1.25)
    out["nguong"] = nguong
    # ---- đánh giá tốc độ hiện tại
    if pct is None:
        out["toc_nhan"], out["toc_mau"] = "Chưa đủ dữ liệu (cần cân ≥ 7 ngày)", "#8b8577"
    else:
        p = -pct if giam else pct
        if p < 0.1:
            out["toc_nhan"], out["toc_mau"] = ("Đang chững / đi ngược", "#B4442F")
        elif p < nguong[0]:
            out["toc_nhan"], out["toc_mau"] = ("Chậm hơn mức khuyến nghị", "#D98E04")
        elif p <= nguong[1]:
            out["toc_nhan"], out["toc_mau"] = ("Tốt — đúng nhịp khuyến nghị", "#1E7B4A")
        else:
            out["toc_nhan"], out["toc_mau"] = ("Nhanh hơn khuyến nghị", "#B4442F" if p > nguong[1] * 1.6 else "#D98E04")
    # ---- khả thi theo hạn
    han = None
    try:
        han = date.fromisoformat(str(k.get("muc_tieu_ngay"))[:10])
    except ValueError:
        han = store.han_goi(k)
    out["han"] = han
    giua = (nguong[0] + nguong[1]) / 2 / 100
    if con > 0:
        tuan_an_toan = math.log(t / now) / math.log(1 - giua) if giam else math.log(t / now) / math.log(1 + giua)
        out["ngay_an_toan"] = hom + timedelta(weeks=max(tuan_an_toan, 0))
        if toc and ((giam and toc < 0) or (not giam and toc > 0)):
            out["ngay_nhip"] = hom + timedelta(weeks=con / abs(toc))
    if han and con > 0:
        tuan_con = max((han - hom).days / 7, 0.1)
        can_pct = round(con / tuan_con / now * 100, 2)
        out["can_pct"] = can_pct
        if can_pct <= nguong[1] * 0.85:
            out["kha_thi"], out["kt_mau"] = "Khả thi", "#1E7B4A"
        elif can_pct <= nguong[1] * 1.15:
            out["kha_thi"], out["kt_mau"] = "Thách thức — cần bám sát kế hoạch", "#D98E04"
        else:
            out["kha_thi"], out["kt_mau"] = "Khó đạt đúng hạn ở tốc độ an toàn", "#B4442F"
    elif con <= 0:
        out["kha_thi"], out["kt_mau"] = "Đã đạt mục tiêu 🎉", "#1E7B4A"
    else:
        out["kha_thi"], out["kt_mau"] = "Chưa có hạn — xem mốc dự kiến", "#8b8577"
    # ---- mục tiêu có hợp lý không
    if cao:
        bmi_t = t / (cao / 100) ** 2
        out["bmi_t"] = round(bmi_t, 1)
        if bmi_t < 18.5:
            out["loi_khuyen"].append(f"⚠️ Cân mục tiêu {t:g} kg ứng với BMI {bmi_t:.1f} (< 18,5 — thiếu cân). Nên đặt lại mục tiêu theo "
                                     "% mỡ / vòng eo thay vì số cân.")
        elif giam and bmi_t >= 25:
            out["loi_khuyen"].append(f"Cân mục tiêu {t:g} kg ứng với BMI {bmi_t:.1f}. Có thể chia thành mốc này trước, đạt rồi đặt mốc "
                                     "tiếp — mốc gần dễ giữ động lực hơn.")
    # ---- lời khuyên theo tốc độ
    if span <= 21 and pct is not None and giam and -pct > nguong[1]:
        out["loi_khuyen"].append("Khách mới vào 2–3 tuần: giảm nhanh lúc đầu phần lớn là **nước + glycogen** (bớt tinh bột, muối). "
                                 "Đừng vội tăng ăn — đánh giá tốc độ thật từ tuần 3–4.")
    elif pct is not None and giam and -pct > nguong[1] * 1.3:
        out["loi_khuyen"].append("Giảm nhanh kéo dài dễ **mất cơ, mệt, đói, ngủ kém** → tăng 100–200 kcal/ngày (chủ yếu tinh bột quanh "
                                 "buổi tập), giữ đạm 2 g/kg, theo dõi sức tạ.")
    elif pct is not None and giam and -pct < nguong[0]:
        out["loi_khuyen"].append("Tốc độ chậm → trước hết kiểm tra **tuân thủ**: check-in ăn theo thực đơn, cardio đủ phút, số bước. "
                                 "Đã tuân thủ tốt ≥ 2 tuần mà vẫn chậm → giảm 100–200 kcal/ngày hoặc thêm 2.000–3.000 bước/ngày.")
    elif pct is not None and not giam and pct > nguong[1]:
        out["loi_khuyen"].append("Tăng cân nhanh hơn mức tăng cơ thực tế → phần dư dễ thành mỡ; bớt 100–150 kcal/ngày.")
    elif pct is not None and not giam and pct < nguong[0]:
        out["loi_khuyen"].append("Tăng chậm → thêm 150–200 kcal/ngày, kiểm tra đủ đạm, tăng tạ đều mỗi tuần.")
    elif pct is not None:
        out["loi_khuyen"].append("Đúng nhịp — **giữ nguyên** kế hoạch, không cần chỉnh. Khen khách để giữ động lực.")
    if out.get("kha_thi", "").startswith("Khó"):
        mk = out.get("ngay_an_toan")
        out["loi_khuyen"].append("Không nên ép nhanh hơn để kịp hạn. Gợi ý: dời hạn"
                                 + (f" tới khoảng **{mk:%d/%m/%Y}**" if mk else "") + " hoặc đặt mốc trung gian trong hạn hiện tại.")
    if nho14 < 4:
        out["loi_khuyen"].append(f"14 ngày qua chỉ có {nho14} lần cân — khuyên khách cân ≥ 4 buổi sáng/tuần để đường trung bình chính xác.")
    out["loi_khuyen"].append("Cân chỉ là 1 chỉ số — kết hợp vòng eo, % mỡ (InBody) và ảnh mỗi 2–4 tuần: tập tạ có thể giữ cân nhưng vẫn "
                             "giảm mỡ.")
    return out
