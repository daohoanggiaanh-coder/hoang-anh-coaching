"""v4.3 — LỊCH THÁNG (khách + HLV) và trang 📊 Thống kê buổi tập cho HLV."""
from __future__ import annotations

from datetime import date, timedelta

import plotly.graph_objects as go
import streamlit as st

from core import db, store, thong_ke_buoi as tk, ui

E = ui.E
THANG = ["", "Tháng 1", "Tháng 2", "Tháng 3", "Tháng 4", "Tháng 5", "Tháng 6", "Tháng 7", "Tháng 8", "Tháng 9", "Tháng 10",
         "Tháng 11", "Tháng 12"]
VANG, DEN, XAM = "#C8A24A", "#1C1B19", "#D9D2C3"

CSS = """<style>
.lt-g{display:grid;grid-template-columns:repeat(7,minmax(0,1fr));gap:4px;margin:6px 0 4px}
.lt-h{font-size:.68rem;font-weight:700;color:#8A8478;text-align:center;padding:2px 0}
.lt-c{min-height:74px;border-radius:9px;padding:4px 4px 5px;background:#F7F3EA;border:1px solid #EEE6D4;position:relative;overflow:hidden}
.lt-c .d{font-size:.78rem;font-weight:700;color:#5E584C;display:flex;justify-content:space-between;align-items:center;line-height:1.1}
.lt-c .d i{font-style:normal;font-size:.6rem;font-weight:700;padding:0 4px;border-radius:6px;background:rgba(255,255,255,.75);color:#7A5B14}
.lt-c .t{font-size:.6rem;line-height:1.22;margin-top:3px;display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;
  overflow:hidden;word-break:break-word}
.lt-c.da{background:linear-gradient(160deg,#D8B45C,#B8902F);border-color:#B8902F}
.lt-c.da .d,.lt-c.da .t{color:#fff}
.lt-c.hen{background:#fff;border:1.5px dashed #C8A24A}
.lt-c.hen .t{color:#7A5B14;font-weight:600}
.lt-c.lo{background:#FBEDEA;border-color:#F0CFC8}.lt-c.lo .t{color:#B4442F}
.lt-c.nghi .t{color:#A39B8B}
.lt-c.trong{background:transparent;border:0}
.lt-c.hom{box-shadow:0 0 0 2.5px #1C1B19}
.lt-c.moc{box-shadow:0 0 0 2.5px #2E7D4F}
.lt-c.hom.moc{box-shadow:0 0 0 2.5px #1C1B19,0 0 0 5px #2E7D4F}
.lt-c .m{position:absolute;right:3px;bottom:2px;font-size:.8rem}
.lt-lg{display:flex;flex-wrap:wrap;gap:4px 12px;font-size:.72rem;color:#6B6458;margin:2px 0 8px}
.lt-lg span{display:inline-flex;align-items:center;gap:4px}
.lt-lg b{width:12px;height:12px;border-radius:3px;display:inline-block}
.lt-bar{height:12px;border-radius:7px;background:#EEE6D4;overflow:hidden;margin:4px 0 2px}
.lt-bar div{height:100%;background:linear-gradient(90deg,#D8B45C,#B8902F)}
.lt-ds{font-size:.84rem;margin:2px 0}
.lt-ds .r{display:flex;gap:8px;padding:6px 2px;border-bottom:1px solid #F0E8D6;align-items:baseline}
.lt-ds .r .n{min-width:62px;font-weight:700;color:#5E584C}
.lt-ds .r small{color:#8A8478}
.lt-tip{background:#F3F7F1;border:1px solid #D6E6D3;border-radius:12px;padding:10px 12px;font-size:.88rem;margin:6px 0}
@media (max-width:480px){.lt-c{min-height:66px;padding:3px}.lt-c .t{font-size:.56rem}.lt-g{gap:3px}}
</style>"""


