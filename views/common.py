# Hoàng Anh Coaching v1.0 (2026-10-31) — khối giao diện dùng chung cho HLV và khách:
# dinh dưỡng · giáo án · ghi buổi tập · số tạ & kỷ lục · cân hằng ngày
from __future__ import annotations

import html
from datetime import timedelta

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from core import db, dinh_duong as dd, giao_an as ga, store, tien_do as td, ui

E = html.escape
S = st.session_state


# =================================================================== dữ liệu nền
def can_pbf(ma: str) -> tuple[float | None, float | None, str]:
    """(cân mới nhất, % mỡ mới nhất, ngày cân)."""
    SD, CAN = td.so_do(ma), td.can_ngay(ma)
    moi = td.moi_nhat(SD, CAN) or {}
    pbf = None
    if not SD.empty and SD["pbf"].notna().any():
        pbf = float(SD.dropna(subset=["pbf"]).iloc[-1]["pbf"])
    ngay = moi.get("_ngay_can") or moi.get("ngay")
    return (float(moi["can_nang"]) if moi.get("can_nang") else None), pbf, (f"{ngay:%d/%m/%Y}" if ngay else "")


def ho_so_dd(k: dict) -> dict:
    """Thiết lập dinh dưỡng đã lưu + điền sẵn từ hồ sơ khách (giới tính, tuổi, cao, cân, % mỡ, ngày tập)."""
    hs = dict(db.latest("DinhDuong").get(f"hs|{k['ma']}", {}))
    kg, pbf, _ = can_pbf(k["ma"])
    hs.setdefault("gioi_tinh", k.get("gioi_tinh") or "Nam")
    if store.tuoi(k):
        hs["tuoi"] = store.tuoi(k)
    if k.get("chieu_cao"):
        hs.setdefault("cao", float(k["chieu_cao"]))
    if kg:
        hs["kg"] = kg
    if pbf and not hs.get("bo_pbf"):
        hs["pbf"] = pbf
    lich = store.lich_co_dinh(k)
    if lich and not hs.get("ngay_tap"):
        hs["ngay_tap"] = sorted({int(x["thu"]) for x in lich})
        hs.setdefault("buoi_tuan", len(hs["ngay_tap"]))
    return hs


def luu_hs_dd(ma: str, hs: dict, nguoi: str) -> bool:
    return db.append("DinhDuong", f"hs|{ma}", {k: v for k, v in hs.items() if not k.startswith("_")}, nguoi, ma)


# =================================================================== DINH DƯỠNG
def form_dd(k: dict, hs: dict, vai: str, nguoi: str):
    """HLV sửa mọi thông số; khách chỉ sửa sở thích ăn (số bữa, giờ tập, chế độ ăn, món không ăn)."""
    hlv = vai == "hlv"
    with st.form(f"dd_f_{k['ma']}_{vai}"):
        if hlv:
            ui.sec("Thông số cơ thể")
            a, b, c, d, e = st.columns(5)
            gt = a.selectbox("Giới tính", ["Nam", "Nữ"], index=1 if str(hs.get("gioi_tinh")) == "Nữ" else 0)
            tuoi = b.number_input("Tuổi", 14, 90, int(hs.get("tuoi") or 30))
            cao = c.number_input("Cao (cm)", 120.0, 220.0, float(hs.get("cao") or 165), step=0.5)
            kg = d.number_input("Cân (kg)", 30.0, 250.0, float(hs.get("kg") or 60), step=0.1, help="Tự lấy cân mới nhất; sửa nếu cần")
            pbf = e.number_input("% mỡ (InBody)", 0.0, 60.0, float(hs.get("pbf") or 0), step=0.1, help="Để 0 nếu chưa đo")
            ui.sec("Vận động & tập luyện")
            a, b, c, d = st.columns(4)
            vd = a.selectbox("Ngoài giờ tập", list(dd.VAN_DONG), format_func=lambda x: dd.VAN_DONG[x][0],
                             index=list(dd.VAN_DONG).index(hs.get("van_dong", "nhe")) if hs.get("van_dong") in dd.VAN_DONG else 1)
            bt = b.number_input("Buổi tập / tuần", 0, 7, int(hs.get("buoi_tuan") or 3))
            pb = c.number_input("Phút / buổi", 20, 150, int(hs.get("phut_buoi") or 60), step=5)
            cd = d.selectbox("Cường độ", list(dd.CUONG_DO), format_func=lambda x: dd.CUONG_DO[x][0],
                             index=list(dd.CUONG_DO).index(hs.get("cuong_do", "vua")) if hs.get("cuong_do") in dd.CUONG_DO else 0)
            a, b = st.columns([1, 3])
            cardio = a.number_input("Cardio thêm (phút / tuần)", 0, 900, int(hs.get("cardio_phut_tuan") or 0), step=15)
            ngay_tap = b.multiselect("Thứ có tập (để tính ngày tập / ngày nghỉ)", list(range(7)), default=[int(x) for x in hs.get("ngay_tap") or []],
                                     format_func=lambda i: store.THU[i])
            ui.sec("Mục tiêu")
            a, b, c, d = st.columns(4)
            mt = a.selectbox("Mục tiêu", list(dd.MUC_TIEU), format_func=dd.MUC_TIEU.get,
                             index=list(dd.MUC_TIEU).index(hs.get("muc_tieu", "giam_mo")) if hs.get("muc_tieu") in dd.MUC_TIEU else 0)
            tdo = b.selectbox("Tốc độ", list(dd.TOC_DO), format_func=dd.TOC_DO.get,
                              index=list(dd.TOC_DO).index(hs.get("toc_do", "vua")) if hs.get("toc_do") in dd.TOC_DO else 1)
            kct = c.number_input("Ghi đè kcal TB / ngày", 0, 6000, int(hs.get("kcal_tay") or 0), step=50, help="0 = để web tự tính")
            dgk = d.number_input("Ghi đè đạm (g/kg)", 0.0, 3.5, float(hs.get("dam_g_kg") or 0), step=0.1, help="0 = để web tự tính")
        ui.sec("Thói quen ăn")
        a, b, c = st.columns([1, 1, 2])
        sb = a.selectbox("Số bữa / ngày", [3, 4, 5, 6], index=[3, 4, 5, 6].index(int(hs.get("so_bua") or 4)))
        gt_ = b.selectbox("Giờ tập", list(dd.GIO_TAP), format_func=dd.GIO_TAP.get,
                          index=list(dd.GIO_TAP).index(hs.get("gio_tap", "chieu")) if hs.get("gio_tap") in dd.GIO_TAP else 2)
        cdo = c.multiselect("Chế độ ăn / kiêng", list(dd.CHE_DO), default=[x for x in (hs.get("che_do") or ["thuong"]) if x in dd.CHE_DO],
                            format_func=dd.CHE_DO.get)
        F = dd.foods()
        bo = st.multiselect("Món không ăn / không thích", sorted(F, key=lambda x: F[x]["ten"]),
                            default=[x for x in hs.get("bo_mon") or [] if x in F], format_func=lambda x: F[x]["ten"])
        if st.form_submit_button("💾 Lưu & tính lại", type="primary", use_container_width=True):
            moi = {**hs, "so_bua": sb, "gio_tap": gt_, "che_do": [x for x in cdo if x != "thuong"] or ["thuong"], "bo_mon": bo}
            if hlv:
                moi.update({"gioi_tinh": gt, "tuoi": tuoi, "cao": cao, "kg": kg, "pbf": pbf or None, "bo_pbf": not pbf,
                            "van_dong": vd, "buoi_tuan": bt, "phut_buoi": pb, "cuong_do": cd, "cardio_phut_tuan": cardio,
                            "ngay_tap": ngay_tap, "muc_tieu": mt, "toc_do": tdo, "kcal_tay": kct or None, "dam_g_kg": dgk or None})
            if luu_hs_dd(k["ma"], moi, nguoi):
                S.pop(f"dd_doi_{k['ma']}", None)
                st.toast("Đã lưu — thực đơn đã tính lại")
                st.rerun()
            st.error("Chưa lưu được — thử lại.")


