"""v3.6 — Buổi tư vấn F1: chuyển khách đã đăng ký thành hồ sơ khách (không import streamlit, để kiểm thử được)."""
from __future__ import annotations

from datetime import date

from core import khao_sat as ks, store, thau_hieu as th, tien_do as td, tu_van as tv
from core.nhap_kh_atlas import khong_dau


def sang_khach(h: dict, nguoi: str) -> str | None:
    """Khách đăng ký → tạo (hoặc cập nhật) hồ sơ khách + số đo đầu khoá + hồ sơ Thấu hiểu. Trả mã khách."""
    from core import quet_inbody as qi
    DS = store.clients()
    ten, sdt = str(h.get("ho_ten") or "").strip(), "".join(ch for ch in str(h.get("sdt") or "") if ch.isdigit())
    if not ten:
        return None
    k = next((x for x in DS if khong_dau(x.get("ho_ten", "")) == khong_dau(ten)
              and (not sdt or "".join(ch for ch in str(x.get("sdt") or "") if ch.isdigit()) in ("", sdt))), None)
    ngay = date.fromisoformat(str(h.get("ngay_f1") or date.today())[:10])
    moi = dict(k or {"ma": store.ma_moi(DS), "trang_thai": "Đang tập"})
    for f, v in (("ho_ten", ten), ("sdt", str(h.get("sdt") or "").strip()), ("gioi_tinh", h.get("gioi_tinh")),
                 ("chieu_cao", h.get("chieu_cao")), ("muc_tieu", tv.GOALS.get(h.get("muc_tieu"), "")),
                 ("chan_thuong", h.get("ghi_chu_kh")), ("khung_gio", h.get("lich_co_dinh")), ("ly_do", (h.get("ks") or {}).get("ly_do_sau"))):
        if v not in (None, "") and not moi.get(f):
            moi[f] = v
    if h.get("khan_cap") and not moi.get("lh_ten"):
        moi["lh_ten"] = h["khan_cap"]
    gk = str(h.get("ket_qua") or "").replace("Đăng ký ", "", 1)
    G = next((x for x in store.goi_list() if x.get("ten") == gk), None)
    if G and not k:
        lo = G.get("loai", "buoi")
        moi.update({"goi_ten": G["ten"], "goi_loai": lo, "gia": G.get("gia", ""), "ngay_bat_dau": ngay.isoformat(),
                    **({"goi_buoi": G.get("so")} if lo == "buoi" else {"goi_so": G.get("so")})})
    if not store.save_client(moi, nguoi):
        return None
    k2 = store.client(moi["ma"]) or moi
    vals = {c: h.get(c) for c in ("can_nang", "pbf", "smm", "khoi_mo", "mo_noi_tang", "bmr", "diem_inbody", "nuoc", "protein",
                                  "khoang_chat", "tuoi_may", "tuoi")}
    vals = {a: b for a, b in vals.items() if tv.num(b) is not None}
    vong = {"v_nguc": h.get("v_nguc"), "v_eo": h.get("v_eo"), "v_bung": h.get("v_bung"), "v_hong": h.get("v_hong"),
            "v_dui": h.get("v_dui_p") or h.get("v_dui_t"), "v_tay": h.get("v_tay_p") or h.get("v_tay_t")}
    vong = {a: b for a, b in vong.items() if tv.num(b) is not None}
    if vals:
        qi.luu(k2, ngay, "dau_khoa", vals, {"name": nguoi})
    if vong:
        td.luu_so_do(k2["ma"], ngay, "dau_khoa", vong, "Số đo buổi tư vấn F1", {"name": nguoi}, gop=True)
    if h.get("ks"):
        th.luu(k2["ma"], ks.ap_vao_ho_so(th.ho_so(k2["ma"]), h["ks"], ngay.isoformat()), nguoi)
    return k2["ma"]
