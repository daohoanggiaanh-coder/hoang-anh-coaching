"""v3.0 — 📊 Tiến độ tất cả khách: mỗi khách một thẻ biểu đồ (cân · % mỡ · khối cơ · vòng eo).
Dùng để theo dõi / chăm sóc và chụp màn hình khoe kết quả học viên.
Thứ tự mặc định: Gold Gym → Online → Atlas → phòng khác; HLV tự đổi thứ tự, ẩn khách, lưu lại cho lần sau."""
from __future__ import annotations

import html
import json
import pandas as pd
import streamlit as st
from plotly.subplots import make_subplots

from core import config, db, store, tien_do as td, ui

S = st.session_state
E = html.escape
KEY = "td_thu_tu"                          # DinhDuong: {ma: {"tt": số, "an": bool}}
UU_TIEN = ["Gold Gym", "Online", "Atlas"]  # anh Hoàng Anh muốn Gold Gym & Online lên trước


def _uu(k: dict) -> tuple:
    p = store.phong(k)
    return (UU_TIEN.index(p) if p in UU_TIEN else len(UU_TIEN) + (0 if p else 1), str(k.get("ho_ten", "")))


def thu_tu_luu() -> dict:
    v = db.latest("DinhDuong").get(KEY, {})
    v = v.get("v", v) if isinstance(v, dict) else {}
    if isinstance(v, str):
        try:
            v = json.loads(v)
        except ValueError:
            v = {}
    return {m: x for m, x in (v or {}).items() if isinstance(x, dict)}


def sap_xep(DS: list[dict], TT: dict) -> list[dict]:
    """Thứ tự đã lưu (số nhỏ lên trước); khách chưa xếp → theo phòng ưu tiên, đứng sau các khách đã xếp tay."""
    mac = {k["ma"]: (i + 1) * 10 for i, k in enumerate(sorted(DS, key=_uu))}
    return sorted(DS, key=lambda k: (float(TT.get(k["ma"], {}).get("tt") or mac[k["ma"]] + 10000), _uu(k)))


def ten_an(k: dict) -> str:
    """Chế độ đăng MXH: 'Học viên N.T.M. Duyên' — che họ, giữ tên."""
    w = str(k.get("ho_ten", "")).split()
    if len(w) < 2:
        return "Học viên " + (w[0] if w else "")
    return "Học viên " + "".join(x[0].upper() + "." for x in w[:-1]) + " " + w[-1].capitalize()


def du_lieu(k: dict) -> dict:
    sd, cn = td.so_do(k["ma"]), td.can_ngay(k["ma"])
    dau, moi = td.dau_khoa(sd, cn), td.moi_nhat(sd, cn)
    ss = {x["k"]: x for x in td.so_sanh(dau, moi)} if dau and moi else {}
    return {"sd": sd, "cn": cn, "dau": dau, "moi": moi, "ss": ss, "co": bool(len(sd) or len(cn))}


def _chip(x: dict | None, ten: str) -> str:
    if not x or not x["chenh"]:
        return ""
    tot = x["tot"]
    mau = "#2E7D4F" if tot else ("#B3412E" if tot is False else "#5B6770")
    so = f"{x['chenh']:+g}".replace("-", "−")
    return (f'<span class="tda-c" style="border-color:{mau};color:{mau}"><b>{so}{(" " + x["dv"]) if x["dv"] else ""}</b>'
            f'<small>{E(ten)}</small></span>')


