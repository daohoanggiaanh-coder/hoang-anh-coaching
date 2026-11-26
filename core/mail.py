"""v4.2 — EMAIL BÁO CÁO cho HLV: sau mỗi buổi tập (so với buổi trước) + tổng kết cuối ngày.

Gửi qua Apps Script (MailApp) về CHÍNH Gmail chủ database — web không giữ mật khẩu email nào.
Chạy thử (không có SHEETS_WEBAPP_URL) → lưu file HTML vào data/_local/mail/ để xem trước.
"""
from __future__ import annotations

import html
import threading
from datetime import date, timedelta

import requests

from core import buoi as bt, config, db, goi, lo_trinh as lt, store, tang_tien as tt, tien_do as td, tu_van as tv

E = html.escape
KHOA = "mail|cai_dat"
MAC_DINH = {"sau_buoi": True, "khach_tu_ghi": True, "cuoi_ngay": True}
VANG, XANH, DO, CAM, XAM = "#B8902F", "#2E7D4F", "#C0392B", "#D9822B", "#8A8478"


# ------------------------------------------------------------------ cài đặt + gửi
def cai_dat() -> dict:
    try:
        v = db.latest("DinhDuong").get(KHOA) or {}
    except Exception:  # noqa: BLE001
        v = {}
    return {**MAC_DINH, **{k: v[k] for k in MAC_DINH if k in v}}


def luu_cai_dat(v: dict, nguoi: str) -> bool:
    return db.append("DinhDuong", KHOA, {k: bool(v.get(k)) for k in MAC_DINH}, nguoi)


def _ket_noi() -> tuple[str | None, str]:
    return db._url(), db._token()


def kiem_tra() -> dict:
    """{ok, email, con_lai} — Apps Script đã có chức năng mail chưa."""
    url, tok = _ket_noi()
    if not url:
        return {"ok": True, "email": "(chạy thử — lưu file HTML)", "con_lai": None, "thu": True}
    try:
        r = requests.get(url, timeout=25, params={"token": tok, "action": "mail_info"}).json()
    except (requests.RequestException, ValueError) as e:
        return {"ok": False, "loi": f"Không kết nối được Apps Script ({e.__class__.__name__})."}
    if not r.get("ok"):
        return {"ok": False, "loi": "Apps Script chưa có chức năng gửi mail — cần cập nhật Code.gs bản v4.2 (xem hướng dẫn bên dưới)."}
    return {"ok": True, "email": r.get("email"), "con_lai": r.get("con_lai")}


def gui(tieu_de: str, noi_dung: str, url: str | None = None, tok: str | None = None) -> tuple[bool, str]:
    if url is None:
        url, tok = _ket_noi()
    if not url:
        thu = config.LOCAL_DIR / "mail"
        thu.mkdir(parents=True, exist_ok=True)
        p = thu / f"{db.now_vn():%Y%m%d_%H%M%S}.html"
        p.write_text(f"<title>{E(tieu_de)}</title>" + noi_dung, encoding="utf-8")
        return True, str(p)
    try:
        r = requests.post(url, timeout=40, json={"token": tok, "action": "mail", "subject": tieu_de, "html": noi_dung}).json()
    except (requests.RequestException, ValueError) as e:
        return False, f"lỗi kết nối: {e.__class__.__name__}"
    return (True, str(r.get("to", ""))) if r.get("ok") else (False, str(r.get("error") or "Apps Script chưa hỗ trợ gửi mail"))


def gui_nen(tieu_de: str, noi_dung: str) -> None:
    """Gửi ở luồng nền — trang không phải chờ. URL / token lấy trước ở luồng chính."""
    url, tok = _ket_noi()
    threading.Thread(target=gui, args=(tieu_de, noi_dung, url, tok), daemon=True).start()


