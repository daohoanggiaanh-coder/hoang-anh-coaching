# Hoàng Anh Coaching v1.0 (2026-10-31) — hồ sơ khách, lịch cố định, hẹn / dời / nghỉ / đã tập, đếm buổi, tin Zalo
# (chuyển từ mục 🔒 Khách riêng của Atlas Academy v3.71 — giữ nguyên tên trường để chuyển dữ liệu 1-1)
from __future__ import annotations

import hashlib
import json
from datetime import date, datetime, timedelta

from core import db

THU = ["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7", "Chủ nhật"]
TRANG_THAI = ["Đang tập", "Tạm dừng", "Ngưng tập"]
HINH_THUC = ["Trực tiếp", "Online", "Kết hợp"]
FIELDS = ["ma", "ho_ten", "sdt", "ten_zalo", "goi_khach", "xung_toi", "dia_diem", "goi_buoi", "da_tap_truoc", "gia",
          "ngay_bat_dau", "lich", "trang_thai", "ghi_chu", "xoa", "ngay_sinh",
          "gioi_tinh", "chieu_cao", "muc_tieu", "can_muc_tieu", "hinh_thuc", "chan_thuong",
          "muc_tieu_loai", "muc_tieu_mo", "muc_tieu_co", "muc_tieu_eo", "muc_tieu_ngay",     # v1.1: lộ trình (chỉ HLV xem)
          "goi_ten", "goi_loai", "goi_so",                                                      # v1.2: gói theo buổi / tuần / tháng
          "quyen",                                                                              # v1.3: mục khách được thấy / dùng
          "anh_dai_dien", "avatar_y", "avatar_r",                                               # v1.8: ảnh đại diện
          "email", "nghe_nghiep", "khu_vuc", "kinh_nghiem", "mon_da_tap", "buoi_co_the",       # v1.9: hồ sơ đầy đủ
          "khung_gio", "cong_viec", "giac_ngu", "ly_do", "benh_nen", "thuoc", "lh_ten", "lh_quan_he", "lh_sdt", "can_mong_muon"]                                                                              # v1.3: mục khách được thấy / dùng
LOAI_GOI = {"buoi": "buổi", "tuan": "tuần", "thang": "tháng"}
# v1.3 — quyền cổng khách: id → (nhóm, nhãn, mô tả). Mặc định bật hết; HLV tắt từng mục cho từng khách.
QUYEN = {
    "giao_an": ("🏋️ Tập luyện", "Xem giáo án", "Giáo án HLV soạn (bài, hiệp, lần, RPE, nghỉ)"),
    "ghi_buoi": ("🏋️ Tập luyện", "Tự ghi buổi tập", "Khách tự nhập kg × lần từng hiệp + xem lịch sử, lời nhắn HLV"),
    "tu_tao_plan": ("🏋️ Tập luyện", "Tự tạo plan", "Khách tự tạo / sửa plan riêng khi tập một mình"),
    "so_ta": ("🏋️ Tập luyện", "Số tạ & kỷ lục", "Biểu đồ số tạ, 1RM ước tính, kỷ lục"),
    "cardio": ("🏃 Cardio", "Xem target & tiến độ cardio", "Target từng ngày, phần bù, biểu đồ hoàn thành tuần"),
    "ghi_cardio": ("🏃 Cardio", "Tự nhập kết quả cardio", "Khách nhập phút, độ dốc, tốc độ, ảnh màn hình máy"),
    "thuc_don": ("🍽 Dinh dưỡng", "Xem thực đơn", "Thực đơn hôm nay + 7 ngày (gram từng món)"),
    "chi_so_dd": ("🍽 Dinh dưỡng", "Chỉ số kcal & macro", "Số kcal, đạm, tinh bột, béo, dự kiến tốc độ, cách tính"),
    "doi_mon": ("🍽 Dinh dưỡng", "Đổi món", "Tự đổi món trong bữa + bảng món tương đương"),
    "so_thich_an": ("🍽 Dinh dưỡng", "Sửa sở thích ăn", "Số bữa, giờ tập, chế độ ăn, món không ăn"),
    "bo_sung": ("🍽 Dinh dưỡng", "Thực phẩm bổ sung", "Gợi ý bổ sung HLV chọn (không bắt buộc)"),
    "di_cho": ("🍽 Dinh dưỡng", "Danh sách đi chợ", "Tổng thực phẩm cả tuần"),
    "can": ("📈 Tiến độ", "Cân hằng ngày", "Tự nhập cân + biểu đồ trung bình 7 ngày"),
    "so_do": ("📈 Tiến độ", "Số đo & ảnh", "So sánh số đo đầu khoá → hiện tại, ảnh trước / sau"),
    "thanh_qua": ("🏆 Thành quả", "Hồ sơ HLV & thành quả học viên", "Ảnh trước / sau, kết quả các học viên đã đồng ý đăng"),
    "lich": ("🏠 Tổng quan", "Lịch hẹn & gói", "Buổi hẹn 2 tuần tới, số buổi / ngày còn trong gói"),
}


