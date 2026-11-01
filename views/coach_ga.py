# Hoàng Anh Coaching v1.1 (2026-10-31) — Giáo án HLV kiểu Atlas: giáo án tuần tự xếp theo mục tiêu, trình độ, số buổi,
# dạng lịch, vùng chấn thương (8 bài / buổi, theo lầu, superset bụng, kết buổi strongman / HIIT); bảng sửa từng buổi;
# đổi bài khi thiếu máy; ghi buổi với thể trạng đầu buổi + điểm sẵn sàng + gợi ý tạ. Chuyển từ Atlas Academy v3.64.
from __future__ import annotations

import html
from datetime import date, timedelta

import pandas as pd
import streamlit as st

from core import buoi as bt, ga_atlas as ga, store, the_trang as tt_, tu_van as tv
from views import common as C

E = html.escape
CSS = """<style>
div[class*="st-key-sets_"] [data-testid="stHorizontalBlock"]{flex-wrap:nowrap!important;gap:.4rem}
div[class*="st-key-sets_"] [data-testid="stColumn"]{min-width:0!important;width:auto!important}
div[class*="st-key-sets_"] [data-testid="stNumberInputStepDown"],div[class*="st-key-sets_"] [data-testid="stNumberInputStepUp"]{display:none}
div[class*="st-key-sets_"] input{text-align:center;font-weight:700}
div[class*="st-key-gx_"]{background:#fff;border:1px solid #E6DCC6;border-left:4px solid #A3803C;border-radius:16px;
  padding:14px 16px 8px;box-shadow:0 2px 10px rgba(28,27,25,.05)}
div[class*="st-key-sw_"] div[data-baseweb="select"]>div{border:1px dashed #D9CBA8!important;background:#FFFDF8!important;border-radius:10px;min-height:50px}
div[class*="st-key-sw_"] div[data-baseweb="select"] div, div[class*="st-key-sw_"] div[data-baseweb="select"] span{font-weight:800!important;
  font-size:1.18rem!important;color:#1C1B19!important}
.gx-tang{background:#F3ECDC;color:#7A5B14;font-size:.68rem;font-weight:800;border-radius:999px;padding:3px 9px;letter-spacing:.06em}
.gx-lau{display:flex;align-items:center;gap:10px;margin:14px 0 6px;color:#7A5B14;font-weight:900;font-size:.8rem;letter-spacing:.14em}
.gx-lau:before,.gx-lau:after{content:"";flex:1;height:1px;background:#D9CBA8}
div[class*="st-key-kb_"]{background:#1C1B19;border-radius:16px;padding:16px 18px;color:#F3ECDC}
div[class*="st-key-kb_"] label, div[class*="st-key-kb_"] p{color:#F3ECDC!important}
.gx-h{display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin-bottom:6px}
.gx-n{min-width:32px;height:32px;padding:0 6px;border-radius:999px;background:#1C1B19;color:#E8C76A;font-weight:800;
  display:inline-flex;align-items:center;justify-content:center;font-size:.8rem}
.gx-b{color:#fff;font-size:.64rem;font-weight:800;letter-spacing:.09em;padding:4px 10px;border-radius:999px;text-transform:uppercase}
.gx-eq{color:#8b8577;font-size:.76rem}.gx-sw{color:#A3803C;font-size:.74rem;font-weight:600}
.gx-chips{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin:8px 0 6px}
.gx-c{background:#FBF8F1;border:1px solid #EFE6D3;border-radius:12px;padding:7px 6px;text-align:center}
.gx-c small{display:block;font-size:.58rem;letter-spacing:.12em;color:#A3803C;font-weight:800;text-transform:uppercase}
.gx-c b{display:block;font-size:.98rem;color:#1C1B19;line-height:1.3}.gx-c i{display:block;font-size:.66rem;color:#8b8577;font-style:normal}
.gx-tip{font-size:.8rem;color:#5a5448;background:#F6F1E6;border-radius:10px;padding:6px 10px;margin:2px 0 8px;text-align:center}
.gx-th{display:grid;grid-template-columns:.55fr 1fr 1fr;gap:.4rem;font-size:.62rem;letter-spacing:.12em;color:#8b8577;
  font-weight:800;text-transform:uppercase;text-align:center;margin-bottom:2px}
.gs-h{display:flex;align-items:center;gap:10px;flex-wrap:wrap;background:#1C1B19;color:#fff;border-radius:14px;padding:10px 14px;margin:4px 0 8px}
.gs-ma{background:#E8C76A;color:#1C1B19;font-weight:900;font-size:.72rem;letter-spacing:.1em;border-radius:999px;padding:4px 10px}
.gs-t{font-weight:700}.gs-n{margin-left:auto;color:#D8D1C1;font-size:.78rem}
.gs-flow{font-size:.78rem;color:#6C6860;text-align:center;margin:4px 0 2px}
@media(max-width:640px){.gx-c b{font-size:.86rem}.gs-n{margin-left:0}}
html[data-hac-theme=dark] div[class*="st-key-gx_"]{background:#1A1814;border-color:#332E25;box-shadow:none}
html[data-hac-theme=dark] div[class*="st-key-sw_"] div[data-baseweb="select"]>div{background:#221F1A!important;border-color:#4A4234!important}
html[data-hac-theme=dark] div[class*="st-key-sw_"] div[data-baseweb="select"] div,
html[data-hac-theme=dark] div[class*="st-key-sw_"] div[data-baseweb="select"] span{color:#F3ECDC!important}
html[data-hac-theme=dark] .gx-c{background:#221F1A;border-color:#332E25}
html[data-hac-theme=dark] .gx-c b{color:#F3ECDC}
html[data-hac-theme=dark] :is(.gx-tip,.gx-tang){background:#2A251D;color:#D8CFBD}
html[data-hac-theme=dark] :is(.gx-lau,.gx-c small){color:#E2BE62}
html[data-hac-theme=dark] .gs-flow{color:#A8A091}
html[data-hac-theme=dark] div[class*="st-key-kb_"]{background:#080706;border:1px solid #332E25}
</style>"""


