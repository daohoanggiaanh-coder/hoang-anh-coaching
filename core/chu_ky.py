# Hoàng Anh Coaching v2.3 (2026-11-05) — CHU KỲ KINH NGUYỆT (khách nữ): HLV ghi ngày bắt đầu các kỳ → web dự đoán kỳ tới,
# tự gợi ý giảm tạ / bớt hiệp / buổi nhẹ đúng những ngày đó và nhắc khách nhẹ nhàng.
"""Dữ liệu NHẠY CẢM: chỉ HLV xem / sửa (bảng DinhDuong, khoá ck|<mã>). Khách không thấy ngày, chỉ thấy lời nhắc (kín đáo hoặc nói rõ
tuỳ HLV chọn).
Căn cứ: tổng quan McNulty và cộng sự (2020, Sports Medicine) — hiệu suất có thể giảm NHẸ ở đầu chu kỳ (pha nang noãn sớm), mức độ
khác nhau nhiều giữa từng người → điều chỉnh theo cảm nhận của chính khách, không áp cứng cho mọi người. Dự đoán ngày chỉ là ước tính."""
from __future__ import annotations

from datetime import date, timedelta

from core import db, store

MUC = {
    "nhe": {"ten": "Nhẹ — gần như không ảnh hưởng", "ngay": 1, "kg": 0.95, "hiep": 0, "nghi_ngay1": False},
    "vua": {"ten": "Vừa — mệt, đau bụng nhẹ 1–2 ngày đầu", "ngay": 2, "kg": 0.85, "hiep": 1, "nghi_ngay1": False},
    "nang": {"ten": "Nặng — đau nhiều, mệt rõ", "ngay": 3, "kg": 0.8, "hiep": 1, "nghi_ngay1": True},
}
MAC_DINH = {"ngay_bd": [], "do_dai": 28, "so_ngay": 5, "muc": "vua", "kieu_nhac": "kin_dao", "bat": True, "ghi_chu": ""}


def cai_dat(ma: str) -> dict:
    v = db.latest("DinhDuong", ma).get(f"ck|{ma}") or {}
    out = {**MAC_DINH, **{k: x for k, x in v.items() if k in MAC_DINH}}
    out["ngay_bd"] = sorted({d for d in (store._d(x) for x in out.get("ngay_bd") or []) if d})
    return out


def luu(ma: str, c: dict, nguoi: str) -> bool:
    v = {**c, "ngay_bd": [d.isoformat() if hasattr(d, "isoformat") else str(d) for d in c.get("ngay_bd") or []], "ma_kh": ma}
    return db.append("DinhDuong", f"ck|{ma}", v, nguoi, ma)


def do_dai_tb(c: dict) -> int:
    """Độ dài chu kỳ trung bình từ các lần đã ghi (6 lần gần nhất, chỉ lấy khoảng 21–45 ngày), thiếu thì dùng số HLV đặt."""
    ds = c["ngay_bd"][-7:]
    kc = [(b - a).days for a, b in zip(ds, ds[1:]) if 21 <= (b - a).days <= 45]
    return round(sum(kc) / len(kc)) if kc else int(c.get("do_dai") or 28)


def cac_ky(c: dict, den: date) -> list[tuple[date, bool]]:
    """[(ngày bắt đầu, là dự đoán?)] — kỳ đã ghi + kỳ dự đoán tới ngày `den`."""
    if not c["ngay_bd"]:
        return []
    out = [(d, False) for d in c["ngay_bd"]]
    n = do_dai_tb(c)
    d = c["ngay_bd"][-1] + timedelta(days=n)
    while d <= den + timedelta(days=n):
        out.append((d, True))
        d += timedelta(days=n)
    return out


def ngay_thu(c: dict, d: date) -> tuple[int, bool] | None:
    """Ngày thứ mấy của kỳ (1 = ngày đầu) nếu `d` rơi vào kỳ đã ghi / dự đoán; kèm cờ dự đoán."""
    for bd, du in cac_ky(c, d):
        i = (d - bd).days + 1
        if 1 <= i <= int(c.get("so_ngay") or 5):
            return i, du
    return None


def dieu_chinh(ma: str, d: date, k: dict | None = None) -> dict | None:
    """Gợi ý cho buổi ngày `d` (None nếu không rơi vào kỳ hoặc HLV tắt)."""
    k = k or store.client(ma) or {}
    if str(k.get("gioi_tinh") or "") != "Nữ":
        return None
    c = cai_dat(ma)
    if not c.get("bat") or not c["ngay_bd"]:
        return None
    x = ngay_thu(c, d)
    if not x:
        return None
    i, du = x
    m = MUC.get(c["muc"], MUC["vua"])
    nang = i <= m["ngay"]
    return {"ngay_thu": i, "du_doan": du, "nang": nang, "nghi": m["nghi_ngay1"] and i == 1,
            "kg": m["kg"] if nang else 1.0, "hiep": m["hiep"] if nang else 0, "kieu_nhac": c["kieu_nhac"],
            "hlv": (f"🌸 Ngày {i} chu kỳ{' (dự đoán)' if du else ''}: "
                    + ("đề xuất buổi phục hồi nhẹ / nghỉ." if m["nghi_ngay1"] and i == 1 else
                       f"tạ ~{m['kg'] * 100:.0f}%, bớt {m['hiep']} hiệp, tránh gập bụng mạnh / treo người." if nang else
                       "tập bình thường nếu khách thấy khoẻ; hỏi cảm nhận.")),
            "khach": loi_nhan(c["kieu_nhac"], i, nang, m)}


def loi_nhan(kieu: str, i: int, nang: bool, m: dict) -> str:
    if not nang:
        return ""
    if kieu == "ro":
        return ("🌸 Những ngày này cơ thể cần nhẹ nhàng hơn — HLV đã giảm nhẹ tạ và số hiệp cho bạn. Uống nước ấm, ăn thêm "
                "thịt bò / rau xanh đậm (giàu sắt), ngủ sớm. Thấy khoẻ thì cứ tập như bình thường nhé 💛")
    return ("💛 Hôm nay HLV đã điều chỉnh buổi tập nhẹ hơn một chút cho bạn (tạ nhẹ hơn, bớt 1 hiệp). "
            "Lắng nghe cơ thể — thấy khoẻ thì cứ tập như bình thường nhé.")


def sap_toi(ma: str, tu: date, so_ngay: int = 35) -> list[dict]:
    """Các ngày sắp tới rơi vào kỳ (cho HLV xem trước)."""
    c = cai_dat(ma)
    out = []
    for j in range(so_ngay):
        d = tu + timedelta(days=j)
        x = ngay_thu(c, d)
        if x:
            out.append({"ngay": d, "ngay_thu": x[0], "du_doan": x[1]})
    return out