# ------------------------------------------------------------------ khung HTML
def _khung(tieu_de: str, phu: str, than: str) -> str:
    return (f'<div style="font-family:Arial,Helvetica,sans-serif;max-width:680px;margin:0 auto;color:#1C1B19;background:#FBF8F1">'
            f'<div style="background:#1C1B19;color:#fff;padding:18px 20px;border-radius:14px 14px 0 0">'
            f'<div style="color:{VANG};font-size:11px;letter-spacing:2px;font-weight:700">HOÀNG ANH COACHING</div>'
            f'<div style="font-size:20px;font-weight:700;margin-top:4px">{E(tieu_de)}</div>'
            f'<div style="font-size:13px;opacity:.8;margin-top:2px">{E(phu)}</div></div>'
            f'<div style="padding:6px 16px 16px;border:1px solid #E6DCC4;border-top:0;border-radius:0 0 14px 14px">{than}</div>'
            f'<div style="font-size:11px;color:{XAM};text-align:center;padding:10px">Email tự động từ web Hoàng Anh Coaching · '
            f'số liệu theo dữ liệu đã nhập trên app.</div></div>')


def _muc(ten: str, noi: str) -> str:
    return (f'<div style="margin-top:16px"><div style="font-weight:700;font-size:15px;border-bottom:2px solid {VANG};'
            f'padding-bottom:4px;margin-bottom:8px">{ten}</div>{noi}</div>')


def _bang(dau: list[str], dong: list[list[str]]) -> str:
    th = "".join(f'<th style="text-align:left;padding:6px;font-size:12px;color:{XAM};border-bottom:1px solid #E6DCC4">{h}</th>' for h in dau)
    tr = "".join("<tr>" + "".join(f'<td style="padding:6px;font-size:13px;border-bottom:1px solid #F0E8D6;vertical-align:top">{c}</td>'
                                  for c in r) + "</tr>" for r in dong)
    return f'<table style="width:100%;border-collapse:collapse"><tr>{th}</tr>{tr}</table>'


def _mau(chu: str, mau: str) -> str:
    return f'<b style="color:{mau}">{chu}</b>'


def _so(x: float, dv: str = "") -> str:
    return f"{x:g}".replace(".", ",") + (f" {dv}" if dv else "")


def _ds(ds: list[str]) -> str:
    return "<ul style='margin:4px 0;padding-left:18px'>" + "".join(f"<li style='margin:3px 0;font-size:13px'>{x}</li>" for x in ds) + "</ul>"


# ------------------------------------------------------------------ so sánh bài tập
def _so_bai(hom: dict, truoc: dict | None, giay: bool) -> tuple[str, str]:
    """(chữ so sánh, màu) giữa 2 lần tập của 1 bài."""
    if not truoc:
        return "🆕 lần đầu", XAM
    kg1, kg0 = max(h["kg"] for h in hom["hiep"]), max(h["kg"] for h in truoc["hiep"])
    l1, l0 = sum(h["lan"] for h in hom["hiep"]), sum(h["lan"] for h in truoc["hiep"])
    v1 = sum(h["kg"] * h["lan"] for h in hom["hiep"])
    v0 = sum(h["kg"] * h["lan"] for h in truoc["hiep"])
    if giay:
        return (f"⏱ {l1 - l0:+d} giây", XANH if l1 > l0 else DO if l1 < l0 else XAM)
    if kg1 > kg0:
        return f"⬆️ +{_so(kg1 - kg0, 'kg')}", XANH
    if kg1 < kg0:
        return f"↘️ {_so(kg1 - kg0, 'kg')}", CAM
    if len(hom["hiep"]) > len(truoc["hiep"]):
        return f"➕ thêm {len(hom['hiep']) - len(truoc['hiep'])} hiệp", XANH
    if l1 > l0:
        return f"➕ +{l1 - l0} lần", XANH
    if l1 < l0:
        return f"↘️ {l1 - l0} lần", CAM
    if v1 == v0:
        return "= giữ nguyên", XAM
    return ("➕ nhiều hơn" if v1 > v0 else "↘️ ít hơn"), (XANH if v1 > v0 else CAM)