def quyen(k: dict | None) -> dict[str, bool]:
    q = (k or {}).get("quyen")
    if isinstance(q, str):
        try:
            q = json.loads(q) if q.strip() else {}
        except ValueError:
            q = {}
    q = q if isinstance(q, dict) else {}
    return {x: bool(q.get(x, True)) for x in QUYEN}


def trang_khach(q: dict[str, bool]) -> dict[str, bool]:
    """Trang nào của cổng khách được hiện (tắt hết mục con → ẩn luôn trang)."""
    return {"tap": q["giao_an"] or q["ghi_buoi"] or q["so_ta"] or q["tu_tao_plan"], "an": q["thuc_don"], "tien_do": q["can"] or q["so_do"],
            "cardio": q["cardio"] or q["ghi_cardio"], "thanh_qua": q["thanh_qua"]}


# ------------------------------------------------------------------ khách
def clients(ca_ngung: bool = True) -> list[dict]:
    out = [{**v, "ma": v.get("ma") or k} for k, v in db.latest("KhachHang").items()]
    if not ca_ngung:
        out = [r for r in out if (r.get("trang_thai") or "Đang tập") == "Đang tập"]
    return sorted(out, key=lambda r: (TRANG_THAI.index(r.get("trang_thai") or "Đang tập")
                                      if (r.get("trang_thai") or "Đang tập") in TRANG_THAI else 9, str(r.get("ho_ten", ""))))


def client(ma: str) -> dict | None:
    v = db.latest("KhachHang").get(str(ma))
    return {**v, "ma": v.get("ma") or ma} if v else None


def ma_moi(ds: list[dict]) -> str:
    so = [int(str(r.get("ma", ""))[1:]) for r in ds if str(r.get("ma", ""))[1:].isdigit()]
    return f"R{(max(so) if so else 0) + 1:03d}"


def save_client(k: dict, nguoi: str) -> bool:
    k = {f: k.get(f, "") for f in FIELDS}
    if k.get("xoa"):
        k["xoa"] = 1
    return db.append("KhachHang", k["ma"], k, nguoi, k["ma"])


def tuoi(k: dict, hom_nay: date | None = None) -> int | None:
    d = _d(k.get("ngay_sinh"))
    if not d:
        return None
    t = hom_nay or db.now_vn().date()
    return t.year - d.year - ((t.month, t.day) < (d.month, d.day))


# ------------------------------------------------------------------ lịch
def hens(ma: str | None = None) -> dict[str, dict]:
    return db.latest("LichHen", ma, ca_xoa=True)


def hen_id(ma: str, ngay: date, gio: str) -> str:
    return f"{ma}|{ngay.isoformat()}|{gio}"


def ghi_hen(ma: str, ngay: date, gio: str, trang_thai: str, nguoi: str, dia_diem: str = "", ghi_chu: str = "",
            goc: str = "") -> bool:
    """trang_thai: hen (thêm / dời tới) · xong (đã tập) · huy (nghỉ)."""
    hid = goc if goc and trang_thai in ("huy", "xong") else hen_id(ma, ngay, gio)
    return db.append("LichHen", hid, {"ma": ma, "ngay": ngay.isoformat(), "gio": gio, "dia_diem": dia_diem,
                                      "trang_thai": trang_thai, "ghi_chu": ghi_chu, "goc": goc}, nguoi, ma)


def lich_co_dinh(k: dict) -> list[dict]:
    try:
        v = k.get("lich")
        v = json.loads(v) if isinstance(v, str) else (v or [])
        return [x for x in v if isinstance(x, dict) and "thu" in x]
    except (TypeError, ValueError):
        return []


