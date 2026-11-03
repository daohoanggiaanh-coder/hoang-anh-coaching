# Hoàng Anh Coaching v2.0 (2026-11-03) — tab "Đã ăn · còn lại" (nhật ký từng bữa) + tab "Ăn ngoài".
from __future__ import annotations

import html
from datetime import date

import streamlit as st

from core import an_ngoai as an, db, dinh_duong as dd, ui

E = html.escape
S = st.session_state

CSS = """<style>
.an-c{border:1px solid #E7DFCF;border-radius:14px;padding:12px 14px;margin:0 0 10px;background:rgba(255,255,255,.55)}
html[data-hac-theme=dark] .an-c{background:rgba(255,255,255,.04);border-color:#3A372F}
.an-c h4{margin:0 0 2px;font-size:1rem}.an-c .s{font-size:.78rem;opacity:.75}
.an-chip{display:inline-block;font-size:.7rem;font-weight:700;border-radius:999px;padding:1px 8px;color:#fff;margin-left:6px;vertical-align:middle}
.an-mac{display:flex;gap:10px;flex-wrap:wrap;font-size:.82rem;margin:6px 0}.an-mac b{font-size:.95rem}
.an-r{font-size:.84rem;margin:2px 0}.an-r span{display:inline-block;min-width:58px;font-weight:700}
.an-con{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin:6px 0 12px}
.an-con div{border-radius:12px;padding:8px 10px;background:#1C1B19;color:#F3ECDC}
.an-con small{display:block;font-size:.66rem;letter-spacing:.08em;opacity:.75;font-weight:800}
.an-con b{font-size:1.15rem}.an-con i{font-style:normal;font-size:.72rem;opacity:.75;display:block}
.an-con .am b{color:#F09A86}
@media (max-width:640px){.an-con{grid-template-columns:repeat(2,1fr)}}
</style>"""


def _so(x: float) -> str:
    return f"{x:,.0f}".replace(",", ".")


def _o_con(nhan: str, con: float, da: float, muc: float, dv: str) -> str:
    am = con < 0
    return (f'<div class="{"am" if am else ""}"><small>{nhan} {"VƯỢT" if am else "CÒN"}</small><b>{_so(abs(con))} {dv}</b>'
            f'<i>đã {_so(da)} / {_so(muc)} {dv}</i></div>')


def bang_con(t: dict) -> str:
    d, m, c = t["da"], t["muc"], t["con"]
    return ('<div class="an-con">' + _o_con("KCAL", c["kcal"], d["kcal"], m["kcal"], "") + _o_con("ĐẠM", c["p"], d["p"], m["p"], "g")
            + _o_con("TINH BỘT", c["c"], d["c"], m["c"], "g") + _o_con("BÉO", c["f"], d["f"], m["f"], "g") + "</div>")


def the_mon(m: dict, phan: float | None = None, thich: bool = False) -> str:
    ten, mau = an.HOP[m["hop"]]
    x = an.macro(m, phan or 1.0)
    goi_phan = f' · <b>nên ăn {an.PHAN.get(phan, phan)}</b>' if phan and phan != 1.0 else ""
    luu = f'<div class="an-r">ℹ️ {E(m["luu_y"])}</div>' if m.get("luu_y") else ""
    return (f'<div class="an-c"><h4>{"⭐ " if thich else ""}{E(m["ten"])}<span class="an-chip" style="background:{mau}">{ten}</span></h4>'
            f'<div class="s">{E(m["nhom"])} · {E(m["phan"])}{goi_phan}</div>'
            f'<div class="an-mac"><span><b>≈ {_so(x["kcal"])}</b> kcal</span><span>Đạm <b>{x["p"]:.0f}</b> g</span>'
            f'<span>Tinh bột <b>{x["c"]:.0f}</b> g</span><span>Béo <b>{x["f"]:.0f}</b> g</span></div>'
            f'<div class="an-r"><span>Gọi</span>{E(m["goi"])}</div><div class="an-r"><span>Bỏ</span>{E(m["bo"])}</div>'
            f'<div class="an-r"><span>Thêm</span>{E(m["them"])}</div>{luu}</div>')