def bieu_do(d: dict, h: int, key: str):
    sd, cn = d["sd"], d["cn"]
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    if len(cn) >= 2:
        fig.add_scatter(x=cn["ngay"], y=cn["tb7"], name="Cân (TB 7 ngày)", mode="lines", line=dict(color=ui.VANG, width=3.5),
                        hovertemplate="%{x|%d/%m}: %{y:.1f} kg<extra></extra>", secondary_y=False)
    elif len(sd) and sd["can_nang"].notna().any():
        c = sd[sd["can_nang"].notna()]
        fig.add_scatter(x=c["ngay"], y=c["can_nang"], name="Cân", mode="lines+markers+text", line=dict(color=ui.VANG, width=3.5),
                        text=[f"{v:g}" for v in c["can_nang"]], textposition="top center",
                        hovertemplate="%{x|%d/%m}: %{y:.1f} kg<extra></extra>", secondary_y=False)
    if len(sd) and sd["smm"].notna().any():
        c = sd[sd["smm"].notna()]
        fig.add_scatter(x=c["ngay"], y=c["smm"], name="Khối cơ (kg)", mode="lines+markers", line=dict(color="#2E7D4F", width=2.5),
                        hovertemplate="%{x|%d/%m}: cơ %{y:.1f} kg<extra></extra>", secondary_y=False)
    if len(sd) and sd["pbf"].notna().any():
        c = sd[sd["pbf"].notna()]
        fig.add_scatter(x=c["ngay"], y=c["pbf"], name="% mỡ", mode="lines+markers+text", line=dict(color="#B3412E", width=2.5, dash="dot"),
                        text=[f"{v:g}%" for v in c["pbf"]], textposition="bottom center", textfont=dict(color="#B3412E", size=11),
                        hovertemplate="%{x|%d/%m}: %{y:.1f}% mỡ<extra></extra>", secondary_y=True)
    ui.layout(fig, h)
    fig.update_layout(legend=dict(orientation="h", y=-0.18, font=dict(size=11)), margin=dict(l=4, r=4, t=22, b=4))
    fig.update_xaxes(tickformat="%d/%m")
    fig.update_yaxes(title_text="kg", secondary_y=False)
    fig.update_yaxes(title_text="% mỡ", secondary_y=True, showgrid=False, tickformat=".1f")
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False}, key=key)


