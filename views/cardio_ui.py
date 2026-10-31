# Hoàng Anh Coaching v1.4 (2026-10-31) — trang cardio dùng chung: HLV (đặt target, nhập từ ảnh khách) · khách (xem, nhập kết quả)
from __future__ import annotations

import html
from datetime import timedelta

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from core import cardio as cd, db, store, tien_do as td, ui

E = html.escape
S = st.session_state
LOAI = {"tap": ("Ngày tập tạ", "🏋️", "#C8A24A"), "nghi": ("Ngày nghỉ", "🚶", "#2E7D4F"), "off": ("Nghỉ hẳn", "😴", "#9c958a")}
CSS = """<style>
.cd-wk{display:grid;grid-template-columns:repeat(7,1fr);gap:8px;margin:8px 0 14px}
@media(max-width:760px){.cd-wk{grid-template-columns:repeat(2,1fr)}}
.cd-d{background:#fff;border:1px solid #E6DCC6;border-radius:16px;padding:10px 11px;position:relative}
.cd-d.h{border:2px solid #C8A24A;box-shadow:0 6px 18px rgba(200,162,74,.18)}
.cd-d.x{background:#F2FAF4;border-color:#9FD0AE}.cd-d.m{background:#FDF3F1;border-color:#E9B8AE}
.cd-d small{display:block;font-size:.62rem;letter-spacing:.12em;font-weight:900;color:#8b8577}
.cd-d .t{font-size:1.25rem;font-weight:900;color:#1C1B19;margin:2px 0}.cd-d .t i{font-style:normal;font-size:.72rem;color:#8b8577}
.cd-d .b{font-size:.7rem;font-weight:800;color:#B4442F}.cd-d .p{font-size:.72rem;color:#6C6860;margin-top:2px}
.cd-d .bar{height:6px;border-radius:9px;background:#F0E9D8;margin-top:6px;overflow:hidden}.cd-d .bar span{display:block;height:100%}
.cd-hero{background:radial-gradient(circle at 10% 0%,#3d3427,#14120F 70%);border-radius:22px;padding:18px 22px;color:#F3ECDC;margin:4px 0 10px}
.cd-hero .k{color:#E8C76A;letter-spacing:.18em;font-weight:800;font-size:.64rem}
.cd-hero .big{font-size:2.1rem;font-weight:900;color:#fff}.cd-hero .big small{font-size:.9rem;color:#D8D1C1;margin-left:6px}
.cd-hero .bar{height:10px;border-radius:9px;background:rgba(255,255,255,.12);margin:10px 0 6px;overflow:hidden}
.cd-hero .bar span{display:block;height:100%;background:linear-gradient(90deg,#C8A24A,#E8C76A)}
.cd-hero .row{display:flex;gap:18px;flex-wrap:wrap;font-size:.8rem;color:#D8D1C1}.cd-hero .row b{color:#fff}
</style>"""


def _thong_so(d: dict) -> str:
    if not d.get("may"):
        return ""
    s = cd.MAY.get(d["may"], "")
    if d["may"] in cd.CO_DOC:
        s += f" · dốc {float(d.get('doc') or 0):g}% · {float(d.get('toc_do') or 0):g} km/h"
    return s


