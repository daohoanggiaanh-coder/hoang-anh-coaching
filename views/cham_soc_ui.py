# Hoàng Anh Coaching v2.4 (2026-11-05) — trang HLV "✨ Chăm sóc khách": tin tổng kết tuần, mốc thành tích + thư khen,
# thư tổng kết khoá (PDF), nhắc qua Telegram.
from __future__ import annotations

import html
from datetime import timedelta

import pandas as pd
import streamlit as st

from core import buoi as bt, db, store, thong_bao as tb, wow

E = html.escape
S = st.session_state


def _gui_tg(k: dict, txt: str, key: str):
    chat = tb.chat_cua(k["ma"]) if tb.san_sang() else None
    if chat and st.button("📨 Gửi qua Telegram", key=f"tg_{key}", use_container_width=True):
        st.toast("Đã gửi qua Telegram ✓" if tb.gui(chat, txt) else "Gửi chưa được — kiểm tra bot")


def tong_quan(DS: list[dict]):
    hom = db.now_vn().date()
    rows = []
    for k in DS:
        m = wow.moc(k, hom)
        tt = wow.moc_trang_thai(k["ma"])
        moi = [x["ten"] for x in m if x["id"] not in tt["hlv_gui"]]
        d = store._d(k.get("ngay_sinh"))
        sn = next((j for j in range(8) if d and ((hom + timedelta(days=j)).month, (hom + timedelta(days=j)).day) == (d.month, d.day)), None)
        t2 = hom - timedelta(days=6)
        ss_all = bt.sessions(k["ma"])
        pr = sum(len(wow.ky_luc_moi(s["bai"], [x for x in ss_all if x["ngay"] < s["ngay"]])) for s in ss_all if s["ngay"] >= t2)
        rows.append({"Khách": k["ho_ten"], "Mốc mới chưa chúc": ", ".join(moi) or "—",
                     "Sinh nhật": ("🎂 hôm nay" if sn == 0 else f"🎂 còn {sn} ngày") if sn is not None else "",
                     "Kỷ lục 7 ngày": pr or "", "Telegram": "✅" if tb.chat_cua(k["ma"]) else "—"})
    st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)


def trang(k: dict, u: dict):
    from views.coach import _soan
    ma = k["ma"]
    hom = db.now_vn().date()
    t1, t2, t3, t4 = st.tabs(["📨 Tin tổng kết tuần", "🏅 Mốc thành tích", "🎓 Thư tổng kết khoá", "🔔 Nhắc qua Telegram"])
    with t1:
        st.caption("Web soạn từ số liệu tuần trước (buổi tập, tổng tạ, kỷ lục, cân TB, giấc ngủ) theo cách anh xưng hô với khách. "
                   "Sửa thoải mái rồi gửi — gợi ý gửi sáng thứ Hai.")
        txt = st.text_area("Tin nhắn", wow.tin_tuan(k, hom), height=230, key=f"tt_{ma}")
        _soan(k, txt, f"tuan_{ma}", u, hien=False)
        _gui_tg(k, txt, f"tuan_{ma}")
    with t2:
        m = wow.moc(k, hom)
        tt = wow.moc_trang_thai(ma)
        if not m:
            st.info("Khách chưa đạt mốc nào — mốc đầu tiên thường là 10 buổi tập hoặc giảm 1 kg.")
        for x in reversed(m):
            da = x["id"] in tt["hlv_gui"]
            with st.expander(f"{x['icon']} {x['ten']}" + (" · ✅ đã chúc" if da else " · 🆕 chưa chúc"), expanded=not da):
                thu = st.text_area("Thư khen", wow.thu_khen(k, x), height=110, key=f"tk_{ma}_{x['id']}")
                _soan(k, thu, f"moc_{ma}_{x['id']}", u, hien=False)
                _gui_tg(k, thu, f"moc_{ma}_{x['id']}")
                if not da and st.button("✔️ Đánh dấu đã chúc", key=f"dc_{ma}_{x['id']}"):
                    wow.danh_dau_moc(ma, {"hlv_gui": [x["id"]]}, u["name"])
                    st.rerun()
        st.caption("Khách cũng thấy thẻ chúc mừng mốc mới ngay trên trang Tổng quan của mình.")
    with t3:
        st.caption("PDF tặng khách khi kết thúc khoá / gia hạn: ảnh trước – sau, thay đổi cân · mỡ · eo, sức mạnh tăng, tổng buổi, "
                   "tổng tạ, và thư của anh.")
        loi = st.text_area("Thư của HLV (để trống = web viết sẵn theo cách xưng hô)", "", height=120, key=f"thu_{ma}")
        if st.button("📄 Tạo thư tổng kết khoá", key=f"pdftk_{ma}", type="primary"):
            with st.spinner("Đang dựng PDF…"):
                S[f"_pdftk_{ma}"] = wow.pdf_tong_ket(k, loi)
        if S.get(f"_pdftk_{ma}"):
            st.download_button("⬇️ Tải PDF", S[f"_pdftk_{ma}"], f"Thu_tong_ket_{k['ho_ten']}.pdf", "application/pdf", key=f"dltk_{ma}")
        sm = wow.tien_bo_suc_manh(ma)
        if sm:
            st.dataframe(pd.DataFrame([{"Bài": r["bai"], "1RM đầu": r["dau"], "1RM tốt nhất": r["moi"], "Tăng": f"+{r['pct']}%"} for r in sm]),
                         hide_index=True, use_container_width=True)
    with t4:
        telegram(k, u)


