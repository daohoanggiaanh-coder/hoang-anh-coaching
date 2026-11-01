# Hoàng Anh Coaching v1.9 (2026-11-01) — hồ sơ khách đầy đủ (giống app tập): ảnh đại diện, thông tin cá nhân, kinh nghiệm tập,
# sức khoẻ, liên hệ khẩn cấp. Khách tự điền ở Tài khoản; HLV điền thay ở Khách & tài khoản. Có % hoàn thành hồ sơ.
from __future__ import annotations

import html
from datetime import date

import streamlit as st

from core import anh as A, db, hinh, store

E = html.escape
S = st.session_state

KINH_NGHIEM = ["Chưa tập bao giờ", "Dưới 6 tháng", "6–12 tháng", "1–3 năm", "Trên 3 năm"]
MON_DA_TAP = ["Gym / tạ", "Chạy bộ", "Yoga / Pilates", "Bơi", "Cầu lông / tennis", "Bóng đá", "Võ thuật", "Đạp xe", "Nhảy / aerobic", "Khác"]
KHUNG_GIO = ["Sáng sớm (5–7h)", "Sáng (7–11h)", "Trưa (11–14h)", "Chiều (14–17h)", "Tối (17–20h)", "Tối muộn (sau 20h)"]
CONG_VIEC = ["Ngồi văn phòng nhiều", "Đi lại vừa phải", "Đứng / di chuyển nhiều", "Lao động nặng"]
GIAC_NGU = ["Dưới 5 tiếng", "5–6 tiếng", "6–7 tiếng", "7–8 tiếng", "Trên 8 tiếng"]

# trường dùng để tính % hoàn thành
CAN_CO = ["ho_ten", "ngay_sinh", "gioi_tinh", "chieu_cao", "sdt", "nghe_nghiep", "kinh_nghiem", "mon_da_tap", "buoi_co_the",
          "khung_gio", "muc_tieu", "chan_thuong", "benh_nen", "giac_ngu", "cong_viec", "lh_ten", "lh_sdt"]


def phan_tram(k: dict) -> int:
    co = sum(1 for f in CAN_CO if str(k.get(f) or "").strip() not in ("", "[]", "0", "None"))
    co += 1 if hinh.anh_goc_khach(k) else 0
    return round(co / (len(CAN_CO) + 1) * 100)


def _d(v) -> date | None:
    try:
        return date.fromisoformat(str(v)[:10])
    except ValueError:
        return None


def _ds(v) -> list:
    if isinstance(v, list):
        return v
    return [x.strip() for x in str(v or "").split(",") if x.strip()]


def anh_dai_dien(k: dict, nguoi: str, vai: str):
    """Ảnh đại diện: xem trước, tải ảnh riêng (khách / HLV), kéo khung cắt, quay lại dùng ảnh đầu khoá."""
    ma = k["ma"]
    a, b = st.columns([1, 2.2], vertical_alignment="center")
    khung = a.empty()
    goc = hinh.anh_goc_khach(k)
    rieng = bool(k.get("anh_dai_dien"))
    y0 = int(float(k.get("avatar_y") or (45 if rieng else 14)))
    r0 = int(float(k.get("avatar_r") or (88 if rieng else 62)))
    with b:
        st.caption("Ảnh riêng của khách" if rieng else ("Đang tự cắt từ ảnh mặt trước đầu khoá" if goc else "Chưa có ảnh — tải ảnh chân dung rõ mặt"))
        f = st.file_uploader("Tải ảnh đại diện (chân dung, rõ mặt)", type=["jpg", "jpeg", "png", "webp"], key=f"hs_av_{ma}_{vai}")
        y, r = y0, r0
        if goc:
            with st.expander("✂️ Chỉnh khung cắt"):
                y = st.slider("Vị trí khuôn mặt (từ trên xuống, %)", 0, 100, y0, key=f"hs_avy_{ma}_{vai}")
                r = st.slider("Độ zoom (nhỏ = gần mặt hơn)", 20, 100, r0, key=f"hs_avr_{ma}_{vai}")
        c1, c2 = st.columns(2)
        if f is not None and c1.button("⬆️ Dùng ảnh này", type="primary", key=f"hs_avu_{ma}_{vai}", use_container_width=True):
            up = db.upload_images({"x": A.shrink(f.getvalue(), 900)}, f"HAC_{ma}_AV_")
            if up and up.get("x") and store.save_client({**k, "anh_dai_dien": up["x"], "avatar_y": 45, "avatar_r": 88}, nguoi):
                st.toast("Đã cập nhật ảnh đại diện")
                st.rerun()
            st.error("Chưa tải được ảnh — thử lại.")
        if goc and (y, r) != (y0, r0) and c1.button("💾 Lưu khung cắt", key=f"hs_avs_{ma}_{vai}", use_container_width=True):
            store.save_client({**k, "avatar_y": y, "avatar_r": r}, nguoi)
            st.rerun()
        if rieng and vai == "hlv" and c2.button("↩ Dùng ảnh đầu khoá", key=f"hs_avr0_{ma}_{vai}", use_container_width=True):
            store.save_client({**k, "anh_dai_dien": "", "avatar_y": "", "avatar_r": ""}, nguoi)
            st.rerun()
    khung.markdown(hinh.the_avatar(hinh._uri(goc, y, r) if goc else "", k.get("ho_ten", ""), 130), unsafe_allow_html=True)


