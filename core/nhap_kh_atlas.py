"""v2.8 — Chép khách anh đang dạy ở Atlas Academy sang HAC (CHỈ CHÉP, không sửa / xoá gì bên Atlas).

Đọc qua Apps Script của Atlas (Secrets ATLAS_SHEETS_WEBAPP_URL / ATLAS_SHEETS_TOKEN):
  KhachHang (hồ sơ, bản mới nhất theo ma_kh) · SoDo (số đo / InBody) · LichHen (lịch cố định "mau") · BuoiTap (buổi đã tập).
Mỗi khách chép sang mang `ma_atlas` để chạy lại không bị trùng, và `phong_tap` = phòng anh chọn (mặc định "Atlas").
"""
from __future__ import annotations

import json
import re
import unicodedata
from datetime import date

import pandas as pd

from core import config, db, store, tien_do

SHEETS = {"kh": "KhachHang", "sodo": "SoDo", "hen": "LichHen", "buoi": "BuoiTap"}
SO_DO = [k for k, *_ in tien_do.CHI_SO]


def co_cau_hinh() -> bool:
    import os
    return bool(os.environ.get("HAC_FAKE_ATLAS")) or bool(config.get("ATLAS_SHEETS_WEBAPP_URL") and config.get("ATLAS_SHEETS_TOKEN"))


NGUON: dict[str, list[dict]] | None = None     # dữ liệu từ file tải lên (xlsx / json) — thay cho đọc qua Apps Script


def doc_file(name: str, data: bytes) -> dict[str, list[dict]]:
    """File Google Sheets của Atlas tải về dạng .xlsx (mọi sheet) hoặc .json {sheet: [dòng]}."""
    import io
    if name.lower().endswith(".json"):
        d = json.loads(data.decode("utf-8"))
    else:
        x = pd.read_excel(io.BytesIO(data), sheet_name=None, dtype=str)
        d = {k: v.fillna("").to_dict("records") for k, v in x.items() if k in SHEETS.values()}
    if not d.get(SHEETS["kh"]):
        raise ValueError("File không có sheet KhachHang của Atlas")
    return d


def doc(sheet: str) -> list[dict]:
    if NGUON is not None:
        return NGUON.get(sheet, [])
    import os
    if os.environ.get("HAC_FAKE_ATLAS"):            # chỉ dùng khi chạy thử trên máy (không có trên web)
        return json.load(open(os.environ["HAC_FAKE_ATLAS"], encoding="utf-8")).get(sheet, [])
    import requests
    r = requests.get(config.get("ATLAS_SHEETS_WEBAPP_URL"), timeout=90,
                     params={"token": config.get("ATLAS_SHEETS_TOKEN"), "action": "read", "sheet": sheet}).json()
    if not r.get("ok"):
        raise RuntimeError(r.get("error") or "Atlas không trả dữ liệu")
    return r.get("rows") or []


def _s(v) -> str:
    s = "" if v is None else str(v).strip()
    return "" if s in ("nan", "None", "NaT") else s


def _n(v) -> float | None:
    try:
        x = float(_s(v).replace(",", "."))
    except ValueError:
        return None
    return None if x != x else x


def _xoa(v) -> bool:
    return _s(v) not in ("", "0", "0.0", "False")


def khong_dau(s) -> str:
    s = unicodedata.normalize("NFD", _s(s).lower()).replace("đ", "d")
    return re.sub(r"\s+", " ", "".join(c for c in s if unicodedata.category(c) != "Mn")).strip()


def cung_pt(pt, ten_pt: str) -> bool:
    """'Đào Hoàng Anh' khớp 'Hoàng Anh' (so 2 chữ cuối, bỏ dấu) — giống cách Atlas tô màu PT."""
    a, b = khong_dau(pt).split(), khong_dau(ten_pt).split()
    return bool(a and b) and a[-2:] == b[-2:]


def khach_atlas(rows: list[dict]) -> list[dict]:
    """Bản mới nhất mỗi ma_kh, bỏ khách đã xoá."""
    last: dict[str, dict] = {}
    for r in sorted(rows, key=lambda r: _s(r.get("thoi_gian"))):
        if _s(r.get("ma_kh")):
            last[_s(r["ma_kh"])] = r
    return [r for r in last.values() if not _xoa(r.get("xoa"))]


