# Hoàng Anh Coaching v1.0 (2026-10-31) — trang HLV: lịch & nhắc tập, khách & tài khoản, giáo án, dinh dưỡng,
# tiến độ & báo cáo, soạn tin Zalo, bảng thực phẩm, chuyển dữ liệu từ Atlas Academy
from __future__ import annotations

import html
import json
from datetime import date, timedelta

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from core import anh as _anh, auth, config, db, dinh_duong as dd, goi, store, tien_do as td, ui
from views import common as C

E = html.escape
S = st.session_state
MAU = {"hen": ("#A3803C", "HẸN"), "xong": ("#1E7B4A", "ĐÃ TẬP"), "huy": ("#8b8577", "NGHỈ")}


def _user() -> dict:
    u = auth.current_user()
    if not u or u.get("role") != "coach":
        st.error("Trang này chỉ dành cho HLV.")
        st.stop()
    return u


def _hang_cho(u: dict):
    CHO = store.hang_cho()
    if CHO:
        with st.container(border=True):
            st.markdown(f"**🤖 Chờ Claude gửi qua Zalo · {len(CHO)} tin** — nhắn Claude “gửi hàng chờ Hoàng Anh Coaching”.")
            for c in CHO:
                a, b = st.columns([5, 1], vertical_alignment="center")
                a.caption(f"{c.get('ho_ten')} (Zalo: {c.get('ten_zalo') or '—'}): {str(c.get('noi_dung'))[:90]}…")
                if b.button("Bỏ", key=f"bo_{c['_khoa']}"):
                    store.danh_dau_gui(c["_khoa"], u["name"], bo=True)
                    st.rerun()


def _soan(k: dict, txt: str, key: str, u: dict, hien: bool = True):
    """Khung tin: chép · mở Zalo · nhờ Claude gửi."""
    from core import zalo
    if hien:
        st.code(txt, language=None, wrap_lines=True)
    a, b = st.columns(2)
    lk = zalo.link(k.get("sdt"))
    if lk:
        a.link_button("💬 Mở Zalo", lk, use_container_width=True)
    if b.button("📤 Nhờ Claude gửi", key=f"q_{key}", use_container_width=True, type="primary",
                help="Xếp vào hàng chờ — nhắn Claude “gửi hàng chờ Hoàng Anh Coaching”, Claude gửi qua Zalo Web trên Chrome của anh"):
        if store.xep_hang(k, txt, u["name"]):
            st.toast("Đã xếp vào hàng chờ")
            st.rerun()


def _chon_khach(DS: list[dict], key: str = "hlv_kh") -> dict | None:
    if not DS:
        st.info("Chưa có khách — thêm ở trang **👤 Khách & tài khoản**.")
        return None
    by = {k["ma"]: k for k in DS}
    lua = [k["ma"] for k in sorted(DS, key=lambda k: ((k.get("trang_thai") or "Đang tập") != "Đang tập", store.thu_tu_phong(store.phong(k)),
                                                     str(k.get("ho_ten", ""))))]
    mac = S.get("hlv_kh") if S.get("hlv_kh") in lua else lua[0]
    ma = st.selectbox("Khách", lua, index=lua.index(mac), key=f"{key}_sel",
                      format_func=lambda m: (f"🏢 {store.phong(by[m])} · " if store.phong(by[m]) else "") + f"{by[m]['ho_ten']} · {by[m].get('trang_thai') or 'Đang tập'}"
                                            + (f" · {by[m]['hinh_thuc']}" if by[m].get("hinh_thuc") else "")
                                            )
    S["hlv_kh"] = ma
    return by[ma]


# =================================================================== LỊCH
def _phong_tong(dang: list[dict], B: list[dict], tuan0: date):
    """Số khách đang tập + số buổi tuần này theo từng phòng tập."""
    if not dang:
        return
    nhom: dict[str, list[dict]] = {}
    for k in dang:
        nhom.setdefault(store.phong(k) or "Chưa ghi phòng", []).append(k)
    for p in store.PHONG_TAP:                               # luôn hiện đủ Atlas · Gold Gym · Online
        nhom.setdefault(p, [])
    tuan = [b for b in B if tuan0 <= b["ngay"] <= tuan0 + timedelta(days=6) and b["trang_thai"] != "huy"]
    by = {k["ma"]: k for k in dang}
    ui.sec("🏢 Khách theo phòng tập")
    ui.tiles([(len(v), p, f"{len([b for b in tuan if b['ma'] in {x['ma'] for x in v}])} buổi tuần này")
              for p, v in sorted(nhom.items(), key=lambda x: store.thu_tu_phong("" if x[0] == "Chưa ghi phòng" else x[0]))])
    with st.expander("Xem tên khách từng phòng"):
        for p, v in sorted(nhom.items(), key=lambda x: store.thu_tu_phong("" if x[0] == "Chưa ghi phòng" else x[0])):
            st.markdown(f"**🏢 {E(p)}** ({len(v)}): " + (", ".join(E(x["ho_ten"]) for x in sorted(v, key=lambda x: x["ho_ten"])) or "—"))
        if "Chưa ghi phòng" in nhom:
            st.caption("Ghi phòng cho khách ở trang 👤 Khách & tài khoản › ô 🏢 Phòng tập.")
    _ = by


def _inbody_nhac(dang: list[dict], T: dict, B: list[dict], hom: date):
    from core import inbody
    can = sorted([(T[k["ma"]], k) for k in dang if T.get(k["ma"]) and T[k["ma"]]["con"] <= 1], key=lambda x: x[0]["con"])
    if not can:
        return
    ui.sec(f"📏 Cần đo InBody ({len(can)})")
    if st.button("📷 Đo xong cả nhóm? Quét nhiều phiếu InBody một lần", key="ib_quet"):
        S["_dich"] = "quet_inbody"
        st.rerun()
    BD = {k["ma"]: inbody.buoi_do(k, t, B, hom) for t, k in can}
    can.sort(key=lambda x: (BD[x[1]["ma"]] is None, BD[x[1]["ma"]]["ngay"] if BD[x[1]["ma"]] else hom, x[0]["con"]))
    for i, (t, k) in enumerate(can):
        if i == 4:
            st.caption(f"…và {len(can) - 4} khách nữa — bấm “Xem tất cả” bên dưới.")
            if not st.toggle("Xem tất cả khách cần đo", key="ib_all"):
                break
        bd = BD[k["ma"]]
        noi = (f" · đo buổi <b>{store.THU[bd['ngay'].weekday()]} {bd['ngay']:%d/%m} {E(store.gio_s(bd['gio']))}</b>" if bd
               else " · chưa có buổi hẹn")
        c1, c2 = st.columns([4, 1], vertical_alignment="center")
        c1.markdown(f'<div class="hac-b"><span class="n">{E(k["ho_ten"])}</span>'
                    + (f'<span class="hac-chip" style="background:{store.mau_phong(store.phong(k))}">🏢 {E(store.phong(k))}</span>' if store.phong(k) else "")
                    + f'<span class="m">{E(inbody.mo_ta(t))}{noi}</span></div>', unsafe_allow_html=True)
        if c2.button("📏 Nhập số đo", key=f"ib_{k['ma']}", use_container_width=True):
            S["hlv_kh"] = k["ma"]
            S["_dich"] = "tien_do"
            st.rerun()


