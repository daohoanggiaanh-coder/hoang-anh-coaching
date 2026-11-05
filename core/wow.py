# Hoàng Anh Coaching v2.4 (2026-11-05) — trải nghiệm "wow": kỷ lục mới (thẻ ảnh chia sẻ), mốc thành tích, tin tổng kết tuần,
# thư tổng kết khoá (PDF), nhận biết ngủ ít → buổi tập nhẹ hơn.
from __future__ import annotations

import io
from datetime import date, timedelta

from core import buoi as bt, db, dong_luc as dl, ga_atlas as ga, giao_an as gs, store, tien_do as td, tu_van as tv


# ------------------------------------------------------------------ kỷ lục mới
def ky_luc_moi(bai_moi: list[dict], hist: list[dict]) -> list[dict]:
    """So buổi vừa ghi với lịch sử TRƯỚC đó: bài nào vượt 1RM ước tính / mức tạ cao nhất → kỷ lục mới."""
    out = []
    for b in bai_moi:
        e_moi = bt.best_1rm(b)
        if not e_moi:
            continue
        cu = [bt.best_1rm(x) for s in hist for x in s["bai"] if x.get("id") == b.get("id")]
        cu = [x for x in cu if x]
        if cu and e_moi > max(cu) * 1.005:
            top = max((h for h in b["hiep"] if (tv.num(h.get("kg"), 0) or 0) > 0), key=lambda h: tv.num(h.get("kg"), 0) or 0, default=None)
            if top:
                out.append({"bai": b.get("ten") or ga.ex(b["id"])["ten"], "kg": tv.num(top["kg"]), "lan": int(tv.num(top["lan"]) or 0),
                            "e1rm": round(e_moi, 1), "cu": round(max(cu), 1), "tang": round(e_moi - max(cu), 1)})
    return out


def the_ky_luc_png(ten_khach: str, pr: dict, ngay: date) -> bytes:
    """Thẻ ảnh 1080 × 1350 (tỷ lệ Instagram) để khách lưu / chia sẻ."""
    from PIL import Image, ImageDraw, ImageFont

    from core import config
    W, H = 1080, 1350
    im = Image.new("RGB", (W, H), "#14120F")
    d = ImageDraw.Draw(im)
    for r in range(900, 0, -6):                       # quầng sáng vàng phía trên
        a = int(40 * (1 - r / 900))
        d.ellipse((W / 2 - r, -r * 0.6, W / 2 + r, r * 0.9), fill=(20 + a, 18 + a, 15 + int(a * .6)))

    def f(w, s):
        return ImageFont.truetype(str(config.FONTS / f"BeVietnamPro-{w}.ttf"), s)

    def giua(y, s, font, col):
        w = d.textlength(s, font=font)
        d.text(((W - w) / 2, y), s, font=font, fill=col)

    giua(90, "HOÀNG ANH COACHING", f("Bold", 34), "#C8A24A")
    giua(200, "🏆 KỶ LỤC MỚI".replace("🏆 ", ""), f("Bold", 92), "#F6D77E")
    giua(330, pr["bai"][:34], f("SemiBold", 52), "#F3ECDC")
    giua(470, f"{pr['kg']:g} kg × {pr['lan']}", f("Bold", 150), "#FFFFFF")
    giua(680, f"1RM ước tính {pr['e1rm']:g} kg".replace(".", ","), f("SemiBold", 46), "#E6D3A1")
    giua(750, f"+{pr['tang']:g} kg so với kỷ lục cũ".replace(".", ","), f("Regular", 40), "#7BD3A0")
    d.line((240, 860, 840, 860), fill="#C8A24A", width=3)
    giua(900, ten_khach, f("Bold", 60), "#F3ECDC")
    giua(985, f"{ngay:%d/%m/%Y}", f("Regular", 38), "#A8A091")
    giua(1180, "Mỗi kg thêm lên thanh tạ là một lời hứa đã giữ.", f("Regular", 34), "#A8A091")
    giua(1235, "HLV Hoàng Anh", f("SemiBold", 34), "#C8A24A")
    buf = io.BytesIO()
    im.save(buf, "PNG", optimize=True)
    return buf.getvalue()