def _bang_bua(b: dict, F: dict) -> str:
    vai = {"truoc": '<span class="hac-chip g">TRƯỚC TẬP</span>', "sau": '<span class="hac-chip x">SAU TẬP</span>'}.get(b["vai"], "")
    t = b["thuc"]
    dong = "".join(
        f'<tr><td>{E(F[m]["ten"])}</td><td class="g">{g:g} g</td><td class="u">{E(dd.mo_ta_luong(m, g, F))}</td></tr>'
        for m, g in b["mon"].items())
    return (f'<div class="hac-meal"><div class="h"><b>{E(b["ten"])} {vai}</b><span>~{E(b["gio"])} · {t["kcal"]:.0f} kcal · '
            f'Đ {t["p"]:.0f} g · TB {t["c"]:.0f} g · B {t["f"]:.0f} g</span></div><table>{dong}</table></div>')


def dinh_duong(k: dict, vai: str, nguoi: str):
    hs = ho_so_dd(k)
    hlv = vai == "hlv"
    if not hs.get("cao") or not hs.get("kg"):
        st.info("Cần chiều cao và cân nặng để tính." + (" Nhập ở hồ sơ khách hoặc ngay dưới đây." if hlv else " HLV sẽ cập nhật giúp bạn."))
    if hlv or not hs.get("_khoa"):
        with st.expander("⚙️ Thông số tính thực đơn" if hlv else "⚙️ Sở thích ăn uống", expanded=hlv and not hs.get("_khoa")):
            form_dd(k, hs, vai, nguoi)
    else:
        with st.expander("⚙️ Sở thích ăn uống (số bữa, giờ tập, món không ăn)"):
            form_dd(k, hs, vai, nguoi)
    if not hs.get("cao") or not hs.get("kg"):
        return
    h = dd.HoSo.tu_dict(hs)
    kq = dd.tinh(h)
    F = dd.foods()
    bo = set(hs.get("bo_mon") or [])

    ui.tiles([(f"{kq['tap']['kcal']:,}".replace(",", "."), "kcal ngày tập", f"Đ {kq['tap']['p']} · TB {kq['tap']['c']} · B {kq['tap']['f']} g"),
              (f"{kq['nghi']['kcal']:,}".replace(",", "."), "kcal ngày nghỉ", f"Đ {kq['nghi']['p']} · TB {kq['nghi']['c']} · B {kq['nghi']['f']} g"),
              (f"{kq['dam']} g", "đạm mỗi ngày", f"{kq['dam_g_kg']:g} g / kg cân"),
              (f"{kq['nuoc_nghi']:g}–{kq['nuoc_tap']:g} L", "nước / ngày", "ngày nghỉ – ngày tập")])
    if kq["kg_tuan"]:
        dich = k.get("can_muc_tieu")
        tt = dd.tuan_toi_dich(h, kq, float(dich)) if dich else None
        ui.note(f"<b>Dự kiến:</b> {'giảm' if kq['kg_tuan'] < 0 else 'tăng'} khoảng <b>{abs(kq['kg_tuan']):g} kg / tuần</b>"
                + (f" → tới mục tiêu {float(dich):g} kg sau khoảng <b>{tt:g} tuần</b>" if tt else "")
                + ". Đây là ước tính; số thật theo dõi bằng cân trung bình 7 ngày.")
    if hlv:
        for g in kq["ghi"]:
            st.caption(f"⚠️ {g}")

    t1, t2, t3, t4, t5 = st.tabs(["🍽 Thực đơn hôm nay", "📅 Thực đơn 7 ngày", "🔁 Đổi món tương đương", "🛒 Đi chợ tuần", "🧮 Cách tính"])
    hom = db.now_vn().date()
    tap_set = set(dd.ngay_tap_tuan(h))
    with t1:
        a, b = st.columns([2, 1])
        thu = a.segmented_control("Ngày", list(range(7)), default=hom.weekday(), format_func=lambda i: store.THU[i].replace("Thứ ", "T"),
                                  key=f"dd_thu_{k['ma']}_{vai}")
        thu = hom.weekday() if thu is None else thu
        la_tap = b.toggle("Ngày có tập", value=thu in tap_set, key=f"dd_tap_{k['ma']}_{vai}_{thu}")
        doi = S.setdefault(f"dd_doi_{k['ma']}", {})
        ngay = dd.thuc_don_ngay(h, kq, la_tap, thu, k["ma"], doi.get(thu), bo)
        m = kq["tap"] if la_tap else kq["nghi"]
        tt = {x: sum(bb["thuc"][x] for bb in ngay) for x in ("kcal", "p", "c", "f", "xo")}
        c1, c2 = st.columns([1.1, 1])
        with c1:
            fig = go.Figure(go.Pie(labels=["Đạm", "Tinh bột", "Béo"], values=[tt["p"] * 4, tt["c"] * 4, tt["f"] * 9], hole=.62,
                                   marker=dict(colors=[ui.MACRO_MAU["p"], ui.MACRO_MAU["c"], ui.MACRO_MAU["f"]]), sort=False,
                                   textinfo="percent", hovertemplate="%{label}: %{value:.0f} kcal<extra></extra>"))
            fig.add_annotation(text=f"<b>{tt['kcal']:.0f}</b><br>kcal", showarrow=False, font=dict(size=18))
            st.plotly_chart(ui.layout(fig, 250), use_container_width=True, config={"displayModeBar": False})
        with c2:
            st.dataframe(pd.DataFrame([
                {"": "Năng lượng", "Mục tiêu": f"{m['kcal']} kcal", "Thực đơn": f"{tt['kcal']:.0f} kcal"},
                {"": "Đạm", "Mục tiêu": f"{m['p']} g", "Thực đơn": f"{tt['p']:.0f} g"},
                {"": "Tinh bột", "Mục tiêu": f"{m['c']} g", "Thực đơn": f"{tt['c']:.0f} g"},
                {"": "Béo", "Mục tiêu": f"{m['f']} g", "Thực đơn": f"{tt['f']:.0f} g"},
                {"": "Chất xơ", "Mục tiêu": f"≥ {m['xo']} g", "Thực đơn": f"{tt['xo']:.0f} g"}]), hide_index=True, use_container_width=True)
            if tt["xo"] < m["xo"] * 0.8:
                st.caption("Chất xơ còn thiếu — thêm rau, trái cây, đổi cơm trắng sang gạo lứt / khoai lang.")
        st.markdown("".join(_bang_bua(bb, F) for bb in ngay), unsafe_allow_html=True)
        with st.expander("🔁 Đổi món trong bữa (web tự tính lại số gram)"):
            for bb in ngay:
                cols = st.columns(4)
                cols[0].markdown(f"**{bb['ten']}**")
                cho = dict(doi.get(thu, {}).get(bb["bua"], {}))
                for i, vt in enumerate(("dam", "tinh_bot", "beo")):
                    ds = dd.lua_chon(bb["mau"], vt, F, h.che_do, bo)
                    hien = bb["vai_tro"].get(vt)
                    if not ds or hien not in ds:
                        continue
                    x = cols[i + 1].selectbox({"dam": "Đạm", "tinh_bot": "Tinh bột", "beo": "Béo"}[vt], ds, index=ds.index(hien),
                                              format_func=lambda z: F[z]["ten"], key=f"dd_s_{k['ma']}_{vai}_{thu}_{bb['bua']}_{vt}")
                    if x != hien:
                        cho[vt] = x
                        doi.setdefault(thu, {})[bb["bua"]] = cho
                        st.rerun()
            if doi.get(thu) and st.button("↩ Về thực đơn gợi ý", key=f"dd_reset_{k['ma']}_{vai}_{thu}"):
                doi.pop(thu, None)
                st.rerun()
        ui.note("Gram là <b>khối lượng đã nấu chín</b> (cơm, thịt, cá) — riêng yến mạch, whey là khô. Nấu bằng ít dầu: "
                "dầu trong thực đơn đã tính sẵn. Rau ăn thoải mái thêm nếu còn đói.")

    with t2:
        tuan = dd.thuc_don_tuan(h, kq, k["ma"], bo)
        st.dataframe(pd.DataFrame([{"Ngày": store.THU[d["thu"]], "Loại": "🏋️ Tập" if d["tap"] else "😌 Nghỉ",
                                    "kcal": round(sum(b["thuc"]["kcal"] for b in d["bua"])),
                                    "Đạm (g)": round(sum(b["thuc"]["p"] for b in d["bua"])),
                                    "Tinh bột (g)": round(sum(b["thuc"]["c"] for b in d["bua"])),
                                    "Béo (g)": round(sum(b["thuc"]["f"] for b in d["bua"]))} for d in tuan]),
                     hide_index=True, use_container_width=True)
        for d in tuan:
            with st.expander(f"{store.THU[d['thu']]} · {'ngày tập' if d['tap'] else 'ngày nghỉ'}"):
                st.markdown("".join(_bang_bua(bb, F) for bb in d["bua"]), unsafe_allow_html=True)

    with t3:
        st.caption("Ăn ngoài, hết món? Đổi sang món khác cùng nhóm với lượng tương đương dưới đây.")
        a, b = st.columns(2)
        with a:
            st.markdown("**25 g đạm tương đương**")
            st.dataframe(pd.DataFrame(dd.quy_doi({"dam"}, 25, "p", h.che_do), columns=["Món", "Gram", "Ước lượng"]),
                         hide_index=True, use_container_width=True)
        with b:
            st.markdown("**40 g tinh bột tương đương**")
            st.dataframe(pd.DataFrame(dd.quy_doi({"tinh_bot", "trai_cay"}, 40, "c", h.che_do), columns=["Món", "Gram", "Ước lượng"]),
                         hide_index=True, use_container_width=True)
        st.markdown("**10 g béo tương đương**")
        st.dataframe(pd.DataFrame(dd.quy_doi({"beo"}, 10, "f", h.che_do), columns=["Món", "Gram", "Ước lượng"]),
                     hide_index=True, use_container_width=True)
        st.caption("Món đạm động vật kèm ít béo; đậu, hạt kèm thêm tinh bột / béo — nên đổi sang món gần nhóm nhất.")

    with t4:
        tuan = dd.thuc_don_tuan(h, kq, k["ma"], bo)
        ds = dd.di_cho(tuan)
        st.dataframe(pd.DataFrame([{"Món": t, "Cả tuần": f"{g / 1000:.2f} kg" if g >= 1000 else f"{g:.0f} g"} for t, g in ds]),
                     hide_index=True, use_container_width=True)
        st.caption("Khối lượng đã nấu chín (trừ đồ khô) — thịt cá sống thường nặng hơn khoảng 25–35 % (ước lượng, tuỳ món và cách nấu).")

    with t5:
        fig = go.Figure(go.Waterfall(
            orientation="v", measure=["absolute", "relative", "relative", "relative", "total"],
            x=["BMR (nền)", "Vận động ngoài giờ", "Buổi tập (ngày tập)", "Điều chỉnh mục tiêu", "Ngày tập"],
            y=[kq["bmr"], kq["neat"] + kq["e_cardio"], kq["e_buoi"], kq["tap"]["kcal"] - kq["tdee_tap"], 0],
            text=[f"{kq['bmr']}", f"+{kq['neat'] + kq['e_cardio']}", f"+{kq['e_buoi']}", f"{kq['tap']['kcal'] - kq['tdee_tap']:+}",
                  f"{kq['tap']['kcal']}"], textposition="outside",
            connector=dict(line=dict(color="#DDD4C0")), increasing=dict(marker=dict(color="#C8A24A")),
            decreasing=dict(marker=dict(color="#B4442F")), totals=dict(marker=dict(color="#1C1B19"))))
        st.plotly_chart(ui.layout(fig, 320, "kcal"), use_container_width=True, config={"displayModeBar": False})
        st.markdown(f"""
| Bước | Cách tính | Kết quả |
|---|---|---|
| Năng lượng nền (BMR) | Mifflin-St Jeor (1990){' · Katch-McArdle theo khối nạc ' + str(kq['lbm']) + ' kg (dùng số này)' if kq['bmr_k'] else ''} | {kq['bmr_m']} kcal{f" · {kq['bmr_k']} kcal" if kq['bmr_k'] else ''} |
| Vận động ngoài giờ | BMR × {kq['he_so']:g} (hệ số thực hành, đã gồm tiêu hoá thức ăn) | {kq['tdee_nghi'] - kq['e_cardio']} kcal |
| Buổi tập | (MET − 1) × {h.kg:g} kg × {h.phut_buoi} phút — Compendium of Physical Activities 2011 | +{kq['e_buoi']} kcal ngày tập |
| Cardio thêm | (6 − 1) × kg × giờ / 7 ngày | +{kq['e_cardio']} kcal / ngày |
| TDEE | ngày nghỉ · ngày tập · trung bình tuần | {kq['tdee_nghi']} · {kq['tdee_tap']} · {kq['tdee_tb']} kcal |
| Điều chỉnh | {dd.MUC_TIEU.get(h.muc_tieu)} · {dd.TOC_DO.get(h.toc_do)} | {kq['delta']:+} kcal / ngày |
| Đạm | {kq['cach_dam']} — Morton 2018; Helms 2014 | {kq['dam']} g |
| Béo | 25–28 % năng lượng, ≥ 0,6 g/kg (AMDR 20–35 %, IOM 2005) | ngày tập {kq['tap']['f']} g |
| Tinh bột | phần năng lượng còn lại | {kq['tap']['c']} g tập · {kq['nghi']['c']} g nghỉ |
| Chất xơ | 14 g / 1.000 kcal (IOM 2005) | ≥ {kq['tap']['xo']} g |
| Nước | 35 ml / kg + 0,5 L mỗi giờ tập (ước lượng) | {kq['nuoc_nghi']:g}–{kq['nuoc_tap']:g} L |
""")
        ui.note("Mọi công thức trên cho ra <b>ước tính ban đầu</b>, sai số thường vài trăm kcal mỗi ngày. Cách chỉnh: theo dõi "
                "<b>cân trung bình 7 ngày</b> trong 2–3 tuần — nếu không đổi theo hướng mong muốn thì HLV chỉnh ±100–200 kcal. "
                "Bảng thực phẩm lấy theo USDA FoodData Central (món Việt dùng loại gần nhất), sai số ±10–15 %. "
                "Người có bệnh nền (tiểu đường, thận, tim mạch…) hoặc đang mang thai cần bác sĩ / chuyên gia dinh dưỡng duyệt.")