def _bai_tap(s: dict, hist: list[dict]) -> tuple[str, list[str], dict]:
    """Bảng bài tập buổi này vs lần trước của từng bài + tổng khối lượng."""
    dong, chu_y, dem = [], [], {"tang": 0, "giam": 0, "bai": 0}
    truoc_hist = [x for x in hist if x is not s and (x["ngay"], str(x.get("_luc"))) <= (s["ngay"], str(s.get("_luc")))]
    for b in s.get("bai", []):
        ls_moi = tt.lich_su([s], b.get("id"), b.get("ten", ""), 1)
        if not ls_moi:
            continue
        ls_cu = tt.lich_su(truoc_hist, b.get("id"), b.get("ten", ""), 1)
        giay = bool(b.get("giay"))
        chu, mau = _so_bai(ls_moi[0], ls_cu[0] if ls_cu else None, giay)
        dem["bai"] += 1
        dem["tang"] += mau == XANH
        dem["giam"] += mau == CAM
        gc = f"<br><i style='color:{XAM};font-size:12px'>{E(str(b['ghi_chu'])[:120])}</i>" if b.get("ghi_chu") else ""
        dong.append([f"<b>{E(b.get('ten', ''))}</b>{gc}", E(tt.mo_ta(ls_moi[0], giay)[6:]),
                     E(tt.mo_ta(ls_cu[0], giay)) if ls_cu else "—", _mau(chu, mau)])
        if any(w in str(b.get("ghi_chu", "")).lower() for w in tt.DAU):
            chu_y.append(f"⚠️ {E(b.get('ten', ''))}: khách ghi “{E(str(b['ghi_chu'])[:80])}” — hỏi lại, buổi sau chưa tăng bài này.")
    # tổng khối lượng so với lần gần nhất cùng buổi (hoặc buổi liền trước)
    tn = bt.tonnage(s.get("bai", []))
    cung = [x for x in truoc_hist if s.get("buoi_ma") and x.get("buoi_ma") == s.get("buoi_ma")] or truoc_hist
    them = ""
    if cung and tn:
        t0 = bt.tonnage(cung[-1].get("bai", []))
        if t0:
            pc = (tn - t0) / t0 * 100
            them = (f"Tổng khối lượng (kg × lần): <b>{tn:,.0f} kg</b> · lần trước ({cung[-1]['ngay']:%d/%m}) {t0:,.0f} kg → "
                    + _mau(f"{pc:+.0f}%", XANH if pc > 2 else CAM if pc < -5 else XAM)).replace(",", ".")
    elif tn:
        them = f"Tổng khối lượng (kg × lần): <b>{tn:,.0f} kg</b>".replace(",", ".")
    bang = _bang(["Bài", "Hôm nay", "Lần trước", "So sánh"], dong) if dong else "<i>Không có bài nào ghi số hiệp.</i>"
    return bang + (f"<p style='font-size:13px;margin:8px 0 0'>{them}</p>" if them else ""), chu_y, dem


