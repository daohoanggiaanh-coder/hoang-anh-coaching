# Hoàng Anh Coaching v1.0 (2026-10-31) — giao diện: đen – vàng đồng, gọn trên điện thoại
from __future__ import annotations

import html

import streamlit as st

from core import config

E = html.escape
VANG, VANG_D, DEN, KEM, XAM = "#C8A24A", "#7A5B14", "#14120F", "#F3ECDC", "#8b8577"
PAL = ["#C8A24A", "#7A5B14", "#2E7D4F", "#B4442F", "#4B6A88", "#8E6BB0"]
MACRO_MAU = {"p": "#B4442F", "c": "#C8A24A", "f": "#4B6A88"}

CSS = """
<style>
html,body,.stMarkdown,.stButton button,input,textarea,select{font-family:'BeVietnamPro',system-ui,sans-serif}
h1,h2,h3,h4{letter-spacing:-.01em}
.block-container{padding-top:1.4rem;max-width:1100px}
[data-testid="stSidebar"]{background:#14120F}
[data-testid="stSidebar"] *{color:#E9E2D0}
[data-testid="stSidebar"] button{background:#2a261f!important;border:1px solid rgba(200,162,74,.35)!important}
[data-testid="stSidebar"] button p{color:#E8C76A!important;font-weight:700}
[data-testid="stSidebarNav"] a[aria-current="page"]{background:rgba(200,162,74,.18)!important;border-radius:10px}
.hac-hero{background:radial-gradient(circle at 20% 0%,#3a3326,#14120F 72%);border-radius:22px;padding:22px 24px;color:#F3ECDC;
  margin-bottom:14px;border:1px solid rgba(200,162,74,.25)}
.hac-hero small{color:#E8C76A;letter-spacing:.18em;font-weight:800;font-size:.66rem}
.hac-hero .t{font-size:1.65rem;font-weight:800;color:#fff;line-height:1.2;margin:4px 0 2px}
.hac-hero .s{color:#D8D1C1;font-size:.88rem}
.hac-tiles{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin:4px 0 14px}
@media(max-width:700px){.hac-tiles{grid-template-columns:repeat(2,1fr)}.hac-hero .t{font-size:1.35rem}}
.hac-tile{background:#fff;border:1px solid #E6DCC6;border-radius:16px;padding:12px 14px}
.hac-tile b{display:block;font-size:1.45rem;color:#1C1B19;line-height:1.15}
.hac-tile small{color:#8b8577;font-size:.72rem;letter-spacing:.04em}
.hac-tile i{font-style:normal;font-size:.72rem;color:#2E7D4F;font-weight:700}
.hac-sec{font-weight:800;color:#7A5B14;letter-spacing:.12em;font-size:.76rem;margin:20px 0 8px;text-transform:uppercase}
.hac-card{background:#fff;border:1px solid #E6DCC6;border-radius:16px;padding:14px 16px;margin:8px 0}
.hac-card h4{margin:0 0 4px;font-size:1.02rem}
.hac-ex{background:#fff;border:1px solid #E6DCC6;border-left:4px solid #C8A24A;border-radius:14px;padding:10px 14px;margin:8px 0}
.hac-ex .n{font-weight:800;font-size:1.02rem}
.hac-ex .m{color:#6C6860;font-size:.82rem;margin-top:2px}
.hac-chip{display:inline-block;font-size:.66rem;font-weight:800;letter-spacing:.06em;border-radius:999px;padding:3px 9px;
  color:#fff;background:#1C1B19;margin-right:4px}
.hac-chip.g{background:#C8A24A;color:#1C1B19}.hac-chip.x{background:#2E7D4F}.hac-chip.r{background:#B4442F}.hac-chip.m{background:#8b8577}
.hac-meal{background:#fff;border:1px solid #E6DCC6;border-radius:16px;padding:12px 16px;margin:10px 0}
.hac-meal .h{display:flex;justify-content:space-between;align-items:baseline;gap:8px;flex-wrap:wrap}
.hac-meal .h b{font-size:1.02rem}.hac-meal .h span{color:#8b8577;font-size:.8rem}
.hac-meal table{width:100%;border-collapse:collapse;margin-top:6px;font-size:.88rem;border:none}
.hac-meal tr{border:none}
.hac-meal td{padding:5px 2px;border:none;border-top:1px solid #F0E9D8}
.hac-meal td.g{text-align:right;font-weight:800;white-space:nowrap}
.hac-meal td.u{color:#8b8577;font-size:.78rem;text-align:right;white-space:nowrap;padding-left:8px}
.hac-bar{display:flex;height:9px;border-radius:9px;overflow:hidden;margin:8px 0 2px;background:#F3ECDC}
.hac-bar i{display:block;height:100%}
.hac-note{background:#FBF8F1;border:1px dashed #DDD4C0;border-radius:12px;padding:10px 14px;color:#5b574f;font-size:.84rem;margin:8px 0}
.hac-b{display:flex;align-items:center;gap:12px;flex-wrap:wrap;background:#fff;border:1px solid #E6DCC6;border-left:4px solid #A3803C;
  border-radius:14px;padding:10px 14px;margin:6px 0 2px}
.hac-b .t{font-weight:900;font-size:1.05rem;min-width:62px}.hac-b .n{font-weight:800}.hac-b .m{color:#8b8577;font-size:.8rem}
.hac-d{margin:14px 0 4px;font-weight:900;color:#7A5B14;letter-spacing:.1em;font-size:.78rem}
.hac-foot{color:#a39d8f;font-size:.72rem;text-align:center;margin:36px 0 8px}
div[data-testid="stMetricValue"]{font-weight:800;letter-spacing:-.01em}
.hac-hero .t{letter-spacing:-.015em}
/* ---------- giao diện tối (html[data-hac-theme=dark] do pwa.py tự đặt theo nền của app) ---------- */
html[data-hac-theme=dark] :is(.hac-tile,.hac-card,.hac-ex,.hac-meal,.hac-b,.dd-bua,.dd-bsc,.dd-wd:not(.t),.cd-d,.dl-m,.dl-b){
  background:#1A1814!important;border-color:#332E25!important;color:#EDE6D6;box-shadow:none}
html[data-hac-theme=dark] :is(.hac-tile b,.hac-ex .n,.hac-card h4,.dd-it .n,.dd-it .g,.dd-bsc h4,.cd-d .t,.dl-m,.dl-m .t,.dl-b .t,.dd-wd b,.hac-meal .h b,.hac-b .t,.hac-b .n){color:#F3ECDC!important}
html[data-hac-theme=dark] :is(.hac-tile small,.hac-ex .m,.dd-it .n small,.cd-d small,.cd-d .p,.cd-d .t i,.dl-m .s,.dl-b .m,.hac-meal .h span,
  .hac-meal td.u,.hac-b .m,.dd-bsc .e,.dd-wd i,.dd-wd small,.dd-bsc p){color:#A8A091!important}
html[data-hac-theme=dark] :is(.hac-sec,.hac-d,.dd-bsc .l,.dd-it .g small){color:#E2BE62!important}
html[data-hac-theme=dark] .hac-note{background:#1D1A15!important;border-color:#3A3429!important;color:#CFC6B4!important}
html[data-hac-theme=dark] .dd-bf{background:#15130F!important;border-color:#2A251D!important;color:#A8A091}
html[data-hac-theme=dark] .dd-bf b{color:#F3ECDC}
html[data-hac-theme=dark] :is(.dd-ic,.cd-d .bar,.hac-bar,.dl-14 div[style*="EEE8DA"]){background:#2A251D!important}
html[data-hac-theme=dark] :is(.dd-it,.hac-meal td){border-color:#2A251D!important}
html[data-hac-theme=dark] :is(.cd-d.x,.dl-m.x){background:#12261A!important;border-color:#2E7D4F!important}
html[data-hac-theme=dark] .cd-d.m{background:#2A1714!important;border-color:#6B2E22!important}
html[data-hac-theme=dark] .cd-d.h{border-color:#D9B65C!important}
html[data-hac-theme=dark] .dl-m.x .s{color:#5CC48A!important}
html[data-hac-theme=dark] .hac-tile i{color:#5CC48A}
html[data-hac-theme=dark] .hac-foot{color:#6f685c}
</style>
"""


