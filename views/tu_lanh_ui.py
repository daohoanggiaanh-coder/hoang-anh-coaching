"""v4.0 — 🧊 Tủ lạnh: chọn món đang có → web đề xuất số gram để đạt kcal + đạm / tinh bột / béo mục tiêu."""
from __future__ import annotations

import html

import streamlit as st

from core import db, dinh_duong as dd, tu_lanh as tl

E = html.escape
S = st.session_state
CSS = """<style>
.tl-r{display:grid;grid-template-columns:2.2fr 1fr 1.6fr;gap:8px;align-items:center;padding:7px 10px;
 border-bottom:1px solid rgba(163,128,60,.18);font-size:.9rem}
.tl-r b{font-size:1.05rem}.tl-r small{opacity:.7;font-size:.74rem;display:block}
.tl-r.bo{opacity:.45}
.tl-c{border:1px solid rgba(200,162,74,.35);border-radius:14px;overflow:hidden;margin:6px 0 10px}
.tl-h{background:rgba(200,162,74,.12);padding:8px 12px;font-weight:700}
.tl-m{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin:8px 0}
.tl-m div{border:1px solid rgba(163,128,60,.3);border-radius:12px;padding:8px 10px;text-align:center}
.tl-m b{display:block;font-size:1.15rem}.tl-m small{opacity:.7;font-size:.72rem}
@media (max-width:640px){.tl-m{grid-template-columns:repeat(2,1fr)}}
</style>"""


def _key(ma: str) -> str:
    return f"tl|{ma}"


def da_luu(ma: str) -> list[str]:
    try:
        return list((db.latest("DinhDuong").get(_key(ma)) or {}).get("mon") or [])
    except Exception:  # noqa: BLE001
        return []


def _o(v: float, muc: float, dv: str = "g") -> str:
    lech = v - muc
    mau = "#2E7D4F" if abs(lech) <= max(0.08 * muc, 5) else ("#C0392B" if lech > 0 else "#D9822B")
    return f'<b>{v:.0f} {dv}</b><small>mục tiêu {muc:.0f} · <span style="color:{mau}">{lech:+.0f}</span></small>'


