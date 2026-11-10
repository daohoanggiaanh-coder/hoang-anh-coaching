# Hoàng Anh Coaching v3.6 — 🎯 Buổi tư vấn F1 · F2 (port từ Atlas Academy v3.46, mang thương hiệu Hoàng Anh Coaching):
# HLV nhập số liệu tại sàn (hoặc chụp phiếu InBody để tự điền) → tự xếp loại theo chuẩn nam/nữ, tuổi cơ thể, ảnh form khách cạnh
# ảnh mẫu, biến thể bài test khi thiếu dụng cụ, phân tích OHS, bảng hỏi tính cách, lộ trình 12 tuần, đề xuất gói của HLV,
# xuất báo cáo PDF gửi khách; khách đăng ký → tự tạo hồ sơ khách + số đo + hồ sơ Thấu hiểu.
import html
from datetime import date

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from core import anh, auth, bao_cao, config, db, f1, hinh, icons, khao_sat as ks, llm, phieu_f1, store, thau_hieu as th, tu_van as tv, ui
from core.nhap_kh_atlas import khong_dau

user = auth.current_user()
if not user or user.get("role") != "coach":
    st.error("Trang này chỉ dành cho HLV.")
    st.stop()
S = st.session_state
P = "kh_"                                   # tiền tố khoá ô nhập → hồ sơ khách
NM = tv.norms()
LV = NM["muc_mau"]


def avatar(name: str, b64, size: int = 56, bg: str = "#A3803C") -> str:
    """Ảnh tròn (base64 hoặc data URI) hoặc chữ cái đầu."""
    if b64:
        src = b64 if str(b64).startswith("data:") else f"data:image/jpeg;base64,{b64}"
        return (f'<img src="{src}" style="width:{size}px;height:{size}px;border-radius:50%;object-fit:cover;'
                f'border:2px solid #C8A24A;flex:0 0 {size}px">')
    ch = "".join(w[0] for w in str(name or "?").split()[-2:]).upper()[:2] or "?"
    return (f'<div style="width:{size}px;height:{size}px;border-radius:50%;background:{bg};color:#fff;display:grid;'
            f'place-items:center;font-weight:800;font-size:{size * 0.36:.0f}px;flex:0 0 {size}px">{html.escape(ch)}</div>')


def g(k, d=None):
    return S.get(P + k, d)


def profile() -> dict:
    h = {k[len(P):]: v for k, v in S.items() if str(k).startswith(P)}
    for k, v in list(h.items()):
        if isinstance(v, date):
            h[k] = v.isoformat()
    return h


def num_in(where, label, lo, hi, k, **kw):
    """number_input không truyền value khi ô đã có giá trị (tránh cảnh báo của Streamlit)."""
    if P + k not in S or S[P + k] in ("", None):
        S.pop(P + k, None)
        kw["value"] = None
    else:
        kw.pop("value", None)
        try:   # giá trị nạp từ Google Sheets có thể là chuỗi / số thực → ép đúng kiểu của ô
            S[P + k] = int(float(S[P + k])) if isinstance(lo, int) else float(S[P + k])
        except (TypeError, ValueError):
            S.pop(P + k, None)
            kw["value"] = None
    return where.number_input(label, lo, hi, key=P + k, **kw)


def badge(res, unit=""):
    if not res:
        st.caption("Nhập số để xem xếp loại.")
        return
    col = LV[str(res["diem"])]
    st.markdown(f'<div style="display:flex;gap:10px;align-items:center;margin:4px 0 10px">'
                f'<span style="font-size:1.35rem;font-weight:800">{html.escape(fmt(res["gia_tri"], nd=2) if isinstance(res["gia_tri"], (int, float)) else str(res["gia_tri"]))}{unit}</span>'
                f'<span style="background:{col};color:#fff;border-radius:999px;padding:3px 12px;font-size:.8rem;'
                f'font-weight:700">{html.escape(res["nhan"])}</span></div>', unsafe_allow_html=True)


def scale(levels, value, vmin, vmax, unit=""):
    """Dải màu thang chuẩn + vạch giá trị (HTML)."""
    segs, hi = [], vmax
    for lv in levels:
        lo = max(lv["tu"], vmin)
        if hi > lo:
            segs.append((lo, hi, lv["diem"], lv["nhan"]))
        hi = lo
    segs.sort()
    bars = "".join(
        f'<div title="{html.escape(n)}" style="flex:{b - a};background:{LV[str(d)]};height:10px"></div>' for a, b, d, n in segs)
    labs = "".join(
        f'<div style="flex:{b - a};font-size:.62rem;color:#8b8577;text-align:center;overflow:hidden;white-space:nowrap">'
        f'{html.escape(n)}</div>' for a, b, d, n in segs)
    mark = ""
    if value is not None:
        pos = (min(max(value, vmin), vmax) - vmin) / (vmax - vmin) * 100
        mark = (f'<div style="position:absolute;left:calc({pos}% - 6px);top:-14px;font-size:.8rem;color:#1c1b19">▼</div>')
    st.markdown(f'<div style="position:relative;margin:18px 0 4px"><div style="display:flex;border-radius:6px;'
                f'overflow:hidden">{bars}</div>{mark}</div><div style="display:flex">{labs}</div>', unsafe_allow_html=True)


def has_pic(name) -> bool:
    return any((config.ROOT / "assets" / d / f"{name}.jpg").exists() for d in ("anh_that", "anh_minh_hoa"))


def pic(name, cap="", w=None):
    for d in ("anh_that", "anh_minh_hoa"):
        f = config.ROOT / "assets" / d / f"{name}.jpg"
        if f.exists():
            st.image(str(f), caption=cap or None, use_container_width=w is None, width=w)
            return


def take(up_key: str, store: str, fn) -> bool:
    """Xử lý ảnh vừa tải 1 lần (theo file_id) → lưu bytes đã thu nhỏ vào hồ sơ. Trả True nếu vừa xử lý."""
    f = S.get(up_key)
    if f is None:
        return False
    fid = getattr(f, "file_id", None) or f"{f.name}{f.size}"
    if S.get("_fid_" + up_key) == fid:
        return False
    S["_fid_" + up_key] = fid
    S[P + store] = fn(f.getvalue())
    return True


def placeholder(text: str):
    st.markdown(f'<div style="aspect-ratio:4/3;border:1.5px dashed #D9CFB8;border-radius:12px;display:grid;'
                f'place-items:center;color:#8b8577;font-size:.75rem;text-align:center;padding:6px">{text}</div>',
                unsafe_allow_html=True)


def uk(name: str) -> str:
    """Khoá ô tải ảnh theo từng khách: đổi khách → ô tải ảnh trống lại."""
    return f"{name}_{S.get('_kh_nonce', 0)}"


def _ho_so_f1() -> dict[str, dict]:
    """Các hồ sơ F1 đã lưu (DinhDuong f1|…), mới nhất trước → {nhãn: dòng}."""
    ds = [v for k, v in db.latest("DinhDuong").items() if str(k).startswith("f1|") and isinstance(v, dict) and not v.get("xoa")]
    ds.sort(key=lambda v: str(v.get("_luc") or v.get("ngay_f1") or ""), reverse=True)
    out = {}
    for v in ds:
        out[f"{v.get('ho_ten', '')} · {tv.as_text('sdt', v.get('sdt', ''))} · F1 {str(v.get('ngay_f1', ''))[:10]}"] = v
    return out


def _f1_id(h: dict) -> str:
    sdt = "".join(ch for ch in str(h.get("sdt") or "") if ch.isdigit())
    return "f1|" + (khong_dau(h.get("ho_ten") or "khach").replace(" ", "_") + "_" + (sdt or "0"))[:60]


def goi_hac(per_week: int) -> dict:
    """Gói đề xuất lấy từ 📦 Bảng gói của HLV (trang Khách) — không dùng giá Atlas."""
    G = [x for x in store.goi_list() if int(x.get("gia") or 0) > 0]
    pw = max(int(per_week or 3), 1)
    ds = []
    for x in G:
        so, lo = int(x.get("so") or 0), x.get("loai", "buoi")
        tuan = so if lo == "tuan" else (so * 4.3 if lo == "thang" else (so / pw if so else 0))
        buoi = so if lo == "buoi" else round(tuan * pw)
        if not buoi:
            continue
        ds.append({"id": x["ten"], "ten": x["ten"], "buoi": buoi, "gia": int(x["gia"]), "gia_buoi": round(int(x["gia"]) / buoi),
                   "tuan": round(tuan, 1), "goi_y": False, "tiet_kiem": 0, "loai": lo})
    if ds:
        need = pw * 8                                        # tối thiểu ~8 tuần để thấy thay đổi rõ
        best = min(ds, key=lambda p: (abs(p["buoi"] - need), p["gia_buoi"]))
        best["goi_y"] = True
        base = max(p["gia_buoi"] for p in ds)
        for p in ds:
            p["tiet_kiem"] = max(0, round(base * p["buoi"] - p["gia"], -3))
    ds.sort(key=lambda p: (not p["goi_y"], p["gia"]))
    return {"ds": ds[:3], "goi_y": next((p["id"] for p in ds if p["goi_y"]), None),
            "bonus": S.get(P + "qua_tang") or "Đăng ký ngay sau buổi F1: buổi F2 được cộng thêm vào gói."}