def _gon(t: str) -> str:
    """Tên buổi gọn cho ô lịch: 'Buổi A · Chuỗi trước 1 · đùi trước…' → 'A · Chuỗi trước 1'."""
    t = str(t or "")
    if t.lower().startswith("buổi ") and len(t) > 7 and t[6:9].strip().startswith("·"):
        t = t[5:]
    ps = [p.strip() for p in t.split("·")]
    return " · ".join(ps[:2]) if len(ps) > 2 else t


def _o(x: dict | None, hom: date) -> str:
    if x is None:
        return '<div class="lt-c trong"></div>'
    d, loai = x["ngay"], x["loai"]
    cls = [loai] + (["hom"] if d == hom else []) + (["moc"] if x.get("moc") else [])
    so = f"<i>#{x['so']}</i>" if x.get("so") else ""
    if loai == "da":
        t = "✓ " + E(_gon(x["ten"]))
    elif loai == "hen":
        t = (E(x["gio"]) + " · " if x.get("gio") else "") + E(_gon(x["ten"]))
    elif loai == "lo":
        t = "✕ Lỡ buổi"
    else:
        t = "🚶 NEAT" if d >= hom - timedelta(days=0) else ""
    m = f'<span class="m">{x["moc"][:1] if x.get("moc") else ""}</span>' if x.get("moc") else ""
    tip = E(x.get("moc") or x.get("ten") or x.get("meo") or "")
    return f'<div class="lt-c {" ".join(cls)}" title="{tip}"><div class="d">{d.day}{so}</div><div class="t">{t}</div>{m}</div>'


