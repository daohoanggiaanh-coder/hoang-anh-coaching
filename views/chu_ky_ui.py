# Hoàng Anh Coaching v2.3 (2026-11-05) — tab "🌸 Chu kỳ" ở trang Khách (chỉ HLV, chỉ khách nữ).
from __future__ import annotations

import html
from datetime import timedelta

import streamlit as st

from core import chu_ky as ck, db, store, ui

E = html.escape


def tab(k: dict, nguoi: str):
    ma = k["ma"]
    if str(k.get("gioi_tinh") or "") != "Nữ":
        st.info("Mục này dành cho khách nữ — đặt Giới tính = Nữ ở tab Thông tin.")
        return
    hom = db.now_vn().date()
    c = ck.cai_dat(ma)
    st.caption("🔒 Chỉ HLV thấy. Khách KHÔNG thấy ngày — chỉ nhận lời nhắc + buổi tập đã được chỉnh nhẹ đúng những ngày đó.")
    a, b = st.columns([1, 1])
    with a:
        ui.sec("Ghi ngày bắt đầu kỳ")
        d = st.date_input("Ngày bắt đầu (ngày 1)", value=hom, max_value=hom + timedelta(days=3), format="DD/MM/YYYY", key=f"ck_d_{ma}")
        if st.button("➕ Ghi ngày này", key=f"ck_add_{ma}", type="primary"):
            if ck.luu(ma, {**c, "ngay_bd": sorted(set(c["ngay_bd"]) | {d})}, nguoi):
                st.toast("Đã ghi")
                st.rerun()
        if c["ngay_bd"]:
            st.markdown("Đã ghi: " + " · ".join(f"{x:%d/%m/%Y}" for x in c["ngay_bd"][-8:]))
            bo = st.multiselect("Xoá ngày ghi nhầm", c["ngay_bd"], format_func=lambda x: f"{x:%d/%m/%Y}", key=f"ck_bo_{ma}",
                                placeholder="Chọn ngày cần xoá")
            if bo and st.button("🗑 Xoá ngày đã chọn", key=f"ck_xoa_{ma}"):
                if ck.luu(ma, {**c, "ngay_bd": [x for x in c["ngay_bd"] if x not in bo]}, nguoi):
                    st.rerun()
    with b:
        ui.sec("Dự đoán")
        if c["ngay_bd"]:
            n = ck.do_dai_tb(c)
            tiep = next((x for x, du in ck.cac_ky(c, hom + timedelta(days=60)) if du and x >= hom - timedelta(days=int(c["so_ngay"]))), None)
            ui.tiles([(f"{n} ngày", "chu kỳ trung bình", "tính từ các lần đã ghi" if len(c["ngay_bd"]) > 1 else "theo số anh đặt"),
                      (f"{tiep:%d/%m}" if tiep else "—", "kỳ tới (dự đoán)", "ước tính ± vài ngày")])
            sap = ck.sap_toi(ma, hom, 35)
            B = {b_["ngay"]: b_ for b_ in store.buoi([k], hom, hom + timedelta(days=35)) if b_["trang_thai"] == "hen"}
            trung = [x for x in sap if x["ngay"] in B]
            if trung:
                st.markdown("**Buổi tập rơi vào kỳ (35 ngày tới):** " + " · ".join(
                    f"{store.THU[x['ngay'].weekday()]} {x['ngay']:%d/%m} (ngày {x['ngay_thu']})" for x in trung))
        else:
            st.caption("Ghi ít nhất 1 ngày bắt đầu kỳ để web dự đoán. Ghi 2–3 kỳ trở lên → web tự tính độ dài chu kỳ riêng của khách.")
    ui.sec("Cài đặt điều chỉnh")
    with st.form(f"ck_f_{ma}"):
        a, b, c3 = st.columns(3)
        bat = a.toggle("Bật tự điều chỉnh", value=bool(c.get("bat", True)))
        do_dai = b.number_input("Chu kỳ mặc định (ngày)", 21, 45, int(c.get("do_dai") or 28), help="Dùng khi chưa ghi đủ 2 kỳ")
        so_ngay = c3.number_input("Số ngày hành kinh", 2, 8, int(c.get("so_ngay") or 5))
        muc = st.radio("Mức ảnh hưởng của khách", list(ck.MUC), index=list(ck.MUC).index(c.get("muc", "vua")), horizontal=True,
                       format_func=lambda x: ck.MUC[x]["ten"])
        kieu = st.radio("Cách nhắc khách", ["kin_dao", "ro"], index=0 if c.get("kieu_nhac", "kin_dao") == "kin_dao" else 1, horizontal=True,
                        format_func=lambda x: "Kín đáo (không nhắc tới chu kỳ)" if x == "kin_dao" else "Nói rõ, quan tâm (có nhắc chu kỳ)")
        m = ck.MUC[muc]
        st.caption(f"Áp dụng: {m['ngay']} ngày đầu → tạ ~{m['kg'] * 100:.0f}%, bớt {m['hiep']} hiệp, tránh gập bụng mạnh / treo người"
                   + (", ngày 1 gợi ý buổi phục hồi nhẹ" if m["nghi_ngay1"] else "") + ". Khách bấm “thấy khoẻ” thì tập bình thường.")
        st.markdown(f"Khách sẽ thấy: _{E(ck.loi_nhan(kieu, 1, True, m))}_")
        if st.form_submit_button("💾 Lưu cài đặt", type="primary"):
            if ck.luu(ma, {**c, "bat": bat, "do_dai": do_dai, "so_ngay": so_ngay, "muc": muc, "kieu_nhac": kieu}, nguoi):
                st.toast("Đã lưu")
                st.rerun()
    st.caption("Căn cứ: tổng quan McNulty & cs. (2020, Sports Medicine) — sức tập có thể giảm nhẹ ở đầu chu kỳ, khác nhau nhiều giữa "
               "từng người → web chỉ gợi ý, HLV và khách quyết theo cảm nhận thật. Đau bụng dữ dội, kinh kéo dài / thất thường → khuyên khách đi khám.")
