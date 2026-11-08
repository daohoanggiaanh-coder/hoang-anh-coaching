"""v3.2 — Màu nền sáng / tối: 🕒 tự động theo giờ (6h–18h sáng, còn lại tối) · ☀️ luôn sáng · 🌙 luôn tối.
Lưu theo tài khoản (bảng DinhDuong, key ui|tên_đăng_nhập) + nhớ trên máy (localStorage) → lần sau mở vẫn đúng.
Đổi bằng menu ⋮ Settings của Streamlit cũng được ghi nhớ trên máy đó."""
from __future__ import annotations

import json

import streamlit as st
import streamlit.components.v1 as components

from core import db

NEN = {"auto": "🕒 Tự động theo giờ", "light": "☀️ Luôn sáng", "dark": "🌙 Luôn tối"}


def doc(username: str) -> dict:
    v = db.latest("DinhDuong").get(f"ui|{username}", {})
    return v if isinstance(v, dict) else {}


def chon(user: dict):
    """Ô chọn ở thanh bên + đồng bộ xuống trình duyệt."""
    un = user.get("username") or user.get("name", "")
    v = doc(un)
    nen = v.get("nen") if v.get("nen") in NEN else "auto"
    ts = int(v.get("ts") or 0)
    S = st.session_state
    S["nen_ui"] = S.get("nen_ui_moi", nen)

    def _doi():
        moi = S["nen_ui"]
        S["nen_ui_moi"] = moi
        S["nen_ts"] = int(db.now_vn().timestamp() * 1000)
        db.append("DinhDuong", f"ui|{un}", {**{k: x for k, x in v.items() if not str(k).startswith("_")},
                                            "nen": moi, "ts": S["nen_ts"]}, user.get("name", ""), user.get("ma_kh", ""))
    st.selectbox("🌗 Màu nền", list(NEN), key="nen_ui", format_func=NEN.get, on_change=_doi,
                 help="Tự động: sáng từ 6h–18h, tối từ 18h–6h (theo giờ điện thoại). Chọn xong web nhớ cho lần sau.")
    ts = max(ts, int(S.get("nen_ts", 0)))
    if ts:
        components.html("<script>(function(){var n=0;function f(){try{if(window.parent.hacNenSet){window.parent.hacNenSet("
                        f"{json.dumps(S['nen_ui'])},{ts});return;}}}}catch(e){{}}if(++n<20)setTimeout(f,500);}}f();}})();</script>",
                        height=0)
