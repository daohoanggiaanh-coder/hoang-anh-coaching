"""v3.4 — 📷 Quét phiếu InBody: HLV quét nhiều phiếu một lần (tự nhận khách theo tên trên phiếu) · khách tự quét phiếu của mình."""
from __future__ import annotations

from datetime import date

import pandas as pd
import streamlit as st

from core import db, store, tien_do as td, ui
from core import quet_inbody as qi

S = st.session_state
BO_QUA = "— bỏ qua phiếu này —"
COT = [("can_nang", "Cân (kg)"), ("pbf", "% mỡ"), ("smm", "Cơ SMM (kg)"), ("khoi_mo", "Mỡ (kg)"),
       ("mo_noi_tang", "Mỡ nội tạng"), ("bmr", "BMR"), ("diem_inbody", "Điểm")]


def _can_ai() -> bool:
    from core import llm
    if llm.is_online():
        return True
    st.warning("Chức năng quét cần khoá AI (đọc chữ trong ảnh). Cách thêm (miễn phí, ~3 phút):")
    st.markdown("1. Vào **aistudio.google.com** → đăng nhập Google → **Get API key** → **Create API key** → chép khoá.\n"
                "2. Vào **share.streamlit.io** → app *hoang-anh-coaching* → **⋮ → Settings → Secrets**.\n"
                "3. Thêm 1 dòng: `GEMINI_API_KEY = \"khoá vừa chép\"` → **Save** (app tự khởi động lại).\n\n"
                "Khoá là bí mật — anh tự dán vào Secrets, không gửi cho ai (kể cả Claude).")
    return False


def _doc(f) -> dict:
    from core import anh as A, llm, tu_van as tv
    raw = f.getvalue()
    try:
        r = tv.read_inbody(A.shrink(raw, 1800))
    except llm.LLMError as e:
        return {"_loi": str(e)}
    return r or {"_loi": "Không đọc được số nào — chụp lại thẳng, đủ sáng, rõ phần số."}


def trang(u: dict):
    """Trang HLV: tải nhiều ảnh phiếu → AI đọc → đoán khách → xác nhận → lưu tất cả."""
    from core import anh as A
    ui.hero("QUÉT PHIẾU INBODY", "Chụp nhiều phiếu một lần · web tự đọc số và nhận khách · anh xác nhận rồi lưu", "")
    bao_cao()
    if not _can_ai():
        return
    DS = [k for k in store.clients() if not k.get("xoa")]
    hom = db.now_vn().date()
    a, b, c = st.columns(3)
    PH = ["(tất cả)"] + store.PHONG_TAP
    ph = a.selectbox("Ưu tiên khách ở phòng", PH, index=PH.index("Atlas"), key="qib_ph",
                     help="Phiếu chỉ ghi tên gọi (vd “Lan”) mà có 2 khách trùng → ưu tiên khách phòng này.")
    dot = b.selectbox("Đợt", list(td.DOT), index=list(td.DOT).index("tuan"), format_func=td.DOT.get, key="qib_dot")
    nd = c.date_input("Ngày đo (khi phiếu không in ngày)", hom, max_value=hom, format="DD/MM/YYYY", key="qib_nd")
    FS = st.file_uploader("Ảnh phiếu InBody (chọn nhiều ảnh cùng lúc · điện thoại: chụp hoặc chọn từ thư viện)",
                          type=["jpg", "jpeg", "png", "webp"], accept_multiple_files=True, key=f"qib_f{S.get('qib_v', 0)}")
    st.caption("Chụp thẳng, đủ sáng, thấy rõ tên và các con số. Mỗi phiếu AI đọc mất khoảng 10–30 giây.")
    if FS and st.button(f"🔍 Đọc {len(FS)} phiếu", type="primary", use_container_width=True):
        kq, thanh = [], st.progress(0.0, "Đang đọc…")
        for i, f in enumerate(FS):
            thanh.progress(i / len(FS), f"Đang đọc phiếu {i + 1}/{len(FS)}: {f.name}")
            r = _doc(f)
            ma, diem = qi.khop_khach(r.get("ten", ""), DS, None if ph == PH[0] else ph)
            kq.append({"file": f.name, "anh": A.shrink(f.getvalue(), 1600), "r": r, "ma": ma, "diem": diem})
        thanh.empty()
        S["qib_kq"] = kq
        st.rerun()
    KQ = S.get("qib_kq") or []
    if not KQ:
        return
    loi = [x for x in KQ if "_loi" in x["r"]]
    for x in loi:
        st.error(f"{x['file']}: {x['r']['_loi']}")
    OK = [x for x in KQ if "_loi" not in x["r"]]
    if not OK:
        return
    nhan = {}
    for k in sorted(DS, key=lambda k: (store.phong(k) != ph, k.get("ho_ten", ""))):
        t = f"{k.get('ho_ten', '')} · {store.phong(k) or 'chưa xếp phòng'}"
        nhan[t if t not in nhan else f"{t} · {k['ma']}"] = k["ma"]
    theo_ma = {v: t for t, v in nhan.items()}
    df = pd.DataFrame([{"Phiếu": x["file"], "Tên trên phiếu": x["r"].get("ten", ""),
                        "Khách": theo_ma.get(x["ma"], BO_QUA),
                        "Ngày đo": date.fromisoformat(x["r"]["ngay_do"]) if x["r"].get("ngay_do") else nd,
                        **{t: x["r"].get(c) for c, t in COT}} for x in OK])
    st.markdown("**Kiểm tra lại trước khi lưu** — AI có thể đọc nhầm số hoặc đoán sai khách. Sửa thẳng trong bảng; "
                f"khách chưa nhận ra được để “{BO_QUA}” → chọn tay.")
    ED = st.data_editor(df, hide_index=True, use_container_width=True, key=f"qib_ed{S.get('qib_v', 0)}",
                        disabled=["Phiếu", "Tên trên phiếu"],
                        column_config={"Khách": st.column_config.SelectboxColumn("Khách", options=[BO_QUA] + list(nhan), required=True, width="medium"),
                                       "Ngày đo": st.column_config.DateColumn("Ngày đo", format="DD/MM/YYYY", max_value=hom),
                                       **{t: st.column_config.NumberColumn(t, format="%.1f") for _, t in COT}})
    with st.expander("🖼️ Xem ảnh từng phiếu để đối chiếu"):
        cs = st.columns(3)
        for i, x in enumerate(OK):
            try:
                cs[i % 3].image(x["anh"], caption=x["file"], use_container_width=True)
            except Exception:  # noqa: BLE001 — ảnh định dạng lạ: bỏ qua phần xem trước
                cs[i % 3].caption(f"{x['file']} (không xem trước được)")
    chon = [i for i, r in ED.iterrows() if r["Khách"] != BO_QUA]
    trung = ED.loc[chon, "Khách"].duplicated(keep=False) & ED.loc[chon, "Ngày đo"].duplicated(keep=False) if chon else []
    if len(chon) and any(trung):
        st.warning("Có 2 phiếu cùng khách cùng ngày — phiếu sau sẽ ghi đè phiếu trước. Kiểm tra lại cột Khách.")
    a, b = st.columns([3, 1])
    if a.button(f"💾 Lưu {len(chon)} phiếu", type="primary", disabled=not chon, use_container_width=True):
        KH = {k["ma"]: k for k in DS}
        bao, thanh = [], st.progress(0.0, "Đang lưu…")
        for j, i in enumerate(chon):
            r, x = ED.loc[i], OK[i]
            thanh.progress(j / len(chon), f"Đang lưu {r['Khách']}")
            ma = nhan[r["Khách"]]
            vals = {**{c: x["r"].get(c) for c in ("chieu_cao", "gioi_tinh", "nuoc", "protein", "khoang_chat", "tuoi_may")},
                    **{c: (None if pd.isna(r[t]) else float(r[t])) for c, t in COT}}
            ngay = r["Ngày đo"] if isinstance(r["Ngày đo"], date) else pd.to_datetime(r["Ngày đo"]).date()
            up = db.upload_images({"inbody": x["anh"]}, f"HAC_{ma}_")
            lam = qi.luu(KH[ma], ngay, dot, vals, u, (up or {}).get("inbody"))
            bao.append(f"✅ **{r['Khách']}** ({ngay:%d/%m}): " + (", ".join(lam) if lam else "không có số để lưu"))
        thanh.empty()
        S["qib_kq"], S["qib_v"] = None, S.get("qib_v", 0) + 1
        S["qib_bao"] = bao
        st.rerun()
    if b.button("Huỷ", use_container_width=True):
        S["qib_kq"], S["qib_v"] = None, S.get("qib_v", 0) + 1
        st.rerun()


