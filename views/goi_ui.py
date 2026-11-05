# Hoàng Anh Coaching v2.2 (2026-11-05) — tab "Gói · công nợ · bảo lưu" ở trang Khách & tài khoản (chỉ HLV).
from __future__ import annotations

import html
from datetime import timedelta

import pandas as pd
import streamlit as st

from core import db, goi, store, ui

E = html.escape


def chip(t: dict) -> str:
    return (f'<span style="display:inline-block;background:{t["mau"]};color:#fff;border-radius:999px;padding:2px 10px;'
            f'font-size:.78rem;font-weight:700">{E(t["ten"])}</span>')


def tab(k: dict, nguoi: str):
    hom = db.now_vn().date()
    H = store.hens()
    t = goi.trang_thai(k, hom, H)
    cn = goi.cong_no(k)
    bd, kt = goi.ngay_bat_dau(k), goi.ngay_ket_thuc(k)
    con = store.con_lai(k, H)
    st.markdown(f"**{E(store.mo_ta_goi(k, H, hom))}** &nbsp; {chip(t)}"
                + ("" if t["vao"] else " &nbsp; 🔒 <b>khách đang không vào được web</b>"), unsafe_allow_html=True)
    ui.tiles([(f"{bd:%d/%m/%Y}" if bd else "—", "bắt đầu", ""),
              (f"{kt:%d/%m/%Y}" if kt else "—", "kết thúc", "tự đặt" if k.get("ngay_ket_thuc") else
               ("theo gói" + (" + bảo lưu" if goi.bao_luu(k) else "") if kt else "gói buổi: hết khi hết buổi")),
              (f"{con} buổi" if con is not None else (f"{store.con_ngay(k, hom)} ngày" if kt else "—"), "còn lại", ""),
              (goi.vnd(cn["con_no"]) if cn["gia"] else "—", "còn nợ",
               f"đã trả {goi.vnd(cn['da_tra'])} / {goi.vnd(cn['gia'])}" if cn["gia"] else "chưa ghi giá gói")])

    ui.sec("💳 Thanh toán & công nợ")
    tt0 = goi.thanh_toan(k)
    df = pd.DataFrame([{"Ngày": store._d(x.get("ngay")), "Số tiền (đ)": goi.tien(x.get("so_tien")), "Ghi chú": x.get("ghi_chu", "")}
                       for x in tt0] or [{"Ngày": hom, "Số tiền (đ)": 0, "Ghi chú": ""}])
    with st.form(f"tt_{k['ma']}"):
        a, b = st.columns([1, 2])
        gia = a.text_input("Giá gói", value=str(k.get("gia") or ""), placeholder="VD 6.000.000 hoặc 6tr, 2tr5")
        b.caption("Mỗi lần khách chuyển tiền ghi 1 dòng. Còn nợ = giá gói − tổng đã trả.")
        ed = st.data_editor(df, num_rows="dynamic", hide_index=True, use_container_width=True,
                            column_config={"Ngày": st.column_config.DateColumn(format="DD/MM/YYYY"),
                                           "Số tiền (đ)": st.column_config.NumberColumn(format="%d", step=100000, min_value=0)})
        if st.form_submit_button("💾 Lưu thanh toán", type="primary"):
            ds = [{"ngay": (r["Ngày"] or hom).isoformat() if hasattr(r["Ngày"] or hom, "isoformat") else str(r["Ngày"])[:10],
                   "so_tien": int(r["Số tiền (đ)"] or 0), "ghi_chu": str(r.get("Ghi chú") or "").strip()}
                  for r in ed.to_dict("records") if int(r.get("Số tiền (đ)") or 0) > 0]
            if goi.luu(k, {"gia": gia.strip(), "thanh_toan": ds}, nguoi):
                st.toast("Đã lưu thanh toán")
                st.rerun()
            st.error("Chưa lưu được — thử lại.")

    ui.sec("⏸ Bảo lưu")
    st.caption("Trong thời gian bảo lưu: không xếp lịch, khách không vào web, mỗi ngày bảo lưu cộng thêm 1 ngày vào hạn gói "
               "(gói tuần / tháng, khi ngày kết thúc để tự tính).")
    bl0 = goi.bao_luu(k)
    dang = goi.dang_bao_luu(k, hom)
    if dang:
        st.info(f"Đang bảo lưu {dang['tu']:%d/%m} → {dang['den']:%d/%m}" + (f" · {dang.get('ly_do')}" if dang.get("ly_do") else ""))
        if st.button("▶️ Kết thúc bảo lưu hôm nay (khách tập lại)", key=f"bl_end_{k['ma']}"):
            ds = [{"tu": x["tu"].isoformat(), "den": (hom - timedelta(days=1) if x is dang else x["den"]).isoformat(),
                   "ly_do": x.get("ly_do", "")} for x in bl0 if not (x is dang and x["tu"] >= hom)]
            if goi.luu(k, {"bao_luu": ds}, nguoi):
                st.rerun()
    with st.form(f"bl_{k['ma']}"):
        df2 = pd.DataFrame([{"Từ ngày": x["tu"], "Đến ngày": x["den"], "Lý do": x.get("ly_do", "")} for x in bl0],
                           columns=["Từ ngày", "Đến ngày", "Lý do"])
        df2["Từ ngày"] = pd.to_datetime(df2["Từ ngày"])
        df2["Đến ngày"] = pd.to_datetime(df2["Đến ngày"])
        df2["Lý do"] = df2["Lý do"].astype(str)
        ed2 = st.data_editor(df2,
                             num_rows="dynamic", hide_index=True, use_container_width=True,
                             column_config={"Từ ngày": st.column_config.DateColumn(format="DD/MM/YYYY"),
                                            "Đến ngày": st.column_config.DateColumn(format="DD/MM/YYYY")})
        if st.form_submit_button("💾 Lưu bảo lưu", type="primary"):
            ds, loi = [], []
            for r in ed2.to_dict("records"):
                tu, den = r.get("Từ ngày"), r.get("Đến ngày")
                if not tu or not den or pd.isna(tu) or pd.isna(den):
                    continue
                tu, den = pd.Timestamp(tu).date(), pd.Timestamp(den).date()
                if den < tu:
                    loi.append(f"{tu:%d/%m} → {den:%d/%m}")
                    continue
                ds.append({"tu": tu.isoformat(), "den": den.isoformat(), "ly_do": str(r.get("Lý do") or "").strip()})
            if loi:
                st.error("Đến ngày phải sau Từ ngày: " + ", ".join(loi))
            elif goi.luu(k, {"bao_luu": ds}, nguoi):
                st.toast("Đã lưu bảo lưu")
                st.rerun()

    ui.sec("🔒 Ngày kết thúc & quyền vào web")
    with st.form(f"kt_{k['ma']}"):
        a, b = st.columns(2)
        kt_tay = a.date_input("Ngày kết thúc (tự đặt)", value=store._d(k.get("ngay_ket_thuc")), format="DD/MM/YYYY",
                              help="Để trống = web tự tính từ gói (bắt đầu + số tuần / tháng + ngày bảo lưu). "
                                   "Gói buổi: đặt ngày nếu gói có hạn dùng.")
        b.caption(f"Tự tính theo gói: {(store.han_goi(k) - timedelta(days=1)):%d/%m/%Y}" if store.han_goi(k) else "Gói buổi — không có hạn tự tính.")
        cho = st.checkbox("Cho khách vào web dù gói đã hết / đang bảo lưu (mở tạm, VD chờ gia hạn)", value=bool(k.get("cho_vao")))
        if st.form_submit_button("💾 Lưu", type="primary"):
            if goi.luu(k, {"ngay_ket_thuc": kt_tay.isoformat() if kt_tay else "", "cho_vao": bool(cho)}, nguoi):
                st.toast("Đã lưu")
                st.rerun()
    st.caption("Khách bị khoá khi: trạng thái Ngưng tập · đang bảo lưu · quá ngày kết thúc · gói buổi dùng hết buổi. "
               "Khách thấy thông báo lý do và lời nhắn liên hệ HLV để gia hạn. HLV vẫn xem mọi dữ liệu của khách bình thường.")


