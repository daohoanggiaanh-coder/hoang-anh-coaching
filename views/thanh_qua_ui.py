# Hoàng Anh Coaching v1.8 (2026-11-01) — hồ sơ HLV, thành quả học viên (khách xem), quản lý ảnh đại diện
from __future__ import annotations

import html
import re

import streamlit as st

from core import anh as A, db, hinh, store, ui

E = html.escape
S = st.session_state
CSS = """<style>
.tq-hlv{display:flex;gap:18px;align-items:center;flex-wrap:wrap;background:radial-gradient(circle at 10% 0%,#3d3427,#14120F 70%);
  border-radius:22px;padding:18px 20px;color:#F3ECDC;border:1px solid rgba(232,199,106,.3);margin:6px 0 14px}
.tq-hlv .k{color:#E8C76A;letter-spacing:.16em;font-weight:800;font-size:.64rem}.tq-hlv .n{font-size:1.35rem;font-weight:800;color:#fff}
.tq-hlv .c{color:#D8D1C1;font-size:.85rem}.tq-hlv p{margin:6px 0 0;font-size:.88rem;color:#E9E2D0;line-height:1.55}
.tq-chip{display:inline-block;background:rgba(232,199,106,.16);color:#F1D78E;border:1px solid rgba(232,199,106,.35);border-radius:999px;
  padding:3px 10px;font-size:.72rem;font-weight:700;margin:6px 6px 0 0}
.tq-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:16px;margin:8px 0}
@media(max-width:760px){.tq-grid{grid-template-columns:1fr}}
.tq-c{background:#fff;border:1px solid #E6DCC6;border-radius:20px;overflow:hidden;box-shadow:0 8px 24px rgba(28,27,25,.06)}
.tq-ba{display:grid;grid-template-columns:1fr 1fr;gap:2px;background:#14120F;position:relative}
.tq-ba div{position:relative}.tq-ba img{width:100%;height:300px;object-fit:cover;display:block}
.tq-ba span{position:absolute;left:10px;bottom:10px;background:rgba(20,18,15,.82);color:#fff;font-size:.62rem;font-weight:900;
  letter-spacing:.14em;border-radius:999px;padding:4px 10px}.tq-ba div:last-child span{background:#C8A24A;color:#14120F}
.tq-b{padding:14px 16px}.tq-b .t{font-weight:800;font-size:1.05rem;color:#1C1B19}.tq-b .m{color:#8b8577;font-size:.78rem}
.tq-kq{display:flex;flex-wrap:wrap;gap:6px;margin:8px 0}
.tq-kq b{background:#F0F9F3;color:#1E7B4A;border:1px solid #BFE3CB;border-radius:999px;padding:4px 10px;font-size:.78rem}
.tq-b q{display:block;color:#4a463f;font-size:.88rem;line-height:1.55;font-style:italic;margin-top:4px}
.tq-sw{display:flex;overflow-x:auto;scroll-snap-type:x mandatory;background:#14120F;scrollbar-width:none}
.tq-sw::-webkit-scrollbar{display:none}
.tq-sw img{flex:0 0 100%;width:100%;aspect-ratio:4/5;object-fit:cover;scroll-snap-align:center;display:block}
.tq-dots{text-align:center;font-size:.7rem;color:#8b8577;padding:6px 0 0;letter-spacing:.06em}
html[data-hac-theme=dark] .tq-c{background:#1A1814;border-color:#332E25;box-shadow:none}
html[data-hac-theme=dark] .tq-b .t{color:#F3ECDC}html[data-hac-theme=dark] .tq-b q{color:#CFC6B4}
html[data-hac-theme=dark] .tq-kq b{background:#12261A;border-color:#2E7D4F;color:#7BD3A0}
</style>"""


