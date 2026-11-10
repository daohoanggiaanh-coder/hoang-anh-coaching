"""v3.8 — Biểu đồ tiến độ rõ ràng: trên = cân từng ngày (ghi số kg), dưới = khối cơ (kg) + % mỡ.
Khách không đo InBody → % mỡ ƯỚC TÍNH từ vòng bụng / eo gần nhất (công thức RFM), vẽ nét đứt và ghi '≈'. Mọi điểm đặt đúng ngày nhập."""
from __future__ import annotations

import streamlit as st
from plotly.subplots import make_subplots

from core import tien_do as td, ui

DO, XANH, CAM = "#C0392B", "#2E7D4F", "#D9822B"


def _nhan(vals: list[float], fmt: str, toi_da: int = 14) -> list[str]:
    """Ghi số ở mọi điểm nếu ít; nhiều điểm → cách quãng, luôn giữ điểm đầu, cuối, thấp nhất, cao nhất."""
    n = len(vals)
    if n <= toi_da:
        return [fmt.format(v) for v in vals]
    buoc = -(-n // toi_da)
    giu = {0, n - 1, vals.index(min(vals)), vals.index(max(vals))}
    return [fmt.format(v) if (i % buoc == 0 or i in giu) else "" for i, v in enumerate(vals)]


def ve(k: dict, sd=None, cn=None, h: int = 520, key: str = "bd", so_nhan: int = 14):
    D = td.chuoi_tien_do(k, sd, cn)
    can, co, mo, mu = D["can"], D["co"], D["mo"], D["mo_uoc"]
    if not can and not co and not mo and not mu:
        st.caption("Chưa có lần cân / đo nào để vẽ biểu đồ.")
        return
    duoi = bool(co or mo or mu)
    fig = make_subplots(rows=2 if duoi else 1, cols=1, shared_xaxes=True, vertical_spacing=0.13,
                        row_heights=[0.55, 0.45] if duoi else [1], specs=[[{}], [{"secondary_y": True}]] if duoi else [[{}]],
                        subplot_titles=["⚖️ Cân nặng (kg)"] + ([" · ".join(x for x, c in (("💪 Khối cơ (kg)", co), ("🔥 % mỡ", mo or mu)) if c)] if duoi else []))
    if can:
        x, y = [a for a, _ in can], [b for _, b in can]
        fig.add_scatter(x=x, y=y, mode="lines+markers+text", name="Cân (kg)", text=_nhan(y, "{:.1f}", so_nhan), textposition="top center",
                        textfont=dict(size=12, color="#B8912F"), line=dict(color=ui.VANG, width=3), marker=dict(size=7, color=ui.VANG),
                        hovertemplate="%{x|%d/%m/%Y}: <b>%{y:.1f} kg</b><extra></extra>", row=1, col=1)
        lo, hi = min(y), max(y)
        dich = td._so(k.get("can_muc_tieu"))
        if dich and lo - 5 <= dich <= hi + 5:
            fig.add_hline(y=dich, line_dash="dot", line_color=XANH, annotation_text=f"Mục tiêu {dich:g} kg",
                          annotation_position="bottom right", row=1, col=1)
            lo, hi = min(lo, dich), max(hi, dich)
        pad = max((hi - lo) * 0.25, 1.0)
        fig.update_yaxes(range=[lo - pad, hi + pad * 1.4], row=1, col=1)
    if duoi:
        if co:
            x, y = [a for a, _ in co], [b for _, b in co]
            fig.add_scatter(x=x, y=y, mode="lines+markers+text", name="Khối cơ (kg)", text=_nhan(y, "{:.1f}", so_nhan),
                            textposition="top center", textfont=dict(size=11, color=XANH), line=dict(color=XANH, width=2.5),
                            marker=dict(size=7), hovertemplate="%{x|%d/%m/%Y}: cơ <b>%{y:.1f} kg</b><extra></extra>",
                            row=2, col=1, secondary_y=False)
            lo, hi = min(y), max(y)
            sp = max(hi - lo, 1.0)                     # cơ nằm nửa TRÊN khung dưới, % mỡ nửa DƯỚI → 2 đường không đè số lên nhau
            fig.update_yaxes(range=[lo - sp * 1.6, hi + sp * 0.5], row=2, col=1, secondary_y=False, tickformat=".0f")
        if mo:
            x, y = [a for a, _ in mo], [b for _, b in mo]
            fig.add_scatter(x=x, y=y, mode="lines+markers+text", name="% mỡ (InBody)", text=_nhan(y, "{:.1f}%", so_nhan),
                            textposition="bottom center", textfont=dict(size=11, color=DO), line=dict(color=DO, width=2.5),
                            marker=dict(size=7, symbol="diamond"), hovertemplate="%{x|%d/%m/%Y}: <b>%{y:.1f}% mỡ</b> (InBody)<extra></extra>",
                            row=2, col=1, secondary_y=bool(co))
        if mu:
            x, y, v = [a for a, _, _ in mu], [b for _, b, _ in mu], [c for _, _, c in mu]
            fig.add_scatter(x=x, y=y, mode="lines+markers+text", name="% mỡ ước tính (từ vòng)", text=_nhan(y, "≈{:.0f}%", so_nhan),
                            textposition="bottom center", textfont=dict(size=11, color=CAM), line=dict(color=CAM, width=2, dash="dash"),
                            marker=dict(size=7, symbol="circle-open"), customdata=v,
                            hovertemplate="%{x|%d/%m/%Y}: ≈<b>%{y:.1f}% mỡ</b> ước tính từ vòng %{customdata}<extra></extra>",
                            row=2, col=1, secondary_y=bool(co))
        pm = [b for _, b in mo] + [b for _, b, _ in mu]
        if pm:
            lo, hi = min(pm), max(pm)
            sp = max(hi - lo, 1.0)
            # không có khối cơ → % mỡ dùng trục chính của khung dưới (trục phụ đứng một mình bị Plotly kéo ra cả biểu đồ)
            fig.update_yaxes(range=[lo - sp * 0.6, hi + sp * (1.6 if co else 0.6)], row=2, col=1, secondary_y=bool(co), showgrid=not co,
                             title_text="% mỡ", ticksuffix="%", tickformat=".0f")
        if co:
            fig.update_yaxes(title_text="kg cơ", row=2, col=1, secondary_y=False)
    ui.layout(fig, h if duoi else int(h * 0.62))
    fig.update_layout(legend=dict(orientation="h", y=-0.1, font=dict(size=11)), margin=dict(l=36, r=6, t=34, b=6), hovermode="closest")
    fig.update_xaxes(tickformat="%d/%m")
    if duoi:
        fig.update_xaxes(showticklabels=False, row=1, col=1)       # ngày chỉ ghi ở khung dưới, khỏi đè tiêu đề
    fig.update_annotations(font=dict(size=13))
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False}, key=key)
    if mu:
        st.caption("Ngày không đo InBody: **% mỡ ước tính** (nét đứt, ký hiệu ≈) tính từ vòng bụng (hoặc eo) và chiều cao theo công thức "
                   "RFM (Woolcott & Bergman, 2018). Đây là ước tính, sai số vài % — dùng để xem xu hướng, không so trực tiếp với số InBody.")
