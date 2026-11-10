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
.hac-sec{font-weight:800;color:#7A5B14;letter-spacing:.12em;font-size:.76rem;margin:20px 0 8px;text-transform:uppercase;text-align:center}
/* v2.8: căn giữa thống nhất — tiêu đề, ô số, chỉ số, hàng tab; tên + đoạn văn dài giữ bên trái */
.hac-tile{text-align:center}
[data-testid="stMetric"]{text-align:center}[data-testid="stMetric"] > div{justify-content:center;width:100%}
[data-testid="stMetricLabel"],[data-testid="stMetricValue"],[data-testid="stMetricDelta"]{justify-content:center;display:flex}
.stMainBlockContainer [data-testid="stMarkdownContainer"] :is(h1,h2,h3,h4,h5){text-align:center}
.stTabs [role="tablist"]{justify-content:center}
.stMainBlockContainer [data-testid="stElementContainer"]:has(> [data-testid="stButtonGroup"]){align-self:center;width:auto!important;max-width:100%}
[data-testid="stButtonGroup"]{display:flex;flex-direction:column;align-items:center}
[data-testid="stButtonGroup"] [data-testid="stWidgetLabel"]{justify-content:center;width:100%}
.hac-d{text-align:center}
.tk-o{justify-content:center;text-align:center;flex-direction:column;align-items:center}
.gd-c,.gd-vol div,.an-con div{text-align:center}
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
.hac-hero{text-align:center}.hac-hero>div[style*="flex"]{justify-content:center;text-align:left}
/* ---------- v2.2: tab & mục mở rộng nhìn rõ là nút bấm (Streamlit 1.66: role=tablist / data-testid=stTab) ---------- */
.stTabs [role="tablist"]{gap:6px!important;flex-wrap:wrap!important;border-bottom:none!important;box-shadow:none!important;padding:2px 0 8px;overflow:visible!important}
.stTabs [data-testid="stTab"]{background:#F6F1E6!important;border:1.5px solid #E2D7BF!important;border-radius:12px!important;
  padding:8px 14px!important;height:auto!important;margin:0!important;box-shadow:0 2px 0 rgba(122,91,20,.10)!important;transition:all .12s}
.stTabs [data-testid="stTab"]::after,.stTabs [data-testid="stTab"]::before{display:none!important}
.stTabs [data-testid="stTab"] p{font-weight:700!important;font-size:.9rem!important}
.stTabs [data-testid="stTab"]:hover{border-color:#C8A24A!important;background:#FBF6EA!important}
.stTabs [data-testid="stTab"][aria-selected="true"]{background:#1C1B19!important;border-color:#1C1B19!important;box-shadow:0 3px 10px rgba(0,0,0,.18)!important}
.stTabs [data-testid="stTab"][aria-selected="true"] p{color:#E8C76A!important}
/* v2.3: menu trang (trên cùng + thanh bên) thành nút */
[data-testid="stTopNavLink"]{border:1.5px solid #E2D7BF!important;background:#F6F1E6!important;border-radius:12px!important;
  padding:6px 12px!important;margin:0 3px!important;box-shadow:0 2px 0 rgba(122,91,20,.10)}
[data-testid="stTopNavLink"]:hover{border-color:#C8A24A!important;background:#FBF6EA!important}
[data-testid="stTopNavLink"][aria-current="page"]{background:#1C1B19!important;border-color:#1C1B19!important}
[data-testid="stTopNavLink"][aria-current="page"] *{color:#E8C76A!important}
[data-testid="stTopNavLink"] span{font-weight:700!important}
[data-testid="stSidebarNavLink"]{border:1px solid rgba(200,162,74,.22)!important;background:#1D1A15!important;border-radius:10px!important;
  margin:2px 0!important;padding:4px 10px!important;min-height:2.1rem!important}
/* v3.7: tiêu đề nhóm menu — chữ vàng, có khoảng cách giữa các nhóm */
[data-testid="stNavSectionHeader"]{color:#C8A24A!important;font-weight:800!important;letter-spacing:.06em;font-size:.78rem!important;
  margin:14px 0 4px!important;padding:4px 2px 4px!important;border-bottom:1px solid rgba(200,162,74,.25)}
[data-testid="stNavSectionHeader"] *{color:#C8A24A!important;font-weight:800!important}
[data-testid="stSidebarNavLink"]:hover{border-color:#C8A24A!important;background:#26221B!important}
[data-testid="stSidebarNavLink"][aria-current="page"]{background:#3A2F18!important;border:2px solid #E8C76A!important}
[data-testid="stSidebarNavLink"][aria-current="page"] *{color:#F6D77E!important;font-weight:800!important}
[data-testid="stSidebarNavLink"] span{font-weight:600}
html[data-hac-theme=dark] [data-testid="stTopNavLink"]{background:#211E19!important;border-color:#3A342A!important}
html[data-hac-theme=dark] [data-testid="stTopNavLink"][aria-current="page"]{background:#C8A24A!important;border-color:#C8A24A!important}
html[data-hac-theme=dark] [data-testid="stTopNavLink"][aria-current="page"] *{color:#14120F!important}
/* nút đi tới trang (trang chủ khách) — chỉ hiện trên điện thoại (máy tính đã có menu bên trái), 2 nút / hàng */
@media (min-width:768px){.st-key-hac_di_toi{display:none!important}}
.st-key-hac_di_toi [data-testid="stHorizontalBlock"]{flex-wrap:nowrap!important;gap:8px!important}
.st-key-hac_di_toi [data-testid="stColumn"]{min-width:0!important;width:50%!important;flex:1 1 50%!important}
.st-key-hac_di_toi [data-testid="stPageLink"] a{border:1.5px solid #E2D7BF;background:#FFFDF8;border-radius:14px;padding:12px 10px;
  justify-content:center;box-shadow:0 2px 0 rgba(122,91,20,.10)}
.st-key-hac_di_toi [data-testid="stPageLink"] a:hover{border-color:#C8A24A;background:#FBF6EA}
.st-key-hac_di_toi [data-testid="stPageLink"] p{font-weight:800}
html[data-hac-theme=dark] .st-key-hac_di_toi [data-testid="stPageLink"] a{background:#1A1814;border-color:#3A342A}
[data-testid="stExpander"] details{border:1.5px solid #E2D7BF!important;border-radius:12px!important;background:#FFFDF8}
[data-testid="stExpander"] summary{font-weight:700}
[data-testid="stExpander"] summary:hover{background:#FBF6EA}
html[data-hac-theme=dark] .stTabs [data-testid="stTab"]{background:#211E19!important;border-color:#3A342A!important}
html[data-hac-theme=dark] .stTabs [data-testid="stTab"] p{color:#E9E2D0!important}
html[data-hac-theme=dark] .stTabs [data-testid="stTab"][aria-selected="true"]{background:#C8A24A!important;border-color:#C8A24A!important}
html[data-hac-theme=dark] .stTabs [data-testid="stTab"][aria-selected="true"] p{color:#14120F!important}
html[data-hac-theme=dark] [data-testid="stExpander"] details{background:#1A1814;border-color:#3A342A!important}
html[data-hac-theme=dark] [data-testid="stExpander"] summary:hover{background:#221F19}
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
    can_giua_bang()


_TEN_COT = ("gói","tình trạng gói","tài khoản","khách", "họ tên", "tên", "bài", "món", "nhóm cơ", "mục tiêu", "giai đoạn", "ghi chú", "nội dung", "lý do", "thực phẩm",
            "cơ", "mô tả", "lịch")


def _cot_ten(c) -> bool:
    c = str(c).lower()
    return any(c == x or c.startswith(x + " ") or c.startswith(x) and len(c) <= len(x) + 3 for x in _TEN_COT)


def can_giua_bang():
    """v2.8: mọi st.dataframe căn giữa, trừ cột tên / chữ dài (căn trái) — không phải sửa từng bảng."""
    from streamlit.delta_generator import DeltaGenerator
    goc = DeltaGenerator.dataframe
    if getattr(goc, "_hac_cg", False):
        return

    def df(self, data=None, *a, column_config=None, **kw):
        try:
            cols = list(getattr(data, "columns", []))
            cfg = dict(column_config or {})
            for c in cols:
                al = "left" if _cot_ten(c) else "center"
                v = cfg.get(c)
                if v is None:
                    cfg[c] = st.column_config.Column(alignment=al)
                elif isinstance(v, dict) and not v.get("alignment"):
                    cfg[c] = {**v, "alignment": al}
            column_config = cfg or None
        except Exception:  # noqa: BLE001 — lỗi gì thì vẫn hiện bảng như cũ
            pass
        return goc(self, data, *a, column_config=column_config, **kw)
    df._hac_cg = True
    DeltaGenerator.dataframe = df
    st.dataframe = lambda *a, **kw: df(st._main, *a, **kw)


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
