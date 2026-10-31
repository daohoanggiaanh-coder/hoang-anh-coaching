# Hoàng Anh Coaching v1.0 (2026-10-31) — tiến độ: cân hằng ngày (TB 7 ngày), số đo theo đợt, ảnh 3 góc,
# báo cáo kết quả đầu khoá + tiến độ (tin Zalo + PDF). Chuyển từ Atlas Academy v3.71 (core/tien_do_rieng.py).
"""Bảng: SoDo (khoá "<mã>|<ngày>|<đợt>") · CanNang ("<mã>|<ngày>") · Anh ("<mã>|<ngày>|<góc>"). Module không import streamlit."""
from __future__ import annotations

from datetime import date

import pandas as pd

from core import db

DOT = {"dau_khoa": "Đầu khoá", "tuan": "Hằng tuần", "cuoi_khoa": "Cuối khoá", "khac": "Khác"}
GOC = {"truoc": "Trước", "nghieng": "Nghiêng", "sau": "Sau"}
CHI_SO = [("can_nang", "Cân nặng", "kg", -1), ("pbf", "% mỡ", "%", -1), ("smm", "Khối cơ", "kg", 1),
          ("khoi_mo", "Khối mỡ", "kg", -1), ("mo_noi_tang", "Mỡ nội tạng", "", -1),
          ("v_nguc", "Vòng ngực", "cm", 0), ("v_eo", "Vòng eo", "cm", -1), ("v_bung", "Vòng bụng", "cm", -1),
          ("v_hong", "Vòng mông", "cm", 0), ("v_dui", "Vòng đùi", "cm", 0), ("v_tay", "Vòng bắp tay", "cm", 0)]
TEN = {k: (t, dv, h) for k, t, dv, h in CHI_SO}


def _so(v) -> float | None:
    try:
        x = float(str(v).replace(",", ".").strip())
    except (TypeError, ValueError):
        return None
    return None if x != x or x <= 0 else x


def _d(v) -> date | None:
    t = pd.to_datetime(str(v or "")[:10], errors="coerce")
    return None if pd.isna(t) else t.date()


BANG = {"rieng_sodo": "SoDo", "rieng_can": "CanNang", "rieng_anh": "Anh"}


def _rows(loai: str, ma: str, df=None) -> list[dict]:
    return [v for v in db.latest(BANG[loai], ma).values() if _d(v.get("ngay"))]


def _log(loai: str, key: str, data: dict, user: dict) -> bool:
    return db.append(BANG[loai], key, data, user.get("name", ""), data.get("ma", ""))


# ------------------------------------------------------------------ đọc
def so_do(ma: str, df=None) -> pd.DataFrame:
    rows = []
    for v in _rows("rieng_sodo", ma, df):
        r = {"ngay": _d(v["ngay"]), "dot": v.get("dot") or "khac", "ghi_chu": v.get("ghi_chu", "")}
        r.update({k: _so(v.get(k)) for k, *_ in CHI_SO})
        rows.append(r)
    cols = ["ngay", "dot", "ghi_chu"] + [k for k, *_ in CHI_SO]
    return pd.DataFrame(rows, columns=cols).sort_values("ngay").reset_index(drop=True) if rows else pd.DataFrame(columns=cols)


def can_ngay(ma: str, df=None) -> pd.DataFrame:
    """Cân hằng ngày + trung bình 7 ngày (theo ngày lịch, bỏ qua ngày trống)."""
    rows = [{"ngay": _d(v["ngay"]), "kg": _so(v.get("kg"))} for v in _rows("rieng_can", ma, df)]
    rows = [r for r in rows if r["kg"]]
    if not rows:
        return pd.DataFrame(columns=["ngay", "kg", "tb7"])
    d = pd.DataFrame(rows).sort_values("ngay").reset_index(drop=True)
    s = pd.Series(d["kg"].values, index=pd.to_datetime(d["ngay"]))
    d["tb7"] = s.rolling("7D").mean().round(2).values
    return d


def anh(ma: str, df=None) -> list[dict]:
    return sorted(_rows("rieng_anh", ma, df), key=lambda v: (str(v["ngay"]), list(GOC).index(v.get("goc", "truoc"))
                                                             if v.get("goc") in GOC else 9))