def _thuc_don(h, kq, ma: str, ngay: date, la_tap: bool, bo: set[str]) -> tuple[list[dict], dict]:
    doi = S.get(f"dd_doi_{ma}", {})
    td = dd.thuc_don_ngay(h, kq, la_tap, ngay.weekday(), ma, doi.get(ngay.weekday()), bo)
    return td, (kq["tap"] if la_tap else kq["nghi"])


# ------------------------------------------------------------------ nhật ký bữa
def nhat_ky(k: dict, vai: str, nguoi: str, h, kq: dict, F: dict, bo: set[str], tap_set: set[int]):
    st.markdown(CSS, unsafe_allow_html=True)
    ma = k["ma"]
    hom = db.now_vn().date()
    a, b = st.columns([2, 1])
    ngay = a.date_input("Ngày", hom, max_value=hom, format="DD/MM/YYYY", key=f"an_ngay_{ma}_{vai}")
    la_tap = b.toggle("Ngày có tập", value=ngay.weekday() in tap_set, key=f"an_tap_{ma}_{vai}_{ngay}")
    td, m = _thuc_don(h, kq, ma, ngay, la_tap, bo)
    logs = an.nhat_ky(ma, ngay)
    t = an.tong_ngay(td, logs, m)
    st.markdown(bang_con(t), unsafe_allow_html=True)
    for x in an.loi_khuyen(t):
        st.caption("💡 " + x)
    M = an.mon()
    th = an.thich(ma)
    rieng = {f"r{i}": r for i, r in enumerate(th["rieng"])}
    for bb in td:
        lg = logs.get(bb["bua"]) or {}
        loai = lg.get("loai", "chua")
        with st.container(border=True):
            tt = an.thuc_te(bb, lg)
            dau = (f"**🕒 {bb['gio']} · {bb['ten']}**  \n🎯 Mục tiêu bữa: **{bb['thuc']['kcal']:.0f} kcal** · Đạm {bb['thuc']['p']:.0f} g · "
                   f"Tinh bột {bb['thuc']['c']:.0f} g · Béo {bb['thuc']['f']:.0f} g")
            if tt:
                dau += (f"  \n{an.LOAI[loai]}" + (f" — {lg.get('ten')}" if lg.get("ten") else "")
                        + f": **{tt['kcal']:.0f} kcal** · Đ {tt['p']:.0f} · TB {tt['c']:.0f} · B {tt['f']:.0f} g")
            elif bb["bua"] in t["chia"] and t["so_chua"] < len(td):
                c = t["chia"][bb["bua"]]
                dau += (f"  \n⏳ Chưa ăn — để bù đúng ngày, bữa này nên khoảng **{c['kcal']:.0f} kcal** · Đ {c['p']:.0f} · "
                        f"TB {c['c']:.0f} · B {c['f']:.0f} g")
            st.markdown(dau)
            kk = f"{ma}_{vai}_{ngay}_{bb['bua']}"
            ds_loai = list(an.LOAI)
            chon = st.segmented_control("Bữa này", ds_loai, default=loai, format_func=lambda z: an.LOAI[z], key=f"an_l_{kk}",
                                        label_visibility="collapsed") or loai
            v: dict | None = None
            if chon == "dung":
                v = {"loai": "dung", "ten": bb.get("mon_viet") or "Theo thực đơn"}
            elif chon == "chua":
                v = {"loai": "chua"}
            elif chon == "ngoai":
                ids = th["mon"] + [i for i in M if i not in th["mon"]] + list(rieng)
                c1, c2 = st.columns([3, 1])
                mid = c1.selectbox("Món", ids, index=ids.index(lg["mon"]) if lg.get("mon") in ids else 0,
                                   format_func=lambda z: ("⭐ " if z in th["mon"] or z in rieng else "") + (M.get(z) or rieng.get(z, {})).get("ten", z),
                                   key=f"an_m_{kk}")
                mm = M.get(mid) or rieng.get(mid) or {}
                ph = c2.selectbox("Phần", list(an.PHAN), index=list(an.PHAN).index(float(lg.get("phan") or 1.0))
                                  if float(lg.get("phan") or 1.0) in an.PHAN else 2, format_func=lambda z: an.PHAN[z], key=f"an_p_{kk}")
                if mid in M:
                    st.markdown(the_mon(M[mid], ph), unsafe_allow_html=True)
                v = {"loai": "ngoai", "mon": mid, "phan": ph, "ten": mm.get("ten", mid)} | an.macro(mm, ph)
            else:
                c0, c1, c2, c3, c4 = st.columns([2, 1, 1, 1, 1])
                ten = c0.text_input("Ăn gì", lg.get("ten", ""), key=f"an_t_{kk}", placeholder="VD: 1 hộp cơm gà")
                kc = c1.number_input("kcal", 0, 3000, int(lg.get("kcal") or 0), 10, key=f"an_k_{kk}")
                p = c2.number_input("Đạm g", 0, 300, int(lg.get("p") or 0), key=f"an_pp_{kk}")
                c = c3.number_input("Tinh bột g", 0, 500, int(lg.get("c") or 0), key=f"an_c_{kk}")
                f = c4.number_input("Béo g", 0, 300, int(lg.get("f") or 0), key=f"an_f_{kk}")
                if not kc and (p or c or f):
                    kc = p * 4 + c * 4 + f * 9
                v = {"loai": "tu_nhap", "ten": ten, "kcal": kc, "p": p, "c": c, "f": f}
            ghi_chu = st.text_input("Ghi chú (tuỳ chọn)", lg.get("ghi_chu", ""), key=f"an_g_{kk}", label_visibility="collapsed",
                                    placeholder="Ghi chú cho HLV (tuỳ chọn)")
            if st.button("💾 Lưu bữa này", key=f"an_s_{kk}", type="primary" if chon != loai else "secondary"):
                if an.ghi(ma, ngay, bb["bua"], (v or {}) | {"ghi_chu": ghi_chu}, nguoi):
                    st.toast("Đã lưu ✓")
                    st.rerun()
                else:
                    st.error("Chưa lưu được — thử lại sau ít phút.")
    ui.note("Mục tiêu từng bữa lấy theo thực đơn gợi ý. Khi một bữa ăn khác đi (ăn ngoài, ăn thêm), web <b>chia lại phần còn lại</b> "
            "cho các bữa chưa ăn — xem dòng ⏳ ở mỗi bữa. Macro món ăn ngoài là ước lượng (sai số ±20–30 %), dùng để định hướng, "
            "không cần chính xác tuyệt đối.")