def lich(k: dict, key: str = "lt", cho_khach: bool = True):
    """Lịch tháng: ngày đã tập (tên buổi), buổi sắp tới (tên buổi theo giáo án), mốc, ngày nghỉ → nhắc NEAT."""
    hom = db.now_vn().date()
    sk = f"{key}_{k['ma']}_thang"
    nam, thang = st.session_state.get(sk, (hom.year, hom.month))
    st.markdown(CSS, unsafe_allow_html=True)
    st.markdown(f"<style>.st-key-{sk}_nav [data-testid=stHorizontalBlock]{{flex-wrap:nowrap!important;gap:.4rem}}"
                f".st-key-{sk}_nav [data-testid=stColumn]{{min-width:0!important;width:auto!important}}</style>", unsafe_allow_html=True)
    nav = st.container(key=f"{sk}_nav")
    a, b, c = nav.columns([1, 3, 1], vertical_alignment="center")
    if a.button("◀", key=f"{sk}_lui", use_container_width=True):
        nam, thang = (nam - 1, 12) if thang == 1 else (nam, thang - 1)
    if c.button("▶", key=f"{sk}_toi", use_container_width=True):
        nam, thang = (nam + 1, 1) if thang == 12 else (nam, thang + 1)
    st.session_state[sk] = (nam, thang)
    L = tk.lich_thang(k, nam, thang, hom)
    b.markdown(f"<div style='text-align:center;font-weight:800;font-size:1.05rem'>{THANG[thang]} · {nam}</div>",
               unsafe_allow_html=True)
    g = L["goi"]
    if g["tong"]:
        pc = min(100, round(g["da"] / g["tong"] * 100))
        st.markdown(f"<div style='font-size:.86rem'><b>{g['da']}/{g['tong']}</b> buổi trong gói · còn <b>{max(g['con'] or 0, 0)}</b> buổi"
                    f"<span style='float:right;color:#8A8478'>{pc}%</span></div><div class='lt-bar'><div style='width:{pc}%'></div></div>",
                    unsafe_allow_html=True)
    st.markdown(f"<div style='font-size:.8rem;color:#6B6458'>{THANG[thang]}: <b>{L['da_thang']}</b> buổi đã tập"
                + (f" · <b>{L['hen_thang']}</b> buổi sắp tới" if L["hen_thang"] else "")
                + (f" · {L['lo_thang']} buổi lỡ" if L["lo_thang"] else "") + "</div>", unsafe_allow_html=True)
    dau = L["o"][0]["ngay"].weekday()
    cells = [None] * dau + L["o"]
    cells += [None] * (-len(cells) % 7)
    st.markdown('<div class="lt-g">' + "".join(f'<div class="lt-h">{t}</div>' for t in ("T2", "T3", "T4", "T5", "T6", "T7", "CN"))
                + "".join(_o(x, hom) for x in cells) + "</div>"
                '<div class="lt-lg"><span><b style="background:#C8A24A"></b>Đã tập</span>'
                '<span><b style="background:#fff;border:1.5px dashed #C8A24A"></b>Sắp tập</span>'
                '<span><b style="background:#F7F3EA;border:1px solid #E6DCC4"></b>Nghỉ → tăng NEAT</span>'
                '<span><b style="background:#FBEDEA"></b>Lỡ buổi</span>'
                '<span><b style="box-shadow:0 0 0 2px #2E7D4F;background:#fff"></b>Cột mốc</span>'
                '<span><b style="box-shadow:0 0 0 2px #1C1B19;background:#fff"></b>Hôm nay</span></div>', unsafe_allow_html=True)
    # hôm nay
    o_hom = next((x for x in L["o"] if x["ngay"] == hom), None)
    if o_hom and o_hom["loai"] == "nghi" and cho_khach:
        i = hom.toordinal()
        nx = tk.buoi_tiep_theo(k) if not L["hen_thang"] else None
        if nx:      # khách tự tập, không có lịch cố định → nhắc buổi kế tiếp theo giáo án
            st.markdown(f"<div class='lt-tip' style='background:#FBF6EA;border-color:#EBDDB7'><b>🏋️ Buổi tập tiếp theo của bạn:</b> "
                        f"{E(nx)}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='lt-tip'><b>😌 {'Ngày nghỉ' if nx else 'Hôm nay nghỉ tập'}</b> — giảm nhẹ calo và tăng vận động ngoài giờ tập "
                    f"(NEAT):<br>{E(tk.NEAT[i % len(tk.NEAT)])}<br>{E(tk.NEAT[(i + 3) % len(tk.NEAT)])}</div>", unsafe_allow_html=True)
    elif o_hom and o_hom["loai"] == "hen":
        st.markdown(f"<div class='lt-tip' style='background:#FBF6EA;border-color:#EBDDB7'><b>🏋️ Hôm nay tập</b>"
                    f"{' lúc ' + E(o_hom['gio']) if o_hom.get('gio') else ''}: <b>{E(o_hom['ten'])}</b>"
                    f"{' · ' + E(o_hom['moc']) if o_hom.get('moc') else ''}</div>", unsafe_allow_html=True)
    # chi tiết dạng danh sách — đọc rõ tên buổi
    ds = [x for x in L["o"] if x["loai"] in ("da", "hen", "lo")]
    if ds:
        with st.expander(f"📋 Chi tiết từng buổi {THANG[thang].lower()}", expanded=False):
            st.markdown('<div class="lt-ds">' + "".join(
                f'<div class="r"><span class="n">{store.THU[x["ngay"].weekday()]} {x["ngay"]:%d/%m}</span><span>'
                + ({"da": "✅ ", "hen": "🗓 ", "lo": "✕ "}[x["loai"]]) + f'<b>{E(x["ten"])}</b>'
                + (f' <small>· {E(x["gio"])}</small>' if x.get("gio") else "")
                + (f' <small>· buổi #{x["so"]}</small>' if x.get("so") else "")
                + (f' <small style="color:#2E7D4F">· {E(x["moc"])}</small>' if x.get("moc") else "") + "</span></div>"
                for x in ds) + "</div>", unsafe_allow_html=True)


