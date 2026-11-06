# Hoàng Anh Coaching v2.5 (2026-11-06) — GHI BỮA ĂN BẰNG ẢNH / MÔ TẢ + AI ƯỚC LƯỢNG CALO & GỢI Ý ĐIỀU CHỈNH theo mục tiêu.
"""Có khoá AI (GEMINI_API_KEY miễn phí ở aistudio.google.com — hoặc ANTHROPIC / OPENAI): AI nhìn ảnh + đọc mô tả → từng món,
lượng ước tính, kcal · đạm · tinh bột · béo, nhận xét theo mục tiêu và phần còn lại trong ngày, gợi ý bữa tiếp theo.
Không có khoá: web tự ước lượng từ mô tả (khớp tên món trong danh sách ăn ngoài + bảng thực phẩm, "150g ức gà"…) — độ tin cậy thấp.
Mọi con số là ƯỚC LƯỢNG: ảnh không cho biết dầu mỡ, nước sốt, khối lượng thật → sai số thường ±20–30 %, có thể hơn."""
from __future__ import annotations

import re
import unicodedata

from core import an_ngoai as an, dinh_duong as dd, llm

# khối lượng 1 đơn vị đếm thường gặp (gram, ước lượng) — dùng khi khách ghi "2 trứng", "1 chén cơm"
DON_VI = {"trung": 50, "com": 150, "chuoi": 120, "tao": 180, "cam": 150, "khoai lang": 150, "banh mi": 80, "sua chua": 100,
          "dau hu": 120, "yen mach": 40, "sua": 200, "bo": 150}
# món chung chung không có trong bảng — 1 phần ước lượng
CHUNG = {"rau": ("Rau luộc / xào ít dầu (1 đĩa)", {"kcal": 50, "p": 3, "c": 7, "f": 1.5}),
         "canh": ("Canh rau (1 chén)", {"kcal": 40, "p": 2, "c": 5, "f": 1}),
         "salad": ("Salad (1 đĩa, ít sốt)", {"kcal": 90, "p": 2, "c": 8, "f": 6}),
         "trai cay": ("Trái cây (1 chén)", {"kcal": 80, "p": 1, "c": 20, "f": 0}),
         "nuoc ngot": ("Nước ngọt (1 lon)", {"kcal": 140, "p": 0, "c": 35, "f": 0}),
         "tra sua": ("Trà sữa (1 ly)", {"kcal": 400, "p": 3, "c": 70, "f": 12})}
TIN_CAY = {"cao": "🟢 khá chắc", "vua": "🟡 tương đối", "thap": "🔴 ước lượng thô"}

PROMPT = """Bạn là chuyên gia dinh dưỡng thể thao của Hoàng Anh Coaching (Việt Nam). Khách gửi {nguon} một bữa ăn.
Mô tả của khách: "{mo_ta}"
Bữa: {bua}. Mục tiêu khách: {muc_tieu}. Giới tính: {gt}.
Mục tiêu bữa này khoảng: {muc_bua}. Phần còn lại cả ngày TRƯỚC bữa này: {con_lai}.

Nhiệm vụ:
1. Liệt kê từng món / thành phần nhìn thấy hoặc được mô tả, ước lượng lượng ăn (gram hoặc chén / tô / miếng) theo khẩu phần Việt Nam,
   tính kcal, đạm (p), tinh bột (c), béo (f) bằng gram. Nhớ tính dầu mỡ chiên xào, nước sốt, nước chấm, da, mỡ nếu có.
2. Cộng tổng. Nếu mô tả của khách có số lượng cụ thể, ưu tiên số của khách hơn ảnh.
3. Đánh giá ngắn gọn bữa này so với mục tiêu bữa và mục tiêu chung (đủ đạm chưa, dư tinh bột / béo không), giọng thân thiện, tích cực.
4. 1–3 gợi ý điều chỉnh CỤ THỂ cho lần sau (bỏ gì, giảm bao nhiêu, đổi món gì) và 1 gợi ý cho bữa tiếp theo để cả ngày vẫn đúng mục tiêu.
5. Độ tin cậy: "cao" (mô tả rõ lượng), "vua", "thap" (ảnh mờ / khó đoán lượng / nhiều dầu mỡ khuất).
Không bịa món không có. Không nói về bệnh, không chẩn đoán. Xưng "HLV", gọi khách là "{goi}".
Trả JSON đúng mẫu:
{{"mon":[{{"ten":"...","luong":"...","kcal":0,"p":0,"c":0,"f":0}}],"tong":{{"kcal":0,"p":0,"c":0,"f":0}},
"do_tin_cay":"cao|vua|thap","nhan_xet":"...","dieu_chinh":["..."],"bua_sau":"..."}}"""