# =================================================================== GIÁO ÁN
def _the_bai(b: dict, truoc: dict | None = None) -> str:
    ss = f'<span class="hac-chip g">{E(b["ss"])}</span>' if b.get("ss") else ""
    x = []
    if b.get("hiep"):
        x.append(f"{b['hiep']} hiệp × {b.get('lan') or '?'} lần")
    if b.get("kg"):
        x.append(f"{b['kg']:g} kg")
    if b.get("rpe"):
        x.append(f"RPE {b['rpe']:g}")
    elif b.get("rpe_txt"):
        x.append(str(b["rpe_txt"]))
    if b.get("nghi"):
        x.append(f"nghỉ {int(b['nghi'])} giây")
    elif b.get("nghi_txt"):
        x.append(f"nghỉ {b['nghi_txt']}")
    if b.get("tempo"):
        x.append(f"tempo {b['tempo']}")
    tr = ""
    if truoc:
        tr = " · lần trước: " + ", ".join(f"{ga._f(s.get('kg')) or 0:g}×{ga._i(s.get('lan')) or 0}" for s in truoc["sets"][:6])
    return (f'<div class="hac-ex"><div class="n">{ss}{E(b["bai"])}</div><div class="m">{E(" · ".join(x))}{E(tr)}</div>'
            + (f'<div class="m">📝 {E(b["ghi_chu"])}</div>' if b.get("ghi_chu") else "") + "</div>")


