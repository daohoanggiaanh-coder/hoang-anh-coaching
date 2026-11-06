# Hoàng Anh Coaching v2.5 (2026-11-06) — TỔNG KẾT NGÀY: mọi hoạt động của khách trong 1 ngày (tập · cardio · bước chân · cân ·
# số đo · check-in · ăn uống · nhiệm vụ) — khách xem của mình, HLV xem từng khách + bảng tất cả khách.
from __future__ import annotations

import html
from datetime import date

import pandas as pd
import streamlit as st

from core import an_ngoai as an, buoi as bt, cardio as cd, db, dinh_duong as dd, dong_luc as dl, store, tien_do as td, wow

E = html.escape


def _dd_ctx(k: dict):
    from views import common as C
    hs = C.ho_so_dd(k)
    if not hs.get("cao") or not hs.get("kg"):
        return None
    h = dd.HoSo.tu_dict(hs)
    return h, dd.tinh(h), set(hs.get("bo_mon") or []), set(dd.ngay_tap_tuan(h))


def du_lieu(k: dict, d: date) -> dict:
    ma = k["ma"]
    out: dict = {"ngay": d}
    hist = bt.sessions(ma)
    ss = [s for s in hist if s["ngay"] == d]
    out["tap"] = []
    for s in ss:
        so_hiep = sum(len([h for h in b["hiep"] if (h.get("lan") or h.get("kg"))]) for b in s["bai"])
        out["tap"].append({"bai": len(s["bai"]), "hiep": so_hiep, "tan": bt.tonnage(s["bai"]),
                           "pr": wow.ky_luc_moi(s["bai"], [x for x in hist if x["ngay"] < d]),
                           "tinh_trang": s.get("tinh_trang") or "", "ten": [b.get("ten") for b in s["bai"]][:8]})
    out["cardio"] = [v for v in cd.logs(ma) if str(v.get("ngay"))[:10] == d.isoformat()]
    c = cd.cai_dat(ma)
    out["buoc"] = cd.buoc_logs(ma).get(d)
    from core import thong_tin as ttin
    out["buoc_tg"] = cd.buoc_muc_tieu(c, {"suc_khoe": "giu", "suc_manh": "giu"}.get(ttin.muc_tieu(k), ttin.muc_tieu(k)))
    CAN = td.can_ngay(ma)
    r = CAN[CAN["ngay"] == d] if not CAN.empty else CAN
    out["can"] = float(r["kg"].iloc[-1]) if len(r) else None
    SD = td.so_do(ma)
    out["so_do"] = None
    if not SD.empty:
        x = SD[SD["ngay"] == d]
        if len(x):
            out["so_do"] = {kk: x.iloc[-1][kk] for kk in ("v_eo", "v_mong", "v_dui", "pbf") if kk in x and pd.notna(x.iloc[-1][kk])}
    out["checkin"] = dl.checkins(ma).get(d)
    ctx = _dd_ctx(k)
    out["an"] = None
    if ctx:
        h, kq, bo, tap_set = ctx
        doi = st.session_state.get(f"dd_doi_{ma}", {})
        td_ = dd.thuc_don_ngay(h, kq, d.weekday() in tap_set, d.weekday(), ma, doi.get(d.weekday()), bo)
        m = kq["tap"] if d.weekday() in tap_set else kq["nghi"]
        logs = an.nhat_ky(ma, d)
        out["an"] = {"t": an.tong_ngay(td_, logs, m), "logs": logs, "so_bua": len(td_),
                     "ghi": len([v for v in logs.values() if v.get("loai") != "chua"])}
    try:
        t = dl.tong_hop(k, d, store.quyen(k))
        out["nv"] = [x for x in t["nv"]]
    except Exception:  # noqa: BLE001
        out["nv"] = []
    return out


def _o(icon: str, ten: str, gia_tri: str, phu: str = "", ok: bool | None = None) -> str:
    mau = "#2E7D4F" if ok else "#B4442F" if ok is False else "#8b8577"
    return (f'<div class="tk-o"><div class="tk-i">{icon}</div><div><div class="tk-t">{E(ten)}</div><div class="tk-v">{gia_tri}</div>'
            + (f'<div class="tk-p" style="color:{mau}">{phu}</div>' if phu else "") + "</div></div>")