def the_hlv(hs: dict | None = None, gon: bool = False):
    hs = hs or hinh.ho_so_hlv()
    st.markdown(CSS, unsafe_allow_html=True)
    av = hinh.the_avatar(hinh.avatar_hlv(hs), hs["ten"], 64 if gon else 96)
    cc = "".join(f'<span class="tq-chip">🎓 {E(x)}</span>' for x in hs.get("chung_chi") or [])
    st.markdown(f'<div class="tq-hlv">{av}<div style="flex:1;min-width:220px"><div class="k">HUẤN LUYỆN VIÊN CỦA BẠN</div>'
                f'<div class="n">{E(hs["ten"])}</div><div class="c">{E(hs.get("chuc_danh") or "")}</div>'
                + ("" if gon else (f'<p>{E(hs["gioi_thieu"])}</p>' if hs.get("gioi_thieu") else "") + (f"<div>{cc}</div>" if cc else ""))
                + "</div></div>", unsafe_allow_html=True)
    if hs.get("zalo") and not gon:
        so = "".join(c for c in str(hs["zalo"]) if c.isdigit())
        st.link_button("💬 Nhắn Zalo cho HLV", f"https://zalo.me/{so}")


def gallery(ds: list[dict]):
    st.markdown(CSS, unsafe_allow_html=True)
    if not ds:
        st.caption("Chưa có thành quả nào được đăng.")
        return
    o = ""
    for t in ds:
        if t.get("anh_ds"):                                   # ảnh ghép sẵn trước / sau (1080×1350) — vuốt xem từng góc
            imgs = [hinh.anh_full(i) for i in t["anh_ds"]]
            slide = "".join(f'<img src="{u}" alt="">' for u in imgs if u)
            kq = "".join(f"<b>{E(x.strip())}</b>" for x in re.split(r"[;\n|]|,\s+", str(t.get("ket_qua") or "")) if x.strip())
            o += (f'<div class="tq-c"><div class="tq-sw">{slide}</div>'
                  + (f'<div class="tq-dots">⇠ vuốt xem {len(imgs)} góc ⇢</div>' if len(imgs) > 1 else "")
                  + f'<div class="tq-b"><div class="t">{E(t.get("ten") or "Học viên")}</div>'
                  f'<div class="m">{E(" · ".join(x for x in (t.get("mo_ta"), t.get("thoi_gian")) if x))}</div>'
                  + (f'<div class="tq-kq">{kq}</div>' if kq else "") + (f'<q>{E(t["loi"])}</q>' if t.get("loi") else "") + "</div></div>")
            continue
        a, b = hinh.anh_full(t.get("anh_truoc", "")), hinh.anh_full(t.get("anh_sau", ""))
        kq = "".join(f"<b>{E(x.strip())}</b>" for x in re.split(r"[;\n|]|,\s+", str(t.get("ket_qua") or "")) if x.strip())
        o += (f'<div class="tq-c"><div class="tq-ba"><div>{f"<img src={chr(34)}{a}{chr(34)}>" if a else ""}<span>TRƯỚC</span></div>'
              f'<div>{f"<img src={chr(34)}{b}{chr(34)}>" if b else ""}<span>SAU</span></div></div>'
              f'<div class="tq-b"><div class="t">{E(t.get("ten") or "Học viên")}</div>'
              f'<div class="m">{E(" · ".join(x for x in (t.get("mo_ta"), t.get("thoi_gian")) if x))}</div>'
              + (f'<div class="tq-kq">{kq}</div>' if kq else "")
              + (f'<q>{E(t["loi"])}</q>' if t.get("loi") else "") + "</div></div>")
    st.markdown(f'<div class="tq-grid">{o}</div>', unsafe_allow_html=True)


def trang_khach():
    ui.hero("THÀNH QUẢ", "Họ đã làm được — bạn cũng vậy 💪",
            "Kết quả thật của học viên HLV Hoàng Anh. Mỗi người một xuất phát điểm — điểm chung là kiên trì báo cáo và tập đều.")
    the_hlv()
    ui.sec("Thành quả học viên")
    gallery(hinh.transforms())
    st.caption("Ảnh và số liệu đăng khi học viên đã đồng ý. Kết quả mỗi người khác nhau, tuỳ cơ địa, xuất phát điểm và mức tuân thủ.")


# ------------------------------------------------------------------ HLV quản lý
def _anh_moi(f, canh: int = 1400) -> str | None:
    up = db.upload_images({"x": A.shrink(f.getvalue(), canh)}, "HAC_TQ_")
    return (up or {}).get("x")


