"""v3.1 — 🧠 Thấu hiểu khách: trang CHỈ HLV thấy (không có trong cổng khách, không có quyền nào bật cho khách)."""
from __future__ import annotations

import html
from datetime import date

import pandas as pd
import streamlit as st

from core import db, store, thau_hieu as th, ui

E = html.escape
S = st.session_state

CAU_HOI = [
    ("Lý do thật sự", "Nếu 3 tháng nữa đạt mục tiêu, điều gì trong cuộc sống của anh/chị sẽ khác đi?"),
    ("Trải nghiệm cũ", "Trước đây anh/chị đã từng tập ở đâu chưa? Điều gì làm anh/chị dừng lại?"),
    ("Rào cản", "Tuần nào là tuần khó nhất để đi tập? Thường vì chuyện gì?"),
    ("Cách động viên", "Khi tập mệt, anh/chị thích em thúc mạnh hay nhẹ nhàng động viên?"),
    ("Cách nhắn tin", "Anh/chị muốn em nhắn nhắc lịch / hỏi thăm nhiều hay ít?"),
    ("Thói quen", "Một ngày bình thường của anh/chị bắt đầu và kết thúc lúc mấy giờ? Ăn ngoài mấy bữa?"),
    ("Người xung quanh", "Ở nhà / công ty có ai cũng đang muốn tập hoặc giảm cân không?"),
    ("Hài lòng (hỏi mỗi 4–6 tuần)", "Từ 0–10, khả năng anh/chị giới thiệu em cho bạn bè là bao nhiêu? Điều gì làm điểm đó cao hơn?"),
]


def _ds() -> list[dict]:
    return [k for k in store.clients(ca_ngung=False) if (k.get("trang_thai") or "Đang tập") == "Đang tập"]


def trang(u: dict):
    ui.hero("CHỈ HLV THẤY", "🧠 Thấu hiểu khách",
            "Ghi lại tính cách, động lực, rào cản của từng khách → web gợi ý cách nói chuyện, lên giáo án, giữ chân và xin giới thiệu.")
    st.caption("🔒 Khách không thấy mục này. Đây là gợi ý dựa trên quan sát của anh, không phải trắc nghiệm hay chẩn đoán tâm lý — "
               "không chắc thì hỏi thẳng khách. Không ghi bệnh án, chuyện riêng tư nhạy cảm của khách vào đây.")
    DS = _ds()
    if not DS:
        st.info("Chưa có khách đang tập.")
        return
    t1, t2, t3 = st.tabs(["📋 Tổng quan cả lớp", "🧭 Từng khách", "🤝 Nguồn khách (giới thiệu)"])
    with t1:
        tong_quan(DS)
    with t2:
        tung_khach(DS, u)
    with t3:
        nguon_khach(DS, u)


# ------------------------------------------------------------------ tổng quan
def tong_quan(DS: list[dict]):
    hom = db.now_vn().date()
    rows, cao, san = [], 0, 0
    for k in DS:
        hs = th.ho_so(k["ma"])
        g = th.huong_dan(k, hs, hom)
        cao += g["nguy_co"] >= 60
        san += g["gt"] >= 60
        cc = g["cc"]
        rows.append({"Khách": k["ho_ten"], "🏢 Phòng": store.phong(k) or "—",
                     "Kiểu": th.PHONG_CACH[g["pc"]][0] if g["pc"] else "chưa ghi",
                     "Giai đoạn": th.GIAI_DOAN.get(hs.get("giai_doan"), "—"),
                     "Đi tập 3 tuần": f"{cc['xong']}/{cc['tong']}" if cc["tong"] else "—",
                     "Nguy cơ bỏ": f"{th.muc(g['nguy_co'])} ({g['nguy_co']})",
                     "Sẵn sàng giới thiệu": f"{th.muc(g['gt'])} ({g['gt']})",
                     "Việc nên làm trước": g["viec"][0] if g["viec"] else "✅ ổn",
                     "_nc": g["nguy_co"]})
    L = th.leads()
    ui.tiles([(cao, "Nguy cơ bỏ cao", "ưu tiên gọi / gặp tuần này"),
              (san, "Sẵn sàng giới thiệu", "nên xin giới thiệu"),
              (len(L), "Khách tiềm năng", f"{sum(x.get('trang_thai') == th.LEAD_TT[4] for x in L)} đã đăng ký"),
              (sum(1 for k in DS if th.ho_so(k['ma'])), "Đã có hồ sơ", f"/ {len(DS)} khách đang tập")])
    df = pd.DataFrame(rows).sort_values("_nc", ascending=False).drop(columns="_nc")
    st.dataframe(df, hide_index=True, use_container_width=True)
    st.caption("Nguy cơ bỏ & sẵn sàng giới thiệu là điểm 0–100 tính theo quy tắc đơn giản (đi tập, giai đoạn, rào cản, mức hài lòng, "
               "gói còn lại…) — dùng để biết nên chăm ai trước, không phải dự đoán chính xác.")