# ------------------------------------------------------------------ thông số cơ thể
def _thong_so(k: dict, hom: date) -> tuple[str, list[str]]:
    ma, out, chu_y = k["ma"], [], []
    cn = td.can_ngay(ma)
    sd = td.so_do(ma)
    if not cn.empty:
        c1 = cn.iloc[-1]
        dong = f"Cân gần nhất <b>{_so(float(c1['kg']), 'kg')}</b> ({c1['ngay']:%d/%m})"
        if len(cn) >= 2:
            c0 = cn.iloc[-2]
            ch = float(c1["kg"]) - float(c0["kg"])
            dong += f" · lần cân trước {_so(float(c0['kg']), 'kg')} ({c0['ngay']:%d/%m}) → {_mau(f'{ch:+.1f} kg'.replace('.', ','), XAM)}"
        cu = cn[cn["ngay"] >= hom - timedelta(days=7)]
        if len(cu) >= 2:
            tb7 = cu["kg"].astype(float).mean()
            dong += f" · TB 7 ngày {_so(round(tb7, 1), 'kg')}"
        if (hom - c1["ngay"]).days >= 7:
            chu_y.append(f"Khách {(hom - c1['ngay']).days} ngày chưa cân — nhắc cân buổi sáng.")
        out.append(dong)
    else:
        chu_y.append("Khách chưa có số cân nào trên app.")
    if not sd.empty:
        moi = sd.iloc[-1].to_dict()
        cu = sd.iloc[-2].to_dict() if len(sd) >= 2 else None
        dau = td.dau_khoa(sd)
        dong = []
        for r in td.so_sanh(cu, moi) if cu else []:
            mau = XAM if r["tot"] is None else XANH if r["tot"] else DO
            r0 = next((x for x in td.so_sanh(dau, moi) if x["k"] == r["k"]), None) if dau else None
            dong.append([E(r["ten"]), _so(r["dau"], r["dv"]), f"<b>{_so(r['moi'], r['dv'])}</b>",
                         _mau(f"{r['chenh']:+g} {r['dv']}".replace(".", ","), mau),
                         (f"{r0['chenh']:+g}".replace(".", ",") if r0 and dau is not cu else "—")])
        tieu = (f"Lần đo / InBody mới nhất {moi['ngay']:%d/%m/%Y}" + (f" so với lần trước {cu['ngay']:%d/%m/%Y}" if cu else ""))
        out.append(f"<div style='margin-top:8px;font-size:13px'>{tieu}</div>"
                   + (_bang(["Chỉ số", "Lần trước", "Mới nhất", "Thay đổi", "Từ đầu khoá"], dong) if dong
                      else "<div style='font-size:13px'><i>Mới có 1 lần đo — chưa so được.</i></div>"))
        if (hom - moi["ngay"]).days >= 28:
            chu_y.append(f"Đã {(hom - moi['ngay']).days} ngày chưa đo lại số đo / InBody — hẹn đo lại.")
    return "".join(f"<p style='font-size:13px;margin:4px 0'>{x}</p>" if not x.startswith("<div") else x for x in out) or \
        "<i>Chưa có số liệu.</i>", chu_y


def _muc_tieu(k: dict, hom: date) -> tuple[str, list[str]]:
    chu_y = []
    try:
        t = lt.tien_do(k, hom)
    except Exception:  # noqa: BLE001
        t = None
    mt = E(str(k.get("muc_tieu") or "").strip())
    dau = f"<p style='font-size:13px;margin:4px 0'>Mục tiêu khách: <b>{mt or 'chưa ghi'}</b>" + \
          (f" · hạn {E(str(k.get('muc_tieu_ngay'))[:10])}" if k.get("muc_tieu_ngay") else "") + "</p>"
    if not t:
        return dau + "<p style='font-size:13px'><i>Chưa đủ số đo để tính % tiến độ.</i></p>", chu_y
    dong = []
    for r in t["rows"]:
        mau = XANH if r["pct"] >= t["tg_pct"] - 15 else DO if r["pct"] < 0 else CAM
        dong.append([E(r["ten"]), f"{_so(r['goc'])} → <b>{_so(r['hien_tai'])}</b> / đích {_so(r['dich'])} {E(r['dv'])}",
                     _mau(f"{r['pct']}%", mau), E(r["trang_thai"]) + (f"<br><small style='color:{XAM}'>{E(r.get('du_doan', ''))}</small>"
                                                                      if r.get("du_doan") else "")])
        if r["pct"] < 0:
            chu_y.append(f"{E(r['ten'])} đang đi ngược mục tiêu.")
    return (dau + f"<p style='font-size:13px;margin:4px 0'>Tổng tiến độ <b>{t['tong']}%</b> · thời gian đã qua {t['tg_pct']}% · "
            f"{E(t['nhan_xet'])}</p>" + _bang(["Chỉ số", "Gốc → hiện tại / đích", "% đạt", "Đánh giá"], dong)), chu_y