def _d(v) -> date | None:
    try:
        return datetime.strptime(str(v)[:10], "%Y-%m-%d").date()
    except ValueError:
        return None


def buoi(ds: list[dict], tu: date, den: date, H: dict[str, dict] | None = None) -> list[dict]:
    """Các buổi từ tu → den: lịch cố định + buổi hẹn thêm / dời; kèm trạng thái (hen / xong / huy)."""
    H = hens() if H is None else H
    by = {k["ma"]: k for k in ds}
    out: dict[str, dict] = {}
    for k in ds:
        if (k.get("trang_thai") or "Đang tập") != "Đang tập":
            continue
        bd = _d(k.get("ngay_bat_dau")) or date.min
        d = tu
        while d <= den:
            for s in lich_co_dinh(k):
                if int(s["thu"]) == d.weekday() and d >= bd:
                    hid = hen_id(k["ma"], d, str(s.get("gio", "")))
                    out[hid] = {"id": hid, "ma": k["ma"], "ngay": d, "gio": str(s.get("gio", "")),
                                "dia_diem": s.get("dia_diem") or k.get("dia_diem", ""), "trang_thai": "hen", "co_dinh": True}
            d += timedelta(days=1)
    for hid, h in H.items():
        nd = _d(h.get("ngay"))
        if h.get("ma") not in by:
            continue
        if hid in out:
            out[hid].update({"trang_thai": h.get("trang_thai", "hen"), "ghi_chu": h.get("ghi_chu", "")})
        elif nd and tu <= nd <= den:
            out[hid] = {"id": hid, "ma": h["ma"], "ngay": nd, "gio": h.get("gio", ""), "dia_diem": h.get("dia_diem", ""),
                        "trang_thai": h.get("trang_thai", "hen"), "ghi_chu": h.get("ghi_chu", ""), "co_dinh": False}
    return sorted(out.values(), key=lambda b: (b["ngay"], str(b["gio"])))


def da_tap(k: dict, H: dict[str, dict] | None = None) -> int:
    H = hens() if H is None else H
    bd = _d(k.get("ngay_bat_dau")) or date.min
    n = sum(1 for h in H.values() if h.get("ma") == k["ma"] and h.get("trang_thai") == "xong" and (_d(h.get("ngay")) or bd) >= bd)
    try:
        n += int(float(k.get("da_tap_truoc") or 0))
    except ValueError:
        pass
    return n


# ------------------------------------------------------------------ v1.2: gói theo thời gian (Online 12 tuần, 1 tháng…)
def loai_goi(k: dict) -> str:
    lo = str(k.get("goi_loai") or "").strip()
    return lo if lo in LOAI_GOI else "buoi"


def han_goi(k: dict) -> date | None:
    """Ngày hết gói với gói tuần / tháng (ngày bắt đầu + thời lượng); gói buổi → None."""
    lo, bd = loai_goi(k), _d(k.get("ngay_bat_dau"))
    try:
        n = int(float(k.get("goi_so") or 0))
    except ValueError:
        n = 0
    if lo == "buoi" or not bd or n <= 0:
        return None
    if lo == "tuan":
        return bd + timedelta(weeks=n)
    m = bd.month - 1 + n
    y, m = bd.year + m // 12, m % 12 + 1
    import calendar
    return date(y, m, min(bd.day, calendar.monthrange(y, m)[1]))


def con_ngay(k: dict, hom_nay: date | None = None) -> int | None:
    h = han_goi(k)
    if not h:
        return None
    return max((h - (hom_nay or db.now_vn().date())).days, 0)


def mo_ta_goi(k: dict, H: dict | None = None, hom_nay: date | None = None) -> str:
    """VD 'Online 12 tuần · còn 81 ngày (hết 21/01/2027)' hoặc 'Gói 12 buổi · còn 9 buổi'."""
    ten = str(k.get("goi_ten") or "").strip()
    if loai_goi(k) != "buoi":
        h, c = han_goi(k), con_ngay(k, hom_nay)
        return (ten or f"Gói {k.get('goi_so')} {LOAI_GOI[loai_goi(k)]}") + (f" · còn {c} ngày (hết {h:%d/%m/%Y})" if h else "")
    c = con_lai(k, H)
    return (ten or (f"Gói {int(float(k.get('goi_buoi') or 0))} buổi" if k.get("goi_buoi") else "Chưa ghi gói")) + \
        (f" · còn {c} buổi" if c is not None else "")