# ------------------------------------------------------------------ từng khách
def tung_khach(DS: list[dict], u: dict):
    from views.coach import _chon_khach
    k = _chon_khach(DS, "th")
    if not k:
        return
    ma, hom = k["ma"], db.now_vn().date()
    hs = th.ho_so(ma)
    a, d, b, c = st.tabs(["🧭 Hướng dẫn cho khách này", "📝 Bảng hỏi tính cách", "✍️ Ghi hồ sơ tính cách", "📓 Nhật ký quan sát"])
    with d:
        from views import khao_sat_ui as ksu
        if hs.get("ks"):
            st.success(f"Khách đã trả lời ngày {hs.get('ks_ngay', '')}.")
            ksu.ket_qua_hlv(hs)
        else:
            st.caption("Khách có thể tự làm ở trang 👤 Hồ sơ của khách, hoặc anh hỏi trực tiếp và chọn giúp ở đây.")
        with st.form(f"ks_hlv_{ma}"):
            ans = ksu.form(f"kshlv_{ma}", hs.get("ks"), "hlv")
            if st.form_submit_button("💾 Lưu bảng hỏi", type="primary"):
                if ksu.luu(ma, ans, u["name"]):
                    st.toast("Đã lưu — web cập nhật kiểu giao tiếp & gợi ý.")
                    st.rerun()
    with b:
        _form(k, hs, u)
    with a:
        _huong_dan(k, hs, hom)
    with c:
        _nhat_ky(k, u, hom)


def _form(k: dict, hs: dict, u: dict):
    ma = k["ma"]
    with st.expander("💬 Câu hỏi nên hỏi trong buổi tư vấn / lúc nghỉ giữa hiệp"):
        for t, q in CAU_HOI:
            st.markdown(f"**{t}:** {E(q)}")
    with st.form(f"th_f_{ma}"):
        st.markdown("**1. Dấu hiệu anh quan sát được** (tick những gì đúng)")
        cs = st.columns(2)
        dh = {f"dh{i}": cs[i % 2].checkbox(t, value=bool(hs.get(f"dh{i}")), key=f"th_dh{i}_{ma}") for i, (t, _) in enumerate(th.DAU_HIEU)}
        pcs = ["(để web tự tính)"] + list(th.PHONG_CACH)
        tay = st.selectbox("Hoặc anh tự chọn kiểu giao tiếp", pcs, format_func=lambda x: th.PHONG_CACH[x][0] if x in th.PHONG_CACH else x,
                           index=pcs.index(hs.get("phong_cach_tay")) if hs.get("phong_cach_tay") in pcs else 0)
        st.markdown("**2. Động lực**")
        x1, x2 = st.columns(2)
        dl = x1.multiselect("Khách tập vì", th.DONG_LUC, default=[x for x in hs.get("dong_luc", []) if x in th.DONG_LUC])
        noi = x2.slider("Động lực từ đâu?", 1, 10, int(hs.get("dong_luc_noi", 5)),
                        help="1 = chủ yếu bên ngoài (người khác bảo, sự kiện) · 10 = tự thích tập, tự giác")
        lds = st.text_input("Lý do thật sự (lời của khách)", hs.get("ly_do_sau", ""), placeholder="VD: muốn bế con không đau lưng; mặc lại váy cưới…")
        st.markdown("**3. Giai đoạn & rào cản**")
        y1, y2 = st.columns(2)
        gds = list(th.GIAI_DOAN)
        gd = y1.selectbox("Giai đoạn", gds, format_func=th.GIAI_DOAN.get, index=gds.index(hs["giai_doan"]) if hs.get("giai_doan") in gds else 0)
        rc = y2.multiselect("Rào cản", th.RAO_CAN, default=[x for x in hs.get("rao_can", []) if x in th.RAO_CAN])
        st.markdown("**4. Cách khách thích được động viên**")
        z1, z2 = st.columns(2)
        khen = z1.multiselect("Thích được khen kiểu", th.KHEN, default=[x for x in hs.get("khen", []) if x in th.KHEN])
        nhan = z2.selectbox("Tần suất nhắn tin", th.NHAN, index=th.NHAN.index(hs["nhan"]) if hs.get("nhan") in th.NHAN else 1)
        st.markdown("**5. Đời sống & mạng lưới** (để chăm sóc và xin giới thiệu đúng người)")
        w1, w2 = st.columns(2)
        st_ = w1.text_input("Sở thích / chủ đề khách hay nói", hs.get("so_thich", ""), placeholder="VD: du lịch, cà phê, con học lớp 3…")
        ml = w2.multiselect("Khách có mạng lưới nào", th.MANG_LUOI, default=[x for x in hs.get("mang_luoi", []) if x in th.MANG_LUOI])
        st.markdown("**6. Mức hài lòng**")
        v1, v2 = st.columns(2)
        hl_opts = ["chưa hỏi"] + [str(i) for i in range(11)]
        hl = v1.selectbox("Điểm 0–10 khách trả lời (câu hỏi giới thiệu)", hl_opts,
                          index=hl_opts.index(str(hs.get("hai_long"))) if str(hs.get("hai_long")) in hl_opts else 0)
        kq = v2.checkbox("Khách đã thấy / nói ra kết quả rõ ràng", value=bool(hs.get("da_thay_ket_qua")))
        gc = st.text_area("Ghi chú khác (điều khách thích / ghét, chuyện cần nhớ)", hs.get("ghi_chu", ""), height=80)
        if st.form_submit_button("💾 Lưu hồ sơ", type="primary"):
            moi = {**dh, "phong_cach_tay": tay if tay in th.PHONG_CACH else "", "dong_luc": dl, "dong_luc_noi": noi,
                   "ly_do_sau": lds.strip(), "giai_doan": gd, "rao_can": rc, "khen": khen, "nhan": nhan, "so_thich": st_.strip(),
                   "mang_luoi": ml, "hai_long": "" if hl == "chưa hỏi" else int(hl), "da_thay_ket_qua": kq, "ghi_chu": gc.strip()}
            if hl != "chưa hỏi" and str(hl) != str(hs.get("hai_long")):
                moi["ngay_hoi_hl"] = db.now_vn().date().isoformat()
            elif hs.get("ngay_hoi_hl"):
                moi["ngay_hoi_hl"] = hs["ngay_hoi_hl"]
            if th.luu(k["ma"], moi, u["name"]):
                st.toast("Đã lưu hồ sơ ✅")
                st.rerun()
            st.error("Lưu chưa được — thử lại.")