def lich():
    u = _user()
    DS = store.clients()
    H = store.hens()
    hom = db.now_vn().date()
    by = {k["ma"]: k for k in DS}
    dang = [k for k in DS if (k.get("trang_thai") or "Đang tập") == "Đang tập"]
    tuan0 = hom - timedelta(days=hom.weekday())
    B = store.buoi(DS, hom - timedelta(days=7), tuan0 + timedelta(days=13), H)
    homnay = [b for b in B if b["ngay"] == hom]
    ui.hero(config.BRAND, f"{len(dang)} khách đang tập",
            f"{len([b for b in homnay if b['trang_thai'] != 'huy'])} buổi hôm nay · "
            f"{len([b for b in B if tuan0 <= b['ngay'] <= tuan0 + timedelta(days=6) and b['trang_thai'] != 'huy'])} buổi tuần này")
    _hang_cho(u)
    from core import inbody
    T = {k["ma"]: inbody.trang_thai(k, hom) for k in dang}
    _phong_tong(dang, B, tuan0)
    _inbody_nhac(dang, T, B, hom)
    xem = st.segmented_control("Xem", ["Hôm nay", "Ngày mai", "Tuần này", "Tuần sau", "Chưa đánh dấu"], default="Hôm nay",
                               key="l_xem") or "Hôm nay"
    if xem == "Hôm nay":
        L = homnay
    elif xem == "Ngày mai":
        L = [b for b in B if b["ngay"] == hom + timedelta(days=1)]
    elif xem == "Tuần này":
        L = [b for b in B if tuan0 <= b["ngay"] <= tuan0 + timedelta(days=6)]
    elif xem == "Tuần sau":
        L = [b for b in B if tuan0 + timedelta(days=7) <= b["ngay"] <= tuan0 + timedelta(days=13)]
    else:
        L = [b for b in B if b["ngay"] < hom and b["trang_thai"] == "hen"]
    PH = sorted({store.phong(by.get(b["ma"], {})) or "Chưa ghi phòng" for b in L})
    if len(PH) > 1:
        lp = st.pills("Lọc phòng", PH, selection_mode="multi", key="l_phong")
        if lp:
            L = [b for b in L if (store.phong(by.get(b["ma"], {})) or "Chưa ghi phòng") in lp]
    if not L:
        st.caption("Không có buổi nào.")
    # v3.5: buổi giáo án dự kiến của từng buổi hẹn (tự nối tiếp; HLV đổi được ở nút ↻ Dời / đổi)
    from core import lich_tap as _lt
    KH_PLAN, KH_CK = {}, {}
    for m_ in {b["ma"] for b in L if b["ngay"] >= hom and b["trang_thai"] == "hen"}:
        try:
            ds_ = _lt.sap_toi(by[m_], 21)
            KH_PLAN[m_] = {x.get("id"): x for x in ds_ if x.get("buoi")}
            KH_CK[m_] = _lt.chu_ky(by[m_])
        except Exception:  # noqa: BLE001 — khách chưa có giáo án
            pass
    truoc = None
    for b in L:
        k = by.get(b["ma"], {})
        if b["ngay"] != truoc:
            st.markdown(f'<div class="hac-d">{store.THU[b["ngay"].weekday()].upper()} · {b["ngay"]:%d/%m}'
                        + (" · HÔM NAY" if b["ngay"] == hom else "") + "</div>", unsafe_allow_html=True)
            truoc = b["ngay"]
        mau, nhan = MAU.get(b["trang_thai"], MAU["hen"])
        from core import chu_ky as _ck
        ckx = _ck.dieu_chinh(b["ma"], b["ngay"], k) if k else None
        st.markdown(f'<div class="hac-b"><span class="t">{E(store.gio_s(b["gio"]))}</span><span class="n">{E(k.get("ho_ten", ""))}</span>'
                    f'<span class="hac-chip" style="background:{mau}">{nhan}</span>'
                    + (f'<span class="hac-chip" style="background:#D46A92" title="{E(ckx["hlv"])}">🌸 ngày {ckx["ngay_thu"]}'
                       f'{" (dự đoán)" if ckx["du_doan"] else ""}</span>' if ckx and ckx["nang"] else "")
                    + (f'<span class="hac-chip" style="background:{store.mau_phong(store.phong(k))}">🏢 {E(store.phong(k))}</span>' if k and store.phong(k) else "")
                    + ('<span class="hac-chip" style="background:#2F7D5B">📏 Đo InBody</span>'
                       if T.get(b["ma"]) and b["ngay"] >= hom and T[b["ma"]]["han"] <= b["ngay"] and b["trang_thai"] != "huy" else "")
                    + (f'<span class="hac-chip" style="background:#3E6E9E">🏋️ {E(pl["buoi"])} · {E(pl["ten"])}{" (đã đổi)" if pl.get("doi") else ""}</span>'
                       if (pl := KH_PLAN.get(b["ma"], {}).get(b["id"])) else "")
                    + f'<span class="m">{E(b.get("dia_diem") or "")}' + (f" · {E(store.mo_ta_goi(k, H, hom))}" if k else "")
                    + (" · hẹn thêm" if not b.get("co_dinh") else "") + "</span></div>", unsafe_allow_html=True)
        c1, c2, c3, c4 = st.columns(4)
        if b["trang_thai"] != "xong" and c1.button("✅ Đã tập", key=f"x_{b['id']}", use_container_width=True):
            store.ghi_hen(b["ma"], b["ngay"], b["gio"], "xong", u["name"], b.get("dia_diem", ""), goc=b["id"])
            st.rerun()
        if b["trang_thai"] == "hen" and c2.button("✖ Nghỉ", key=f"h_{b['id']}", use_container_width=True):
            store.ghi_hen(b["ma"], b["ngay"], b["gio"], "huy", u["name"], b.get("dia_diem", ""), goc=b["id"])
            st.rerun()
        if b["trang_thai"] != "hen" and c2.button("↩ Hoàn tác", key=f"u_{b['id']}", use_container_width=True):
            store.ghi_hen(b["ma"], b["ngay"], b["gio"], "hen", u["name"], b.get("dia_diem", ""), goc=b["id"])
            st.rerun()
        with c3.popover("↻ Dời / đổi", use_container_width=True):
            nd = st.date_input("Ngày mới", value=b["ngay"], format="DD/MM/YYYY", key=f"dn_{b['id']}")
            ng = st.text_input("Giờ mới", value=b["gio"], key=f"dg_{b['id']}", placeholder="18:00")
            moi_tuan = b.get("co_dinh") and st.checkbox(
                f"Áp dụng cho mọi tuần sau (đổi lịch cố định {store.THU[b['ngay'].weekday()]} {store.gio_s(b['gio'])})",
                key=f"dt_{b['id']}", help="Từ ngày mới trở đi, buổi này luôn rơi vào thứ / giờ mới. Các tuần đã qua giữ nguyên.")
            if st.button("Dời buổi", key=f"dv_{b['id']}"):
                g2 = _gio_chuan(ng) or ng.strip()
                if moi_tuan and k:
                    k2 = {**k, "lich": json.dumps(store.doi_lich_co_dinh(k, b["ngay"].weekday(), b["gio"], min(nd, b["ngay"]),
                                                                        nd.weekday(), g2), ensure_ascii=False)}
                    store.save_client(k2, u["name"])
                    if nd < b["ngay"]:
                        store.ghi_hen(b["ma"], nd, g2, "hen", u["name"], b.get("dia_diem", ""), f"dời từ {b['ngay']:%d/%m} {b['gio']}")
                else:
                    store.ghi_hen(b["ma"], b["ngay"], b["gio"], "huy", u["name"], b.get("dia_diem", ""), "dời lịch", goc=b["id"])
                    store.ghi_hen(b["ma"], nd, g2, "hen", u["name"], b.get("dia_diem", ""), f"dời từ {b['ngay']:%d/%m} {b['gio']}",
                                  buoi_ga=b.get("buoi_ga", ""))
                S["_soan_doi"] = (b["ma"], nd.isoformat(), g2, b["ngay"].isoformat(), b["gio"])
                st.rerun()
            CK = KH_CK.get(b["ma"]) or []
            if CK and b["trang_thai"] == "hen" and b["ngay"] >= hom:
                st.divider()
                pl = KH_PLAN.get(b["ma"], {}).get(b["id"]) or {}
                hien = next((i for i, x in enumerate(CK) if x.split(" · ")[0] == pl.get("buoi")), 0)
                cb = st.selectbox("🔀 Đổi buổi giáo án hôm đó", CK, index=hien, key=f"cb_{b['id']}",
                                  help="VD hôm nay khách đau chân → tập Pull thay Leg. Các buổi sau tự nối tiếp từ buổi anh chọn.")
                if st.button("Lưu buổi tập", key=f"cbl_{b['id']}"):
                    store.ghi_hen(b["ma"], b["ngay"], b["gio"], "hen", u["name"], b.get("dia_diem", ""), b.get("ghi_chu", ""),
                                  goc=b["id"], buoi_ga=cb.split(" · ")[0])
                    st.rerun()
        with c4.popover("💬 Nhắc", use_container_width=True):
            if k:
                _soan(k, store.tin_nhac(k, b, hom), f"n_{b['id']}", u)
    if S.get("_soan_doi"):
        m_, nd_, ng_, od_, og_ = S["_soan_doi"]
        k = by.get(m_)
        if k:
            st.success("Đã dời buổi — tin báo cho khách:")
            _soan(k, store.tin_hen(k, date.fromisoformat(nd_), ng_, hom, k.get("dia_diem", ""),
                                   {"ngay": date.fromisoformat(od_), "gio": og_}), "doi", u)
        if st.button("Đóng", key="l_dong"):
            S.pop("_soan_doi", None)
            st.rerun()
    if dang:
        st.divider()
        ui.sec("📨 Nhắc lịch tuần này cho cả nhóm")
        for k in dang:
            with st.expander(f"{k['ho_ten']} · Zalo {k.get('ten_zalo') or '—'}"):
                _soan(k, store.tin_tuan(k, [b for b in B if tuan0 <= b["ngay"] <= tuan0 + timedelta(days=6)], hom, H), f"w_{k['ma']}", u)


# =================================================================== KHÁCH & TÀI KHOẢN
def _gio_chuan(g: str) -> str | None:
    g = str(g or "").strip().lower().replace("h", ":").rstrip(":")
    if not g:
        return None
    g = g if ":" in g else f"{g}:00"
    hh, mm = (g.split(":") + ["00"])[:2]
    try:
        return f"{int(hh):02d}:{(mm or '00')[:2].zfill(2)}"
    except ValueError:
        return None