def xem_giao_an(k: dict, g: dict, L: list[dict]):
    if g.get("ghi_chu"):
        ui.note(E(g["ghi_chu"]))
    buoi = g.get("buoi") or []
    if not buoi:
        st.caption("Giáo án chưa có buổi nào.")
        return
    tabs = st.tabs([b.get("ten") or f"Buổi {i + 1}" for i, b in enumerate(buoi)])
    for t, b in zip(tabs, buoi):
        with t:
            st.markdown("".join(_the_bai(x, ga.lan_truoc(k["ma"], x["bai"], L)) for x in b.get("bai", [])), unsafe_allow_html=True)


def sua_giao_an(k: dict, vai: str, nguoi: str, g0: dict | None):
    """Soạn / sửa giáo án. Khách chỉ sửa giáo án do chính khách tạo."""
    key = f"ga_ed_{k['ma']}_{(g0 or {}).get('_khoa', 'moi')}"
    if key not in S:
        S[key] = [dict(b) for b in (g0 or {}).get("buoi") or [{"ten": "Buổi A", "bai": []}]]
    buoi = S[key]
    tv = ga.ten_bai()
    them = S.setdefault("ga_bai_them", [])
    co = sorted({x["bai"] for b in buoi for x in b.get("bai", [])} - set(tv))
    opts = tv + sorted(set(them + co))
    a, b = st.columns([2, 1])
    ten = a.text_input("Tên giáo án", value=(g0 or {}).get("ten", "Giáo án " + db.now_vn().strftime("%m/%Y")), key=key + "_ten")
    dung = b.toggle("Đang dùng", value=bool((g0 or {}).get("dang_dung", True)), key=key + "_dd")
    gc = st.text_area("Ghi chú chung (khởi động, cardio, lưu ý chấn thương…)", value=(g0 or {}).get("ghi_chu", ""), height=70, key=key + "_gc")
    with st.popover("➕ Bài ngoài thư viện"):
        nb = st.text_input("Tên bài", key=key + "_nb")
        if st.button("Thêm vào danh sách chọn", key=key + "_nbb") and nb.strip():
            them.append(nb.strip())
            st.rerun()
    if vai == "hlv" and not (g0 or {}).get("buoi"):
        mau = config_mau()
        with st.popover("⚡ Tạo nhanh từ mẫu"):
            mk = st.selectbox("Mục tiêu", list(mau), format_func=lambda x: mau[x]["ten"], key=key + "_mau")
            st.caption(mau[mk]["cuong_do"])
            if st.button("Dùng mẫu này", key=key + "_maub"):
                buoi[0]["bai"] = mau[mk]["bai"]
                st.rerun()
    cfg = {"ss": st.column_config.TextColumn("SS", help="Cùng chữ (A, B…) = superset, tập liền nhau", width="small"),
           "bai": st.column_config.SelectboxColumn("Bài", options=opts, required=True, width="medium"),
           "hiep": st.column_config.NumberColumn("Hiệp", min_value=1, max_value=10, step=1, width="small"),
           "lan": st.column_config.TextColumn("Lần", help="VD 8-10, 12, 30 giây", width="small"),
           "kg": st.column_config.NumberColumn("Kg", min_value=0.0, step=0.5, format="%.1f", width="small"),
           "rpe": st.column_config.NumberColumn("RPE", min_value=5.0, max_value=10.0, step=0.5, width="small"),
           "nghi": st.column_config.NumberColumn("Nghỉ (s)", min_value=0, step=15, width="small"),
           "tempo": st.column_config.TextColumn("Tempo", help="VD 3-1-1", width="small"),
           "ghi_chu": st.column_config.TextColumn("Ghi chú")}
    moi = []
    for i, bb in enumerate(buoi):
        with st.container(border=True):
            c1, c2 = st.columns([4, 1], vertical_alignment="bottom")
            tb = c1.text_input("Tên buổi", value=bb.get("ten", f"Buổi {i + 1}"), key=f"{key}_tb{i}_{len(buoi)}")
            if c2.button("🗑 Xoá buổi", key=f"{key}_xb{i}", use_container_width=True, disabled=len(buoi) == 1):
                buoi.pop(i)
                st.rerun()
            df = st.data_editor(ga.bai_df(bb.get("bai", [])), num_rows="dynamic", hide_index=True, use_container_width=True,
                                column_config=cfg, key=f"{key}_de{i}_{len(buoi)}")
            moi.append({"ten": tb.strip() or f"Buổi {i + 1}", "bai": ga.df_bai(df)})
    a, b, c = st.columns(3)
    if a.button("➕ Thêm buổi", key=key + "_tbm", use_container_width=True):
        S[key] = moi + [{"ten": f"Buổi {chr(65 + len(moi))}", "bai": []}]
        st.rerun()
    if b.button("💾 Lưu giáo án", key=key + "_luu", type="primary", use_container_width=True):
        if not any(x["bai"] for x in moi):
            st.error("Chưa có bài nào.")
        else:
            gid = ga.save_plan(k["ma"], {**(g0 or {}), "ten": ten.strip() or "Giáo án", "dang_dung": dung, "ghi_chu": gc.strip(),
                                         "buoi": moi, "tac_gia": (g0 or {}).get("tac_gia") or vai}, nguoi)
            S.pop(key, None)
            S[f"ga_chon_{k['ma']}"] = gid
            S[f"ga_sua_{k['ma']}"] = False
            st.toast("Đã lưu giáo án")
            st.rerun()
    if g0 and c.button("🗑 Xoá giáo án", key=key + "_xoa", use_container_width=True):
        ga.xoa_plan(k["ma"], g0["_khoa"], nguoi)
        S.pop(key, None)
        S.pop(f"ga_chon_{k['ma']}", None)
        S[f"ga_sua_{k['ma']}"] = False
        st.rerun()


