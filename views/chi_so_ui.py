"""v3.6 — 🧬 Chỉ số cơ thể & tuổi cơ thể (giống trang tư vấn Atlas, mang thương hiệu Hoàng Anh Coaching).

Lấy lần đo InBody gần nhất của khách → xếp loại BMI / % mỡ / mỡ nội tạng theo chuẩn nam–nữ, tính tuổi cơ thể ước tính và so với
lần đo đầu tiên. Tuổi cơ thể là ƯỚC TÍNH để theo dõi tiến bộ, không phải chẩn đoán y khoa.
"""
from __future__ import annotations

import html

import pandas as pd
import streamlit as st

from core import icons, store, tien_do as td, tu_van as tv, ui

E = html.escape
NM = tv.norms()
LV = NM["muc_mau"]
COT = ["can_nang", "pbf", "smm", "khoi_mo", "mo_noi_tang", "bmr", "diem_inbody", "nuoc", "protein", "khoang_chat", "tuoi_may", "tuoi",
       "v_eo", "v_hong"]
CSS = """<style>
.cs-g{display:grid;grid-template-columns:repeat(auto-fill,minmax(158px,1fr));gap:10px;margin:8px 0 14px}
.cs-t{border:1px solid rgba(163,128,60,.32);background:rgba(163,128,60,.07);border-radius:16px;padding:12px 14px;display:flex;gap:11px}
.cs-i{flex:0 0 38px;height:38px;border-radius:50%;background:rgba(200,162,74,.18);display:grid;place-items:center}
.cs-t small{display:block;font-size:.72rem;opacity:.7}.cs-t b{font-size:1.2rem;font-weight:800;line-height:1.25}
.cs-p{display:inline-block;color:#fff;border-radius:999px;padding:2px 9px;font-size:.66rem;font-weight:700;margin-top:3px}
.cs-d{font-size:.7rem;opacity:.75;margin-left:4px}
.cs-age{background:#141311;color:#F4EFE4;border:1px solid #A3803C;border-radius:18px;padding:18px 20px}
.cs-age .n{font-size:3rem;font-weight:800;line-height:1.05;color:#fff}
.cs-tb{width:100%;border-collapse:collapse;font-size:.85rem}.cs-tb td{padding:5px 8px;border-bottom:1px solid rgba(163,128,60,.18)}
</style>"""


def _f(v, unit="", nd=1):
    x = tv.num(v)
    if x is None:
        return "—"
    return (f"{x:.{nd}f}".rstrip("0").rstrip(".") if nd else f"{x:.0f}") + (f" {unit}" if unit else "")


def _tile(icon, label, value, res=None, sub="", delta=""):
    pill = (f'<span class="cs-p" style="background:{LV[str(res["diem"])]}">{E(res["nhan"])}</span>' if res else "")
    return (f'<div class="cs-t"><div class="cs-i">{icons.svg(icon, "#C8A24A", 21)}</div><div style="min-width:0">'
            f'<small>{E(label)}</small><b style="white-space:nowrap">{E(value)}</b>'
            + (f'<div class="cs-d" style="margin:0;color:#B8912F;font-weight:600">{E(delta)}</div>' if delta else "")
            + f'<div>{pill}<span class="cs-d">{E(sub)}</span></div></div></div>')


def _scale(levels, value, vmin, vmax):
    segs, hi = [], vmax
    for lv in levels:
        lo = max(lv["tu"], vmin)
        if hi > lo:
            segs.append((lo, hi, lv["diem"], lv["nhan"]))
        hi = lo
    segs.sort()
    bars = "".join(f'<div title="{E(n)}" style="flex:{b - a};background:{LV[str(d)]};height:10px"></div>' for a, b, d, n in segs)
    labs = "".join(f'<div style="flex:{b - a};font-size:.6rem;opacity:.7;text-align:center;overflow:hidden;white-space:nowrap">{E(n)}</div>'
                   for a, b, d, n in segs)
    mark = ""
    if value is not None:
        pos = (min(max(value, vmin), vmax) - vmin) / (vmax - vmin) * 100
        mark = f'<div style="position:absolute;left:calc({pos}% - 6px);top:-15px;font-size:.8rem">▼</div>'
    st.markdown(f'<div style="position:relative;margin:18px 0 4px"><div style="display:flex;border-radius:6px;overflow:hidden">{bars}</div>'
                f'{mark}</div><div style="display:flex">{labs}</div>', unsafe_allow_html=True)


