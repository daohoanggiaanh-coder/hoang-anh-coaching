# Hoàng Anh Coaching v2.0 (2026-11-03) — trang "Lộ trình" theo giai đoạn (khách + HLV).
from __future__ import annotations

import html

import streamlit as st

import pandas as pd

from core import giai_doan as gd, ui, volume as vo

E = html.escape

CSS = """<style>
.gd-bar{display:flex;gap:4px;margin:8px 0 4px}.gd-bar i{flex:1;height:10px;border-radius:4px;background:#E7DFCF}
.gd-bar i.x{background:#C8A24A}.gd-bar i.dl{background:#8E7CC3}.gd-bar i.x.dl{background:#6B4BA3}.gd-bar i.n{background:#1C1B19;outline:2px solid #C8A24A}
html[data-hac-theme=dark] .gd-bar i{background:#3A372F}html[data-hac-theme=dark] .gd-bar i.n{background:#F3ECDC}
.gd-ph{display:grid;grid-template-columns:repeat(var(--n),1fr);gap:10px;margin:10px 0}
.gd-c{border:1px solid #E7DFCF;border-radius:14px;padding:12px;opacity:.7}
.gd-c.on{opacity:1;border:2px solid #C8A24A;box-shadow:0 6px 20px rgba(200,162,74,.18)}
.gd-c small{font-size:.68rem;letter-spacing:.1em;font-weight:800;color:#8b8577}.gd-c h4{margin:2px 0 4px}
.gd-c p{font-size:.84rem;margin:0}
.gd-sec{margin:10px 0 2px;font-weight:800;font-size:.92rem}
.gd-li{font-size:.86rem;margin:2px 0 2px 4px}
.gd-vol{display:grid;grid-template-columns:repeat(auto-fill,minmax(118px,1fr));gap:6px;margin:4px 0}
.gd-vol div{border:1px solid #E7DFCF;border-radius:10px;padding:5px 8px;font-size:.78rem}
.gd-vol div.u{border:2px solid #C8A24A;background:rgba(200,162,74,.08)}.gd-vol b{display:block;font-size:.98rem}
.gd-dl{border-left:4px solid #6B4BA3;background:rgba(107,75,163,.07);border-radius:8px;padding:6px 10px;font-size:.84rem;margin:6px 0}
@media (max-width:640px){.gd-ph{grid-template-columns:1fr}}
</style>"""