def khach():
    u = _user()
    DS = store.clients()
    H = store.hens()
    hom = db.now_vn().date()
    by = {k["ma"]: k for k in DS}
    ui.hero("KHÁCH & TÀI KHOẢN", f"{len(DS)} khách", "Hồ sơ, lịch cố định, gói buổi — và tài khoản đăng nhập cổng khách.")
    if S.get("_k_pick_next") is not None:              # v2.6: lưu xong vẫn ở lại khách vừa sửa
        nx_ = S.pop("_k_pick_next")
        S["k_pick"] = nx_ if nx_ in by else "__moi__"
    cot = st.selectbox("Chọn khách để sửa", ["__moi__"] + [k["ma"] for k in DS],
                       format_func=lambda m: "➕ Thêm khách mới" if m == "__moi__" else f"{by[m]['ho_ten']} · {by[m].get('trang_thai') or 'Đang tập'}",
                       key="k_pick")
    k0 = {} if cot == "__moi__" else by[cot]
    from views import goi_ui
    goi_ui.canh_bao(DS)
    t1, t4, t3, t5, t2 = st.tabs(["✏️ Thông tin, gói & lịch tập", "💳 Gói · công nợ · bảo lưu", "🪪 Hồ sơ đầy đủ & ảnh đại diện",
                                  "🌸 Chu kỳ (chỉ HLV)", "🔐 Tài khoản cổng khách"])
    with t5:
        if not k0:
            st.info("Lưu khách trước.")
        else:
            from views import chu_ky_ui
            chu_ky_ui.tab(k0, u["name"])
    with t1:
        if k0 and store.lich_co_dinh(k0):
            from views import lich_ga_ui
            lich_ga_ui.bang(k0)
    with t4:
        if not k0:
            st.info("Lưu khách trước (tab Thông tin, gói & lịch tập).")
        else:
            goi_ui.tab(k0, u["name"])
    with t3:
        if not k0:
            st.info("Lưu khách trước (tab Gói & lịch tập), rồi điền hồ sơ đầy đủ.")
        else:
            from views import ho_so_ui
            if ho_so_ui.tom_tat(k0):
                st.caption(ho_so_ui.tom_tat(k0))
            if k0.get("ly_do"):
                st.markdown(f"💡 **Động lực của khách:** {E(k0['ly_do'])}")
            if k0.get("can_mong_muon") and str(k0.get("can_mong_muon")) != str(k0.get("can_muc_tieu")):
                st.caption(f"Khách mong muốn {float(k0['can_mong_muon']):g} kg — cân mục tiêu anh đặt: "
                           + (f"{float(k0['can_muc_tieu']):g} kg" if k0.get("can_muc_tieu") else "chưa đặt"))
            ho_so_ui.form(k0, u["name"], "hlv")
    with t1:
        lich0 = store.lich_co_dinh(k0)
        with st.form(f"kf_{cot}"):
            a, b, c = st.columns([2, 1.2, 1])
            ten = a.text_input("Họ tên *", value=k0.get("ho_ten", ""))
            sdt = b.text_input("SĐT (mở Zalo)", value=str(k0.get("sdt", "")))
            ht = c.selectbox("Hình thức", store.HINH_THUC, index=store.HINH_THUC.index(k0["hinh_thuc"]) if k0.get("hinh_thuc") in store.HINH_THUC else 0)
            a, b, c = st.columns(3)
            tz = a.text_input("Tên Zalo", value=k0.get("ten_zalo", ""), help="Tên hiện trong Zalo — Claude tìm theo tên này khi gửi")
            gk = b.text_input("Gọi khách là", value=k0.get("goi_khach", ""), placeholder="VD chị Lan, anh Tuấn, em Vy")
            xt = c.text_input("Tự xưng", value=k0.get("xung_toi", ""), placeholder="em / anh / mình")
            GOI = store.goi_list()
            ten_goi = ["— Tự nhập —"] + [g["ten"] for g in GOI]
            a, b, c, d = st.columns([1.6, 1, 0.8, 1.2])
            g_chon = a.selectbox("Gói", ten_goi, index=ten_goi.index(k0.get("goi_ten")) if k0.get("goi_ten") in ten_goi else 0,
                                 help="Chọn gói có sẵn (sửa bảng gói ở cuối trang) — loại, thời lượng, giá tự điền khi lưu")
            lo0 = store.loai_goi(k0)
            g_lo = b.selectbox("Tính theo", list(store.LOAI_GOI), index=list(store.LOAI_GOI).index(lo0), format_func=store.LOAI_GOI.get)
            so0 = int(float((k0.get("goi_so") if lo0 != "buoi" else k0.get("goi_buoi")) or 0))
            g_so = c.number_input("Số", 0, 300, so0, help="Số buổi / tuần / tháng của gói")
            gia = d.text_input("Giá gói", value=str(k0.get("gia", "")), placeholder="VD 6.000.000")
            a, b, c = st.columns(3)
            truoc = a.number_input("Đã tập trước đó (buổi)", 0, 300, int(float(k0.get("da_tap_truoc") or 0)))
            try:
                bd0 = date.fromisoformat(str(k0.get("ngay_bat_dau"))[:10])
            except ValueError:
                bd0 = hom
            bd = b.date_input("Bắt đầu gói", value=bd0, format="DD/MM/YYYY")
            if k0 and goi.ngay_ket_thuc(k0):
                c.markdown(f"<div style='padding-top:30px;color:#7A5B14;font-weight:700'>Kết thúc {goi.ngay_ket_thuc(k0):%d/%m/%Y}</div>",
                           unsafe_allow_html=True)
            try:
                ns0 = date.fromisoformat(str(k0.get("ngay_sinh"))[:10])
            except ValueError:
                ns0 = None
            a, p_, b, c = st.columns([1, 1.2, 1.4, 1])
            ns = a.date_input("Ngày sinh", value=ns0, format="DD/MM/YYYY", min_value=date(1940, 1, 1), max_value=hom)
            P_ = store.ds_phong(DS)
            pt0 = str(k0.get("phong_tap") or "")
            pt_ = p_.selectbox("🏢 Phòng tập", ["— chưa chọn —"] + P_ + ["➕ Phòng khác…"],
                               index=(P_.index(pt0) + 1) if pt0 in P_ else 0,
                               help="Khách đang tập ở phòng nào — hiện ở danh sách khách, lịch, thanh bên. Chọn ➕ rồi ghi tên ở ô bên cạnh.")
            dd_ = b.text_input("Nơi tập / tên phòng khác", value=k0.get("dia_diem", ""), placeholder="VD chi nhánh, nhà khách, online Zalo")
            tt = c.selectbox("Trạng thái", store.TRANG_THAI, index=store.TRANG_THAI.index(k0.get("trang_thai") or "Đang tập")
                             if (k0.get("trang_thai") or "Đang tập") in store.TRANG_THAI else 0)
            from core import inbody as _ib
            _ky0 = _ib.ky(k0) if k0 else 7
            _kys = list(_ib.KY)
            ib_ = st.columns([1, 2])[0].selectbox("📏 Nhắc đo InBody", _kys, index=_kys.index(_ky0) if _ky0 in _kys else 0, format_func=lambda x: _ib.KY[x],
                               help="Web tự nhắc ở trang Lịch (và tin Telegram buổi sáng) khi tới hạn — đo ngay buổi tập gần nhất.")
            st.markdown("**📅 Lịch tập cố định** — tick ngày tập, ghi giờ. Đây là nguồn chung cho số buổi / tuần, ngày tập của thực đơn, "
                        "giáo án (buổi xếp theo thứ tự giáo án: Push → Pull → Leg → Push 2…), nhắc lịch.")
            L0 = {int(x["thu"]): x for x in lich0}
            gio_md = st.text_input("Giờ mặc định (dùng cho ngày tick mà để trống giờ)", value=next((x.get("gio", "") for x in lich0), ""),
                                   placeholder="VD 18:30")
            lich_in = []
            hang = st.columns(7)
            for i_ in range(7):
                with hang[i_]:
                    on_ = st.checkbox(store.THU[i_], value=i_ in L0, key=f"lt_on_{k0.get('ma', 'moi')}_{i_}")
                    g_ = st.text_input("Giờ", value=L0.get(i_, {}).get("gio", ""), key=f"lt_g_{k0.get('ma', 'moi')}_{i_}",
                                       placeholder="giờ", label_visibility="collapsed")
                    n_ = st.text_input("Nơi", value=L0.get(i_, {}).get("dia_diem", ""), key=f"lt_n_{k0.get('ma', 'moi')}_{i_}",
                                       placeholder="nơi (nếu khác)", label_visibility="collapsed")
                lich_in.append((on_, g_, n_))
            st.markdown("**Hồ sơ đầu khoá** — dùng cho báo cáo, thực đơn (BMI, mức mỡ, năng lượng)")
            a, b, c, d = st.columns(4)
            gt_l = ["", "Nam", "Nữ"]
            gt = a.selectbox("Giới tính", gt_l, index=gt_l.index(k0.get("gioi_tinh")) if k0.get("gioi_tinh") in gt_l else 0)
            cc = b.number_input("Chiều cao (cm)", 0.0, 230.0, float(k0.get("chieu_cao") or 0), step=0.5)
            cmt = c.number_input("Cân mục tiêu (kg)", 0.0, 250.0, float(k0.get("can_muc_tieu") or 0), step=0.5)
            mt_ = d.text_input("Mô tả mục tiêu", value=k0.get("muc_tieu", ""), placeholder="VD giảm mỡ bụng, gọn eo")
            from core import thong_tin as ttin, ga_atlas as _ga
            a, b = st.columns(2)
            ml_ = a.selectbox("Mục tiêu chính (dùng chung cho giáo án, dinh dưỡng, lộ trình)", list(ttin.TEN),
                              index=list(ttin.TEN).index(ttin.muc_tieu(k0)) if k0 else 0, format_func=ttin.TEN.get)
            td_ = b.selectbox("Trình độ tập (dùng chung cho giáo án, volume)", list(range(5)), index=ttin.trinh_do(k0) if k0 else 0,
                              format_func=lambda i: _ga.LEVELS[i])
            gd_ = st.radio("Giao diện cổng khách", list(store.GIAO_DIEN), horizontal=True, format_func=store.GIAO_DIEN.get,
                           index=0 if store.co_ban(k0) else 1, help="Cơ bản: chữ to, ít mục — hợp khách lớn tuổi. Khách tự đổi được trong menu.")
            ct = st.text_input("Chấn thương / bệnh nền cần lưu ý", value=k0.get("chan_thuong", ""))
            gc = st.text_area("Ghi chú (chỉ HLV thấy)", value=k0.get("ghi_chu", ""), height=70)
            a, b = st.columns([3, 1])
            luu = a.form_submit_button("💾 Lưu khách", type="primary", use_container_width=True)
            xoa = b.form_submit_button("🗑 Xoá", use_container_width=True, disabled=not k0)
        if luu or xoa:
            if not ten.strip():
                st.error("Nhập họ tên.")
            else:
                sl = []
                for i_, (on_, g_, n_) in enumerate(lich_in):
                    g = _gio_chuan(g_) or _gio_chuan(gio_md)
                    if on_ and g:
                        sl.append({"thu": i_, "gio": g, **({"dia_diem": n_.strip()} if str(n_ or "").strip() else {})})
                    elif on_:
                        st.warning(f"{store.THU[i_]}: chưa có giờ — ghi giờ hoặc giờ mặc định.")
                gc_ = next((g for g in GOI if g["ten"] == g_chon), None)
                if gc_:
                    g_lo, g_so = gc_.get("loai", "buoi"), int(gc_.get("so") or 0)
                    gia = gia.strip() or f"{int(gc_.get('gia') or 0):,}".replace(",", ".")
                k1 = {**k0, "goi_ten": g_chon if gc_ else "", "goi_loai": g_lo, "goi_so": g_so if g_lo != "buoi" else "",
                      "gioi_tinh": gt, "chieu_cao": cc or "", "can_muc_tieu": cmt or "", "muc_tieu": mt_.strip(), "muc_tieu_loai": ml_, "trinh_do": td_, "giao_dien": gd_,
                      "ma": k0.get("ma") or store.ma_moi(DS), "ho_ten": ten.strip(), "sdt": sdt.strip(), "ten_zalo": tz.strip(),
                      "goi_khach": gk.strip(), "xung_toi": xt.strip(), "dia_diem": dd_.strip(), "inbody_ky": ib_, "phong_tap": (dd_.strip() if pt_.startswith("➕") else ("" if pt_.startswith("—") else pt_)), "goi_buoi": g_so if g_lo == "buoi" else "", "da_tap_truoc": truoc,
                      "gia": gia.strip(), "ngay_bat_dau": bd.isoformat(), "lich": sl, "trang_thai": tt, "ghi_chu": gc.strip(),
                      "ngay_sinh": ns.isoformat() if ns else "", "hinh_thuc": ht, "chan_thuong": ct.strip(), "xoa": bool(xoa)}
                if store.save_client(k1, u["name"]):
                    if xoa:
                        acc = auth.account_of(k1["ma"])
                        if acc:
                            auth.save_account(k1["ma"], acc["_khoa"], None, u["name"], khoa=True, cu=acc)
                    st.toast("Đã xoá" if xoa else "Đã lưu")
                    S["_k_pick_next"] = "__moi__" if xoa else k1["ma"]
                    st.rerun()
                st.error("Chưa lưu được — kiểm tra kết nối rồi thử lại.")
    with t2:
        if not k0:
            st.info("Lưu hồ sơ khách trước, rồi cấp tài khoản.")
        else:
            acc = auth.account_of(k0["ma"])
            link = str(config.get("APP_URL", "") or "https://<link-web-cua-anh>.streamlit.app")
            if acc:
                st.markdown(f"Tên đăng nhập: **{acc['_khoa']}** · trạng thái: "
                            + ("🔒 **đang khoá**" if acc.get("khoa") else "✅ **đang hoạt động**"))
            else:
                st.caption("Khách này chưa có tài khoản.")
            goi_y = acc["_khoa"] if acc else auth.norm_user(k0["ho_ten"].split()[-1] + k0["ma"][1:])
            with st.form(f"tk_{k0['ma']}"):
                a, b = st.columns(2)
                un = a.text_input("Tên đăng nhập", value=goi_y, help="Chữ không dấu, số, dấu . _ -")
                pw = b.text_input("Mật khẩu mới", value="" if acc else auth.tao_mat_khau(),
                                  help="Để trống = giữ mật khẩu cũ" if acc else "Web tạo sẵn — sửa được")
                khoa = st.checkbox("Khoá tài khoản (khách không đăng nhập được)", value=bool(acc and acc.get("khoa")))
                if st.form_submit_button("💾 Lưu tài khoản" if acc else "🔐 Cấp tài khoản", type="primary", use_container_width=True):
                    ok, loi = auth.save_account(k0["ma"], un, pw.strip() or None, u["name"], khoa, acc)
                    if ok:
                        S[f"tk_moi_{k0['ma']}"] = (auth.norm_user(un), pw.strip() or None)
                        st.rerun()
                    st.error(loi)
            if S.get(f"tk_moi_{k0['ma']}"):
                un_, pw_ = S[f"tk_moi_{k0['ma']}"]
                st.success("Đã lưu. Tin gửi khách (mật khẩu chỉ hiện lần này — web không lưu mật khẩu gốc):")
                _soan(k0, store.tin_tai_khoan(k0, link, un_, pw_), f"tk_{k0['ma']}", u)
            if not config.get("APP_URL"):
                st.caption("💡 Thêm `APP_URL` (link web) vào Secrets để tin nhắn tự điền đúng link.")
    if DS:
        ui.sec("Danh sách")
        TK = {v.get("ma_kh"): v for v in auth.accounts().values()}
        PH = sorted({store.phong(k) or "Chưa ghi phòng" for k in DS})
        loc = st.pills("Lọc theo phòng tập", PH, selection_mode="multi", key="ds_loc_phong") if len(PH) > 1 else []
        DSL = [k for k in DS if not loc or (store.phong(k) or "Chưa ghi phòng") in loc]
        st.dataframe(pd.DataFrame([{"Khách": k["ho_ten"], "🏢 Phòng": store.phong(k) or "—", "Hình thức": k.get("hinh_thuc") or "Trực tiếp",
                                    "Lịch": ", ".join(f"{store.THU[int(x['thu'])]} {store.gio_s(x['gio'])}" for x in store.lich_co_dinh(k)),
                                    "Đã tập": store.da_tap(k, H), "Gói": store.mo_ta_goi(k, H, hom),
                                    "Bắt đầu": f"{goi.ngay_bat_dau(k):%d/%m/%Y}" if goi.ngay_bat_dau(k) else "",
                                    "Kết thúc": f"{goi.ngay_ket_thuc(k):%d/%m/%Y}" if goi.ngay_ket_thuc(k) else "",
                                    "Còn nợ": goi.vnd(goi.cong_no(k)["con_no"]) if goi.cong_no(k)["con_no"] else "—",
                                    "Tình trạng gói": goi.trang_thai(k, hom, H)["ten"],
                                    "Tài khoản": ("🔒 " if TK[k["ma"]].get("khoa") else "✅ ") + TK[k["ma"]]["_khoa"] if k["ma"] in TK else "—",
                                    "Trạng thái": k.get("trang_thai") or "Đang tập"} for k in DSL]), hide_index=True, use_container_width=True)
    _bang_goi(u)


