"""v3.5 — 📦 Gói & buổi tập: mỗi khách đã mua bao nhiêu buổi, đã tập bao nhiêu, còn bao nhiêu · cập nhật nhanh · gia hạn · nhập từ ModunSoft."""
from __future__ import annotations

import html
import json
from datetime import date

import pandas as pd
import streamlit as st

from core import db, goi, store, ui

S = st.session_state
E = html.escape
CSS = """<style>
.gb-r{display:grid;grid-template-columns:minmax(150px,1.4fr) minmax(120px,1fr) 2fr 1.1fr;gap:10px;align-items:center;
 padding:9px 12px;border:1px solid rgba(163,128,60,.25);border-radius:12px;margin:6px 0}
.gb-r b{font-size:.98rem}.gb-r small{opacity:.75;display:block;line-height:1.35}
.gb-bar{height:12px;border-radius:7px;background:rgba(128,128,128,.18);overflow:hidden;position:relative}
.gb-bar i{display:block;height:100%;border-radius:7px}
.gb-n{font-size:1.25rem;font-weight:700;text-align:right}.gb-n small{font-size:.75rem;font-weight:400}
@media (max-width:640px){.gb-r{grid-template-columns:1fr 1fr}.gb-n{text-align:left}}
</style>"""


def _mau(t: dict) -> str:
    if t["con"] is None:
        return "#4B6A88"
    if t["con"] <= 0:
        return "#B4442F"
    return "#E08A3C" if t["con"] <= 2 else "#2E7D4F"


def _dong(k: dict, t: dict, hom: date) -> str:
    if t["loai"] != "buoi":
        kt = t["het_han"]
        tien = f"còn {(kt - hom).days + 1} ngày · hết {kt:%d/%m/%Y}" if kt else "chưa có ngày hết"
        bar, so = "", f'{t["da"]}<small> buổi đã tập</small>'
        giua = f"<small>Gói theo thời gian — {E(tien)}</small>"
    else:
        tong, da = t["tong"], t["da"]
        p = min(da / tong, 1) if tong else 0
        bar = f'<div class="gb-bar"><i style="width:{p * 100:.0f}%;background:{_mau(t)}"></i></div>'
        giua = bar + f'<small>Đã tập <b>{da}</b> / {tong} buổi' + (f' · <b style="color:#B4442F">vượt {t["vuot"]}</b>' if t["vuot"] else "") + "</small>"
        so = (f'<span style="color:{_mau(t)}">{t["con"] if t["con"] is not None else "—"}</span><small> còn</small>'
              if tong else '<small>chưa ghi số buổi</small>')
    phu = []
    if t["bat_dau"]:
        phu.append(f"từ {t['bat_dau']:%d/%m}")
    if t["so_goi"] > 1:
        phu.append(f"gói thứ {t['so_goi']} · tổng {t['tong_da']}/{t['tong_mua']} buổi")
    cuoi = f"tập cuối {t['buoi_cuoi']:%d/%m}" if t["buoi_cuoi"] else "chưa ✅ buổi nào trên web"
    toi = f"buổi tới {store.THU[t['buoi_toi'].weekday()]} {t['buoi_toi']:%d/%m}" if t["buoi_toi"] else "chưa có lịch tới"
    return (f'<div class="gb-r"><div><b>{E(k.get("ho_ten", ""))}</b><small>{E(cuoi)} · {E(toi)}</small></div>'
            f'<div><b style="font-size:.9rem">{E(t["ten"])}</b><small>{E(" · ".join(phu))}</small></div>'
            f'<div>{giua}</div><div class="gb-n">{so}</div></div>')