def _ngay(v) -> str:
    t = pd.to_datetime(_s(v)[:10], errors="coerce")
    return "" if pd.isna(t) else t.date().isoformat()


def buoi_atlas(rows: list[dict]) -> dict[str, list[dict]]:
    """{ma_kh: [buổi]} — bỏ buổi đã huỷ / xoá (dòng huỷ trỏ huy_id tới id buổi gốc)."""
    def key(r):
        return _s(r.get("id")) or ("tg:" + _s(r.get("thoi_gian")) if _s(r.get("thoi_gian")) else "")
    huy = {_s(r.get("huy_id")) for r in rows} - {""}
    out: dict[str, list[dict]] = {}
    for r in rows:
        if _xoa(r.get("xoa")) or key(r) in huy or not _ngay(r.get("ngay")) or not _s(r.get("ma_kh")):
            continue
        out.setdefault(_s(r["ma_kh"]), []).append(r)
    return out


def lich_atlas(rows: list[dict]) -> dict[str, list[dict]]:
    """{ma_kh: lịch cố định mới nhất [{thu, gio}]} từ dòng loai = "mau"."""
    out: dict[str, tuple[str, list]] = {}
    for r in sorted(rows, key=lambda r: (_s(r.get("tu_ngay")), _s(r.get("thoi_gian")))):
        if _s(r.get("loai")) != "mau" or _xoa(r.get("xoa")):
            continue
        try:
            sl = [{"thu": int(x["thu"]), "gio": _s(x.get("gio"))[:5]} for x in json.loads(r.get("lich") or "[]")]
        except (TypeError, ValueError, KeyError):
            continue
        out[_s(r.get("ma_kh"))] = (_s(r.get("tu_ngay")), sl)
    return {k: v[1] for k, v in out.items()}


def chuyen_khach(a: dict, hac: list[dict], phong: str, so_buoi_web: int, lich: list[dict] | None) -> dict:
    """Hồ sơ Atlas → hồ sơ khách HAC (chưa lưu)."""
    cu = next((k for k in hac if _s(k.get("ma_atlas")) == _s(a.get("ma_kh"))), None)
    nb = _n(a.get("so_buoi_goi"))
    da = int((_n(a.get("buoi_da_tap_truoc")) or 0) + max(so_buoi_web - int(_n(a.get("moc_buoi_web")) or 0), 0))
    tt = _s(a.get("trang_thai")) or "Đang tập"
    tt = {"Đã kết thúc": "Ngưng tập"}.get(tt, tt)
    tt = tt if tt in store.TRANG_THAI else "Đang tập"
    gioi = _s(a.get("gioi_tinh"))
    ns = _s(a.get("ngay_sinh")) or (f"{int(_n(a.get('nam_sinh')))}-01-01" if _n(a.get("nam_sinh")) else "")
    ghi = " · ".join(x for x in [_s(a.get("ghi_chu")), f"Chép từ Atlas ({_s(a.get('ma_kh'))})"] if x)
    k = {**(cu or {}),
         "ma": (cu or {}).get("ma") or store.ma_moi(hac),
         "ho_ten": _s(a.get("ho_ten")), "sdt": _s(a.get("sdt")).lstrip("'"), "email": _s(a.get("email")),
         "ten_zalo": _s(a.get("ten_zalo")), "goi_khach": _s(a.get("goi_khach")), "xung_toi": _s(a.get("xung_toi")),
         "gioi_tinh": "Nữ" if khong_dau(gioi).startswith("nu") else ("Nam" if gioi else ""),
         "ngay_sinh": ns, "nghe_nghiep": _s(a.get("nghe_nghiep")), "muc_tieu": _s(a.get("muc_tieu")),
         "muc_tieu_loai": _s(a.get("muc_tieu_loai")), "chan_thuong": _s(a.get("chan_thuong")) or _s(a.get("suc_khoe")),
         "benh_nen": _s(a.get("suc_khoe")), "khung_gio": _s(a.get("khung_gio")),
         "goi_ten": " · ".join(x for x in [_s(a.get("loai_goi")), f"{int(nb)} buổi" if nb else ""] if x),
         "goi_loai": "buoi", "goi_so": int(nb) if nb else "", "goi_buoi": int(nb) if nb else "",
         "gia": int(_n(a.get("gia_goi")) or 0) or "", "da_tap_truoc": da,
         "ngay_bat_dau": _ngay(a.get("ngay_bat_dau")), "ngay_ket_thuc": _ngay(a.get("ngay_het_han")),
         "trang_thai": tt, "ghi_chu": (cu or {}).get("ghi_chu") or ghi,
         "phong_tap": phong, "dia_diem": (cu or {}).get("dia_diem") or phong, "ma_atlas": _s(a.get("ma_kh"))}
    if lich:
        k["lich"] = json.dumps(lich, ensure_ascii=False)
    return k