def bao_cao():
    if S.get("qib_bao"):
        st.success("Đã lưu:  \n" + "  \n".join(S.pop("qib_bao")))


def quet_mot(k: dict, nguoi: str, vai: str = "khach"):
    """Khách (hoặc HLV) tự quét phiếu của 1 khách → xem số → lưu."""
    from core import anh as A, llm
    if not llm.is_online():
        return
    ma, key = k["ma"], f"q1_{k['ma']}_{vai}"
    with st.expander("📷 Có phiếu InBody? Chụp phiếu để web tự điền số"):
        f = st.file_uploader("Ảnh phiếu InBody", type=["jpg", "jpeg", "png", "webp"], key=f"{key}_f{S.get(key + 'v', 0)}")
        if f is not None and st.button("🔍 Đọc phiếu", key=key + "b"):
            with st.spinner("Đang đọc phiếu (10–30 giây)…"):
                r = _doc(f)
            if "_loi" in r:
                st.error(r["_loi"])
            else:
                S[key] = {"r": r, "anh": A.shrink(f.getvalue(), 1600)}
        x = S.get(key)
        if not x:
            return
        r, hom = x["r"], db.now_vn().date()
        st.markdown("**Web đọc được:** " + " · ".join(f"{t} **{r[c]:g}**" for c, t in COT if r.get(c) is not None))
        if r.get("ten"):
            st.caption(f"Tên trên phiếu: {r['ten']} — kiểm tra đúng phiếu của {'bạn' if vai == 'khach' else k.get('ho_ten', '')}.")
        nd = st.date_input("Ngày đo", date.fromisoformat(r["ngay_do"]) if r.get("ngay_do") else hom, max_value=hom,
                           format="DD/MM/YYYY", key=key + "nd")
        st.caption("Số nào web đọc sai thì bấm Huỷ, chụp lại rõ hơn — hoặc nhập tay ở form bên dưới.")
        a, b = st.columns(2)
        if a.button("💾 Lưu kết quả này", type="primary", key=key + "luu", use_container_width=True):
            dot = "dau_khoa" if td.so_do(ma).empty else "tuan"
            up = db.upload_images({"inbody": x["anh"]}, f"HAC_{ma}_")
            lam = qi.luu(k, nd, dot, r, {"name": nguoi}, (up or {}).get("inbody"))
            S.pop(key, None)
            S[key + "v"] = S.get(key + "v", 0) + 1
            st.toast("Đã lưu: " + ", ".join(lam) if lam else "Không có số để lưu")
            st.rerun()
        if b.button("Huỷ", key=key + "huy", use_container_width=True):
            S.pop(key, None)
            S[key + "v"] = S.get(key + "v", 0) + 1
            st.rerun()
