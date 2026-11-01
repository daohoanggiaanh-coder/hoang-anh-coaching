# Hoàng Anh Coaching v1.1 (2026-10-31) — cấu hình trung tâm
"""Đọc cấu hình từ st.secrets (Streamlit Cloud) hoặc biến môi trường (chạy local / test)."""
from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path

VERSION = "v1.7"
VERSION_DATE = "2026-11-01"
VERSION_LABEL = f"{VERSION} · {VERSION_DATE}"
BRAND = "HOÀNG ANH COACHING"

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
LOCAL_DIR = DATA_DIR / "_local"          # chạy thử khi chưa nối Google Sheets (không đưa lên GitHub)
FONTS = ROOT / "assets" / "fonts"


def get(key: str, default=None):
    """Ưu tiên st.secrets, sau đó biến môi trường."""
    try:
        import streamlit as st

        if key in st.secrets:
            return st.secrets[key]
    except Exception:  # noqa: BLE001
        pass
    return os.environ.get(key, default)


@lru_cache(maxsize=None)
def load_json(name: str):
    with open(DATA_DIR / name, encoding="utf-8") as f:
        return json.load(f)
