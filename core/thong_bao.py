# Hoàng Anh Coaching v2.4 (2026-11-05) — NHẮC QUA TELEGRAM (thông báo thật trên điện thoại khách).
"""Cách chạy:
  - Bot Telegram của HLV (tạo ở @BotFather) → TELEGRAM_BOT_TOKEN, TELEGRAM_BOT_USERNAME trong Secrets.
  - Khách bấm link t.me/<bot>?start=<mã liên kết> → bấm Start → web (hoặc lần chạy nhắc kế tiếp) đọc getUpdates, lưu chat_id.
  - Gửi tự động: GitHub Actions chạy scripts/nhac.py theo giờ (sáng 6h30, tối 20h giờ VN) — xem .github/workflows/nhac.yml.
Lưu trong bảng DinhDuong: tg|<mã> = {chat_id, ten, luc} · tg_hlv = {chat_id} · tg_gui|<mã>|<ngày>|<loại> (chống gửi trùng)."""
from __future__ import annotations

import hashlib
import hmac
from datetime import date, timedelta

import requests

from core import config, db, store

API = "https://api.telegram.org/bot{}/{}"


def token() -> str:
    return str(config.get("TELEGRAM_BOT_TOKEN", "") or "")


def bot() -> str:
    return str(config.get("TELEGRAM_BOT_USERNAME", "") or "").lstrip("@")


def san_sang() -> bool:
    return bool(token() and bot())


def _goi(method: str, **params) -> dict:
    try:
        r = requests.post(API.format(token(), method), json=params, timeout=20)
        return r.json()
    except (requests.RequestException, ValueError):
        return {"ok": False}


def gui(chat_id, text: str) -> bool:
    if not token() or not chat_id:
        return False
    return bool(_goi("sendMessage", chat_id=chat_id, text=text, disable_web_page_preview=True).get("ok"))


def ma_lien_ket(ma: str) -> str:
    """Mã ngắn, không đoán được (ký bằng token bot) — dùng trong link Start."""
    sig = hmac.new(("hac-tg|" + token()).encode(), ma.encode(), hashlib.sha256).hexdigest()[:8]
    return f"{ma}_{sig}"


def link(ma: str) -> str:
    return f"https://t.me/{bot()}?start={ma_lien_ket(ma)}"


def link_hlv() -> str:
    return f"https://t.me/{bot()}?start={ma_lien_ket('HLV')}"


def chat_cua(ma: str) -> str | None:
    v = db.latest("DinhDuong", ma).get(f"tg|{ma}") or {}
    return None if v.get("xoa") else v.get("chat_id")


def chat_hlv() -> str | None:
    return (db.latest("DinhDuong").get("tg_hlv") or {}).get("chat_id") or config.get("TELEGRAM_COACH_CHAT_ID")


def cap_nhat_lien_ket() -> list[str]:
    """Đọc tin /start <mã> mới gửi tới bot → lưu chat_id cho đúng khách (hoặc HLV). Trả về tên đã liên kết."""
    if not token():
        return []
    r = _goi("getUpdates", timeout=0, allowed_updates=["message"])
    out = []
    ds = {k["ma"]: k for k in store.clients()}
    for u in r.get("result") or []:
        m = u.get("message") or {}
        t = str(m.get("text") or "")
        if not t.startswith("/start "):
            continue
        code = t.split(" ", 1)[1].strip()
        ma = code.rsplit("_", 1)[0]
        if code != ma_lien_ket(ma):
            continue
        chat = m.get("chat", {}).get("id")
        if ma == "HLV":
            if chat_hlv() != chat:
                db.append("DinhDuong", "tg_hlv", {"chat_id": chat, "luc": db.now_str()}, "telegram")
                gui(chat, "✅ Đã kết nối — anh sẽ nhận tóm tắt mỗi sáng từ Hoàng Anh Coaching.")
                out.append("HLV")
        elif ma in ds and chat_cua(ma) != chat:
            db.append("DinhDuong", f"tg|{ma}", {"chat_id": chat, "ten": ds[ma].get("ho_ten"), "luc": db.now_str(), "ma_kh": ma}, "telegram", ma)
            goi, toi = store.xung(ds[ma])
            gui(chat, f"✅ Chào {goi}! Từ giờ {toi} sẽ nhắc lịch tập, cân buổi sáng và giữ chuỗi lửa cho {goi} qua đây nhé 💪 — HLV Hoàng Anh")
            out.append(ds[ma].get("ho_ten", ma))
    if r.get("result"):
        _goi("getUpdates", offset=r["result"][-1]["update_id"] + 1, timeout=0)     # đánh dấu đã đọc
    return out


def huy(ma: str, nguoi: str) -> bool:
    return db.append("DinhDuong", f"tg|{ma}", {"xoa": 1, "ma_kh": ma}, nguoi, ma)


# ------------------------------------------------------------------ nội dung nhắc
def _da_gui(ma: str, ngay: date, loai: str) -> bool:
    return bool(db.latest("DinhDuong", ma).get(f"tg_gui|{ma}|{ngay.isoformat()}|{loai}"))


def _ghi_gui(ma: str, ngay: date, loai: str) -> None:
    db.append("DinhDuong", f"tg_gui|{ma}|{ngay.isoformat()}|{loai}", {"ma_kh": ma}, "telegram", ma)


