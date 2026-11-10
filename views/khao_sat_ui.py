"""v3.6 — 📝 Bảng hỏi tính cách & động lực: dùng chung cho buổi F1, trang Thấu hiểu (HLV hỏi) và trang Hồ sơ của khách."""
from __future__ import annotations

import streamlit as st

from core import db, khao_sat as ks, thau_hieu as th


def form(key: str, ans: dict | None = None, vai: str = "khach") -> dict:
    """Vẽ bảng hỏi, trả về câu trả lời hiện tại. vai='khach' → xưng 'bạn'; 'hlv' → nhắc HLV đọc cho khách."""
    ans = dict(ans or {})
    if vai == "hlv":
        st.caption("Đọc từng câu cho khách chọn — chọn đáp án gần đúng nhất, không có đúng / sai.")
    else:
        st.caption("Khoảng 2 phút · không có đáp án đúng / sai — chọn ý gần với bạn nhất để HLV hiểu và đồng hành cùng bạn tốt hơn.")
    out = {}
    for i, (q, opts) in enumerate(ks.CAU_PC):
        v = ans.get(f"pc{i}")
        r = st.radio(f"**{i + 1}. {q}**", opts, index=v if isinstance(v, int) and 0 <= v < 4 else None, key=f"{key}_pc{i}")
        out[f"pc{i}"] = opts.index(r) if r is not None else None
    n = len(ks.CAU_PC)
    out["dong_luc"] = st.multiselect(f"**{n + 1}. Lý do sâu xa khiến bạn muốn tập lúc này**", th.DONG_LUC,
                                     default=[x for x in ans.get("dong_luc") or [] if x in th.DONG_LUC], key=f"{key}_dl")
    ops = [x for x, _ in ks.DONG_LUC_NOI]
    r = st.radio(f"**{n + 2}. Bạn tập chủ yếu vì…**", ops, index=ans.get("noi") if isinstance(ans.get("noi"), int) else None, key=f"{key}_noi")
    out["noi"] = ops.index(r) if r is not None else None
    ops = [x for x, _ in ks.DUY_TRI]
    r = st.radio(f"**{n + 3}. Trước đây bạn duy trì tập luyện được bao lâu?**", ops,
                 index=ans.get("duy_tri") if isinstance(ans.get("duy_tri"), int) else None, key=f"{key}_dt")
    out["duy_tri"] = ops.index(r) if r is not None else None
    out["rao_can"] = st.multiselect(f"**{n + 4}. Điều có thể cản trở bạn tập đều**", th.RAO_CAN,
                                    default=[x for x in ans.get("rao_can") or [] if x in th.RAO_CAN], key=f"{key}_rc")
    out["nhan"] = st.radio(f"**{n + 5}. Bạn muốn HLV nhắn tin hỏi thăm…**", th.NHAN,
                           index=th.NHAN.index(ans["nhan"]) if ans.get("nhan") in th.NHAN else None, key=f"{key}_nh")
    out["mang_luoi"] = st.multiselect(f"**{n + 6}. Bạn thường sinh hoạt cùng nhóm nào?**", th.MANG_LUOI,
                                      default=[x for x in ans.get("mang_luoi") or [] if x in th.MANG_LUOI], key=f"{key}_ml")
    out["chia_se"] = st.radio(f"**{n + 7}. Khi có kết quả tốt, bạn có muốn chia sẻ hành trình của mình?**", ks.CHIA_SE,
                              index=ks.CHIA_SE.index(ans["chia_se"]) if ans.get("chia_se") in ks.CHIA_SE else None, key=f"{key}_cs")
    out["ly_do_sau"] = st.text_input(f"**{n + 8}. Nếu 3 tháng nữa đạt mục tiêu, điều gì trong cuộc sống của bạn sẽ khác đi?**",
                                     ans.get("ly_do_sau", ""), key=f"{key}_ld", placeholder="VD: bế con không đau lưng, tự tin mặc đồ bơi…")
    out["so_thich"] = st.text_input(f"**{n + 9}. Sở thích / chủ đề bạn hay nói chuyện**", ans.get("so_thich", ""), key=f"{key}_st",
                                    placeholder="VD: du lịch, cà phê, bóng đá, con cái…")
    return {k: v for k, v in out.items() if v not in (None, "", [])}


def ket_qua_hlv(hs: dict):
    """Tóm tắt kết quả cho HLV (không hiện cho khách)."""
    if not hs.get("ks"):
        return
    d = hs.get("ks_diem") or {}
    st.markdown(" · ".join(f"{th.PHONG_CACH[p][0]} **{d.get(p, 0)}**" for p in ks.PC if p in th.PHONG_CACH))
    for x in ks.tom_tat(hs):
        st.markdown("- " + x)


def luu(ma: str, ans: dict, nguoi: str) -> bool:
    hs = th.ho_so(ma)
    return th.luu(ma, ks.ap_vao_ho_so(hs, ans, db.now_vn().date().isoformat()), nguoi)


def cho_khach(k: dict):
    """Trang Hồ sơ của khách: khách tự làm bảng hỏi (kết quả phân tích chỉ HLV thấy)."""
    hs = th.ho_so(k["ma"])
    xong = bool(hs.get("ks"))
    with st.expander("📝 Bảng hỏi 2 phút — giúp HLV hiểu bạn" + (" ✅ đã làm" if xong else " (chưa làm)"), expanded=not xong):
        with st.form(f"ks_kh_{k['ma']}"):
            ans = form(f"kskh_{k['ma']}", hs.get("ks"), "khach")
            if st.form_submit_button("💾 Gửi cho HLV", type="primary"):
                if luu(k["ma"], ans, k.get("ho_ten", "")):
                    st.success("Cảm ơn bạn! HLV sẽ dựa vào đây để lên giáo án và cách đồng hành phù hợp với bạn.")
                else:
                    st.error("Chưa lưu được — thử lại sau ít phút.")