def _form_target(k: dict, c: dict, tap: list[int], nguoi: str, hs: dict):
    with st.form(f"cdt_{k['ma']}"):
        moi = {}
        cols = st.columns(2)
        for col, loai in zip(cols, ("tap", "nghi")):
            ten, ic, _ = LOAI[loai]
            lo, hi = cd.KHOANG[loai]
            with col:
                st.markdown(f"**{ic} {ten}** · khuyến nghị {lo}–{hi} phút")
                x = c[loai]
                may = st.selectbox("Máy", list(cd.MAY), index=list(cd.MAY).index(x["may"]) if x["may"] in cd.MAY else 0,
                                   format_func=cd.MAY.get, key=f"cdm_{k['ma']}_{loai}")
                a, b = st.columns(2)
                doc = a.number_input("Độ dốc (%)", 0.0, 30.0, float(x["doc"]), step=0.5, key=f"cdd_{k['ma']}_{loai}")
                tdo = b.number_input("Tốc độ (km/h)", 0.0, 20.0, float(x["toc_do"]), step=0.1, key=f"cds_{k['ma']}_{loai}")
                a, b = st.columns(2)
                ph = a.number_input("Thời gian (phút)", 5, 180, int(x["phut"]), step=5, key=f"cdp_{k['ma']}_{loai}")
                td_ = b.number_input("Tối đa khi bù (phút)", 5, 240, int(max(x["toi_da"], x["phut"])), step=5, key=f"cdx_{k['ma']}_{loai}",
                                     help="Ngày thiếu được bù chia đều cho các ngày còn lại nhưng không vượt mức này")
                moi[loai] = {"may": may, "doc": doc, "toc_do": tdo, "phut": ph, "toi_da": max(td_, ph)}
        a, b = st.columns(2)
        nt = a.multiselect("Thứ có tập tạ", list(range(7)), default=tap, format_func=lambda i: store.THU[i], key=f"cdnt_{k['ma']}")
        off = b.multiselect("Thứ nghỉ hẳn (không cardio)", list(range(7)), default=[int(x) for x in c.get("ngay_off") or []],
                            format_func=lambda i: store.THU[i], key=f"cdo_{k['ma']}")
        ranh = st.toggle("Khách rảnh — cho phép dồn bù vượt mức tối đa", value=bool(c.get("ranh")), key=f"cdr_{k['ma']}")
        gc = st.text_input("Lời dặn khách (khách thấy)", value=c.get("ghi_chu") or "", key=f"cdg_{k['ma']}",
                           placeholder="VD: giữ nhịp thở nói chuyện được, không vịn tay vịn")
        dong_bo = st.checkbox("Cập nhật tổng phút cardio vào thông số thực đơn", value=True, key=f"cdsy_{k['ma']}",
                              help="Thực đơn sẽ cộng năng lượng cardio này vào nhu cầu hằng ngày")
        if st.form_submit_button("💾 Lưu target cardio", type="primary", use_container_width=True):
            c2 = {**c, **moi, "ngay_tap": nt, "ngay_off": off, "ranh": ranh, "ghi_chu": gc.strip()}
            if cd.luu_cai_dat(k["ma"], c2, nguoi):
                if dong_bo and hs:
                    from views import common as C
                    W = sum(x["phut"] for x in cd.target_goc(c2, nt or tap).values())
                    C.luu_hs_dd(k["ma"], {**hs, "cardio_phut_tuan": W, **({"ngay_tap": nt} if nt else {})}, nguoi)
                st.toast("Đã lưu target cardio")
                st.rerun()
            st.error("Chưa lưu được — thử lại.")


def _the_tuan(w: dict) -> str:
    out = ""
    for d in w["ngay"]:
        ten, ic, mau = LOAI[d["loai"]]
        tg = d["target"]
        pct = min(d["lam"] / tg * 100, 100) if tg else 0
        cls = "h" if d["hom_nay"] else ("x" if tg and d["lam"] >= tg else "m" if d["qua"] and tg and d["lam"] < tg else "")
        bu = f'<div class="b">+{d["bu"]} phút bù</div>' if d["bu"] > 0 else (f'<div class="b" style="color:#2E7D4F">{d["bu"]} phút (đã làm dư)</div>'
                                                                            if d["bu"] < 0 else "")
        trang = "✅" if tg and d["lam"] >= tg else ("⚠️" if d["qua"] and tg else "")
        out += (f'<div class="cd-d {cls}"><small>{store.THU[d["thu"]].replace("Thứ ", "T").upper()} · {d["ngay"]:%d/%m}'
                f'{" · HÔM NAY" if d["hom_nay"] else ""}</small>'
                f'<div class="p">{ic} {ten}</div>'
                + (f'<div class="t">{d["lam"]}<i> / {tg} phút</i> {trang}</div>{bu}<div class="p">{E(_thong_so(d))}</div>'
                   f'<div class="bar"><span style="width:{pct:.0f}%;background:{mau}"></span></div>' if tg else '<div class="t">—</div>')
                + "</div>")
    return f'<div class="cd-wk">{out}</div>'