def trang(u: dict):
    ui.hero("GÓI & BUỔI TẬP", "Đã mua · đã tập · còn lại của từng khách",
            "Mỗi lần bấm ✅ Đã tập ở trang Lịch (hoặc ghi buổi giáo án) là tự trừ 1 buổi.")
    st.markdown(CSS, unsafe_allow_html=True)
    hom = db.now_vn().date()
    DS = [k for k in store.clients() if not k.get("xoa")]
    H = store.hens()
    dang = [k for k in DS if (k.get("trang_thai") or "Đang tập") == "Đang tập"]
    T = {k["ma"]: goi.tong_quan(k, H, hom) for k in dang}
    het = [k for k in dang if T[k["ma"]]["con"] is not None and T[k["ma"]]["con"] <= 0]
    sap = [k for k in dang if T[k["ma"]]["con"] is not None and 0 < T[k["ma"]]["con"] <= 3]
    chua = [k for k in dang if T[k["ma"]]["loai"] == "buoi" and not T[k["ma"]]["tong"]]
    ui.tiles([(str(len(dang)), "Khách đang tập", ""),
              (str(sum(max(t["con"] or 0, 0) for t in T.values())), "Buổi còn phải dạy", "các gói theo buổi"),
              (str(len(sap)), "Sắp hết (≤ 3 buổi)", ", ".join(k["ho_ten"] for k in sap)[:60]),
              (str(len(het)), "Hết buổi / vượt", ", ".join(k["ho_ten"] for k in het)[:60])])
    if S.get("gb_msg"):
        st.success(S.pop("gb_msg"))
    if chua:
        st.info("Chưa ghi số buổi gói: " + ", ".join(k["ho_ten"] for k in chua) + " — điền ở tab ✏️ Cập nhật nhanh.")
    t1, t2, t3, t4 = st.tabs(["📋 Tổng quan", "✏️ Cập nhật nhanh", "➕ Gia hạn / gói mới", "📥 Nhập từ ModunSoft"])
    with t1:
        PH = sorted({store.phong(k) for k in dang}, key=store.thu_tu_phong)
        for p in PH:
            nhom = sorted([k for k in dang if store.phong(k) == p],
                          key=lambda k: (T[k["ma"]]["con"] if T[k["ma"]]["con"] is not None else 999, k.get("ho_ten", "")))
            ui.sec(f"🏢 {p or 'Chưa ghi phòng'} ({len(nhom)})")
            st.markdown("".join(_dong(k, T[k["ma"]], hom) for k in nhom), unsafe_allow_html=True)
        with st.expander("📜 Lịch sử các gói đã mua"):
            for k in dang:
                ls = goi.lich_su(k)
                if ls:
                    st.markdown(f"**{k['ho_ten']}** — " + " · ".join(
                        f"{x.get('ten', '')} ({x.get('buoi', '')} buổi, {str(x.get('ngay', ''))[:10]})" for x in ls))
    with t2:
        _cap_nhat(dang, T, H, u)
    with t3:
        _gia_han(dang, T, H, u, hom)
    with t4:
        _nhap(DS, H, u)


def _cap_nhat(dang, T, H, u):
    st.caption("Sửa thẳng trong bảng rồi bấm Lưu. **Đã tập (gói này)** = số buổi khách đã dùng của gói hiện tại tính đến hôm nay — "
               "các buổi ✅ sau này web tự cộng thêm.")
    df = pd.DataFrame([{"ma": k["ma"], "Khách": k["ho_ten"], "Phòng": store.phong(k) or "—", "Tên gói": T[k["ma"]]["ten"] if k.get("goi_ten") else "",
                        "Tổng buổi gói": T[k["ma"]]["tong"] or None, "Đã tập (gói này)": T[k["ma"]]["da"],
                        "Ngày bắt đầu gói": T[k["ma"]]["bat_dau"]} for k in dang if T[k["ma"]]["loai"] == "buoi"])
    if df.empty:
        st.caption("Chưa có khách gói theo buổi.")
        return
    ED = st.data_editor(df, hide_index=True, use_container_width=True, key="gb_ed", disabled=["ma", "Khách", "Phòng"],
                        column_config={"ma": None,
                                       "Tổng buổi gói": st.column_config.NumberColumn(min_value=0, max_value=500, step=1),
                                       "Đã tập (gói này)": st.column_config.NumberColumn(min_value=0, max_value=500, step=1),
                                       "Ngày bắt đầu gói": st.column_config.DateColumn(format="DD/MM/YYYY")})
    if st.button("💾 Lưu thay đổi", type="primary", key="gb_luu"):
        KH, n = {k["ma"]: k for k in dang}, 0
        for (_, a), (_, b) in zip(df.iterrows(), ED.iterrows()):
            if all(str(a[c]) == str(b[c]) for c in ("Tên gói", "Tổng buổi gói", "Đã tập (gói này)", "Ngày bắt đầu gói")):
                continue
            k = dict(KH[b["ma"]])
            nbd = b["Ngày bắt đầu gói"]
            nbd = nbd if isinstance(nbd, date) else (pd.to_datetime(nbd).date() if pd.notna(nbd) else None)
            k.update({"goi_ten": str(b["Tên gói"] or "").strip(), "goi_loai": "buoi",
                      "goi_buoi": int(b["Tổng buổi gói"]) if pd.notna(b["Tổng buổi gói"]) else "",
                      "ngay_bat_dau": nbd.isoformat() if nbd else ""})
            k = goi.dat_da_tap(k, int(b["Đã tập (gói này)"] or 0), H)    # tính lại theo ngày bắt đầu mới
            n += bool(store.save_client(k, u["name"]))
        S["gb_msg"] = f"Đã lưu {n} khách."
        st.rerun()