def the(k: dict, d: dict, che: bool, h: int):
    p = store.phong(k)
    bd = store._d(k.get("ngay_bat_dau"))
    hom = db.now_vn().date()
    tuan = ((hom - bd).days // 7 + 1) if bd and bd <= hom else None
    ss = d["ss"]
    ten = ten_an(k) if che else str(k.get("ho_ten", ""))
    with st.container(border=True, key=f"tda_{k['ma']}"):
        st.markdown(
            f'<div class="tda-h"><span class="n">{E(ten)}</span>'
            + (f'<span class="hac-chip" style="background:{store.mau_phong(p)}">🏢 {E(p)}</span>' if p else "")
            + (f'<span class="m">Tuần {tuan}</span>' if tuan else "")
            + (f'<span class="m">🎯 {E(str(k.get("muc_tieu_loai") or k.get("muc_tieu") or ""))[:40]}</span>'
               if (k.get("muc_tieu_loai") or k.get("muc_tieu")) else "")
            + "</div>"
            + '<div class="tda-cs">' + "".join(_chip(ss.get(x), t) for x, t in
                                              [("can_nang", "cân"), ("pbf", "% mỡ"), ("smm", "cơ"), ("khoi_mo", "mỡ"), ("v_eo", "eo"),
                                               ("v_bung", "bụng"), ("v_hong", "mông")]) + "</div>",
            unsafe_allow_html=True)
        if d["dau"] and d["moi"]:
            dn, mn = d["dau"].get("_ngay_can") or d["dau"].get("ngay"), d["moi"].get("_ngay_can") or d["moi"].get("ngay")
            if dn and mn:
                st.caption(f"Từ {dn:%d/%m/%Y} → {mn:%d/%m/%Y}")
        bieu_do(d, h, f"tda_f_{k['ma']}")
        st.markdown(f'<div class="tda-wm">{E(config.BRAND)}</div>', unsafe_allow_html=True)


CSS = """<style>
.tda-h{display:flex;flex-wrap:wrap;align-items:center;gap:8px;justify-content:flex-start}
.tda-h .n{font-weight:800;font-size:1.12rem}.tda-h .m{color:#8b8577;font-size:.85rem}
.tda-cs{display:flex;flex-wrap:wrap;gap:6px;margin:8px 0 2px}
.tda-c{border:1.5px solid;border-radius:10px;padding:3px 9px;display:inline-flex;flex-direction:column;align-items:center;line-height:1.15}
.tda-c b{font-size:1.02rem}.tda-c small{font-size:.7rem;opacity:.85}
.tda-wm{text-align:right;font-size:.62rem;letter-spacing:.18em;color:#B8912F;opacity:.8;font-weight:700;margin-top:-6px}
</style>"""


def trang(u: dict):
    st.markdown(CSS, unsafe_allow_html=True)
    DS = store.clients(ca_ngung=False)
    ui.hero("TIẾN ĐỘ HỌC VIÊN", "Biểu đồ tiến độ tất cả khách",
            "Theo dõi & chăm sóc từng khách · chụp màn hình khoe kết quả (bật “Che họ tên” trước khi đăng).")
    if not DS:
        st.info("Chưa có khách đang tập.")
        return
    TT = thu_tu_luu()
    a, b, c = st.columns([2, 1, 1], vertical_alignment="bottom")
    PH = sorted({store.phong(k) or "Chưa ghi phòng" for k in DS}, key=lambda p: (UU_TIEN.index(p) if p in UU_TIEN else 9, p))
    loc = a.pills("Phòng", PH, selection_mode="multi", key="tda_phong")
    cot = b.segmented_control("Số cột", [1, 2, 3], default=2, key="tda_cot") or 2
    che = c.toggle("🙈 Che họ tên", key="tda_che", help="Bật trước khi chụp màn hình đăng mạng xã hội: chỉ hiện tên, che họ (VD Học viên N.T.M. Duyên).")
    con_an = st.toggle("Hiện cả khách đã ẩn / chưa có số liệu", key="tda_all")

    with st.expander("↕️ Sắp xếp thứ tự & ẩn khách (để chụp màn hình)"):
        st.caption("Đổi số ở cột **Thứ tự** (số nhỏ đứng trước), bỏ tick **Hiện** để ẩn khách khỏi trang, rồi bấm Lưu. "
                   "Mặc định: Gold Gym → Online → Atlas.")
        L = sap_xep(DS, TT)
        df = pd.DataFrame([{"Thứ tự": i + 1, "Hiện": not TT.get(k["ma"], {}).get("an", False), "Khách": k["ho_ten"],
                            "🏢 Phòng": store.phong(k) or "—", "ma": k["ma"]} for i, k in enumerate(L)])
        ed = st.data_editor(df, hide_index=True, use_container_width=True, key="tda_ed",
                            column_order=["Thứ tự", "Hiện", "Khách", "🏢 Phòng"], disabled=["Khách", "🏢 Phòng"],
                            column_config={"Thứ tự": st.column_config.NumberColumn(min_value=1, step=1, alignment="center"),
                                           "Hiện": st.column_config.CheckboxColumn(alignment="center"),
                                           "Khách": st.column_config.Column(alignment="left"),
                                           "🏢 Phòng": st.column_config.Column(alignment="center")})
        x1, x2 = st.columns(2)
        if x1.button("💾 Lưu thứ tự", type="primary", use_container_width=True):
            moi = {r["ma"]: {"tt": float(r["Thứ tự"] or 999), "an": not bool(r["Hiện"])} for r in ed.to_dict("records")}
            db.append("DinhDuong", KEY, {"v": moi}, u["name"], "")
            st.toast("Đã lưu thứ tự ✅")
            st.rerun()
        if x2.button("↺ Về mặc định (Gold Gym → Online → Atlas)", use_container_width=True):
            db.append("DinhDuong", KEY, {"v": {}}, u["name"], "")
            st.rerun()

    L = [k for k in sap_xep(DS, TT) if not loc or (store.phong(k) or "Chưa ghi phòng") in loc]
    hien, thieu = [], []
    for k in L:
        if TT.get(k["ma"], {}).get("an") and not con_an:
            continue
        d = du_lieu(k)
        (hien if d["co"] else thieu).append((k, d))
    if con_an:
        hien += thieu
    if not hien:
        st.info("Chưa khách nào có số đo / cân — nhập ở trang 📈 Tiến độ & báo cáo.")
    h = {1: 380, 2: 300, 3: 250}[cot]
    for i in range(0, len(hien), cot):
        cs = st.columns(cot)
        for j, (k, d) in enumerate(hien[i:i + cot]):
            with cs[j]:
                the(k, d, che, h)
    if thieu and not con_an:
        st.caption("Chưa có số đo / cân: " + ", ".join(k["ho_ten"] for k, _ in thieu))
    st.caption("⚠️ Chỉ đăng kết quả của khách đã đồng ý. Ngày đầu khoá = lần đo đánh dấu “đầu khoá” (không có thì lần đo đầu tiên).")
