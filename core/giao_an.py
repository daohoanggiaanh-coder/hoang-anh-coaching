# Hoàng Anh Coaching v1.0 (2026-10-31) — giáo án, nhật ký số tạ, kỷ lục, gợi ý tăng tạ
"""
GiaoAn  (khoá = id giáo án): {ma_kh, ten, tac_gia: "hlv"|"khach", dang_dung, ghi_chu, buoi: [{ten, bai: [BAI]}]}
        BAI = {bai, nhom, hiep, lan ("8-10"), kg, rpe, nghi (giây), tempo, ghi_chu, ss (nhóm superset "A", "B"…)}
NhatKy  (khoá = id buổi):    {ma_kh, ngay, ga_id, buoi, nguoi_ghi: "hlv"|"khach", bai: [{bai, sets: [{kg, lan, rpe}]}],
                              cam_nhan (1–5), thoi_luong (phút), ghi_chu}

Ước tính 1RM: công thức Epley (1985) 1RM ≈ kg × (1 + lần / 30) — chỉ dùng để so tiến bộ, chính xác nhất khi ≤ 10 lần.
Gợi ý tăng tạ: "double progression" — mọi hiệp đạt mức lần cao nhất của khoảng (VD 10 trong "8-10") thì buổi sau
tăng 2,5 kg (thân trên / tạ đơn) hoặc 5 kg (thân dưới tạ đòn / máy); chưa đạt thì giữ tạ, cố thêm lần.
"""
from __future__ import annotations

import re
import uuid
from datetime import date

import pandas as pd

from core import config, db

NHOM_DUOI = {"squat", "hinge", "mot_chan", "iso_chan"}


def thu_vien() -> dict[str, dict]:
    """{tên bài: {nhom, ten_nhom, loai, dung_cu}} từ thư viện 89 bài (chung nguồn với Atlas Academy)."""
    d = config.load_json("thu_vien_bai_tap.json")
    out = {}
    for nk, n in d["nhom"].items():
        for b in n["bai"]:
            out[b["ten"]] = {"nhom": nk, "ten_nhom": n["ten"], "loai": b.get("loai", ""), "dung_cu": b.get("dung_cu", "")}
    return out


def ten_bai() -> list[str]:
    tv = thu_vien()
    return sorted(tv, key=lambda t: (tv[t]["ten_nhom"], t))


# ------------------------------------------------------------------ giáo án
def plans(ma: str) -> list[dict]:
    ds = list(db.latest("GiaoAn", ma).values())
    return sorted(ds, key=lambda g: (not g.get("dang_dung"), g.get("tac_gia") != "hlv", str(g.get("_luc"))), reverse=False)


def plan(ma: str, gid: str) -> dict | None:
    return db.latest("GiaoAn", ma).get(gid)


def save_plan(ma: str, g: dict, nguoi: str) -> str:
    gid = g.get("_khoa") or g.get("id") or uuid.uuid4().hex[:10]
    data = {k: v for k, v in g.items() if not k.startswith("_")}
    data.update({"ma_kh": ma, "id": gid})
    db.append("GiaoAn", gid, data, nguoi, ma)
    return gid


def xoa_plan(ma: str, gid: str, nguoi: str) -> bool:
    return db.append("GiaoAn", gid, {"ma_kh": ma, "id": gid, "xoa": 1}, nguoi, ma)


def bai_df(bai: list[dict]) -> pd.DataFrame:
    cols = ["ss", "bai", "hiep", "lan", "kg", "rpe", "nghi", "tempo", "ghi_chu"]
    df = pd.DataFrame([{c: b.get(c, "") for c in cols} for b in bai] or [{c: "" for c in cols}], columns=cols)
    for c in ("hiep", "kg", "rpe", "nghi"):
        df[c] = pd.to_numeric(df[c], errors="coerce")
    for c in ("ss", "bai", "lan", "tempo", "ghi_chu"):
        df[c] = df[c].fillna("").astype(str)
    return df


def df_bai(df: pd.DataFrame) -> list[dict]:
    tv = thu_vien()
    out = []
    for r in df.to_dict("records"):
        ten = str(r.get("bai") or "").strip()
        if not ten:
            continue
        x = {"bai": ten, "nhom": tv.get(ten, {}).get("nhom", "")}
        for c in ("ss", "lan", "tempo", "ghi_chu"):
            v = str(r.get(c) or "").strip()
            if v and v.lower() != "nan":
                x[c] = v
        for c in ("hiep", "kg", "rpe", "nghi"):
            v = pd.to_numeric(r.get(c), errors="coerce")
            if pd.notna(v):
                x[c] = float(v) if c in ("kg", "rpe") else int(v)
        out.append(x)
    return out


def khoang_lan(s) -> tuple[int, int] | None:
    nums = [int(x) for x in re.findall(r"\d+", str(s or ""))]
    if not nums:
        return None
    return (min(nums), max(nums))


# ------------------------------------------------------------------ nhật ký
def logs(ma: str) -> list[dict]:
    return sorted(db.latest("NhatKy", ma).values(), key=lambda x: (str(x.get("ngay")), str(x.get("_luc"))))