def trang_hlv(nguoi: str):
    ui.hero("HỒ SƠ HLV & THÀNH QUẢ", "Ảnh đại diện · giới thiệu · transform học viên",
            "Khách thấy hồ sơ của anh và các ca transform ở mục 🏆 Thành quả. Ảnh đại diện khách tự cắt từ ảnh đầu khoá.")
    t1, t2, t3, t4 = st.tabs(["👤 Hồ sơ HLV", "🏆 Thành quả học viên", "🖼 Ảnh đại diện khách", "📦 Nhập hàng loạt (ZIP)"])
    with t4:
        nhap_zip(nguoi)
    with t1:
        hs = hinh.ho_so_hlv()
        a, b = st.columns([1, 2])
        with a:
            khung = st.empty()
            khung.markdown(hinh.the_avatar(hinh.avatar_hlv(hs), hs["ten"], 140), unsafe_allow_html=True)
            f = st.file_uploader("Ảnh đại diện", type=["jpg", "jpeg", "png", "webp"], key="hlv_anh")
            if f is not None and st.button("⬆️ Dùng ảnh này", type="primary"):
                i = _anh_moi(f, 1200)
                if i and hinh.luu_ho_so_hlv({**hs, "anh": i}, nguoi):
                    st.toast("Đã cập nhật ảnh đại diện")
                    st.rerun()
                st.error("Chưa tải được ảnh — thử lại.")
            if hs.get("anh"):
                y = st.slider("Vị trí khuôn mặt (từ trên xuống, %)", 0, 100, int(hs.get("y") or 30), key="hlv_y")
                r = st.slider("Độ zoom (nhỏ = gần mặt hơn)", 25, 100, int(hs.get("r") or 70), key="hlv_r")
                khung.markdown(hinh.the_avatar(hinh._uri(hs["anh"], y, r), hs["ten"], 140), unsafe_allow_html=True)
                if (y, r) != (int(hs.get("y") or 30), int(hs.get("r") or 70)) and st.button("💾 Lưu khung cắt"):
                    hinh.luu_ho_so_hlv({**hs, "y": y, "r": r}, nguoi)
                    st.rerun()
        with b:
            with st.form("hlv_hs"):
                ten = st.text_input("Tên hiển thị", hs["ten"])
                cd = st.text_input("Chức danh", hs.get("chuc_danh") or "")
                gt = st.text_area("Giới thiệu ngắn (khách đọc)", hs.get("gioi_thieu") or "", height=110,
                                  placeholder="VD 8 năm huấn luyện, chuyên giảm mỡ – tăng cơ cho người bận rộn…")
                cc = st.text_area("Chứng chỉ (mỗi dòng 1 cái)", "\n".join(hs.get("chung_chi") or []), height=100)
                zl = st.text_input("Số Zalo (nút nhắn nhanh cho khách)", hs.get("zalo") or "")
                if st.form_submit_button("💾 Lưu hồ sơ", type="primary", use_container_width=True):
                    if hinh.luu_ho_so_hlv({**hs, "ten": ten.strip() or "Hoàng Anh", "chuc_danh": cd.strip(), "gioi_thieu": gt.strip(),
                                           "chung_chi": [x.strip() for x in cc.splitlines() if x.strip()], "zalo": zl.strip()}, nguoi):
                        st.toast("Đã lưu hồ sơ")
                        st.rerun()
        ui.sec("Khách thấy như sau")
        the_hlv(hinh.ho_so_hlv())
    with t2:
        ds = hinh.transforms(ca_an=True)
        moi = {"id": None}
        lua = [None] + [t["id"] for t in ds]
        by = {t["id"]: t for t in ds}
        chon = st.selectbox("Sửa ca", lua, format_func=lambda i: "➕ Thêm ca mới" if i is None else
                            f"{by[i].get('ten')} · {'đang hiện' if by[i].get('hien') and by[i].get('dong_y') else 'đang ẩn'}", key="tq_chon")
        t = by.get(chon, moi)
        a, b = st.columns(2)
        fa = a.file_uploader("Ảnh TRƯỚC", type=["jpg", "jpeg", "png", "webp"], key=f"tq_a_{chon}")
        fb = b.file_uploader("Ảnh SAU", type=["jpg", "jpeg", "png", "webp"], key=f"tq_b_{chon}")
        if t.get("anh_truoc") and fa is None:
            a.image(db.get_images([t["anh_truoc"]]).get(t["anh_truoc"]) or b"", width=180)
        if t.get("anh_sau") and fb is None:
            b.image(db.get_images([t["anh_sau"]]).get(t["anh_sau"]) or b"", width=180)
        with st.form(f"tq_f_{chon}"):
            c1, c2 = st.columns(2)
            ten = c1.text_input("Tên hiển thị", t.get("ten") or "", placeholder="VD Chị N. · 38 tuổi (có thể viết tắt)")
            tg = c2.text_input("Thời gian", t.get("thoi_gian") or "", placeholder="VD 12 tuần")
            mt = st.text_input("Mô tả ngắn", t.get("mo_ta") or "", placeholder="VD Nhân viên văn phòng, đau lưng dưới, tập 4 buổi/tuần")
            kq = st.text_input("Kết quả (cách nhau bằng dấu phẩy)", t.get("ket_qua") or "", placeholder="−8,5 kg, −9 cm eo, −6 % mỡ, hết đau lưng",
                               help="Ngăn cách bằng dấu phẩy + khoảng trắng (8,5 vẫn giữ nguyên)")
            loi = st.text_area("Lời chia sẻ của học viên", t.get("loi") or "", height=80)
            c1, c2, c3 = st.columns(3)
            dy = c1.checkbox("✅ Học viên ĐÃ ĐỒNG Ý đăng ảnh", value=bool(t.get("dong_y")))
            hien = c2.checkbox("Hiện cho khách xem", value=bool(t.get("hien", True)))
            tt = c3.number_input("Thứ tự", 1, 99, int(t.get("thu_tu") or 1))
            ok = st.form_submit_button("💾 Lưu ca này", type="primary", use_container_width=True)
        if ok:
            t2_ = {**t, "ten": ten.strip(), "thoi_gian": tg.strip(), "mo_ta": mt.strip(), "ket_qua": kq.strip(), "loi": loi.strip(),
                   "dong_y": dy, "hien": hien, "thu_tu": tt}
            if fa is not None:
                t2_["anh_truoc"] = _anh_moi(fa)
            if fb is not None:
                t2_["anh_sau"] = _anh_moi(fb)
            if not t2_.get("anh_ds") and (not t2_.get("anh_truoc") or not t2_.get("anh_sau")):
                st.error("Cần đủ ảnh TRƯỚC và SAU.")
            elif hinh.luu_transform(t2_, nguoi):
                st.toast("Đã lưu" + ("" if dy else " — đang ẩn vì chưa đánh dấu học viên đồng ý"))
                S.pop("tq_chon", None)
                st.rerun()
        if chon and st.button("🗑 Xoá ca này"):
            hinh.xoa_transform(chon, nguoi)
            S.pop("tq_chon", None)
            st.rerun()
        st.caption("Chỉ ca có **học viên đồng ý** + **Hiện** mới hiện cho khách. Nên che mặt / viết tắt tên nếu học viên muốn kín đáo.")
        ui.sec("Khách thấy như sau")
        gallery(hinh.transforms())
    with t3:
        DS = store.clients()
        if not DS:
            return
        by = {k["ma"]: k for k in DS}
        ma = st.selectbox("Khách", list(by), format_func=lambda m: by[m]["ho_ten"], key="av_kh")
        k = by[ma]
        a, b = st.columns([1, 2])
        with b:
            if not hinh.anh_goc_khach(k):
                st.info("Khách chưa có ảnh đầu khoá — tải ở **📈 Tiến độ › 📸 Ảnh**, hoặc tải ảnh đại diện riêng bên dưới.")
            y = st.slider("Vị trí khuôn mặt (từ trên xuống, %)", 0, 100, int(float(k.get("avatar_y") or 14)), key=f"avy_{ma}")
            r = st.slider("Độ zoom (nhỏ = gần mặt hơn)", 20, 100, int(float(k.get("avatar_r") or 62)), key=f"avr_{ma}")
            goc = hinh.anh_goc_khach(k)
            a.markdown(hinh.the_avatar(hinh._uri(goc, y, r, cat=not k.get("anh_dai_dien_vuong")) if goc else "", k["ho_ten"], 140),
                       unsafe_allow_html=True)
            f = st.file_uploader("Hoặc tải ảnh đại diện riêng", type=["jpg", "jpeg", "png", "webp"], key=f"av_f_{ma}")
            if st.button("💾 Lưu ảnh đại diện", type="primary", key=f"av_s_{ma}"):
                k1 = {**k, "avatar_y": y, "avatar_r": r}
                if f is not None:
                    k1["anh_dai_dien"] = _anh_moi(f, 900)
                if store.save_client(k1, nguoi):
                    st.toast("Đã lưu")
                    st.rerun()
            if k.get("anh_dai_dien") and st.button("↩ Dùng lại ảnh đầu khoá", key=f"av_r_{ma}"):
                store.save_client({**k, "anh_dai_dien": ""}, nguoi)
                st.rerun()
            st.caption("Kéo thanh trượt — ảnh bên trái đổi ngay; bấm Lưu để áp dụng cho khách.")


