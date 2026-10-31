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