def config_mau() -> dict:
    from core import config
    d = config.load_json("thu_vien_bai_tap.json")
    tv = {b["id"]: b["ten"] for n in d["nhom"].values() for b in n["bai"]}
    nhom = {b["id"]: nk for nk, n in d["nhom"].items() for b in n["bai"]}
    ten = {"giam_mo": "Giảm mỡ", "tang_co": "Tăng cơ", "recomp": "Recomp", "suc_khoe": "Sức khoẻ", "suc_manh": "Sức mạnh"}
    out = {}
    for mk, m in d["giao_an"].items():
        bai = []
        for _, bid, lieu in m["bai"]:
            if bid not in tv:
                continue
            hiep, _, lan = str(lieu).partition("×")
            bai.append({"bai": tv[bid], "nhom": nhom[bid], "hiep": int(hiep) if hiep.strip().isdigit() else 3, "lan": lan.strip()})
        out[mk] = {"ten": ten.get(mk, mk), "cuong_do": m.get("cuong_do", ""), "bai": bai}
    return out


def ghi_buoi(k: dict, vai: str, nguoi: str, G: list[dict], L: list[dict]):
    """Ghi kg × lần từng hiệp. Điền sẵn theo giáo án + gợi ý tăng tạ từ lần trước."""
    ma = k["ma"]
    dung = [g for g in G if g.get("dang_dung")] or G
    lua = [("tu_do", "Buổi tự do (tự chọn bài)")] + [(f"{g['_khoa']}|{i}", f"{g.get('ten')} › {b.get('ten')}")
                                                    for g in dung for i, b in enumerate(g.get("buoi") or [])]
    a, b = st.columns([2, 1])
    chon = a.selectbox("Buổi tập", [x[0] for x in lua], format_func=dict(lua).get, index=1 if len(lua) > 1 else 0, key=f"gb_ch_{ma}_{vai}")
    ngay = b.date_input("Ngày", db.now_vn().date(), format="DD/MM/YYYY", max_value=db.now_vn().date(), key=f"gb_ng_{ma}_{vai}")
    if chon == "tu_do":
        bai_ga = [{"bai": x, "nhom": ga.thu_vien().get(x, {}).get("nhom", ""), "hiep": 3}
                  for x in st.multiselect("Chọn bài", ga.ten_bai(), key=f"gb_td_{ma}_{vai}")]
        gid, ten_buoi = "", "Buổi tự do"
    else:
        gid, i = chon.rsplit("|", 1)
        g = next(x for x in G if x["_khoa"] == gid)
        bai_ga, ten_buoi = g["buoi"][int(i)].get("bai", []), g["buoi"][int(i)].get("ten", "")
    if not bai_ga:
        st.caption("Chọn bài để bắt đầu ghi.")
        return
    with st.form(f"gb_f_{ma}_{vai}_{chon}"):
        ket = []
        for j, x in enumerate(bai_ga):
            tr = ga.lan_truoc(ma, x["bai"], L)
            kg_g, loi = ga.goi_y(x, tr)
            st.markdown(_the_bai(x, tr), unsafe_allow_html=True)
            if loi:
                st.caption(f"💡 {loi}")
            n = int(x.get("hiep") or 3)
            kl = ga.khoang_lan(x.get("lan"))
            nan = float("nan")
            df0 = pd.DataFrame({"Hiệp": list(range(1, n + 1)), "Kg": [kg_g if kg_g is not None else nan] * n,
                                "Lần": [nan] * n, "RPE": [nan] * n})
            df = st.data_editor(df0, num_rows="dynamic", hide_index=True, use_container_width=True, key=f"gb_de_{ma}_{vai}_{chon}_{j}",
                                column_config={"Hiệp": st.column_config.NumberColumn(disabled=True, width="small"),
                                               "Kg": st.column_config.NumberColumn(min_value=0.0, step=0.5, format="%.1f"),
                                               "Lần": st.column_config.NumberColumn(min_value=0, step=1,
                                                                                    help=f"Mục tiêu {kl[0]}–{kl[1]}" if kl else None),
                                               "RPE": st.column_config.NumberColumn(min_value=5.0, max_value=10.0, step=0.5)})
            sets = [{"kg": ga._f(r["Kg"]) or 0, "lan": ga._i(r["Lần"]), **({"rpe": float(r["RPE"])} if pd.notna(r["RPE"]) else {})}
                    for r in df.to_dict("records") if ga._i(r.get("Lần"))]
            ket.append({"bai": x["bai"], **({"id": x["id"]} if x.get("id") else {}), "sets": sets})
        a, b, c = st.columns(3)
        cn = a.select_slider("Cảm nhận buổi tập", [1, 2, 3, 4, 5], value=4,
                             format_func=lambda v: {1: "😫 Rất mệt", 2: "😕 Mệt", 3: "😐 Bình thường", 4: "🙂 Tốt", 5: "🔥 Rất tốt"}[v])
        tl = b.number_input("Thời lượng (phút)", 0, 240, 60, step=5)
        gc = c.text_input("Ghi chú", placeholder="VD đau nhẹ vai trái, ngủ ít…")
        if st.form_submit_button("💾 Lưu buổi tập", type="primary", use_container_width=True):
            ket = [x for x in ket if x["sets"]]
            if not ket:
                st.error("Chưa nhập số lần của hiệp nào.")
            else:
                cu = ga.ky_luc(ga.lich_su_bai(ma, L))
                ga.save_log(ma, {"ngay": ngay.isoformat(), "ga_id": gid, "buoi": ten_buoi, "nguoi_ghi": vai, "bai": ket,
                                 "cam_nhan": cn, "thoi_luong": tl, "ghi_chu": gc.strip()}, nguoi)
                moi_pr = []
                for x in ket:
                    best = max((ga.e1rm(s["kg"], s["lan"]) or 0) for s in x["sets"])
                    old = cu[cu["bai"] == x["bai"]]["e1rm"]
                    if best and (old.empty or best > float(old.iloc[0])):
                        moi_pr.append(x["bai"])
                S[f"gb_pr_{ma}"] = moi_pr
                st.toast("Đã lưu buổi tập 💪")
                st.rerun()
    if S.get(f"gb_pr_{ma}"):
        st.success("🏆 Kỷ lục mới: " + ", ".join(S.pop(f"gb_pr_{ma}")))