# ------------------------------------------------------------------ mốc thành tích
def _can_tb(ma: str) -> tuple[float | None, float | None]:
    CAN = td.can_ngay(ma)
    SD = td.so_do(ma)
    dau = (td.dau_khoa(SD, CAN) or {}).get("can_nang")
    if CAN.empty:
        return dau, None
    moi = CAN.tail(7)["kg"].mean()
    return dau, round(float(moi), 1)


def moc(k: dict, hom: date | None = None) -> list[dict]:
    """Các mốc khách ĐÃ đạt (id cố định để chỉ chúc mừng 1 lần)."""
    hom = hom or db.now_vn().date()
    ma = k["ma"]
    out = []
    ss = bt.sessions(ma)
    n_buoi = max(store.da_tap(k), len(ss))
    for n in (10, 25, 50, 100, 150, 200):
        if n_buoi >= n:
            out.append({"id": f"buoi{n}", "icon": "🏋️", "ten": f"{n} buổi tập", "loi": f"Bạn đã hoàn thành {n} buổi tập — kỷ luật thật sự!"})
    dau, moi = _can_tb(ma)
    if dau and moi:
        giam = dau - moi
        for n in (1, 2, 3, 5, 7, 10, 15, 20):
            if giam >= n:
                out.append({"id": f"giam{n}", "icon": "🔥", "ten": f"Giảm {n} kg", "loi": f"Cân trung bình đã giảm {n} kg so với đầu khoá!"})
        for n in (1, 2, 3, 5):
            if -giam >= n and str(k.get("muc_tieu_loai") or "") == "tang_co":
                out.append({"id": f"tang{n}", "icon": "💪", "ten": f"Tăng {n} kg", "loi": f"Đã tăng {n} kg — đúng hướng tăng cơ!"})
    SD = td.so_do(ma)
    if not SD.empty and "v_eo" in SD and SD["v_eo"].notna().sum() >= 2:
        eo = SD["v_eo"].dropna()
        g = float(eo.iloc[0] - eo.iloc[-1])
        for n in (2, 3, 5, 8, 10):
            if g >= n:
                out.append({"id": f"eo{n}", "icon": "📏", "ten": f"Eo nhỏ {n} cm", "loi": f"Vòng eo đã nhỏ hơn {n} cm so với lần đo đầu!"})
    tan = sum(bt.tonnage(s["bai"]) for s in ss) / 1000
    for n in (10, 25, 50, 100, 250):
        if tan >= n:
            out.append({"id": f"tan{n}", "icon": "🦾", "ten": f"{n} tấn", "loi": f"Tổng tạ bạn đã nâng vượt {n} tấn!"})
    tuan = gs.chuoi_tuan(gs.logs(ma), hom)
    for n in (4, 8, 12, 24):
        if tuan >= n:
            out.append({"id": f"tuan{n}", "icon": "📅", "ten": f"{n} tuần liên tiếp", "loi": f"{n} tuần liên tiếp không bỏ tập — đây là thói quen rồi!"})
    return out


def moc_trang_thai(ma: str) -> dict:
    v = db.latest("DinhDuong", ma).get(f"moc|{ma}") or {}
    return {"khach_xem": list(v.get("khach_xem") or []), "hlv_gui": list(v.get("hlv_gui") or [])}


def danh_dau_moc(ma: str, them: dict, nguoi: str) -> bool:
    v = moc_trang_thai(ma)
    for k_, ids in them.items():
        v[k_] = sorted(set(v.get(k_, [])) | set(ids))
    return db.append("DinhDuong", f"moc|{ma}", {**v, "ma_kh": ma}, nguoi, ma)