CSS = """<style>
.tk-g{display:grid;grid-template-columns:repeat(auto-fill,minmax(210px,1fr));gap:10px;margin:8px 0 14px}
.tk-o{display:flex;gap:10px;border:1.5px solid #E7DFCF;border-radius:14px;padding:10px 12px;background:#FFFDF8}
html[data-hac-theme=dark] .tk-o{background:#1A1814;border-color:#3A342A}
.tk-i{font-size:1.5rem}.tk-t{font-size:.7rem;letter-spacing:.08em;font-weight:800;color:#8b8577;text-transform:uppercase}
.tk-v{font-size:1.05rem;font-weight:800}.tk-p{font-size:.76rem;font-weight:600}
</style>"""


def the_ngay(D: dict) -> str:
    o = []
    if D["tap"]:
        s = D["tap"][0]
        o.append(_o("🏋️", "Tập tạ", f"{s['bai']} bài · {s['hiep']} hiệp", f"tổng tạ {s['tan']:,.0f} kg".replace(",", ".")
                    + (f" · 🏆 {len(s['pr'])} kỷ lục" if s["pr"] else ""), True))
    else:
        o.append(_o("🏋️", "Tập tạ", "Không tập", "", None))
    ph = sum(float(v.get("phut") or 0) for v in D["cardio"])
    o.append(_o("🏃", "Cardio", f"{ph:.0f} phút" if ph else "—", ", ".join(dict.fromkeys(cd.MAY.get(v.get("may"), str(v.get("may") or "")) for v in D["cardio"]))[:40], ph > 0 if D["cardio"] else None))
    if D["buoc"] is not None:
        o.append(_o("👣", "Bước chân", f"{D['buoc']:,}".replace(",", "."), f"mục tiêu {D['buoc_tg']:,}".replace(",", "."), D["buoc"] >= D["buoc_tg"]))
    else:
        o.append(_o("👣", "Bước chân", "—", "chưa ghi", None))
    o.append(_o("⚖️", "Cân sáng", f"{D['can']:.1f} kg".replace(".", ",") if D["can"] else "—", "" if D["can"] else "chưa cân",
                bool(D["can"]) if D["can"] else None))
    if D["so_do"]:
        o.append(_o("📏", "Số đo", " · ".join(f"{v:g}" for v in D["so_do"].values()), "eo · mông · đùi · % mỡ", True))
    ck = D["checkin"]
    if ck:
        o.append(_o("📝", "Check-in", f"ngủ {ck.get('ngu', '—')} h · nước {ck.get('nuoc', '—')} L",
                    f"ăn đúng {ck.get('an', '—')}% · năng lượng {ck.get('nang_luong', '—')}", True))
    else:
        o.append(_o("📝", "Check-in", "—", "chưa check-in", None))
    if D["an"]:
        t = D["an"]["t"]
        o.append(_o("🍽", "Ăn uống", f"{t['da']['kcal']:,.0f} / {t['muc']['kcal']:,.0f} kcal".replace(",", "."),
                    f"đạm {t['da']['p']:.0f}/{t['muc']['p']:.0f} g · {D['an']['ghi']}/{D['an']['so_bua']} bữa đã ghi",
                    (abs(t["con"]["kcal"]) <= 0.12 * t["muc"]["kcal"] and t["con"]["p"] <= 15)
                    if D["an"]["ghi"] >= D["an"]["so_bua"] else None))
    xong = [x for x in D["nv"] if x.get("xong") and not x.get("phu")]
    chinh = [x for x in D["nv"] if not x.get("phu")]
    if chinh:
        o.append(_o("🔥", "Nhiệm vụ giữ lửa", f"{len(xong)}/{len(chinh)} việc", ", ".join(x["ten"] for x in chinh if not x.get("xong"))[:60]
                    or "đủ hết 👏", len(xong) == len(chinh)))
    return CSS + '<div class="tk-g">' + "".join(o) + "</div>"