def lich_su(k: dict, vai: str, nguoi: str, L: list[dict]):
    if not L:
        st.info("Chưa có buổi nào được ghi.")
        return
    for nk in reversed(L[-30:]):
        t = ga.tong_buoi(nk)
        ai = "HLV ghi" if nk.get("nguoi_ghi") == "hlv" else "Tự ghi"
        with st.expander(f"{pd.Timestamp(str(nk.get('ngay'))[:10]):%d/%m/%Y} · {nk.get('buoi') or 'Buổi tập'} · "
                         f"{t['bai']} bài · {t['volume']:,.0f} kg tổng · {ai}".replace(",", ".")):
            for b in nk.get("bai", []):
                st.markdown(f"**{b['bai']}** — " + " · ".join(
                    f"{ga._f(s.get('kg')) or 0:g} kg × {ga._i(s.get('lan')) or 0}" + (f" @ {s['rpe']:g}" if s.get("rpe") else "")
                    for s in b.get("sets", [])))
            if nk.get("ghi_chu"):
                st.caption(f"📝 {nk['ghi_chu']}")
            if nk.get("loi_nhan"):
                st.info(f"💬 Lời nhắn HLV: {nk['loi_nhan']}")
            if vai == "hlv" and nk.get("ghi_chu_hlv"):
                st.caption(f"🔒 Ghi chú nội bộ: {nk['ghi_chu_hlv']}")
            if vai == "hlv" and nk.get("tinh_trang"):
                st.caption(f"🩺 Thể trạng: {nk['tinh_trang']}" + (f" · sẵn sàng {nk['san_sang']}/100" if nk.get("san_sang") else "")
                           + (f" · RPE buổi {nk['rpe']}" if nk.get("rpe") else ""))
            if (vai == "hlv" or nk.get("nguoi_ghi") == "khach") and st.button("🗑 Xoá buổi này", key=f"ls_x_{nk['id']}_{vai}"):
                ga.xoa_log(k["ma"], nk["id"], nguoi)
                st.rerun()