def thu_khen(k: dict, m: dict) -> str:
    goi, toi = store.xung(k)
    loi = m["loi"].replace("Bạn đã", f"{goi[:1].upper() + goi[1:]} đã").replace("bạn", goi)
    return (f"{goi[:1].upper() + goi[1:]} ơi, {toi} vừa thấy {goi} đạt mốc {m['icon']} {m['ten']}! {loi} "
            f"Đây là kết quả của từng buổi {goi} đến tập dù bận hay mệt. {toi[:1].upper() + toi[1:]} tự hào về {goi} lắm — "
            "mình giữ nhịp này tiếp nhé 💪")


# ------------------------------------------------------------------ tin tổng kết tuần (HLV duyệt rồi gửi)
def tin_tuan(k: dict, hom: date | None = None) -> str:
    hom = hom or db.now_vn().date()
    ma = k["ma"]
    goi, toi = store.xung(k)
    t2 = hom - timedelta(days=hom.weekday() + 7)          # tuần trước (T2 → CN)
    cn = t2 + timedelta(days=6)
    ss_all = bt.sessions(ma)
    ss = [s for s in ss_all if t2 <= s["ngay"] <= cn]
    truoc = [s for s in ss_all if s["ngay"] < t2]
    pr = []
    for s in ss:
        pr += ky_luc_moi(s["bai"], [x for x in ss_all if x["ngay"] < s["ngay"]])
    tan = sum(bt.tonnage(s["bai"]) for s in ss)
    CAN = td.can_ngay(ma)
    can_s = ""
    if not CAN.empty:
        a = CAN[(CAN["ngay"] >= t2) & (CAN["ngay"] <= cn)]["kg"].mean()
        b = CAN[(CAN["ngay"] >= t2 - timedelta(days=7)) & (CAN["ngay"] < t2)]["kg"].mean()
        if a == a and b == b:
            can_s = f"Cân trung bình tuần {a - b:+.1f} kg so với tuần trước.".replace(".", ",", 1)
    ck = dl.checkins(ma)
    ngu = [float(v.get("ngu") or 0) for d_, v in ck.items() if t2 <= d_ <= cn and v.get("ngu")]
    ke = len(store.lich_co_dinh(k)) or 0
    dong = [f"{goi[:1].upper() + goi[1:]} ơi, {toi} tổng kết tuần {t2:%d/%m}–{cn:%d/%m} nhé 👇"]
    dong.append(f"🏋️ {len(ss)}{f'/{ke}' if ke else ''} buổi tập · tổng tạ {tan:,.0f} kg".replace(",", "."))
    if pr:
        dong.append("🏆 Kỷ lục mới: " + "; ".join(f"{p['bai']} {p['kg']:g} kg × {p['lan']}".replace(".", ",") for p in pr[:3]))
    if can_s:
        dong.append("⚖️ " + can_s)
    if ngu:
        tb = sum(ngu) / len(ngu)
        dong.append(f"😴 Ngủ trung bình {tb:.1f} tiếng".replace(".", ",") + (" — tuần này mình cố ngủ thêm chút nhé." if tb < 7 else " — rất tốt!"))
    if not ss:
        dong.append(f"Tuần trước {goi} chưa tập buổi nào — không sao, tuần này mình bắt đầu lại từ buổi đầu tiên nhé, {toi} đợi {goi}!")
    elif ke and len(ss) >= ke:
        dong.append(f"Đủ buổi cả tuần — {toi} thấy {goi} rất kỷ luật 👏")
    elif truoc:
        dong.append(f"Tuần này mình cố đủ {ke or len(ss) + 1} buổi nha.")
    dong.append(f"Tuần mới mình tiếp tục: ăn đủ đạm, đủ bước chân, ngủ trước 23h. Có gì cần chỉnh {goi} nhắn {toi} liền nhé!")
    return "\n".join(dong)


