# Hoàng Anh Coaching v2.1 (2026-11-05) — bản đồ cơ thể tô màu theo volume tuần + đánh giá theo mục tiêu + kiến thức volume cho HLV.
from __future__ import annotations

import html
import re
from datetime import timedelta

import pandas as pd
import streamlit as st

from core import db, ga_atlas as ga, ui, volume as vo

E = html.escape
S = st.session_state

# ------------------------------------------------------------------ hình người (viewBox 200 × 420, nửa trái, phải lật gương)
_TRUOC = {
    "lung_giua": ["M92 58 L74 70 L92 69 Z"],
    "vai_giua": ["M66 70 Q50 74 51 98 L59 99 Q60 82 66 70 Z"],
    "vai_truoc": ["M66 70 Q78 70 80 80 L70 99 L59 99 Q60 82 66 70 Z"],
    "nguc": ["M80 78 Q90 73 99 76 L99 108 Q86 113 74 104 Q71 96 80 78 Z"],
    "tay_truoc": ["M53 102 L68 102 Q71 121 66 142 L55 142 Q50 121 53 102 Z"],
    "bung": ["M87 113 L99 113 L99 186 L89 186 Q85 150 87 113 Z"],
    "lien_suon": ["M74 108 L86 113 Q84 150 88 186 L81 190 Q72 160 74 108 Z"],
    "dui_truoc": ["M76 204 Q87 199 95 207 L95 282 Q90 300 82 301 Q71 262 76 204 Z"],
    "khep_dui": ["M95 207 L99 205 L99 258 L95 276 Z"],
    "bap_chan": ["M79 316 Q88 309 95 316 L93 372 L84 374 Q76 344 79 316 Z"],
}
_SAU = {
    "lung_giua": ["M100 54 L76 70 L90 96 L100 124 Z"],
    "vai_sau": ["M66 70 Q50 74 51 98 L66 94 Q72 80 78 70 Z"],
    "xo": ["M78 76 L90 98 L99 128 L97 154 Q83 144 75 116 Q72 94 78 76 Z"],
    "tay_sau": ["M53 100 L68 100 Q71 121 66 142 L55 142 Q50 121 53 100 Z"],
    "lung_duoi": ["M89 150 L99 154 L99 188 L86 188 Z"],
    "mong": ["M76 190 Q99 184 99 196 L99 238 Q86 247 75 234 Q71 210 76 190 Z"],
    "dui_sau": ["M76 242 Q88 249 97 242 L95 300 L83 302 Q74 272 76 242 Z"],
    "bap_chan": ["M79 316 Q89 306 96 316 L94 360 L84 370 Q75 340 79 316 Z"],
}
_NEN = [  # phần không tô, nửa trái (đầu, cổ, cẳng tay, hông, gối, bàn chân) — lật gương khi vẽ
    "M100 12 Q84 12 84 34 Q84 52 100 54 Z", "M92 52 L100 52 L100 62 L92 62 Z",
    "M54 145 L67 145 L64 192 L53 192 Z", "M81 188 L100 188 L100 204 L76 204 Z",
    "M80 302 L95 302 L95 314 L80 314 Z", "M83 374 L94 374 L96 390 L78 390 Z",
]


def _lat(d: str) -> str:
    """Lật gương 1 path qua trục x = 100."""
    return re.sub(r"(-?\d+(?:\.\d+)?) (-?\d+(?:\.\d+)?)", lambda m: f"{200 - float(m.group(1)):g} {m.group(2)}", d)


def _hinh(regions: dict, rows: dict, dx: int, nhan: str) -> str:
    out = [f'<g transform="translate({dx},0)">']
    for d in _NEN:
        for p in (d, _lat(d)):
            out.append(f'<path d="{p}" fill="#F0EBE1" stroke="#E2DACB" stroke-width=".8"/>')
    for co, ds in regions.items():
        r = rows.get(co)
        mau = vo.TRANG_THAI[r["tt"]][1] if r else "#E7E1D4"
        tip = f"{vo.CO[co][0]}: {r['hiep']:g} hiệp / tuần · {vo.TRANG_THAI[r['tt']][0]}" if r else vo.CO[co][0]
        vien = ' stroke="#C8A24A" stroke-width="2.2"' if r and r["uu_tien"] else ' stroke="rgba(0,0,0,.18)" stroke-width=".6"'
        for d in ds:
            for p in (d, _lat(d)):
                out.append(f'<path d="{p}" fill="{mau}"{vien}><title>{E(tip)}</title></path>')
    out.append(f'<text x="100" y="410" text-anchor="middle" font-size="11" font-weight="800" fill="#8b8577" '
               f'letter-spacing="1.5">{nhan}</text></g>')
    return "".join(out)