def _gia_han(dang, T, H, u, hom):
    if not dang:
        return
    by = {k["ma"]: k for k in dang}
    ma = st.selectbox("Khách", list(by), format_func=lambda m: f"{by[m]['ho_ten']} · {T[m]['ten']}"
                      + (f" · còn {T[m]['con']} buổi" if T[m]["con"] is not None else ""), key="gh_k")
    t = T[ma]
    G = [x for x in store.goi_list() if x.get("loai", "buoi") == "buoi"]
    a, b = st.columns(2)
    mau = a.selectbox("Gói", ["(tự nhập)"] + [g["ten"] for g in G], key="gh_mau")
    g = next((x for x in G if x["ten"] == mau), {})
    ten = b.text_input("Tên gói", g.get("ten", t["ten"] if t["ten"] != "Chưa ghi gói" else ""), key=f"gh_ten_{mau}")
    c, d, e = st.columns(3)
    so = c.number_input("Số buổi", 1, 500, int(float(g.get("so") or t["tong"] or 12)), key=f"gh_so_{mau}")
    gia = d.text_input("Giá", str(g.get("gia", "")), key=f"gh_gia_{mau}", placeholder="9.500.000")
    ngay = e.date_input("Ngày bắt đầu", hom, format="DD/MM/YYYY", key="gh_ng")
    cd = False
    if t["con"]:
        cd = st.checkbox(f"Cộng {t['con']} buổi còn của gói cũ vào gói mới" if t["con"] > 0 else
                         f"Trừ {-t['con']} buổi tập vượt của gói cũ vào gói mới", value=t["con"] > 0, key="gh_cd")
    st.caption("Gói đang dùng sẽ chuyển vào lịch sử (vẫn xem được ở tab Tổng quan).")
    if st.button("➕ Lưu gói mới", type="primary", key="gh_luu"):
        k = goi.gia_han(by[ma], ten.strip(), int(so), ngay, gia.strip(), cd, H)
        if cd and t["con"] < 0:
            k["goi_buoi"] = int(so) + t["con"]
        if store.save_client(k, u["name"]):
            S["gb_msg"] = f"Đã ghi gói mới cho {by[ma]['ho_ten']}: {k['goi_buoi']} buổi từ {ngay:%d/%m/%Y}."
            st.rerun()


def _nhap(DS, H, u):
    """File JSON [{ten, goi_ten, goi_buoi, ngay_bat_dau, da_goi_nay, gia, goi_ls}] — Claude tạo từ ModunSoft + sổ PT."""
    from core import quet_inbody as qi
    st.caption("Tải file .json tổng hợp từ ModunSoft (gói đã mua) + sổ buổi PT Atlas (buổi đã tập). Web tự nhận khách theo tên, "
               "anh xem bảng rồi bấm Áp dụng.")
    f = st.file_uploader("File gói (.json)", type=["json"], key=f"gn_f{S.get('gn_v', 0)}")
    if f is None:
        return
    try:
        R = json.loads(f.getvalue().decode("utf-8"))
        R = R.get("khach", R) if isinstance(R, dict) else R
    except ValueError:
        st.error("File không đọc được.")
        return
    by = {k["ma"]: k for k in DS}
    rows = []
    for r in R:
        ma, d = qi.khop_khach(r.get("ten", ""), DS, "Atlas")
        rows.append({"Áp dụng": bool(ma), "Tên trong file": r.get("ten", ""),
                     "Khách trên web": by[ma]["ho_ten"] if ma else "— không khớp —", "Gói": r.get("goi_ten", ""),
                     "Tổng": r.get("goi_buoi"), "Đã tập": r.get("da_goi_nay"),
                     "Còn": (int(r.get("goi_buoi") or 0) - int(r.get("da_goi_nay") or 0)) if r.get("goi_buoi") else None,
                     "Bắt đầu": r.get("ngay_bat_dau", ""), "Gói trước": len(r.get("goi_ls") or []), "_ma": ma or ""})
    df = pd.DataFrame(rows)
    ED = st.data_editor(df, hide_index=True, use_container_width=True, key="gn_ed",
                        disabled=[c for c in df.columns if c != "Áp dụng"], column_config={"_ma": None})
    if st.button(f"✅ Áp dụng {int(ED['Áp dụng'].sum())} khách", type="primary", key="gn_ok"):
        n = 0
        for i, row in ED.iterrows():
            if row["Áp dụng"] and row["_ma"]:
                n += bool(store.save_client(goi.ap_dung_nhap(by[row["_ma"]], R[i], H), u["name"]))
        S["gn_v"] = S.get("gn_v", 0) + 1
        S["gb_msg"] = f"Đã cập nhật gói cho {n} khách."
        st.rerun()