def _bang_goi(u: dict):
    with st.expander("📦 Bảng gói của anh (Online 12 tuần, 1 tháng, gói buổi…)"):
        st.caption("Lưu trong Google Sheet riêng của anh, không nằm trong code công khai. Chọn gói ở hồ sơ khách là tự điền loại, thời lượng, giá.")
        df = pd.DataFrame([{"Tên gói": g["ten"], "Tính theo": store.LOAI_GOI.get(g.get("loai"), "buổi"), "Số": int(g.get("so") or 0),
                            "Giá (đ)": int(g.get("gia") or 0)} for g in store.goi_list()] or [{"Tên gói": "", "Tính theo": "tuần", "Số": 0, "Giá (đ)": 0}])
        ed = st.data_editor(df, num_rows="dynamic", hide_index=True, use_container_width=True, key="bang_goi",
                            column_config={"Tính theo": st.column_config.SelectboxColumn(options=list(store.LOAI_GOI.values())),
                                           "Giá (đ)": st.column_config.NumberColumn(format="%d", step=50000)})
        if st.button("💾 Lưu bảng gói"):
            nguoc = {v: k_ for k_, v in store.LOAI_GOI.items()}
            ds = [{"ten": str(r["Tên gói"]).strip(), "loai": nguoc.get(r["Tính theo"], "buoi"), "so": int(r["Số"] or 0),
                   "gia": int(r["Giá (đ)"] or 0)} for r in ed.to_dict("records") if str(r.get("Tên gói") or "").strip()]
            if store.save_goi_list(ds, u["name"]):
                st.toast("Đã lưu bảng gói")
                st.rerun()


# =================================================================== GIÁO ÁN, DINH DƯỠNG
def tap():
    u = _user()
    ui.hero("GIÁO ÁN KHÁCH", "Giáo án tuần tự xếp theo mục tiêu — phương pháp Hoàng Anh Coaching",
            "Mục tiêu · trình độ · số buổi · dạng lịch · vùng chấn thương → 8 bài / buổi, Compound → Multi → Isolate → Core, superset, kết buổi. "
            "Khách thấy giáo án (liều tự tính theo tuần) trên cổng khách khi anh bấm Lưu.")
    k = _chon_khach(store.clients())
    if k:
        from views import coach_ga
        coach_ga.trang(u, k)


def tong_ket():
    u = _user()
    ui.hero("TỔNG KẾT NGÀY", "Hôm nay khách đã làm gì?", "Tập · cardio · bước chân · cân · check-in · ăn uống · nhiệm vụ — tất cả trong 1 chỗ.")
    from views import tong_ket_ui
    DS = store.clients(ca_ngung=False)
    d = st.date_input("Ngày xem tất cả khách", db.now_vn().date(), max_value=db.now_vn().date(), format="DD/MM/YYYY", key="tk_all_d")
    with st.expander("📋 Tất cả khách trong ngày", expanded=True):
        tong_ket_ui.bang_tat_ca(DS, d)
    k = _chon_khach(DS)
    if k:
        tong_ket_ui.trang(k, "hlv", u["name"])


def cham_soc():
    u = _user()
    ui.hero("CHĂM SÓC KHÁCH", "Những điều nhỏ khiến khách nhớ mãi",
            "Tin tổng kết tuần · mốc thành tích & thư khen · thư tổng kết khoá · nhắc qua Telegram.")
    from views import cham_soc_ui
    DS = store.clients(ca_ngung=False)
    with st.expander("📋 Tổng quan tất cả khách", expanded=True):
        cham_soc_ui.tong_quan(DS)
    k = _chon_khach(DS)
    if k:
        cham_soc_ui.trang(k, u)


def volume():
    u = _user()
    ui.hero("VOLUME & BẢN ĐỒ CƠ", "Tuần này khách tập đủ volume chưa?",
            "Số hiệp nặng mỗi nhóm cơ trong tuần, tô màu trên cơ thể, đánh giá theo mục tiêu hình thể + trình độ.")
    k = _chon_khach(store.clients())
    if k:
        from views import volume_ui
        volume_ui.trang(k, "hlv", u["name"])


def an():
    u = _user()
    ui.hero("DINH DƯỠNG", "Năng lượng · macro · thực đơn 7 ngày", "Khách xem được thực đơn này ở cổng khách (không thấy phần thông số).")
    k = _chon_khach(store.clients())
    if k:
        C.dinh_duong(k, "hlv", u["name"])


def ho_so():
    from views import thanh_qua_ui
    thanh_qua_ui.trang_hlv(_user()["name"])


def cam_ket():
    ui.hero("CAM KẾT KHÁCH", "Ai đang chăm, ai đang chững?", "Chuỗi lửa, điểm chăm chỉ tuần, việc hôm nay còn thiếu — xếp khách cần nhắc lên đầu.")
    from views import dong_luc_ui as DL
    DS = store.clients(ca_ngung=False)
    if not DS:
        st.info("Chưa có khách đang tập.")
        return
    DL.bang_hlv(DS)
    st.caption("Điểm tuần = trung bình % nhiệm vụ đã làm mỗi ngày. Có sẵn tin nhắc cho khách dưới 80 điểm — bấm biểu tượng sao chép để dán Zalo.")


def cardio():
    u = _user()
    ui.hero("CARDIO", "Target & kết quả cardio", "Đặt target ngày tập / ngày nghỉ, nhập kết quả từ ảnh khách gửi, theo dõi hoàn thành tuần.")
    k = _chon_khach(store.clients(ca_ngung=False), "cd")
    if k:
        from views import cardio_ui
        cardio_ui.trang(k, "hlv", u["name"])


def thuc_pham():
    u = _user()
    ui.hero("BẢNG THỰC PHẨM", "Giá trị dinh dưỡng / 100 g", "Sửa số theo nhãn sản phẩm khách thật sự dùng (VD whey, sữa chua).")
    F = dd.foods()
    ui.note(E(config.load_json("thuc_pham.json")["_ghi_chu"]))
    df = pd.DataFrame([{"id": k, "Món": v["ten"], "Nhóm": v["nhom"], "kcal": v["kcal"], "Đạm": v["p"], "Tinh bột": v["c"], "Béo": v["f"],
                        "Xơ": v.get("xo", 0)} for k, v in F.items()])
    ed = st.data_editor(df, hide_index=True, use_container_width=True, disabled=["id", "Nhóm"], key="tp_ed",
                        column_config={c: st.column_config.NumberColumn(format="%.1f") for c in ("kcal", "Đạm", "Tinh bột", "Béo", "Xơ")})
    if st.button("💾 Lưu thay đổi", type="primary"):
        n = 0
        for r in ed.to_dict("records"):
            cu = F[r["id"]]
            moi = {**cu, "ten": r["Món"], "kcal": float(r["kcal"]), "p": float(r["Đạm"]), "c": float(r["Tinh bột"]), "f": float(r["Béo"]),
                   "xo": float(r["Xơ"])}
            if any(moi[x] != cu.get(x) for x in ("ten", "kcal", "p", "c", "f", "xo")):
                db.append("DinhDuong", f"mon|{r['id']}", moi, u["name"])
                n += 1
        st.toast(f"Đã lưu {n} món")
        st.rerun()


