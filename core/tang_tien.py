"""v3.9 — TĂNG TIẾN THEO BIẾN SỐ: đọc các buổi cũ của từng bài → gợi ý hôm nay tăng tạ / tăng lần / đổi biến số (hiệp, tempo,
nghỉ) / giảm tạ, kèm điều cần chú ý; soạn tin nhắc khách trước buổi.

Nguyên tắc (double progression — cách tăng tiến phổ biến trong huấn luyện sức mạnh):
  • Chưa đạt số lần trên của khoảng mục tiêu ở mọi hiệp → GIỮ tạ, cố thêm 1 lần mỗi hiệp.
  • Đạt đủ số lần trên ở mọi hiệp → TĂNG tạ 1 bậc (2,5 kg; tạ đơn 1 kg; chân ≥ 40 kg: 5 kg), quay về số lần dưới.
  • Đứng yên 3 buổi liên tiếp (cùng mức tạ, tổng số lần không tăng) → ĐỔI BIẾN SỐ: thêm 1 hiệp, hoặc hạ chậm 3 giây, hoặc giảm
    10% rồi xây lại.
  • Nghỉ bài đó ≥ 14 ngày → bắt đầu lại nhẹ hơn ~10%.
  • Buổi trước ghi đau / khó chịu ở bài → không tăng, ưu tiên kỹ thuật, hỏi lại khách.
Đây là gợi ý mặc định; HLV điều chỉnh theo thể trạng thực tế trong buổi.
"""
from __future__ import annotations

import re
from datetime import date

from core import buoi as bt, db, ga_atlas as ga, tu_van as tv

DAU = ("đau", "nhói", "khó chịu", "chấn thương", "căng cứng", "tê")
ICON = {"moi": "🆕", "tang_ta": "⬆️", "tang_lan": "➕", "doi_bien": "🔁", "giam": "↘️", "chu_y": "⚠️", "giay": "⏱", "kho_hon": "🧗",
        "giu": "✋"}


def _khoang(lieu: str) -> tuple[int | None, int | None, int]:
    """'3×10–12' → (10, 12, 3); '2–3×8–10' → (8, 10, 3); '3×30–45 giây' → (30, 45, 3)."""
    s = str(lieu or "")
    try:
        hiep = int(s.split("×")[0].split("–")[-1].strip())
    except ValueError:
        hiep = 3
    so = [int(x) for x in re.findall(r"\d+", s.split("×", 1)[1])] if "×" in s else []
    if not so:
        return None, None, hiep
    return so[0], (so[1] if len(so) > 1 else so[0]), hiep


def lich_su(hist: list[dict], eid: str, ten: str = "", n: int = 4) -> list[dict]:
    """n lần gần nhất của bài (mới → cũ): ngay, hiep [{kg, lan}], ghi_chu, rpe (cả buổi), cam_nhan, ghi_chu_buoi."""
    out = []
    for s in reversed(hist or []):
        for b in s.get("bai", []):
            if (b.get("id") == eid or (ten and b.get("ten") == ten)) and b.get("hiep"):
                hs = [{"kg": tv.num(h.get("kg"), 0) or 0, "lan": int(tv.num(h.get("lan"), 0) or 0)} for h in b["hiep"]
                      if tv.num(h.get("lan"))]
                if hs:
                    out.append({"ngay": s["ngay"], "hiep": hs, "ghi_chu": b.get("ghi_chu", ""), "rpe": tv.num(s.get("rpe")),
                                "cam_nhan": s.get("cam_nhan", ""), "ghi_chu_buoi": s.get("ghi_chu", "")})
                break
        if len(out) >= n:
            break
    return out


def mo_ta(x: dict, giay_: bool = False) -> str:
    """'12/11 40 kg × 10/10/8' — 1 lần tập."""
    hs = x["hiep"]
    kgs = sorted({h["kg"] for h in hs})
    lan = "/".join(str(h["lan"]) for h in hs)
    if giay_:
        return f"{x['ngay']:%d/%m} {lan} giây"
    if not any(kgs):
        return f"{x['ngay']:%d/%m} {lan} lần"
    if len(kgs) == 1:
        return f"{x['ngay']:%d/%m} {kgs[0]:g} kg × {lan}"
    return f"{x['ngay']:%d/%m} " + " · ".join(f"{h['kg']:g}×{h['lan']}" for h in hs)


def _tron(kg: float, buoc: float) -> float:
    return max(round(round(kg / buoc) * buoc, 2), 0)