# ------------------------------------------------------------------ ăn ngoài
def an_ngoai(k: dict, vai: str, nguoi: str, h, kq: dict, bo: set[str], tap_set: set[int]):
    st.markdown(CSS, unsafe_allow_html=True)
    ma = k["ma"]
    hom = db.now_vn().date()
    th = an.thich(ma)
    M = an.mon()
    td, m = _thuc_don(h, kq, ma, hom, hom.weekday() in tap_set, bo)
    t = an.tong_ngay(td, an.nhat_ky(ma, hom), m)
    ke = next((b for b in td if b["bua"] in t["chia"]), None)
    muc_bua = t["chia"].get(ke["bua"]) if ke else None
    with st.expander("📏 Nguyên tắc ăn ngoài & áng chừng bằng bàn tay", expanded=False):
        st.markdown("\n".join(f"- {x}" for x in an.data()["nguyen_tac"]))
        st.markdown("""
| Nhóm | Áng chừng mỗi bữa | Tương đương (ước lượng) |
|---|---|---|
| Đạm (thịt, cá, trứng, đậu hũ) | Nữ 1 lòng bàn tay · Nam 2 lòng bàn tay | ≈ 100–120 g chín ≈ 20–30 g đạm / lòng bàn tay |
| Tinh bột (cơm, bún, bánh) | Nữ 1 nắm tay · Nam 1–2 nắm tay | 1 nắm tay ≈ 1 chén cơm nhỏ ≈ 30–40 g tinh bột |
| Rau | 1–2 nắm tay trở lên | ăn thoải mái |
| Béo (dầu, bơ, hạt, sốt) | Nữ 1 ngón cái · Nam 1–2 ngón cái | 1 ngón cái ≈ 7–12 g béo |
""")
        st.caption("Phương pháp áng chừng bằng bàn tay (hand-portion) là cách ước lượng thực hành, sai số lớn hơn cân — đủ dùng khi ăn ngoài. "
                   "Lòng bàn tay = cỡ và độ dày lòng bàn tay của chính bạn, không tính ngón.")
    ui.sec("Gợi ý cho bữa tới" + (f" · {ke['ten']}" if ke else ""))
    if muc_bua:
        st.caption(f"Bữa tới còn khoảng {muc_bua['kcal']:.0f} kcal · Đạm {muc_bua['p']:.0f} g · Tinh bột {muc_bua['c']:.0f} g · Béo {muc_bua['f']:.0f} g "
                   "(theo nhật ký hôm nay). Món ⭐ là món bạn hay ăn.")
    else:
        st.caption("Hôm nay đã ghi đủ các bữa — gợi ý dưới đây cho bữa bình thường.")
    for x in an.goi_y(h.muc_tieu, muc_bua, th["mon"], n=4):
        st.markdown(the_mon(x, an.phan_hop(x, muc_bua) if muc_bua else None, x["id"] in th["mon"]), unsafe_allow_html=True)

    ui.sec("Tất cả món")
    a, b = st.columns([2, 1])
    nh = a.pills("Nhóm", an.nhom(), selection_mode="multi", key=f"an_nh_{ma}_{vai}", label_visibility="collapsed")
    tim = b.text_input("Tìm món", key=f"an_tim_{ma}_{vai}", placeholder="🔍 Tìm món…", label_visibility="collapsed")
    ds = [x for x in an.data()["mon"] if (not nh or x["nhom"] in nh) and (not tim or tim.lower() in x["ten"].lower())]
    ds.sort(key=lambda x: (x["id"] not in th["mon"], ["tot", "sua", "han_che"].index(x["hop"])))
    c = st.columns(2)
    for i, x in enumerate(ds):
        c[i % 2].markdown(the_mon(x, None, x["id"] in th["mon"]), unsafe_allow_html=True)

    ui.sec("⭐ Món hay ăn")
    with st.form(f"an_thich_{ma}_{vai}"):
        chon = st.multiselect("Món bạn hay ăn ngoài (ưu tiên trong gợi ý)", list(M), default=[x for x in th["mon"] if x in M],
                              format_func=lambda z: M[z]["ten"], placeholder="Chọn món")
        st.markdown("**Thêm món riêng** (món quen không có trong danh sách — nhập ước lượng, HLV có thể sửa)")
        c0, c1, c2, c3, c4 = st.columns([2, 1, 1, 1, 1])
        ten = c0.text_input("Tên món", placeholder="VD: Cơm văn phòng quán cô Ba")
        kc = c1.number_input("kcal", 0, 3000, 0, 10)
        p = c2.number_input("Đạm g", 0, 300, 0)
        cc = c3.number_input("Tinh bột g", 0, 500, 0)
        f = c4.number_input("Béo g", 0, 300, 0)
        xoa_r = st.multiselect("Xoá món riêng", [r["ten"] for r in th["rieng"]], placeholder="Chọn món riêng cần xoá") if th["rieng"] else []
        if st.form_submit_button("💾 Lưu", type="primary"):
            rieng = [r for r in th["rieng"] if r["ten"] not in xoa_r]
            if ten.strip():
                rieng.append({"ten": ten.strip(), "kcal": kc or p * 4 + cc * 4 + f * 9, "p": p, "c": cc, "f": f})
            if an.luu_thich(ma, {"mon": chon, "rieng": rieng}, nguoi):
                st.toast("Đã lưu ✓")
                st.rerun()
            st.error("Chưa lưu được — thử lại sau ít phút.")
    if th["rieng"]:
        st.caption("Món riêng: " + " · ".join(f"{r['ten']} (≈ {r['kcal']:.0f} kcal, Đ {r['p']:.0f} g)" for r in th["rieng"]))
    st.caption(an.data()["_ghi_chu"])