def clear_profile():
    for k in [k for k in S if str(k).startswith((P, "_fid_", "f2_editor", "_inbody", "_anh_saved", "_pdf_kieu"))]:
        del S[k]
    S["_kh_nonce"] = S.get("_kh_nonce", 0) + 1


def tile(icon: str, label: str, value: str, res=None, sub: str = "") -> str:
    pill = ""
    if res:
        pill = (f'<span style="background:{LV[str(res["diem"])]};color:#fff;border-radius:999px;padding:2px 9px;'
                f'font-size:.68rem;font-weight:700;white-space:nowrap">{html.escape(res["nhan"])}</span>')
    return (f'<div style="background:#fff;color:#1C1B19;border:1px solid #ECE6D8;border-radius:16px;padding:12px 14px;display:flex;'
            f'gap:12px;align-items:flex-start"><div style="flex:0 0 40px;height:40px;border-radius:50%;background:#F3ECDC;'
            f'display:grid;place-items:center">{icons.svg(icon, "#7A5B14", 22)}</div><div style="min-width:0">'
            f'<div style="font-size:.72rem;color:#8b8577">{html.escape(label)}</div>'
            f'<div style="font-size:1.25rem;font-weight:800;line-height:1.25">{html.escape(value)}</div>'
            f'<div style="display:flex;gap:6px;align-items:center;flex-wrap:wrap;margin-top:2px">{pill}'
            f'<span style="font-size:.68rem;color:#8b8577">{html.escape(sub)}</span></div></div></div>')


def fmt(v, unit="", nd=1):
    x = tv.num(v)
    if x is None:
        return "—"
    return (f"{x:.{nd}f}".rstrip("0").rstrip(".") if nd else f"{x:.0f}") + (f" {unit}" if unit else "")


# ================================================================== đầu trang: chọn khách
ui.hero("BUỔI TƯ VẤN F1 · F2", "Đánh giá thể chất & lộ trình 12 tuần",
        "Nhập số liệu ngay tại sàn: web tự xếp loại theo chuẩn nam/nữ, tính tuổi cơ thể, phân tích tư thế, hiểu tính cách khách, "
        "lên lộ trình 12 tuần và xuất báo cáo PDF mang thương hiệu Hoàng Anh Coaching.")

with st.container(border=True):
    st.markdown("**Quy trình:** F1 đánh giá chuyên sâu (PAR-Q · InBody · tư thế · OHS · bài test) → **ngồi tư vấn lộ trình "
                "ngay sau F1** → khách đăng ký thì buổi F2 được cộng vào gói. Mọi buổi F1, F2 đều **quay video** và gửi "
                "báo cáo cho khách.")
    c1, c2, c3 = st.columns([2.2, 1, 1])
    REC = _ho_so_f1()
    names = list(REC)
    pick = c1.selectbox("Mở hồ sơ đã lưu (để làm tiếp F2 hoặc tư vấn lại)", ["— Khách mới —"] + names)
    if c2.button("📂 Mở hồ sơ", use_container_width=True, disabled=pick == "— Khách mới —"):
        row = REC[pick]
        clear_profile()
        for k, v in tv.restore_profile(row).items():
            S[P + k] = v
        ids = g("anh_ids") or {}
        if ids:
            with st.spinner("Đang tải ảnh của khách…"):
                got = db.get_images(list(ids.values()))
            for slot, fid in ids.items():
                if fid in got:
                    S[P + "_anh_" + slot] = got[fid]
            S["_anh_saved"] = {slot: tv.image_hash(got[fid]) for slot, fid in ids.items() if fid in got}
        st.rerun()
    if c3.button("🆕 Khách mới", use_container_width=True):
        clear_profile()
        st.rerun()

S.setdefault(P + "hlv", user["name"])
S.setdefault(P + "ngay_f1", date.today())
S.setdefault(P + "gioi_tinh", "Nam")
S.setdefault(P + "muc_tieu", "giam_mo")
S.setdefault(P + "buoi_tuan", 3)

# số đọc từ phiếu InBody (bấm nút ở thẻ ②) → điền vào ô trước khi vẽ (ô ở thẻ ① đã vẽ thì không sửa được)
if S.get("_inbody_pending"):
    for k, v in S.pop("_inbody_pending").items():
        if k == "tuoi" and g("tuoi"):
            continue
        S[P + k] = v

# ảnh: thu nhỏ 1 lần; ảnh tư thế góc trước → tự cắt ảnh đại diện khách (nếu chưa tải chân dung riêng)
for _k in ("truoc", "ben", "sau"):
    if take(uk(f"up_{_k}"), f"_anh_{_k}", anh.shrink) and _k == "truoc" and not g("_avatar_tay"):
        _img, _found = anh.face_crop(g("_anh_truoc"))
        S[P + "anh_dai_dien"] = anh.to_b64(_img)
        S[P + "_avatar_mat"] = _found
take(uk("up_inbody"), "_anh_inbody", lambda d: anh.shrink(d, 1800))
if take(uk("up_avatar_kh"), "_avatar_src", anh.shrink):
    _img, _found = anh.face_crop(g("_avatar_src"))
    S[P + "anh_dai_dien"] = anh.to_b64(_img)
    S[P + "_avatar_tay"] = True
    S[P + "_avatar_mat"] = _found
_HLV = hinh.ho_so_hlv()
_av = hinh.avatar_hlv(_HLV)
S[P + "_anh_hlv"] = _av.split(",", 1)[1] if _av.startswith("data:") else (_av or None)


def strip(big: bool = False):
    """Dải nhận diện: ảnh khách — thông tin — ảnh HLV."""
    sz = 72 if big else 56
    who = html.escape(g("ho_ten") or "Khách hàng mới")
    meta = " · ".join(html.escape(str(x)) for x in (g("gioi_tinh"), f"{g('tuoi')} tuổi" if g("tuoi") else "",
                                                     tv.GOALS.get(g("muc_tieu"), "")) if x)
    st.markdown(
        f'<div style="display:flex;align-items:center;gap:16px;background:#fff;color:#1C1B19;border:1px solid #ECE6D8;border-radius:18px;'
        f'padding:12px 18px;margin:6px 0 14px">{avatar(g("ho_ten") or "?", g("anh_dai_dien"), sz)}'
        f'<div style="flex:1;min-width:0"><div style="font-size:.7rem;letter-spacing:.12em;color:#A3803C;font-weight:700">'
        f'KHÁCH HÀNG</div><div style="font-size:{1.35 if big else 1.15}rem;font-weight:800">{who}</div>'
        f'<div style="font-size:.8rem;color:#8b8577">{meta}</div></div>'
        f'<div style="text-align:right"><div style="font-size:.7rem;letter-spacing:.12em;color:#A3803C;font-weight:700">'
        f'HUẤN LUYỆN VIÊN</div><div style="font-weight:700">{html.escape(str(g("hlv") or ""))}</div></div>'
        f'{avatar(str(g("hlv") or "PT"), g("_anh_hlv"), sz, "#1C1B19")}</div>', unsafe_allow_html=True)


strip()

t1, t2, t3, t4, t5, t8, t6, t7 = st.tabs(["① Hồ sơ & PAR-Q", "② InBody & huyết áp", "③ Tư thế & OHS", "④ Bài test",
                                          "⑤ Buổi F2", "⑥ Tính cách & động lực", "⑦ Trình bày lộ trình", "⑧ Lưu & báo cáo"])

