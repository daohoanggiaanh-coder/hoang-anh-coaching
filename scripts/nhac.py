# Hoàng Anh Coaching v2.4 — chạy bởi GitHub Actions: gửi nhắc Telegram buổi sáng / buổi tối.
# python -m scripts.nhac sang | toi   (cần biến môi trường SHEETS_WEBAPP_URL, SHEETS_TOKEN, TELEGRAM_BOT_TOKEN, APP_URL)
from __future__ import annotations

import sys

from core import db, thong_bao as tb


def main() -> int:
    kieu = (sys.argv[1] if len(sys.argv) > 1 else "").strip()
    if kieu not in ("sang", "toi"):
        gio = db.now_vn().hour
        kieu = "sang" if gio < 12 else "toi"
    if not tb.token():
        print("Thiếu TELEGRAM_BOT_TOKEN — bỏ qua.")
        return 0
    if not db._url():
        print("Thiếu SHEETS_WEBAPP_URL — bỏ qua.")
        return 0
    kq = tb.chay(kieu)
    print(f"{kieu}: đã gửi {kq['gui']} tin · kết nối mới: {', '.join(kq['lien_ket']) or 'không'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
