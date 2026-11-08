"""v3.4 — Quét phiếu InBody hàng loạt: AI đọc từng phiếu → tự đoán khách theo tên in trên phiếu → HLV xác nhận → lưu.

Module không import streamlit. Việc đọc ảnh nằm ở core.tu_van.read_inbody (AI có thể đọc nhầm → luôn cho HLV xem lại).
"""
from __future__ import annotations

import difflib
from datetime import date

from core import db, store, tien_do
from core.nhap_kh_atlas import khong_dau

LUU = [k for k, *_ in tien_do.CHI_SO if k in ("can_nang", "pbf", "smm", "khoi_mo", "mo_noi_tang")] + [k for k, *_ in tien_do.THEM]


def _tokens(s: str) -> list[str]:
    return [t for t in khong_dau(s).replace(".", " ").replace("_", " ").split() if t]


def diem_ten(ten_phieu: str, ten_khach: str) -> float:
    """0–1: tên trên phiếu (thường không dấu, có khi chỉ tên gọi / viết tắt) giống tên khách tới đâu."""
    a, b = _tokens(ten_phieu), _tokens(ten_khach)
    if not a or not b:
        return 0.0
    if a == b:
        return 1.0
    sa, sb = " ".join(a), " ".join(b)
    r = difflib.SequenceMatcher(None, sa, sb).ratio()
    # mọi chữ trên phiếu đều có trong tên khách (vd phiếu ghi "Lan" / "Thi Lan", khách "Nguyễn Thị Lan")
    if set(a) <= set(b):
        r = max(r, 0.7 + 0.25 * len(a) / len(b) if a[-1] == b[-1] else 0.6)
    elif a[-1] == b[-1]:                                   # trùng tên gọi (chữ cuối)
        r = max(r, 0.55)
    return round(min(r, 1.0), 3)


def khop_khach(ten_phieu: str, DS: list[dict], phong: str | None = "Atlas") -> tuple[str | None, float]:
    """(mã khách đoán được, điểm). Ưu tiên khách đang tập; hoà điểm thì ưu tiên phòng `phong`. Điểm < 0.6 → None."""
    if not ten_phieu:
        return None, 0.0
    tot = None
    for k in DS:
        d = diem_ten(ten_phieu, k.get("ho_ten", ""))
        if d <= 0:
            continue
        uu = ((k.get("trang_thai") or "Đang tập") == "Đang tập", bool(phong) and store.phong(k) == phong)
        kh = (d, uu)
        if tot is None or kh > tot[0]:
            tot = (kh, k["ma"])
    if not tot or tot[0][0] < 0.6:
        return None, tot[0][0] if tot else 0.0
    # 2 khách cùng điểm cao nhất (vd 2 bạn tên "Lan" cùng phòng) → không tự chọn
    cung = [k for k in DS if diem_ten(ten_phieu, k.get("ho_ten", "")) == tot[0][0]
            and (k.get("trang_thai") or "Đang tập") == "Đang tập"]
    if len(cung) > 1 and tot[0][0] < 1:
        return None, tot[0][0]
    return tot[1], tot[0][0]


def luu(k: dict, ngay: date, dot: str, vals: dict, user: dict, anh_id: str | None = None) -> list[str]:
    """Lưu 1 phiếu cho khách `k`. Trả danh sách việc đã làm (để báo HLV)."""
    ma, nguoi = k["ma"], user.get("name", "")
    so = {x: vals.get(x) for x in LUU if tien_do._so(vals.get(x))}
    lam = []
    if so and tien_do.luu_so_do(ma, ngay, dot, so, "Quét phiếu InBody", user, gop=True):
        lam.append(f"{len(so)} chỉ số")
    if so.get("can_nang") and tien_do.luu_can(ma, ngay, so["can_nang"], user):
        lam.append("cân")
    if anh_id and tien_do.luu_anh(ma, ngay, dot, "inbody", anh_id, user):
        lam.append("ảnh phiếu")
    bmr = tien_do._so(vals.get("bmr"))
    if bmr:
        hs = dict(db.latest("DinhDuong").get(f"hs|{ma}", {}))
        if str(hs.get("bmr_inbody") or "") != str(int(bmr)):
            db.append("DinhDuong", f"hs|{ma}", {**{x: y for x, y in hs.items() if not x.startswith("_")},
                                                "bmr_inbody": int(bmr)}, nguoi, ma)
            lam.append("BMR cho thực đơn")
    moi = {}
    if vals.get("chieu_cao") and not tien_do._so(k.get("chieu_cao")):
        moi["chieu_cao"] = vals["chieu_cao"]
    if vals.get("gioi_tinh") in ("Nam", "Nữ") and not k.get("gioi_tinh"):
        moi["gioi_tinh"] = vals["gioi_tinh"]
    if moi:
        store.save_client({**k, **moi}, nguoi)
        lam.append("hồ sơ (" + ", ".join(moi) + ")")
    return lam