def _goi_chuyen_can(k: dict, hom: date) -> tuple[str, list[str]]:
    chu_y, dong = [], []
    try:
        g = goi.tong_quan(k, hom=hom)
        if g["tong"]:
            dong.append(f"Gói: <b>{E(g['ten'])}</b> · đã tập {g['da']}/{g['tong']} · còn <b>{g['con']}</b> buổi")
            if g["con"] is not None and g["con"] <= 3:
                chu_y.append(f"Gói còn {g['con']} buổi — chuẩn bị tư vấn gia hạn.")
        elif g["ten"]:
            dong.append(f"Gói: <b>{E(g['ten'])}</b>")
        if g.get("het_han"):
            dong.append(f"Hết hạn: {g['het_han']:%d/%m/%Y}")
        if g.get("buoi_toi"):
            dong.append(f"Buổi hẹn tới: <b>{g['buoi_toi']:%d/%m}</b>")
    except Exception:  # noqa: BLE001
        pass
    try:
        cc = lt.chuyen_can(k, hom)
        dong.append("Chuyên cần 4 tuần: " + " · ".join(f"{t['tuan']}: {t['buoi']}" for t in cc["tuans"])
                    + (f" (kế hoạch {cc['ke_hoach']} buổi/tuần)" if cc["ke_hoach"] else ""))
        if cc.get("ty_le") is not None and cc["ty_le"] < 70:
            chu_y.append(f"Chuyên cần thấp ({cc['ty_le']}% kế hoạch) — hỏi lý do, cân nhắc đổi lịch.")
    except Exception:  # noqa: BLE001
        pass
    return "".join(f"<p style='font-size:13px;margin:4px 0'>{x}</p>" for x in dong), chu_y


def _buoi_toi(k: dict, hist: list[dict], hom: date) -> str:
    try:
        kh = tt.ke_hoach(k, hom + timedelta(days=1), hist=hist)
    except Exception:  # noqa: BLE001
        kh = None
    if not kh:
        return ""
    ds = [f"{b['pt']['icon']} <b>{E(b['ten'])}</b>: {E(b['pt']['ngan'].replace('**', ''))}" for b in kh["bai"]
          if b["pt"]["muc"] != "moi"][:6]
    return _muc(f"🎯 Buổi tới ({E(kh['buoi'].get('ten', ''))}) cần tăng tiến gì", _ds(ds)) if ds else ""