def phan_tich(item: dict, lieu: str, ls: list[dict], hom: date | None = None) -> dict:
    """Gợi ý hôm nay cho 1 bài. ls = lich_su(...) (mới → cũ).
    → {muc, icon, ngan, kg (đề xuất hoặc None), lan (mục tiêu từng hiệp), chu_y: [..]}"""
    hom = hom or db.now_vn().date()
    bot, top, n_set = _khoang(lieu)
    giay = "giây" in str(lieu)
    buoc = bt._step(item)
    if not ls:
        return {"muc": "moi", "icon": ICON["moi"], "kg": None, "lan": [],
                "ngan": "Buổi đầu với bài này: chọn mức tạ làm đủ số lần mà vẫn còn dư 2–3 lần.", "chu_y": []}
    x = ls[0]
    hs = x["hiep"]
    kg = max(h["kg"] for h in hs)
    lans = [h["lan"] for h in hs if h["kg"] == kg] or [h["lan"] for h in hs]
    cach = (hom - x["ngay"]).days if isinstance(x["ngay"], date) else 0
    chu_y = []
    ghi = " ".join(str(v or "") for v in (x.get("ghi_chu"), x.get("ghi_chu_buoi"))).lower()
    dau = any(w in ghi for w in DAU)
    if dau:
        chu_y.append(f"Buổi {x['ngay']:%d/%m} có ghi: “{(x.get('ghi_chu') or x.get('ghi_chu_buoi'))[:80]}” → hỏi lại khách trước khi tập.")
    if x.get("rpe") and x["rpe"] >= 9:
        chu_y.append(f"Buổi trước khách chấm độ nặng RPE {x['rpe']:g}/10 → khởi động kỹ, theo dõi kỹ thuật ở hiệp cuối.")
    if x.get("cam_nhan") in ("Rất mệt", "Mệt"):
        chu_y.append(f"Buổi trước khách thấy “{x['cam_nhan']}” → hỏi giấc ngủ, ăn uống trước buổi.")
    # ---- bài tính giây
    if giay:
        tb = round(sum(h["lan"] for h in hs) / len(hs))
        if top and min(h["lan"] for h in hs) >= top:
            return {"muc": "kho_hon", "icon": ICON["kho_hon"], "kg": None, "lan": [top] * n_set, "chu_y": chu_y,
                    "ngan": f"Lần trước giữ đủ {top} giây mọi hiệp → hôm nay đổi biến thể khó hơn hoặc thêm tạ nhẹ, giữ {bot or top} giây."}
        mt = [min(h["lan"] + 5, top or h["lan"] + 5) for h in hs]
        return {"muc": "giay", "icon": ICON["giay"], "kg": None, "lan": mt, "chu_y": chu_y,
                "ngan": f"Lần trước {'/'.join(str(h['lan']) for h in hs)} giây (TB {tb}) → hôm nay cố {'/'.join(map(str, mt))} giây."}
    # ---- nghỉ lâu
    if cach >= 14 and kg:
        moi = _tron(kg * 0.9, buoc)
        return {"muc": "giam", "icon": ICON["giam"], "kg": moi, "lan": [bot or min(lans)] * n_set, "chu_y": chu_y,
                "ngan": f"Đã {cach} ngày chưa tập bài này (lần cuối {kg:g} kg) → bắt đầu lại {moi:g} kg (≈ −10%), lấy lại cảm giác."}
    # ---- đau
    if dau:
        return {"muc": "chu_y", "icon": ICON["chu_y"], "kg": kg or None, "lan": lans, "chu_y": chu_y,
                "ngan": f"Giữ {kg:g} kg × {'/'.join(map(str, lans))}, không tăng — ưu tiên kỹ thuật; còn đau thì giảm tạ hoặc đổi bài."
                if kg else "Không tăng — ưu tiên kỹ thuật; còn đau thì đổi bài."}
    # ---- tạ cơ thể
    if not kg:
        if top and min(lans) >= top:
            return {"muc": "kho_hon", "icon": ICON["kho_hon"], "kg": None, "lan": [bot or top] * n_set, "chu_y": chu_y,
                    "ngan": f"Đạt đủ {top} lần mọi hiệp → tăng độ khó: đeo tạ nhẹ, hạ chậm 3 giây hoặc đổi biến thể khó hơn."}
        mt = [min(v + 1, top) if top else v + 1 for v in lans]
        return {"muc": "tang_lan", "icon": ICON["tang_lan"], "kg": None, "lan": mt, "chu_y": chu_y,
                "ngan": f"Lần trước {'/'.join(map(str, lans))} lần → hôm nay cố {'/'.join(map(str, mt))} (mỗi hiệp +1)."}
    # ---- đứng yên / đi lùi (so các lần cùng mức tạ)
    cung = [y for y in ls if max(h["kg"] for h in y["hiep"]) == kg]
    tong = [sum(h["lan"] for h in y["hiep"] if h["kg"] == kg) for y in cung]
    if len(tong) >= 2 and tong[0] <= tong[1] - 3:
        chu_y.append(f"Số lần ở {kg:g} kg giảm so với buổi trước nữa ({tong[1]} → {tong[0]} lần) → hỏi ngủ / ăn / mệt; giữ tạ, chưa tăng.")
    if top and min(lans) >= top:
        nho = bool(x.get("rpe") and x["rpe"] >= 9)
        moi = kg + (buoc / 2 if nho and buoc >= 2.5 else buoc)
        return {"muc": "tang_ta", "icon": ICON["tang_ta"], "kg": moi, "lan": [bot or top] * n_set, "chu_y": chu_y,
                "ngan": f"Lần trước {kg:g} kg đạt đủ {top} lần mọi hiệp → hôm nay **{moi:g} kg**, làm {bot or top} lần/hiệp rồi tăng dần."
                + (" (tăng nhỏ vì buổi trước rất nặng)" if nho else "")}
    if len(tong) >= 3 and tong[0] <= tong[2] and len(cung) >= 3:
        them = n_set < 5
        return {"muc": "doi_bien", "icon": ICON["doi_bien"], "kg": kg, "lan": lans, "chu_y": chu_y,
                "ngan": f"Đứng ở {kg:g} kg × ~{round(tong[0] / max(len(lans), 1))} lần đã 3 buổi → đổi biến số: "
                + ("**thêm 1 hiệp**, hoặc " if them else "") + "**hạ chậm 3 giây** mỗi lần, hoặc giảm 10% "
                f"({_tron(kg * 0.9, buoc):g} kg) rồi xây lại."}
    mt = [min(v + 1, top) if top else v + 1 for v in lans]
    return {"muc": "tang_lan", "icon": ICON["tang_lan"], "kg": kg, "lan": mt, "chu_y": chu_y,
            "ngan": f"Giữ **{kg:g} kg**, cố **{'/'.join(map(str, mt))}** lần (lần trước {'/'.join(map(str, lans))}"
            + (f"; đủ {top} lần mọi hiệp thì buổi sau tăng tạ)" if top else ")")}


