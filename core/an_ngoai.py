# Hoàng Anh Coaching v2.0 (2026-11-03) — ăn ngoài + nhật ký bữa ăn trong ngày.
# Món ăn ngoài: data/an_ngoai.json (macro ƯỚC LƯỢNG ±20–30 %). Nhật ký lưu trong bảng DinhDuong:
#   an|<mã>|<ngày>|<bữa>  → {loai: dung | ngoai | tu_nhap | chua, mon, phan, p, c, f, kcal, ghi_chu}
#   an_thich|<mã>        → {mon: [id món ăn ngoài khách thích], rieng: [{ten, p, c, f, kcal}]}
from __future__ import annotations

import json
from datetime import date
from functools import lru_cache
from pathlib import Path

from core import db

HOP = {"tot": ("✅ Hợp mục tiêu", "#2E7D4F"), "sua": ("🟡 Được nếu gọi đúng", "#C8A24A"), "han_che": ("🔴 Hạn chế", "#B4442F")}
LOAI = {"dung": "✅ Ăn đúng thực đơn", "ngoai": "🍜 Ăn ngoài", "tu_nhap": "✍️ Tự nhập", "chua": "⏳ Chưa ăn"}
PHAN = {0.5: "½ phần", 0.75: "¾ phần", 1.0: "1 phần", 1.5: "1,5 phần", 2.0: "2 phần"}


@lru_cache(maxsize=1)
def data() -> dict:
    return json.loads((Path(__file__).resolve().parent.parent / "data" / "an_ngoai.json").read_text(encoding="utf-8"))


def mon() -> dict[str, dict]:
    return {m["id"]: m for m in data()["mon"]}


def nhom() -> list[str]:
    out: list[str] = []
    for m in data()["mon"]:
        if m["nhom"] not in out:
            out.append(m["nhom"])
    return out


def macro(m: dict, phan: float = 1.0) -> dict:
    return {x: round(float(m.get(x) or 0) * phan, 1) for x in ("kcal", "p", "c", "f")}


def diem(m: dict, muc_tieu: str, con: dict | None = None) -> float:
    """Điểm gợi ý: hợp mục tiêu + mật độ đạm (g đạm / 100 kcal) + vừa với phần còn lại trong ngày."""
    s = {"tot": 3.0, "sua": 1.5, "han_che": 0.0}[m["hop"]]
    s += min(m["p"] / max(m["kcal"], 1) * 100, 10) * (0.5 if muc_tieu == "giam_mo" else 0.3)
    if con and con.get("kcal", 0) > 0:
        if m["kcal"] > con["kcal"] * 1.15:
            s -= 2
        if con.get("p", 0) > 20 and m["p"] >= 25:
            s += 1
    return s


def goi_y(muc_tieu: str, con: dict | None = None, thich: list[str] | None = None, n: int = 6) -> list[dict]:
    ds = [m for m in data()["mon"] if m["hop"] != "han_che" and m["kcal"] >= 250]
    ds.sort(key=lambda m: -(diem(m, muc_tieu, con) + (1.5 if m["id"] in (thich or []) else 0)))
    return ds[:n]


def phan_hop(m: dict, muc_bua: dict) -> float:
    """Phần nên ăn để không vượt kcal bữa (làm tròn ½ / ¾ / 1)."""
    r = muc_bua.get("kcal", 0) / max(m["kcal"], 1)
    return 1.0 if r >= 0.95 else 0.75 if r >= 0.7 else 0.5


# ------------------------------------------------------------------ nhật ký bữa
def _k(ma: str, ngay: date, bua: str) -> str:
    return f"an|{ma}|{ngay.isoformat()}|{bua}"


def nhat_ky(ma: str, ngay: date) -> dict[str, dict]:
    tien_to = f"an|{ma}|{ngay.isoformat()}|"
    return {kk[len(tien_to):]: v for kk, v in db.latest("DinhDuong", ma).items() if kk.startswith(tien_to) and not v.get("xoa")}


def ghi(ma: str, ngay: date, bua: str, v: dict, nguoi: str) -> bool:
    return db.append("DinhDuong", _k(ma, ngay, bua), v | {"ngay": ngay.isoformat(), "bua": bua, "ma_kh": ma}, nguoi, ma)