def bo_anh(ds: list[dict], dau: bool = True) -> dict[str, dict]:
    """{góc: ảnh} của đợt đầu tiên (dau=True) hoặc mới nhất — mỗi góc lấy ảnh sớm / muộn nhất."""
    out: dict[str, dict] = {}
    for v in (ds if dau else reversed(ds)):
        out.setdefault(v.get("goc", "truoc"), v)
    return out


def dau_khoa(sd: pd.DataFrame) -> dict | None:
    """Lần đo đầu khoá (đợt 'dau_khoa' sớm nhất; chưa đánh dấu thì lần đo đầu tiên)."""
    if sd.empty:
        return None
    dk = sd[sd["dot"] == "dau_khoa"]
    return (dk.iloc[0] if len(dk) else sd.iloc[0]).to_dict()


def moi_nhat(sd: pd.DataFrame, can: pd.DataFrame | None = None) -> dict | None:
    """Số đo mới nhất; cân nặng lấy bản mới hơn giữa lần đo và cân hằng ngày."""
    if sd.empty and (can is None or can.empty):
        return None
    m = sd.iloc[-1].to_dict() if not sd.empty else {"ngay": None}
    if can is not None and not can.empty:
        c = can.iloc[-1]
        if m.get("ngay") is None or c["ngay"] >= m["ngay"] or not m.get("can_nang"):
            m = {**m, "can_nang": float(c["kg"]), "_ngay_can": c["ngay"]}
    return m


def so_sanh(dau: dict | None, moi: dict | None) -> list[dict]:
    """[{k, ten, dv, dau, moi, chenh, tot}] — tot True / False / None (không xét tốt xấu)."""
    if not dau or not moi:
        return []
    out = []
    for k, t, dv, h in CHI_SO:
        a, b = _so(dau.get(k)), _so(moi.get(k))
        if a is None or b is None:
            continue
        ch = round(b - a, 1)
        out.append({"k": k, "ten": t, "dv": dv, "dau": a, "moi": b, "chenh": ch,
                    "tot": None if h == 0 or ch == 0 else (ch * h > 0)})
    return out


# ------------------------------------------------------------------ ghi
def luu_so_do(ma: str, ngay: date, dot: str, vals: dict, ghi_chu: str, user: dict) -> bool:
    data = {"ma": ma, "ngay": ngay.isoformat(), "dot": dot, "ghi_chu": ghi_chu,
            **{k: vals.get(k) for k, *_ in CHI_SO if _so(vals.get(k))}}
    return _log("rieng_sodo", f"{ma}|{ngay.isoformat()}|{dot}", data, user)


def xoa_so_do(ma: str, ngay: date, dot: str, user: dict) -> bool:
    return _log("rieng_sodo", f"{ma}|{ngay.isoformat()}|{dot}", {"ma": ma, "ngay": ngay.isoformat(), "dot": dot, "xoa": "1"}, user)


def luu_can(ma: str, ngay: date, kg: float, user: dict) -> bool:
    return _log("rieng_can", f"{ma}|{ngay.isoformat()}", {"ma": ma, "ngay": ngay.isoformat(), "kg": round(float(kg), 2)}, user)


def xoa_can(ma: str, ngay: date, user: dict) -> bool:
    return _log("rieng_can", f"{ma}|{ngay.isoformat()}", {"ma": ma, "ngay": ngay.isoformat(), "xoa": "1"}, user)


def luu_anh(ma: str, ngay: date, dot: str, goc: str, anh_id: str, user: dict) -> bool:
    return _log("rieng_anh", f"{ma}|{ngay.isoformat()}|{goc}",
                {"ma": ma, "ngay": ngay.isoformat(), "dot": dot, "goc": goc, "id": anh_id}, user)


# ------------------------------------------------------------------ đánh giá
def bmi(kg, cao_cm) -> float | None:
    kg, h = _so(kg), _so(cao_cm)
    return round(kg / (h / 100) ** 2, 1) if kg and h and h > 100 else None


def muc_bmi(b: float | None) -> str:
    """Chuẩn WHO cho người châu Á."""
    if b is None:
        return ""
    return ("Thiếu cân" if b < 18.5 else "Bình thường" if b < 23 else "Thừa cân" if b < 25 else
            "Béo phì độ I" if b < 30 else "Béo phì độ II")