# =================================================================== TIẾN ĐỘ & BÁO CÁO
def tien_do():
    u = _user()
    ui.hero("TIẾN ĐỘ & BÁO CÁO", "Cân · số đo · ảnh · báo cáo PDF", "")
    k = _chon_khach(store.clients())
    if not k:
        return
    ma = k["ma"]
    SD, CAN, ANH = td.so_do(ma), td.can_ngay(ma), td.anh(ma)
    DAU, MOI = td.dau_khoa(SD, CAN), td.moi_nhat(SD, CAN)
    hom = db.now_vn().date()
    if not k.get("chieu_cao") or not k.get("gioi_tinh"):
        st.caption("💡 Nhập **giới tính, chiều cao, cân mục tiêu** ở trang Khách để báo cáo có BMI, mức mỡ và % tiến độ.")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Cân đầu khoá", f"{DAU['can_nang']:g} kg" if DAU and DAU.get("can_nang") else "—")
    _ch = round(MOI["can_nang"] - DAU["can_nang"], 1) if DAU and MOI and DAU.get("can_nang") and MOI.get("can_nang") else None
    c2.metric("Cân hiện tại", f"{MOI['can_nang']:g} kg" if MOI and MOI.get("can_nang") else "—", f"{_ch:+g} kg" if _ch else None,
              delta_color="inverse")
    _pt = td.tien_do_can(DAU.get("can_nang") if DAU else None, MOI.get("can_nang") if MOI else None, k.get("can_muc_tieu"))
    c3.metric("Tới mục tiêu", f"{_pt}%" if _pt is not None else "—", f"mục tiêu {k['can_muc_tieu']} kg" if k.get("can_muc_tieu") else None,
              delta_color="off")
    c4.metric("Lần đo · lần cân", f"{len(SD)} · {len(CAN)}")
    s0, s1, s2, s3, s4 = st.tabs(["🧬 Chỉ số cơ thể", "⚖️ Cân hằng ngày", "📏 Số đo", "📸 Ảnh", "📄 Báo cáo"])
    with s0:
        from views import chi_so_ui
        chi_so_ui.hien(k, "hlv")
    with s1:
        C.nhap_can(k, u["name"], CAN, "hlv")
        C.bieu_do_can(k, CAN, 340)
        the_danh_gia(k, CAN, hom)
        if len(CAN):
            with st.expander(f"Bảng cân · {len(CAN)} lần"):
                st.dataframe(CAN.sort_values("ngay", ascending=False).rename(columns={"ngay": "Ngày", "kg": "Cân (kg)", "tb7": "TB 7 ngày"}),
                             hide_index=True, use_container_width=True,
                             column_config={"Ngày": st.column_config.DateColumn(format="DD/MM/YYYY")})
                xn = st.selectbox("Xoá lần cân nhập nhầm", [None] + list(CAN["ngay"]), format_func=lambda d: "—" if d is None else f"{d:%d/%m/%Y}",
                                  key=f"xc_{ma}")
                if xn and st.button("🗑 Xoá lần cân này", key=f"xcb_{ma}"):
                    td.xoa_can(ma, xn, u)
                    st.rerun()
    with s2:
        _quet_inbody(k, u)
        IB = S.get(f"ib_{ma}") or {}
        with st.form(f"sd_{ma}_{S.get(f'ibv_{ma}', 0)}", clear_on_submit=True):
            a, b = st.columns(2)
            nd = a.date_input("Ngày đo", hom, format="DD/MM/YYYY", max_value=hom)
            dot = b.selectbox("Đợt", list(td.DOT), format_func=td.DOT.get, index=0 if SD.empty else 1)
            st.caption("Để trống ô nào không đo. InBody: cân, % mỡ, khối cơ, khối mỡ, mỡ nội tạng · thước dây: các vòng.")
            vals, cs = {}, st.columns(4)
            for i, (ck, ten, dv, _) in enumerate(td.CHI_SO):
                vals[ck] = cs[i % 4].number_input(f"{ten}{f' ({dv})' if dv else ''}", 0.0, 400.0, float(IB.get(ck) or 0.0), step=0.1,
                                                  format="%.1f", key=f"v_{ck}_{ma}_{S.get(f'ibv_{ma}', 0)}")
            gcs = st.text_input("Ghi chú", placeholder="VD đo buổi sáng, sau kỳ nghỉ lễ…")
            if st.form_submit_button("💾 Lưu số đo", type="primary", use_container_width=True):
                if not any(v > 0 for v in vals.values()):
                    st.error("Nhập ít nhất 1 chỉ số.")
                elif td.luu_so_do(ma, nd, dot, vals, (gcs + (" · " if gcs and IB else "") + ("đọc từ phiếu InBody" if IB else "")).strip(), u):
                    if vals.get("can_nang"):
                        td.luu_can(ma, nd, vals["can_nang"], u)
                    S.pop(f"ib_{ma}", None)
                    st.toast("Đã lưu số đo")
                    st.rerun()
                else:
                    st.error("Chưa lưu được — thử lại.")
        if len(SD):
            bang = SD.copy()
            bang["dot"] = bang["dot"].map(lambda x: td.DOT.get(x, x))
            st.dataframe(bang.rename(columns={"ngay": "Ngày", "dot": "Đợt", "ghi_chu": "Ghi chú",
                                              **{c_: f"{t_}{f' ({d_})' if d_ else ''}" for c_, t_, d_, _ in td.CHI_SO}}).dropna(axis=1, how="all"),
                         hide_index=True, use_container_width=True, column_config={"Ngày": st.column_config.DateColumn(format="DD/MM/YYYY")})
            co = [(c_, t_) for c_, t_, d_, _ in td.CHI_SO if c_ != "can_nang" and SD[c_].notna().sum() >= 1]
            if co:
                chon = st.multiselect("Biểu đồ chỉ số", [c_ for c_, _ in co],
                                      default=[c_ for c_, _ in co if c_ in ("v_eo", "v_bung", "v_hong", "pbf")][:3] or [co[0][0]],
                                      format_func=lambda c_: td.TEN[c_][0], key=f"ch_{ma}")
                if chon:
                    fig = go.Figure()
                    for i, c_ in enumerate(chon):
                        g = SD.dropna(subset=[c_])
                        fig.add_scatter(x=g["ngay"], y=g[c_], mode="lines+markers+text", name=td.TEN[c_][0], text=[f"{v:g}" for v in g[c_]],
                                        textposition="top center", line=dict(color=ui.PAL[i % len(ui.PAL)], width=3), marker=dict(size=8))
                    fig.update_xaxes(tickformat="%d/%m")
                    st.plotly_chart(ui.layout(fig, 340), use_container_width=True, config={"displayModeBar": False})
            with st.expander("Xoá 1 lần đo nhập nhầm"):
                lab = {i: f"{r['ngay']:%d/%m/%Y} · {td.DOT.get(r['dot'], r['dot'])}" for i, r in SD.iterrows()}
                xi = st.selectbox("Lần đo", list(lab), format_func=lab.get, key=f"xs_{ma}")
                if st.button("🗑 Xoá lần đo này", key=f"xsb_{ma}"):
                    td.xoa_so_do(ma, SD.loc[xi, "ngay"], SD.loc[xi, "dot"], u)
                    st.rerun()
        else:
            st.info("Chưa có lần đo nào — đợt đầu tiên chọn **Đầu khoá**.")
    with s3:
        with st.form(f"anh_{ma}", clear_on_submit=True):
            a, b = st.columns(2)
            na = a.date_input("Ngày chụp", hom, format="DD/MM/YYYY", max_value=hom)
            dota = b.selectbox("Đợt", list(td.DOT), format_func=td.DOT.get, index=0 if not ANH else 1, key=f"dota_{ma}")
            cs = st.columns(3)
            ups = {g: cs[i].file_uploader(f"Ảnh {ten.lower()}", type=["jpg", "jpeg", "png", "webp"], key=f"up_{g}_{ma}")
                   for i, (g, ten) in enumerate(td.GOC.items())}
            st.caption("Chụp cùng chỗ, cùng ánh sáng, cùng trang phục, đứng thẳng cách máy 2–3 m — so trước / sau mới rõ.")
            if st.form_submit_button("💾 Lưu ảnh", type="primary", use_container_width=True):
                files = {g: _anh.shrink(f.getvalue(), 1600) for g, f in ups.items() if f is not None}
                if not files:
                    st.error("Chọn ít nhất 1 ảnh.")
                else:
                    with st.spinner(f"Đang lưu {len(files)} ảnh lên Google Drive…"):
                        up = db.upload_images(files, f"HAC_{ma}_")
                    if not up:
                        st.error("Chưa lưu được ảnh — kiểm tra quyền Google Drive của Apps Script (chạy hàm capQuyenAnh).")
                    else:
                        for g, i_ in up.items():
                            td.luu_anh(ma, na, dota, g, i_, u)
                        st.toast(f"Đã lưu {len(up)} ảnh")
                        st.rerun()
        if ANH:
            IMG = db.get_images([v["id"] for v in ANH])
            dot_ngay = sorted({(str(v["ngay"]), v.get("dot", "")) for v in ANH})
            for ngay_, d_ in dot_ngay:
                st.caption(f"{pd.Timestamp(ngay_):%d/%m/%Y} · {td.DOT.get(d_, d_)}")
                cs = st.columns(3)
                for i, g in enumerate(td.GOC):
                    v = next((x for x in ANH if str(x["ngay"]) == ngay_ and x.get("goc") == g), None)
                    if v and v["id"] in IMG:
                        cs[i].image(IMG[v["id"]], caption=td.GOC[g], use_container_width=True)
        else:
            st.info("Chưa có ảnh — đợt đầu tiên chọn **Đầu khoá**, chụp đủ 3 góc trước · nghiêng · sau.")
    with s4:
        if not DAU:
            st.info("Cần ít nhất 1 lần đo (đợt **Đầu khoá**) ở tab 📏 Số đo để làm báo cáo.")
            return
        kieu = st.segmented_control("Loại báo cáo", ["dau_khoa", "tien_do"], default="dau_khoa", key=f"kieu_{ma}",
                                    format_func={"dau_khoa": "🏁 Kết quả đầu khoá", "tien_do": "📈 Tiến độ (đầu khoá → hiện tại)"}.get) or "dau_khoa"
        co_moi = MOI and (MOI.get("_ngay_can") or MOI.get("ngay")) and (MOI.get("_ngay_can") or MOI["ngay"]) > DAU["ngay"]
        if kieu == "tien_do" and not co_moi:
            st.info("Chưa có lần đo / lần cân nào sau đầu khoá để so sánh.")
            return
        if kieu == "tien_do":
            ss = td.so_sanh(DAU, MOI)
            if ss:
                st.dataframe(pd.DataFrame([{"Chỉ số": x["ten"], "Đầu khoá": f"{x['dau']:g} {x['dv']}", "Hiện tại": f"{x['moi']:g} {x['dv']}",
                                            "Thay đổi": f"{'✅' if x['tot'] else '⚠️' if x['tot'] is False else '➖'} {x['chenh']:+g} {x['dv']}"}
                                           for x in ss]), hide_index=True, use_container_width=True)
            txt_ = td.tin_tien_do(k, DAU, MOI, CAN)
        else:
            for s_ in td.nhan_xet_dau_khoa(k, DAU):
                st.markdown(f"- {s_}")
            txt_ = td.tin_dau_khoa(k, DAU)
        st.markdown("**Tin nhắn Zalo**")
        _soan(k, txt_, f"td_{kieu}_{ma}", u)
        if st.button("📄 Tạo PDF báo cáo", key=f"pdf_{kieu}_{ma}", use_container_width=True):
            with st.spinner("Đang dựng PDF…"):
                IMG2 = db.get_images([v["id"] for v in ANH]) if ANH else {}
                S[f"_pdf_{kieu}_{ma}"] = td.pdf(k, kieu, SD, CAN, IMG2, td.bo_anh(ANH, True), td.bo_anh(ANH, False))
        if S.get(f"_pdf_{kieu}_{ma}"):
            st.download_button("⬇️ Lưu file PDF", S[f"_pdf_{kieu}_{ma}"],
                               f"{hom:%Y-%m-%d}_{'Ket_qua_dau_khoa' if kieu == 'dau_khoa' else 'Tien_do'}_{k['ho_ten'].replace(' ', '_')}.pdf",
                               "application/pdf", type="primary", key=f"dl_{kieu}_{ma}")