def nhap_zip(nguoi: str):
    """ZIP gồm manifest.json + ảnh: {"hlv": {"file", "y", "r"}, "transforms": [{"ten", "files": [...], "mo_ta", "thoi_gian",
    "ket_qua", "loi", "thu_tu"}]}. Mỗi ca lưu = học viên đã đồng ý (HLV chọn đưa lên) + hiện cho khách."""
    import json
    import zipfile
    st.caption("Tải file ZIP chuẩn bị sẵn (có manifest.json) — web tự tải ảnh lên Drive và tạo từng ca. Ca trùng tên sẽ được cập nhật.")
    f = st.file_uploader("File ZIP", type=["zip"], key="tq_zip")
    if f is None:
        return
    try:
        z = zipfile.ZipFile(f)
        mf = json.loads(z.read("manifest.json").decode("utf-8"))
    except Exception as e:  # noqa: BLE001
        st.error(f"File ZIP chưa đúng định dạng: {e}")
        return
    ds = mf.get("transforms") or []
    st.markdown(f"Tìm thấy **{len(ds)} ca** thành quả" + (" + **ảnh đại diện HLV**" if mf.get("hlv") else "") + ":")
    for t in ds:
        st.markdown(f"- {E(t.get('ten', ''))} · {len(t.get('files') or [])} ảnh")
    if not st.button("⬆️ Nhập tất cả", type="primary"):
        return
    cu = {t.get("ten"): t for t in hinh.transforms(ca_an=True)}
    tien = st.progress(0.0, text="Đang tải ảnh lên…")
    n = len(ds) + (1 if mf.get("hlv") else 0)
    i = 0
    if mf.get("hlv"):
        h = mf["hlv"]
        up = db.upload_images({"hlv": A.shrink(z.read(h["file"]), 1200)}, "HAC_HLV_")
        if up and up.get("hlv"):
            hinh.luu_ho_so_hlv({**hinh.ho_so_hlv(), "anh": up["hlv"], "y": h.get("y", 36), "r": h.get("r", 56)}, nguoi)
        i += 1
        tien.progress(i / n, text="Đã xong ảnh đại diện HLV")
    loi = []
    for t in ds:
        files = {f"a{j}": A.shrink(z.read(fn), 1350) for j, fn in enumerate(t.get("files") or [])}
        up = db.upload_images(files, "HAC_TQ_") if files else {}
        ids = [up.get(f"a{j}") for j in range(len(files))] if up else []
        if not ids or not all(ids):
            loi.append(t.get("ten", ""))
        else:
            goc = cu.get(t.get("ten"), {})
            hinh.luu_transform({**goc, **{k: v for k, v in t.items() if k != "files"}, "anh_ds": ids, "dong_y": True, "hien": True}, nguoi)
        i += 1
        tien.progress(i / n, text=f"Đã xong {t.get('ten', '')}")
    if loi:
        st.error("Chưa tải được: " + ", ".join(loi) + " — bấm Nhập lại (ca đã xong sẽ được cập nhật, không nhân đôi).")
    else:
        st.success(f"Đã nhập {len(ds)} ca thành quả" + (" và ảnh đại diện HLV" if mf.get("hlv") else "") + ".")
        st.balloons()