# ================================================================== ⑥ tính cách (v3.6)
with t8:
    from views import khao_sat_ui as _ksu
    st.caption("Hỏi trong lúc nghỉ giữa các bài test hoặc khi ngồi tư vấn. Kết quả chỉ HLV thấy — khách đăng ký thì tự chuyển "
               "vào 🧠 Thấu hiểu khách để web gợi ý cách nói chuyện, cách khen, giữ chân và thời điểm xin giới thiệu.")
    S[P + "ks"] = _ksu.form(f"f1ks_{S.get('_kh_nonce', 0)}", g("ks"), "hlv")
    _kq = ks.cham(S[P + "ks"])
    if _kq.get("ks_phong_cach") in th.PHONG_CACH:
        _pc = th.PHONG_CACH[_kq["ks_phong_cach"]]
        st.success(f"Phong cách chính: **{_pc[0]}** — {_pc[1]}")
        for _x in th.GOI_Y_PC.get(_kq["ks_phong_cach"], {}).get("noi", [])[:3]:
            st.markdown("- " + _x)

# ================================================================== ① hồ sơ + PAR-Q
with t1:
    a, b, c = st.columns(3)
    a.text_input("Họ và tên khách *", key=P + "ho_ten")
    b.text_input("Số điện thoại *", key=P + "sdt")
    c.radio("Giới tính", ["Nam", "Nữ"], key=P + "gioi_tinh", horizontal=True)
    a, b, c = st.columns(3)
    num_in(a, "Tuổi", 12, 90, "tuoi", step=1, placeholder="VD 30")
    b.date_input("Ngày F1", key=P + "ngay_f1", format="DD/MM/YYYY")
    c.text_input("HLV phụ trách", key=P + "hlv")
    a, b, c = st.columns(3)
    a.selectbox("Mục tiêu chính", list(tv.GOALS), format_func=tv.GOALS.get, key=P + "muc_tieu")
    b.select_slider("Số buổi tập được / tuần", [2, 3, 4, 5], key=P + "buoi_tuan")
    c.text_input("Khung giờ tập cố định", key=P + "lich_co_dinh", placeholder="VD Thứ 2-4-6, 18h")
    a, b = st.columns(2)
    a.text_input("Nghề nghiệp · lối sống", key=P + "loi_song", placeholder="VD văn phòng, ngồi 9 tiếng, ngủ 6 tiếng")
    b.text_input("Người liên hệ khẩn cấp (tên · SĐT) *", key=P + "khan_cap")
    a, b = st.columns(2)
    a.caption("📲 Báo cáo tiến độ gửi khách qua Zalo theo số điện thoại (không dùng email).")
    with b:
        st.caption("Khách tự điền trước buổi F1 bằng phiếu giấy Hoàng Anh Coaching (sức khoẻ, mục tiêu, tính cách, chữ ký):")
        st.download_button("🖨 Tải phiếu thông tin khách in sẵn", phieu_f1.make_pdf(), phieu_f1.FILE_NAME,
                           "application/pdf", key="dl_phieu_f1")
    st.text_area("Mục tiêu theo lời khách · lịch sử tập · chấn thương", key=P + "ghi_chu_kh", height=70)

    st.markdown("#### Ảnh đại diện")
    a, b = st.columns(2, gap="large")
    with a.container(border=True):
        x, y = st.columns([1, 2.6])
        x.markdown(avatar(g("ho_ten") or "?", g("anh_dai_dien"), 84), unsafe_allow_html=True)
        with y:
            st.markdown("**Khách hàng**")
            if g("anh_dai_dien"):
                st.caption(("Tải chân dung riêng" if g("_avatar_tay") else "Tự cắt từ ảnh tư thế góc trước")
                           + ("" if g("_avatar_mat") in (None, True) else " · không thấy rõ mặt, đã lấy vùng đầu ảnh"))
            else:
                st.caption("Tự cắt khi tải ảnh tư thế góc trước ở thẻ ③, hoặc tải chân dung bên dưới.")
            st.file_uploader("Chân dung khác (tuỳ chọn)", type=["jpg", "jpeg", "png"], key=uk("up_avatar_kh"))
    with b.container(border=True):
        x, y = st.columns([1, 2.6])
        x.markdown(avatar(user["name"], g("_anh_hlv"), 84, "#1C1B19"), unsafe_allow_html=True)
        with y:
            st.markdown(f"**HLV · {html.escape(_HLV.get('ten') or user['name'])}**")
            st.caption("Ảnh lấy từ trang 🏆 Hồ sơ HLV & thành quả — đổi ảnh ở đó, báo cáo PDF tự cập nhật.")

    st.markdown("#### Bảng khảo sát sức khoẻ trước tập (PAR-Q)")
    st.caption("Bắt buộc 100% khách. Trả lời “Có” bất kỳ câu nào → hỏi kỹ, khuyên khám bác sĩ hoặc ký cam kết rủi ro riêng.")
    for i, q in enumerate(tv.PARQ, 1):
        x, y = st.columns([5, 1.3])
        x.markdown(f"**{i}.** {q}")
        y.radio(f"Câu {i}", ["Không", "Có"], key=P + f"parq_{i}", horizontal=True, label_visibility="collapsed")
    yes = [i for i in range(1, 8) if g(f"parq_{i}") == "Có"]
    if yes:
        st.error(f"Khách trả lời “Có” ở câu {', '.join(map(str, yes))}. Hỏi rõ tình trạng; nếu nghiêm trọng (tim mạch, huyết áp "
                 "chưa kiểm soát, chấn thương chưa lành) → khuyên khám bác sĩ hoặc ký giấy cam kết rủi ro cao trước khi tập.")
        st.radio("Xác nhận của khách", ["Đã hỏi ý kiến bác sĩ và được cho phép tập",
                                        "Chưa hỏi bác sĩ, chấp nhận rủi ro (ký cam kết riêng)"], key=P + "parq_xac_nhan")
    else:
        st.success("Tất cả “Không” — cho phép tập luyện bình thường.")