def _ds_html(items: list[str]) -> str:
    return "".join(f"<li>{E(x)}</li>" for x in items)


def _huong_dan(k: dict, hs: dict, hom: date):
    if not hs:
        st.info("Chưa có hồ sơ — vào tab ✍️ Ghi hồ sơ (mất khoảng 2 phút). Web vẫn tính sẵn chuyên cần & gói còn lại bên dưới.")
    g = th.huong_dan(k, hs, hom)
    xh = store.xung(k)[0]
    ui.tiles([(th.PHONG_CACH[g["pc"]][0].split(" ", 1)[1] if g["pc"] else "—", "Kiểu giao tiếp",
               "dấu hiệu anh tick + bảng hỏi" if hs.get("ks") else "từ dấu hiệu anh tick"),
              (th.muc(g["nguy_co"]), "Nguy cơ bỏ tập", "; ".join(g["ly_nc"][:2]) or "chưa thấy dấu hiệu"),
              (th.muc(g["gt"]), "Sẵn sàng giới thiệu", "; ".join(g["ly_gt"][:2]) or "—"),
              (f"{g['cc']['xong']}/{g['cc']['tong']}" if g["cc"]["tong"] else "—", "Đi tập 3 tuần qua", "buổi xong / buổi theo lịch")])
    ui.sec("✅ Việc nên làm tuần này")
    for v in g["viec"] or ["Khách đang ổn — giữ nhịp, ghi thêm quan sát khi có."]:
        st.markdown(f"- {E(v)}")
    from core import khao_sat as _ks
    for x in _ks.tom_tat(hs):
        st.markdown("- " + x)
    if hs.get("ly_do_sau"):
        st.markdown(f'<div class="hac-note">💡 Lý do thật sự của {E(xh)}: <b>“{E(hs["ly_do_sau"])}”</b> — nhắc lại câu này '
                    f"khi khách nản, và gắn mục tiêu buổi tập với nó.</div>", unsafe_allow_html=True)
    if g["pc"]:
        p = th.GOI_Y_PC[g["pc"]]
        ui.sec(f"{th.PHONG_CACH[g['pc']][0]}")
        st.caption(th.PHONG_CACH[g["pc"]][1])
        c1, c2 = st.columns(2)
        c1.markdown("**🗣 Cách nói chuyện**<ul>" + _ds_html(p["noi"]) + "</ul>", unsafe_allow_html=True)
        c2.markdown("**🏋️ Cách lên giáo án**<ul>" + _ds_html(p["tap"]) + "</ul>", unsafe_allow_html=True)
        st.markdown(f"**⛔ {E(p['tranh'])}**")
    if hs.get("giai_doan") in th.GOI_Y_GD:
        ui.sec(th.GIAI_DOAN[hs["giai_doan"]])
        st.markdown(E(th.GOI_Y_GD[hs["giai_doan"]]))
    if hs.get("rao_can"):
        ui.sec("🧱 Gỡ rào cản")
        for r in hs["rao_can"]:
            st.markdown(f"- **{E(r)}:** {E(th.GOI_Y_RC.get(r, ''))}")
    if hs.get("khen") or hs.get("nhan"):
        ui.sec("💬 Động viên & nhắn tin")
        st.markdown(f"- Khen: {E(', '.join(hs.get('khen') or ['chưa ghi']))}\n- Nhắn tin: {E(hs.get('nhan') or 'chưa ghi')}"
                    + (f"\n- Chủ đề bắt chuyện: {E(hs['so_thich'])}" if hs.get("so_thich") else ""))
    ui.sec("🤝 Giới thiệu khách")
    if g["gt"] >= 60:
        st.success("Thời điểm tốt để xin giới thiệu.")
    elif g["gt"] >= 30:
        st.info("Chưa vội — tạo thêm 1 khoảnh khắc ‘wow’ (kỷ lục, số đo đẹp) rồi hãy xin.")
    else:
        st.warning("Chưa nên xin — tập trung để khách hài lòng và thấy kết quả trước.")
    if g["pc"]:
        st.markdown(E(th.GOI_Y_PC[g["pc"]]["gt"]))
    if hs.get("mang_luoi"):
        st.caption("Mạng lưới của khách: " + ", ".join(hs["mang_luoi"]) + " — hỏi cụ thể ‘trong nhóm đó có ai đang muốn…?’ hiệu quả hơn hỏi chung chung.")


