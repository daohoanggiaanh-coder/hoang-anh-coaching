# Hoàng Anh Coaching v2.0 (2026-11-03) — trang "Lộ trình" theo giai đoạn (khách + HLV).
from __future__ import annotations

import html

import streamlit as st

from core import giai_doan as gd, ui

E = html.escape

CSS = """<style>
.gd-bar{display:flex;gap:4px;margin:8px 0 4px}.gd-bar i{flex:1;height:10px;border-radius:4px;background:#E7DFCF}
.gd-bar i.x{background:#C8A24A}.gd-bar i.n{background:#1C1B19;outline:2px solid #C8A24A}
html[data-hac-theme=dark] .gd-bar i{background:#3A372F}html[data-hac-theme=dark] .gd-bar i.n{background:#F3ECDC}
.gd-ph{display:grid;grid-template-columns:repeat(var(--n),1fr);gap:10px;margin:10px 0}
.gd-c{border:1px solid #E7DFCF;border-radius:14px;padding:12px;opacity:.7}
.gd-c.on{opacity:1;border:2px solid #C8A24A;box-shadow:0 6px 20px rgba(200,162,74,.18)}
.gd-c small{font-size:.68rem;letter-spacing:.1em;font-weight:800;color:#8b8577}.gd-c h4{margin:2px 0 4px}
.gd-c p{font-size:.84rem;margin:0}
.gd-sec{margin:10px 0 2px;font-weight:800;font-size:.92rem}
.gd-li{font-size:.86rem;margin:2px 0 2px 4px}
@media (max-width:640px){.gd-ph{grid-template-columns:1fr}}
</style>"""


def trang(k: dict, vai: str):
    st.markdown(CSS, unsafe_allow_html=True)
    L = gd.cua_khach(k)
    G, d = L["gd"], L["dang"]
    trang_thai = ("Khoá chưa bắt đầu" if L["chua_bd"] else "Đã qua hết lộ trình — HLV sẽ lên giai đoạn tiếp theo" if L["da_qua"]
                  else f"Tuần {L['tuan']} / {L['tong']} · đang ở giai đoạn {d + 1}: {G[d]['ten']}")
    st.markdown(f"**🎯 {E(L['muc_tieu'])}** · {L['tong']} tuần từ {L['bat_dau']:%d/%m/%Y} — {E(trang_thai)}")
    st.markdown('<div class="gd-bar">' + "".join(
        f'<i class="{"n" if w == L["tuan"] and not L["chua_bd"] else "x" if w < L["tuan"] else ""}" title="Tuần {w}"></i>'
        for w in range(1, L["tong"] + 1)) + "</div>", unsafe_allow_html=True)
    st.markdown(f'<div class="gd-ph" style="--n:{len(G)}">' + "".join(
        f'<div class="gd-c{" on" if i == d else ""}"><small>GIAI ĐOẠN {g["so"]} · TUẦN {g["tu"]}–{g["den"]}'
        f'{" · ĐANG Ở ĐÂY" if i == d and not L["chua_bd"] else ""}</small><h4>{E(g["ten"])}</h4>'
        f'<p>{g["ngay_tu"]:%d/%m} → {g["ngay_den"]:%d/%m}</p><p style="margin-top:4px">{E(g["muc_tieu"])}</p></div>'
        for i, g in enumerate(G)) + "</div>", unsafe_allow_html=True)
    thu_tu = [d] + [i for i in range(len(G)) if i != d]          # giai đoạn hiện tại mở sẵn
    tabs = st.tabs([f"{'📍 Đang ở · ' if i == d else ''}GĐ {G[i]['so']} · {G[i]['ten']}" for i in thu_tu])
    for t, g in zip(tabs, [G[i] for i in thu_tu]):
        with t:
            a, b = st.columns(2)
            with a:
                _muc("🏋️ Tập tạ", g["tap"])
                _muc("🏃 Cardio", g["cardio"])
                _muc("👣 Bước chân", [f"Khoảng {g['buoc']:,} bước / ngày".replace(",", ".") + " — đếm bằng điện thoại / đồng hồ, "
                                     "ghi ở trang Cardio"])
            with b:
                _muc("🍽 Dinh dưỡng", g["an"])
                _muc("📏 Mốc đo & ảnh", g["do"])
    ui.note("Lộ trình là <b>khung định hướng</b> theo kinh nghiệm huấn luyện — HLV chỉnh theo tiến độ thật (cân TB 7 ngày, số đo, "
            "mức tạ, cảm nhận). Số phút cardio, bước chân, đạm lấy từ thiết lập HLV đặt cho bạn; giai đoạn đầu lên dần, không cần đạt ngay.")
    if vai == "hlv":
        st.caption("Muốn đổi số trong lộ trình: buổi / tuần (lịch cố định), cardio + bước chân (trang Cardio), đạm & mục tiêu "
                   "(Dinh dưỡng → Thông số), số tuần (gói + ngày bắt đầu ở Khách & tài khoản).")


def _muc(ten: str, ds: list[str]):
    st.markdown(f'<div class="gd-sec">{ten}</div>' + "".join(f'<div class="gd-li">• {E(x)}</div>' for x in ds), unsafe_allow_html=True)
