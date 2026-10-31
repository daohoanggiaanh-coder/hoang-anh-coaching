# Hoàng Anh Coaching v1.0 (2026-10-31) — cổng khách: chỉ đọc / ghi dữ liệu của đúng khách đang đăng nhập
from __future__ import annotations

from datetime import timedelta

import pandas as pd
import streamlit as st

from core import auth, db, giao_an as ga, store, tien_do as td, ui
from views import common as C


def _k() -> dict:
    u = auth.current_user()
    if u and u.get("role") == "coach" and st.session_state.get("_xem_nhu"):     # HLV đang "xem như khách"
        k = store.client(st.session_state["_xem_nhu"])
        if k:
            return k
    k = store.client(u["ma_kh"]) if u and u.get("role") == "client" else None
    if not k:
        st.error("Phiên đăng nhập hết hạn — đăng nhập lại.")
        auth.logout()
        st.stop()
    return k


def _ten(k: dict) -> str:
    goi, _ = store.xung(k)
    t = goi if goi != "bạn" else k["ho_ten"].split()[-1]
    return t[:1].upper() + t[1:]


def trang_chu():
    k = _k()
    q = store.quyen(k)
    ma = k["ma"]
    hom = db.now_vn().date()
    H = store.hens(ma)
    B = store.buoi([k], hom, hom + timedelta(days=13), H)
    sap = [b for b in B if b["trang_thai"] == "hen"]
    L = ga.logs(ma)
    SD, CAN = td.so_do(ma), td.can_ngay(ma)
    DAU, MOI = td.dau_khoa(SD), td.moi_nhat(SD, CAN)
    con, da = store.con_lai(k, H), store.da_tap(k, H)
    ui.hero("HÀNH TRÌNH CỦA BẠN", f"Chào {_ten(k)} 👋",
            (f"Mục tiêu: {ui.E(k['muc_tieu'])}" if k.get("muc_tieu") else "Mỗi buổi tập là một bước gần hơn tới mục tiêu.")
            + (f" · buổi tới: <b>{store.THU[sap[0]['ngay'].weekday()]} {sap[0]['ngay']:%d/%m} lúc {store.gio_s(sap[0]['gio'])}</b>"
               if sap and q["lich"] else ""))
    can_s, ch_s = "—", ""
    if MOI and MOI.get("can_nang"):
        can_s = f"{MOI['can_nang']:g} kg"
        if DAU and DAU.get("can_nang"):
            ch = round(MOI["can_nang"] - DAU["can_nang"], 1)
            ch_s = f"{ch:+g} kg từ đầu khoá" if ch else ""
    pt = td.tien_do_can(DAU.get("can_nang") if DAU else None, MOI.get("can_nang") if MOI else None, k.get("can_muc_tieu"))
    cn = store.con_ngay(k, hom)
    tl = []
    if q["lich"]:
        tl.append((str(da), "buổi đã tập", f"còn {con} buổi trong gói" if con is not None else (f"gói còn {cn} ngày" if cn is not None else "")))
    if q["can"] or q["so_do"]:
        tl += [(can_s, "cân hiện tại", ch_s),
               (f"{pt}%" if pt is not None else "—", "tới mục tiêu cân", f"mục tiêu {k['can_muc_tieu']} kg" if k.get("can_muc_tieu") else "")]
    if q["ghi_buoi"]:
        tl.append((str(ga.chuoi_tuan(L, hom)), "tuần liên tiếp", "có ghi buổi tập"))
    if tl:
        ui.tiles(tl)
    a, b = st.columns([1, 1]) if q["lich"] and q["so_ta"] else (st.container(), st.container())
    if q["lich"]:
        with a:
            ui.sec("Lịch 2 tuần tới")
            if not sap:
                st.caption("Chưa có buổi hẹn — nhắn HLV để xếp lịch.")
            for x in sap[:8]:
                st.markdown(f'<div class="hac-b"><span class="t">{store.gio_s(x["gio"])}</span><span class="n">'
                            f'{store.THU[x["ngay"].weekday()]} · {x["ngay"]:%d/%m}</span><span class="m">{ui.E(x.get("dia_diem") or "")}'
                            f'{" · hôm nay" if x["ngay"] == hom else ""}</span></div>', unsafe_allow_html=True)
    if q["so_ta"]:
        with b:
            ui.sec("Kỷ lục gần đây")
            ls = ga.lich_su_bai(ma, L)
            if ls.empty:
                st.caption("Ghi buổi tập ở mục 🏋️ Tập luyện để thấy kỷ lục.")
            else:
                kl = ga.ky_luc(ls).sort_values("ngay", ascending=False).head(5)
                for _, r in kl.iterrows():
                    st.markdown(f'<div class="hac-ex"><div class="n">{ui.E(r["bai"])}</div><div class="m">{r["top_kg"]:g} kg × '
                                f'{int(r["top_lan"])} · 1RM ước tính {r["e1rm"]:g} kg · {r["ngay"]:%d/%m}</div></div>', unsafe_allow_html=True)
    if len(CAN) >= 2 and q["can"]:
        ui.sec("Cân nặng")
        C.bieu_do_can(k, CAN, 260)