def ho_so_do(k: dict, row: dict | None) -> dict:
    """Hồ sơ phẳng cho tv.evaluate từ khách + 1 lần đo."""
    h = {"gioi_tinh": k.get("gioi_tinh") or "Nam", "chieu_cao": k.get("chieu_cao")}
    for c in COT:
        v = (row or {}).get(c)
        if v is not None and not (isinstance(v, float) and pd.isna(v)):
            h[c] = v
    h["tuoi"] = store.tuoi(k) or h.get("tuoi")
    if not h.get("tuoi"):                     # chưa có ngày sinh → dùng tuổi in trên phiếu InBody (nếu có)
        h["tuoi"] = tv.num((row or {}).get("tuoi"))
    return h


def _cac_lan(k: dict) -> list[dict]:
    SD = td.so_do(k["ma"], them=True)
    if SD.empty:
        return []
    SD = SD.sort_values("ngay")
    out = []
    for _, r in SD.iterrows():
        d = {c: r[c] for c in SD.columns if c in COT and pd.notna(r[c])}
        if any(d.get(c) is not None for c in ("pbf", "smm", "mo_noi_tang", "khoi_mo")):
            out.append({**d, "ngay": r["ngay"]})
    return out


def hien(k: dict, vai: str = "hlv"):
    """Bảng chỉ số cơ thể + tuổi cơ thể (lần InBody gần nhất), so với lần đầu."""
    st.markdown(CSS, unsafe_allow_html=True)
    L = _cac_lan(k)
    if not L:
        st.info("Chưa có lần đo InBody nào (% mỡ, cơ, mỡ nội tạng). Quét phiếu InBody hoặc nhập số đo để xem chỉ số và tuổi cơ thể.")
        return
    dau, moi = L[0], L[-1]
    h, h0 = ho_so_do(k, moi), ho_so_do(k, dau)
    ev, ev0 = tv.evaluate(h), tv.evaluate(h0)
    ba, ba0 = ev.get("tuoi_co_the"), ev0.get("tuoi_co_the")
    co_dau = len(L) > 1

    def dl(c, unit="", nd=1):
        a, b = tv.num(dau.get(c)), tv.num(moi.get(c))
        if not co_dau or a is None or b is None or round(b - a, nd) == 0:
            return ""
        return f"{b - a:+.{nd}f}".rstrip("0").rstrip(".") + (f" {unit}" if unit else "") + " từ lần đầu"

    st.caption(f"Lần đo gần nhất **{pd.to_datetime(moi['ngay']):%d/%m/%Y}**"
               + (f" · so với lần đầu {pd.to_datetime(dau['ngay']):%d/%m/%Y}" if co_dau else ""))
    smm_pct = (f"{tv.num(h['smm']) / tv.num(h['can_nang']) * 100:.0f}% cân nặng" if tv.num(h.get("smm")) and tv.num(h.get("can_nang")) else "")
    T = [
        _tile("can_nang", "Cân nặng", _f(h.get("can_nang"), "kg"), sub=f"Cao {_f(h.get('chieu_cao'), 'cm')}", delta=dl("can_nang", "kg")),
        _tile("co", "Khối cơ xương", _f(h.get("smm"), "kg"), sub=smm_pct, delta=dl("smm", "kg")),
        _tile("khoi_mo", "Khối mỡ", _f(h.get("khoi_mo"), "kg"), delta=dl("khoi_mo", "kg")),
        _tile("pbf", "Tỉ lệ mỡ", _f(h.get("pbf"), "%"), ev.get("pbf"), delta=dl("pbf", "%")),
        _tile("noi_tang", "Mỡ nội tạng", _f(h.get("mo_noi_tang"), nd=0), ev.get("mo_noi_tang"), delta=dl("mo_noi_tang", nd=0)),
        _tile("bmi", "BMI", _f(ev["bmi"]["gia_tri"]) if ev.get("bmi") else "—", ev.get("bmi")),
        _tile("bmr", "Trao đổi chất cơ bản", _f(h.get("bmr"), "kcal", 0), sub="năng lượng lúc nghỉ / ngày"),
        _tile("nuoc", "Nước cơ thể", _f(h.get("nuoc"), "lít")),
        _tile("diem", "Điểm InBody", _f(h.get("diem_inbody"), nd=0), sub="trên 100", delta=dl("diem_inbody", nd=0)),
        _tile("tuoi", "Tuổi cơ thể", f"{ba['gia_tri']} tuổi" if ba else "—",
              {"diem": ba["diem"], "nhan": f"{ba['chenh']:+d} so với tuổi thật" if ba["chenh"] else "Bằng tuổi thật"} if ba else None,
              delta=(f"{ba['gia_tri'] - ba0['gia_tri']:+d} từ lần đầu" if ba and ba0 and co_dau and ba["gia_tri"] != ba0["gia_tri"] else "")),
    ]
    st.markdown(f'<div class="cs-g">{"".join(T)}</div>', unsafe_allow_html=True)
    sk = tv.sex_key(h.get("gioi_tinh"))
    c1, c2, c3 = st.columns(3, gap="large")
    with c1:
        st.markdown("**BMI** · chuẩn WHO châu Á")
        r_ = ev.get("bmi")
        _scale(NM["bmi"], r_["gia_tri"] if r_ else None, 15, 35)
        if not r_:
            st.caption("Cần chiều cao trong hồ sơ khách.")
    with c2:
        st.markdown(f"**% mỡ** · chuẩn ACE ({'nam' if sk == 'nam' else 'nữ'})")
        r_ = ev.get("pbf")
        _scale(NM["pbf"][sk], r_["gia_tri"] if r_ else None, 0 if sk == "nam" else 8, 45)
    with c3:
        st.markdown("**Mỡ nội tạng** · InBody: 1–9 bình thường")
        r_ = ev.get("mo_noi_tang")
        _scale(NM["mo_noi_tang"], r_["gia_tri"] if r_ else None, 1, 20)
    ui.sec("Tuổi cơ thể")
    if not ba:
        st.caption("Cần **ngày sinh** trong hồ sơ khách (hoặc tuổi in trên phiếu InBody) và ít nhất % mỡ, mỡ nội tạng hoặc khối cơ.")
        return
    col = LV[str(ba["diem"])]
    x, y = st.columns([1, 2], gap="large")
    x.markdown(
        f'<div class="cs-age"><div style="display:flex;gap:10px;align-items:center">{icons.svg("tuoi", "#E2C88A", 24)}'
        f'<span style="letter-spacing:.12em;font-size:.72rem;color:#E2C88A;font-weight:700">TUỔI CƠ THỂ</span></div>'
        f'<div class="n">{ba["gia_tri"]}</div><div>Tuổi thật {ba["tuoi"]} · <b style="color:{col}">{ba["chenh"]:+d} năm</b></div>'
        + (f'<div style="font-size:.8rem;opacity:.8;margin-top:4px">Lần đầu: {ba0["gia_tri"]} tuổi → nay {ba["gia_tri"]} tuổi</div>'
           if ba0 and co_dau else "")
        + (f'<div style="font-size:.8rem;opacity:.8;margin-top:2px">Máy InBody in: {ba["tuoi_may"]} tuổi</div>' if ba["tuoi_may"] else "")
        + "</div>", unsafe_allow_html=True)
    rows = "".join(f'<tr><td style="font-weight:600">{E(p["ten"])}</td><td style="opacity:.75">{E(p["giai_thich"])}</td>'
                   f'<td style="text-align:right;font-weight:800;color:{"#E0604D" if p["delta"] > 0 else "#3DAA6B"}">{p["delta"]:+.1f}</td></tr>'
                   for p in ba["chi_tiet"])
    y.markdown(f'<table class="cs-tb"><tr style="font-size:.7rem;opacity:.65"><td>THÀNH PHẦN</td><td>SO VỚI CHUẨN</td>'
               f'<td style="text-align:right">± NĂM</td></tr>{rows}</table>', unsafe_allow_html=True)
    y.caption("Tuổi cơ thể = tuổi thật ± chênh lệch % mỡ, mỡ nội tạng, khối cơ (và thể lực nếu có bài test) so với mức chuẩn cùng giới. "
              "Đây là **ước tính** để theo dõi tiến bộ, không phải chẩn đoán y khoa.")
    if vai == "hlv" and len(L) > 1:
        with st.expander("📈 Tuổi cơ thể qua các lần đo"):
            ds = []
            for r in L:
                b_ = tv.evaluate(ho_so_do(k, r)).get("tuoi_co_the")
                if b_:
                    ds.append({"Ngày": pd.to_datetime(r["ngay"]).date(), "Tuổi cơ thể": b_["gia_tri"], "% mỡ": r.get("pbf"),
                               "Cơ (kg)": r.get("smm"), "Mỡ nội tạng": r.get("mo_noi_tang")})
            if ds:
                st.dataframe(pd.DataFrame(ds), hide_index=True, use_container_width=True,
                             column_config={"Ngày": st.column_config.DateColumn(format="DD/MM/YYYY")})