def _bieu_do(w: dict):
    x = [f"{store.THU[d['thu']].replace('Thứ ', 'T')}" for d in w["ngay"]]
    fig = go.Figure()
    fig.add_bar(x=x, y=[d["target"] for d in w["ngay"]], name="Target (đã gồm bù)", marker_color="#EFE6D2",
                text=[d["target"] or "" for d in w["ngay"]], textposition="outside")
    fig.add_bar(x=x, y=[d["lam"] for d in w["ngay"]], name="Đã làm", marker_color=["#2E7D4F" if d["target"] and d["lam"] >= d["target"]
                                                                                    else "#C8A24A" for d in w["ngay"]])
    goc, lam, a, b = [], [], 0, 0
    for d in w["ngay"]:
        a += d["phut"]
        b += d["lam"]
        goc.append(a)
        lam.append(b)
    fig.add_scatter(x=x, y=goc, name="Cộng dồn target", yaxis="y2", line=dict(color="#1C1B19", dash="dot", width=2), mode="lines+markers")
    fig.add_scatter(x=x, y=lam, name="Cộng dồn đã làm", yaxis="y2", line=dict(color="#B4442F", width=3), mode="lines+markers")
    fig.update_layout(barmode="overlay", yaxis2=dict(overlaying="y", side="right", showgrid=False, title="phút cộng dồn"),
                      legend=dict(orientation="h", y=-0.2))
    st.plotly_chart(ui.layout(fig, 340, "phút / ngày"), use_container_width=True, config={"displayModeBar": False})


def _form_ket_qua(k: dict, vai: str, nguoi: str, w: dict, kg: float | None):
    ma = k["ma"]
    hom = db.now_vn().date()
    hien = next((d for d in w["ngay"] if d["hom_nay"]), w["ngay"][0])
    pre = S.get(f"cd_doc_{ma}") or {}
    v = S.get(f"cd_v_{ma}", 0)
    hlv = vai == "hlv"
    with st.container(border=True):
        st.markdown("**✍️ Nhập kết quả cardio**" + (" — hoặc tải ảnh màn hình máy khách gửi" if hlv else ""))
        anh = st.file_uploader("📷 Ảnh màn hình máy (không bắt buộc)", type=["jpg", "jpeg", "png", "webp"], key=f"cd_f_{ma}_{v}")
        if anh is not None:
            a, b = st.columns([1, 2])
            a.image(anh.getvalue(), use_container_width=True)
            from core import llm
            if llm.is_online():
                if b.button("🤖 Đọc số từ ảnh", key=f"cd_ai_{ma}_{v}"):
                    from core import anh as A
                    with st.spinner("Đang đọc ảnh (10–30 giây)…"):
                        try:
                            S[f"cd_doc_{ma}"] = cd.doc_anh(A.shrink(anh.getvalue(), 1400))
                        except llm.LLMError as e:
                            b.error(f"Chưa đọc được: {e}")
                    st.rerun()
                if pre:
                    b.success("Đã đọc — kiểm tra lại từng ô rồi bấm Lưu.")
            else:
                b.caption("Nhìn ảnh rồi điền số bên dưới. (Thêm `GEMINI_API_KEY` vào Secrets để web tự đọc số.)")
        with st.form(f"cd_kq_{ma}_{v}", clear_on_submit=False):
            a, b, c = st.columns(3)
            ngay = a.date_input("Ngày", value=hom, min_value=hom - timedelta(days=60), max_value=hom, format="DD/MM/YYYY")
            m0 = pre.get("may") or hien.get("may") or "bo_doc"
            may = b.selectbox("Máy", list(cd.MAY), index=list(cd.MAY).index(m0) if m0 in cd.MAY else 0, format_func=cd.MAY.get)
            ph = c.number_input("Thời gian (phút)", 0.0, 300.0, float(pre.get("phut") or 0), step=1.0)
            a, b, c = st.columns(3)
            doc = a.number_input("Độ dốc TB (%)", 0.0, 40.0, float(pre.get("doc") if pre.get("doc") is not None else hien.get("doc") or 0), step=0.5)
            tdo = b.number_input("Tốc độ TB (km/h)", 0.0, 25.0, float(pre.get("toc_do") or hien.get("toc_do") or 0), step=0.1)
            qd = c.number_input("Quãng đường (km, nếu có)", 0.0, 60.0, float(pre.get("quang_duong") or 0), step=0.1)
            a, b, c = st.columns(3)
            kc = a.number_input("Kcal máy hiện (nếu có)", 0, 3000, int(pre.get("kcal") or 0), step=5)
            nt = b.number_input("Nhịp tim TB (nếu có)", 0, 220, int(pre.get("nhip_tim") or 0), step=1)
            cn = c.select_slider("Cảm giác", ["Rất nhẹ", "Nhẹ", "Vừa", "Mệt", "Rất mệt"], value="Vừa")
            gc = st.text_input("Ghi chú", placeholder="VD: đau gối nhẹ phút 30, giảm dốc")
            if st.form_submit_button("💾 Lưu kết quả", type="primary", use_container_width=True):
                if ph <= 0:
                    st.error("Nhập thời gian (phút).")
                else:
                    r = {"ngay": ngay.isoformat(), "may": may, "phut": ph, "doc": doc if may in cd.CO_DOC else None,
                         "toc_do": tdo if may in cd.CO_DOC else None, "quang_duong": qd or None, "kcal_may": kc or None,
                         "nhip_tim": nt or None, "cam_giac": cn, "ghi_chu": gc.strip()}
                    r["kcal"] = cd.kcal(r, kg)
                    if anh is not None:
                        from core import anh as A
                        up = db.upload_images({"cd": A.shrink(anh.getvalue(), 1400)}, f"HAC_{ma}_CD_")
                        if up:
                            r["anh"] = up["cd"]
                    if cd.ghi(ma, r, nguoi, vai):
                        S.pop(f"cd_doc_{ma}", None)
                        S[f"cd_v_{ma}"] = v + 1
                        st.toast(f"Đã lưu {ph:g} phút cardio")
                        st.rerun()
                    st.error("Chưa lưu được — thử lại.")


