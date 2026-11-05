# Hoàng Anh Coaching v2.4 (2026-11-05) — XƯNG HÔ CÁ NHÂN HOÁ trên cổng khách.
"""Mọi chữ "bạn" trong nội dung khách thấy được đổi thành cách HLV gọi khách (ô "Gọi khách là" — VD "chị Ngân", "anh Đại").
Làm ở 1 chỗ: bọc các hàm hiển thị chữ của Streamlit; chỉ áp dụng cho phiên đăng nhập của khách (session_state["_xung_goi"])."""
from __future__ import annotations

import re

import streamlit as st
from streamlit.delta_generator import DeltaGenerator

_HAM = ("markdown", "caption", "info", "success", "warning", "error", "write", "subheader", "header", "title", "toast",
        "button", "toggle", "checkbox", "select_slider", "slider", "text_input", "text_area", "pills", "segmented_control",
        "expander", "number_input", "selectbox", "radio", "multiselect", "date_input", "popover", "tabs")
_RE = re.compile(r"(?<![\wÀ-ỹ])(BẠN|[Bb]ạn)(?![\wÀ-ỹ])(?!\s+(?:bè|đời|học|gái|trai|thân|đồng hành|cùng tập))")
_DA = False


def doi(text, goi: str | None = None):
    goi = goi if goi is not None else st.session_state.get("_xung_goi")
    if not goi or not isinstance(text, str) or goi.lower() == "bạn":
        return text

    def thay(m):
        w = m.group(1)
        return goi.upper() if w == "BẠN" else (goi[:1].upper() + goi[1:]) if w[0] == "B" else goi
    return _RE.sub(thay, text)


def _doi_x(v):
    return [doi(x) for x in v] if isinstance(v, (list, tuple)) and all(isinstance(x, str) for x in v) else doi(v)


def _boc(fn):
    def f(*a, **kw):
        a = list(a)
        i = 1 if a and isinstance(a[0], DeltaGenerator) else 0
        if len(a) > i:
            a[i] = _doi_x(a[i])
        for kk in ("body", "label", "tabs", "text"):
            if kk in kw:
                kw[kk] = _doi_x(kw[kk])
        return fn(*a, **kw)
    f._hac_xh = True
    return f


def cai():
    """Gọi 1 lần mỗi lần chạy (idempotent): bọc hàm của lớp DeltaGenerator và các hàm st.* đã gắn sẵn."""
    global _DA
    if _DA:
        return
    for h in _HAM:
        g = getattr(DeltaGenerator, h, None)
        if g and not getattr(g, "_hac_xh", False):
            setattr(DeltaGenerator, h, _boc(g))
        s = getattr(st, h, None)
        if s and not getattr(s, "_hac_xh", False):
            setattr(st, h, _boc(s))
    _DA = True


def goi_khach(k: dict) -> str:
    from core import store
    return store.xung(k)[0]
