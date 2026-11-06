# Hoàng Anh Coaching v2.6 (2026-11-06) — bảng "Lịch tập sắp tới theo giáo án" (HLV + khách).
from __future__ import annotations

import html

import streamlit as st

from core import lich_tap as lt, store

E = html.escape


def bang(k: dict, so_ngay: int = 21, tieu_de: str = "📅 Lịch tập sắp tới theo giáo án"):
    ds = lt.sap_toi(k, so_ngay)
    if not ds:
        return
    ck = lt.chu_ky(k)
    st.markdown(f"**{tieu_de}**" + (f"  \n<span style='font-size:.78rem;color:#8b8577'>Thứ tự giáo án: {E(' → '.join(ck))}</span>" if ck else
                                    "  \n<span style='font-size:.78rem;color:#8b8577'>Chưa có giáo án — chỉ hiện ngày giờ</span>"),
                unsafe_allow_html=True)
    o = "".join(
        f'<div class="hac-b" style="flex-wrap:nowrap"><span class="t" style="min-width:92px">{store.THU[x["ngay"].weekday()]} {x["ngay"]:%d/%m}</span>'
        f'<span style="min-width:52px;font-weight:700">{E(store.gio_s(x["gio"]))}</span>'
        f'<span class="n">{"<b>Buổi " + E(x["buoi"]) + "</b> · " + E(x["ten"]) if x.get("buoi") else "—"}</span></div>' for x in ds)
    st.markdown(o, unsafe_allow_html=True)
    st.caption("Buổi nối tiếp theo buổi khách tập gần nhất — nghỉ 1 buổi thì lịch tự lùi, không bỏ buổi nào trong chu kỳ.")
