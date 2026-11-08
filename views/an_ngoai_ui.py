# Hoàng Anh Coaching v2.0 (2026-11-03) — tab "Đã ăn · còn lại" (nhật ký từng bữa) + tab "Ăn ngoài".
from __future__ import annotations

import html
from datetime import date

import streamlit as st

from core import an_ai, an_ngoai as an, anh as A, db, dinh_duong as dd, store, ui

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
            if chon == "ghi":
                con_truoc = {x: t["con"][x] + (tt[x] if tt else 0) for x in ("kcal", "p", "c", "f")}
                khung_ghi(k, ngay, bb["bua"], bb["ten"], lg if loai == "ghi" else {}, t["chia"].get(bb["bua"]) or bb["thuc"],
                          con_truoc, nguoi, vai)
                continue
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
    ui.sec("🍪 Bữa phụ · ăn vặt · ăn thêm")
    for b_, v_ in an.bua_them(logs):
        with st.container(border=True):
            c1, c2 = st.columns([5, 1])
            c1.markdown(f"**{E(v_.get('ten') or 'Ăn thêm')}** · {float(v_.get('kcal') or 0):.0f} kcal · Đ {float(v_.get('p') or 0):.0f} · "
                        f"TB {float(v_.get('c') or 0):.0f} · B {float(v_.get('f') or 0):.0f} g" + (f" · 🕒 {v_.get('gio')}" if v_.get("gio") else ""))
            if c2.button("🗑", key=f"an_xt_{ma}_{vai}_{b_}", help="Xoá"):
                an.xoa(ma, ngay, b_, nguoi)
                st.rerun()
            if v_.get("loai") == "ghi":
                hien_ghi(v_, k, ngay, b_, nguoi, vai)
    kt = f"an_moi_{ma}_{vai}_{ngay}"
    if kt not in S:
        S[kt] = "them_" + db.now_vn().strftime("%H%M%S")
    with st.expander("➕ Thêm bữa phụ / ăn vặt (chụp ảnh hoặc ghi món)"):
        con_now = dict(t["con"])
        khung_ghi(k, ngay, S[kt], "Bữa phụ", {}, {x: max(con_now[x], 0) * 0.3 for x in con_now}, con_now, nguoi, vai, them=True)
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
        from views import ban_tay_ui as _bt
        if muc_bua:
            st.markdown(f"**Bữa tới của bạn ≈** {_bt.dong_ban_tay(muc_bua, 0)} · thêm 1–2 nắm tay rau")
            st.markdown(_bt.the_ban_tay(an.so_phan(muc_bua, 180)), unsafe_allow_html=True)
        else:
            st.markdown(_bt.the_ban_tay(), unsafe_allow_html=True)
        st.markdown("\n".join(f"- {x}" for x in _bt.HUONG_DAN_AN_NGOAI))
        st.caption("Áng chừng bằng bàn tay (theo hướng dẫn phổ biến của Precision Nutrition) — sai số lớn hơn cân, đủ dùng khi ăn ngoài. "
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



# ------------------------------------------------------------------ v2.5: ghi bữa bằng ảnh / mô tả + AI
def _bang_mon(mon: list[dict]) -> str:
    if not mon:
        return ""
    return ('<table style="width:100%;font-size:.82rem;border-collapse:collapse;margin:4px 0">'
            '<tr style="color:#8b8577;text-align:left"><th>Món</th><th>Lượng</th><th>kcal</th><th>Đạm</th><th>TB</th><th>Béo</th></tr>'
            + "".join(f'<tr style="border-top:1px solid #EFE7D6"><td>{E(m["ten"])}</td><td>{E(m.get("luong", ""))}</td>'
                      f'<td><b>{m["kcal"]:.0f}</b></td><td>{m["p"]:.0f}</td><td>{m["c"]:.0f}</td><td>{m["f"]:.0f}</td></tr>' for m in mon)
            + "</table>")


def _ket_qua_ai(r: dict):
    st.markdown(_bang_mon(r.get("mon") or []), unsafe_allow_html=True)
    st.markdown(f"**{'AI ước lượng' if r.get('nguon') == 'ai' else 'Ước lượng'}:** {r['tong']['kcal']:.0f} kcal · đạm {r['tong']['p']:.0f} g · tinh bột {r['tong']['c']:.0f} g · "
                f"béo {r['tong']['f']:.0f} g · {an_ai.TIN_CAY.get(r.get('do_tin_cay'), '')}"
                + (" · _(chưa có AI — ước lượng từ mô tả)_" if r.get("nguon") == "offline" else ""))
    if r.get("nhan_xet"):
        st.markdown(f"💬 {E(r['nhan_xet'])}")
    for x in r.get("dieu_chinh") or []:
        st.markdown(f"- 🔧 {E(x)}")
    if r.get("bua_sau"):
        st.markdown(f"➡️ **Bữa tiếp theo:** {E(r['bua_sau'])}")


def hien_ghi(lg: dict, k: dict, ngay, bua: str, nguoi: str, vai: str):
    """Bữa đã lưu bằng ảnh / mô tả: ảnh, mô tả, kết quả AI, nhận xét HLV."""
    ids = [i for i in (lg.get("anh") or []) if i]
    if ids:
        imgs = db.get_images(ids)
        cs = st.columns(min(len(ids), 3) + 1)
        for i, x in enumerate(ids[:3]):
            if imgs.get(x):
                cs[i].image(A.shrink(imgs[x], 500), use_container_width=True)
    if lg.get("mo_ta"):
        st.caption("📝 " + lg["mo_ta"])
    if lg.get("ai"):
        _ket_qua_ai(lg["ai"])
    if vai == "hlv":
        nx = st.text_input("💬 Nhận xét của HLV (khách thấy)", lg.get("hlv_nx", ""), key=f"an_nx_{k['ma']}_{ngay}_{bua}")
        if nx != lg.get("hlv_nx", "") and st.button("Lưu nhận xét", key=f"an_nxs_{k['ma']}_{ngay}_{bua}"):
            an.ghi(k["ma"], ngay, bua, {**{x: v for x, v in lg.items() if not x.startswith("_")}, "hlv_nx": nx}, nguoi)
            st.rerun()
    elif lg.get("hlv_nx"):
        st.info("💬 HLV: " + lg["hlv_nx"])


def khung_ghi(k: dict, ngay, bua: str, ten_bua: str, lg: dict, muc_bua: dict, con_truoc: dict, nguoi: str, vai: str,
              them: bool = False):
    from core import thong_tin as ttin
    ma = k["ma"]
    kk = f"{ma}_{vai}_{ngay}_{bua}"
    if lg:
        hien_ghi(lg, k, ngay, bua, nguoi, vai)
    with st.expander("✏️ " + ("Sửa lại bữa này" if lg else "Chụp ảnh / ghi món để AI tính"), expanded=not lg and not them):
        fs = st.file_uploader("Ảnh bữa ăn (tối đa 3 — chụp thẳng từ trên xuống, thấy rõ cả đĩa)", type=["jpg", "jpeg", "png", "webp"],
                              accept_multiple_files=True, key=f"an_up_{kk}")
        mo_ta = st.text_area("Mô tả món (càng rõ lượng càng chính xác)", lg.get("mo_ta", ""), key=f"an_mt_{kk}", height=80,
                             placeholder="VD: 1 chén cơm, 150g ức gà áp chảo, rau muống xào, 1 trái chuối")
        if st.button("🤖 AI phân tích bữa này", key=f"an_ai_{kk}", type="primary", disabled=not (fs or mo_ta.strip())):
            imgs = [A.shrink(f.getvalue(), 1024) for f in (fs or [])[:3]]
            with st.spinner("AI đang xem bữa ăn…"):
                r = an_ai.phan_tich(imgs, mo_ta, ten_bua, ttin.TEN.get(ttin.muc_tieu(k), ""), k.get("gioi_tinh") or "",
                                    muc_bua, con_truoc, store.xung(k)[0])
            S[f"an_kq_{kk}"] = (r, imgs)
        if S.get(f"an_kq_{kk}"):
            r, imgs = S[f"an_kq_{kk}"]
            _ket_qua_ai(r)
            st.caption("Số AI là ước lượng (±20–30 %). Biết chính xác hơn thì sửa trước khi lưu.")
            c0, c1, c2, c3 = st.columns(4)
            kc = c0.number_input("kcal", 0, 4000, int(r["tong"]["kcal"]), 10, key=f"an_ak_{kk}")
            p = c1.number_input("Đạm g", 0, 400, int(r["tong"]["p"]), key=f"an_ap_{kk}")
            c = c2.number_input("Tinh bột g", 0, 600, int(r["tong"]["c"]), key=f"an_ac_{kk}")
            f = c3.number_input("Béo g", 0, 300, int(r["tong"]["f"]), key=f"an_af_{kk}")
            if st.button("💾 Lưu bữa này", key=f"an_luu_{kk}", type="primary"):
                ids = []
                if imgs:
                    up = db.upload_images({f"{i}": b for i, b in enumerate(imgs)}, prefix=f"an_{ma}_{ngay}_{bua}_") or {}
                    ids = list(up.values())
                ten = ", ".join(m["ten"] for m in r.get("mon", [])[:3]) or (mo_ta[:40] if mo_ta else "Bữa ăn")
                v = {"loai": "ghi", "ten": ten, "mo_ta": mo_ta, "anh": ids or lg.get("anh") or [], "ai": r,
                     "kcal": kc, "p": p, "c": c, "f": f, "gio": db.now_vn().strftime("%H:%M")}
                if an.ghi(ma, ngay, bua, v, nguoi):
                    S.pop(f"an_kq_{kk}", None)
                    if them:
                        S.pop(f"an_moi_{ma}_{vai}_{ngay}", None)
                    st.toast("Đã lưu ✓")
                    st.rerun()
                st.error("Chưa lưu được — thử lại.")


# ------------------------------------------------------------------ v2.5: báo cáo dinh dưỡng theo ngày
def bao_cao(k: dict, vai: str, nguoi: str, h, kq: dict, bo: set[str], tap_set: set[int]):
    import pandas as pd
    st.markdown(CSS, unsafe_allow_html=True)
    ma = k["ma"]
    hom = db.now_vn().date()
    from datetime import timedelta
    tu = hom - timedelta(days=13)
    LS = an.lich_su(ma, tu, hom)
    rows = []
    for i in range(14):
        d = tu + timedelta(days=i)
        la_tap = d.weekday() in tap_set
        td_, m = _thuc_don(h, kq, ma, d, la_tap, bo)
        t = an.tong_ngay(td_, LS.get(d, {}), m)
        so_ghi = len([v for v in LS.get(d, {}).values() if v.get("loai") != "chua"])
        rows.append({"ngay": d, "da": t["da"], "muc": t["muc"], "ghi": so_ghi, "bua": len(td_)})
    df = pd.DataFrame([{"Ngày": f"{r['ngay']:%d/%m}", "kcal ăn": round(r["da"]["kcal"]) if r["ghi"] else None,
                        "kcal mục tiêu": round(r["muc"]["kcal"]), "Đạm ăn": round(r["da"]["p"]) if r["ghi"] else None,
                        "Đạm mục tiêu": round(r["muc"]["p"])} for r in rows])
    co = [r for r in rows if r["ghi"]]
    if co:
        tb_k = sum(r["da"]["kcal"] for r in co) / len(co)
        tb_m = sum(r["muc"]["kcal"] for r in co) / len(co)
        tb_p = sum(r["da"]["p"] for r in co) / len(co)
        ui.tiles([(f"{len(co)}/14", "ngày có ghi bữa", ""), (f"{tb_k:,.0f}".replace(",", "."), "kcal TB / ngày", f"mục tiêu {tb_m:,.0f}".replace(",", ".")),
                  (f"{tb_p:.0f} g", "đạm TB / ngày", f"mục tiêu {co[-1]['muc']['p']:.0f} g"),
                  (f"{sum(1 for r in co if abs(r['da']['kcal'] - r['muc']['kcal']) <= 0.1 * r['muc']['kcal'])}", "ngày đúng ±10 % kcal", "")])
        st.line_chart(df.set_index("Ngày")[["kcal ăn", "kcal mục tiêu"]], height=220, color=["#C8A24A", "#8b8577"])
        st.bar_chart(df.set_index("Ngày")[["Đạm ăn", "Đạm mục tiêu"]], height=200, stack=False, color=["#2E7D4F", "#CFC8B8"])
    else:
        st.info("14 ngày qua chưa ghi bữa nào — ghi ở tab 📝 Đã ăn · còn lại.")
    ui.sec("Xem chi tiết 1 ngày")
    d = st.date_input("Ngày", hom, min_value=tu, max_value=hom, format="DD/MM/YYYY", key=f"an_bc_d_{ma}_{vai}")
    lg = LS.get(d, {})
    td_, m = _thuc_don(h, kq, ma, d, d.weekday() in tap_set, bo)
    t = an.tong_ngay(td_, lg, m)
    st.markdown(bang_con(t), unsafe_allow_html=True)
    ten = {b["bua"]: f"🕒 {b['gio']} · {b['ten']}" for b in td_}
    if not lg:
        st.caption("Ngày này chưa ghi bữa nào.")
    for b, v in sorted(lg.items(), key=lambda x: (x[0] not in ten, x[0])):
        if v.get("loai") == "chua":
            continue
        with st.container(border=True):
            tt = an.thuc_te(next((x for x in td_ if x["bua"] == b), {"thuc": {"kcal": 0, "p": 0, "c": 0, "f": 0}}), v) or {}
            st.markdown(f"**{E(ten.get(b, '🍪 Bữa phụ' + (' · ' + v['gio'] if v.get('gio') else '')))}** — {an.LOAI.get(v.get('loai'), '')}"
                        + (f": {E(v.get('ten'))}" if v.get("ten") else "")
                        + (f"  \n{tt.get('kcal', 0):.0f} kcal · Đ {tt.get('p', 0):.0f} · TB {tt.get('c', 0):.0f} · B {tt.get('f', 0):.0f} g" if tt else ""))
            if v.get("loai") == "ghi":
                hien_ghi(v, k, d, b, nguoi, vai)
            elif v.get("ghi_chu"):
                st.caption("📝 " + v["ghi_chu"])
