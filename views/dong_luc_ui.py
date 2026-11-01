# Hoàng Anh Coaching v1.5 (2026-10-31) — giao diện động lực: chuỗi lửa, cấp độ, nhiệm vụ hôm nay, check-in, huy hiệu,
# hướng dẫn lần đầu (chỉ hiện 1 lần) và hướng dẫn cài app lên điện thoại.
from __future__ import annotations

import html
from datetime import datetime, timedelta

import streamlit as st

from core import db, dong_luc as dl, store

E = html.escape
S = st.session_state
LINK = {"tap": "tap_luyen", "cardio": "cardio", "can": None, "checkin": None}
CSS = """<style>
.dl-hero{background:radial-gradient(circle at 12% 0%,#4a3b22,#17140F 62%);border-radius:24px;padding:20px 22px;color:#F3ECDC;
  border:1px solid rgba(232,199,106,.35);display:grid;grid-template-columns:auto 1fr;gap:22px;align-items:center;margin:4px 0 12px}
@media(max-width:640px){.dl-hero{grid-template-columns:1fr;gap:12px}}
.dl-fire{text-align:center;min-width:120px}.dl-fire .n{font-size:3.4rem;font-weight:900;line-height:1;color:#fff}
.dl-fire .f{font-size:2.6rem;filter:drop-shadow(0 0 14px rgba(255,140,40,.7))}.dl-fire .f.off{filter:grayscale(1);opacity:.45}
.dl-fire small{display:block;font-size:.7rem;letter-spacing:.14em;color:#E8C76A;font-weight:800;margin-top:4px}
.dl-cap .t{font-size:.66rem;letter-spacing:.16em;color:#E8C76A;font-weight:800}.dl-cap .c{font-size:1.4rem;font-weight:900;color:#fff}
.dl-cap .bar{height:10px;border-radius:9px;background:rgba(255,255,255,.12);margin:8px 0 5px;overflow:hidden}
.dl-cap .bar span{display:block;height:100%;background:linear-gradient(90deg,#C8A24A,#F6E3A1)}
.dl-cap .r{font-size:.78rem;color:#D8D1C1;display:flex;gap:14px;flex-wrap:wrap}.dl-cap .r b{color:#fff}
.dl-warn{background:linear-gradient(90deg,#B4442F,#D9653F);color:#fff;border-radius:14px;padding:10px 14px;font-weight:700;margin:0 0 10px}
.dl-ok{background:linear-gradient(90deg,#1E7B4A,#2E9D61);color:#fff;border-radius:14px;padding:10px 14px;font-weight:700;margin:0 0 10px}
.dl-nv{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin:6px 0 10px}
@media(max-width:760px){.dl-nv{grid-template-columns:repeat(2,1fr)}}
.dl-nv a{text-decoration:none}
.dl-m{background:#fff;border:1.5px solid #E6DCC6;border-radius:16px;padding:12px;text-align:center;color:#1C1B19;height:100%}
.dl-m.x{background:#F0F9F3;border-color:#2E9D61}.dl-m .i{font-size:1.6rem}.dl-m .t{font-weight:800;font-size:.86rem;margin-top:2px}
.dl-m .s{font-size:.72rem;color:#8b8577}.dl-m.x .s{color:#1E7B4A;font-weight:800}
.dl-14{display:flex;gap:6px;flex-wrap:wrap;margin:6px 0 12px}
.dl-14 div{width:30px;height:30px;border-radius:9px;display:grid;place-items:center;font-size:.66rem;font-weight:800;color:#1C1B19}
.dl-bd{display:grid;grid-template-columns:repeat(auto-fill,minmax(130px,1fr));gap:10px;margin:6px 0}
.dl-b{background:#fff;border:1px solid #E6DCC6;border-radius:14px;padding:10px;text-align:center}
.dl-b .i{font-size:1.7rem}.dl-b .t{font-weight:800;font-size:.8rem}.dl-b .m{font-size:.66rem;color:#8b8577}
.dl-b.no{opacity:.4;filter:grayscale(1)}
</style>"""