def tap():
    k = _k()
    ui.hero("TẬP LUYỆN", "Giáo án & số tạ", "Xem bài HLV soạn, ghi kg × lần từng hiệp, hoặc tự tạo plan khi tập một mình.")
    C.tap_luyen(k, "khach", k["ho_ten"], store.quyen(k))


def an():
    k = _k()
    ui.hero("DINH DƯỠNG", "Thực đơn của bạn", "Tính riêng theo cơ thể, lịch tập và mục tiêu — ngày tập ăn nhiều hơn ngày nghỉ.")
    q = store.quyen(k)
    if not q["thuc_don"]:
        st.info("Mục thực đơn HLV chưa mở cho bạn.")
        return
    C.dinh_duong(k, "khach", k["ho_ten"], q)


def tien_do():
    k = _k()
    ma = k["ma"]
    q = store.quyen(k)
    ui.hero("TIẾN ĐỘ", "Cân & số đo", "Cân mỗi sáng, xem đường trung bình 7 ngày — đừng lo dao động từng ngày.")
    CAN, SD = td.can_ngay(ma), td.so_do(ma)
    if q["can"]:
        C.nhap_can(k, k["ho_ten"], CAN, "kh")
        C.bieu_do_can(k, CAN)
    if not q["so_do"]:
        return
    DAU, MOI = td.dau_khoa(SD), td.moi_nhat(SD, CAN)
    if DAU and MOI:
        ui.sec("Số đo: đầu khoá → hiện tại")
        ss = td.so_sanh(DAU, MOI)
        if ss:
            st.dataframe(pd.DataFrame([{"Chỉ số": x["ten"], "Đầu khoá": f"{x['dau']:g} {x['dv']}", "Hiện tại": f"{x['moi']:g} {x['dv']}",
                                        "Thay đổi": f"{'✅' if x['tot'] else '⚠️' if x['tot'] is False else '➖'} {x['chenh']:+g} {x['dv']}"}
                                       for x in ss]), hide_index=True, use_container_width=True)
    if len(SD):
        with st.expander(f"Tất cả lần đo ({len(SD)})"):
            bang = SD.copy()
            bang["dot"] = bang["dot"].map(lambda x: td.DOT.get(x, x))
            st.dataframe(bang.rename(columns={"ngay": "Ngày", "dot": "Đợt", "ghi_chu": "Ghi chú",
                                              **{c: f"{t}{f' ({d})' if d else ''}" for c, t, d, _ in td.CHI_SO}}).dropna(axis=1, how="all"),
                         hide_index=True, use_container_width=True)
    ANH = td.anh(ma)
    if ANH:
        ui.sec("Ảnh trước / hiện tại")
        IMG = db.get_images([v["id"] for v in ANH])
        d0, d1 = td.bo_anh(ANH, True), td.bo_anh(ANH, False)
        for nhan, bo in (("Đầu tiên", d0), ("Mới nhất", d1)):
            st.markdown(f"**{nhan}**")
            cs = st.columns(3)
            for i, g in enumerate(td.GOC):
                v = bo.get(g)
                if v and v["id"] in IMG:
                    cs[i].image(IMG[v["id"]], caption=f"{td.GOC[g]} · {pd.Timestamp(v['ngay']):%d/%m/%Y}", use_container_width=True)
            if d0 == d1:
                break


def tai_khoan():
    k = _k()
    u = auth.current_user()
    ui.hero("TÀI KHOẢN", k["ho_ten"], f"Tên đăng nhập: <b>{ui.E(u['username'])}</b>")
    with st.form("doi_mk"):
        st.markdown("**Đổi mật khẩu**")
        cu = st.text_input("Mật khẩu hiện tại", type="password")
        m1 = st.text_input("Mật khẩu mới (ít nhất 6 ký tự)", type="password")
        m2 = st.text_input("Nhập lại mật khẩu mới", type="password")
        if st.form_submit_button("Đổi mật khẩu", type="primary"):
            acc = auth.accounts().get(u["username"]) or {}
            if not auth.check_pw(cu, acc.get("salt", ""), acc.get("hash", "")):
                st.error("Mật khẩu hiện tại chưa đúng.")
            elif m1 != m2:
                st.error("Hai lần nhập mật khẩu mới chưa khớp.")
            else:
                ok, loi = auth.save_account(k["ma"], u["username"], m1, k["ho_ten"], cu=acc)
                if ok:
                    auth.set_user(u)                    # cấp vé mới theo mật khẩu mới
                    st.success("Đã đổi mật khẩu.")
                else:
                    st.error(loi)
    if st.button("Đăng xuất"):
        auth.logout()
        st.rerun()
    st.caption("📲 Dùng như app: mở trang này trên điện thoại → Chia sẻ (iPhone) hoặc ⋮ (Android) → Thêm vào màn hình chính.")