def trang(k: dict, vai: str):
    st.markdown(CSS, unsafe_allow_html=True)
    from views import common as C
    L = gd.cua_khach(k, hs=C.ho_so_dd(k))
    G, d = L["gd"], L["dang"]
    trang_thai = ("Khoá chưa bắt đầu" if L["chua_bd"] else "Đã qua hết lộ trình — HLV sẽ lên giai đoạn tiếp theo" if L["da_qua"]
                  else f"Tuần {L['tuan']} / {L['tong']} · đang ở giai đoạn {d + 1}: {G[d]['ten']}")
    st.markdown(f"**🎯 {E(L['muc_tieu'])}** · {L['tong']} tuần từ {L['bat_dau']:%d/%m/%Y} — {E(trang_thai)}")
    st.markdown('<div class="gd-bar">' + "".join(
        f'<i class="{"n" if w == L["tuan"] and not L["chua_bd"] else "x" if w < L["tuan"] else ""}{" dl" if w in L["deload"] else ""}" '
        f'title="Tuần {w}{" · deload" if w in L["deload"] else ""}"></i>'
        for w in range(1, L["tong"] + 1)) + "</div>", unsafe_allow_html=True)
    st.caption(f"Trình độ: {L['trinh_do']} · ưu tiên: " + (", ".join(vo.UU_TIEN[x][0] for x in L["uu_tien"]) or "chưa chọn")
               + (f" · 🟪 tuần deload: {', '.join(str(w) for w in L['deload'])}" if L["deload"] else ""))
    thieu = [x for x, ok in (("chưa có giáo án HLV", L["co_giao_an"]), ("chưa chọn mục tiêu hình thể (trang 💪 Volume)", L["uu_tien"]),
                             ("thiếu chiều cao / cân để tính macro", L["macro"])) if not ok]
    if thieu and vai == "hlv":
        st.warning("Lộ trình còn thiếu: " + " · ".join(thieu))
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
                _muc("🏋️ Tập tạ · rep · RIR · nghỉ", g["tap"])
                st.markdown('<div class="gd-sec">📊 Volume mục tiêu (hiệp nặng / nhóm cơ / tuần)</div><div class="gd-vol">' + "".join(
                    f'<div class="{"u" if v["uu_tien"] else ""}">{"⭐ " if v["uu_tien"] else ""}{E(v["ten"])}<b>{v["hiep"]}</b></div>'
                    for v in g["volume"]) + "</div>", unsafe_allow_html=True)
                st.markdown('<div class="gd-dl">' + (
                    f"🟪 <b>Deload tuần {', '.join(str(w) for w in g['deload'])}</b>: giảm ⅓–½ số hiệp, giữ mức tạ, chừa 3–4 lần; cardio nhẹ, ngủ nhiều hơn."
                    if g["deload"] else "Deload sớm (1 tuần nhẹ) nếu: tạ tụt 2 buổi liền, đau mỏi kéo dài > 3 ngày, ngủ kém, mất hứng tập.")
                    + "</div>", unsafe_allow_html=True)
                _muc("🏃 Cardio", g["cardio"])
                _muc("👣 Bước chân", [f"Khoảng {g['buoc']:,} bước / ngày".replace(",", ".") + " — đếm bằng điện thoại / đồng hồ, "
                                     "ghi ở trang Cardio"])
            with b:
                _muc("🍽 Dinh dưỡng · macro", g["an"])
                _muc("🥦 Vi chất · nước · muối", L["vi_chat"])
                _muc("😴 Ngủ & phục hồi", L["phuc_hoi"])
                if L["bo_sung"]:
                    _muc("💊 Bổ sung (không bắt buộc)", L["bo_sung"])
                _muc("📏 Mốc đo & ảnh", g["do"])
            if g["giao_an"]:
                with st.expander(f"📋 Giáo án & liều trong giai đoạn này (tuần {g['tu']}–{g['den']})"):
                    for bb in g["giao_an"]:
                        st.markdown(f"**{E(bb['ten'])}**")
                        st.dataframe(pd.DataFrame([{"Bài": r["bai"], "Hiệp × lần": r["lieu"], "Gắng sức": r["rir"], "Nghỉ": r["nghi"]}
                                                   for r in bb["bai"]]), hide_index=True, use_container_width=True)
    if L["ta"]:
        ui.sec("🏋️ Mức tạ hiện tại (lần ghi gần nhất)")
        st.dataframe(pd.DataFrame([{"Bài": r["bai"], "Hiệp nặng nhất": r["top"], "1RM ước tính": f"{r['e1rm']:g} kg" if r["e1rm"] else "—",
                                    "Ngày": f"{r['ngay']:%d/%m}"} for r in L["ta"]]), hide_index=True, use_container_width=True)
        st.caption("Tăng tải kép: đủ số lần trên cùng mọi hiệp → buổi sau thêm tạ. 1RM ước tính theo Epley — để so tiến bộ, không phải để thử tối đa.")
    ui.note("Lộ trình là <b>khung định hướng</b> theo kinh nghiệm huấn luyện — HLV chỉnh theo tiến độ thật (cân TB 7 ngày, số đo, "
            "mức tạ, cảm nhận). Số phút cardio, bước chân, đạm lấy từ thiết lập HLV đặt cho bạn; giai đoạn đầu lên dần, không cần đạt ngay.")
    if vai == "hlv":
        st.caption("Muốn đổi số trong lộ trình: buổi / tuần (lịch cố định), cardio + bước chân (trang Cardio), đạm & mục tiêu "
                   "(Dinh dưỡng → Thông số), số tuần (gói + ngày bắt đầu ở Khách & tài khoản).")


def _muc(ten: str, ds: list[str]):
    st.markdown(f'<div class="gd-sec">{ten}</div>' + "".join(f'<div class="gd-li">• {E(x)}</div>' for x in ds), unsafe_allow_html=True)