def canh_bao(DS: list[dict]) -> None:
    """Đầu trang Khách: ai sắp hết / đã hết gói, ai còn nợ."""
    hom = db.now_vn().date()
    H = store.hens()
    het, sap, no = [], [], []
    for k in DS:
        if (k.get("trang_thai") or "Đang tập") == "Ngưng tập":
            continue
        t = goi.trang_thai(k, hom, H)
        if t["ma"] in ("het_han", "het_buoi"):
            het.append(f"{k['ho_ten']} ({t['ten'].lower()})")
        elif t["ma"] == "sap_het":
            sap.append(f"{k['ho_ten']} ({t['ten'].lower()})")
        c = goi.cong_no(k)
        if c["con_no"] > 0:
            no.append(f"{k['ho_ten']} {goi.vnd(c['con_no'])}")
    if het:
        st.error("🔒 Hết gói (khách không vào được web): " + " · ".join(het))
    if sap:
        st.warning("⏳ Sắp hết gói: " + " · ".join(sap))
    if no:
        st.info("💳 Còn nợ: " + " · ".join(no))


def man_khoa(k: dict, t: dict) -> None:
    """Màn hình khách thấy khi gói hết / bảo lưu."""
    goi_k, _ = store.xung(k)
    ui.hero("HOÀNG ANH COACHING", f"Chào {goi_k} 👋", t["ly_do"] or "Tài khoản đang tạm khoá.")
    st.markdown(f"<div class='hac-card'><b>{E(t['ly_do'])}</b><br>Nhắn HLV Hoàng Anh để gia hạn hoặc mở lại tài khoản. "
                "Toàn bộ dữ liệu của bạn (giáo án, số đo, ảnh, thực đơn) vẫn được giữ nguyên.</div>", unsafe_allow_html=True)
