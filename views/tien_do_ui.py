# Hoàng Anh Coaching v1.9 (2026-11-01) — khách tự nhập số đo hằng tuần + ảnh tiến độ (đầu khoá, mỗi 4 tuần)
from __future__ import annotations

import html
from datetime import timedelta

import pandas as pd
import streamlit as st

from core import anh as A, db, tien_do as td

E = html.escape
S = st.session_state
THUOC_DAY = ["can_nang", "v_eo", "v_bung", "v_hong", "v_dui", "v_tay", "v_nguc"]
INBODY = ["pbf", "smm", "khoi_mo", "mo_noi_tang"]
CHU_KY_ANH = 28
HUONG_DAN_DO = {
    "v_eo": "chỗ nhỏ nhất giữa xương sườn và rốn", "v_bung": "ngang rốn, thở ra nhẹ", "v_hong": "chỗ mông to nhất",
    "v_dui": "đùi phải, dưới nếp mông 1 gang tay", "v_tay": "bắp tay phải, giữa vai và khuỷu, tay thả lỏng", "v_nguc": "ngang núm vú",
}


def lich_anh(ANH: list[dict], hom) -> tuple[str, object]:
    """(đợt nên chụp, ngày đến hạn)."""
    if not ANH:
        return "dau_khoa", hom
    cuoi = max(pd.Timestamp(v["ngay"]).date() for v in ANH)
    return "hang_thang", cuoi + timedelta(days=CHU_KY_ANH)


def nhap_so_do(k: dict, nguoi: str, vai: str = "khach"):
    ma = k["ma"]
    hom = db.now_vn().date()
    SD = td.so_do(ma)
    tuan_nay = hom - timedelta(days=hom.weekday())
    da = (not SD.empty) and any(d >= tuan_nay for d in SD["ngay"])
    st.markdown("**📏 Số đo hằng tuần** — đo **sáng thứ Hai**, trước khi ăn, cùng 1 thước dây" + (" ✅ tuần này đã đo" if da else ""))
    with st.form(f"sdk_{ma}_{vai}", clear_on_submit=True):
        a, b = st.columns(2)
        nd = a.date_input("Ngày đo", hom, format="DD/MM/YYYY", max_value=hom, min_value=hom - timedelta(days=30))
        dot = "dau_khoa" if SD.empty else "tuan"
        b.markdown(f"<div style='padding-top:30px;color:#8b8577'>Đợt: <b>{td.DOT[dot]}</b></div>", unsafe_allow_html=True)
        vals, cs = {}, st.columns(2)
        for i, ck in enumerate(THUOC_DAY):
            ten, dv, _ = td.TEN[ck]
            vals[ck] = cs[i % 2].number_input(f"{ten} ({dv})", 0.0, 300.0, value=None, step=0.1, format="%.1f", placeholder="—",
                                              help=HUONG_DAN_DO.get(ck), key=f"sdk_{ck}_{ma}_{vai}")
        with st.expander("Có đo InBody? (không bắt buộc)"):
            cs2 = st.columns(2)
            for i, ck in enumerate(INBODY):
                ten, dv, _ = td.TEN[ck]
                vals[ck] = cs2[i % 2].number_input(f"{ten}{f' ({dv})' if dv else ''}", 0.0, 100.0, value=None, step=0.1, format="%.1f",
                                                   placeholder="—", key=f"sdk_{ck}_{ma}_{vai}")
        gc = st.text_input("Ghi chú", placeholder="VD đo sau kỳ nghỉ, đang tới tháng…")
        if st.form_submit_button("💾 Lưu số đo", type="primary", use_container_width=True):
            v2 = {x: y for x, y in vals.items() if y}
            if not v2:
                st.error("Nhập ít nhất 1 chỉ số.")
            elif td.luu_so_do(ma, nd, dot, v2, gc.strip(), {"name": nguoi}):
                if v2.get("can_nang"):
                    td.luu_can(ma, nd, v2["can_nang"], {"name": nguoi})
                st.toast("Đã lưu số đo +25 điểm 📏")
                st.rerun()
            else:
                st.error("Chưa lưu được — thử lại.")
    st.caption("Mẹo: thước dây sát da nhưng không thít; đo 2 lần lấy trung bình. Vòng giảm mà cân đứng yên = đang giảm mỡ, tăng cơ — tốt!")


def nhap_anh(k: dict, nguoi: str, vai: str = "khach"):
    ma = k["ma"]
    hom = db.now_vn().date()
    ANH = td.anh(ma)
    dot, han = lich_anh(ANH, hom)
    if dot == "dau_khoa":
        st.markdown("**📸 Ảnh đầu khoá** — chụp ngay để sau này so trước / sau")
    elif han <= hom:
        st.markdown(f"**📸 Đến hạn chụp ảnh 4 tuần** (từ {han:%d/%m}) — chụp hôm nay nhé!")
    else:
        st.markdown(f"**📸 Ảnh tiến độ** — lần chụp tiếp theo: **{han:%d/%m/%Y}** (mỗi 4 tuần)")
    with st.form(f"anhk_{ma}_{vai}", clear_on_submit=True):
        a, b = st.columns(2)
        na = a.date_input("Ngày chụp", hom, format="DD/MM/YYYY", max_value=hom, min_value=hom - timedelta(days=30))
        b.markdown(f"<div style='padding-top:30px;color:#8b8577'>Đợt: <b>{td.DOT[dot]}</b></div>", unsafe_allow_html=True)
        cs = st.columns(3)
        ups = {g: cs[i].file_uploader(f"Ảnh {ten.lower()}", type=["jpg", "jpeg", "png", "webp"], key=f"upk_{g}_{ma}_{vai}")
               for i, (g, ten) in enumerate(td.GOC.items())}
        st.caption("Chụp cùng chỗ, cùng ánh sáng, cùng trang phục (đồ bó / đồ tập), đứng thẳng, tay thả lỏng, máy ngang bụng cách 2–3 m. "
                   "Ảnh chỉ bạn và HLV xem.")
        if st.form_submit_button("💾 Lưu ảnh", type="primary", use_container_width=True):
            files = {g: A.shrink(f.getvalue(), 1600) for g, f in ups.items() if f is not None}
            if not files:
                st.error("Chọn ít nhất 1 ảnh.")
            else:
                with st.spinner(f"Đang lưu {len(files)} ảnh…"):
                    up = db.upload_images(files, f"HAC_{ma}_")
                if not up:
                    st.error("Chưa lưu được ảnh — thử lại.")
                else:
                    for g, i_ in up.items():
                        td.luu_anh(ma, na, dot, g, i_, {"name": nguoi})
                    st.toast(f"Đã lưu {len(up)} ảnh +40 điểm 📸")
                    st.rerun()
