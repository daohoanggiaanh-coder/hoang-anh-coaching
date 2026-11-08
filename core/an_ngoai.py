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
LOAI = {"dung": "✅ Đúng thực đơn", "ghi": "📷 Ảnh / mô tả (AI)", "ngoai": "🍜 Ăn ngoài", "tu_nhap": "✍️ Tự nhập số",
        "chua": "⏳ Chưa ăn"}
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
    ke = {b["bua"] for b in ngay_td}
    for bua, lg in logs.items():                      # bữa phụ / ăn thêm ngoài thực đơn
        if bua not in ke:
            t = thuc_te({}, lg)
            if t:
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


def bua_them(logs: dict[str, dict]) -> list[tuple[str, dict]]:
    return sorted(((b, v) for b, v in logs.items() if b.startswith("them_")), key=lambda x: x[0])


def lich_su(ma: str, tu: date, den: date) -> dict[date, dict[str, dict]]:
    """Nhật ký bữa theo ngày (cho báo cáo)."""
    out: dict[date, dict[str, dict]] = {}
    tien = f"an|{ma}|"
    for kk, v in db.latest("DinhDuong", ma).items():
        if not kk.startswith(tien) or v.get("xoa"):
            continue
        try:
            d = date.fromisoformat(kk[len(tien):len(tien) + 10])
        except ValueError:
            continue
        if tu <= d <= den:
            out.setdefault(d, {})[kk[len(tien) + 11:]] = v
    return out


# ------------------------------------------------------------------ v3.3: món / combo ăn ngoài tương đương 1 bữa trong thực đơn
def _combo_key(m: dict) -> tuple:
    return (round(m.get("kcal", 0) / 25), round(m.get("p", 0) / 3), round(m.get("c", 0) / 5), round(m.get("f", 0) / 3))


_CACHE: dict = {}


SUA = {"sua_tuoi_kd", "sua_chua_kd", "sua_chua_hl", "sua_dau_nanh_kd"}
BOT_TB = {"Bún · phở · hủ tiếu", "Cơm"}                     # món có thể để lại bớt bánh / cơm


def _bien_the(m: dict) -> list[dict]:
    """Món chính + bản 'để lại ⅓ bánh / cơm' (bớt 30 % tinh bột) — cách thực tế nhất để khỏi dư calo khi ăn ngoài."""
    out = [m]
    if m["nhom"] in BOT_TB and m["kcal"] >= 400:
        bot = 0.3 * m["c"]
        out.append({**m, "id": m["id"] + "_bot", "goc": m["id"], "ten": m["ten"] + (" (để lại ⅓ cơm)" if m["nhom"] == "Cơm" else " (để lại ⅓ bánh / bún)"),
                    "c": round(m["c"] - bot, 1), "kcal": round(m["kcal"] - bot * 4)})
    return out


def tuong_duong(muc: dict, n: int = 3, chinh: bool = False) -> list[dict]:
    """Món hoặc combo ăn ngoài có kcal gần mục tiêu bữa (−20 % … +15 %) và đủ đạm (≥ 80 %), xếp theo độ khớp macro.
    chinh=True (bữa chính): ưu tiên có 1 món ăn chính (phở, cơm, bún…) + tối đa 2 món kèm."""
    key = (_combo_key(muc), chinh)
    if key in _CACHE:
        return _CACHE[key]
    from itertools import combinations
    M = [m for m in data()["mon"] if m["hop"] != "han_che" and m["nhom"] != "Đồ uống · tráng miệng"]
    lon = [v for m in M if m["kcal"] >= 250 for v in _bien_the(m)]
    nho = [m for m in M if m["kcal"] < 250]
    K, P, C, F = (max(float(muc.get(x, 0)), 1) for x in ("kcal", "p", "c", "f"))
    co_lon = [[a] for a in lon] + [[a, b] for a in lon for b in nho] + [[a, *x] for a in lon for x in combinations(nho, 2)]
    chi_nho = [[m] for m in nho] + [list(x) for x in combinations(nho, 2)] + [list(x) for x in combinations(nho, 3)]

    def tinh(cands):
        out = []
        for ds in cands:
            if sum(m["id"] in SUA for m in ds) > 1:
                continue
            t = {x: sum(float(m[x]) for m in ds) for x in ("kcal", "p", "c", "f")}
            if not (0.8 * K <= t["kcal"] <= 1.15 * K) or t["p"] < 0.8 * P:
                continue
            sc = 2 * ((t["kcal"] - K) / K) ** 2 + 2 * (min(t["p"] - P, 0) / P) ** 2 + 0.6 * ((t["c"] - C) / max(C, 20)) ** 2 \
                + 0.6 * ((t["f"] - F) / max(F, 8)) ** 2 + 0.05 * (len(ds) - 1) + (0.15 if any(m["hop"] == "sua" for m in ds) else 0)
            out.append((sc, ds, t))
        return sorted(out, key=lambda x: x[0])

    kq = tinh(co_lon) if chinh else tinh(co_lon + chi_nho)
    if chinh and len(kq) < n:
        kq += tinh(chi_nho)
    chon, dau, dung = [], set(), {}
    for sc, ds, t in kq:
        goc = ds[0].get("goc", ds[0]["id"])
        if goc in dau or any(dung.get(m["id"], 0) >= 2 for m in ds):     # đa dạng: không lặp món chính, món kèm tối đa 2 lần
            continue
        dau.add(goc)
        for m in ds:
            dung[m["id"]] = dung.get(m["id"], 0) + 1
        chon.append({"mon": ds, "ten": " + ".join(m["ten"] for m in ds), "thuc": t,
                     "goi": "; ".join(m["goi"] for m in ds if m.get("goi"))})
        if len(chon) >= n:
            break
    _CACHE[key] = chon
    return chon


# ------------------------------------------------------------------ v3.3: quy tắc bàn tay (hand-portion)
# Theo cách áng chừng phổ biến của Precision Nutrition: 1 lòng bàn tay đạm ≈ 20–30 g đạm · 1 vốc tay tinh bột ≈ 20–30 g
# tinh bột · 1 ngón cái béo ≈ 7–12 g béo · 1 nắm tay rau ≈ 1 chén rau. Web dùng số giữa (25 / 25 / 10) để quy đổi.
BAN_TAY = {"p": 25.0, "c": 25.0, "f": 10.0}


def _nua(x: float) -> float:
    return max(round(x * 2) / 2, 0.5) if x >= 0.25 else 0.0


def so_phan(m: dict, rau_g: float = 0) -> dict:
    return {"p": _nua(m.get("p", 0) / BAN_TAY["p"]), "c": _nua(m.get("c", 0) / BAN_TAY["c"]),
            "f": _nua(m.get("f", 0) / BAN_TAY["f"]), "rau": _nua(rau_g / 90) if rau_g else 0.0}


def so_s(x: float) -> str:
    if not x:
        return "0"
    n, du = int(x), x - int(x)
    return (str(n) if n else "") + ("½" if du else "") if (n or du) else "0"