def ban_do(rows: list[dict]) -> str:
    R = {r["co"]: r for r in rows}
    so = []
    for co, (x, y, side) in {"nguc": (88, 94, 0), "bung": (93, 150, 0), "dui_truoc": (85, 250, 0), "vai_giua": (52, 86, 0),
                             "tay_truoc": (60, 122, 0), "xo": (84, 116, 1), "mong": (86, 216, 1), "dui_sau": (86, 272, 1),
                             "tay_sau": (60, 122, 1), "lung_giua": (100, 84, 1)}.items():
        r = R.get(co)
        if r and r["hiep"] > 0:
            so.append(f'<text x="{x + side * 210}" y="{y}" text-anchor="middle" font-size="10" font-weight="800" fill="#fff" '
                      f'style="paint-order:stroke;stroke:rgba(0,0,0,.45);stroke-width:2px">{r["hiep"]:g}</text>')
    return ('<svg viewBox="0 0 410 420" style="width:100%;max-width:520px;display:block;margin:auto">'
            + _hinh(_TRUOC, R, 0, "MẶT TRƯỚC") + _hinh(_SAU, R, 210, "MẶT SAU") + "".join(so) + "</svg>")


def chu_giai() -> str:
    return '<div style="display:flex;flex-wrap:wrap;gap:6px 14px;font-size:.78rem;margin:4px 0 10px">' + "".join(
        f'<span><i style="display:inline-block;width:12px;height:12px;border-radius:3px;background:{m};vertical-align:-2px;margin-right:4px"></i>{t}</span>'
        for k, (t, m) in vo.TRANG_THAI.items() if k != "na") + \
        '<span><i style="display:inline-block;width:12px;height:12px;border-radius:3px;border:2px solid #C8A24A;vertical-align:-2px;margin-right:4px"></i>Nhóm ưu tiên</span></div>'


# ------------------------------------------------------------------ trang
def trang(k: dict, vai: str, nguoi: str):
    ma = k["ma"]
    hlv = vai == "hlv"
    g = ga.current(ma)
    cd = vo.cai_dat(ma)
    lv = cd["trinh_do"] if cd["trinh_do"] is not None else (g or {}).get("trinh_do", 0)
    td = vo.nhom_td(lv)
    goal = (g or {}).get("muc_tieu", "giam_mo")
    uu = cd["uu_tien"]
    if hlv:
        with st.expander("🎯 Mục tiêu hình thể & trình độ của khách", expanded=not uu):
            with st.form(f"vol_cd_{ma}"):
                a, b = st.columns([2, 1])
                uu_m = a.multiselect("Ưu tiên (chọn 1–2)", list(vo.UU_TIEN), default=uu, format_func=lambda x: vo.UU_TIEN[x][0],
                                     placeholder="Chọn mục tiêu")
                lv_m = b.selectbox("Trình độ tập", range(len(ga.LEVELS)), index=int(lv or 0), format_func=lambda i: ga.LEVELS[i])
                if st.form_submit_button("💾 Lưu", type="primary"):
                    if vo.luu_cai_dat(ma, {"uu_tien": uu_m, "trinh_do": lv_m}, nguoi):
                        st.toast("Đã lưu")
                        st.rerun()
    a, b = st.columns([2, 1])
    hom = db.now_vn().date()
    t2_nay = hom - timedelta(days=hom.weekday())
    lui = a.segmented_control("Tuần", [0, 1, 2, 3], default=0, key=f"vol_lui_{ma}_{vai}",
                              format_func=lambda i: "Tuần này" if i == 0 else "Tuần trước" if i == 1 else f"{i} tuần trước") or 0
    nguon = b.segmented_control("Xem", ["da_tap", "giao_an"], default="da_tap", key=f"vol_ng_{ma}_{vai}",
                                format_func=lambda x: "Đã tập" if x == "da_tap" else "Theo giáo án") or "da_tap"
    t2 = t2_nay - timedelta(weeks=lui)
    V = vo.tuan(ma, t2) if nguon == "da_tap" else vo.ke_hoach(g)
    rows = vo.danh_gia(V["co"], td, uu, goal in ("giam_mo", "recomp"))
    st.caption(f"{'Tuần ' + format(t2, '%d/%m') + ' → ' + format(t2 + timedelta(days=6), '%d/%m') if nguon == 'da_tap' else 'Giáo án đang dùng, quy về 1 tuần'}"
               f" · {V['so_buoi']} buổi · trình độ: {vo.TEN_TD[td]} · ưu tiên: "
               + (", ".join(vo.UU_TIEN[x][0] for x in uu) or "chưa chọn"))
    c1, c2 = st.columns([1.1, 1])
    with c1:
        st.markdown(ban_do(rows), unsafe_allow_html=True)
        st.markdown(chu_giai(), unsafe_allow_html=True)
    with c2:
        ui.sec("Đánh giá tuần")
        for x in vo.nhan_xet(rows, uu, (g or {}).get("han_che"), int(lv or 0), V["so_buoi"] if nguon == "da_tap" else 0,
                             int((g or {}).get("buoi_tuan") or 0) if nguon == "da_tap" and lui == 0 else 0):
            st.markdown(f"- {E(x)}")
        if V["khong_ro"]:
            st.caption("Bài chưa nhận ra nhóm cơ (không tính): " + ", ".join(f"{t} ({n})" for t, n in V["khong_ro"].items()))
    bang = [r for r in rows if r["tt"] != "na"]
    st.dataframe(pd.DataFrame([{
        "Nhóm cơ": ("⭐ " if r["uu_tien"] else "") + r["ten"], "Hiệp / tuần": r["hiep"], "Trạng thái": vo.TRANG_THAI[r["tt"]][0],
        "Cần đạt": f"≥ {r['can']:g}", "Duy trì": f"{r['moc'][0]:g}", "Tối thiểu hiệu quả": f"{r['moc'][1]:g}",
        "Vùng tốt": f"{r['moc'][1]:g}–{r['moc'][2]:g}", "Trần": f"{r['moc'][3]:g}"} for r in bang]),
        hide_index=True, use_container_width=True, height=35 * (len(bang) + 1) + 3)
    if hlv:
        with st.expander("📚 Kiến thức volume cho HLV — mốc theo trình độ, nhóm cơ, mục tiêu"):
            kien_thuc()