def telegram(k: dict | None, u: dict):
    if not tb.san_sang():
        st.warning("Chưa cài bot Telegram — làm 1 lần theo hướng dẫn dưới đây (khoảng 10 phút).")
        huong_dan()
        return
    a, b = st.columns(2)
    if a.button("🔄 Kiểm tra khách mới bấm Start", use_container_width=True):
        moi = tb.cap_nhat_lien_ket()
        st.toast("Đã kết nối: " + ", ".join(moi) if moi else "Chưa có ai mới bấm Start")
    b.link_button("🔗 Kết nối Telegram của anh (nhận tóm tắt mỗi sáng)", tb.link_hlv(), use_container_width=True)
    st.caption(f"Telegram của anh: {'✅ đã kết nối' if tb.chat_hlv() else 'chưa kết nối — bấm nút trên, bấm Start trong Telegram, rồi bấm Kiểm tra'}")
    if k:
        chat = tb.chat_cua(k["ma"])
        goi, _ = store.xung(k)
        st.markdown(f"**{E(k['ho_ten'])}:** " + ("✅ đã nhận nhắc qua Telegram" if chat else "chưa kết nối"))
        if not chat:
            txt = (f"{goi[:1].upper() + goi[1:]} bấm link này rồi bấm Start để nhận nhắc lịch tập, cân buổi sáng và giữ chuỗi lửa "
                   f"trên điện thoại nhé: {tb.link(k['ma'])}")
            from views.coach import _soan
            _soan(k, txt, f"tglink_{k['ma']}", u)
        else:
            c1, c2 = st.columns(2)
            if c1.button("📨 Gửi thử tin sáng nay", key=f"tgthu_{k['ma']}", use_container_width=True):
                t = tb.tin_sang(k, db.now_vn().date())
                st.toast("Đã gửi ✓" if t and tb.gui(chat, t) else "Không có gì để gửi / gửi lỗi")
            if c2.button("🚫 Ngắt Telegram của khách", key=f"tghuy_{k['ma']}", use_container_width=True):
                tb.huy(k["ma"], u["name"])
                st.rerun()
    st.caption("Tự động: sáng 6h30 (lịch tập hôm nay, nhắc cân, sinh nhật, mốc mới, lời nhắn quan tâm ngày chu kỳ) · tối 20h (còn việc "
               "chưa làm để giữ chuỗi lửa) · anh nhận tóm tắt mỗi sáng (buổi hôm nay, 🌸, gói sắp hết, còn nợ, sinh nhật). "
               "Khách hết gói / bảo lưu thì không nhận.")


def huong_dan():
    st.markdown("""
**Bước 1 — Tạo bot (trên điện thoại, 2 phút)**
1. Mở Telegram, tìm **@BotFather** (có dấu tích xanh) → bấm **Start** → gõ `/newbot`.
2. Đặt tên hiển thị, VD `Hoàng Anh Coaching`, rồi tên đăng nhập kết thúc bằng `bot`, VD `HoangAnhCoachingBot`.
3. BotFather gửi lại 1 dòng **token** (dạng `123456789:ABC...`) — đây là mật khẩu của bot, **không gửi cho ai**, kể cả Claude.

**Bước 2 — Dán vào Secrets của web (Streamlit Cloud)**
share.streamlit.io → app hoang-anh-coaching → ⋮ → **Settings → Secrets**, thêm 2 dòng rồi Save:
```
TELEGRAM_BOT_TOKEN = "token BotFather gửi"
TELEGRAM_BOT_USERNAME = "HoangAnhCoachingBot"
```

**Bước 3 — Bật gửi tự động mỗi ngày (GitHub)**
github.com/daohoanggiaanh-coder/hoang-anh-coaching → **Settings → Secrets and variables → Actions → New repository secret**, tạo 5 secret
(giá trị chép y hệt trong Secrets của Streamlit): `SHEETS_WEBAPP_URL`, `SHEETS_TOKEN`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_BOT_USERNAME`, `APP_URL`.
Xong vào tab **Actions** → bấm bật workflow **"Nhắc khách qua Telegram"** nếu GitHub hỏi.

**Bước 4 — Kết nối:** bấm "Kết nối Telegram của anh" ở trên → Start. Với khách: gửi link kết nối (tab này, từng khách) hoặc khách tự bấm ở trang Hồ sơ.
""")
