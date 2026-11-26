# Hoàng Anh Coaching v4.2 — chạy bởi GitHub Actions 21h30: email tổng kết ngày cho HLV.
# python -m scripts.mail_ngay   (cần SHEETS_WEBAPP_URL, SHEETS_TOKEN)
from __future__ import annotations

import sys

from core import db, mail


def main() -> int:
    if not db._url():
        print("Thiếu SHEETS_WEBAPP_URL / SHEETS_TOKEN trong GitHub Secrets — bỏ qua.")
        return 0
    if not mail.cai_dat()["cuoi_ngay"]:
        print("HLV đã tắt tổng kết cuối ngày — bỏ qua.")
        return 0
    ok, m = mail.gui(*mail.tong_ket_ngay())
    print(("Đã gửi tổng kết → " if ok else "Chưa gửi được: ") + m)
    return 0


if __name__ == "__main__":
    sys.exit(main())