def kien_thuc():
    st.markdown("""
**Đếm hiệp thế nào**
- Chỉ đếm **hiệp nặng**: làm tới khi còn chừa khoảng 0–3 lần (RPE 7–10). Hiệp khởi động, bài kích hoạt / giãn cơ, bật nhảy, thể lực không tính.
- Cơ **chính** của bài = 1 hiệp, cơ **phụ** = ½ hiệp. Ví dụ 4 hiệp đẩy ngực = ngực 4 · tay sau 2 · vai trước 2.
- Volume tính theo **tuần**, chia ít nhất **2 buổi / nhóm cơ / tuần** — một buổi một nhóm cơ quá 8–10 hiệp nặng thường kém hiệu quả dần (mức thực hành).

**4 mốc volume** (khái niệm MV · MEV · MAV · MRV của Renaissance Periodization)
- **Duy trì** (MV): đủ giữ cơ, không tăng — dùng cho nhóm không ưu tiên khi giảm mỡ.
- **Tối thiểu hiệu quả** (MEV): bắt đầu tăng cơ — điểm xuất phát đầu khoá / sau deload.
- **Vùng tốt** (MEV → MAV): tăng cơ tốt nhất; mỗi 1–2 tuần thêm 1–2 hiệp cho nhóm ưu tiên nếu hồi phục tốt.
- **Trần** (MRV): vượt thường hồi phục không kịp → tạ đứng / tụt, đau mỏi kéo dài → cần deload.
""")
    rows = []
    for co, (ten, f) in vo.CO.items():
        if co == "bap_chan":
            continue
        rows.append({"Nhóm cơ": ten, **{vo.TEN_TD[t].split(" (")[0]: "{:g} · {:g} · {:g}–{:g} · {:g}".format(
            *(lambda m: (m[0], m[1], m[1], m[2], m[3]))(vo.moc(co, t))) for t in ("moi", "tb", "cao")}})
    st.markdown("**Mốc hiệp / tuần** (duy trì · tối thiểu · vùng tốt · trần)")
    st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)
    st.markdown("**Theo mục tiêu hình thể**")
    st.dataframe(pd.DataFrame([{"Mục tiêu": v[0], "Nhóm ưu tiên (đẩy lên nửa trên vùng tốt)": ", ".join(vo.CO[c][0] for c in v[1]) or "—",
                                "Hỗ trợ": ", ".join(vo.CO[c][0] for c in v[2]) or "—", "Ghi chú": v[3]} for v in vo.UU_TIEN.values()]),
                 hide_index=True, use_container_width=True)
    st.markdown("""
**Giảm mỡ vs tăng cơ**
- Đang giảm mỡ: nhóm **ưu tiên** vẫn giữ vùng tốt; nhóm khác chỉ cần **≥ duy trì** — thâm hụt năng lượng làm hồi phục chậm hơn, đừng dồn volume tối đa.
- Tăng cơ / dư năng lượng: nâng dần volume trong mỗi chu kỳ 4–6 tuần, rồi **deload** (giảm ~⅓–½ số hiệp, giữ mức tạ, chừa 3–4 lần) 1 tuần.
- Người mới: tăng cơ tốt ngay ở 6–12 hiệp / nhóm / tuần — ưu tiên kỹ thuật và tăng tạ hơn là thêm hiệp.

**Nguồn & độ chắc chắn**
- Schoenfeld, Ogborn & Krieger (2017, *Journal of Sports Sciences*) — tổng hợp liều – đáp ứng: nhiều hiệp / tuần hơn đi kèm tăng cơ nhiều hơn; ≥ 10 hiệp / nhóm / tuần tốt hơn < 5.
- Khái niệm MV / MEV / MAV / MRV: Mike Israetel & Renaissance Periodization — **khung thực hành**, không phải con số đo được cho từng người.
- Các con số trong bảng là **mức HLV chọn** dựa trên các nguồn trên + kinh nghiệm; chỉnh theo hồi phục thật của khách (ngủ, tạ, đau mỏi).
""")
