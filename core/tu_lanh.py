"""v4.0 — 🧊 TỦ LẠNH: khách chọn các món đang có → web tính số gram từng món để khớp kcal + đạm / tinh bột / béo mục tiêu
(cả ngày, 1 bữa, hoặc phần còn lại hôm nay). Không import streamlit.

Cách tính: bình phương tối thiểu có giới hạn (scipy lsq_linear) trên 3 macro quy ra kcal, ưu tiên đạm (trọng số cao hơn);
rau giữ lượng cố định (ít calo, cần cho xơ). Số liệu thực phẩm là ƯỚC TÍNH theo bảng USDA của app (±10–15%).
"""
from __future__ import annotations

from core import dinh_duong as dd

NHOM_TEN = {"dam": "🍗 Đạm (thịt · cá · trứng · đậu)", "sua": "🥛 Sữa · sữa chua", "tinh_bot": "🍚 Tinh bột",
            "trai_cay": "🍎 Trái cây", "beo": "🥑 Chất béo · hạt", "rau": "🥦 Rau"}
W_DAM = 1.6                     # sai số đạm "đắt" hơn tinh bột / béo
RAU_NGAY, RAU_BUA = 300, 150    # gram rau cố định


def _ub(m: str, F: dict, he_so: float) -> float:
    u = dd.GIOI_HAN.get(m, 300)
    if m in ("whey",):
        return u * min(he_so, 2)
    if m in ("dau_an",):
        return u * min(he_so, 3)
    if m in ("trung",):                         # tối đa ~5 quả / ngày
        return u * min(he_so, 1.25)
    return u * he_so