# ------------------------------------------------------------------ ngủ ít → buổi nhẹ hơn
def ngu_it(ma: str, ngay: date) -> dict | None:
    v = dl.checkins(ma).get(ngay)
    try:
        h = float((v or {}).get("ngu") or 0)
    except ValueError:
        return None
    if not h or h >= 6:
        return None
    return {"gio": h, "hlv": f"😴 Check-in sáng nay: khách ngủ {h:g} tiếng → đề xuất giảm ~15% tạ, bớt 1 hiệp.",
            "khach": f"😴 HLV thấy đêm qua bạn ngủ {h:g} tiếng — hôm nay mình tập vừa sức: tạ nhẹ hơn một chút, bớt 1 hiệp. "
                     "Thấy khoẻ thì cứ tập như bình thường nhé."}


# ------------------------------------------------------------------ sức mạnh: bài chính đầu khoá → tốt nhất
def tien_bo_suc_manh(ma: str, n: int = 6) -> list[dict]:
    ss = bt.sessions(ma)
    dau, tot = {}, {}
    for s in ss:
        for b in s["bai"]:
            e = bt.best_1rm(b)
            if not e:
                continue
            dau.setdefault(b["id"], (e, b.get("ten"), s["ngay"]))
            if e > tot.get(b["id"], (0,))[0]:
                tot[b["id"]] = (e, b.get("ten"), s["ngay"])
    out = []
    for i, (e0, ten, d0) in dau.items():
        e1 = tot[i][0]
        if e1 > e0:
            out.append({"bai": ten or ga.ex(i)["ten"], "dau": round(e0, 1), "moi": round(e1, 1), "pct": round((e1 / e0 - 1) * 100)})
    return sorted(out, key=lambda x: -x["pct"])[:n]