# ================================================================== ② InBody + huyết áp
with t2:
    st.markdown("#### Huyết áp & nhịp tim nghỉ (đo trước khi tập)")
    a, b, c = st.columns(3)
    num_in(a, "Huyết áp tâm thu (số trên)", 70, 250, "ha_tam_thu", placeholder="VD 120")
    num_in(b, "Huyết áp tâm trương (số dưới)", 40, 160, "ha_tam_truong", placeholder="VD 80")
    num_in(c, "Nhịp tim nghỉ (lần/phút)", 30, 200, "nhip_tim", placeholder="VD 72")
    bp = tv.rate_bp(g("ha_tam_thu"), g("ha_tam_truong"))
    if bp:
        badge(bp, " mmHg")
        if bp.get("hoan"):
            st.error("Huyết áp ≥ 180/110: **hoãn buổi tập**, khuyên khách đi khám. Ghi vào hồ sơ.")
    st.markdown("#### Chỉ số InBody")
    with st.container(border=True):
        x, y = st.columns([1.6, 1], gap="large")
        with x:
            st.markdown("**📸 Chụp phiếu InBody → tự điền số**")
            st.caption("Chụp thẳng, đủ sáng, thấy rõ cả phiếu. Hệ thống đọc số rồi điền vào các ô bên dưới — "
                       "PT soát lại với phiếu trước khi lưu.")
            fib = st.file_uploader("Ảnh phiếu InBody", type=["jpg", "jpeg", "png"], key=uk("up_inbody"),
                                   label_visibility="collapsed")
            go_ = st.button("🔍 Đọc số từ ảnh", type="primary", disabled=not g("_anh_inbody") or not llm.is_online())
            if not llm.is_online():
                st.caption("Cần khoá AI (Gemini) trong Secrets để đọc ảnh.")
            if go_ and g("_anh_inbody"):
                with st.spinner("Đang đọc phiếu InBody…"):
                    try:
                        got = tv.read_inbody(g("_anh_inbody"))
                    except llm.LLMError as e:
                        got = None
                        st.error(f"Chưa đọc được: {e}")
                if got:
                    S["_inbody_pending"] = got
                    S["_inbody_msg"] = ", ".join(tv.INBODY_FIELDS[k][0] if k in tv.INBODY_FIELDS else "Giới tính"
                                                 for k in got)
                    st.rerun()
                elif got is not None:
                    st.warning("Không thấy số nào trên ảnh — chụp lại rõ hơn hoặc nhập tay.")
            if S.get("_inbody_msg"):
                st.success(f"Đã điền: {S['_inbody_msg']}. Soát lại từng số với phiếu.")
        with y:
            if g("_anh_inbody"):
                st.image(g("_anh_inbody"), use_container_width=True, caption="Phiếu InBody (lưu kèm hồ sơ)")
    a, b, c, d = st.columns(4)
    num_in(a, "Chiều cao (cm)", 120.0, 220.0, "chieu_cao", step=0.5)
    num_in(b, "Cân nặng (kg)", 30.0, 200.0, "can_nang", step=0.1)
    num_in(c, "% mỡ cơ thể (PBF)", 3.0, 60.0, "pbf", step=0.1)
    num_in(d, "Mức mỡ nội tạng", 1, 30, "mo_noi_tang", step=1)
    a, b, c, d = st.columns(4)
    num_in(a, "Khối cơ xương SMM (kg)", 5.0, 80.0, "smm", step=0.1)
    num_in(b, "Khối mỡ (kg)", 1.0, 120.0, "khoi_mo", step=0.1)
    num_in(c, "BMR (kcal)", 600, 3500, "bmr", step=10)
    num_in(d, "Điểm InBody", 30, 120, "diem_inbody", step=1)
    a, b, c, d = st.columns(4)
    num_in(a, "Tổng nước cơ thể (lít)", 10.0, 80.0, "nuoc", step=0.1)
    num_in(b, "Protein (kg)", 2.0, 30.0, "protein", step=0.1)
    num_in(c, "Khoáng chất (kg)", 0.5, 10.0, "khoang_chat", step=0.01)
    num_in(d, "Tuổi cơ thể máy in (nếu có)", 10, 100, "tuoi_may", step=1)
    sk = tv.sex_key(g("gioi_tinh"))
    ev_ = tv.evaluate(profile())
    ba = ev_.get("tuoi_co_the")
    smm_pct = (f"{tv.num(g('smm')) / tv.num(g('can_nang')) * 100:.0f}% cân nặng"
               if tv.num(g("smm")) and tv.num(g("can_nang")) else "")
    tiles = [
        tile("can_nang", "Cân nặng", fmt(g("can_nang"), "kg"), sub=f"Cao {fmt(g('chieu_cao'), 'cm')}"),
        tile("co", "Khối cơ xương", fmt(g("smm"), "kg"), sub=smm_pct),
        tile("khoi_mo", "Khối mỡ", fmt(g("khoi_mo"), "kg")),
        tile("pbf", "Tỉ lệ mỡ", fmt(g("pbf"), "%"), ev_.get("pbf")),
        tile("noi_tang", "Mỡ nội tạng", fmt(g("mo_noi_tang"), nd=0) if g("mo_noi_tang") else "—", ev_.get("mo_noi_tang")),
        tile("bmi", "BMI", fmt(ev_["bmi"]["gia_tri"]) if ev_.get("bmi") else "—", ev_.get("bmi")),
        tile("bmr", "Trao đổi chất cơ bản", fmt(g("bmr"), "kcal", 0), sub="năng lượng lúc nghỉ / ngày"),
        tile("nuoc", "Nước cơ thể", fmt(g("nuoc"), "lít")),
        tile("diem", "Điểm InBody", fmt(g("diem_inbody"), nd=0) if g("diem_inbody") else "—", sub="trên 100"),
        tile("tuoi", "Tuổi cơ thể", f"{ba['gia_tri']} tuổi" if ba else "—",
             {"diem": ba["diem"], "nhan": (f"{ba['chenh']:+d} so với tuổi thật" if ba["chenh"] else "Bằng tuổi thật")}
             if ba else None),
    ]
    st.markdown('<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(155px,1fr));gap:10px;'
                f'margin:8px 0 14px">{"".join(tiles)}</div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3, gap="large")
    with col1:
        st.markdown("**BMI**")
        r_ = tv.rate_bmi(g("can_nang"), g("chieu_cao"))
        badge(r_)
        scale(NM["bmi"], r_["gia_tri"] if r_ else None, 15, 35)
        st.caption("Chuẩn WHO châu Á")
    with col2:
        st.markdown(f"**% mỡ — chuẩn {'nam' if sk == 'nam' else 'nữ'}**")
        r_ = tv.rate_pbf(g("pbf"), g("gioi_tinh"))
        badge(r_, "%")
        scale(NM["pbf"][sk], r_["gia_tri"] if r_ else None, 0 if sk == "nam" else 8, 45)
        st.caption("Chuẩn ACE")
    with col3:
        st.markdown("**Mỡ nội tạng**")
        r_ = tv.rate_visceral(g("mo_noi_tang"))
        badge(r_)
        scale(NM["mo_noi_tang"], r_["gia_tri"] if r_ else None, 1, 20)
        st.caption("Chuẩn InBody: 1–9 bình thường")

    st.markdown("#### Tuổi cơ thể")
    if not ba:
        st.caption("Cần tuổi (thẻ ①) và ít nhất % mỡ, mỡ nội tạng hoặc khối cơ.")
    else:
        cfg = NM["tuoi_co_the"]
        col = LV[str(ba["diem"])]
        x, y = st.columns([1, 2], gap="large")
        x.markdown(
            f'<div style="background:#1C1B19;color:#fff;border-radius:18px;padding:18px 20px">'
            f'<div style="display:flex;gap:10px;align-items:center">{icons.svg("tuoi", "#E2C88A", 26)}'
            f'<span style="letter-spacing:.12em;font-size:.72rem;color:#E2C88A;font-weight:700">TUỔI CƠ THỂ</span></div>'
            f'<div style="font-size:3rem;font-weight:800;line-height:1.1;margin-top:6px">{ba["gia_tri"]}</div>'
            f'<div style="color:#cfc8b8">Tuổi thật {ba["tuoi"]} · <b style="color:{col}">{ba["chenh"]:+d} năm</b></div>'
            + (f'<div style="color:#cfc8b8;font-size:.8rem;margin-top:4px">Máy InBody in: {ba["tuoi_may"]} tuổi</div>'
               if ba["tuoi_may"] else "") + "</div>", unsafe_allow_html=True)
        rows = "".join(
            f'<tr><td style="padding:5px 8px;font-weight:600">{html.escape(p_["ten"])}</td>'
            f'<td style="padding:5px 8px;color:#6c6860">{html.escape(p_["giai_thich"])}</td>'
            f'<td style="padding:5px 8px;text-align:right;font-weight:800;color:{"#C0392B" if p_["delta"] > 0 else "#1E7B4A"}">'
            f'{p_["delta"]:+.1f}</td></tr>' for p_ in ba["chi_tiet"])
        y.markdown(f'<table style="width:100%;border-collapse:collapse;font-size:.85rem"><tr style="color:#8b8577;font-size:.72rem">'
                   f'<td style="padding:4px 8px">THÀNH PHẦN</td><td style="padding:4px 8px">SO VỚI CHUẨN</td>'
                   f'<td style="padding:4px 8px;text-align:right">± NĂM</td></tr>{rows}</table>', unsafe_allow_html=True)
        with y.expander("Công thức tính"):
            st.markdown(
                f"**Tuổi cơ thể = Tuổi thật + Δ mỡ + Δ mỡ nội tạng + Δ cơ + Δ thể lực**\n\n"
                f"- **Δ mỡ** = (% mỡ − {cfg['pbf_chuan']['nam']}% nam / {cfg['pbf_chuan']['nu']}% nữ) × {cfg['nam_moi_diem_pbf']}"
                f", tối đa ±{cfg['tran_mo']} năm\n"
                f"- **Δ mỡ nội tạng** = +{cfg['nam_moi_muc_noi_tang']:g} năm cho mỗi mức trên {cfg['noi_tang_nguong']}; "
                f"mức ≤ {cfg['noi_tang_tot']} được {cfg['thuong_noi_tang_tot']} năm\n"
                f"- **Δ cơ** = (tỉ lệ cơ chuẩn {cfg['smm_ti_le_chuan']['nam'] * 100:.0f}% nam / "
                f"{cfg['smm_ti_le_chuan']['nu'] * 100:.0f}% nữ − SMM ÷ cân nặng) × 100 × {cfg['nam_moi_1pt_smm']}, "
                f"tối đa ±{cfg['tran_co']} năm\n"
                f"- **Δ thể lực** = ({cfg['the_luc_moc']} − điểm trung bình 4 bài test trên thang 1–5) × "
                f"{cfg['nam_moi_bac_the_luc']}, tối đa ±{cfg['tran_the_luc']} năm\n\n"
                f"Tổng chênh giới hạn ±{cfg['bien_do']} năm, không dưới {cfg['toi_thieu']} tuổi. Đây là ước tính để tạo "
                "động lực và theo dõi tiến bộ, không phải chẩn đoán y khoa. Hệ số sửa trong data/chuan_danh_gia.json.")

# ================================================================== ③ tư thế + OHS
with t3:
    st.markdown("#### Ảnh tư thế tĩnh")
    st.caption("Khách đứng tự nhiên, chân rộng bằng hông, nền gọn. Trên điện thoại bấm ô bên dưới để chụp trực tiếp. "
               "Ảnh góc trước tự cắt làm ảnh đại diện của khách.")
    cols = st.columns(3)
    for col, (k, lab) in zip(cols, (("truoc", "Trước"), ("ben", "Bên"), ("sau", "Sau"))):
        with col:
            st.file_uploader(f"Góc {lab.lower()}", type=["jpg", "jpeg", "png"], key=uk(f"up_{k}"))
            if g(f"_anh_{k}"):
                st.image(g(f"_anh_{k}"), use_container_width=True)
    st.markdown("#### Đánh giá tư thế tĩnh")
    cols = st.columns(3)
    for col, (goc, parts) in zip(cols, NM["tu_the"].items()):
        with col.container(border=True):
            st.markdown(f"**{goc.upper()}**")
            for phan, opts in parts.items():
                st.selectbox(phan, opts, key=P + f"tt_{goc}_{phan}")

    st.markdown("#### Overhead Squat (OHS)")
    st.caption("Khách giơ hai tay thẳng qua đầu, squat 5 lần ở mỗi góc. Tích vào điểm bù trừ nhìn thấy; hệ thống tự suy ra cơ căng / cơ yếu.")
    S[P + "ohs_da_lam"] = 1
    by_view = {}
    for k, v in NM["ohs"].items():
        by_view.setdefault(v["goc"], []).append((k, v))
    cols = st.columns(len(by_view))
    for col, (goc, items) in zip(cols, by_view.items()):
        with col.container(border=True):
            st.markdown(f"**Góc {goc.lower()}**")
            for k, v in items:
                st.checkbox(v["ten"], key=P + f"ohs_{k}")
                if v["anh"] and g(f"ohs_{k}"):
                    pic(v["anh"], "Minh hoạ: " + v["ten"].lower())
    ohs = tv.ohs_findings(profile())
    if ohs["loi"]:
        a, b = st.columns(2)
        a.error("**Cơ đang căng** (giãn, lăn):\n\n" + "\n".join(f"- {x}" for x in ohs["cang"]))
        b.info("**Cơ đang yếu** (tăng cường):\n\n" + "\n".join(f"- {x}" for x in ohs["yeu"]))
        st.success("**Bài sửa đưa vào khởi động mỗi buổi:**\n\n" + "\n".join(f"- {x}" for x in ohs["sua"]))
    else:
        st.success("Chưa tích điểm bù trừ nào — vận động OHS tốt.")
    st.text_area("Ghi chú HLV về tư thế / vận động", key=P + "ohs_ghi_chu", height=70)

# ================================================================== ④ bài test
with t4:
    sk = tv.sex_key(g("gioi_tinh"))
    age_ = tv.age(None, g("tuoi"))
    YN = NM["y_nghia"]
    st.caption(f"Thang chuẩn tự chọn theo **{'nam' if sk == 'nam' else 'nữ'}, {age_ or '—'} tuổi**. Làm theo thứ tự dưới đây "
               "sau khởi động 5–8 phút; dừng ngay nếu đau nhói, chóng mặt. Thiếu máy hoặc dụng cụ → đổi biến thể, hệ thống tự "
               "quy đổi về thang chuẩn. Chụp ảnh form của khách để đặt cạnh ảnh mẫu trong báo cáo.")

    def test_block(no: int, k: str, kind: str | None, title: str, render, img: str = ""):
        """no: thứ tự · k: khoá bài · kind: nhóm biến thể trong chuan_danh_gia.json (None = không có biến thể)."""
        with st.container(border=True):
            a, b = st.columns([1.3, 2], gap="large")
            with b:
                st.markdown(f"#### {no}. {title}")
                st.markdown(f'<div style="background:#F3ECDC;border-left:3px solid #A3803C;border-radius:8px;padding:6px 10px;'
                            f'font-size:.82rem;margin:-4px 0 10px">🎯 <b>Đánh giá:</b> {html.escape(YN.get(k) or YN[kind])}</div>',
                            unsafe_allow_html=True)
                cur = {"anh": img}
                if kind:
                    vs = tv.variants(kind) if kind != "strongman" else NM["strongman"]
                    ids = [v["id"] for v in vs]
                    auto = tv.variant(kind, None, g("gioi_tinh"))["id"] if kind != "strongman" else ids[0]
                    cur_v = S.get(P + "bt_" + k)
                    if cur_v not in ids or (cur_v == S.get("_bt_auto_" + k) and cur_v != auto):
                        S[P + "bt_" + k] = auto                             # PT chưa tự đổi → đi theo giới tính
                    S["_bt_auto_" + k] = auto
                    st.selectbox("Bài / biến thể (đổi khi thiếu máy, dụng cụ)", ids, key=P + "bt_" + k,
                                 format_func=lambda i: next(v["ten"] for v in vs if v["id"] == i))
                    cur = next(v for v in vs if v["id"] == g("bt_" + k))
                    st.caption(cur["cach"])
                render(cur)
            with a:
                take(uk(f"up_t_{k}"), f"_anh_t_{k}", lambda d: anh.crop_ratio(d, 4, 3))
                c1, c2 = st.columns(2)
                with c1:
                    if cur.get("anh") and has_pic(cur["anh"]):
                        pic(cur["anh"], "Mẫu chuẩn")
                    else:
                        placeholder("Chưa có ảnh mẫu<br>cho bài này")
                with c2:
                    if g(f"_anh_t_{k}"):
                        st.image(g(f"_anh_t_{k}"), caption="Khách", use_container_width=True)
                    else:
                        placeholder("Ảnh của khách")
                st.file_uploader("Ảnh form của khách", type=["jpg", "jpeg", "png"], key=uk(f"up_t_{k}"))

    # 1 ── Tim mạch: YMCA (mặc định) · Rockport trên máy đi bộ · bước tại chỗ 2 phút
    def _ymca(cur):
        st.caption("⚠️ **Bỏ qua bài này** nếu PAR-Q có vấn đề tim mạch, huyết áp ≥ 160/100 hoặc khách đang mệt, chóng mặt.")
        if cur["id"] == "rockport":
            a_, b_, c_ = st.columns(3)
            num_in(a_, "Thời gian (phút)", 5, 40, "rp_phut")
            num_in(b_, "… và giây", 0, 59, "rp_giay")
            num_in(c_, "Nhịp tim lúc dừng", 60, 220, "rp_hr")
            r_ = tv.rate_cardio(profile(), g("gioi_tinh"), age_)
            if not g("can_nang"):
                st.caption("Nhập cân nặng ở thẻ ② để tính VO₂max.")
            badge(r_, " ml/kg/phút (VO₂max)")
            if r_:
                cuts = list(r_["moc"].items())
                levels = [{"tu": v, "nhan": k_, "diem": NM["vo2max"]["diem"][i]} for i, (k_, v) in enumerate(cuts)]
                scale(levels, r_["gia_tri"], 10, max(cuts[0][1] + 8, r_["gia_tri"] + 3))
                st.caption("VO₂max = lượng oxy tối đa cơ thể dùng được mỗi phút — chỉ số sức bền tim phổi chuẩn nhất. Mốc tối thiểu: "
                           + " · ".join(f"{k_} ≥ {v:g}" for k_, v in cuts if v))
            return
        if cur["id"] == "buoc_2phut":
            num_in(st, "Số lần gối phải chạm mốc trong 2 phút", 0, 200, "step2_reps")
            r_ = tv.rate_cardio(profile(), g("gioi_tinh"), age_)
            badge(r_, " lần")
            if r_:
                lo, hi = r_["khoang"]
                st.caption(f"Khoảng bình thường cho {'nam' if sk == 'nam' else 'nữ'} {age_ or '—'} tuổi: **{lo}–{hi} lần**.")
            if age_ and age_ < 60:
                st.caption("Thang chuẩn này dành cho người 60 tuổi trở lên — khách trẻ hơn nên dùng YMCA hoặc Rockport.")
            return
        num_in(st, "Nhịp tim 1 phút sau test (lần/phút)", 40, 220, "ymca_hr")
        r_ = tv.rate_ymca(g("ymca_hr"), g("gioi_tinh"), age_)
        badge(r_, " lần/phút")
        if r_:
            cuts = list(r_["moc"].items())
            levels = [{"tu": -v, "nhan": k_, "diem": NM["ymca"]["diem"][i]} for i, (k_, v) in enumerate(cuts)]
            levels.append({"tu": -999, "nhan": "Rất kém", "diem": 1})
            scale(levels, -r_["gia_tri"], -(cuts[-1][1] + 25), -(cuts[0][1] - 15))
            st.caption("Thấp hơn là tốt hơn · " + " · ".join(f"{k_} ≤ {v}" for k_, v in cuts))

    test_block(1, "ymca", "tim_mach", "Sức bền tim mạch", _ymca)

    # 2 ── Squat
    def _sq(cur):
        if cur["kieu"] == "ohs":
            r_ = tv.rate_squat(profile(), g("gioi_tinh"), age_)
            if r_:
                badge({**r_, "gia_tri": f"{r_['gia_tri']:.0f}"}, " điểm bù trừ")
                st.caption("Lấy từ phần tích lỗi Overhead Squat ở thẻ ③ — sửa ở đó.")
            else:
                st.info("Tích các điểm bù trừ ở thẻ ③ (Tư thế & OHS) để có kết quả.")
            return
        a_, b_ = st.columns(2)
        num_in(a_, "Số lần trong 60 giây", 0, 120, "squat_reps")
        if cur["id"] == "goblet":
            num_in(b_, "Tạ đơn (kg)", 0.0, 40.0, "squat_kg", step=1.0)
        r_ = tv.rate_squat(profile(), g("gioi_tinh"), age_)
        badge(r_, " lần")
        if r_ and r_.get("quy_doi") is not None:
            st.caption(f"Quy đổi ≈ **{r_['quy_doi']:g} lần squat tay không** (ước tính).")
        if r_:
            cuts = list(r_["moc"].items())
            levels = [{"tu": v, "nhan": k_, "diem": NM["squat_1phut"]["diem"][i]} for i, (k_, v) in enumerate(cuts)]
            val = r_["quy_doi"] or r_["gia_tri"]
            scale(levels, val, 0, max(cuts[0][1] + 10, val + 5))
            st.caption("Mốc tối thiểu: " + " · ".join(f"{k_} ≥ {v}" for k_, v in cuts if v))

    test_block(2, "squat", "squat", "Squat — thân dưới", _sq)

    # 3 ── Kéo
    def _lp(cur):
        if cur["kieu"] == "so_lan":
            num_in(st, "Số lần làm được" + (" trong 60 giây" if cur["id"] == "banded_row" else ""), 0, 120, "keo_xo_reps")
        else:
            a_, b_ = st.columns(2)
            num_in(a_, "Mức tạ (kg" + (", 1 quả)" if cur["id"] == "ta_don" else ")"), 0.0, 200.0, "keo_xo_kg", step=1.0)
            num_in(b_, "Số lần làm được (3–12)", 1, 20, "keo_xo_reps")
        r_ = tv.rate_pulldown(g("keo_xo_kg"), g("keo_xo_reps"), g("can_nang"), g("gioi_tinh"), g("bt_keo"))
        if r_ and r_.get("rm"):
            st.caption(f"1RM ước tính {r_['rm']} kg (Epley) ÷ cân nặng {g('can_nang')} kg")
        elif cur["kieu"] == "ti_le" and g("keo_xo_kg") and not g("can_nang"):
            st.caption("Nhập cân nặng ở thẻ ② để tính tỉ lệ.")
        badge(r_, " lần" if cur["kieu"] == "so_lan" else "× cân nặng")
        tbl = NM[cur["bang"]][sk]
        scale(tbl, r_["gia_tri"] if r_ else None, 0, (tbl[0]["tu"] * 1.3) if cur["kieu"] == "so_lan" else
              round(tbl[0]["tu"] * 1.15, 2))

    test_block(3, "keo", "keo", "Kéo — lưng giữa", _lp)

    # 4 ── Hít đất
    def _pu(cur):
        num_in(st, f"Số lần ({cur['ten'].lower()})", 0, 150, "hit_dat")
        r_ = tv.rate_pushup(g("hit_dat"), g("gioi_tinh"), age_, g("bt_hit_dat"))
        badge(r_, " lần")
        if r_ and r_.get("quy_doi") is not None:
            st.caption(f"Quy đổi ≈ **{r_['quy_doi']:g} lần {r_['bai_chuan']}** (bài chuẩn của thang {'nam' if sk == 'nam' else 'nữ'}).")
        if r_ and r_.get("moc"):
            levels = [{"tu": v, "nhan": k_, "diem": NM["hit_dat"]["diem"][i]} for i, (k_, v) in enumerate(r_["moc"].items())]
            val = r_["quy_doi"] if r_.get("quy_doi") is not None else r_["gia_tri"]
            scale(levels, val, 0, max(list(r_["moc"].values())[0] + 10, val + 5))
            st.caption("Mốc tối thiểu: " + " · ".join(f"{k_} ≥ {v}" for k_, v in r_["moc"].items() if v))

    test_block(4, "hit_dat", "hit_dat", "Hít đất — đẩy", _pu)

    # 5 ── Plank
    def _pl(cur):
        num_in(st, "Thời gian giữ (giây)", 0, 900, "plank")
        r_ = tv.rate_plank(g("plank"), g("bt_plank"), g("gioi_tinh"))
        badge(r_, " giây")
        if r_ and r_.get("quy_doi") is not None:
            st.caption(f"Quy đổi ≈ **{r_['quy_doi']:g} giây plank cẳng tay**.")
        if cur.get("bang"):
            tbl = NM[cur["bang"]][sk]
            scale(tbl, r_["gia_tri"] if r_ else None, 0, tbl[0]["tu"] * 1.4)
            st.caption("Mốc: " + " · ".join(f"{x['nhan']} ≥ {x['tu']} giây" for x in tbl if x["tu"]))
        else:
            scale(NM["plank"], (r_["quy_doi"] or r_["gia_tri"]) if r_ else None, 0, 300)

    test_block(5, "plank", "plank", "Plank — cơ trọng tâm", _pl)

    # 6 ── Dẻo
    def _fx(cur):
        num_in(st, "Khoảng cách so với mũi chân (cm, chưa chạm thì ghi số âm)", -40, 40, "deo_dai")
        r_ = tv.rate_flex(g("deo_dai"))
        badge(r_, " cm")
        scale(NM["deo_dai"], r_["gia_tri"] if r_ else None, -20, 20)

    test_block(6, "deo", "deo", "Độ dẻo — đùi sau, lưng dưới", _fx)

    # 7 ── Strongman (tuỳ chọn)
    st.checkbox("Còn thời gian cuối buổi → làm thêm 1 bài strongman (không tính điểm)", key=P + "sm_co")
    if g("sm_co"):
        def _sm(cur):
            a_, b_, c_ = st.columns([1.6, 1, 1])
            a_.text_input("Kết quả", key=P + "sm_ket_qua", placeholder="VD 45 giây · 14 lần / 30 giây · 20 m trong 32 giây")
            num_in(b_, "Tạ / bóng (kg)", 0.0, 300.0, "sm_kg", step=1.0)
            S.setdefault(P + "sm_rpe", 8)
            c_.select_slider("Mức gắng sức (RPE)", list(range(1, 11)), key=P + "sm_rpe")
            st.text_input("Nhận xét (tinh thần, kỹ thuật, cảm nhận của khách)", key=P + "sm_ghi_chu")

        test_block(7, "sm", "strongman", "Strongman kết buổi", _sm)

# ================================================================== ⑤ F2
with t5:
    S.setdefault(P + "ngay_f2", date.today())
    a, b = st.columns([1, 3])
    a.date_input("Ngày F2", key=P + "ngay_f2", format="DD/MM/YYYY")
    b.info("Mẹo: tư vấn lộ trình **ngay sau F1**. Khách đăng ký gói thì buổi F2 được cộng vào gói — "
           "phần này dùng cho buổi đầu tiên của gói.")
    st.markdown("#### Số đo các vòng (cm)")
    cols = st.columns(5)
    for i, (k, lab) in enumerate(tv.VONG):
        num_in(cols[i % 5], lab, 10.0, 200.0, f"v_{k}", step=0.5)
    w_ = tv.rate_waist(g("v_eo"), g("v_hong"), g("chieu_cao"), g("gioi_tinh"))
    if w_:
        msg = f"Vòng eo {w_['eo']:g} cm ({'vượt' if w_['eo_vuot'] else 'dưới'} ngưỡng {w_['nguong_eo']} cm)"
        if "whr" in w_:
            msg += f" · eo/hông {w_['whr']}"
        if "whtr" in w_:
            msg += f" · eo/chiều cao {w_['whtr']}"
        (st.warning if w_["diem"] < 5 else st.success)(msg)

    goal = g("muc_tieu") or "giam_mo"
    tpl = tv.f2_template(goal)
    LT = tv.library()["loai"]
    st.markdown(f"#### Giáo án buổi F2 · {tv.GOALS.get(goal, goal)}")
    st.caption("Soạn sẵn theo mục tiêu ở thẻ ①. Đổi biến thể hoặc đổi hẳn bài ở ô chọn (biến thể cùng nhóm nằm đầu danh sách). "
               "Hệ thống luôn xếp **Compound (C) → Multi (M) → Isolate (I) → Core**. Tiếp thu = học kỹ thuật nhanh hay chậm · "
               "Cảm nhận cơ = cảm được đúng nhóm cơ (1 kém – 5 rất tốt).")
    st.markdown(f'<div style="background:#F3ECDC;border-radius:12px;padding:10px 14px;font-size:.85rem;margin-bottom:8px">'
                f'<b>Cường độ:</b> {html.escape(tpl["cuong_do"])}<br><b>Cardio:</b> {html.escape(tpl["cardio"])}</div>',
                unsafe_allow_html=True)

    def ex_label(eid, home):
        if eid == "_bo":
            return "— Bỏ bài này —"
        e = tv.exercise(eid)
        if not e:
            return eid
        return (e["ten"] if e["nhom"] == home else f"↪ {e['nhom_ten']}: {e['ten']}") + f"  ·  {e['loai'] if e['loai'] != 'Core' else 'Core'}"

    slots = []
    for i, sl in enumerate(tpl["slots"]):
        kb = f"f2_{goal}_{i}"
        if g(kb + "_bai") not in ["_bo"] + tv.exercise_choices(sl["nhom"]):
            S[P + kb + "_bai"] = sl["mac_dinh"]
        S.setdefault(P + kb + "_hl", sl["hl"])
        slots.append((i, sl, kb, tv.exercise(g(kb + "_bai"))))
    order = sorted(slots, key=lambda x: (tv.order_rank(x[3]["loai"]) if x[3] else 9, x[0]))
    W_ = [0.8, 3, 1.05, 0.9, 0.8, 0.8, 1.5]
    for col, t_ in zip(st.columns(W_), ["", "Bài tập", "Hiệp × lần", "Tạ (kg)", "Tiếp thu", "Cảm nhận", "Ghi chú"]):
        col.markdown(f'<div style="font-size:.72rem;color:#8b8577;font-weight:700">{t_}</div>', unsafe_allow_html=True)
    plan_rows = []
    for n, (i, sl, kb, ex) in enumerate(order, 1):
        c = st.columns(W_, vertical_alignment="center")
        lt = LT[ex["loai"]] if ex else {"ten": "Bỏ", "mau": "#C9C2B2"}
        c[0].markdown(f'<div style="display:flex;flex-direction:column;align-items:flex-start;gap:2px;line-height:1.1">'
                      f'<b style="font-size:1rem">{n}</b><span style="background:{lt["mau"]};color:#fff;border-radius:6px;'
                      f'padding:2px 7px;font-size:.62rem;font-weight:700">{lt["ten"]}</span></div>', unsafe_allow_html=True)
        c[1].selectbox(f"Bài {n}", ["_bo"] + tv.exercise_choices(sl["nhom"]), key=P + kb + "_bai",
                       format_func=lambda e, h_=sl["nhom"]: ex_label(e, h_), label_visibility="collapsed")
        c[2].text_input("Hiệp × lần", key=P + kb + "_hl", label_visibility="collapsed")
        num_in(c[3], "Tạ (kg)", 0.0, 300.0, kb + "_ta", step=0.5, label_visibility="collapsed", placeholder="kg")
        num_in(c[4], "Tiếp thu", 1, 5, kb + "_tt", label_visibility="collapsed", placeholder="1–5")
        num_in(c[5], "Cảm nhận cơ", 1, 5, kb + "_cn", label_visibility="collapsed", placeholder="1–5")
        c[6].text_input("Ghi chú", key=P + kb + "_gc", label_visibility="collapsed", placeholder="Ghi chú")
        if ex:
            plan_rows.append({"Thứ tự": n, "Loại": lt["ten"], "Loại_ma": ex["loai"], "Bài tập": ex["ten"],
                              "Nhóm": ex["nhom_ten"], "Hiệp × lần": g(kb + "_hl") or "", "Tạ (kg)": g(kb + "_ta"),
                              "Tiếp thu (1-5)": g(kb + "_tt"), "Cảm nhận cơ (1-5)": g(kb + "_cn"), "Ghi chú": g(kb + "_gc") or ""})
    with st.expander("➕ Bài thêm ngoài giáo án (tuỳ chọn)"):
        base = g("f2_them") or [{"Bài tập": "", "Hiệp × lần": "", "Tạ (kg)": None, "Tiếp thu (1-5)": None,
                                 "Cảm nhận cơ (1-5)": None, "Ghi chú": ""}]
        ed = st.data_editor(pd.DataFrame(base), num_rows="dynamic", use_container_width=True, key=uk("f2_editor"),
                            column_config={"Tiếp thu (1-5)": st.column_config.NumberColumn(min_value=1, max_value=5, step=1),
                                           "Cảm nhận cơ (1-5)": st.column_config.NumberColumn(min_value=1, max_value=5, step=1),
                                           "Tạ (kg)": st.column_config.NumberColumn(min_value=0, step=0.5)})
        S[P + "f2_them"] = [r for r in ed.to_dict("records") if str(r.get("Bài tập") or "").strip()]
    extra = [{**r, "Thứ tự": len(plan_rows) + j + 1, "Loại": "Thêm", "Loại_ma": ""} for j, r in enumerate(g("f2_them") or [])]
    S[P + "f2_tap"] = plan_rows + extra
    a, b, c = st.columns(3)
    a.selectbox("Cardio", ["Máy đi bộ dốc", "Air bike", "Battle rope", "Không"], key=P + "cardio_may")
    num_in(b, "Thời gian cardio (phút)", 0, 90, "cardio_phut")
    S.setdefault(P + "cardio_rpe", 6)
    c.select_slider("Mức gắng sức (RPE 1–10)", list(range(1, 11)), key=P + "cardio_rpe")
    st.checkbox("Đã giãn cơ cuối buổi (5–8 phút)", key=P + "da_gian_co")

    st.markdown("#### Video buổi tập (bắt buộc)")
    a, b = st.columns(2)
    a.text_input("Link video F1 (Drive / Zalo)", key=P + "video_f1")
    b.text_input("Link video F2", key=P + "video_f2")

# ================================================================== ⑥ trình bày
h = profile()
res = tv.evaluate(h)
rm = tv.roadmap(h, res)
with t6:
    if not h.get("ho_ten"):
        st.info("Nhập họ tên khách ở thẻ ① để bắt đầu.")
    strip(big=True)
    st.markdown(f"### Lộ trình {rm['muc_tieu_ten'].lower()}")
    a, b = st.columns([1, 1.6], gap="large")
    with a:
        sc = res.get("diem_tong")
        fig = go.Figure(go.Indicator(mode="gauge+number", value=sc or 0, number={"suffix": "/100"},
                                     gauge={"axis": {"range": [0, 100]}, "bar": {"color": "#1E7B4A"},
                                            "steps": [{"range": [0, 35], "color": "#F6D5CF"}, {"range": [35, 65], "color": "#F5E8C8"},
                                                      {"range": [65, 100], "color": "#D7EBDD"}]},
                                     title={"text": "Điểm thể chất hiện tại"}))
        fig.update_layout(height=260, margin=dict(l=20, r=20, t=60, b=10), paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    with b:
        rad = {k: (v or 0) for k, v in res["radar"].items()}
        fig = go.Figure()
        fig.add_trace(go.Scatterpolar(r=[60] * len(rad) + [60], theta=list(rad) + [list(rad)[0]], name="Mốc chuẩn",
                                      line=dict(color="#A3803C", dash="dot")))
        fig.add_trace(go.Scatterpolar(r=list(rad.values()) + [list(rad.values())[0]], theta=list(rad) + [list(rad)[0]],
                                      fill="toself", name="Hiện tại", line=dict(color="#1E7B4A")))
        fig.update_layout(height=320, polar=dict(radialaxis=dict(range=[0, 100], showticklabels=False)),
                          margin=dict(l=40, r=40, t=20, b=20), legend=dict(orientation="h"), paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    if rm["proj"][0]["can_nang"]:
        dfp = pd.DataFrame(rm["proj"])
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=dfp["tuan"], y=dfp["can_nang"], name="Cân nặng (kg)", line=dict(color="#1C1B19", width=3)))
        if dfp["pbf"].notna().all():
            fig.add_trace(go.Scatter(x=dfp["tuan"], y=dfp["pbf"], name="% mỡ", yaxis="y2", line=dict(color="#1E7B4A", width=3)))
        fig.update_layout(height=300, title="Dự kiến 12 tuần nếu tập đều và ăn theo thực đơn",
                          xaxis=dict(title="Tuần"), yaxis=dict(title="kg"), yaxis2=dict(title="% mỡ", overlaying="y", side="right"),
                          legend=dict(orientation="h"), margin=dict(l=20, r=20, t=50, b=20), paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    cols = st.columns(3)
    for col, ph in zip(cols, rm["phases"]):
        with col.container(border=True):
            st.markdown(f"**{ph['tuan']}**  \n### {ph['ten'].split('·')[-1].strip()}")
            st.caption(ph["muc_tieu"])
            st.markdown("\n".join(f"- {x}" for x in ph["noi_dung"]))
            st.caption("Mốc đo: " + ph["do"])
    if rm["focus"]:
        st.markdown("**Trọng tâm riêng của bạn:**\n" + "\n".join(f"- {f}" for f in rm["focus"]))
    st.markdown(f"**Lịch mẫu {rm['buoi_tuan']} buổi/tuần:** " + " · ".join(f"{a_}: {b_}" for a_, b_ in tv.week_split(rm["buoi_tuan"])))

    st.markdown("### Gói tập đề xuất")
    GOI = goi_hac(rm["buoi_tuan"])
    if not GOI["ds"]:
        st.info("Chưa có gói nào có giá trong 📦 Bảng gói của anh (trang 👤 Khách & tài khoản) — thêm gói để web đề xuất và in vào báo cáo.")
    cols = st.columns(max(len(GOI["ds"]), 1))
    for col, p in zip(cols, GOI["ds"]):
        border = "2px solid #A3803C" if p["goi_y"] else "1px solid #ECE6D8"
        tag = '<div style="color:#A3803C;font-weight:800;font-size:.75rem;letter-spacing:.12em">ĐỀ XUẤT CHO BẠN</div>' if p["goi_y"] else ""
        save = f"<li>Tiết kiệm {tv.vnd(p['tiet_kiem'])} so với gói lẻ</li>" if p["tiet_kiem"] else ""
        col.markdown(f'<div style="border:{border};border-radius:18px;padding:20px 22px;background:#fff;color:#1C1B19">{tag}'
                     f'<div style="font-weight:700;margin-top:4px">{html.escape(p["ten"])}</div>'
                     f'<div style="font-size:1.8rem;font-weight:800">{tv.vnd(p["gia"])}</div>'
                     f'<div style="color:#8b8577">≈ {tv.vnd(p["gia_buoi"])}/buổi · khoảng {p["tuan"]:g} tuần</div>'
                     f'<ul style="margin:10px 0 0 18px"><li>{p["buoi"]} buổi kèm 1-1</li><li>InBody định kỳ + báo cáo</li>'
                     f'<li>Thực đơn + nhắn tin theo dõi</li>{save}</ul></div>', unsafe_allow_html=True)
    S.setdefault(P + "qua_tang", "Đăng ký ngay sau buổi F1: buổi F2 được cộng thêm vào gói.")
    st.text_input("🎁 Quà tặng khi đăng ký (in trong báo cáo)", key=P + "qua_tang")

# ================================================================== ⑦ lưu + báo cáo
with t7:
    st.text_area("Lời nhắn của HLV in trong báo cáo", key=P + "ghi_chu_hlv", height=80,
                 placeholder="VD: Chị tiếp thu nhanh, cảm nhận cơ mông tốt. Ưu tiên sửa gối và tăng sức bền lõi.")
    _KQ = ["Đang cân nhắc"] + [f"Đăng ký {x['ten']}" for x in store.goi_list() if x.get("ten")] + ["Đăng ký gói khác", "Không đăng ký"]
    if g("ket_qua") not in _KQ:
        S.pop(P + "ket_qua", None)
    st.radio("Kết quả tư vấn", _KQ, key=P + "ket_qua", horizontal=True)
    h = profile()
    missing = [lab for k, lab in (("ho_ten", "họ tên"), ("sdt", "SĐT"), ("khan_cap", "liên hệ khẩn cấp")) if not h.get(k)]
    a, b = st.columns(2)
    if a.button("💾 Lưu hồ sơ khách", type="primary", use_container_width=True, disabled=bool(missing)):
        saved = dict(S.get("_anh_saved") or {})
        ids = dict(g("anh_ids") or {})
        new_imgs = {slot: g("_anh_" + slot) for slot in tv.IMAGE_SLOTS
                    if g("_anh_" + slot) and saved.get(slot) != tv.image_hash(g("_anh_" + slot))}
        img_ok = True
        if new_imgs:
            with st.spinner(f"Đang lưu {len(new_imgs)} ảnh…"):
                up = db.upload_images(new_imgs, tv.file_prefix(h))
            if up is None:
                img_ok = False
            else:
                ids.update(up)
                saved.update({slot: tv.image_hash(b_) for slot, b_ in new_imgs.items()})
                S["_anh_saved"] = saved
                S[P + "anh_ids"] = ids
        h = profile()
        row = tv.to_row(h)
        row["pt"] = user["name"]
        row["diem_tong"] = res.get("diem_tong")
        fid = _f1_id(h)
        ok = db.append("DinhDuong", fid, row, user["name"], "")
        if ok and "Đăng ký" in str(h.get("ket_qua", "")):
            ma_kh = f1.sang_khach(h, user["name"])
            if ma_kh:
                st.info(f"Khách đã đăng ký → đã tạo / cập nhật hồ sơ ở trang **👤 Khách & tài khoản** ({ma_kh}) kèm số đo InBody và "
                        "bảng hỏi tính cách. Anh vào đó tạo tài khoản đăng nhập, ghi phòng tập và lịch cố định cho khách.")
        if ok and img_ok:
            st.success(f"Đã lưu hồ sơ{f' và {len(ids)} ảnh' if ids else ''}. Mở lại hồ sơ là thấy đủ số liệu và ảnh.")
        elif ok:
            st.warning("Đã lưu số liệu nhưng **ảnh chưa lưu được** (kho ảnh Google Drive chưa sẵn sàng). Báo cáo PDF vẫn tải được.")
        else:
            st.error("Chưa lưu được lên Google Sheets. Báo cáo PDF vẫn tải được.")
    if missing:
        a.caption("Cần nhập: " + ", ".join(missing))
    has_f2 = bool(h.get("f2_tap") or any(h.get(f"v_{k}") for k, _ in tv.VONG) or h.get("cardio_phut"))
    S.setdefault("_pdf_kieu", "full" if has_f2 else "f1")
    kieu = b.radio("Nội dung báo cáo", ["f1", "full"], key="_pdf_kieu", horizontal=True,
                   format_func={"f1": "Chỉ buổi F1 (chưa có F2)", "full": "Đầy đủ F1 + F2"}.get)
    if kieu == "full" and not has_f2:
        b.caption("Chưa nhập dữ liệu buổi F2 — phần F2 trong báo cáo sẽ để trống.")
    safe = "".join(ch for ch in (h.get("ho_ten") or "Khach") if ch.isalnum() or ch == " ").strip().replace(" ", "_")
    try:
        pdf = bao_cao.make_pdf(h, f2=kieu == "full", goi=goi_hac(rm["buoi_tuan"]))
        b.download_button("📄 Tải báo cáo PDF gửi khách", pdf,
                          f"HoangAnhCoaching_{date.today().isoformat()}_BaoCao{'F1F2' if kieu == 'full' else 'F1'}_{safe}.pdf",
                          "application/pdf", use_container_width=True)
    except Exception as e:  # noqa: BLE001
        b.error(f"Chưa tạo được báo cáo: {e}")
    st.caption("Báo cáo 7 trang A4 mang thương hiệu Hoàng Anh Coaching: tổng quan · thành phần cơ thể · tư thế & OHS · bài test 1–4 · bài test 5–7 (+ giáo án F2) · lộ trình 12 tuần · gói tập. "
               "Bản **Chỉ F1** bỏ số đo vòng, giáo án và video buổi F2 — gửi ngay sau F1; khách hoàn thành F2 thì gửi bản "
               "**Đầy đủ**. Gửi kèm video buổi tập qua Zalo cho khách.")