def trang(k: dict, vai: str, nguoi: str = ""):
    hom = db.now_vn().date()
    d = st.date_input("Ngày", hom, max_value=hom, format="DD/MM/YYYY", key=f"tk_d_{k['ma']}_{vai}")
    D = du_lieu(k, d)
    st.markdown(the_ngay(D), unsafe_allow_html=True)
    if D["tap"]:
        s = D["tap"][0]
        with st.expander(f"🏋️ Buổi tập: {', '.join(x for x in s['ten'] if x)}"):
            for p in s["pr"]:
                st.markdown(f"🏆 **{E(p['bai'])}** {p['kg']:g} kg × {p['lan']} (+{p['tang']:g} kg 1RM ước tính)".replace(".", ","))
            if s["tinh_trang"]:
                st.caption("Thể trạng: " + s["tinh_trang"])
    if D["an"] and D["an"]["ghi"]:
        with st.expander("🍽 Các bữa đã ghi"):
            for b, v in D["an"]["logs"].items():
                if v.get("loai") == "chua":
                    continue
                st.markdown(f"- **{E(v.get('ten') or b)}** — {an.LOAI.get(v.get('loai'), '')}"
                            + (f" · {float(v.get('kcal') or 0):.0f} kcal · đạm {float(v.get('p') or 0):.0f} g" if v.get("loai") != "dung" else ""))
                if v.get("ai", {}).get("nhan_xet"):
                    st.caption("💬 " + v["ai"]["nhan_xet"])
    if vai == "hlv":
        from views.coach import _soan
        from views.cham_soc_ui import _gui_tg
        txt = st.text_area("Tin nhắn tổng kết ngày (sửa rồi gửi)", tin_ngay(k, D), height=150, key=f"tk_tin_{k['ma']}_{d}")
        _soan(k, txt, f"tk_{k['ma']}_{d}", {"name": nguoi}, hien=False)
        _gui_tg(k, txt, f"tk_{k['ma']}_{d}")


def tin_ngay(k: dict, D: dict) -> str:
    goi, toi = store.xung(k)
    G = goi[:1].upper() + goi[1:]
    dong = [f"{G} ơi, {toi} tổng kết ngày {D['ngay']:%d/%m} nè 👇"]
    if D["tap"]:
        s = D["tap"][0]
        dong.append(f"🏋️ Buổi tập {s['hiep']} hiệp, tổng tạ {s['tan']:,.0f} kg".replace(",", ".")
                    + (f" — có {len(s['pr'])} kỷ lục mới 🏆" if s["pr"] else "") + ".")
    ph = sum(float(v.get("phut") or 0) for v in D["cardio"])
    if ph:
        dong.append(f"🏃 Cardio {ph:.0f} phút.")
    if D["buoc"]:
        dong.append(f"👣 {D['buoc']:,} bước".replace(",", ".") + (" — đạt mục tiêu 👏" if D["buoc"] >= D["buoc_tg"] else
                                                                     f" (mục tiêu {D['buoc_tg']:,})".replace(",", ".")))
    if D["an"] and D["an"]["ghi"]:
        t = D["an"]["t"]
        dong.append(f"🍽 Ăn khoảng {t['da']['kcal']:,.0f}/{t['muc']['kcal']:,.0f} kcal, đạm {t['da']['p']:.0f}/{t['muc']['p']:.0f} g.".replace(",", "."))
        if t["con"]["p"] > 20:
            dong.append(f"Ngày mai mình thêm đạm nhé ({goi} còn thiếu khoảng {t['con']['p']:.0f} g).")
    chinh = [x for x in D["nv"] if not x.get("phu")]
    thieu = [x["ten"] for x in chinh if not x.get("xong")]
    dong.append("Đủ hết nhiệm vụ hôm nay, tuyệt vời! 🔥" if chinh and not thieu else
                (f"Còn thiếu: {', '.join(thieu)} — mai mình bù nhé." if thieu else ""))
    return "\n".join(x for x in dong if x)


def bang_tat_ca(DS: list[dict], d: date):
    rows = []
    for k in DS:
        try:
            D = du_lieu(k, d)
        except Exception:  # noqa: BLE001
            continue
        ph = sum(float(v.get("phut") or 0) for v in D["cardio"])
        chinh = [x for x in D["nv"] if not x.get("phu")]
        rows.append({"Khách": k["ho_ten"], "Tập": f"{D['tap'][0]['hiep']} hiệp" if D["tap"] else "—", "Cardio": f"{ph:.0f}′" if ph else "—",
                     "Bước": D["buoc"] or "—", "Cân": D["can"] or "—",
                     "Ăn (kcal)": f"{D['an']['t']['da']['kcal']:.0f}/{D['an']['t']['muc']['kcal']:.0f}" if D["an"] and D["an"]["ghi"] else "—",
                     "Check-in": "✅" if D["checkin"] else "—",
                     "Nhiệm vụ": f"{len([x for x in chinh if x.get('xong')])}/{len(chinh)}" if chinh else "—"})
    st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)