def save_log(ma: str, nk: dict, nguoi: str) -> str:
    lid = nk.get("_khoa") or nk.get("id") or uuid.uuid4().hex[:10]
    data = {k: v for k, v in nk.items() if not k.startswith("_")}
    data.update({"ma_kh": ma, "id": lid})
    db.append("NhatKy", lid, data, nguoi, ma)
    return lid


def xoa_log(ma: str, lid: str, nguoi: str) -> bool:
    return db.append("NhatKy", lid, {"ma_kh": ma, "id": lid, "xoa": 1}, nguoi, ma)


def e1rm(kg, lan) -> float | None:
    try:
        kg, lan = float(kg), int(lan)
    except (TypeError, ValueError):
        return None
    if kg <= 0 or lan <= 0:
        return None
    return round(kg if lan == 1 else kg * (1 + lan / 30), 1)


def lich_su_bai(ma: str, L: list[dict] | None = None) -> pd.DataFrame:
    """1 dòng / bài / buổi: ngay, bai, top_kg, top_lan, e1rm, volume, so_hiep."""
    rows = []
    for nk in (logs(ma) if L is None else L):
        for b in nk.get("bai", []):
            sets = [s for s in b.get("sets", []) if _f(s.get("kg")) is not None and _i(s.get("lan"))]
            if not sets:
                continue
            best = max(sets, key=lambda s: (e1rm(s.get("kg"), s.get("lan")) or 0, _f(s.get("kg")) or 0))
            rows.append({"ngay": pd.to_datetime(str(nk.get("ngay"))[:10], errors="coerce"), "bai": b.get("bai"),
                         "top_kg": _f(best.get("kg")), "top_lan": _i(best.get("lan")),
                         "e1rm": max(e1rm(s.get("kg"), s.get("lan")) or 0 for s in sets),
                         "volume": sum((_f(s.get("kg")) or 0) * (_i(s.get("lan")) or 0) for s in sets),
                         "so_hiep": len(sets), "id": nk.get("id")})
    df = pd.DataFrame(rows, columns=["ngay", "bai", "top_kg", "top_lan", "e1rm", "volume", "so_hiep", "id"])
    return df.dropna(subset=["ngay"]).sort_values("ngay").reset_index(drop=True)


def _f(v) -> float | None:
    try:
        x = float(str(v).replace(",", "."))
        return None if x != x else x
    except (TypeError, ValueError):
        return None


def _i(v) -> int | None:
    x = _f(v)
    return int(x) if x is not None and x > 0 else None


def ky_luc(ls: pd.DataFrame) -> pd.DataFrame:
    if ls.empty:
        return ls
    g = ls.sort_values("e1rm").groupby("bai").tail(1)
    return g.sort_values("bai").reset_index(drop=True)


def lan_truoc(ma: str, ten_bai: str, L: list[dict] | None = None, tru_id: str | None = None) -> dict | None:
    for nk in reversed(logs(ma) if L is None else L):
        if tru_id and nk.get("id") == tru_id:
            continue
        for b in nk.get("bai", []):
            if b.get("bai") == ten_bai and b.get("sets"):
                return {"ngay": nk.get("ngay"), "sets": b["sets"]}
    return None


def goi_y(bai: dict, truoc: dict | None) -> tuple[float | None, str]:
    """(kg đề xuất, lời nhắn) cho buổi tới theo double progression."""
    kg_ga = _f(bai.get("kg"))
    kl = khoang_lan(bai.get("lan"))
    if not truoc:
        return kg_ga, "Buổi đầu với bài này — chọn mức tạ còn dư 2–3 lần ở hiệp cuối."
    sets = [s for s in truoc["sets"] if _f(s.get("kg")) is not None and _i(s.get("lan"))]
    if not sets:
        return kg_ga, ""
    kg = max(_f(s["kg"]) for s in sets)
    lans = [_i(s["lan"]) for s in sets if _f(s["kg"]) == kg]
    buoc = 5.0 if bai.get("nhom") in NHOM_DUOI and kg >= 40 else 2.5
    if kl and min(lans) >= kl[1]:
        return kg + buoc, f"Lần trước {kg:g} kg đạt đủ {kl[1]} lần mọi hiệp → thử {kg + buoc:g} kg."
    if kl:
        return kg, f"Giữ {kg:g} kg, cố lên {kl[1]} lần ở mọi hiệp rồi mới tăng tạ."
    return kg, f"Lần trước {kg:g} kg."


def tong_buoi(nk: dict) -> dict:
    sets = [s for b in nk.get("bai", []) for s in b.get("sets", [])]
    vol = sum((_f(s.get("kg")) or 0) * (_i(s.get("lan")) or 0) for s in sets)
    return {"bai": len([b for b in nk.get("bai", []) if b.get("sets")]), "hiep": len(sets), "volume": vol}


def chuoi_tuan(L: list[dict], hom_nay: date) -> int:
    """Số tuần liên tiếp (tính tới tuần này) có ít nhất 1 buổi ghi."""
    tuans = {pd.Timestamp(str(x.get("ngay"))[:10]).to_period("W") for x in L if x.get("ngay")}
    p = pd.Timestamp(hom_nay).to_period("W")
    if p not in tuans:
        p -= 1
    n = 0
    while p in tuans:
        n += 1
        p -= 1
    return n