def _so(x, lo=0.0, hi=5000.0) -> float:
    try:
        v = float(str(x).replace(",", "."))
    except (TypeError, ValueError):
        return 0.0
    return round(min(max(v, lo), hi), 1)


def _sach(raw: dict) -> dict:
    mon = []
    for m in raw.get("mon") or []:
        if isinstance(m, dict) and m.get("ten"):
            mon.append({"ten": str(m["ten"])[:60], "luong": str(m.get("luong") or "")[:40], "kcal": _so(m.get("kcal"), 0, 3000),
                        "p": _so(m.get("p"), 0, 300), "c": _so(m.get("c"), 0, 500), "f": _so(m.get("f"), 0, 300)})
    tong = {x: round(sum(m[x] for m in mon), 1) for x in ("kcal", "p", "c", "f")} if mon else \
        {x: _so((raw.get("tong") or {}).get(x)) for x in ("kcal", "p", "c", "f")}
    if tong["kcal"] <= 0 and (tong["p"] or tong["c"] or tong["f"]):
        tong["kcal"] = round(tong["p"] * 4 + tong["c"] * 4 + tong["f"] * 9)
    dc = raw.get("dieu_chinh") or []
    return {"mon": mon, "tong": tong, "do_tin_cay": raw.get("do_tin_cay") if raw.get("do_tin_cay") in TIN_CAY else "vua",
            "nhan_xet": str(raw.get("nhan_xet") or "")[:600], "dieu_chinh": [str(x)[:200] for x in (dc if isinstance(dc, list) else [dc])][:3],
            "bua_sau": str(raw.get("bua_sau") or "")[:300]}


def phan_tich(anh: list[bytes], mo_ta: str, bua: str, muc_tieu: str, gioi_tinh: str, muc_bua: dict | None,
              con_lai: dict | None, goi: str = "bạn") -> dict:
    """Gọi AI (ảnh + mô tả). Lỗi / không có khoá → ước lượng offline từ mô tả."""
    def fm(m):
        return "—" if not m else f"{m['kcal']:.0f} kcal · đạm {m['p']:.0f} g · tinh bột {m['c']:.0f} g · béo {m['f']:.0f} g"
    if llm.is_online() and (anh or mo_ta.strip()):
        try:
            p = PROMPT.format(nguon="ảnh và mô tả" if anh else "mô tả", mo_ta=mo_ta.strip() or "(không mô tả)", bua=bua,
                              muc_tieu=muc_tieu, gt=gioi_tinh, muc_bua=fm(muc_bua), con_lai=fm(con_lai), goi=goi)
            raw = llm.chat_json("Bạn là chuyên gia dinh dưỡng thể thao, ước lượng khẩu phần thực tế, trả lời bằng tiếng Việt.",
                                [{"role": "user", "content": p}], images=anh[:3] or None, max_tokens=1200, timeout=90)
            out = _sach(raw)
            if out["mon"] or out["tong"]["kcal"]:
                return out | {"nguon": "ai"}
        except llm.LLMError:
            pass
    return uoc_luong_offline(mo_ta, muc_bua) | {"nguon": "offline"}