def goi_list() -> list[dict]:
    """Bảng gói của HLV (lưu trong Sheet riêng, không nằm trong code công khai)."""
    v = db.latest("DinhDuong").get("cai_dat|goi") or {}
    return [g for g in v.get("ds", []) if g.get("ten")]


def save_goi_list(ds: list[dict], nguoi: str) -> bool:
    return db.append("DinhDuong", "cai_dat|goi", {"ds": ds}, nguoi)


def con_lai(k: dict, H: dict[str, dict] | None = None) -> int | None:
    if loai_goi(k) != "buoi":
        return None
    try:
        g = int(float(k.get("goi_buoi") or 0))
    except ValueError:
        g = 0
    return max(g - da_tap(k, H), 0) if g else None


# ------------------------------------------------------------------ tin nhắn (như tin nhắn thường: không ký tên)
def xung(k: dict) -> tuple[str, str]:
    goi = str(k.get("goi_khach") or "").split("|")[0].strip() or "bạn"
    toi = str(k.get("xung_toi") or "").strip() or ("mình" if goi == "bạn" else "em")
    return goi, toi


def _chon(pool: list[str], seed: str) -> str:
    return pool[int(hashlib.md5(seed.encode()).hexdigest(), 16) % len(pool)]


def gio_s(g: str) -> str:
    g = str(g or "").strip()
    if ":" in g:
        h, m = g.split(":")[:2]
        try:
            return f"{int(h)}h{m}" if m != "00" else f"{int(h)}h"
        except ValueError:
            return g
    return g


def ngay_s(d: date, hom_nay: date) -> str:
    if d == hom_nay:
        return "hôm nay"
    if d == hom_nay + timedelta(days=1):
        return "ngày mai"
    return f"{THU[d.weekday()]} ({d:%d/%m})"


def _buoi_trong_ngay(g: str) -> str:
    try:
        h = int(str(g).split(":")[0])
    except ValueError:
        return ""
    return "sáng" if h < 11 else "trưa" if h < 13 else "chiều" if h < 18 else "tối"


def tin_nhac(k: dict, b: dict, hom_nay: date) -> str:
    goi, toi = xung(k)
    G = goi[:1].upper() + goi[1:]
    khi = ngay_s(b["ngay"], hom_nay)
    buoi_ = _buoi_trong_ngay(b["gio"])
    noi = f" ở {b['dia_diem']}" if b.get("dia_diem") else ""
    if khi == "hôm nay":
        mo = _chon([f"{G} ơi, {buoi_} nay {gio_s(b['gio'])} mình có buổi tập{noi} nha 💪",
                    f"{G} ơi, nhắc {goi} {buoi_} nay {gio_s(b['gio'])} mình tập{noi} nhé 💪",
                    f"Hello {goi}, {buoi_} nay {gio_s(b['gio'])} có buổi tập{noi} đó nha 🔥"], k["ma"] + str(b["ngay"]))
    else:
        mo = _chon([f"{G} ơi, {khi} {gio_s(b['gio'])} mình có buổi tập{noi} nha 💪",
                    f"{G} ơi, {toi} nhắc lịch {khi} {gio_s(b['gio'])} mình tập{noi} nhé",
                    f"Hello {goi}, {khi} {gio_s(b['gio'])} có buổi tập{noi} nha 🔥"], k["ma"] + str(b["ngay"]))
    ket = _chon([f"Nhớ ăn nhẹ trước tập 1–2 tiếng và mang theo nước nha. Có việc bận thì nhắn {toi} sớm để {toi} dời lịch cho {goi} nhé 😊",
                 f"{G} nhớ ngủ đủ và uống đủ nước nha. Nếu bận thì báo {toi} sớm để mình đổi buổi khác nhé 😊",
                 f"Mang theo khăn với bình nước nha {goi}. Có gì thay đổi cứ nhắn {toi} nhé 😊"], k["ma"] + str(b["ngay"]) + "k")
    return f"{mo}\n\n{ket}"