# ------------------------------------------------------------------ báo cáo 1 buổi
def bao_cao_buoi(k: dict, lid: str | None = None, hist: list[dict] | None = None) -> tuple[str, str] | None:
    """(tiêu đề, HTML) cho buổi `lid` (mặc định: buổi mới nhất) của khách."""
    hist = bt.sessions(k["ma"]) if hist is None else hist
    if not hist:
        return None
    s = next((x for x in hist if lid and x.get("id") == lid), None) or hist[-1]
    hom = s["ngay"]
    ten = str(k.get("ho_ten") or k["ma"])
    bang, cy_bai, dem = _bai_tap(s, hist)
    ts, cy_ts = _thong_so(k, db.now_vn().date())
    mt, cy_mt = _muc_tieu(k, db.now_vn().date())
    gc, cy_gc = _goi_chuyen_can(k, db.now_vn().date())
    # thông tin buổi
    tt_ = []
    ai = "Khách tự ghi" if s.get("nguoi_ghi") in ("khach", "kh") else "HLV ghi"
    for nhan, v in (("Người ghi", ai), ("Tình trạng", s.get("tinh_trang")), ("Sẵn sàng", s.get("san_sang")),
                    ("Cảm nhận", s.get("cam_nhan")), ("RPE", s.get("rpe")), ("Thời lượng", f"{s['thoi_luong']} phút" if s.get("thoi_luong") else "")):
        if v not in (None, "", 0):
            tt_.append(f"{nhan}: <b>{E(str(v))}</b>")
    cd = s.get("cardio")
    if isinstance(cd, dict) and cd.get("phut"):
        tt_.append(f"Cardio: <b>{E(str(cd.get('may', '')))} {cd['phut']} phút</b>")
    ghi = []
    if s.get("ghi_chu"):
        ghi.append(f"💬 Khách gửi HLV: “{E(str(s['ghi_chu'])[:300])}”")
    if s.get("ghi_chu_hlv"):
        ghi.append(f"🔒 Ghi chú nội bộ: {E(str(s['ghi_chu_hlv'])[:300])}")
    if s.get("loi_nhan"):
        ghi.append(f"📨 Lời nhắn đã gửi khách: {E(str(s['loi_nhan'])[:300])}")
    # việc cần làm
    cy = cy_bai + cy_mt + cy_ts + cy_gc
    rpe = tv.num(s.get("rpe"))
    if rpe and rpe >= 9:
        cy.append(f"Buổi rất nặng (RPE {rpe:g}) — theo dõi hồi phục, giấc ngủ trước buổi sau.")
    if str(s.get("cam_nhan")) in ("Rất mệt", "1", "Hơi mệt", "2"):
        cy.append("Khách thấy mệt — hỏi thăm ăn ngủ, cân nhắc giảm tải buổi sau.")
    if dem["bai"] and dem["tang"] == 0 and dem["giam"] >= max(2, dem["bai"] // 2):
        cy.append("Đa số bài giảm so với lần trước — kiểm tra thể trạng / ăn uống tuần này.")
    tom = (f"{dem['tang']}/{dem['bai']} bài tăng tiến" + (f" · {dem['giam']} bài giảm" if dem["giam"] else "")) if dem["bai"] else ""
    than = (f"<p style='font-size:13px;margin:10px 0 0'>{' · '.join(tt_)}</p>" + "".join(f"<p style='font-size:13px;margin:4px 0'>{g}</p>" for g in ghi)
            + (_muc("✅ Việc nên làm để chăm sóc khách", _ds(cy)) if cy else "")
            + _muc(f"🏋️ Bài tập so với lần trước{(' — ' + tom) if tom else ''}", bang)
            + _muc("⚖️ Thông số cơ thể", ts) + _muc("🎯 Mục tiêu", mt) + _muc("📦 Gói & chuyên cần", gc)
            + _buoi_toi(k, hist, hom))
    tieu = f"[HAC] {ten} · buổi {hom:%d/%m}" + (f" · {s.get('buoi')}" if s.get("buoi") else "") + (f" · {tom}" if tom else "")
    return tieu, _khung(f"Báo cáo buổi tập · {ten}", f"{s.get('buoi') or 'Buổi tập'} · {hom:%A %d/%m/%Y}".replace(
        "Monday", "Thứ 2").replace("Tuesday", "Thứ 3").replace("Wednesday", "Thứ 4").replace("Thursday", "Thứ 5").replace(
        "Friday", "Thứ 6").replace("Saturday", "Thứ 7").replace("Sunday", "Chủ nhật"), than)


def sau_buoi(k: dict, lid: str | None, vai: str = "hlv") -> None:
    """Gọi ngay sau khi lưu buổi: dựng báo cáo + gửi nền (lỗi thì bỏ qua — không chặn việc ghi buổi)."""
    try:
        c = cai_dat()
        if not c["sau_buoi"] or (vai != "hlv" and not c["khach_tu_ghi"]):
            return
        r = bao_cao_buoi(k, lid)
        if r:
            gui_nen(*r)
    except Exception:  # noqa: BLE001
        pass


# ------------------------------------------------------------------ tổng kết cuối ngày
def tong_ket_ngay(hom: date | None = None) -> tuple[str, str]:
    hom = hom or db.now_vn().date()
    mai = hom + timedelta(days=1)
    ds = store.clients(ca_ngung=False)
    H = store.hens()
    tap, can_hom, chu_y, lich_mai = [], [], [], []
    for k in ds:
        ma, ten = k["ma"], E(str(k.get("ho_ten") or k["ma"]))
        try:
            hist = bt.sessions(ma)
        except Exception:  # noqa: BLE001
            hist = []
        try:
            g = goi.tong_quan(k, H, hom)
        except Exception:  # noqa: BLE001
            g = {}
        buoi_hom = [x for x in hist if x["ngay"] == hom]
        for s in buoi_hom:
            _, _, dem = _bai_tap(s, hist)
            tap.append([f"<b>{ten}</b>", E(str(s.get("buoi") or "")), "HLV" if s.get("nguoi_ghi") not in ("khach", "kh") else "tự tập",
                        f"{dem['tang']}/{dem['bai']} tăng" + (f" · {dem['giam']} giảm" if dem["giam"] else ""),
                        E(str(s.get("cam_nhan") or "")) + (f" · RPE {s['rpe']}" if s.get("rpe") else "")])
        if not buoi_hom and g.get("buoi_cuoi") == hom:
            tap.append([f"<b>{ten}</b>", "Đã tập (đánh dấu trên lịch)", "HLV", "<i>chưa ghi chi tiết bài</i>", ""])
        try:
            for b in store.buoi([k], mai, mai, H):
                if b["trang_thai"] == "hen":
                    lich_mai.append(f"{E(store.gio_s(b['gio']))} · {ten}" + (f" · {E(b.get('dia_diem') or '')}" if b.get("dia_diem") else ""))
        except Exception:  # noqa: BLE001
            pass
        try:
            cn = td.can_ngay(ma)
        except Exception:  # noqa: BLE001
            cn = None
        if cn is not None and not cn.empty and cn.iloc[-1]["ngay"] == hom:
            ch = f"{float(cn.iloc[-1]['kg']) - float(cn.iloc[-2]['kg']):+.1f}".replace(".", ",") if len(cn) >= 2 else "—"
            can_hom.append(f"{ten}: {_so(float(cn.iloc[-1]['kg']), 'kg')} ({ch} kg so với lần trước)")
        cuoi = max([d for d in (hist[-1]["ngay"] if hist else None, g.get("buoi_cuoi")) if d], default=None)
        if cuoi and 10 <= (hom - cuoi).days <= 60:
            chu_y.append(f"{ten}: {(hom - cuoi).days} ngày chưa tập (buổi cuối {cuoi:%d/%m}).")
        if g.get("tong") and g.get("con") is not None and g["con"] <= 2:
            chu_y.append(f"{ten}: gói còn {g['con']} buổi — tư vấn gia hạn.")
        try:
            t = lt.tien_do(k, hom)
            for r in (t or {}).get("rows", []):
                if r["pct"] < 0:
                    chu_y.append(f"{ten}: {E(r['ten'])} đang đi ngược mục tiêu ({_so(r['goc'])} → {_so(r['hien_tai'])} {E(r['dv'])}).")
        except Exception:  # noqa: BLE001
            pass
    than = (_muc(f"🏋️ Buổi tập hôm nay ({len(tap)})", _bang(["Khách", "Buổi", "Ghi", "So lần trước", "Cảm nhận"], tap) if tap
                 else "<i>Hôm nay chưa có buổi nào được ghi.</i>")
            + _muc(f"⚖️ Khách cân hôm nay ({len(can_hom)})", _ds(can_hom) if can_hom else "<i>Chưa ai cân.</i>")
            + _muc(f"✅ Cần chú ý ({len(chu_y)})", _ds(chu_y) if chu_y else "<i>Không có gì cần chú ý 👍</i>")
            + _muc(f"📅 Lịch ngày mai {mai:%d/%m} ({len(lich_mai)})", _ds(sorted(lich_mai)) if lich_mai else "<i>Chưa có lịch.</i>"))
    return (f"[HAC] Tổng kết {hom:%d/%m} · {len(tap)} buổi · {len(chu_y)} việc cần chú ý",
            _khung("Tổng kết ngày", f"{hom:%d/%m/%Y} · {len(ds)} khách đang tập", than))