def pdf_tong_ket(k: dict, loi_hlv: str = "") -> bytes:
    """Thư tổng kết khoá: ảnh trước / sau, chỉ số thay đổi, sức mạnh tăng, tổng buổi & tổng tạ, thư HLV."""
    from reportlab.lib.colors import white
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.utils import ImageReader, simpleSplit
    from reportlab.pdfgen import canvas

    from core import anh as A, config, hinh
    from core.pdfkit import BRONZE, DARK, GOLD, GREEN, INK, MUTE, RED, RULE, SOFT, fonts
    fonts()
    ma = k["ma"]
    W, H = A4
    M = 40
    SD, CAN = td.so_do(ma), td.can_ngay(ma)
    DAU, MOI = td.dau_khoa(SD, CAN) or {}, td.moi_nhat(SD, CAN) or {}
    ss = bt.sessions(ma)
    tan = sum(bt.tonnage(s["bai"]) for s in ss)
    goi, toi = store.xung(k)
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    c.setTitle(f"Thư tổng kết khoá · {k.get('ho_ten', '')}")

    def txt(x, y, s, f="R", sz=10, col=INK, al="l"):
        c.setFont(f, sz)
        c.setFillColor(col)
        {"l": c.drawString, "c": c.drawCentredString, "r": c.drawRightString}[al](x, y, str(s))

    c.setFillColor(DARK)
    c.rect(0, H - 160, W, 160, stroke=0, fill=1)
    txt(M, H - 48, config.BRAND, "B", 9, GOLD)
    txt(M, H - 84, "THƯ TỔNG KẾT KHOÁ", "B", 24, white)
    txt(M, H - 112, str(k.get("ho_ten", "")), "S", 15, GOLD)
    bd = store._d(k.get("ngay_bat_dau"))
    txt(M, H - 136, (f"Từ {bd:%d/%m/%Y} đến {db.now_vn().date():%d/%m/%Y}" if bd else "") + f" · {len(ss)} buổi đã ghi", "R", 10,
        white)
    y = H - 186
    # ảnh trước / sau (góc trước)
    ANH = td.anh(ma)
    a0, a1 = td.bo_anh(ANH, True).get("truoc"), td.bo_anh(ANH, False).get("truoc")
    if a0 and a1 and a0["id"] != a1["id"]:
        imgs = db.get_images([a0["id"], a1["id"]])
        gw = (W - 2 * M - 16) / 2
        gh = min(gw * 4 / 3, 240)
        for i, (lab, v) in enumerate((("TRƯỚC", a0), ("SAU", a1))):
            x = M + i * (gw + 16)
            try:
                c.drawImage(ImageReader(io.BytesIO(A.crop_ratio(imgs[v["id"]], gw, gh, 900))), x, y - gh, gw, gh)
            except Exception:  # noqa: BLE001
                c.setFillColor(SOFT)
                c.rect(x, y - gh, gw, gh, stroke=0, fill=1)
            c.setStrokeColor(GOLD)
            c.rect(x, y - gh, gw, gh, stroke=1, fill=0)
            txt(x + gw / 2, y - gh - 14, f"{lab} · {str(v['ngay'])[:10]}", "S", 8, BRONZE, "c")
        y -= gh + 34
    # ô số lớn
    o = [(f"{len(ss)}", "buổi tập"), (f"{tan / 1000:,.1f} tấn".replace(".", ","), "tổng tạ đã nâng")]
    for key, ten, dv in (("can_nang", "cân nặng", "kg"), ("pbf", "% mỡ", "%"), ("v_eo", "vòng eo", "cm")):
        a_, b_ = DAU.get(key), MOI.get(key)
        if a_ is not None and b_ is not None and a_ == a_ and b_ == b_ and a_ and b_:
            o.append((f"{MOI[key] - DAU[key]:+.1f} {dv}".replace(".", ","), ten))
    bw = (W - 2 * M - 10 * (len(o) - 1)) / len(o)
    for i, (v, t) in enumerate(o):
        x = M + i * (bw + 10)
        c.setFillColor(SOFT)
        c.roundRect(x, y - 58, bw, 58, 8, stroke=0, fill=1)
        txt(x + bw / 2, y - 30, v, "B", 16, INK, "c")
        txt(x + bw / 2, y - 47, t, "R", 8, MUTE, "c")
    y -= 84
    sm = tien_bo_suc_manh(ma)
    if sm:
        txt(M, y, "SỨC MẠNH TĂNG (1RM ƯỚC TÍNH: LẦN ĐẦU – TỐT NHẤT)", "S", 9, BRONZE)
        y -= 8
        for r in sm:
            y -= 18
            c.setStrokeColor(RULE)
            c.line(M, y - 5, W - M, y - 5)
            txt(M, y, r["bai"], "R", 10)
            txt(W - M - 70, y, f"{r['dau']:g} – {r['moi']:g} kg".replace(".", ","), "S", 10, INK, "r")
            txt(W - M, y, f"+{r['pct']}%", "B", 10, GREEN, "r")
        y -= 30
    txt(M, y, f"THƯ CỦA HLV GỬI {str(goi).upper()}", "S", 9, BRONZE)
    y -= 18
    loi = loi_hlv.strip() or (
        f"{goi[:1].upper() + goi[1:]} thân mến, cảm ơn {goi} đã tin tưởng và đồng hành cùng {toi} suốt khoá vừa qua. "
        f"Mỗi buổi {goi} đến tập, mỗi bữa {goi} ăn đúng, mỗi lần {goi} cân buổi sáng — tất cả cộng lại thành kết quả trên. "
        f"Thành quả lớn nhất không chỉ là con số, mà là những thói quen {goi} đã xây được. {toi[:1].upper() + toi[1:]} tin {goi} "
        "sẽ giữ được và còn tiến xa hơn nữa.")
    for ln in simpleSplit(loi, "R", 10.5, W - 2 * M):
        txt(M, y, ln, "R", 10.5)
        y -= 15
    hs = hinh.ho_so_hlv()
    y -= 10
    txt(W - M, y, f"HLV {hs.get('ten', 'Hoàng Anh')}", "B", 12, INK, "r")
    txt(W - M, y - 15, hs.get("chuc_danh", ""), "R", 8.5, MUTE, "r")
    txt(W / 2, 24, "Hoàng Anh Coaching · số liệu từ nhật ký tập và số đo của bạn", "R", 7.5, MUTE, "c")
    c.showPage()
    c.save()
    _ = RED
    return buf.getvalue()