# =================================================================== LỘ TRÌNH & MỤC TIÊU (chỉ HLV)
def lo_trinh():
    u = _user()
    from core import lo_trinh as lt, muc_tieu as mt, tu_van as tv
    ui.hero("LỘ TRÌNH & TỐC ĐỘ", "Khách đang đi nhanh hay chậm so với mục tiêu?",
            "🔒 Chỉ HLV thấy trang này — khách không xem được.")
    k = _chon_khach(store.clients())
    if not k:
        return
    ma = k["ma"]
    hom = db.now_vn().date()
    lo0 = mt.loai({**k, "muc_tieu_loai": k.get("muc_tieu_loai")})
    with st.expander("🎯 Đặt mục tiêu đo được (để trống ô nào → web tự đặt mức an toàn 12 tuần)", expanded=not k.get("muc_tieu_loai")):
        with st.form(f"mt_{ma}"):
            a, b, c = st.columns([1.4, 1, 1])
            lo = a.selectbox("Loại mục tiêu", list(mt.THEO_LOAI), index=list(mt.THEO_LOAI).index(lo0), format_func=tv.GOALS.get)
            try:
                han0 = date.fromisoformat(str(k.get("muc_tieu_ngay"))[:10])
            except ValueError:
                han0 = None
            han = b.date_input("Hạn đạt mục tiêu", value=han0, format="DD/MM/YYYY")
            c.caption("Hạn trống = 12 tuần từ lần đo đầu.")
            a, b, c, d = st.columns(4)
            f_ = lambda v: float(v) if str(v or "").strip() not in ("", "None") else 0.0   # noqa: E731
            cmt = a.number_input("Cân đích (kg)", 0.0, 250.0, f_(k.get("can_muc_tieu")), step=0.5)
            mo = b.number_input("% mỡ đích", 0.0, 60.0, f_(k.get("muc_tieu_mo")), step=0.5)
            co = c.number_input("Khối cơ SMM đích (kg)", 0.0, 80.0, f_(k.get("muc_tieu_co")), step=0.1)
            eo = d.number_input("Vòng eo đích (cm)", 0.0, 200.0, f_(k.get("muc_tieu_eo")), step=0.5)
            if st.form_submit_button("💾 Lưu mục tiêu", type="primary"):
                k1 = {**k, "muc_tieu_loai": lo, "muc_tieu_ngay": han.isoformat() if han else "", "can_muc_tieu": cmt or "",
                      "muc_tieu_mo": mo or "", "muc_tieu_co": co or "", "muc_tieu_eo": eo or ""}
                if store.save_client(k1, u["name"]):
                    st.toast("Đã lưu mục tiêu")
                    st.rerun()
    tdo = lt.tien_do(k, hom)
    cc = lt.chuyen_can(k, hom)
    toc = lt.toc_do_can(ma)
    if not tdo:
        st.info("Cần ít nhất 1 lần đo (cân / InBody / vòng eo) — nhập ở trang **📈 Tiến độ từng khách**.")
    else:
        mau = "#1E7B4A" if tdo["tong"] >= tdo["tg_pct"] - 15 else "#D98E04" if tdo["tong"] >= 0 else "#B4442F"
        ui.tiles([(f"{tdo['tong']} %", "hoàn thành mục tiêu", tdo["ten_loai"]),
                  (f"{tdo['tg_pct']} %", "thời gian đã qua", f"{tdo['bat_dau']:%d/%m} → {tdo['han']:%d/%m/%Y}"),
                  (f"{toc:+g} kg" if toc is not None else "—", "tốc độ cân / tuần", "theo TB 7 ngày, 14 ngày gần nhất"),
                  (f"{cc['tb']:g}/{cc['ke_hoach'] or '—'}", "buổi / tuần (TB 3 tuần)", f"{cc['ty_le']} % kế hoạch" if cc["ty_le"] is not None else "")])
        st.markdown(f'<div class="hac-card" style="border-left:5px solid {mau}"><b>{E(tdo["nhan_xet"])}</b></div>', unsafe_allow_html=True)
        st.dataframe(pd.DataFrame([{"Chỉ số": r["ten"], "Ban đầu": f"{r['goc']:g} {r['dv']}", "Hiện tại": f"{r['hien_tai']:g} {r['dv']}",
                                    "Đích": f"{r['dich']:g} {r['dv']}" + ("" if r["tu_dat"] else " (tự đặt)"), "Hoàn thành": f"{r['pct']} %",
                                    "Tốc độ / tuần": f"{r['toc_do_tuan']:+g}" if r.get("toc_do_tuan") is not None else "—",
                                    "Trạng thái": r["trang_thai"], "Dự đoán": r["du_doan"]} for r in tdo["rows"]]),
                     hide_index=True, use_container_width=True)
        M = lt.bang_do(ma)
        ui.sec("Thực tế · kế hoạch · dự đoán")
        cs = st.columns(2)
        for i, r in enumerate(tdo["rows"]):
            s_ = M[["ngay", r["ma"]]].dropna()
            fig = go.Figure()
            fig.add_scatter(x=s_["ngay"], y=s_[r["ma"]], mode="lines+markers", name="Thực tế", line=dict(color=ui.VANG, width=3))
            fig.add_scatter(x=[pd.Timestamp(tdo["bat_dau"]), pd.Timestamp(tdo["han"])], y=[r["goc"], r["dich"]], mode="lines",
                            name="Kế hoạch", line=dict(color="#8b8577", dash="dash"))
            if r.get("du_kien"):
                fig.add_scatter(x=[s_["ngay"].iloc[-1], pd.Timestamp(r["du_kien"])], y=[r["hien_tai"], r["dich"]], mode="lines",
                                name="Dự đoán theo nhịp hiện tại", line=dict(color="#2E7D4F", dash="dot"))
            fig.add_hline(y=r["dich"], line_dash="dot", line_color="#2E7D4F", annotation_text=f"Đích {r['dich']:g}")
            fig.update_layout(title=dict(text=f"{r['ten']} ({r['dv']})", font=dict(size=13)))
            fig.update_xaxes(tickformat="%d/%m")
            cs[i % 2].plotly_chart(ui.layout(fig, 260), use_container_width=True, config={"displayModeBar": False})
    the_danh_gia(k, td.can_ngay(ma), hom)
    ui.sec("Gợi ý điều chỉnh")
    for g in lt.goi_y(tdo, cc, toc, lo0):
        st.markdown(f"- {g}")
    st.caption("Gợi ý theo luật đơn giản từ số liệu đã nhập — anh quyết định cuối cùng. Dự đoán chỉ đáng tin khi có ≥ 3–4 lần đo cách nhau ≥ 1 tuần.")
    ui.sec("Chuyên cần 4 tuần")
    fig = go.Figure(go.Bar(x=[t["tuan"] for t in cc["tuans"]], y=[t["buoi"] for t in cc["tuans"]], marker_color=ui.VANG,
                           text=[t["buoi"] for t in cc["tuans"]], textposition="outside"))
    if cc["ke_hoach"]:
        fig.add_hline(y=cc["ke_hoach"], line_dash="dot", annotation_text=f"Kế hoạch {cc['ke_hoach']} buổi")
    st.plotly_chart(ui.layout(fig, 220, "buổi"), use_container_width=True, config={"displayModeBar": False})
    ui.sec("Lộ trình theo giai đoạn · khách cũng thấy (trang 🗺 Lộ trình)")
    from views import giai_doan_ui
    giai_doan_ui.trang(k, "hlv")
    M = lt.bang_do(ma)
    can0 = M["can_nang"].dropna().iloc[0] if M["can_nang"].notna().any() else None
    pbf0 = M["pbf"].dropna().iloc[0] if M["pbf"].notna().any() else None
    rm = tv.roadmap({"muc_tieu": lo0, "can_nang": can0, "pbf": pbf0, "buoi_tuan": len(store.lich_co_dinh(k)) or 3}, {})
    try:
        bd = date.fromisoformat(str(k.get("ngay_bat_dau"))[:10])
    except ValueError:
        bd = hom
    if can0 is not None:
        pj = pd.DataFrame(rm["proj"])
        pj["ngay"] = [pd.Timestamp(bd) + pd.Timedelta(weeks=w) for w in pj["tuan"]]
        fig = go.Figure()
        fig.add_scatter(x=pj["ngay"], y=pj["can_nang"], mode="lines", name="Lộ trình an toàn (cân)", line=dict(color="#8b8577", dash="dash"))
        s_ = M[["ngay", "can_nang"]].dropna()
        fig.add_scatter(x=s_["ngay"], y=s_["can_nang"], mode="lines+markers", name="Thực tế", line=dict(color=ui.VANG, width=3))
        fig.update_xaxes(tickformat="%d/%m")
        st.plotly_chart(ui.layout(fig, 280, "kg"), use_container_width=True, config={"displayModeBar": False})
        st.caption("Lộ trình an toàn theo khung của Hoàng Anh Coaching: giảm mỡ ~0,6 % cân / tuần, tăng cơ ~0,35 % / tuần, recomp ~0,2 % / tuần "
                   "(mức thực hành, không phải cam kết kết quả).")


def the_danh_gia(k: dict, CAN: pd.DataFrame, hom):
    """🔒 Đánh giá mục tiêu cân: tốc độ (kg & % cân / tuần), tính khả thi theo hạn, mốc dự kiến, lời khuyên. Chỉ HLV thấy."""
    from core import lo_trinh as lt
    g = lt.danh_gia_can(k, CAN, hom)
    if not g:
        return
    with st.container(border=True):
        st.markdown("#### 🎯 Đánh giá mục tiêu cân <span style='font-size:.75rem;color:#8b8577;font-weight:500'>🔒 chỉ HLV thấy</span>",
                    unsafe_allow_html=True)
        if not g.get("muc_tieu"):
            for x in g["loi_khuyen"][:1]:
                st.markdown(x)
            return
        huong = "giảm" if g["giam"] else "tăng"
        a, b, c, d = st.columns(4)
        a.metric(f"Đã {huong}", f"{g['da']:g} kg",
                 f"{g['pct_xong']}% chặng đường", delta_color="off")
        b.metric("Còn lại", f"{max(g['con'], 0):g} kg", f"từ {g['now']:g} → {g['muc_tieu']:g} kg", delta_color="off")
        b_t = "—" if g["toc"] is None else f"{g['toc']:+g} kg"
        c.metric("Tốc độ / tuần", b_t, None if g["pct"] is None else f"{g['pct']:+.2f}% cân nặng", delta_color="off")
        ng = g["nguong"]
        d.metric("Khuyến nghị / tuần", f"{ng[0]:g}–{ng[1]:g}%", f"≈ {g['now'] * ng[0] / 100:.1f}–{g['now'] * ng[1] / 100:.1f} kg/tuần",
                 delta_color="off")
        pill = lambda txt, mau: (f"<span style='background:{mau};color:#fff;border-radius:999px;padding:4px 12px;font-weight:800;"  # noqa: E731
                                 f"font-size:.82rem;margin-right:8px'>{E(txt)}</span>")
        st.markdown("**Độ " + huong + ":** " + pill(g["toc_nhan"], g["toc_mau"]) + " &nbsp; **Tính khả thi:** "
                    + pill(g["kha_thi"], g["kt_mau"]), unsafe_allow_html=True)
        moc = []
        if g.get("han") and g.get("con", 0) > 0:
            moc.append(f"Hạn **{g['han']:%d/%m/%Y}** → cần **{g.get('can_pct', 0):.2f}% cân nặng/tuần** "
                       f"(≈ {g['now'] * g.get('can_pct', 0) / 100:.2f} kg/tuần)")
        if g.get("ngay_nhip"):
            moc.append(f"Giữ nhịp hiện tại → đạt khoảng **{g['ngay_nhip']:%d/%m/%Y}**")
        if g.get("ngay_an_toan"):
            moc.append(f"Theo tốc độ khuyến nghị (giữa khoảng) → khoảng **{g['ngay_an_toan']:%d/%m/%Y}**")
        if moc:
            st.markdown("  \n".join("📅 " + x for x in moc))
        st.markdown("**💡 Lời khuyên**  \n" + "  \n".join(f"• {x}" for x in g["loi_khuyen"]))
        st.caption(f"Tính từ cân trung bình 7 ngày ({g['span']} ngày dữ liệu). Khoảng khuyến nghị: giảm mỡ 0,5–1 % cân/tuần "
                   "(Helms và cộng sự, 2014), người BMI ≥ 30 nới tới 1,25 %; tăng cơ 0,25–0,5 %/tuần (mức thực hành). "
                   "Mốc ngày là ước tính — cơ thể thường chậm dần về sau.")


def _quet_inbody(k: dict, u: dict):
    """Chụp / tải ảnh phiếu InBody → AI đọc số → điền sẵn form số đo (HLV xem lại rồi mới lưu). Giống Atlas v2.6."""
    from core import anh as A, llm, tu_van as tv
    ma = k["ma"]
    with st.container(border=True):
        st.markdown("**📷 Quét phiếu InBody** — chụp phiếu, web đọc số và điền sẵn bên dưới để anh kiểm tra")
        if not llm.is_online():
            st.caption("Cần khoá AI: thêm `GEMINI_API_KEY` (miễn phí ở aistudio.google.com) vào Secrets.")
            return
        a, b = st.columns([3, 1], vertical_alignment="bottom")
        f = a.file_uploader("Ảnh phiếu InBody", type=["jpg", "jpeg", "png", "webp"], key=f"ibf_{ma}_{S.get(f'ibv_{ma}', 0)}",
                            label_visibility="collapsed")
        if b.button("🔍 Đọc phiếu", disabled=f is None, use_container_width=True, key=f"ibb_{ma}"):
            with st.spinner("AI đang đọc phiếu (10–30 giây)…"):
                try:
                    r = tv.read_inbody(A.shrink(f.getvalue(), 1800))
                except llm.LLMError as e:
                    st.error(f"Chưa đọc được: {e}")
                    return
            if not r:
                st.error("Không đọc được số nào — chụp lại thẳng, đủ sáng, rõ phần số.")
                return
            S[f"ib_{ma}"] = r
            S[f"ibv_{ma}"] = S.get(f"ibv_{ma}", 0) + 1
            up = db.upload_images({"inbody": A.shrink(f.getvalue(), 1600)}, f"HAC_{ma}_")
            if up:
                td.luu_anh(ma, db.now_vn().date(), "khac", "inbody", up["inbody"], u)
            st.rerun()
        IB = S.get(f"ib_{ma}")
        if IB:
            st.success("Đã đọc: " + " · ".join(f"{tv.INBODY_FIELDS[x][0]} {v:g}" for x, v in IB.items() if x in tv.INBODY_FIELDS)
                       + " — kiểm tra lại từng ô rồi bấm Lưu số đo.")
            moi = {}
            if IB.get("chieu_cao") and not k.get("chieu_cao"):
                moi["chieu_cao"] = IB["chieu_cao"]
            if IB.get("gioi_tinh") and IB["gioi_tinh"] != k.get("gioi_tinh"):
                moi["gioi_tinh"] = IB["gioi_tinh"]
            if moi and st.button("Cập nhật hồ sơ khách: " + ", ".join(f"{x} = {v}" for x, v in moi.items()), key=f"ibhs_{ma}"):
                store.save_client({**k, **moi}, u["name"])
                st.toast("Đã cập nhật hồ sơ")
                st.rerun()