def setup():
    st.markdown(CSS, unsafe_allow_html=True)


def hero(kicker: str, title: str, sub: str = "", avatar: str = ""):
    noi = f'<small>{E(kicker)}</small><div class="t">{E(title)}</div>' + (f'<div class="s">{sub}</div>' if sub else "")
    if avatar:
        noi = f'<div style="display:flex;gap:14px;align-items:center">{avatar}<div>{noi}</div></div>'
    st.markdown(f'<div class="hac-hero">{noi}</div>', unsafe_allow_html=True)


def tiles(items: list[tuple[str, str, str]]):
    """[(số, nhãn, dòng phụ)]"""
    st.markdown('<div class="hac-tiles">' + "".join(
        f'<div class="hac-tile"><b>{E(str(a))}</b><small>{E(b)}</small>' + (f"<br><i>{E(c)}</i>" if c else "") + "</div>"
        for a, b, c in items) + "</div>", unsafe_allow_html=True)


def sec(t: str):
    st.markdown(f'<div class="hac-sec">{E(t)}</div>', unsafe_allow_html=True)


def note(t: str):
    st.markdown(f'<div class="hac-note">{t}</div>', unsafe_allow_html=True)


def macro_bar(p: float, c: float, f: float):
    tong = max(p * 4 + c * 4 + f * 9, 1)
    seg = "".join(f'<i style="width:{v / tong * 100:.1f}%;background:{MACRO_MAU[k]}"></i>'
                  for k, v in (("p", p * 4), ("c", c * 4), ("f", f * 9)))
    st.markdown(f'<div class="hac-bar">{seg}</div>', unsafe_allow_html=True)


def layout(fig, h=320, y_title=""):
    fig.update_layout(height=h, margin=dict(l=10, r=10, t=10, b=10), plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                      legend=dict(orientation="h", y=-0.2), yaxis_title=y_title, hovermode="x unified",
                      font=dict(family="BeVietnamPro, system-ui, sans-serif"))
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(gridcolor="rgba(160,150,130,.25)")
    return fig


def footer():
    st.markdown(f'<div class="hac-foot">{config.BRAND} · {config.VERSION_LABEL}</div>', unsafe_allow_html=True)