def _nhat_ky(k: dict, u: dict, hom: date):
    ma = k["ma"]
    st.caption("Ghi nhanh điều anh để ý trong buổi (tâm trạng, lời khách nói, chuyện gia đình, điều khách vui / phiền…). "
               "Đọc lại trước buổi tập để nhớ hỏi thăm.")
    with st.form(f"th_nk_{ma}", clear_on_submit=True):
        a, b = st.columns([1, 2])
        ng = a.date_input("Ngày", hom, format="DD/MM/YYYY")
        nh = b.selectbox("Loại", ["Quan sát", "Khách chia sẻ", "Khách khen / phàn nàn", "Ý tưởng chăm sóc", "Khách nhắc tới người quen"])
        nd = st.text_area("Nội dung", height=80)
        if st.form_submit_button("➕ Ghi") and nd.strip():
            th.ghi_nhat_ky(ma, ng, nd.strip(), nh, u["name"])
            st.rerun()
    for x in th.nhat_ky(ma)[:30]:
        d = store._d(x.get("ngay"))
        st.markdown(f"**{d:%d/%m/%Y}** · _{E(x.get('nhan', ''))}_ — {E(x.get('noi_dung', ''))}" if d else E(x.get("noi_dung", "")))


# ------------------------------------------------------------------ nguồn khách
def nguon_khach(DS: list[dict], u: dict):
    L = th.leads()
    mt = th.muc_tieu_nguon()
    by = {k["ma"]: k for k in store.clients()}
    dk = sum(x.get("trang_thai") == th.LEAD_TT[4] for x in L)
    a, b = st.columns([1, 2], vertical_alignment="bottom")
    so = a.number_input("🎯 Mục tiêu khách private năm tới", 0, 500, int(mt.get("so", 30) or 30), step=5)
    if b.button("Lưu mục tiêu"):
        db.append("DinhDuong", "th_muc_tieu", {"so": int(so)}, u["name"], "")
        st.rerun()
    st.progress(min(dk / so, 1.0) if so else 0.0, text=f"Đã đăng ký {dk}/{so} · đang theo dõi {len(L)} người")
    cs = st.columns(len(th.LEAD_TT))
    for c, t in zip(cs, th.LEAD_TT):
        c.metric(t, sum(x.get("trang_thai") == t for x in L))

    with st.expander("➕ Thêm khách tiềm năng", expanded=not L):
        with st.form("lead_new", clear_on_submit=True):
            x1, x2, x3 = st.columns(3)
            ten = x1.text_input("Tên")
            sdt = x2.text_input("SĐT / Zalo")
            ng_ = x3.selectbox("Ai giới thiệu", ["(không có)"] + [k["ma"] for k in DS],
                               format_func=lambda m: by[m]["ho_ten"] if m in by else m)
            y1, y2, y3 = st.columns(3)
            qh = y1.text_input("Quan hệ với người giới thiệu", placeholder="VD: đồng nghiệp, em gái")
            mtk = y2.text_input("Muốn tập để", placeholder="VD: giảm mỡ bụng sau sinh")
            ph = y3.selectbox("Phù hợp", ["Private studio", "Gold Gym", "Atlas", "Online", "Chưa rõ"])
            gc = st.text_input("Ghi chú")
            if st.form_submit_button("Lưu", type="primary") and ten.strip():
                th.luu_lead({"ten": ten.strip(), "sdt": sdt.strip(), "nguon_ma": "" if ng_.startswith("(") else ng_, "quan_he": qh.strip(),
                             "muc_tieu": mtk.strip(), "phu_hop": ph, "ghi_chu": gc.strip(), "trang_thai": th.LEAD_TT[0],
                             "ngay": db.now_vn().date().isoformat()}, u["name"])
                st.rerun()

    if L:
        df = pd.DataFrame([{"id": x["id"], "Tên": x.get("ten", ""), "SĐT": x.get("sdt", ""),
                            "Người giới thiệu": by.get(x.get("nguon_ma"), {}).get("ho_ten", "—"), "Quan hệ": x.get("quan_he", ""),
                            "Muốn tập để": x.get("muc_tieu", ""), "Phù hợp": x.get("phu_hop", ""),
                            "Trạng thái": x.get("trang_thai") or th.LEAD_TT[0], "Ghi chú": x.get("ghi_chu", ""),
                            "Ngày": x.get("ngay", "")} for x in L])
        ed = st.data_editor(df, hide_index=True, use_container_width=True, key="lead_ed", column_order=[c for c in df.columns if c != "id"],
                            disabled=["Người giới thiệu", "Ngày"],
                            column_config={"Trạng thái": st.column_config.SelectboxColumn(options=th.LEAD_TT),
                                           "Phù hợp": st.column_config.SelectboxColumn(options=["Private studio", "Gold Gym", "Atlas", "Online", "Chưa rõ"])})
        if st.button("💾 Lưu thay đổi danh sách"):
            goc = {x["id"]: x for x in L}
            n = 0
            for r in ed.to_dict("records"):
                o = goc[r["id"]]
                moi = {**o, "ten": r["Tên"], "sdt": r["SĐT"], "quan_he": r["Quan hệ"], "muc_tieu": r["Muốn tập để"],
                       "phu_hop": r["Phù hợp"], "trang_thai": r["Trạng thái"], "ghi_chu": r["Ghi chú"]}
                if any(str(moi.get(c)) != str(o.get(c)) for c in ("ten", "sdt", "quan_he", "muc_tieu", "phu_hop", "trang_thai", "ghi_chu")):
                    th.luu_lead(moi, u["name"])
                    n += 1
            st.toast(f"Đã lưu {n} dòng ✅")
            st.rerun()
        top = pd.Series([by.get(x.get("nguon_ma"), {}).get("ho_ten") for x in L if x.get("nguon_ma")]).value_counts()
        if len(top):
            st.caption("🏅 Khách giới thiệu nhiều nhất: " + ", ".join(f"{n} ({c})" for n, c in top.head(5).items())
                       + " — nhớ cảm ơn (buổi tập tặng, quà nhỏ, lời cảm ơn công khai nếu khách thích).")
    ui.note("Gợi ý xây nguồn khách cho private studio: (1) xin giới thiệu đúng lúc khách vừa có kết quả; (2) tặng ‘buổi tập đôi’ để khách dẫn bạn; "
            "(3) ghi lại mọi người quen khách nhắc tới ở tab 📝 Nhật ký; (4) chương trình cảm ơn rõ ràng cho người giới thiệu — "
            "quyết định mức thưởng là việc của anh, web chỉ đếm giúp.")