def muc_mo(pbf, gioi_tinh: str) -> str:
    p = _so(pbf)
    if p is None:
        return ""
    nu = str(gioi_tinh or "").strip().lower() in ("nữ", "nu", "female")
    nguong = (14, 21, 25, 32) if nu else (6, 14, 18, 25)
    return ("Rất thấp" if p < nguong[0] else "Vận động viên" if p < nguong[1] else "Săn chắc" if p < nguong[2]
            else "Trung bình" if p < nguong[3] else "Cao — cần giảm")


def tien_do_can(dau_kg, moi_kg, muc_tieu_kg) -> int | None:
    a, b, t = _so(dau_kg), _so(moi_kg), _so(muc_tieu_kg)
    if not (a and b and t) or a == t:
        return None
    return max(0, min(100, round((a - b) / (a - t) * 100)))


def nhan_xet_dau_khoa(k: dict, dau: dict) -> list[str]:
    out = []
    b = bmi(dau.get("can_nang"), k.get("chieu_cao"))
    if b:
        out.append(f"BMI {b:g} — {muc_bmi(b).lower()} (chuẩn người châu Á).")
    if _so(dau.get("pbf")):
        out.append(f"Tỉ lệ mỡ {dau['pbf']:g}% — mức {muc_mo(dau['pbf'], k.get('gioi_tinh')).lower()}.")
    if _so(dau.get("mo_noi_tang")) and dau["mo_noi_tang"] >= 10:
        out.append(f"Mỡ nội tạng mức {dau['mo_noi_tang']:g} (≥ 10) — ưu tiên giảm mỡ bụng, cải thiện ăn uống, ngủ.")
    eo, hong = _so(dau.get("v_eo")), _so(dau.get("v_hong"))
    if eo and hong:
        whr = round(eo / hong, 2)
        nu = str(k.get("gioi_tinh") or "").strip().lower() in ("nữ", "nu")
        cao = whr >= (0.85 if nu else 0.90)
        out.append(f"Tỉ lệ eo / mông {whr:g} — {'cao hơn ngưỡng khuyến nghị, cần giảm vòng eo' if cao else 'trong ngưỡng tốt'}.")
    if _so(k.get("can_muc_tieu")) and _so(dau.get("can_nang")):
        ch = round(_so(dau["can_nang"]) - _so(k["can_muc_tieu"]), 1)
        if ch > 0:
            out.append(f"Mục tiêu {k['can_muc_tieu']} kg — cần giảm {ch:g} kg; tốc độ an toàn 0,3–0,7 kg/tuần "
                       f"(khoảng {max(1, round(ch / 0.7))}–{max(1, round(ch / 0.3))} tuần).")
        elif ch < 0:
            out.append(f"Mục tiêu {k['can_muc_tieu']} kg — cần tăng {-ch:g} kg, ưu tiên tăng cơ (0,2–0,5 kg/tuần).")
    return out


# ------------------------------------------------------------------ tin Zalo
def _xung(k: dict) -> tuple[str, str]:
    from core import store
    return store.xung(k)


def _gia_tri(v, dv) -> str:
    return f"{v:g} {dv}".strip()


def tin_dau_khoa(k: dict, dau: dict) -> str:
    goi, toi = _xung(k)
    G = goi[:1].upper() + goi[1:]
    dong = [f"{t}: {_gia_tri(dau[c], dv)}" for c, t, dv, _ in CHI_SO if _so(dau.get(c))]
    nx = nhan_xet_dau_khoa(k, dau)
    mt = f"\n🎯 Mục tiêu: {k['muc_tieu']}" if k.get("muc_tieu") else ""
    return (f"{G} ơi, {toi} gửi kết quả đánh giá đầu khoá ngày {pd.Timestamp(dau['ngay']):%d/%m/%Y} nha 💪\n\n"
            "📏 Chỉ số đầu khoá:\n" + "\n".join(f"• {x}" for x in dong)
            + ("\n\n📝 Nhận xét:\n" + "\n".join(f"• {x}" for x in nx) if nx else "") + mt
            + f"\n\nĐây là mốc xuất phát của {goi}. Mỗi tuần {toi} đo lại và gửi {goi} xem thay đổi nha. "
              f"{G} nhớ cân buổi sáng sau khi thức dậy, trước khi ăn và nhắn {toi} số cân mỗi ngày nhé.")


