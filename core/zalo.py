# Hoàng Anh Coaching v1.0 (2026-10-31) — link mở đúng khung chat Zalo theo số điện thoại
import re


def link(sdt) -> str:
    so = re.sub(r"\D", "", str(sdt or ""))
    if so.startswith("84"):
        so = "0" + so[2:]
    return f"https://zalo.me/{so}" if len(so) >= 9 else ""