def so_ta(k: dict, L: list[dict]):
    ls = ga.lich_su_bai(k["ma"], L)
    if ls.empty:
        st.info("Ghi buổi tập đầu tiên để thấy số tạ, kỷ lục và biểu đồ tiến bộ.")
        return
    hom = pd.Timestamp(db.now_vn().date())
    tuan = ls[ls["ngay"] >= hom - pd.Timedelta(days=6)]
    ui.tiles([(str(len({x.get("id") for x in L})), "buổi đã ghi", ""),
              (str(ga.chuoi_tuan(L, db.now_vn().date())), "tuần liên tiếp", "có ít nhất 1 buổi"),
              (f"{tuan['volume'].sum():,.0f}".replace(",", "."), "kg tổng 7 ngày", "tạ × lần"),
              (str(ls["bai"].nunique()), "bài đã tập", "")])
    ui.sec("Kỷ lục từng bài")
    kl = ga.ky_luc(ls)
    st.dataframe(pd.DataFrame([{"Bài": r["bai"], "Hiệp tốt nhất": f"{r['top_kg']:g} kg × {int(r['top_lan'])}",
                                "1RM ước tính": f"{r['e1rm']:g} kg", "Ngày": r["ngay"].strftime("%d/%m/%Y")} for _, r in kl.iterrows()]),
                 hide_index=True, use_container_width=True)
    ui.sec("Biểu đồ tiến bộ")
    nhieu = ls["bai"].value_counts().index.tolist()
    chon = st.multiselect("Bài", nhieu, default=nhieu[:3], key=f"st_ch_{k['ma']}")
    kieu = st.segmented_control("Chỉ số", ["e1rm", "top_kg", "volume"], default="e1rm", key=f"st_k_{k['ma']}",
                                format_func={"e1rm": "1RM ước tính", "top_kg": "Tạ nặng nhất", "volume": "Tổng khối lượng"}.get) or "e1rm"
    if chon:
        fig = go.Figure()
        for i, b in enumerate(chon):
            g = ls[ls["bai"] == b]
            fig.add_scatter(x=g["ngay"], y=g[kieu], mode="lines+markers", name=b, line=dict(color=ui.PAL[i % len(ui.PAL)], width=3),
                            marker=dict(size=8))
        fig.update_xaxes(tickformat="%d/%m")
        st.plotly_chart(ui.layout(fig, 340, "kg"), use_container_width=True, config={"displayModeBar": False})
    st.caption("1RM ước tính theo công thức Epley (kg × (1 + lần / 30)) — để so tiến bộ của chính bạn, không phải để thử tạ tối đa.")