def tin_tien_do(k: dict, dau: dict, moi: dict, can: pd.DataFrame) -> str:
    goi, toi = _xung(k)
    G = goi[:1].upper() + goi[1:]
    ss = so_sanh(dau, moi)
    dong = [f"{'✅' if x['tot'] else '➖' if x['tot'] is None else '⚠️'} {x['ten']}: {x['dau']:g} → {x['moi']:g} {x['dv']} "
            f"({x['chenh']:+g})".replace("  ", " ") for x in ss]
    tuan = ""
    if not can.empty and len(can) >= 2:
        g = can[pd.to_datetime(can["ngay"]) >= pd.Timestamp(can["ngay"].iloc[-1]) - pd.Timedelta(days=6)]
        tuan = f"\n⚖️ Cân 7 ngày gần nhất: trung bình {g['kg'].mean():.1f} kg ({len(g)} lần cân)"
    pt = tien_do_can(dau.get("can_nang"), moi.get("can_nang"), k.get("can_muc_tieu"))
    pt_s = f"\n🎯 Đã đi được {pt}% chặng đường tới mục tiêu {k['can_muc_tieu']} kg" if pt is not None else ""
    so_tuan = max(1, round((pd.Timestamp(moi.get('_ngay_can') or moi['ngay']) - pd.Timestamp(dau['ngay'])).days / 7))
    return (f"{G} ơi, {toi} tổng kết sau {so_tuan} tuần tập nè 👇\n\n"
            + "\n".join(dong) + tuan + pt_s
            + f"\n\nTiến bộ đều là nhờ {goi} giữ nhịp tập và ăn uống đó. Tuần này mình cố thêm chút nữa nha 🔥")


