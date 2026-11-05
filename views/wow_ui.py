# Hoàng Anh Coaching v2.3 (2026-11-05) — những chạm nhỏ khiến khách "wow": nút đi nhanh, chúc sinh nhật, quan tâm theo chu kỳ,
# tổng kết tuần bằng hình ảnh dễ nhớ (tổng tạ đã nâng quy ra vật quen thuộc), mốc thành tích.
from __future__ import annotations

import html
from datetime import timedelta

import streamlit as st

from core import buoi as bt, db, store, tien_do as td, ui

E = html.escape
S = st.session_state

# vật quen thuộc để quy đổi tổng tạ — khối lượng xấp xỉ, chỉ để vui
VAT = [(110, "chiếc xe máy tay ga", "🛵"), (1_200, "chiếc ô tô 4 chỗ", "🚗"), (4_000, "chú voi con", "🐘"),
       (12_000, "chiếc xe buýt", "🚌")]


def di_nhanh():
    pages = S.get("_trang_khach") or []
    if not pages:
        return
    with st.container(key="hac_di_toi"):
        for i in range(0, len(pages), 2):
            cols = st.columns(2)
            for j, p in enumerate(pages[i:i + 2]):
                cols[j].page_link(p, label=p.title, icon=p.icon, use_container_width=True)


def sinh_nhat(k: dict, ten: str):
    d = store._d(k.get("ngay_sinh"))
    hom = db.now_vn().date()
    if not d or (d.month, d.day) != (hom.month, hom.day):
        return
    tuoi = store.tuoi(k, hom)
    st.markdown(f'<div class="hac-hero" style="text-align:center"><div class="t">🎂 Chúc mừng sinh nhật {E(ten)}!</div>'
                f'<div class="s">Tuổi {tuoi} khoẻ hơn, mạnh hơn và tự tin hơn — HLV Hoàng Anh luôn đồng hành cùng bạn 💛</div></div>',
                unsafe_allow_html=True)
    if not S.get("_sn_balloons"):
        st.balloons()
        S["_sn_balloons"] = True


def chu_ky(k: dict):
    from core import chu_ky as ck
    x = ck.dieu_chinh(k["ma"], db.now_vn().date(), k)
    if x and x["nang"] and x["khach"]:
        st.markdown(f'<div class="hac-note" style="border-style:solid;border-color:#E6C46A;background:#FFF8E6">{E(x["khach"])}</div>',
                    unsafe_allow_html=True)


def tong_ket_tuan(k: dict):
    """7 ngày qua: số buổi, tổng tạ đã nâng (quy ra vật quen thuộc), cardio, cân TB."""
    ma = k["ma"]
    hom = db.now_vn().date()
    tu = hom - timedelta(days=6)
    ss = [s for s in bt.sessions(ma) if tu <= s["ngay"] <= hom]
    tan = sum(bt.tonnage(s["bai"]) for s in ss)
    tong_all = sum(bt.tonnage(s["bai"]) for s in bt.sessions(ma))
    if not ss and not tong_all:
        return
    from core import cardio as cd
    phut = sum(float(v.get("phut") or 0) for v in cd.logs(ma) if tu <= (store._d(v.get("ngay")) or tu - timedelta(days=1)) <= hom)
    vat = next(((n, t, i) for n, t, i in reversed(VAT) if tong_all >= n), VAT[0])
    so_vat = tong_all / vat[0]
    CAN = td.can_ngay(ma)
    can_s = ""
    if len(CAN) >= 8:
        a = CAN[CAN["ngay"] >= (hom - timedelta(days=6))]["kg"].mean()
        b = CAN[(CAN["ngay"] < (hom - timedelta(days=6))) & (CAN["ngay"] >= (hom - timedelta(days=13)))]["kg"].mean()
        if a == a and b == b:
            can_s = f"{a - b:+.1f} kg".replace(".", ",")
    ui.sec("📊 7 ngày qua của bạn")
    ui.tiles([(str(len(ss)), "buổi tập", ""), (f"{tan:,.0f} kg".replace(",", "."), "tổng tạ đã nâng", "kg × lần mọi hiệp"),
              (f"{phut:.0f} phút", "cardio", ""), (can_s or "—", "cân TB tuần", "so với tuần trước" if can_s else "")])
    if tong_all >= VAT[0][0]:
        tong_s = f"{tong_all:,.0f}".replace(",", ".")
        so_s = f"{so_vat:.1f}".replace(".", ",")
        st.markdown(f'<div class="hac-card" style="text-align:center;font-size:1.02rem">{vat[2]} Từ ngày bắt đầu, bạn đã nâng tổng cộng '
                    f'<b>{tong_s} kg</b> — nặng bằng khoảng <b>{so_s} {vat[1]}</b>! 💪</div>', unsafe_allow_html=True)


def moc_moi(k: dict):
    """Thẻ chúc mừng mốc thành tích mới (mỗi mốc chỉ hiện tới khi khách bấm cảm ơn)."""
    from core import wow
    ma = k["ma"]
    da = set(wow.moc_trang_thai(ma)["khach_xem"])
    moi = [m for m in wow.moc(k) if m["id"] not in da]
    if not moi:
        return
    m = moi[-1]
    st.markdown(f'<div class="hac-hero" style="text-align:center"><small>MỐC THÀNH TÍCH MỚI</small>'
                f'<div class="t" style="font-size:2rem">{m["icon"]} {E(m["ten"])}</div><div class="s">{E(m["loi"])}</div></div>',
                unsafe_allow_html=True)
    if not S.get(f"_moc_bb_{m['id']}"):
        st.balloons()
        S[f"_moc_bb_{m['id']}"] = True
    if st.button("💛 Cảm ơn HLV — xem tiếp", key=f"moc_ok_{m['id']}", use_container_width=True):
        wow.danh_dau_moc(ma, {"khach_xem": [x["id"] for x in moi]}, k.get("ho_ten", ""))
        st.rerun()