def ke_hoach(k: dict, ngay: date | None = None, buoi_ma: str | None = None, P: dict | None = None,
             hist: list[dict] | None = None) -> dict | None:
    """Kế hoạch tăng tiến cho 1 buổi theo giáo án (mặc định: buổi kế tiếp trong chu kỳ)."""
    P = ga.current(k["ma"]) if P is None else P
    if not P or not P.get("buoi"):
        return None
    hist = bt.sessions(k["ma"]) if hist is None else hist
    ngay = ngay or db.now_vn().date()
    bu = next((b for b in P["buoi"] if b["ma"] == buoi_ma), None) or ga.buoi_tiep(P, hist)
    wk = ga.week_no(P["ngay_bat_dau"], ngay)
    bai = []
    for it in bu.get("bai", []):
        r = ga.rx(it, P["muc_tieu"], wk, P["trinh_do"])
        ls = lich_su(hist, it["id"], it.get("ten", ""))
        bai.append({"id": it["id"], "ten": it.get("ten", ""), "lieu": r["lieu"], "ls": ls,
                    "pt": phan_tich(it, r["lieu"], ls, ngay), "giay": "giây" in r["lieu"]})
    chung = []
    if hist:
        cuoi = hist[-1]
        cach = (ngay - cuoi["ngay"]).days
        if cach >= 10:
            chu = f"Khách đã {cach} ngày chưa tập (buổi cuối {cuoi['ngay']:%d/%m}) → khởi động lâu hơn, tạ giảm nhẹ ở bài chính."
            chung.append(chu)
        if cuoi.get("ghi_chu"):
            chung.append(f"Lời khách gửi buổi {cuoi['ngay']:%d/%m}: “{str(cuoi['ghi_chu'])[:120]}”")
    so = {m: sum(1 for b in bai if b["pt"]["muc"] == m) for m in ICON}
    return {"buoi": bu, "tuan": wk, "phase": ga.PHASES[ga.phase_of(wk)], "bai": bai, "chung": chung, "dem": so}


def tin_zalo(k: dict, kh: dict, ngay: date | None = None, xung: str = "") -> str:
    """Tin nhắc khách trước buổi: hôm nay tập gì, mỗi bài tăng gì, chú ý gì."""
    ngay = ngay or db.now_vn().date()
    if not xung:
        from core import store
        xung = store.xung(k)[0]
    ten = xung or "bạn"
    dong = [f"Chào {ten}! Buổi {kh['buoi']['ma']} · {kh['buoi']['ten']} ({ngay:%d/%m}) mình sẽ tăng tiến như sau:"]
    for b in kh["bai"]:
        p = b["pt"]
        if p["muc"] == "moi":
            continue
        dong.append(f"{p['icon']} {b['ten']}: " + p["ngan"].replace("**", ""))
    chu = [c for b in kh["bai"] for c in b["pt"]["chu_y"] if "hỏi lại khách" in c or "RPE" in c][:2]
    if chu or kh["chung"]:
        dong.append("Lưu ý: ngủ đủ, ăn nhẹ trước tập 1–2 tiếng; chỗ nào còn đau nhắn mình trước nhé.")
    dong.append("Hẹn gặp ở buổi tập 💪")
    return "\n".join(dong)