def _ten(eid):
    return ga.ex(eid)["ten"]


def _cc(fn, *a, **kw):
    try:
        return fn(*a, alignment="center", **kw)
    except TypeError:
        return fn(*a, **kw)


def _flow(bai: list[dict]) -> str:
    nh = ga.nhan_ss(bai)
    return " → ".join(f"<b>{n_}</b> {E(it['ten'].split('(')[0].strip())}" if n_ else E(it["ten"].split("(")[0].strip())
                      for n_, it in zip(nh, bai))


def _chip(nhan: str, gia: str, phu: str = "") -> str:
    return f'<div class="gx-c"><small>{E(nhan)}</small><b>{E(gia or "—")}</b>' + (f"<i>{E(phu)}</i>" if phu else "") + "</div>"


def _sig(x: dict | None) -> tuple:
    x = x or {}
    return (x.get("muc_tieu"), int(x.get("trinh_do") or 0), min(max(int(x.get("buoi_tuan") or 3), 2), 5),
            tuple(sorted(x.get("han_che") or [])), x.get("kieu") or "auto")


def trang(user: dict, k: dict):
    S = st.session_state
    ma = k["ma"]
    st.markdown(CSS, unsafe_allow_html=True)
    plan = ga.current(ma)
    H = store.hens(ma)
    da = store.da_tap(k, H)
    tong = int(float(k.get("goi_buoi") or 0)) if store.loai_goi(k) == "buoi" else 0
    week = ga.week_no(plan["ngay_bat_dau"], bt.today()) if plan else 1
    CT = ga.guess_limits(k.get("chan_thuong"))
    st.markdown(f'<div style="font-size:.85rem;color:#8b8577;margin:-4px 0 6px">{E(k.get("muc_tieu") or "chưa ghi mục tiêu")} · '
                f'đã tập {da}' + (f'/{tong}' if tong else '') + f' buổi · {E(store.mo_ta_goi(k, H))}' + (f' · tuần {week} · {ga.PHASES[ga.phase_of(week)]}' if plan else "") + "</div>",
                unsafe_allow_html=True)
    if CT or k.get("chan_thuong"):
        st.markdown(f'<div style="background:#FDECEA;border:1px solid #E6A49B;border-left:5px solid #C0392B;border-radius:12px;'
                    f'padding:10px 14px;margin:6px 0"><b style="color:#C0392B">⚠️ CHẤN THƯƠNG: {E(", ".join(CT) or "xem ghi chú")}</b> — '
                    f'giáo án và bài thay thế tự tránh bài hại vùng này.<br><span style="font-size:.85rem">{E(str(k.get("chan_thuong") or ""))}</span>'
                    "</div>", unsafe_allow_html=True)
    DKEY, LKEY, VKEY = f"_ga_draft_{ma}", f"_ga_live_{ma}", f"_ga_ver_{ma}"

    def _reset():
        S[VKEY] = S.get(VKEY, 0) + 1

    def _luu(info: dict) -> bool:
        ok = ga.save(ma, {**info, "ngay_bat_dau": info.get("ngay_bat_dau") or date.today().isoformat()}, info["buoi"], user["name"])
        if ok:
            S.pop(DKEY, None)
            S.pop(LKEY, None)
            _reset()
        return ok

    t1, t2, t3, t4 = st.tabs(["✍️ Ghi buổi tập", "🗓 Giáo án tuần", "🏋️ Số tạ & lịch sử", "📱 Plan khách tự tạo"])

    # ============================================================== giáo án tuần
    with t2:
        base = S.get(DKEY) or plan
        with st.container(border=True):
            st.markdown("**Thông số giáo án** · đổi ô nào giáo án tự xếp lại ngay")
            a, b, c = st.columns(3)
            gks = list(ga.GOALS)
            g0 = base["muc_tieu"] if base else ga.guess_goal(k.get("muc_tieu"))
            goal = a.selectbox("Mục tiêu", gks, index=gks.index(g0) if g0 in gks else 0, format_func=ga.GOALS.get, key=f"g_{ma}")
            lv = b.select_slider("Trình độ", list(range(5)), value=base["trinh_do"] if base else 0,
                                 format_func=lambda i: ga.LEVELS[i], key=f"lv_{ma}")
            pw = c.select_slider("Số buổi / tuần", [2, 3, 4, 5], value=min(max(base["buoi_tuan"], 2), 5) if base else
                                 min(max(len(store.lich_co_dinh(k)) or 3, 2), 5), key=f"pw_{ma}")
            a, b = st.columns([1.3, 1])
            kks = list(ga.KIEU_LICH)
            k0 = (base or {}).get("kieu") or ("mong_nu" if (k.get("gioi_tinh") == "Nữ" and "mông" in str(k.get("muc_tieu", "")).lower())
                                               else "auto")
            kieu = a.selectbox("Dạng lịch", kks, index=kks.index(k0) if k0 in kks else 0, format_func=ga.KIEU_LICH.get, key=f"kieu_{ma}")
            try:
                d0 = date.fromisoformat(base["ngay_bat_dau"]) if base and base.get("ngay_bat_dau") else \
                    date.fromisoformat(str(k.get("ngay_bat_dau"))[:10])
            except ValueError:
                d0 = date.today()
            start = b.date_input("Bắt đầu chương trình", value=d0, format="DD/MM/YYYY", key=f"st_{ma}")
            if ga.KIEU_MO_TA.get(kieu):
                st.caption(ga.KIEU_MO_TA[kieu])
            if kieu in ga.CHU_KY or (kieu == "auto" and pw >= 4):
                n_ck = len(ga.KIEU_SPLIT.get(kieu, {}).get(pw) or ga.SPLIT[pw])
                st.caption(f"🔁 Chu kỳ {n_ck} buổi tập lần lượt, không phụ thuộc tuần: khách tập {pw} buổi/tuần thì buổi chưa tập "
                           "nối sang đầu tuần sau — mỗi kiểu buổi vẫn đủ 2 biến thể.")
            lim = st.multiselect("Vùng cần tránh (chấn thương, đau)", list(ga.HAN_CHE), placeholder="Không có",
                                 default=base["han_che"] if base else CT, key=f"lim_{ma}")
        if set(CT) - set(lim):
            st.warning(f"Hồ sơ khách có chấn thương **{', '.join(sorted(set(CT) - set(lim)))}** nhưng giáo án chưa tránh — "
                       "thêm vào ô “Vùng cần tránh” để xếp lại.")
        params = {"muc_tieu": goal, "trinh_do": lv, "buoi_tuan": pw, "han_che": lim, "kieu": kieu}
        xep = base and st.button("🔄 Xếp lại theo mẫu (8 bài / buổi, chu kỳ)", key=f"xep_{ma}")
        if not base or _sig(base) != _sig(params) or xep:
            S[DKEY] = {**params, "ngay_bat_dau": start.isoformat(), "ghi_chu": (base or {}).get("ghi_chu", ""), "pt": user["name"],
                       "buoi": ga.generate(goal, lv, pw, k.get("gioi_tinh") or "Nam", lim, kieu)}
            _reset()
            if base:
                st.toast(f"Đã xếp lại giáo án: {ga.KIEU_LICH.get(kieu, kieu)}")
        work = S.get(DKEY) or plan
        ver = S.get(VKEY, 0)
        wk = ga.week_no(start, bt.today())
        st.markdown(f'<div class="gs-flow">Tuần {wk} · {ga.PHASES[ga.phase_of(wk)]} · liều tự đổi theo giai đoạn (tuần 1–4 · 5–8 · 9–12) · '
                    f'Cardio: {E(ga.cardio(goal, wk))}</div>', unsafe_allow_html=True)
        st.caption("✏️ Bấm thẳng vào ô để sửa: **Bài** · **Hiệp × lần** (VD 4x8, 3x12–15, 3x40 giây) · **RPE** (VD 7–8) · **Nghỉ** · "
                   "**STT** · **SS** = superset, ghi cùng chữ A / B cho các bài tập liền nhau. Thêm bài ở dòng trống cuối bảng.")
        lib = tv.library()["nhom"]
        ten_ok = [b_["ten"] for nh in lib for b_ in sorted(lib[nh]["bai"], key=lambda b_: ga.do_kho(b_["id"])) if ga.allowed(b_["id"], lv, lim)]
        ten_ok += [it["ten"] for bu in work["buoi"] for it in bu["bai"] if it["ten"] not in ten_ok]
        cfg = {"STT": _cc(st.column_config.NumberColumn, "STT", min_value=1, max_value=30, step=1, width="small"),
               "Bài": st.column_config.SelectboxColumn("Bài tập", options=ten_ok, required=True, width="medium"),
               "Dạng": _cc(st.column_config.TextColumn, "Dạng", disabled=True, width="small"),
               "Lầu": _cc(st.column_config.TextColumn, "Lầu", disabled=True, width="small", help="Tầng máy (phong cách Atlas)"),
               "Superset": _cc(st.column_config.TextColumn, "SS", max_chars=2, width="small"),
               "Hiệp × lần": _cc(st.column_config.TextColumn, "Hiệp × lần", width="small"),
               "RPE": _cc(st.column_config.TextColumn, "RPE", width="small"),
               "Nghỉ": _cc(st.column_config.TextColumn, "Nghỉ", width="small")}
        new_plan = []
        for bu in work["buoi"]:
            st.markdown(f'<div class="gs-h"><span class="gs-ma">BUỔI {E(str(bu["ma"]))}</span><span class="gs-t">{E(bu["ten"])}</span>'
                        f'<span class="gs-n">{len(bu["bai"])} bài' + (" · mạch bài" if bu.get("circuit") else "") + "</span></div>",
                        unsafe_allow_html=True)
            ed = st.data_editor(pd.DataFrame(ga.bang_buoi(bu, goal, wk, lv)), column_config=cfg, num_rows="dynamic",
                                hide_index=True, use_container_width=True, key=f"de_{ma}_{bu['ma']}_{ver}_{wk}")
            nb = ga.tu_bang(bu, ed.to_dict("records"), goal, wk, lv)
            st.markdown(f'<div class="gs-flow">{_flow(nb["bai"])}</div>', unsafe_allow_html=True)
            new_plan.append(nb)
        live = {**work, **params, "ngay_bat_dau": start.isoformat(), "buoi": new_plan}
        S[LKEY] = live
        with st.expander("🔁 Không có máy / máy hỏng → đổi bài tương đương cả giáo án"):
            st.caption("Đổi sang bài cùng nhóm cơ (bài cô lập: cùng cơ đích), cùng dạng, độ khó gần nhất, tránh vùng chấn thương; "
                       "giữ nguyên hiệp × lần, RPE, nghỉ và superset.")
            co = {it["id"]: it["ten"] for bu in new_plan for it in bu["bai"]}
            dcs = sorted({ga.ex(x).get("dung_cu") or "" for x in co} - {""})
            a, b = st.columns(2)
            bo = a.multiselect("Bài cần đổi", list(co), format_func=co.get, key=f"bo_{ma}_{ver}", placeholder="Chọn bài")
            dc = b.multiselect("Hoặc cả loại máy / dụng cụ", dcs, key=f"dc_{ma}_{ver}", placeholder="VD Cáp, Smith…")
            if st.button("🔁 Đổi bài", key=f"doi_{ma}", disabled=not (bo or dc)):
                moi, doi = ga.doi_bai(new_plan, set(bo), lv, lim, set(dc))
                if doi:
                    S[DKEY] = {**live, "buoi": moi}
                    _reset()
                    S["_ga_doi"] = doi
                    st.rerun()
                st.warning("Không tìm được bài thay phù hợp — chọn bài khác trong bảng.")
        if S.get("_ga_doi"):
            st.success("Đã đổi: " + " · ".join(f"{a_} → **{b_}**" for a_, b_ in S.pop("_ga_doi")))
        for w in ga.check(new_plan, kieu):
            st.warning(w)
        chua_luu = not plan or plan["buoi"] != new_plan or _sig(plan) != _sig(params) or str(plan.get("ngay_bat_dau"))[:10] != start.isoformat()
        note = st.text_input("Ghi chú giáo án (khách thấy — VD khởi động, lưu ý kỹ thuật)", value=work.get("ghi_chu", ""), key=f"gc_{ma}")
        a, b = st.columns([1.4, 1])
        if a.button("💾 Lưu giáo án" + (" (có thay đổi chưa lưu)" if chua_luu else ""), type="primary" if chua_luu else "secondary",
                    use_container_width=True, key=f"save_{ma}"):
            if _luu({**live, "ghi_chu": note}):
                st.toast("Đã lưu giáo án — khách thấy ngay trên cổng khách")
                st.rerun()
            st.error("Chưa lưu được — kiểm tra kết nối rồi thử lại.")
        if plan and chua_luu and b.button("↩️ Quay về bản đã lưu", use_container_width=True, key=f"undo_{ma}"):
            S.pop(DKEY, None)
            S.pop(LKEY, None)
            for kk in (f"g_{ma}", f"lv_{ma}", f"pw_{ma}", f"kieu_{ma}", f"lim_{ma}", f"st_{ma}"):
                S.pop(kk, None)
            _reset()
            st.rerun()
        if plan and plan.get("thoi_gian"):
            st.caption(f"Bản đang dùng lưu lúc {plan['thoi_gian'][:16]}.")

    # ============================================================== ghi buổi tập
    with t1:
        if S.get("_ga_flash"):
            st.success(S.pop("_ga_flash"))
        P_ = S.get(LKEY) or plan
        if not P_:
            st.info("Chọn thông số ở tab **🗓 Giáo án tuần** — giáo án tự xếp, rồi quay lại đây để ghi buổi.")
        else:
            chua = not plan or plan["buoi"] != P_["buoi"] or _sig(plan) != _sig(P_)
            if chua:
                a, b = st.columns([2.2, 1], vertical_alignment="center")
                a.warning(f"Đang theo giáo án **{ga.KIEU_LICH.get(P_.get('kieu') or 'auto', '')}** vừa sửa, chưa lưu. "
                          "Kết thúc buổi sẽ lưu luôn giáo án này.")
                if b.button("💾 Lưu giáo án", key=f"save1_{ma}", use_container_width=True):
                    if _luu(P_):
                        st.toast("Đã lưu giáo án")
                        st.rerun()
            ghi_buoi(k, P_, user["name"], "hlv", chua, _luu)

    with t3:
        from core import giao_an as gsimple
        L = gsimple.logs(ma)
        C.so_ta(k, L)
        ui_sec = st.markdown
        ui_sec("**Lịch sử buổi** (cả buổi HLV ghi và khách tự ghi)")
        C.lich_su(k, "hlv", user["name"], L)

    with t4:
        from core import giao_an as gsimple
        tu = [g for g in gsimple.plans(ma) if g.get("tac_gia") == "khach"]
        if not tu:
            st.caption("Khách chưa tự tạo plan nào.")
        for g in tu:
            with st.expander(f"{g.get('ten')} · tạo lúc {str(g.get('_luc'))[:16]}"):
                C.xem_giao_an(k, g, gsimple.logs(ma))