def xoa(ma: str, ngay: date, bua: str, nguoi: str) -> bool:
    return db.append("DinhDuong", _k(ma, ngay, bua), {"xoa": True, "ma_kh": ma}, nguoi, ma)


def thich(ma: str) -> dict:
    v = db.latest("DinhDuong", ma).get(f"an_thich|{ma}") or {}
    return {"mon": list(v.get("mon") or []), "rieng": list(v.get("rieng") or [])}


def luu_thich(ma: str, v: dict, nguoi: str) -> bool:
    return db.append("DinhDuong", f"an_thich|{ma}", v | {"ma_kh": ma}, nguoi, ma)


def thuc_te(bua: dict, log: dict | None) -> dict | None:
    """Macro thực ăn của 1 bữa theo nhật ký; None = chưa ghi / chưa ăn."""
    if not log or log.get("loai") == "chua":
        return None
    if log.get("loai") == "dung":
        return {x: float(bua["thuc"][x]) for x in ("kcal", "p", "c", "f")}
    return {x: float(log.get(x) or 0) for x in ("kcal", "p", "c", "f")}


def tong_ngay(ngay_td: list[dict], logs: dict[str, dict], m: dict) -> dict:
    """Đã ăn / còn lại trong ngày + mục tiêu chia lại cho các bữa chưa ăn."""
    da = {x: 0.0 for x in ("kcal", "p", "c", "f")}
    chua: list[dict] = []
    for b in ngay_td:
        t = thuc_te(b, logs.get(b["bua"]))
        if t is None:
            chua.append(b)
        else:
            for x in da:
                da[x] += t[x]
    muc = {"kcal": float(m["kcal"]), "p": float(m["p"]), "c": float(m["c"]), "f": float(m["f"])}
    con = {x: muc[x] - da[x] for x in muc}
    # chia phần còn lại cho các bữa chưa ăn theo tỷ trọng bữa trong thực đơn gợi ý
    chia = {}
    for x in ("kcal", "p", "c", "f"):
        w = sum(b["thuc"][x] for b in chua) or 1
        for b in chua:
            chia.setdefault(b["bua"], {})[x] = max(con[x], 0) * b["thuc"][x] / w
    return {"da": da, "muc": muc, "con": con, "chia": chia, "so_chua": len(chua)}


def loi_khuyen(t: dict) -> list[str]:
    """Nhắc ngắn theo phần còn lại (mức thực hành, không phải ngưỡng cứng)."""
    con, muc, out = t["con"], t["muc"], []
    if t["so_chua"] == 0:
        if con["p"] > 15:
            out.append(f"Còn thiếu khoảng {con['p']:.0f} g đạm — thêm 1 hũ sữa chua Hy Lạp / 1 ly sữa + 2 lòng trắng, hoặc 1 muỗng whey.")
        if con["kcal"] < -0.1 * muc["kcal"]:
            out.append("Hôm nay vượt năng lượng hơn 10 % — không cần bù bằng nhịn ăn ngày mai; mai ăn đúng thực đơn, đi thêm 2.000–3.000 bước.")
        return out or ["Đã ghi đủ các bữa hôm nay 👍"]
    if con["kcal"] <= 0:
        out.append("Đã đủ năng lượng cả ngày — các bữa còn lại chọn đạm nạc + rau (ức gà, cá, trứng trắng, đậu hũ), bỏ tinh bột và dầu.")
    elif con["f"] < 5:
        out.append("Béo trong ngày gần hết — bữa còn lại luộc / hấp, bỏ dầu, bỏ da, không chấm sốt béo.")
    if con["p"] > 0 and con["kcal"] > 0 and con["p"] * 4 > con["kcal"] * 0.6:
        out.append("Đạm còn nhiều so với năng lượng còn lại — ưu tiên món đạm nạc: ức gà, cá, tôm, lòng trắng trứng, sữa chua Hy Lạp.")
    if con["c"] < 15 and con["kcal"] > 0:
        out.append("Tinh bột gần hết — bữa còn lại ít cơm / bún, thay bằng rau + đạm nạc.")
    return out or ["Đang đúng hướng — phần còn lại đã chia cho các bữa chưa ăn (dòng ⏳ ở mỗi bữa)."]