def tap_luyen(k: dict, vai: str, nguoi: str):
    ma = k["ma"]
    from core import ga_atlas
    G = [({**ga_atlas.to_simple(g, db.now_vn().date()), "_khoa": g["_khoa"]} if g.get("loai_ga") == "atlas" else g)
         for g in ga.plans(ma)]
    L = ga.logs(ma)
    t1, t2, t3, t4 = st.tabs(["📋 Giáo án", "✍️ Ghi buổi tập", "🏋️ Số tạ & kỷ lục", "🗓 Lịch sử"])
    with t1:
        sua = S.get(f"ga_sua_{ma}", False)
        lua = [g["_khoa"] for g in G]
        a, b, c = st.columns([3, 1, 1], vertical_alignment="bottom")
        if G:
            mac = S.get(f"ga_chon_{ma}") if S.get(f"ga_chon_{ma}") in lua else lua[0]
            gid = a.selectbox("Giáo án", lua, index=lua.index(mac), key=f"ga_sel_{ma}_{vai}",
                              format_func=lambda x: next((f"{'⭐ ' if g.get('dang_dung') else ''}{g.get('ten')} · "
                                                          f"{'HLV soạn' if g.get('tac_gia') == 'hlv' else 'tự tạo'}" for g in G if g['_khoa'] == x), x))
            S[f"ga_chon_{ma}"] = gid
            g = next(x for x in G if x["_khoa"] == gid)
        else:
            g = None
            a.caption("Chưa có giáo án." + ("" if vai == "hlv" else " Chờ HLV soạn, hoặc tự tạo plan của bạn."))
        duoc_sua = g is not None and g.get("loai_ga") != "atlas" and (vai == "hlv" or g.get("tac_gia") == "khach")
        if duoc_sua and b.button("✏️ Sửa" if not sua else "👁 Xem", key=f"ga_bsua_{ma}_{vai}", use_container_width=True):
            S[f"ga_sua_{ma}"] = not sua
            st.rerun()
        if c.button("➕ Tạo mới" if vai == "hlv" else "➕ Tự tạo plan", key=f"ga_moi_{ma}_{vai}", use_container_width=True):
            S[f"ga_sua_{ma}"] = "moi"
            st.rerun()
        if sua == "moi":
            sua_giao_an(k, vai, nguoi, None)
        elif sua and duoc_sua:
            sua_giao_an(k, vai, nguoi, g)
        elif g:
            xem_giao_an(k, g, L)
    with t2:
        ghi_buoi(k, vai, nguoi, G, L)
    with t3:
        so_ta(k, L)
    with t4:
        lich_su(k, vai, nguoi, L)


# =================================================================== CÂN HẰNG NGÀY
def bieu_do_can(k: dict, CAN: pd.DataFrame, h: int = 320):
    if not len(CAN):
        st.info("Chưa có lần cân nào.")
        return
    fig = go.Figure()
    fig.add_scatter(x=CAN["ngay"], y=CAN["kg"], mode="lines+markers", name="Cân từng ngày", line=dict(color=ui.XAM, width=1.5),
                    marker=dict(size=6))
    fig.add_scatter(x=CAN["ngay"], y=CAN["tb7"], mode="lines", name="Trung bình 7 ngày", line=dict(color=ui.VANG, width=3.5))
    if k.get("can_muc_tieu"):
        fig.add_hline(y=float(k["can_muc_tieu"]), line_dash="dot", line_color="#2E7D4F",
                      annotation_text=f"Mục tiêu {k['can_muc_tieu']} kg", annotation_position="bottom right")
    fig.update_xaxes(tickformat="%d/%m")
    st.plotly_chart(ui.layout(fig, h, "kg"), use_container_width=True, config={"displayModeBar": False})


def nhap_can(k: dict, nguoi: str, CAN: pd.DataFrame, key: str):
    hom = db.now_vn().date()
    with st.form(f"can_{k['ma']}_{key}", clear_on_submit=True):
        a, b, c = st.columns([1.2, 1, 1], vertical_alignment="bottom")
        nc = a.date_input("Ngày", hom, format="DD/MM/YYYY", max_value=hom, min_value=hom - timedelta(days=60))
        kg = b.number_input("Cân (kg)", 0.0, 250.0, float(CAN["kg"].iloc[-1]) if len(CAN) else 0.0, step=0.1, format="%.1f")
        if c.form_submit_button("💾 Lưu cân", type="primary", use_container_width=True):
            if kg <= 0:
                st.error("Nhập số cân.")
            elif td.luu_can(k["ma"], nc, kg, {"name": nguoi}):
                st.toast(f"Đã lưu {kg:.1f} kg ngày {nc:%d/%m}")
                st.rerun()
            else:
                st.error("Chưa lưu được — thử lại.")
    st.caption("Cân buổi sáng sau khi thức dậy, đi vệ sinh, trước khi ăn uống. Nhìn **đường vàng (trung bình 7 ngày)** — "
               "cân từng ngày dao động 0,5–1 kg do nước, muối là bình thường.")