# =================================================================== SOẠN TIN
def soan_tin():
    u = _user()
    ui.hero("SOẠN TIN ZALO", "Hẹn buổi · nhắc buổi · lịch tuần · rủ tập lại", "")
    DS = store.clients()
    k = _chon_khach(DS)
    if not k:
        return
    hom = db.now_vn().date()
    H = store.hens()
    tuan0 = hom - timedelta(days=hom.weekday())
    B = store.buoi(DS, hom - timedelta(days=7), tuan0 + timedelta(days=13), H)
    m = k["ma"]
    loai = st.radio("Loại tin", ["Hẹn buổi mới", "Nhắc buổi sắp tới", "Lịch tuần này", "Rủ tập lại", "Tự viết"], horizontal=True, key="st_loai")
    if loai == "Hẹn buổi mới":
        a, b, c = st.columns(3)
        nd = a.date_input("Ngày", value=hom + timedelta(days=1), format="DD/MM/YYYY", key="st_nd")
        ng = b.text_input("Giờ", value="18:00", key="st_ng")
        dd_ = c.text_input("Nơi tập", value=k.get("dia_diem", ""), key="st_dd")
        txt = store.tin_hen(k, nd, ng, hom, dd_)
        if st.button("📌 Ghi buổi hẹn vào lịch", key="st_ghi"):
            store.ghi_hen(m, nd, _gio_chuan(ng) or ng.strip(), "hen", u["name"], dd_.strip())
            st.toast("Đã ghi buổi hẹn")
    elif loai == "Nhắc buổi sắp tới":
        sap = [b for b in B if b["ma"] == m and b["ngay"] >= hom and b["trang_thai"] == "hen"]
        if not sap:
            st.caption("Chưa có buổi sắp tới — hẹn buổi mới hoặc thêm lịch cố định.")
            txt = ""
        else:
            bi = st.selectbox("Buổi", range(len(sap)), format_func=lambda i: f"{store.THU[sap[i]['ngay'].weekday()]} "
                              f"{sap[i]['ngay']:%d/%m} · {store.gio_s(sap[i]['gio'])}", key="st_bi")
            txt = store.tin_nhac(k, sap[bi], hom)
    elif loai == "Lịch tuần này":
        txt = store.tin_tuan(k, [b for b in B if tuan0 <= b["ngay"] <= tuan0 + timedelta(days=6)], hom, H)
    elif loai == "Rủ tập lại":
        txt = store.tin_ru_quay_lai(k)
    else:
        txt = ""
    txt = st.text_area("Nội dung (sửa được trước khi gửi)", value=txt, height=180, key=f"st_txt_{m}_{loai}")
    if txt.strip():
        _soan(k, txt.strip(), f"st_{m}", u, hien=False)


# =================================================================== CHUYỂN DỮ LIỆU TỪ ATLAS
DOI = {"rieng_kh": "KhachHang", "rieng_hen": "LichHen", "rieng_can": "CanNang", "rieng_sodo": "SoDo", "rieng_anh": "Anh"}


def chuyen_atlas(rows: list[dict], nguoi: str, de: bool, lay_anh=None) -> dict[str, int]:
    """rows: dòng sheet TuongTac của Atlas. Chỉ lấy loai rieng_*; mỗi khoá lấy bản mới nhất. lay_anh(ids) → {id: bytes}."""
    rows = sorted([r for r in rows if str(r.get("loai")) in DOI], key=lambda r: str(r.get("thoi_gian") or ""))
    last: dict[tuple[str, str], dict] = {}
    for r in rows:
        last[(str(r["loai"]), str(r.get("su_kien") or ""))] = r
    dem = {v: 0 for v in DOI.values()}
    co = {b: set(db.latest(b, ca_xoa=True)) for b in DOI.values()}
    anh_rows = []
    for (loai, khoa), r in last.items():
        bang = DOI[loai]
        try:
            d = json.loads(r.get("noi_dung") or "{}")
        except (TypeError, ValueError):
            continue
        if not isinstance(d, dict) or (khoa in co[bang] and not de):
            continue
        if loai == "rieng_anh":
            anh_rows.append((khoa, d))
            continue
        ma = d.get("ma") or (khoa if loai == "rieng_kh" else "")
        if db.append(bang, khoa, d, nguoi, ma):
            dem[bang] += 1
    if anh_rows:
        cu = {d.get("id") for _, d in anh_rows if d.get("id") and str(d.get("xoa") or "") != "1"}
        IMG = lay_anh(list(cu)) if lay_anh and cu else {}
        for khoa, d in anh_rows:
            if str(d.get("xoa") or "") == "1":
                db.append("Anh", khoa, d, nguoi, d.get("ma", ""))
                continue
            data = IMG.get(d.get("id"))
            if data:
                up = db.upload_images({"x": data}, f"HAC_{d.get('ma')}_")
                if up:
                    d = {**d, "id": up["x"], "id_atlas": d.get("id")}
            if db.append("Anh", khoa, d, nguoi, d.get("ma", "")):
                dem["Anh"] += 1
    return dem


def nhap_atlas():
    u = _user()
    ui.hero("CHUYỂN DỮ LIỆU", "Chép khách từ Atlas Academy sang Hoàng Anh Coaching",
            "Chỉ CHÉP — không sửa, không xoá gì bên Atlas. Chạy lại không bị trùng khách.")
    t1, t2 = st.tabs(["👥 Khách anh đang dạy ở Atlas", "🔒 Mục Khách riêng (cũ)"])
    with t1:
        _chep_khach_atlas(u)
    with t2:
        _nhap_rieng()


def _chep_khach_atlas(u: dict):
    from core import nhap_kh_atlas as NA
    f = st.file_uploader("Cách nhanh: tải file Google Sheets của Atlas (Tệp › Tải xuống › .xlsx) hoặc file .json",
                         type=["xlsx", "json"], key="na_file")
    if f is not None:
        try:
            S["na_nguon"] = NA.doc_file(f.name, f.getvalue())
            S["na_rows"] = NA.khach_atlas(S["na_nguon"][NA.SHEETS["kh"]])
        except Exception as e:  # noqa: BLE001
            st.error(f"Không đọc được file: {e}")
    NA.NGUON = S.get("na_nguon") if f is not None else None
    if f is None and not NA.co_cau_hinh():
        ui.note("⚠️ Web chưa có quyền đọc Atlas. Vào <b>share.streamlit.io › app hoang-anh-coaching › Settings › Secrets</b>, "
                "thêm 2 dòng <code>ATLAS_SHEETS_WEBAPP_URL</code> và <code>ATLAS_SHEETS_TOKEN</code> — chép y hệt 2 dòng "
                "<code>SHEETS_WEBAPP_URL</code> / <code>SHEETS_TOKEN</code> trong Secrets của web Atlas — rồi Save và tải lại trang này. "
                "Hoặc dùng cách nhanh ở trên: tải file Sheets Atlas về rồi thả vào ô tải file.")
        return
    a, b = st.columns([1.3, 1])
    ten_pt = a.text_input("Tên PT bên Atlas (lọc khách anh dạy)", value=S.get("na_pt", "Hoàng Anh"), key="na_pt")
    phong = b.selectbox("🏢 Gắn phòng tập cho khách chép sang", store.ds_phong(store.clients()), key="na_phong")
    if f is None and st.button("🔎 Đọc danh sách khách từ Atlas", type="primary"):
        with st.spinner("Đang đọc hồ sơ khách của Atlas…"):
            try:
                S["na_rows"] = NA.khach_atlas(NA.doc(NA.SHEETS["kh"]))
            except Exception as e:  # noqa: BLE001
                st.error(f"Không đọc được Atlas: {e}")
                S.pop("na_rows", None)
    R = S.get("na_rows")
    if R is None:
        st.caption("Bấm nút trên để xem danh sách khách — chưa có gì được chép cho tới khi anh bấm 📥 Chép.")
        return
    da_co = {str(k.get("ma_atlas")) for k in store.clients() if k.get("ma_atlas")}
    cua_anh = [r for r in R if NA.cung_pt(r.get("pt"), ten_pt)]
    tat_ca = st.toggle(f"Hiện cả khách của PT khác ({len(R) - len(cua_anh)})", value=False, key="na_all")
    ds = R if tat_ca else cua_anh
    if not ds:
        st.warning(f"Không thấy khách nào có PT khớp “{ten_pt}”. Kiểm tra lại tên PT, hoặc bật hiện cả khách PT khác.")
        return
    df = pd.DataFrame([{"Chép": (str(r.get("ma_kh")) not in da_co) and (str(r.get("trang_thai") or "Đang tập") in ("Đang tập", "Tạm dừng")),
                        "Khách": NA._s(r.get("ho_ten")), "Mã Atlas": NA._s(r.get("ma_kh")), "PT": NA._s(r.get("pt")),
                        "Gói": f"{NA._s(r.get('loai_goi'))} {NA._s(r.get('so_buoi_goi'))}".strip(),
                        "Trạng thái": NA._s(r.get("trang_thai")) or "Đang tập",
                        "Đã có bên HAC": "✅ đã chép" if str(r.get("ma_kh")) in da_co else ""} for r in ds])
    ed = st.data_editor(df, hide_index=True, use_container_width=True, disabled=[c for c in df.columns if c != "Chép"],
                        column_config={"Chép": st.column_config.CheckboxColumn(alignment="center"),
                                       **{c: st.column_config.Column(alignment="left" if c in ("Khách", "Gói") else "center")
                                          for c in df.columns if c != "Chép"}}, key="na_ed")
    c1, c2, c3 = st.columns(3)
    sd = c1.checkbox("Chép số đo / InBody", value=True)
    bt = c2.checkbox("Chép buổi đã tập (kg × lần)", value=True)
    lc = c3.checkbox("Chép lịch tập cố định", value=True)
    chon = [r for r, x in zip(ds, ed["Chép"]) if x]
    st.caption(f"Đã tick {len(chon)} khách. Khách đã chép trước đó sẽ được cập nhật lại (không tạo khách trùng).")
    if st.button(f"📥 Chép {len(chon)} khách sang web này", type="primary", disabled=not chon):
        with st.spinner("Đang chép… (khách nhiều buổi có thể mất 1–2 phút)"):
            try:
                dem = NA.chep(chon, phong, u["name"], sd, bt, lc)
            except Exception as e:  # noqa: BLE001
                st.error(f"Chép dở dang: {e} — bấm chép lại được, không bị trùng.")
                return
        st.success("Đã chép: " + " · ".join(f"{v} {k}" for k, v in dem.items()))
        ui.note("Kiểm tra từng khách ở trang <b>👤 Khách & tài khoản</b> (gói, ngày kết thúc, buổi đã tập, lịch). "
                "Khách chưa có tài khoản đăng nhập — cấp ở tab 🔐 Tài khoản.")