def tin_sang(k: dict, hom: date) -> str | None:
    from core import chu_ky, goi, wow
    if not goi.trang_thai(k, hom)["vao"]:
        return None
    g, toi = store.xung(k)
    G = g[:1].upper() + g[1:]
    dong = [f"☀️ Chào buổi sáng {g}!"]
    b = [x for x in store.buoi([k], hom, hom) if x["trang_thai"] == "hen"]
    if b:
        dong.append(f"🏋️ Hôm nay {g} có buổi tập lúc {store.gio_s(b[0]['gio'])}" + (f" ở {b[0]['dia_diem']}" if b[0].get("dia_diem") else "") + ".")
        ck = chu_ky.dieu_chinh(k["ma"], hom, k)
        if ck and ck["nang"] and ck["khach"]:
            dong.append(ck["khach"])
    dong.append("⚖️ Nhớ cân buổi sáng (sau vệ sinh, trước ăn) và ghi vào web nhé.")
    d = store._d(k.get("ngay_sinh"))
    if d and (d.month, d.day) == (hom.month, hom.day):
        dong.insert(0, f"🎂 Chúc mừng sinh nhật {G}! Chúc {g} một tuổi mới khoẻ mạnh, rực rỡ — {toi} luôn đồng hành cùng {g} 💛")
    moi = [m for m in wow.moc(k, hom) if m["id"] not in wow.moc_trang_thai(k["ma"])["khach_xem"]]
    if moi:
        dong.append(f"🏅 {G} vừa đạt mốc {moi[-1]['icon']} {moi[-1]['ten']}! Vào web xem nhé.")
    url = config.get("APP_URL")
    if url:
        dong.append(str(url))
    return "\n".join(dong)


def tin_toi(k: dict, hom: date) -> str | None:
    """Tối 20h: còn việc chưa làm để giữ chuỗi lửa."""
    from core import dong_luc as dl, goi
    if not goi.trang_thai(k, hom)["vao"]:
        return None
    t = dl.tong_hop(k, hom, store.quyen(k))
    thieu = [x for x in t["nv"] if not x["xong"] and not x.get("phu")]
    if not thieu:
        return None
    g, _ = store.xung(k)
    return (f"🔥 Còn 4 tiếng nữa là hết ngày — {g} còn {len(thieu)} việc để giữ chuỗi lửa: "
            + ", ".join(x["ten"] for x in thieu[:3]) + ". Làm nhanh 2 phút thôi nè!")


def tom_tat_hlv(hom: date) -> str:
    from core import chu_ky, goi
    DS = store.clients(ca_ngung=False)
    H = store.hens()
    B = store.buoi(DS, hom, hom, H)
    by = {k["ma"]: k for k in DS}
    dong = [f"📋 Hôm nay {store.THU[hom.weekday()]} {hom:%d/%m}: {len([b for b in B if b['trang_thai'] == 'hen'])} buổi"]
    for b in B:
        k = by.get(b["ma"], {})
        ck = chu_ky.dieu_chinh(b["ma"], hom, k) if k else None
        dong.append(f"• {store.gio_s(b['gio'])} {k.get('ho_ten', '')}" + (f" · {store.phong(k)}" if k and store.phong(k) else "")
                    + (f" 🌸 ngày {ck['ngay_thu']}" if ck and ck["nang"] else ""))
    from core import inbody
    ib = []
    for b in B:
        k = by.get(b["ma"])
        t = inbody.trang_thai(k, hom) if k and b["trang_thai"] != "huy" else None
        if t and t["han"] <= hom:
            ib.append(f"{k['ho_ten']} ({inbody.mo_ta(t)})")
    if ib:
        dong.append("📏 Đo InBody buổi hôm nay: " + "; ".join(ib))
    sap, no = [], []
    for k in DS:
        t = goi.trang_thai(k, hom, H)
        if t["ma"] in ("sap_het", "het_han", "het_buoi"):
            sap.append(f"{k['ho_ten']} ({t['ten']})")
        c = goi.cong_no(k)
        if c["con_no"]:
            no.append(f"{k['ho_ten']} {goi.vnd(c['con_no'])}")
        d = store._d(k.get("ngay_sinh"))
        if d and any(((hom + timedelta(days=j)).month, (hom + timedelta(days=j)).day) == (d.month, d.day) for j in range(4)):
            dong.append(f"🎂 Sinh nhật {k['ho_ten']} {d:%d/%m}")
    if sap:
        dong.append("⏳ Gói: " + "; ".join(sap))
    if no:
        dong.append("💳 Còn nợ: " + "; ".join(no))
    return "\n".join(dong)


def chay(kieu: str, hom: date | None = None) -> dict:
    """kieu: sang | toi. Chạy bởi GitHub Actions (scripts/nhac.py). Không gửi trùng trong ngày."""
    hom = hom or db.now_vn().date()
    kq = {"lien_ket": cap_nhat_lien_ket(), "gui": 0}
    for k in store.clients(ca_ngung=False):
        chat = chat_cua(k["ma"])
        if not chat or _da_gui(k["ma"], hom, kieu):
            continue
        t = tin_sang(k, hom) if kieu == "sang" else tin_toi(k, hom)
        if t and gui(chat, t):
            _ghi_gui(k["ma"], hom, kieu)
            kq["gui"] += 1
    if kieu == "sang" and chat_hlv() and not _da_gui("HLV", hom, "sang"):
        if gui(chat_hlv(), tom_tat_hlv(hom)):
            _ghi_gui("HLV", hom, "sang")
    return kq