def tab(k: dict, vai: str, nguoi: str, h, kq: dict, F: dict, bo: set[str], tap_set: set[int]):
    st.markdown(CSS, unsafe_allow_html=True)
    ma = k["ma"]
    hom = db.now_vn().date()
    st.caption("Chọn các món đang có trong tủ lạnh / bếp → web tính mỗi món nên ăn bao nhiêu gram để vừa đủ calo và đạm, "
               "tinh bột, béo của mục tiêu. Thịt cá tính **đã nấu chín**, cơm / bún tính **chín**.")
    duoc = {m: f for m, f in F.items() if dd.duoc_an(f, h.che_do) and m not in bo}
    cu = [m for m in da_luu(ma) if m in duoc]
    chon = []
    nh_ds = list(tl.NHOM_TEN)
    cols = st.columns(2)
    for i, nh in enumerate(nh_ds):
        ids = sorted([m for m, f in duoc.items() if f.get("nhom") == nh], key=lambda m: duoc[m]["ten"])
        chon += cols[i % 2].multiselect(tl.NHOM_TEN[nh], ids, default=[m for m in cu if m in ids],
                                        format_func=lambda m: duoc[m]["ten"], key=f"tl_{nh}_{ma}_{vai}", placeholder="Chọn món…")
    c1, c2 = st.columns([1.4, 1])
    if c2.button("💾 Lưu tủ lạnh", use_container_width=True, key=f"tl_luu_{ma}_{vai}",
                 help="Lần sau mở ra web nhớ sẵn các món này."):
        if db.append("DinhDuong", _key(ma), {"mon": chon, "ngay": hom.isoformat()}, nguoi, ma):
            st.toast("Đã lưu các món trong tủ lạnh.")
    KIEU = {"ngay": "Cả ngày", "con": "Phần còn lại hôm nay", "bua": "Một bữa"}
    kieu = c1.segmented_control("Tính cho", list(KIEU), default="ngay", format_func=KIEU.get, key=f"tl_kieu_{ma}_{vai}") or "ngay"
    la_tap = st.toggle("Hôm nay có tập", value=hom.weekday() in tap_set, key=f"tl_tap_{ma}_{vai}")
    m = kq["tap"] if la_tap else kq["nghi"]
    muc, he_so, nhan = {x: float(m[x]) for x in ("kcal", "p", "c", "f")}, 2.5, "cả ngày"
    if kieu == "bua":
        B = dd.phan_bua(h, m, la_tap)
        bb = st.selectbox("Bữa", B, format_func=lambda b: f"{b['ten']} · ~{b['kcal']:.0f} kcal", key=f"tl_bua_{ma}_{vai}")
        muc, he_so, nhan = {x: float(bb[x]) for x in ("kcal", "p", "c", "f")}, 1.0, bb["ten"].lower()
    elif kieu == "con":
        from core import an_ngoai as an
        from views.an_ngoai_ui import _thuc_don
        td_, m_ = _thuc_don(h, kq, ma, hom, la_tap, bo)
        t = an.tong_ngay(td_, an.nhat_ky(ma, hom), m_)
        muc = {x: max(float(t["con"][x]), 0) for x in ("kcal", "p", "c", "f")}
        he_so, nhan = max(1.0, 2.5 * t["so_chua"] / max(len(td_), 1)), "phần còn lại hôm nay"
        st.caption(f"Đã ghi ăn hôm nay: {t['da']['kcal']:.0f} kcal · Đ {t['da']['p']:.0f} g → còn **{muc['kcal']:.0f} kcal** · "
                   f"Đ {muc['p']:.0f} · TB {muc['c']:.0f} · B {muc['f']:.0f} g (ghi bữa ở tab 📝 Đã ăn · còn lại).")
        if muc["kcal"] < 80:
            st.success("Hôm nay đã ăn đủ mục tiêu 👍")
            return
    if not chon:
        st.info("Chọn ít nhất 1 món đạm + 1 món tinh bột để web tính.")
        return
    kq_ = tl.goi_y(chon, muc, F, he_so)
    t = kq_["tong"]
    st.markdown('<div class="tl-m">' + "".join(f"<div><small>{n}</small>{_o(t[x if x != 'kcal' else 'kcal_macro'], muc[x], dv)}</div>"
                                                for n, x, dv in (("Calo", "kcal", "kcal"), ("Đạm", "p", "g"), ("Tinh bột", "c", "g"),
                                                                 ("Béo", "f", "g"))) + "</div>", unsafe_allow_html=True)
    so_bua = len(dd.LICH_BUA.get(int(h.so_bua), dd.LICH_BUA[4])) if kieu == "ngay" else 1
    dong = []
    for d in kq_["ds"]:
        if d.get("bo"):
            dong.append(f'<div class="tl-r bo"><div>{E(d["ten"])}<small>không cần dùng — đã đủ từ các món khác</small></div><div>0 g</div><div></div></div>')
            continue
        chia = f"≈ {d['g'] / so_bua:.0f} g / bữa nếu chia {so_bua} bữa" if so_bua > 1 and d["nhom"] not in ("beo",) else ""
        dong.append(f'<div class="tl-r"><div>{E(d["ten"])}<small>{E(d["luong"])}{" · " if d["luong"] and chia else ""}{E(chia)}</small></div>'
                    f'<div><b>{d["g"]:.0f} g</b></div>'
                    f'<div><small>{d["kcal"]:.0f} kcal · Đ {d["p"]:.0f} · TB {d["c"]:.0f} · B {d["f"]:.0f} g</small></div></div>')
    st.markdown(f'<div class="tl-c"><div class="tl-h">🍽 Gợi ý lượng ăn — {E(nhan)}</div>{"".join(dong)}</div>', unsafe_allow_html=True)
    for c in kq_["canh_bao"]:
        st.warning(c)
    mua = tl.nen_mua(kq_["thieu_nhom"], F, h.che_do, bo, chon)
    if mua:
        st.info("🛒 Nên mua thêm: " + ", ".join(mua))
    st.caption("Lượng tính theo bảng thực phẩm của app (ước tính, sai số ±10–15% tuỳ cách nấu). Dầu ăn để nấu nhớ đong; "
               "rau giữ lượng cố định vì ít calo. " + ("Muốn ăn đúng hơn: ghi lại ở tab 📝 Đã ăn · còn lại." if vai != "hlv" else ""))