def trang(k: dict, vai: str, nguoi: str, q: dict | None = None):
    st.markdown(CSS, unsafe_allow_html=True)
    ma = k["ma"]
    hlv = vai == "hlv"
    q = {x: True for x in store.QUYEN} if hlv else (q or store.quyen(k))
    from views import common as C
    hs = C.ho_so_dd(k)
    c = cd.cai_dat(ma)
    tap = cd.ngay_tap(c, k, hs)
    L = cd.logs(ma)
    CAN = td.can_ngay(ma)
    kg = float(CAN["kg"].iloc[-1]) if len(CAN) else (float(hs["kg"]) if hs.get("kg") else None)
    hom = db.now_vn().date()
    if hlv:
        with st.expander("🎯 Target cardio của khách" + ("" if c["_co"] else " — chưa đặt, đang dùng mặc định"), expanded=not c["_co"]):
            _form_target(k, c, tap, nguoi, hs)
    elif not c["_co"]:
        st.info("HLV chưa đặt target cardio riêng — tạm theo mức chung bên dưới.")
    lui = st.segmented_control("Tuần", [0, 1, 2, 3], default=0, key=f"cd_tuan_{ma}_{vai}",
                               format_func=lambda i: "Tuần này" if i == 0 else f"{i} tuần trước") or 0
    w = cd.tuan(c, tap, L, hom, kg, cd.dau_tuan(hom) - timedelta(weeks=lui))     # tuần đã qua: đủ 7 ngày, không bù
    st.markdown(
        f'<div class="cd-hero"><div class="k">CARDIO · {w["tu"]:%d/%m} – {w["den"]:%d/%m}</div>'
        f'<div class="big">{w["da"]}<small>/ {w["W"]} phút target tuần · {w["pct"]}%</small></div>'
        f'<div class="bar"><span style="width:{min(w["pct"], 100)}%"></span></div>'
        f'<div class="row"><span>Còn lại <b>{w["con"]} phút</b></span><span>Thiếu từ các ngày trước <b>{w["thieu"]} phút</b> — đã chia đều '
        f'cho các ngày còn lại</span><span>≈ <b>{w["kcal"]:,} kcal</b> (ước tính)</span></div></div>'.replace(",", "."),
        unsafe_allow_html=True)
    if w["khong_bu"] and not lui:
        st.warning(f"Còn **{w['khong_bu']} phút** không bù kịp trong tuần vì các ngày còn lại đã chạm mức tối đa. "
                   + ("HLV có thể tăng mức tối đa hoặc bật 'Khách rảnh'." if hlv else "Không sao — tuần sau làm đều hơn nhé."))
    if c.get("ghi_chu"):
        ui.note(f"<b>HLV dặn:</b> {E(c['ghi_chu'])}")
    st.markdown(_the_tuan(w), unsafe_allow_html=True)
    _bieu_do(w)
    ui.note("Ngày nào thiếu, phần thiếu được <b>chia đều</b> cho các ngày còn lại trong tuần (không dồn vào 1 ngày), tối đa "
            f"<b>{c['tap']['toi_da']} phút</b> ngày tập, <b>{c['nghi']['toi_da']} phút</b> ngày nghỉ"
            + (" — khách rảnh nên phần vượt vẫn được chia tiếp." if c.get("ranh") else ".")
            + " Kcal tính theo phương trình ACSM (máy chạy) hoặc MET (máy khác) — chỉ là ước tính, sai số khoảng ±10–20 %.")
    if hlv or q.get("ghi_cardio"):
        _form_ket_qua(k, vai, nguoi, w, kg)
    LS = [r for r in reversed(L)][:40]
    if LS:
        ui.sec("Nhật ký cardio")
        IMG = db.get_images([r["anh"] for r in LS[:10] if r.get("anh")]) if any(r.get("anh") for r in LS[:10]) else {}
        for r in LS[:15]:
            a, b = st.columns([5, 1], vertical_alignment="center")
            a.markdown(f"**{pd.Timestamp(r['ngay']):%d/%m}** · {cd.MAY.get(r.get('may'), '')} · **{float(r.get('phut') or 0):g} phút**"
                       + (f" · dốc {float(r['doc']):g}% · {float(r['toc_do']):g} km/h" if r.get("doc") is not None and r.get("toc_do") else "")
                       + (f" · {cd.quang_duong(r):g} km" if cd.quang_duong(r) else "")
                       + (f" · ≈ {r['kcal']:.0f} kcal" if r.get("kcal") else "")
                       + (f" · ❤️ {r['nhip_tim']}" if r.get("nhip_tim") else "")
                       + (f" · {r.get('cam_giac')}" if r.get("cam_giac") else "")
                       + (" · *HLV nhập*" if r.get("nguon") == "hlv" else "")
                       + (f"  \n_{E(r['ghi_chu'])}_" if r.get("ghi_chu") else ""))
            if (hlv or r.get("nguon") != "hlv") and b.button("Xoá", key=f"cdx_{r['id']}_{vai}"):
                cd.xoa(ma, r["id"], nguoi)
                st.rerun()
            if r.get("anh") in IMG:
                with a.expander("Ảnh"):
                    st.image(IMG[r["anh"]], width=320)
    H = cd.lich_su_tuan(c, tap, L, hom, kg, 8)
    if any(x["da"] for x in H):
        ui.sec("8 tuần gần nhất")
        fig = go.Figure(go.Bar(x=[f"{x['tu']:%d/%m}" for x in H], y=[x["pct"] for x in H], text=[f"{x['pct']}%" for x in H],
                               textposition="outside", marker_color=["#2E7D4F" if x["pct"] >= 100 else "#C8A24A" for x in H]))
        fig.add_hline(y=100, line_dash="dot", line_color="#1C1B19")
        st.plotly_chart(ui.layout(fig, 260, "% hoàn thành target tuần"), use_container_width=True, config={"displayModeBar": False})