def form(k: dict, nguoi: str, vai: str):
    """Hồ sơ đầy đủ. vai = 'hlv' (điền thay) hoặc 'khach' (tự điền)."""
    ma = k["ma"]
    hom = db.now_vn().date()
    pt = phan_tram(k)
    st.progress(pt / 100, text=f"Hồ sơ hoàn thành {pt}%" + (" — điền đủ để HLV lên giáo án và thực đơn chính xác hơn" if pt < 100 else " ✅"))
    anh_dai_dien(k, nguoi, vai)
    with st.form(f"hsf_{ma}_{vai}"):
        st.markdown("##### 👤 Thông tin cá nhân")
        a, b, c = st.columns(3)
        ten = a.text_input("Họ tên *", k.get("ho_ten", ""))
        ns = b.date_input("Ngày sinh", value=_d(k.get("ngay_sinh")), min_value=date(1940, 1, 1), max_value=hom, format="DD/MM/YYYY")
        gt = c.selectbox("Giới tính", ["", "Nữ", "Nam"], format_func=lambda x: x or "— Chọn —", index=["", "Nữ", "Nam"].index(k.get("gioi_tinh")) if k.get("gioi_tinh") in ("Nữ", "Nam") else 0)
        a, b, c = st.columns(3)
        cc = a.number_input("Chiều cao (cm)", 0.0, 230.0, float(k.get("chieu_cao") or 0), step=0.5)
        sdt = b.text_input("Số điện thoại", str(k.get("sdt") or ""))
        em = c.text_input("Email", k.get("email") or "")
        a, b = st.columns(2)
        ng = a.text_input("Nghề nghiệp", k.get("nghe_nghiep") or "", placeholder="VD nhân viên văn phòng, kinh doanh, giáo viên")
        kv = b.text_input("Khu vực sống", k.get("khu_vuc") or "", placeholder="VD Biên Hoà, Đồng Nai")

        st.markdown("##### 🏋️ Kinh nghiệm & thói quen tập")
        a, b = st.columns(2)
        kn = a.selectbox("Kinh nghiệm tập", [""] + KINH_NGHIEM, format_func=lambda x: x or "— Chọn —", index=([""] + KINH_NGHIEM).index(k.get("kinh_nghiem"))
                         if k.get("kinh_nghiem") in KINH_NGHIEM else 0)
        mdt = b.multiselect("Môn đã / đang tập", MON_DA_TAP, placeholder="Chọn một hoặc nhiều", default=[x for x in _ds(k.get("mon_da_tap")) if x in MON_DA_TAP])
        a, b = st.columns(2)
        bct = a.number_input("Số buổi / tuần có thể tập", 0, 7, int(float(k.get("buoi_co_the") or 0)))
        kg = b.multiselect("Khung giờ rảnh để tập", KHUNG_GIO, placeholder="Chọn một hoặc nhiều", default=[x for x in _ds(k.get("khung_gio")) if x in KHUNG_GIO])
        a, b = st.columns(2)
        cv = a.selectbox("Công việc hằng ngày", [""] + CONG_VIEC, format_func=lambda x: x or "— Chọn —", index=([""] + CONG_VIEC).index(k.get("cong_viec"))
                         if k.get("cong_viec") in CONG_VIEC else 0)
        gn = b.selectbox("Giấc ngủ trung bình", [""] + GIAC_NGU, format_func=lambda x: x or "— Chọn —", index=([""] + GIAC_NGU).index(k.get("giac_ngu"))
                         if k.get("giac_ngu") in GIAC_NGU else 0)

        st.markdown("##### 🎯 Mục tiêu")
        a, b = st.columns([2, 1])
        mt = a.text_input("Mục tiêu chính", k.get("muc_tieu") or "", placeholder="VD giảm mỡ bụng, khoẻ lưng, tăng cơ tay vai")
        f_can = "can_muc_tieu" if vai == "hlv" else "can_mong_muon"
        cmt = b.number_input("Cân mục tiêu (kg) — dùng cho lộ trình" if vai == "hlv" else "Cân nặng bạn mong muốn (kg)", 0.0, 250.0,
                             float(k.get(f_can) or (k.get("can_muc_tieu") if vai != "hlv" else 0) or 0), step=0.5)
        ly = st.text_input("Vì sao bạn muốn đạt mục tiêu này?", k.get("ly_do") or "",
                           placeholder="VD mặc vừa váy cưới tháng 3, chơi với con không bị mệt — động lực thật giúp bạn giữ cam kết")

        st.markdown("##### 🩺 Sức khoẻ (chỉ bạn và HLV xem)" if vai != "hlv" else "##### 🩺 Sức khoẻ")
        ct = st.text_area("Chấn thương / vùng đau", k.get("chan_thuong") or "", height=68, placeholder="VD đau lưng dưới, từng lật cổ chân phải")
        a, b = st.columns(2)
        bn = a.text_input("Bệnh nền", k.get("benh_nen") or "", placeholder="VD huyết áp, tiểu đường, không có")
        th = b.text_input("Thuốc đang dùng", k.get("thuoc") or "", placeholder="Không bắt buộc")

        st.markdown("##### 📞 Liên hệ khẩn cấp")
        a, b, c = st.columns(3)
        lht = a.text_input("Họ tên", k.get("lh_ten") or "")
        lhq = b.text_input("Quan hệ", k.get("lh_quan_he") or "", placeholder="VD chồng, mẹ")
        lhs = c.text_input("SĐT", k.get("lh_sdt") or "")
        ok = st.form_submit_button("💾 Lưu hồ sơ", type="primary", use_container_width=True)
    if ok:
        if not ten.strip():
            st.error("Nhập họ tên.")
            return
        k1 = {**k, "ho_ten": ten.strip(), "ngay_sinh": ns.isoformat() if ns else "", "gioi_tinh": gt, "chieu_cao": cc or "",
              "sdt": sdt.strip(), "email": em.strip(), "nghe_nghiep": ng.strip(), "khu_vuc": kv.strip(), "kinh_nghiem": kn,
              "mon_da_tap": mdt, "buoi_co_the": bct or "", "khung_gio": kg, "cong_viec": cv, "giac_ngu": gn, "muc_tieu": mt.strip(),
              f_can: cmt or "", "ly_do": ly.strip(), "chan_thuong": ct.strip(), "benh_nen": bn.strip(), "thuoc": th.strip(),
              "lh_ten": lht.strip(), "lh_quan_he": lhq.strip(), "lh_sdt": lhs.strip()}
        if store.save_client(k1, nguoi):
            st.toast("Đã lưu hồ sơ" + (" ✅ hoàn thành 100%" if phan_tram(k1) == 100 else f" — hoàn thành {phan_tram(k1)}%"))
            st.rerun()
        st.error("Chưa lưu được — thử lại.")


def tom_tat(k: dict) -> str:
    """Dòng tóm tắt cho HLV (tuổi, kinh nghiệm, công việc, giấc ngủ…)."""
    t = store.tuoi(k)
    x = [f"{t} tuổi" if t is not None else "", k.get("gioi_tinh") or "", f"{float(k['chieu_cao']):g} cm" if k.get("chieu_cao") else "",
         k.get("kinh_nghiem") or "", k.get("cong_viec") or "", f"ngủ {k['giac_ngu']}" if k.get("giac_ngu") else ""]
    return " · ".join(v for v in x if v)