# ------------------------------------------------------------------ PDF
def pdf(k: dict, kieu: str, sd: pd.DataFrame, can: pd.DataFrame, imgs: dict[str, bytes], anh_dau: dict, anh_moi: dict) -> bytes:
    """kieu = 'dau_khoa' (báo cáo kết quả đầu khoá) | 'tien_do' (đầu khoá → hiện tại). A4 dọc, đen – vàng đồng."""
    import io

    from reportlab.lib.colors import HexColor, white
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.utils import ImageReader, simpleSplit
    from reportlab.pdfgen import canvas

    from core import anh as A, config
    from core.pdfkit import BRONZE, INK, MUTE, RULE, SOFT, fonts as _fonts
    _fonts()
    W, H = A4
    M = 40
    DARK, GOLD, GREEN, RED = HexColor("#1C1B19"), HexColor("#C8A24A"), HexColor("#2E7D4F"), HexColor("#B4442F")
    dau = dau_khoa(sd) or {}
    moi = moi_nhat(sd, can) or {}
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    tieu_de = "BÁO CÁO KẾT QUẢ ĐẦU KHOÁ" if kieu == "dau_khoa" else "BÁO CÁO TIẾN ĐỘ"
    c.setTitle(f"{config.VERSION} · {tieu_de} · {k.get('ho_ten', '')}")

    def txt(x, y, s, f="R", sz=10, col=INK, al="l"):
        c.setFont(f, sz)
        c.setFillColor(col)
        {"l": c.drawString, "c": c.drawCentredString, "r": c.drawRightString}[al](x, y, str(s))

    def pic(data, x, y, w, h):
        try:
            c.drawImage(ImageReader(io.BytesIO(A.crop_ratio(data, w, h, 900))), x, y, w, h)
            return True
        except Exception:  # noqa: BLE001
            return False

    # ---- đầu trang
    c.setFillColor(DARK)
    c.rect(0, H - 150, W, 150, stroke=0, fill=1)
    txt(M, H - 46, config.BRAND, "B", 9, GOLD)
    txt(M, H - 80, tieu_de, "B", 21, white)
    txt(M, H - 106, str(k.get("ho_ten", "")), "S", 14, HexColor("#E6D3A1"))
    ngay_s = (f"Ngày đo {pd.Timestamp(dau['ngay']):%d/%m/%Y}" if kieu == "dau_khoa" and dau.get("ngay") else
              f"{pd.Timestamp(dau['ngay']):%d/%m/%Y} – {pd.Timestamp(moi.get('_ngay_can') or moi['ngay']):%d/%m/%Y}"
              if dau.get("ngay") and moi.get("ngay") else "")
    info = " · ".join(x for x in (ngay_s, f"Cao {k['chieu_cao']} cm" if k.get("chieu_cao") else "",
                                  k.get("gioi_tinh", ""), f"Mục tiêu {k['can_muc_tieu']} kg" if k.get("can_muc_tieu") else "") if x)
    txt(M, H - 128, info, "R", 9, HexColor("#BDB6A8"))
    y = H - 172

    # ---- ảnh
    goc = list(GOC)
    if kieu == "dau_khoa":
        co = [g for g in goc if anh_dau.get(g) and anh_dau[g]["id"] in imgs]
        if co:
            gw = (W - 2 * M - 2 * 12) / 3
            gh = gw * 4 / 3
            for i, g in enumerate(goc):
                x = M + i * (gw + 12)
                if anh_dau.get(g) and anh_dau[g]["id"] in imgs and pic(imgs[anh_dau[g]["id"]], x, y - gh, gw, gh):
                    c.setStrokeColor(GOLD)
                    c.rect(x, y - gh, gw, gh, stroke=1, fill=0)
                else:
                    c.setFillColor(SOFT)
                    c.rect(x, y - gh, gw, gh, stroke=0, fill=1)
                txt(x + gw / 2, y - gh - 13, GOC[g].upper(), "S", 8, BRONZE, "c")
            y -= gh + 30
    else:
        cap = [(g, anh_dau.get(g), anh_moi.get(g)) for g in goc
               if anh_dau.get(g) and anh_moi.get(g) and anh_dau[g]["id"] in imgs and anh_moi[g]["id"] in imgs
               and anh_dau[g]["id"] != anh_moi[g]["id"]]
        if cap:
            g, a_, b_ = cap[0]
            gw = (W - 2 * M - 16) / 2
            gh = min(gw * 4 / 3, 225)
            for i, (lab, v) in enumerate((("TRƯỚC · " + pd.Timestamp(a_["ngay"]).strftime("%d/%m"), a_),
                                          ("HIỆN TẠI · " + pd.Timestamp(b_["ngay"]).strftime("%d/%m"), b_))):
                x = M + i * (gw + 16)
                pic(imgs[v["id"]], x, y - gh, gw, gh)
                c.setStrokeColor(GOLD)
                c.rect(x, y - gh, gw, gh, stroke=1, fill=0)
                txt(x + gw / 2, y - gh - 13, lab, "S", 8, BRONZE, "c")
            y -= gh + 30

    # ---- bảng chỉ số
    txt(M, y, "CHỈ SỐ ĐẦU KHOÁ" if kieu == "dau_khoa" else "THAY ĐỔI TỪ ĐẦU KHOÁ ĐẾN HIỆN TẠI", "S", 9, BRONZE)
    c.setStrokeColor(RULE)
    c.line(M, y - 6, W - M, y - 6)
    y -= 22
    if kieu == "dau_khoa":
        ds = [(t, _gia_tri(dau[k_], dv)) for k_, t, dv, _ in CHI_SO if _so(dau.get(k_))]
        b = bmi(dau.get("can_nang"), k.get("chieu_cao"))
        if b:
            ds.insert(1, ("BMI", f"{b:g} · {muc_bmi(b)}"))
        cw = (W - 2 * M - 12) / 2
        for i, (t, v) in enumerate(ds):
            x = M + (i % 2) * (cw + 12)
            yy = y - (i // 2) * 24
            c.setFillColor(SOFT)
            c.roundRect(x, yy - 7, cw, 20, 4, stroke=0, fill=1)
            txt(x + 10, yy, t, "R", 9.5, MUTE)
            txt(x + cw - 10, yy, v, "B", 10, INK, "r")
        y -= ((len(ds) + 1) // 2) * 24 + 10
        nx = nhan_xet_dau_khoa(k, dau)
        if nx or k.get("muc_tieu"):
            txt(M, y, "NHẬN XÉT & MỤC TIÊU", "S", 9, BRONZE)
            c.line(M, y - 6, W - M, y - 6)
            y -= 22
            for s in nx + ([f"Mục tiêu của bạn: {k['muc_tieu']}"] if k.get("muc_tieu") else []):
                for j, ln in enumerate(simpleSplit(s, "R", 10, W - 2 * M - 14)):
                    if j == 0:
                        c.setFillColor(GOLD)
                        c.circle(M + 3, y + 3.5, 2.4, stroke=0, fill=1)
                    txt(M + 12, y, ln, "R", 10, INK)
                    y -= 14
                y -= 3
    else:
        ss = so_sanh(dau, moi)
        cols = [M, M + 190, M + 290, M + 390]
        for x, h_ in zip(cols, ("Chỉ số", "Đầu khoá", "Hiện tại", "Thay đổi")):
            txt(x, y, h_, "S", 8.5, MUTE)
        y -= 16
        for x in ss:
            c.setFillColor(SOFT)
            c.rect(M - 4, y - 6, W - 2 * M + 8, 19, stroke=0, fill=1)
            txt(cols[0], y, x["ten"], "R", 10)
            txt(cols[1], y, _gia_tri(x["dau"], x["dv"]), "R", 10)
            txt(cols[2], y, _gia_tri(x["moi"], x["dv"]), "B", 10)
            txt(cols[3], y, f"{x['chenh']:+g} {x['dv']}".strip(), "B", 10,
                GREEN if x["tot"] else RED if x["tot"] is False else MUTE)
            y -= 22
        pt = tien_do_can(dau.get("can_nang"), moi.get("can_nang"), k.get("can_muc_tieu"))
        if pt is not None:
            y -= 6
            txt(M, y, f"Tiến độ tới mục tiêu {k['can_muc_tieu']} kg", "S", 9, BRONZE)
            c.setFillColor(SOFT)
            c.roundRect(M, y - 18, W - 2 * M, 9, 4, stroke=0, fill=1)
            c.setFillColor(GOLD)
            c.roundRect(M, y - 18, max((W - 2 * M) * pt / 100, 9), 9, 4, stroke=0, fill=1)
            txt(W - M, y, f"{pt}%", "B", 10, INK, "r")
            y -= 34
        # ---- biểu đồ cân hằng ngày
        if not can.empty and len(can) >= 2 and y > 170:
            ch = min(150, y - 80)
            txt(M, y, "CÂN NẶNG HẰNG NGÀY · ĐƯỜNG VÀNG = TRUNG BÌNH 7 NGÀY", "S", 8.5, BRONZE)
            y -= 14
            x0, x1, y0, y1 = M + 28, W - M, y - ch, y
            vals = list(can["kg"]) + list(can["tb7"])
            lo, hi = min(vals) - 0.5, max(vals) + 0.5
            t0, t1 = pd.Timestamp(can["ngay"].iloc[0]), pd.Timestamp(can["ngay"].iloc[-1])
            span = max((t1 - t0).days, 1)
            X = lambda d_: x0 + (pd.Timestamp(d_) - t0).days / span * (x1 - x0)   # noqa: E731
            Y = lambda v: y0 + (v - lo) / (hi - lo) * (y1 - y0)                    # noqa: E731
            c.setStrokeColor(RULE)
            c.setLineWidth(.5)
            for i in range(5):
                v = lo + (hi - lo) * i / 4
                c.line(x0, Y(v), x1, Y(v))
                txt(x0 - 4, Y(v) - 3, f"{v:.1f}", "R", 7, MUTE, "r")
            for col, key, wdt in ((HexColor("#B9B2A3"), "kg", 1), (GOLD, "tb7", 2.2)):
                c.setStrokeColor(col)
                c.setLineWidth(wdt)
                p = c.beginPath()
                for i, r in enumerate(can.to_dict("records")):
                    (p.moveTo if i == 0 else p.lineTo)(X(r["ngay"]), Y(r[key]))
                c.drawPath(p, stroke=1, fill=0)
            txt(x0, y0 - 12, f"{t0:%d/%m}", "R", 7, MUTE)
            txt(x1, y0 - 12, f"{t1:%d/%m}", "R", 7, MUTE, "r")
            y = y0 - 26
    # ---- chân trang
    c.setStrokeColor(RULE)
    c.line(M, 44, W - M, 44)
    txt(M, 30, "Báo cáo riêng cho khách · số đo nên đo cùng giờ, cùng điều kiện để so sánh chính xác", "R", 7.5, MUTE)
    txt(W - M, 30, f"{config.BRAND} · {config.VERSION_LABEL}", "R", 7.5, MUTE, "r")
    c.showPage()
    c.save()
    return buf.getvalue()