def _con_lai() -> str:
    now = db.now_vn()
    het = datetime.combine(now.date() + timedelta(days=1), datetime.min.time()).replace(tzinfo=now.tzinfo)
    s = int((het - now).total_seconds())
    return f"{s // 3600} giờ {s % 3600 // 60} phút"


def the_chinh(k: dict, t: dict):
    st.markdown(CSS, unsafe_allow_html=True)
    cap, sau = t["cap"], t["cap_sau"]
    lua = t["chuoi"]
    st.markdown(
        f'<div class="dl-hero"><div class="dl-fire"><div class="f{"" if lua else " off"}">🔥</div><div class="n">{lua}</div>'
        f'<small>NGÀY GIỮ LỬA</small></div>'
        f'<div class="dl-cap"><div class="t">CẤP ĐỘ</div><div class="c">{cap[2]} {E(cap[1])}</div>'
        f'<div class="bar"><span style="width:{t["pct_cap"]}%"></span></div>'
        f'<div class="r"><span><b>{t["xp"]:,}</b> điểm</span>'.replace(",", ".")
        + (f'<span>còn <b>{sau[0] - t["xp"]:,}</b> điểm lên {sau[2]} {E(sau[1])}</span>'.replace(",", ".") if sau else "<span>Cấp cao nhất 👑</span>")
        + f'<span>🛡️ <b>{t["khien"]}</b> khiên</span><span>Kỷ lục chuỗi <b>{t["dai_nhat"]}</b> ngày</span></div></div></div>',
        unsafe_allow_html=True)
    xong = sum(1 for x in t["nv"] if x["xong"])
    con = len(t["nv"]) - xong
    if t["lua_hom"] and con == 0:
        st.markdown('<div class="dl-ok">✅ Hôm nay hoàn thành 100% — xuất sắc! +20 điểm thưởng. Hẹn bạn ngày mai 🔥</div>', unsafe_allow_html=True)
        if not S.get(f"dl_mung_{k['ma']}_{t['hom']}"):
            S[f"dl_mung_{k['ma']}_{t['hom']}"] = True
            st.balloons()
    elif t["lua_hom"]:
        st.markdown(f'<div class="dl-ok">🔥 Đã giữ lửa hôm nay. Làm nốt {con} việc để lấy trọn điểm + thưởng 100%.</div>', unsafe_allow_html=True)
    else:
        can = max(0, -(-len(t["nv"]) * 2 // 3) - xong)
        st.markdown(f'<div class="dl-warn">⏳ Còn {_con_lai()} — làm thêm {can} việc để giữ lửa'
                    f'{" chuỗi " + str(t["chuoi"]) + " ngày" if t["chuoi"] else ""}'
                    + (f' (có {t["khien"]} khiên đỡ nếu lỡ)' if t["khien"] else "") + "</div>", unsafe_allow_html=True)
    o = ""
    for x in t["nv"]:
        sub = "✓ Xong · +" + str(DIEM_X(x)) if x["xong"] else (f'{x["lam"]}/{x["tg"]} phút' if x["id"] == "cardio" else f'+{dl.DIEM[x["id"]]} điểm')
        the = f'<div class="dl-m{" x" if x["xong"] else ""}"><div class="i">{x["icon"]}</div><div class="t">{E(x["ten"])}</div><div class="s">{sub}</div></div>'
        o += f'<a href="/{LINK[x["id"]]}" target="_self">{the}</a>' if LINK.get(x["id"]) and not x["xong"] else the
    st.markdown(f'<div class="dl-nv">{o}</div>', unsafe_allow_html=True)


def DIEM_X(x: dict) -> int:
    return dl.DIEM[x["id"]]


def tuan_va_lich(t: dict):
    a, b = st.columns([1, 2])
    tt = t["diem_tt"]
    a.metric("Điểm chăm chỉ tuần này", f"{t['diem_tuan']}/100",
             None if tt is None else f"{t['diem_tuan'] - tt:+} so với tuần trước", help="Trung bình % nhiệm vụ đã làm mỗi ngày trong tuần")
    with b:
        o = ""
        for x in t["ngay"][-14:]:
            mau = "#2E9D61" if x["tl"] == 1 else "#E8C76A" if x["lua"] else "#F2C9BF" if x["tl"] > 0 else "#EEE8DA"
            o += f'<div style="background:{mau}" title="{x["ngay"]:%d/%m} · {round(x["tl"] * 100)}%">{x["ngay"]:%d}</div>'
        st.markdown("<small><b>14 ngày gần nhất</b> — 🟩 đủ 100% · 🟨 giữ lửa · 🟥 làm ít</small>"
                    f'<div class="dl-14">{o}</div>', unsafe_allow_html=True)


def huy_hieu(t: dict):
    co = sum(1 for h in t["huy_hieu"] if h["co"])
    with st.expander(f"🏅 Huy hiệu {co}/{len(t['huy_hieu'])}"):
        st.markdown('<div class="dl-bd">' + "".join(
            f'<div class="dl-b{"" if h["co"] else " no"}"><div class="i">{h["icon"]}</div><div class="t">{E(h["ten"])}</div>'
            f'<div class="m">{E(h["mo_ta"])}</div></div>' for h in t["huy_hieu"]) + "</div>", unsafe_allow_html=True)


def check_in(k: dict, nguoi: str, t: dict):
    ma = k["ma"]
    hom = t["hom"]
    cu = dl.checkins(ma).get(hom, {})
    with st.expander("📝 Check-in hôm nay — ăn · nước · ngủ · năng lượng" + (" ✅" if cu else ""), expanded=not cu):
        with st.form(f"ci_{ma}_{hom}"):
            a, b = st.columns(2)
            an = a.select_slider("Ăn theo thực đơn", [0, 25, 50, 75, 100], value=int(cu.get("an", 75)), format_func=lambda v: f"{v}%")
            nuoc = b.select_slider("Nước (lít)", [0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0], value=float(cu.get("nuoc", 2.0)))
            a, b = st.columns(2)
            ngu = a.select_slider("Ngủ đêm qua (giờ)", [4, 5, 6, 7, 8, 9, 10], value=int(cu.get("ngu", 7)))
            nl = b.select_slider("Năng lượng hôm nay", [1, 2, 3, 4, 5], value=int(cu.get("nang_luong", 3)),
                                 format_func={1: "😫 Kiệt sức", 2: "😕 Mệt", 3: "🙂 Ổn", 4: "😃 Tốt", 5: "🔥 Rất sung"}.get)
            gc = st.text_input("Gửi HLV (không bắt buộc)", value=cu.get("ghi_chu", ""), placeholder="VD: hôm nay đi đám cưới, ăn ngoài")
            if st.form_submit_button("✅ Gửi check-in" if not cu else "💾 Cập nhật", type="primary", use_container_width=True):
                if dl.luu_checkin(ma, hom, {"an": an, "nuoc": nuoc, "ngu": ngu, "nang_luong": nl, "ghi_chu": gc.strip()}, nguoi):
                    st.toast("Đã check-in +15 điểm 🔥")
                    st.rerun()
                st.error("Chưa gửi được — thử lại.")


# ------------------------------------------------------------------ hướng dẫn cài app
def huong_dan_cai():
    a, b = st.tabs(["🍎 iPhone", "🤖 Android"])
    with a:
        st.markdown("""
1. Nếu đang mở link trong **Zalo / Messenger**: bấm **⋯** (góc trên) → **Mở bằng trình duyệt** → chọn **Safari**.
2. Trong **Safari**, bấm nút **Chia sẻ** ⬆️ (ô vuông có mũi tên ở thanh dưới).
3. Kéo xuống chọn **Thêm vào MH chính** (*Add to Home Screen*).
4. Bấm **Thêm** — biểu tượng **HA Coaching** xuất hiện trên màn hình như một app.

💡 Chắc ăn nhất là dùng **Safari**. Chrome trên iPhone (iOS 16.4 trở lên) cũng có mục này trong nút Chia sẻ.
""")
    with b:
        st.markdown("""
1. Nếu đang mở link trong **Zalo / Messenger**: bấm **⋮** → **Mở bằng trình duyệt** → chọn **Chrome**.
2. Trong **Chrome**, bấm **⋮** (góc trên bên phải).
3. Chọn **Thêm vào màn hình chính** hoặc **Cài đặt ứng dụng**.
4. Bấm **Thêm / Cài đặt** — biểu tượng **HA Coaching** xuất hiện ngoài màn hình.
""")
    st.caption("Mở app → nếu đã chọn 'Ghi nhớ đăng nhập' thì vào thẳng, không cần gõ lại mật khẩu.")


# ------------------------------------------------------------------ hướng dẫn lần đầu (chỉ 1 lần)
BUOC = [
    ("👋", "Chào mừng bạn!", "Đây là app riêng giữa bạn và HLV Hoàng Anh. Mọi thứ — giáo án, thực đơn, cardio, tiến độ — đều tính riêng "
     "cho cơ thể và mục tiêu của bạn. <b>Bạn báo cáo đều → HLV chỉnh đúng → bạn đạt mục tiêu nhanh hơn.</b>"),
    ("🔥", "Mỗi ngày: giữ lửa", "Trang <b>Tổng quan</b> có vài nhiệm vụ nhỏ: cân buổi sáng, check-in ăn · ngủ · nước, ghi buổi tập, cardio. "
     "Làm từ <b>2/3</b> số việc là giữ được lửa 🔥. Mỗi 7 ngày liền được 1 <b>khiên</b> 🛡️ đỡ cho ngày lỡ. Điểm tích luỹ lên cấp "
     "🌱 → ⚔️ → 🛡️ → 🔩 → 💎 → 👑 và mở huy hiệu."),
    ("🏋️", "Tập luyện", "Mục <b>Tập luyện</b>: xem giáo án HLV soạn, bấm <b>🖼 Cách tập đúng</b> dưới mỗi bài để xem ảnh và lỗi hay sai. "
     "Tập xong ghi <b>kg × lần</b> từng hiệp — web nhớ lần trước và gợi ý tăng tạ."),
    ("🍽", "Thực đơn & cardio", "<b>Thực đơn</b> ghi sẵn gram từng món theo kiểu ăn Việt; muốn đổi món cứ bấm đổi, web tự tính lại. "
     "<b>Cardio</b>: làm đủ phút mỗi ngày; hôm nào thiếu, web tự chia đều phần thiếu cho các ngày còn lại."),
    ("📲", "Cài app lên điện thoại", None),
]


@st.dialog("Hướng dẫn nhanh", width="large")
def _dialog(k: dict, nguoi: str):
    i = S.get("ob_i", 0)
    ic, tieu, nd = BUOC[i]
    st.markdown(f"<div style='text-align:center;font-size:3rem'>{ic}</div>"
                f"<h3 style='text-align:center;margin:0 0 8px'>{tieu}</h3>", unsafe_allow_html=True)
    if nd:
        st.markdown(f"<div style='font-size:1rem;line-height:1.6'>{nd}</div>", unsafe_allow_html=True)
    else:
        st.markdown("Để mở nhanh như app (không cần tìm link Zalo mỗi lần):")
        huong_dan_cai()
    st.progress((i + 1) / len(BUOC), text=f"{i + 1} / {len(BUOC)}")
    a, b = st.columns(2)
    if i > 0 and a.button("← Trước", use_container_width=True):
        S["ob_i"] = i - 1
        st.rerun()
    if i < len(BUOC) - 1:
        if b.button("Tiếp →", type="primary", use_container_width=True):
            S["ob_i"] = i + 1
            st.rerun()
    elif b.button("Bắt đầu thôi 🚀", type="primary", use_container_width=True):
        S["ob_xong"] = True
        S.pop("ob_i", None)
        st.rerun()


def lan_dau(k: dict, nguoi: str):
    """Hiện 1 lần duy nhất cho mỗi khách (lưu trên máy chủ — đổi điện thoại cũng không hiện lại). Xem lại ở trang Tài khoản."""
    if S.get("_xem_nhu") or S.get("ob_xong"):
        return
    ma = k["ma"]
    if not S.get("ob_dang") and dl.da_xem(ma).get("onboard"):
        return
    if not S.get("ob_dang"):
        dl.danh_dau_xem(ma, "onboard", nguoi)        # đánh dấu ngay khi hiện — lỡ đóng cũng không hiện lại
        S["ob_dang"] = True
    _dialog(k, nguoi)


def xem_lai(k: dict, nguoi: str):
    if st.button("📘 Xem lại hướng dẫn nhanh"):
        S["ob_dang"], S["ob_i"] = True, 0
        S.pop("ob_xong", None)
        _dialog(k, nguoi)


# ------------------------------------------------------------------ HLV: bảng cam kết
def bang_hlv(DS: list[dict]):
    st.markdown(CSS, unsafe_allow_html=True)
    rows = dl.cam_ket_tat_ca(DS)
    rows.sort(key=lambda r: (r["t"]["diem_tuan"], r["t"]["chuoi"]))
    for r in rows:
        k, t = r["k"], r["t"]
        thieu = [x["ten"] for x in t["nv"] if not x["xong"]]
        ci = dl.checkins(k["ma"]).get(t["hom"])
        mau = "#B4442F" if t["diem_tuan"] < 50 else "#C8A24A" if t["diem_tuan"] < 80 else "#1E7B4A"
        with st.container(border=True):
            a, b, c, d = st.columns([2.2, 1, 1, 1.2])
            from core import hinh
            a.markdown(f"<div style='display:flex;gap:10px;align-items:center'>{hinh.the_avatar(hinh.avatar_khach(k), k['ho_ten'], 46)}"
                       f"<div><b>{E(k['ho_ten'])}</b> · {t['cap'][2]} {t['cap'][1]}<br>"
                       + (f"Báo cáo gần nhất: <b>{r['lan_cuoi']:%d/%m}</b>" if r["lan_cuoi"] else "Chưa báo cáo lần nào") + "</div></div>",
                       unsafe_allow_html=True)
            b.metric("🔥 Chuỗi", t["chuoi"])
            c.markdown(f"<div style='font-size:.75rem;color:#8b8577'>Điểm tuần</div><div style='font-size:1.6rem;font-weight:900;"
                       f"color:{mau}'>{t['diem_tuan']}</div>", unsafe_allow_html=True)
            d.markdown("**Hôm nay còn:**  \n" + (", ".join(thieu) if thieu else "✅ đủ hết"))
            if ci:
                st.caption(f"Check-in: ăn {ci.get('an')}% · nước {ci.get('nuoc')} L · ngủ {ci.get('ngu')} h · năng lượng {ci.get('nang_luong')}/5"
                           + (f" · 💬 {ci['ghi_chu']}" if ci.get("ghi_chu") else ""))
            if thieu and t["diem_tuan"] < 80:
                goi, _ = store.xung(k)
                st.code(f"{goi[:1].upper() + goi[1:]} ơi, hôm nay còn {', '.join(x.lower() for x in thieu)} nè 💪 "
                        f"Chuỗi {t['chuoi']} ngày đang chờ {goi} giữ lửa đó 🔥 Vào app báo cáo giúp HLV nha!", language=None, wrap_lines=True)