def _bai(b: dict) -> dict:
    sets = [{"kg": h.get("kg"), "lan": h.get("lan"), **({"rpe": h["rpe"]} if h.get("rpe") else {})}
            for h in (b.get("hiep") or []) if _n(h.get("lan"))]
    ten = _s(b.get("ten")) or _s(b.get("bai")) or _s(b.get("id"))
    return {"bai": ten, "ten": ten, "sets": sets, **({"ghi_chu": b["ghi_chu"]} if b.get("ghi_chu") else {})}


def chep(chon: list[dict], phong: str, nguoi: str, so_do: bool = True, buoi: bool = True, lich: bool = True) -> dict:
    """Chép các khách Atlas đã chọn. Trả về số dòng đã ghi mỗi loại."""
    dem = {"khách": 0, "số đo": 0, "buổi tập": 0}
    SD = doc(SHEETS["sodo"]) if so_do else []
    B = buoi_atlas(doc(SHEETS["buoi"]))
    L = lich_atlas(doc(SHEETS["hen"])) if lich else {}
    from core import giao_an
    for a in chon:
        hac = store.clients()
        mk = _s(a.get("ma_kh"))
        k = chuyen_khach(a, hac, phong, len(B.get(mk, [])), L.get(mk))
        av = _s(a.get("anh_dai_dien"))
        if len(av) > 500 and not k.get("anh_dai_dien"):          # Atlas lưu ảnh đại diện dạng base64 trong ô
            try:
                import base64
                up = db.upload_images({"x": base64.b64decode(av)}, f"HAC_{k['ma']}_av_")
                if up:
                    k["anh_dai_dien"] = up["x"]
            except Exception:  # noqa: BLE001
                pass
        if not store.save_client(k, nguoi):
            continue
        dem["khách"] += 1
        ma, u = k["ma"], {"name": nguoi}
        bmr = None
        for r in sorted([r for r in SD if _s(r.get("ma_kh")) == mk and not _xoa(r.get("xoa"))],
                        key=lambda r: _s(r.get("ngay"))):
            nd = _ngay(r.get("ngay") or r.get("thoi_gian"))
            vals = {c: _n(r.get(c)) for c in SO_DO if _n(r.get(c))}
            if nd and vals and tien_do.luu_so_do(ma, date.fromisoformat(nd), "Atlas", vals, _s(r.get("ghi_chu")), u):
                dem["số đo"] += 1
            bmr = _n(r.get("bmr")) or bmr
        if bmr:
            hs = dict(db.latest("DinhDuong").get(f"hs|{ma}", {}))
            if not hs.get("bmr_inbody"):
                db.append("DinhDuong", f"hs|{ma}", {**{x: y for x, y in hs.items() if not x.startswith("_")},
                                                     "bmr_inbody": int(bmr)}, nguoi, ma)
        if buoi:
            da = {str(x.get("id")) for x in giao_an.logs(ma)}
            for r in B.get(mk, []):
                lid = "atl_" + (_s(r.get("id")) or khong_dau(_s(r.get("thoi_gian"))).replace(" ", "_"))
                if lid in da:
                    continue
                try:
                    bai = json.loads(r.get("bai_json") or "[]")
                except (TypeError, ValueError):
                    bai = []
                nk = {"id": lid, "ngay": _ngay(r.get("ngay")), "gio": _s(r.get("gio")).lstrip("'")[:5],
                      "nguoi_ghi": "hlv", "nguon": "Atlas", "ghi_chu": _s(r.get("ghi_chu")),
                      "bai": [_bai(b) for b in bai if isinstance(b, dict)]}
                giao_an.save_log(ma, nk, nguoi)
                dem["buổi tập"] += 1
    return dem