def tin_tuan(k: dict, ds_buoi: list[dict], hom_nay: date, H: dict | None = None) -> str:
    goi, toi = xung(k)
    G = goi[:1].upper() + goi[1:]
    bs = [b for b in ds_buoi if b["ma"] == k["ma"] and b["trang_thai"] != "huy" and b["ngay"] >= hom_nay]
    dong = [f"{G} ơi, {toi} gửi lịch tập tuần này của {goi} nha 💪", ""]
    for b in bs:
        dong.append(f"• {THU[b['ngay'].weekday()]} ({b['ngay']:%d/%m}) – {gio_s(b['gio'])}"
                    + (f" · {b['dia_diem']}" if b.get("dia_diem") else "") + (" (hôm nay)" if b["ngay"] == hom_nay else ""))
    if not bs:
        dong.append("Tuần này mình chưa xếp buổi nào — " + goi + " rảnh hôm nào nhắn " + toi + " để hẹn nhé.")
    con = con_lai(k, H)
    if con is not None and con <= 3:
        dong += ["", f"Gói của {goi} còn {con} buổi nữa nha."]
    cn = con_ngay(k, hom_nay)
    if cn is not None and cn <= 7:
        dong += ["", f"Gói của {goi} còn {cn} ngày nữa là hết nha."]
    dong += ["", f"Hôm nào bận thì nhắn {toi} sớm để {toi} dời lịch cho {goi} nhé 😊"]
    return "\n".join(dong)


def tin_hen(k: dict, ngay: date, gio: str, hom_nay: date, dia_diem: str = "", doi_tu: dict | None = None) -> str:
    goi, toi = xung(k)
    G = goi[:1].upper() + goi[1:]
    noi = f" ở {dia_diem}" if dia_diem else ""
    if doi_tu:
        return (f"{G} ơi, {toi} dời buổi {ngay_s(doi_tu['ngay'], hom_nay)} {gio_s(doi_tu['gio'])} sang "
                f"{ngay_s(ngay, hom_nay)} {gio_s(gio)}{noi} nha. {G} xem giờ này được không, có gì nhắn {toi} nhé 😊")
    return (f"{G} ơi, {toi} hẹn {goi} buổi tập {ngay_s(ngay, hom_nay)} lúc {gio_s(gio)}{noi} nha 💪 "
            f"{G} xác nhận giúp {toi} nhé, nếu chưa tiện thì báo {toi} đổi giờ khác 😊")


def tin_ru_quay_lai(k: dict) -> str:
    goi, toi = xung(k)
    G = goi[:1].upper() + goi[1:]
    return (f"{G} ơi, lâu rồi mình chưa tập lại đó 😄 Tuần này {goi} sắp xếp được buổi nào không? "
            f"{G} báo {toi} ngày giờ tiện để {toi} giữ lịch cho {goi} nha 💪")


def tin_tai_khoan(k: dict, link: str, username: str, password: str | None) -> str:
    goi, toi = xung(k)
    G = goi[:1].upper() + goi[1:]
    mk = f"Mật khẩu: {password}" if password else "Mật khẩu: (giữ như cũ)"
    return (f"{G} ơi, {toi} gửi {goi} trang theo dõi riêng nha 💪 Trong đó có giáo án, thực đơn tính riêng cho {goi}, "
            f"số tạ từng buổi và biểu đồ tiến độ.\n\n"
            f"🔗 {link}\nTên đăng nhập: {username}\n{mk}\n\n"
            f"{G} đăng nhập xong vào mục Tài khoản đổi mật khẩu riêng nhé. Mở trên điện thoại thì bấm Chia sẻ → "
            f"Thêm vào màn hình chính để dùng như app 😊")


# ------------------------------------------------------------------ hàng chờ Claude gửi qua Zalo Web
def xep_hang(k: dict, noi_dung: str, nguoi: str) -> bool:
    key = hashlib.md5((k["ma"] + noi_dung).encode()).hexdigest()[:12]
    return db.append("HangCho", key, {"ma": k["ma"], "ho_ten": k.get("ho_ten"), "ten_zalo": k.get("ten_zalo"),
                                      "sdt": k.get("sdt"), "noi_dung": noi_dung, "trang_thai": "cho"}, nguoi, k["ma"])


def danh_dau_gui(key: str, nguoi: str, bo: bool = False) -> bool:
    cu = db.latest("HangCho", ca_xoa=True).get(key, {})
    d = {k: v for k, v in cu.items() if not k.startswith("_")}
    return db.append("HangCho", key, {**d, "trang_thai": "bo" if bo else "da_gui"}, nguoi, d.get("ma", ""))


def hang_cho() -> list[dict]:
    return [v for v in db.latest("HangCho").values() if v.get("trang_thai", "cho") == "cho"]