# =================================================================== trang HLV
def _layout(fig, h):
    fig.update_layout(height=h, margin=dict(l=8, r=8, t=30, b=8), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      font=dict(size=12), legend=dict(orientation="h", y=1.08, x=0), bargap=0.35)
    fig.update_xaxes(gridcolor="#EEE6D4")
    fig.update_yaxes(gridcolor="#EEE6D4")
    return fig


def trang_hlv(u: dict):
    ui.hero("THỐNG KÊ BUỔI TẬP", "Khách đã tập bao nhiêu · còn bao nhiêu",
            "Biểu đồ gói buổi, chuyên cần từng tuần và lịch tháng của từng khách.")
    hom = db.now_vn().date()
    DS = [k for k in store.clients(ca_ngung=False)]
    if not DS:
        st.info("Chưa có khách đang tập.")
        return
    t1, t2 = st.tabs(["📊 Tất cả khách", "👤 Từng khách"])
    with t1:
        R = tk.tong_hop_khach(DS, hom)
        goi_b = sorted([r for r in R if r["tong"]], key=lambda r: (r["con"] if r["con"] is not None else 999))
        ui.tiles([(str(sum(r["da"] for r in goi_b)), "buổi đã dạy (gói hiện tại)", f"{len(goi_b)} khách gói theo buổi"),
                  (str(sum(max(r["con"] or 0, 0) for r in goi_b)), "buổi còn phải dạy", ""),
                  (str(sum(r["bon_tuan"] for r in R)), "buổi 4 tuần qua", "mọi khách"),
                  (str(sum(1 for r in goi_b if (r["con"] or 0) <= 3)), "khách sắp hết gói", "còn ≤ 3 buổi")])
        if goi_b:
            ui.sec("Gói theo buổi — đã tập / còn lại")
            ten = [f"{r['ten']}" for r in goi_b]
            fig = go.Figure()
            fig.add_bar(y=ten, x=[r["da"] for r in goi_b], name="Đã tập", orientation="h", marker_color=VANG)
            fig.add_bar(y=ten, x=[max(r["con"] or 0, 0) for r in goi_b], name="Còn lại", orientation="h", marker_color=XAM)
            fig.add_scatter(y=ten, x=[max(r["tong"], r["da"]) for r in goi_b], mode="text", showlegend=False, textposition="middle right",
                            text=[f"  {r['da']}/{r['tong']} · còn {max(r['con'] or 0, 0)}" for r in goi_b],
                            textfont=dict(size=11, color="#5E584C"))
            mx = max(max(r["tong"], r["da"]) for r in goi_b)
            fig.update_xaxes(range=[0, mx * 1.55])
            fig.update_layout(barmode="stack", yaxis=dict(autorange="reversed"))
            st.plotly_chart(_layout(fig, 70 + 34 * len(goi_b)), use_container_width=True, config={"displayModeBar": False})
            st.caption("Sắp xếp: khách còn ít buổi nhất ở trên — ưu tiên tư vấn gia hạn.")
        ui.sec("Chuyên cần 4 tuần qua — thực tế so với kế hoạch")
        R2 = sorted([r for r in R if r["bon_tuan"] or r["ke_hoach_4t"]], key=lambda r: r["bon_tuan"] - r["ke_hoach_4t"])
        im = [r["ten"] for r in R if not (r["bon_tuan"] or r["ke_hoach_4t"])]
        if not R2:
            st.caption("Chưa có buổi nào được ghi trong 4 tuần qua.")
        fig = go.Figure() if R2 else None
        fig and fig.add_bar(y=[r["ten"] for r in R2], x=[r["bon_tuan"] for r in R2], name="Đã tập", orientation="h", marker_color=VANG,
                    text=[str(r["bon_tuan"]) for r in R2], textposition="outside")
        if R2:
            if any(r["ke_hoach_4t"] for r in R2):
                fig.add_scatter(y=[r["ten"] for r in R2], x=[r["ke_hoach_4t"] or None for r in R2], mode="markers", name="Kế hoạch",
                                marker=dict(symbol="line-ns", size=18, line=dict(width=3, color=DEN)))
            fig.update_layout(yaxis=dict(autorange="reversed"))
            st.plotly_chart(_layout(fig, 80 + 30 * len(R2)), use_container_width=True, config={"displayModeBar": False})
            st.caption("Vạch đen = số buổi theo lịch cố định × 4 tuần (khách có lịch cố định). Khách thiếu nhiều nhất ở trên.")
        if im:
            st.caption("⚠️ 4 tuần qua chưa có buổi nào được ghi (✅ trên Lịch hoặc ghi bài): " + ", ".join(im))
        with st.expander("📋 Bảng số liệu"):
            st.dataframe([{"Khách": r["ten"], "Gói": r["goi"], "Đã tập": r["da"], "Tổng": r["tong"] or "—",
                           "Còn": r["con"] if r["con"] is not None else "—", "4 tuần": r["bon_tuan"],
                           "Buổi cuối": f"{r['cuoi']:%d/%m}" if r["cuoi"] else "—",
                           "Hết hạn": f"{r['het_han']:%d/%m/%Y}" if r["het_han"] else "—"} for r in R],
                         hide_index=True, use_container_width=True)
    with t2:
        from views.coach import _chon_khach
        k = _chon_khach(DS, "tk_kh")
        if not k:
            return
        R = tk.tong_hop_khach([k], hom)
        r = R[0] if R else None
        T = tk.theo_tuan(k, 12, hom)
        if r:
            a, b = st.columns([1, 1.6])
            with a:
                if r["tong"]:
                    con = max(r["con"] or 0, 0)
                    fig = go.Figure(go.Pie(values=[r["da"], con] if con else [r["da"]], labels=["Đã tập", "Còn lại"] if con else ["Đã tập"],
                                           hole=.68, marker_colors=[VANG, XAM], textinfo="none", sort=False))
                    fig.update_layout(annotations=[dict(text=f"<b>{r['da']}/{r['tong']}</b><br>còn {con}", showarrow=False,
                                                        font_size=17)], showlegend=False)
                    st.plotly_chart(_layout(fig, 230), use_container_width=True, config={"displayModeBar": False})
                    st.caption(f"{r['goi']}" + (f" · hết hạn {r['het_han']:%d/%m/%Y}" if r["het_han"] else ""))
                else:
                    ui.tiles([(str(r["da"]), "buổi đã tập", r["goi"]),
                              (f"{r['het_han']:%d/%m}" if r["het_han"] else "—", "hết hạn gói", "")])
            with b:
                fig = go.Figure()
                fig.add_bar(x=[f"{t['tuan']:%d/%m}" for t in T], y=[t["so"] for t in T], name="Buổi / tuần", marker_color=VANG,
                            text=[str(t["so"]) if t["so"] else "" for t in T], textposition="outside")
                if T and T[0]["ke_hoach"]:
                    fig.add_scatter(x=[f"{t['tuan']:%d/%m}" for t in T], y=[t["ke_hoach"] for t in T], mode="lines", name="Kế hoạch",
                                    line=dict(color=DEN, dash="dot", width=2))
                fig.update_layout(title=dict(text="Buổi mỗi tuần (12 tuần)", font_size=13), yaxis=dict(dtick=1, rangemode="tozero"))
                st.plotly_chart(_layout(fig, 260), use_container_width=True, config={"displayModeBar": False})
            tb = sum(t["so"] for t in T[-4:]) / 4
            st.caption(f"Trung bình 4 tuần gần nhất: **{tb:.1f} buổi/tuần**" + (f" · kế hoạch {T[0]['ke_hoach']} buổi/tuần"
                                                                                  if T and T[0]["ke_hoach"] else "")
                       + (f" · buổi cuối {r['cuoi']:%d/%m}" if r["cuoi"] else ""))
        ui.sec("Lịch tháng của khách")
        lich(k, "tk_hlv", cho_khach=False)