@st.fragment
def ghi_buoi(k: dict, P_: dict, nguoi: str, vai: str = "hlv", chua_luu: bool = False, luu=None):
    """Ghi buổi theo giáo án Atlas — dùng chung HLV và khách (khách: không có ghi chú nội bộ / lời nhắn / trừ buổi gói)."""
    S = st.session_state
    st.markdown(CSS, unsafe_allow_html=True)
    ma = k["ma"]
    km = ma if vai == "hlv" else f"{ma}_kh"
    hlv = vai == "hlv"
    hist = bt.sessions(ma)
    CT = ga.guess_limits(k.get("chan_thuong"))
    H = store.hens(ma)
    da = store.da_tap(k, H)
    tong = int(float(k.get("goi_buoi") or 0)) if store.loai_goi(k) == "buoi" else 0
    if not hlv and S.get(f"_ga_flash_{km}"):
        st.success(S.pop(f"_ga_flash_{km}"))
        st.balloons()
    mas = [b_["ma"] for b_ in P_["buoi"]]
    nx = ga.buoi_tiep(P_, hist)
    a, b = st.columns([2, 1])
    bm = a.radio("Buổi hôm nay", mas, index=mas.index(nx["ma"]), horizontal=True, key=f"bm_{km}",
                 format_func=lambda m: f"Buổi {m} · " + next(x["ten"] for x in P_["buoi"] if x["ma"] == m).split("·")[0].strip())
    ngay = b.date_input("Ngày", value=bt.today(), format="DD/MM/YYYY", key=f"ng_{km}")
    bu = next(x for x in P_["buoi"] if x["ma"] == bm)
    wk = ga.week_no(P_["ngay_bat_dau"], ngay)
    if len(mas) > 1:
        st.markdown('<div class="gs-flow">Chu kỳ ' + " → ".join(f"<b>{m}</b>" if m == nx["ma"] else m for m in mas)
                    + f" · hôm nay theo chu kỳ là <b>buổi {nx['ma']}</b></div>", unsafe_allow_html=True)
    ops = tt_.lua_chon(k.get("gioi_tinh") or "")
    with st.expander("📋 Chấm điểm sẵn sàng tập — 4 câu, 15 giây (khuyên dùng)", expanded=False):
        cs = st.columns(4)
        tl = {ma_: cs[i].select_slider(ten_, options=[1, 2, 3, 4, 5], value=3, format_func=lambda v, o=ops_: o[v - 1],
                                       key=f"ss_{km}_{bm}_{ma_}") for i, (ma_, ten_, ops_) in enumerate(tt_.CAU)}
        diem_, de_xuat = tt_.diem_san_sang(tl)
        x1, x2 = st.columns([1.2, 1], vertical_alignment="center")
        x1.markdown(f'<div style="display:flex;align-items:center;gap:12px"><div style="width:64px;height:64px;border-radius:50%;'
                    f'border:6px solid {tt_.mau_diem(diem_)};display:grid;place-items:center;font-weight:900;font-size:1.2rem">{diem_}</div>'
                    f'<div><b>Điểm sẵn sàng {diem_}/100</b><br><span style="color:#8b8577;font-size:.85rem">Đề xuất: '
                    f'{tt_.TINH_TRANG[de_xuat]["icon"]} {de_xuat}</span></div></div>', unsafe_allow_html=True)
        if x2.button("Áp dụng đề xuất", key=f"ssok_{km}_{bm}", use_container_width=True, type="primary"):
            S[f"tt_{km}_{bm}"] = de_xuat
            S[f"ssd_{km}"] = diem_
            st.rerun(scope="fragment")
    tts = st.pills("🩺 Hôm nay " + ("khách" if hlv else "bạn") + " thấy thế nào?", ops, default=None if f"tt_{km}_{bm}" in S else "Khoẻ", key=f"tt_{km}_{bm}",
                   format_func=lambda x: f"{tt_.TINH_TRANG[x]['icon']} {x}") or "Khoẻ"
    cf = tt_.get(tts)
    mu, mau_ = tt_.MUC[cf["muc"]]
    st.markdown(f'<div style="display:flex;gap:10px;align-items:flex-start;border:1px solid {mau_}55;background:{mau_}12;'
                f'border-radius:14px;padding:10px 14px;margin:2px 0 8px"><span style="background:{mau_};color:#fff;font-weight:800;'
                f'font-size:.66rem;letter-spacing:.08em;border-radius:999px;padding:4px 10px;white-space:nowrap">{mu}</span>'
                f'<span style="font-size:.86rem;color:#2b2822">{E(cf["loi"])}'
                + (f' <b>Tạ gợi ý ×{cf["kg"]:.2f}'.replace(".", ",") + (f", −{cf['hiep']} hiệp" if cf["hiep"] else "") + "</b>"
                   if cf["kg"] < 1 else "") + "</span></div>", unsafe_allow_html=True)
    nhe = cf.get("nhe") and st.toggle("🔄 Đổi sang buổi phục hồi nhẹ (không tính vào chu kỳ giáo án)", value=True, key=f"nhe_{km}_{bm}")
    if nhe:
        bu = ga.buoi_nhe(P_["trinh_do"], P_.get("han_che"))
    elif cf.get("core_nhe"):
        co_ = {x["id"] for x in bu["bai"]}
        nhe_ = [c for c in tt_.CORE_NHE if c not in co_]
        moi_ = []
        for x in bu["bai"]:
            if x["id"] in tt_.CORE_NANG and nhe_:
                e_ = ga.ex(nhe_.pop(0))
                x = {**x, **{q: e_[q] for q in ("id", "ten", "nhom", "loai", "dung_cu")}, "thay_cho": x["ten"]}
            moi_.append(x)
        bu = {**bu, "bai": moi_}
    tkey = ops.index(tts) if tts in ops else 0
    bm_luu = bu["ma"]
    st.markdown(f'<div class="gs-h"><span class="gs-ma">{"PHỤC HỒI" if bm_luu == "PH" else "BUỔI " + E(str(bm))}</span>'
                f'<span class="gs-t">{E(bu["ten"])}</span><span class="gs-n">Tuần {wk} · {E(ga.PHASES[ga.phase_of(wk)])}</span></div>',
                unsafe_allow_html=True)
    st.caption("Bấm vào **tên bài** để đổi sang bài tương đương. Ghi kg và số lần thực tế từng hiệp; để trống hiệp không tập.")
    nhan = ga.nhan_ss(bu["bai"])
    ids = {it["id"] for it in bu["bai"]}
    lau_cur = None
    bai = []
    for j, it0 in enumerate(bu["bai"]):
        lim_ = sorted(set(P_.get("han_che") or []) | set(CT))
        alt = [it0["id"]] + ga.ung_vien(it0["id"], ids, P_["trinh_do"], lim_, n=8)
        t_ = ga.tang(it0["id"])
        if t_ and t_ != lau_cur and it0.get("loai") not in ("S", "T"):
            st.markdown(f'<div class="gx-lau">{"⬇️" if t_ == 1 else "⬆️"} LẦU {t_}</div>', unsafe_allow_html=True)
            lau_cur = t_
        if it0.get("loai") in ("S", "T") and lau_cur != "ket":
            st.markdown('<div class="gx-lau">🔥 KẾT BUỔI</div>', unsafe_allow_html=True)
            lau_cur = "ket"
        with st.container(key=f"gx_{km}_{bm_luu}_{j}"):
            head = st.empty()
            eid = st.selectbox("Bài tập", alt, key=f"sw_{km}_{bm_luu}_{j}", label_visibility="collapsed",
                               format_func=lambda x, o=it0["id"]: _ten(x) if x == o else
                               f"↺ {_ten(x)}  ·  {ga.dang(x)[0]} · {ga.ex(x).get('dung_cu', '')}")
            e = ga.ex(eid)
            it = it0 if eid == it0["id"] else {**it0, **{x: e[x] for x in ("id", "ten", "nhom", "loai", "dung_cu")},
                                                "thay_cho": it0.get("thay_cho") or it0["ten"]}
            r = ga.rx(it, P_["muc_tieu"], wk, P_["trinh_do"])
            dg, mau = ga.dang(it.get("loai") or eid)
            so = nhan[j] or str(j + 1)
            head.markdown(f'<div class="gx-h"><span class="gx-n">{E(so)}</span><span class="gx-b" style="background:{mau}">{E(dg)}</span>'
                          + (f'<span class="gx-tang">LẦU {ga.tang(eid)}</span>' if ga.tang(eid) else "")
                          + f'<span class="gx-eq">{E(str(e.get("dung_cu") or ""))}</span>'
                          + (f'<span class="gx-sw">↺ thay cho {E(it["thay_cho"])}</span>' if it.get("thay_cho") else "")
                          + "".join(f'<span class="gx-b" style="background:#C0392B">⚠️ hại {E(v)}</span>' for v in CT
                                    if eid in ga.HAN_CHE.get(v, set())) + "</div>", unsafe_allow_html=True)
            ke = nhan[j + 1] if j + 1 < len(nhan) else ""
            if nhan[j] and ke[:1] == nhan[j][:1]:
                nghi, phu_n = f"→ {ke}", "chuyển ngay, không nghỉ"
            else:
                nghi, phu_n = r["nghi"], ("sau cả cặp superset" if nhan[j] else "giữa các hiệp")
            rir = r["rir"] if r["rir"] and r["rir"] != r["rpe"] else ""
            rpe_ = tt_.rpe(r["rpe"], tts)
            if rpe_ != r["rpe"]:
                rir = f"giảm theo thể trạng (gốc {r['rpe']})"
            st.markdown('<div class="gx-chips">' + _chip("Mục tiêu", r["lieu"], "hiệp × lần")
                        + _chip("Cường độ", rpe_ or ("—" if not rir else "Kỹ thuật"), rir)
                        + _chip("Nghỉ", nghi, phu_n) + "</div>", unsafe_allow_html=True)
            giay = "giây" in r["lieu"]
            try:
                n_set = int(r["lieu"].split("×")[0].split("–")[-1])
            except ValueError:
                n_set = 3
            n_set = tt_.so_hiep(n_set, tts, it.get("loai", ""))
            met = r["lieu"].rstrip().endswith(" m")
            last = bt.last_for(ma, eid, hist)
            sg = bt.suggest(it, r["lieu"], last)
            if sg:
                st.markdown(f'<div class="gx-tip">💡 {E(sg)}</div>', unsafe_allow_html=True)
            box = st.container(key=f"sets_{km}_{bm_luu}_{j}")
            box.markdown(f'<div class="gx-th"><span>Hiệp</span><span>{"" if giay else "kg"}</span>'
                         f'<span>{"giây" if giay else "mét" if met else "lần"}</span></div>', unsafe_allow_html=True)
            tk = None if giay else tt_.kg_goi_y(bt.target_kg(it, r["lieu"], last), tts, it.get("loai", ""), bt._step(it))
            hs = []
            for si in range(n_set):
                c1, c2, c3 = box.columns([0.55, 1, 1], vertical_alignment="center")
                c1.markdown(f"<div style='text-align:center;color:#8b8577;font-weight:700'>{si + 1}</div>", unsafe_allow_html=True)
                kg = None if giay else c2.number_input("kg", 0.0, 400.0, value=tk, step=0.5, format="%.1f",
                                                       key=f"kg_{km}_{bm_luu}_{j}_{eid}_{si}_{tkey}", placeholder="kg",
                                                       label_visibility="collapsed")
                lan = c3.number_input("lần", 0, 600, value=None, step=1, key=f"ln_{km}_{bm_luu}_{j}_{eid}_{si}",
                                      placeholder="giây" if giay else "mét" if met else "lần", label_visibility="collapsed")
                if lan:
                    hs.append({"kg": kg or 0, "lan": lan})
            gc = st.text_input("Ghi chú bài", key=f"gcb_{km}_{bm_luu}_{j}", placeholder="Ghi chú bài (VD đau nhẹ gối, đổi tay cầm…)",
                               label_visibility="collapsed")
            bai.append({"id": eid, "ten": it["ten"], "hiep": hs, "ghi_chu": gc, "giay": giay,
                        **({"thay_cho": it["thay_cho"]} if it.get("thay_cho") else {}), **({"ss": nhan[j]} if nhan[j] else {})})
    with st.container(key=f"kb_{km}_{bm}"):
        st.markdown("**🏁 Kết buổi**")
        cardio = st.text_input("Cardio", value=ga.cardio(P_["muc_tieu"], wk), key=f"cd_{km}_{bm}")
        a, b = st.columns(2)
        cam = a.select_slider("Khách cảm thấy" if hlv else "Bạn cảm thấy", bt.CAM_NHAN, value="Bình thường", key=f"cn_{km}_{bm}")
        rpe = b.slider("Độ nặng cả buổi (RPE 1–10)", 1, 10, 7, key=f"rpe_{km}_{bm}")
        ghi_pt, loi, gkh, tru = "", "", "", False
        if hlv:
            ghi_pt = st.text_input("Ghi chú nội bộ (khách KHÔNG thấy)", key=f"gpt_{km}_{bm}")
            loi = st.text_area("Lời nhắn gửi khách (khách thấy trong lịch sử buổi)", height=70, key=f"loi_{km}_{bm}",
                               placeholder="VD Hôm nay squat chắc hơn hẳn! Tối nay nhớ ăn đủ đạm, ngủ trước 23h.")
            tru = st.checkbox("Tính 1 buổi trong gói (đánh dấu Đã tập trên lịch)", value=True, key=f"tru_{km}_{bm}")
        else:
            gkh = st.text_area("Gửi HLV (không bắt buộc)", height=70, key=f"gkh_{km}_{bm}",
                               placeholder="VD Hôm nay gối hơi đau ở bài lunge, squat thấy nhẹ hơn tuần trước")
        done = st.button("✅ Kết thúc buổi & lưu" + (" (lưu luôn giáo án mới)" if chua_luu else ""), type="primary",
                         use_container_width=True, key=f"done_{km}_{bm}")
    if done:
        if not any(x["hiep"] for x in bai):
            st.error("Chưa ghi hiệp nào — nhập ít nhất số lần của 1 bài.")
            return
        if chua_luu and not luu(P_):
            st.error("Chưa lưu được giáo án — kiểm tra kết nối rồi bấm lại.")
            return
        s_ = {"ngay": ngay, "ga_id": ga.KHOA.format(ma), "buoi": f"Buổi {bm_luu} · {bu['ten']}", "buoi_ma": bm_luu, "tuan": wk,
              "tinh_trang": tts, "san_sang": S.get(f"ssd_{km}", ""), "bai": bai, "cardio": cardio, "cam_nhan": cam,
              "rpe": rpe, "ghi_chu_hlv": ghi_pt, "loi_nhan": loi, "thoi_luong": 60, "nguoi_ghi": vai,
              **({"ghi_chu": gkh.strip()} if gkh.strip() else {})}
        bt.save(ma, s_, nguoi)
        if tru:
            hom = [x for x in store.buoi([k], ngay, ngay, H) if x["trang_thai"] == "hen"]
            if hom:
                store.ghi_hen(ma, ngay, hom[0]["gio"], "xong", nguoi, hom[0].get("dia_diem", ""), goc=hom[0]["id"])
            elif not [x for x in store.buoi([k], ngay, ngay, H) if x["trang_thai"] == "xong"]:
                store.ghi_hen(ma, ngay, "—", "xong", nguoi, k.get("dia_diem", ""), "ghi từ giáo án")
        for kk in [x for x in S if str(x).startswith((f"kg_{km}_", f"ln_{km}_", f"gcb_{km}_", f"loi_{km}_", f"sw_{km}_", f"bm_{km}",
                                                      f"tt_{km}_", f"nhe_{km}_", f"gpt_{km}_", f"gkh_{km}_"))]:
            S.pop(kk, None)
        con = max(tong - da - (1 if tru else 0), 0) if tong else None
        S["_ga_flash" if hlv else f"_ga_flash_{km}"] = (f"Đã lưu buổi {bm_luu}" + (f" — gói còn {con} buổi" if con is not None else "")
                                                        if hlv else f"💪 Đã lưu buổi {bm_luu} — HLV sẽ xem và nhận xét. +30 điểm 🔥")
        st.rerun()


def _ngay_tuan(d: date) -> date:
    return d - timedelta(days=d.weekday())