# ------------------------------------------------------------------ ước lượng không cần AI
def _bo_dau(s: str) -> str:
    s = unicodedata.normalize("NFD", s.lower().replace("đ", "d"))
    return "".join(ch for ch in s if unicodedata.category(ch) != "Mn")


def _tu_khoa(ten: str) -> str:
    return _bo_dau(re.sub(r"\(.*?\)", "", ten)).strip()


def uoc_luong_offline(mo_ta: str, muc_bua: dict | None = None) -> dict:
    """Tách mô tả theo dấu phẩy / dòng; mỗi phần: "<số>g <tên>" → bảng thực phẩm; tên món ăn ngoài → 1 phần (½, 2… nếu ghi)."""
    F = dd.foods()
    M = an.mon()
    mon = []
    chua_ro = []
    for phan in [x.strip() for x in re.split(r"[,\n;+]| và ", mo_ta) if x.strip()]:
        t = _bo_dau(phan)
        g = re.search(r"(\d+(?:[.,]\d+)?)\s*(g|gr|gram|ml)\b", t)
        he = 1.0
        mh = re.match(r"^\s*(\d+(?:[.,]\d+)?|nua|1/2)\s+(?!g\b)", t)
        if mh:
            he = 0.5 if mh.group(1) in ("nua", "1/2") else float(mh.group(1).replace(",", "."))
        best = None
        for mid, m in M.items():                      # món ăn ngoài — khớp tên dài nhất
            k = _tu_khoa(m["ten"].split("/")[0])
            if k and (k in t or t in k) and (not best or len(k) > best[0]):
                best = (len(k), "an", mid)
        for fid, f in F.items():
            k = _tu_khoa(f["ten"])
            k1 = " ".join(k.split()[:2])
            if k1 and k1 in t and (not best or len(k1) > best[0]):
                best = (len(k1), "tp", fid)
        if not best:
            gn = next(((ten, v) for kk, (ten, v) in CHUNG.items() if kk in t), None)
            if gn:
                x = {kk: round(v_ * he, 1) for kk, v_ in gn[1].items()}
                mon.append({"ten": gn[0], "luong": f"{he:g} phần", **x})
            else:
                chua_ro.append(phan)
            continue
        if best[1] == "an":
            m = M[best[2]]
            x = an.macro(m, he if not g else 1.0)
            mon.append({"ten": m["ten"], "luong": f"{he:g} × {m['phan']}", **x})
        else:
            f = F[best[2]]
            dv = next((v for kk, v in DON_VI.items() if _tu_khoa(f["ten"]).startswith(kk)), 100)
            gam = float(g.group(1).replace(",", ".")) if g else dv * he
            r = gam / 100
            mon.append({"ten": f["ten"], "luong": f"{gam:.0f} g", "kcal": round(f["kcal"] * r), "p": round(f["p"] * r, 1),
                        "c": round(f["c"] * r, 1), "f": round(f["f"] * r, 1)})
    tong = {x: round(sum(m[x] for m in mon), 1) for x in ("kcal", "p", "c", "f")}
    nx = ("Ước lượng thô từ mô tả (chưa có AI). " + (f"Chưa nhận ra: {', '.join(chua_ro)} — nhập tay số kcal nếu biết." if chua_ro else "")
          if mon else "Chưa nhận ra món nào — ghi rõ hơn, VD “150g ức gà, 1 chén cơm, rau luộc” hoặc nhập tay số kcal.")
    dc = []
    if muc_bua and mon:
        if tong["p"] < muc_bua["p"] * 0.7:
            dc.append(f"Bữa này thiếu khoảng {muc_bua['p'] - tong['p']:.0f} g đạm — thêm 1 lòng bàn tay thịt / cá / trứng.")
        if tong["kcal"] > muc_bua["kcal"] * 1.2:
            dc.append("Vượt năng lượng bữa — lần sau bớt ⅓ tinh bột hoặc bỏ phần chiên / sốt.")
    return {"mon": mon, "tong": tong, "do_tin_cay": "thap", "nhan_xet": nx, "dieu_chinh": dc, "bua_sau": ""}