def goi_y(mon: list[str], muc: dict, F: dict, he_so: float = 1.0) -> dict:
    """mon: id thực phẩm đang có · muc: {kcal, p, c, f} · he_so: 1 = một bữa, ~2,5 = cả ngày (nới giới hạn mỗi món).
    → {ds: [{id, ten, nhom, g, p, c, f, kcal, luong}], tong, muc, lech, canh_bao: [..], thieu_nhom: [..]}"""
    import numpy as np
    from scipy.optimize import lsq_linear
    mon = [m for m in dict.fromkeys(mon) if m in F]
    rau = [m for m in mon if F[m].get("nhom") == "rau"]
    giai = [m for m in mon if m not in rau]
    g_rau = {}
    if rau:
        tong_rau = RAU_NGAY if he_so > 1.5 else RAU_BUA
        g_rau = {m: tong_rau / len(rau) for m in rau}
    con = {x: float(muc.get(x) or 0) for x in ("p", "c", "f")}
    for m, g in g_rau.items():
        for x in con:
            con[x] -= F[m].get(x, 0) * g / 100
    out_g = dict(g_rau)
    if giai:
        A = np.array([[F[m]["p"] * 4 / 100 * W_DAM for m in giai], [F[m]["c"] * 4 / 100 for m in giai],
                      [F[m]["f"] * 9 / 100 for m in giai]])
        b = np.array([max(con["p"], 0) * 4 * W_DAM, max(con["c"], 0) * 4, max(con["f"], 0) * 9])
        ub = np.array([_ub(m, F, he_so) for m in giai], dtype=float)
        # kéo nhẹ mỗi món về ~35% mức tối đa của nó → chia lượng đều giữa các món cùng nhóm, không dồn hết vào 1 món
        lam = 60.0
        A = np.vstack([A, np.diag(lam / ub)])
        b = np.concatenate([b, np.full(len(giai), lam * 0.35)])
        r = lsq_linear(A, b, bounds=(np.zeros(len(giai)), ub))
        for m, x in zip(giai, r.x):
            out_g[m] = float(x)
    ds = []
    for m in mon:
        g = out_g.get(m, 0)
        nho = dd.TOI_THIEU.get(m, dd.TOI_THIEU_NHOM.get(F[m].get("nhom"), 20))
        g = dd._tron(m, g, F) if g >= nho * 0.6 else 0          # quá ít → bỏ, khỏi phải cân vài gram
        f = F[m]
        ds.append({"id": m, "ten": f.get("ten", m), "nhom": f.get("nhom", ""), "g": g,
                   **{x: f.get(x, 0) * g / 100 for x in ("p", "c", "f", "xo")}, "kcal": (f.get("kcal", 0) * g / 100),
                   "luong": dd.mo_ta_luong(m, g, F)})
    ds.sort(key=lambda d: (d["g"] == 0, list(NHOM_TEN).index(d["nhom"]) if d["nhom"] in NHOM_TEN else 9, -d["g"]))
    t = {x: sum(d[x] for d in ds) for x in ("p", "c", "f", "xo", "kcal")}
    t["kcal_macro"] = 4 * t["p"] + 4 * t["c"] + 9 * t["f"]
    mk = float(muc.get("kcal") or (4 * con["p"] + 4 * con["c"] + 9 * con["f"]))
    lech = {"kcal": t["kcal_macro"] - mk, **{x: t[x] - float(muc.get(x) or 0) for x in ("p", "c", "f")}}
    cb, thieu = [], []
    co = {F[m].get("nhom") for m in mon}
    if lech["p"] < -0.12 * max(float(muc.get("p") or 0), 1):
        cb.append(f"Thiếu khoảng {-lech['p']:.0f} g đạm so với mục tiêu — món đạm trong tủ chưa đủ.")
        thieu.append("dam")
    if lech["c"] < -0.15 * max(float(muc.get("c") or 0), 1):
        cb.append(f"Thiếu khoảng {-lech['c']:.0f} g tinh bột.")
        thieu.append("tinh_bot")
    if lech["f"] < -0.25 * max(float(muc.get("f") or 0), 1) and lech["f"] < -8:
        cb.append(f"Thiếu khoảng {-lech['f']:.0f} g chất béo → thêm ~{-lech['f'] / 4.6:.0f} thìa cà phê dầu khi nấu, hoặc 1 nắm nhỏ hạt.")
    if lech["f"] > 0.25 * max(float(muc.get("f") or 0), 1) and lech["f"] > 8:
        cb.append(f"Dư khoảng {lech['f']:.0f} g chất béo — các món đang có khá béo (thịt ba chỉ, đùi, hạt…).")
    if lech["kcal"] > 0.08 * mk and mk > 0:
        cb.append(f"Vượt khoảng {lech['kcal']:.0f} kcal — không thể khớp hơn với các món đang có.")
    if not co & {"dam", "sua"}:
        thieu.append("dam")
    if "rau" not in co:
        cb.append("Tủ chưa có rau — nên có ít nhất 1 món rau mỗi bữa chính (xơ, vi chất, no lâu).")
    for d in ds:
        if d["g"] == 0 and d["nhom"] != "rau":
            d["bo"] = True
    return {"ds": ds, "tong": t, "muc": muc, "lech": lech, "canh_bao": cb, "thieu_nhom": list(dict.fromkeys(thieu))}


def nen_mua(thieu: list[str], F: dict, che_do: list[str], bo: set[str], co: list[str], n: int = 4) -> list[str]:
    """Gợi ý món nên mua thêm cho nhóm còn thiếu (theo chế độ ăn của khách)."""
    UU = {"dam": ["uc_ga", "trung", "ca_ngu_hop", "dau_phu", "ca_ro_phi", "long_trang", "bo_nac", "sua_chua_hy_lap"],
          "tinh_bot": ["com", "khoai_lang", "yen_mach", "bun", "banh_mi", "chuoi"]}
    out = []
    for nh in thieu:
        for m in UU.get(nh, []):
            if m in F and m not in co and m not in bo and dd.duoc_an(F[m], che_do) and len(out) < n:
                out.append(F[m]["ten"])
    return out