def _nhap_rieng():
    st.markdown("""
**Cách 1 — đọc thẳng từ Atlas (có cả ảnh):** thêm vào Secrets của web này 2 dòng
`ATLAS_SHEETS_WEBAPP_URL` và `ATLAS_SHEETS_TOKEN` (chép y hệt Secrets của web Atlas), rồi bấm nút bên dưới.

**Cách 2 — file CSV:** mở Google Sheets của Atlas › sheet **TuongTac** › Tệp › Tải xuống › CSV, rồi tải lên đây
(cách này không chép được ảnh — ảnh vẫn nằm ở Drive của Atlas).
""")
    de = st.checkbox("Ghi đè bản đã chuyển trước (nếu chạy lại)", value=False)
    url, tok = config.get("ATLAS_SHEETS_WEBAPP_URL"), config.get("ATLAS_SHEETS_TOKEN")
    if st.button("📥 Đọc thẳng từ Atlas", type="primary", disabled=not (url and tok)):
        import requests
        with st.spinner("Đang đọc sheet TuongTac của Atlas…"):
            try:
                r = requests.get(url, timeout=60, params={"token": tok, "action": "read", "sheet": "TuongTac"}).json()
            except Exception as e:  # noqa: BLE001
                r = {"ok": False, "error": str(e)}
        if not r.get("ok"):
            st.error(f"Không đọc được: {r.get('error')}")
        else:
            def lay_anh(ids):
                import base64
                out = {}
                for j in range(0, len(ids), 20):
                    try:
                        x = requests.get(url, timeout=90, params={"token": tok, "action": "images", "ids": ",".join(ids[j:j + 20])}).json()
                        out.update({k: base64.b64decode(v) for k, v in (x.get("images") or {}).items()})
                    except Exception:  # noqa: BLE001
                        pass
                return out
            with st.spinner("Đang chuyển…"):
                dem = chuyen_atlas(r.get("rows") or [], "Chuyển từ Atlas", de, lay_anh)
            st.success("Đã chuyển: " + " · ".join(f"{k} {v}" for k, v in dem.items()))
    if not (url and tok):
        st.caption("Chưa có ATLAS_SHEETS_WEBAPP_URL / ATLAS_SHEETS_TOKEN trong Secrets.")
    f = st.file_uploader("Hoặc tải file CSV sheet TuongTac", type=["csv"])
    if f is not None and st.button("📥 Chuyển từ file CSV"):
        df = pd.read_csv(f, dtype=str).fillna("")
        dem = chuyen_atlas(df.to_dict("records"), "Chuyển từ Atlas (CSV)", de)
        st.success("Đã chuyển: " + " · ".join(f"{k} {v}" for k, v in dem.items()))
    ui.note("Chuyển xong, kiểm tra lại từng khách ở trang Khách & tài khoản. Khi mọi thứ đúng, anh báo Claude gỡ mục Khách riêng "
            "khỏi web Atlas và xoá các dòng rieng_* trong sheet TuongTac của Atlas.")


# =================================================================== v1.3 KHÁCH THẤY GÌ — bật / tắt mục + xem như khách
def khach_thay():
    u = _user()
    DS = store.clients(ca_ngung=False)
    ui.hero("CỔNG KHÁCH", "Khách thấy gì?", "Chia sẻ lộ trình cho nhiều khách một lúc, hoặc bật / tắt từng mục cho từng khách.")
    t1, t2 = st.tabs(["🔗 Chia sẻ lộ trình (nhiều khách)", "👁 Từng khách"])
    with t1:
        _chia_se(u, DS)
    with t2:
        _khach_thay_1(u, DS)


SHARE = ("lo_trinh", "lich", "can", "so_do")


def _chia_se(u: dict, DS: list[dict]):
    """Cấp tài khoản + bật mục Lộ trình / Lịch / Cân / Số đo cho nhiều khách cùng lúc.
    Mặc định tick khách gói Toàn diện ở Atlas và Gold Gym."""
    if not DS:
        st.info("Chưa có khách đang tập.")
        return
    TK = {v.get("ma_kh"): v for v in auth.accounts().values()}
    st.caption("Khách được chia sẻ sẽ đăng nhập cổng khách và thấy: 🗺 Lộ trình theo giai đoạn (bản tổng quan — bản chi tiết chỉ anh thấy), "
               "lịch hẹn & gói, cân và số đo. Khách chưa có tài khoản → web tạo tài khoản + mật khẩu và soạn sẵn tin Zalo.")
    DSs = sorted(DS, key=lambda k: (store.thu_tu_phong(store.phong(k)), str(k.get("ho_ten", ""))))
    def da_chia(k):
        q = store.quyen(k)
        return k["ma"] in TK and not TK[k["ma"]].get("khoa") and all(q[x] for x in SHARE)
    df = pd.DataFrame([{"Chia sẻ": da_chia(k) or (store.toan_dien(k) and store.phong(k) in ("Atlas", "Gold Gym")),
                        "Khách": k["ho_ten"], "🏢 Phòng": store.phong(k) or "—", "Gói": k.get("goi_ten") or "—",
                        "Toàn diện": "⭐" if store.toan_dien(k) else "",
                        "Tài khoản": ("🔒 " if TK[k["ma"]].get("khoa") else "✅ ") + TK[k["ma"]]["_khoa"] if k["ma"] in TK else "chưa có",
                        "Đang thấy lộ trình": "✅" if da_chia(k) else ""} for k in DSs])
    ed = st.data_editor(df, hide_index=True, use_container_width=True, disabled=[c for c in df.columns if c != "Chia sẻ"],
                        column_config={"Chia sẻ": st.column_config.CheckboxColumn(alignment="center"),
                                       **{c: st.column_config.Column(alignment="left" if c in ("Khách", "Gói") else "center")
                                          for c in df.columns if c != "Chia sẻ"}}, key="cs_ed")
    chon = [k for k, x in zip(DSs, ed["Chia sẻ"]) if x and not da_chia(k)]
    if st.button(f"🔗 Chia sẻ cho {len(chon)} khách", type="primary", disabled=not chon):
        moi = []
        for k in chon:
            q = {**store.quyen(k), **{x: True for x in SHARE}}
            store.save_client({**k, "quyen": q}, u["name"])
            acc = TK.get(k["ma"])
            if not acc:
                un = auth.norm_user(k["ho_ten"].split()[-1] + k["ma"][1:])
                pw = auth.tao_mat_khau()
                ok, _ = auth.save_account(k["ma"], un, pw, u["name"], False, None)
                if not ok:                                   # trùng tên đăng nhập → thêm mã khách
                    un = auth.norm_user(un + k["ma"].lower())
                    ok, _ = auth.save_account(k["ma"], un, pw, u["name"], False, None)
                if ok:
                    moi.append((k, un, pw))
            elif acc.get("khoa"):
                auth.save_account(k["ma"], acc["_khoa"], None, u["name"], khoa=False, cu=acc)
        S["cs_moi"] = moi
        st.rerun()
    for k, un, pw in S.get("cs_moi", []):
        with st.expander(f"✉️ Tin gửi {k['ho_ten']} (tài khoản mới — mật khẩu chỉ hiện lần này)", expanded=True):
            _soan(k, store.tin_tai_khoan(k, config.get("APP_URL") or "https://hoang-anh-coaching.streamlit.app", un, pw), f"cs_{k['ma']}", u)
    ui.note("Muốn thu hồi: bỏ tick không có tác dụng với khách đã chia sẻ — vào tab 👁 Từng khách để tắt mục Lộ trình, "
            "hoặc khoá tài khoản ở trang 👤 Khách & tài khoản.")


def _khach_thay_1(u: dict, DS: list[dict]):
    k = _chon_khach(DS, "kt")
    if not k:
        return
    acc = auth.account_of(k["ma"])
    if not acc:
        ui.note("⚠️ <b>Khách này chưa có tài khoản</b> nên chưa đăng nhập được. Cấp ở trang <b>👤 Khách & tài khoản › 🔐 Tài khoản "
                "cổng khách</b> — web tạo mật khẩu và soạn sẵn tin Zalo gửi khách.")
    else:
        st.caption(f"Tài khoản: **{acc['_khoa']}** · " + ("🔒 đang khoá" if acc.get("khoa") else "✅ đang hoạt động"))
    q = store.quyen(k)
    a, b = st.columns([1, 1.6], gap="large")
    with a:
        ui.sec("Mục khách được thấy / dùng")
        with st.form(f"q_{k['ma']}"):
            moi, nhom = {}, None
            for x, (n, ten, mo) in store.QUYEN.items():
                if n != nhom:
                    st.markdown(f"**{n}**")
                    nhom = n
                moi[x] = st.toggle(ten, value=q[x], help=mo, key=f"q_{k['ma']}_{x}")
            c1, c2 = st.columns(2)
            luu = c1.form_submit_button("💾 Lưu", type="primary", use_container_width=True)
            if c2.form_submit_button("Bật hết", use_container_width=True):
                moi, luu = {x: True for x in store.QUYEN}, True
            if luu:
                if store.save_client({**k, "quyen": moi}, u["name"]):
                    st.toast("Đã lưu — khách thấy ngay lần mở / tải lại trang tới")
                    st.rerun()
                st.error("Chưa lưu được — thử lại.")
        tr = store.trang_khach(q)
        st.caption("Menu khách hiện: 🏠 Tổng quan" + (" · 🏋️ Tập luyện" if tr["tap"] else "") + (" · 🍽 Thực đơn" if tr["an"] else "")
                   + (" · 🏃 Cardio" if tr["cardio"] else "") + (" · 📈 Cân & số đo" if tr["tien_do"] else "") + " · 🔐 Tài khoản. Khách **không bao giờ** thấy: ghi chú nội bộ, "
                   "lộ trình & tốc độ 🔒, giá gói, khách khác, trang HLV.")
    with b:
        ui.sec("Xem như khách")
        from views import client as KV
        tr = store.trang_khach(q)
        ds = [("tong", "🏠 Tổng quan", KV.trang_chu)] + [x for x, on in (
            (("tap", "🏋️ Tập luyện", KV.tap), tr["tap"]), (("an", "🍽 Thực đơn", KV.an), tr["an"]),
            (("cd", "🏃 Cardio", KV.cardio), tr["cardio"]), (("td", "📈 Cân & số đo", KV.tien_do), tr["tien_do"])) if on]
        chon = st.segmented_control("Trang", [x[0] for x in ds], default="tong", key=f"kt_tr_{k['ma']}",
                                    format_func=lambda i: next(t for x, t, _ in ds if x == i)) or "tong"
        st.markdown('<div style="background:#FFF6DD;border:1px dashed #C8A24A;border-radius:12px;padding:6px 12px;font-size:.8rem;'
                    'margin:4px 0 8px">👁 Bản xem trước — <b>đúng như khách thấy</b>. Bấm lưu / ghi ở đây là ghi dữ liệu thật của khách.</div>',
                    unsafe_allow_html=True)
        S["_xem_nhu"] = k["ma"]
        try:
            with st.container(border=True):
                next(f for x, _, f in ds if x == chon)()
        finally:
            S.pop("_xem_nhu", None)


def tien_do_all():
    from views import tien_do_all_ui
    tien_do_all_ui.trang(_user())


def goi_buoi():
    """v3.5 — 📦 Gói & buổi tập."""
    from views import goi_buoi_ui
    goi_buoi_ui.trang(_user())


def quet_inbody():
    """v3.4 — 📷 Quét phiếu InBody hàng loạt."""
    from views import quet_inbody_ui
    quet_inbody_ui.trang(_user())


def thau_hieu():
    """v3.1 — 🧠 Thấu hiểu khách (chỉ HLV)."""
    from views import thau_hieu_ui
    thau_hieu_ui.trang(_user())
