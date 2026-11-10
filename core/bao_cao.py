# Hoàng Anh Coaching v3.6 (port từ Atlas Academy v3.28) — Báo cáo đánh giá F1·F2 dạng PDF A4 cao cấp (reportlab, vẽ vector):
# icon chỉ số, tuổi cơ thể, ảnh form khách cạnh ảnh mẫu, ảnh đại diện khách + HLV
"""
7 trang: 1 Tổng quan · 2 Thành phần cơ thể & vòng đo · 3 Tư thế & Overhead Squat · 4 Bài test 1–4 (YMCA, squat, kéo, đẩy)
         · 5 Bài test 5–7 (plank, dẻo, strongman) + giáo án F2 · 6 Lộ trình 12 tuần · 7 Gói tập & cam kết.
Phong cách: giấy trắng ngà, chữ đen, một màu nhấn vàng đồng; thang màu xanh → đỏ chỉ dùng cho mức xếp loại.
"""
from __future__ import annotations

import io
import math
from datetime import date

from reportlab.lib.colors import HexColor, white
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader, simpleSplit
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

from core import anh, config, icons, tu_van as tv

W, H = A4
M = 40                                   # lề
PAPER, INK, MUTE, RULE = HexColor("#FBF8F1"), HexColor("#1C1B19"), HexColor("#6C6860"), HexColor("#DDD4C0")
BRONZE, BRONZE_D, SOFT = HexColor("#A3803C"), HexColor("#7A5B14"), HexColor("#F3ECDC")
LV = {5: "#1E7B4A", 4: "#5BA36B", 3: "#C8A24A", 2: "#D98E04", 1: "#C0392B"}
FONTS = config.ROOT / "assets" / "fonts"
_REG = False


def _fonts():
    global _REG
    if _REG:
        return
    for name, f in (("R", "BeVietnamPro-Regular"), ("S", "BeVietnamPro-SemiBold"), ("B", "BeVietnamPro-Bold")):
        pdfmetrics.registerFont(TTFont(name, str(FONTS / f"{f}.ttf")))
    _REG = True


def _img(name):
    for p in (config.ROOT / "assets" / "anh_that" / f"{name}.jpg", config.ROOT / "assets" / "anh_minh_hoa" / f"{name}.jpg",
              config.ROOT / "assets" / name, config.ROOT / "assets" / "app" / name):
        if p.exists():
            return ImageReader(str(p))
    return None


class Doc:
    def __init__(self, h: dict, r: dict, rm: dict, f2: bool = True):
        _fonts()
        self.h, self.r, self.rm, self.f2 = h, r, rm, f2
        self.buf = io.BytesIO()
        self.c = canvas.Canvas(self.buf, pagesize=A4)
        self.c.setTitle(f"Báo cáo đánh giá — {h.get('ho_ten', '')}")
        self.c.setAuthor("Hoàng Anh Coaching")
        self.page = 0

    # -------------------------------------------------- khung trang
    def new_page(self, title: str, kicker: str):
        if self.page:
            self.c.showPage()
        self.page += 1
        c = self.c
        c.setFillColor(PAPER)
        c.rect(0, 0, W, H, stroke=0, fill=1)
        logo = _img("icon-512.png")
        if logo:
            c.drawImage(logo, M, H - 62, width=34, height=34, mask="auto", preserveAspectRatio=True)
        c.setFillColor(INK)
        c.setFont("B", 10.5)
        c.drawString(M + 42, H - 40, "HOÀNG ANH COACHING")
        c.setFont("R", 7.5)
        c.setFillColor(MUTE)
        c.drawString(M + 42, H - 52, "Báo cáo đánh giá thể chất · " + ("Trải nghiệm F1 · F2" if self.f2 else "Buổi F1"))
        c.setFont("R", 8)
        c.drawRightString(W - M, H - 40, self.h.get("ho_ten", ""))
        c.drawRightString(W - M, H - 52, f"Ngày {self._date(self.h.get('ngay_f1'))}  ·  HLV {self.h.get('hlv', '')}")
        c.setStrokeColor(BRONZE)
        c.setLineWidth(1.2)
        c.line(M, H - 70, W - M, H - 70)
        c.setFillColor(BRONZE)
        c.setFont("S", 8)
        c.drawString(M, H - 98, kicker.upper())
        c.setFillColor(INK)
        c.setFont("B", 21)
        c.drawString(M, H - 122, title)
        # chân trang
        c.setStrokeColor(RULE)
        c.setLineWidth(0.6)
        c.line(M, 46, W - M, 46)
        c.setFont("R", 7)
        c.setFillColor(MUTE)
        c.drawString(M, 34, f"Hoàng Anh Coaching · Huấn luyện cá nhân 1-1 · HLV {self.h.get('hlv') or 'Hoàng Anh'}")
        c.drawRightString(W - M, 34, f"Trang {self.page} · Hoàng Anh Coaching {config.VERSION_LABEL}")
        return H - 145

    @staticmethod
    def _date(v):
        s = str(v or date.today())[:10]
        return f"{s[8:10]}/{s[5:7]}/{s[0:4]}" if len(s) == 10 and s[4] == "-" else s

    def text(self, x, y, s, font="R", size=9, color=INK, width=None, leading=None):
        c = self.c
        c.setFont(font, size)
        c.setFillColor(color)
        if not width:
            c.drawString(x, y, str(s))
            return y - (leading or size * 1.4)
        lead = leading or size * 1.45
        for line in simpleSplit(str(s), font, size, width):
            c.drawString(x, y, line)
            y -= lead
        return y

    def box(self, x, y, w, h, fill=white, stroke=RULE, r=8):
        self.c.setFillColor(fill)
        self.c.setStrokeColor(stroke)
        self.c.setLineWidth(0.6)
        self.c.roundRect(x, y, w, h, r, stroke=1, fill=1)

    def pill(self, x, y, s, lv):
        c = self.c
        c.setFont("S", 7.5)
        w = pdfmetrics.stringWidth(s, "S", 7.5) + 14
        c.setFillColor(HexColor(LV.get(lv, "#888888")))
        c.roundRect(x, y - 3, w, 13, 6.5, stroke=0, fill=1)
        c.setFillColor(white)
        c.drawString(x + 7, y + 0.5, s)
        return w

    def avatar(self, cx, cy, r, data, name="", ring=BRONZE):
        """Ảnh tròn (bytes hoặc base64); không có ảnh → chữ cái đầu."""
        c = self.c
        if isinstance(data, str):
            data = anh.from_b64(data)
        c.setFillColor(HexColor("#2A261E"))
        c.circle(cx, cy, r, stroke=0, fill=1)
        if data:
            try:
                c.saveState()
                p = c.beginPath()
                p.circle(cx, cy, r)
                c.clipPath(p, stroke=0, fill=0)
                c.drawImage(ImageReader(io.BytesIO(data)), cx - r, cy - r, width=2 * r, height=2 * r)
                c.restoreState()
            except Exception:  # noqa: BLE001
                c.restoreState()
                data = None
        if not data:
            w = [x for x in str(name).split() if x]
            ini = (w[0][0] + w[-1][0]).upper() if len(w) >= 2 else (w[0][:2].upper() if w else "?")
            c.setFillColor(white)
            c.setFont("B", r * 0.7)
            c.drawCentredString(cx, cy - r * 0.25, ini)
        c.setStrokeColor(ring)
        c.setLineWidth(1.6)
        c.circle(cx, cy, r, stroke=1, fill=0)
        c.setLineWidth(1)

    def icon(self, name, x, y, size=22, bg=SOFT, color=BRONZE_D):
        """Icon trong vòng tròn nền nhạt; (x, y) = góc dưới-trái."""
        self.c.setFillColor(bg)
        self.c.circle(x + size / 2, y + size / 2, size / 2, stroke=0, fill=1)
        pad = size * 0.2
        icons.draw(self.c, name, x + pad, y + pad, size - 2 * pad, color)

    def photo(self, data, x, y, w, h, contain=False):
        """Ảnh bytes/tên ảnh mẫu, cắt đầy khung w×h (contain=True: giữ trọn ảnh, không cắt)."""
        try:
            img = ImageReader(io.BytesIO(data)) if isinstance(data, bytes) else data
            iw, ih = img.getSize()
            sc = min(w / iw, h / ih) if contain else max(w / iw, h / ih)
            self.c.saveState()
            p = self.c.beginPath()
            p.roundRect(x, y, w, h, 5)
            self.c.clipPath(p, stroke=0, fill=0)
            self.c.drawImage(img, x + (w - iw * sc) / 2, y + (h - ih * sc) / 2, width=iw * sc, height=ih * sc)
            self.c.restoreState()
            return True
        except Exception:  # noqa: BLE001
            return False

    # -------------------------------------------------- thang màu có vạch đánh dấu
    def scale_bar(self, x, y, w, segs, value, vmin, vmax, unit="", fmt="{:g}"):
        """segs: [(từ, đến, mức 1–5, nhãn)] tăng dần. Vẽ dải màu + mũi tên giá trị."""
        c = self.c
        hgt = 9
        for a, b, lv, lab in segs:
            a2, b2 = max(a, vmin), min(b, vmax)
            if b2 <= a2:
                continue
            xa = x + (a2 - vmin) / (vmax - vmin) * w
            xb = x + (b2 - vmin) / (vmax - vmin) * w
            c.setFillColor(HexColor(LV[lv]))
            c.rect(xa, y, xb - xa, hgt, stroke=0, fill=1)
            c.setFillColor(MUTE)
            c.setFont("R", 6)
            if xb - xa > 34:
                c.drawCentredString((xa + xb) / 2, y - 9, lab)
        if value is not None:
            v = max(vmin, min(vmax, value))
            xv = x + (v - vmin) / (vmax - vmin) * w
            c.setFillColor(INK)
            p = c.beginPath()
            p.moveTo(xv, y + hgt + 1)
            p.lineTo(xv - 4.5, y + hgt + 8)
            p.lineTo(xv + 4.5, y + hgt + 8)
            p.close()
            c.drawPath(p, stroke=0, fill=1)
            c.setFont("B", 8)
            c.drawCentredString(xv, y + hgt + 11, fmt.format(value) + unit)

    @staticmethod
    def segs_from(levels: list[dict], vmin, vmax):
        """levels (từ cao xuống) → đoạn tăng dần."""
        out, hi = [], vmax
        for lv in levels:
            lo = max(lv["tu"], vmin)
            if hi > lo:
                out.append((lo, hi, lv["diem"], lv["nhan"]))
            hi = lo
        return sorted(out)

    # -------------------------------------------------- biểu đồ
    def radar(self, cx, cy, rad, data: dict):
        c = self.c
        keys = list(data.keys())
        n = len(keys)
        c.setStrokeColor(RULE)
        c.setLineWidth(0.5)
        for ring in (0.25, 0.5, 0.75, 1):
            p = c.beginPath()
            for i in range(n + 1):
                a = math.pi / 2 - 2 * math.pi * (i % n) / n
                (p.moveTo if i == 0 else p.lineTo)(cx + rad * ring * math.cos(a), cy + rad * ring * math.sin(a))
            c.drawPath(p, stroke=1, fill=0)
        for i, k in enumerate(keys):
            a = math.pi / 2 - 2 * math.pi * i / n
            c.line(cx, cy, cx + rad * math.cos(a), cy + rad * math.sin(a))
            lx, ly = cx + (rad + 14) * math.cos(a), cy + (rad + 14) * math.sin(a)
            c.setFillColor(INK)
            c.setFont("S", 7.2)
            v = data[k]
            lab = f"{k} · {v if v is not None else '—'}"
            if abs(math.cos(a)) < 0.2:
                c.drawCentredString(lx, ly - 3 + (4 if math.sin(a) > 0 else -4), lab)
            elif math.cos(a) > 0:
                c.drawString(lx, ly - 3, lab)
            else:
                c.drawRightString(lx, ly - 3, lab)
        # vùng chuẩn 60
        p = c.beginPath()
        for i in range(n + 1):
            a = math.pi / 2 - 2 * math.pi * (i % n) / n
            (p.moveTo if i == 0 else p.lineTo)(cx + rad * 0.6 * math.cos(a), cy + rad * 0.6 * math.sin(a))
        c.setStrokeColor(BRONZE)
        c.setDash(2, 2)
        c.drawPath(p, stroke=1, fill=0)
        c.setDash()
        p = c.beginPath()
        for i in range(n + 1):
            k = keys[i % n]
            v = (data[k] or 0) / 100
            a = math.pi / 2 - 2 * math.pi * (i % n) / n
            (p.moveTo if i == 0 else p.lineTo)(cx + rad * v * math.cos(a), cy + rad * v * math.sin(a))
        c.setFillColor(HexColor("#1E7B4A"))
        c.setFillAlpha(0.22)
        c.setStrokeColor(HexColor("#1E7B4A"))
        c.setLineWidth(1.4)
        c.drawPath(p, stroke=1, fill=1)
        c.setFillAlpha(1)

    def ring(self, cx, cy, rad, pct, label):
        c = self.c
        c.setLineWidth(9)
        c.setStrokeColor(SOFT)
        c.circle(cx, cy, rad, stroke=1, fill=0)
        if pct is not None:
            lv = 5 if pct >= 80 else 4 if pct >= 65 else 3 if pct >= 50 else 2 if pct >= 35 else 1
            c.setStrokeColor(HexColor(LV[lv]))
            c.arc(cx - rad, cy - rad, cx + rad, cy + rad, 90, -3.6 * max(pct, 1))
        c.setLineWidth(1)
        c.setFillColor(INK)
        c.setFont("B", 24)
        c.drawCentredString(cx, cy - 4, "—" if pct is None else str(pct))
        c.setFont("R", 7)
        c.setFillColor(MUTE)
        c.drawCentredString(cx, cy - 18, label)

    def line_chart(self, x, y, w, h, series: list[tuple[str, list, str]], xs: list, unit_l=""):
        c = self.c
        vals = [v for _, ys, _ in series for v in ys if v is not None]
        if not vals:
            return
        lo, hi = min(vals), max(vals)
        pad = (hi - lo) * 0.25 or 1
        lo, hi = lo - pad, hi + pad
        c.setStrokeColor(RULE)
        c.setLineWidth(0.5)
        for i in range(5):
            yy = y + h * i / 4
            c.line(x, yy, x + w, yy)
            c.setFont("R", 6.5)
            c.setFillColor(MUTE)
            c.drawRightString(x - 4, yy - 2, f"{lo + (hi - lo) * i / 4:.1f}")
        for i, xv in enumerate(xs):
            if i % 2 == 0:
                c.drawCentredString(x + w * i / (len(xs) - 1), y - 11, f"T{xv}")
        for name, ys, col in series:
            c.setStrokeColor(HexColor(col))
            c.setLineWidth(1.8)
            p = c.beginPath()
            first = True
            for i, v in enumerate(ys):
                if v is None:
                    continue
                px, py = x + w * i / (len(xs) - 1), y + (v - lo) / (hi - lo) * h
                (p.moveTo if first else p.lineTo)(px, py)
                first = False
            c.drawPath(p, stroke=1, fill=0)
            c.setFillColor(HexColor(col))
            c.circle(x + w, y + (ys[-1] - lo) / (hi - lo) * h, 3, stroke=0, fill=1)
            c.setFont("B", 8)
            c.drawString(x + w + 6, y + (ys[-1] - lo) / (hi - lo) * h - 3, f"{ys[-1]}{unit_l}")
            c.setFont("R", 6.5)
            c.drawString(x + w + 6, y + (ys[-1] - lo) / (hi - lo) * h - 12, name)

    # -------------------------------------------------- các trang
    def p_overview(self):
        h, r = self.h, self.r
        y = self.new_page("Tổng quan đánh giá", "Trang 1 · Kết quả buổi F1")
        # thẻ thông tin
        self.box(M, y - 92, W - 2 * M, 92, fill=white)
        self.avatar(M + 50, y - 46, 32, h.get("anh_dai_dien"), h.get("ho_ten", ""))
        cols = [("Khách hàng", h.get("ho_ten", "")), ("Giới tính · Tuổi", f"{h.get('gioi_tinh', '')} · {r.get('tuoi') or '—'}"),
                ("Chiều cao · Cân nặng", f"{h.get('chieu_cao', '—')} cm · {h.get('can_nang', '—')} kg"),
                ("Mục tiêu", tv.GOALS.get(h.get("muc_tieu"), "")), ("Lịch có thể tập", f"{h.get('buoi_tuan', 3)} buổi / tuần"),
                ("Huấn luyện viên", h.get("hlv", ""))]
        x0 = M + 96
        cw = (W - M - 12 - x0) / 3
        for i, (k, v) in enumerate(cols):
            cx, cy = x0 + (i % 3) * cw, y - 26 - (i // 3) * 40
            if k == "Huấn luyện viên":
                self.avatar(cx + 11, cy - 9, 11, h.get("_anh_hlv"), v, ring=INK)
                cx += 28
            self.text(cx, cy, k.upper(), "S", 6.5, MUTE)
            self.text(cx, cy - 13, v, "B", 10, INK, width=cw - 10)
        y -= 112
        # điểm tổng + radar
        self.box(M, y - 250, 170, 250, fill=white)
        self.ring(M + 85, y - 95, 52, r.get("diem_tong"), "điểm thể chất / 100")
        self.text(M + 14, y - 175, "Điểm thể chất tổng hợp từ thành phần cơ thể, các bài kiểm tra và chất lượng vận động.",
                  "R", 7.5, MUTE, width=142)
        self.box(M + 182, y - 250, W - 2 * M - 182, 250, fill=white)
        self.text(M + 196, y - 20, "BẢN ĐỒ THỂ CHẤT (0–100)", "S", 7.5, BRONZE)
        self.radar(M + 182 + (W - 2 * M - 182) / 2, y - 138, 78, r["radar"])
        self.text(M + 196, y - 240, "Đường nét đứt = mốc chuẩn 60 điểm", "R", 6.8, MUTE)
        y -= 270
        # an toàn
        self.text(M, y, "AN TOÀN TẬP LUYỆN", "S", 8, BRONZE)
        y -= 6
        self.box(M, y - 70, W - 2 * M, 70, fill=white)
        parq = "Tất cả “Không” — được tập bình thường" if not r["parq_co"] else \
            f"Có {len(r['parq_co'])} câu trả lời “Có” (câu {', '.join(map(str, r['parq_co']))}) — tập theo chỉ định bác sĩ"
        self.text(M + 12, y - 20, "PAR-Q", "S", 8, MUTE)
        self.text(M + 80, y - 20, parq, "B", 9, HexColor(LV[2] if r["parq_co"] else LV[5]), width=W - 2 * M - 92)
        bp = r.get("huyet_ap")
        self.text(M + 12, y - 44, "Huyết áp", "S", 8, MUTE)
        if bp:
            self.text(M + 80, y - 44, f"{bp['gia_tri']} mmHg", "B", 9)
            self.pill(M + 160, y - 44, bp["nhan"], bp["diem"])
        else:
            self.text(M + 80, y - 44, "Chưa đo", "R", 9, MUTE)
        if h.get("nhip_tim"):
            self.text(M + 340, y - 44, f"Nhịp tim nghỉ {h.get('nhip_tim')} lần/phút", "R", 8.5)
        y -= 92
        # 3 điểm mạnh / 3 ưu tiên
        rad = {k: v for k, v in r["radar"].items() if v is not None}
        strong = sorted(rad, key=lambda k: -rad[k])[:3]
        weak = [k for k in sorted(rad, key=lambda k: rad[k]) if rad[k] < 60][:3]
        half = (W - 2 * M - 12) / 2
        for i, (ttl, items, col) in enumerate((("Điểm mạnh", strong, LV[5]), ("Cần ưu tiên cải thiện", weak, LV[1]))):
            bx = M + i * (half + 12)
            self.box(bx, y - 92, half, 92, fill=white)
            self.c.setFillColor(HexColor(col))
            self.c.rect(bx, y - 92, 4, 92, stroke=0, fill=1)
            self.text(bx + 14, y - 18, ttl.upper(), "S", 7.5, HexColor(col))
            yy = y - 36
            for k in items or ["Chưa đủ dữ liệu"]:
                yy = self.text(bx + 14, yy, f"•  {k}" + (f"  —  {rad[k]}/100" if k in rad else ""), "R", 9, INK)

    def p_body(self):
        h, r = self.h, self.r
        y = self.new_page("Thành phần cơ thể", "Trang 2 · InBody · tuổi cơ thể" + (" · vòng đo" if self.f2 else ""))
        nm = tv.norms()
        sk = tv.sex_key(h.get("gioi_tinh"))
        rows = [
            ("bmi", "Chỉ số khối cơ thể (BMI)", r.get("bmi"), self.segs_from(nm["bmi"], 15, 35), 15, 35, "", nm["nguon"]["bmi"]),
            ("pbf", "Tỉ lệ mỡ cơ thể (PBF)", r.get("pbf"), self.segs_from(nm["pbf"][sk], 0, 45), 0 if sk == "nam" else 8, 45,
             "%", nm["nguon"]["pbf"]),
            ("noi_tang", "Mức mỡ nội tạng", r.get("mo_noi_tang"), self.segs_from(nm["mo_noi_tang"], 1, 20), 1, 20, "",
             nm["nguon"]["mo_noi_tang"]),
        ]
        for ic, name, res, segs, lo, hi, unit, src in rows:
            self.box(M, y - 70, W - 2 * M, 70, fill=white)
            self.icon(ic, M + 12, y - 30, 22)
            self.text(M + 42, y - 22, name, "B", 10.5)
            if res:
                self.pill(W - M - 14 - pdfmetrics.stringWidth(res["nhan"], "S", 7.5) - 14, y - 22, res["nhan"], res["diem"])
            self.scale_bar(M + 42, y - 47, W - 2 * M - 56, segs, res["gia_tri"] if res else None, lo, hi, unit)
            self.text(M + 42, y - 66, "Chuẩn: " + src, "R", 6.3, MUTE)
            y -= 80
        # ô số InBody có icon
        def val(k, nd=1):
            v = tv.num(h.get(k))
            return "—" if v is None else (f"{v:.{nd}f}".rstrip("0").rstrip(".") if nd else f"{v:.0f}")
        smm, kg = tv.num(h.get("smm")), tv.num(h.get("can_nang"))
        cells = [("can_nang", "Cân nặng", val("can_nang"), "kg"), ("co", "Khối cơ xương", val("smm"), "kg"),
                 ("khoi_mo", "Khối mỡ", val("khoi_mo"), "kg"), ("nuoc", "Nước cơ thể", val("nuoc"), "lít"),
                 ("bmr", "Trao đổi chất", val("bmr", 0), "kcal"),
                 ("chieu_cao", "Chiều cao", val("chieu_cao"), "cm"),
                 ("co", "Cơ / cân nặng", f"{smm / kg * 100:.0f}" if smm and kg else "—", "%"),
                 ("protein", "Protein", val("protein"), "kg"), ("khoang_chat", "Khoáng chất", val("khoang_chat", 2), "kg"),
                 ("diem", "Điểm InBody", val("diem_inbody", 0), "/100")]
        cw = (W - 2 * M - 4 * 8) / 5
        for i, (ic, k, v, u) in enumerate(cells):
            bx = M + (i % 5) * (cw + 8)
            by = y - 46 - (i // 5) * 54
            self.box(bx, by, cw, 46, fill=white)
            self.icon(ic, bx + 8, by + 12, 22)
            self.text(bx + 36, by + 30, k, "R", 6.8, MUTE, width=cw - 40)
            self.text(bx + 36, by + 12, v + ("" if v == "—" else f" {u}"), "B", 10.5)
        y -= 46 + 54 + 14
        # tuổi cơ thể
        ba = r.get("tuoi_co_the")
        bh = 96
        self.c.setFillColor(INK)
        self.c.roundRect(M, y - bh, 150, bh, 8, stroke=0, fill=1)
        self.icon("tuoi", M + 12, y - 32, 22, bg=HexColor("#3A352B"), color=HexColor("#E2C88A"))
        self.text(M + 40, y - 24, "TUỔI CƠ THỂ", "S", 7.5, HexColor("#E2C88A"))
        if ba:
            self.text(M + 14, y - 66, str(ba["gia_tri"]), "B", 30, white)
            self.text(M + 62, y - 58, "tuổi", "R", 9, HexColor("#CFC8B8"))
            self.text(M + 14, y - 84, f"Tuổi thật {ba['tuoi']} · {ba['chenh']:+d} năm", "S", 8, HexColor(LV[ba["diem"]])
                      if ba["chenh"] > 0 else HexColor("#8FD3A7"))
        else:
            self.text(M + 14, y - 62, "Cần tuổi + InBody", "R", 8, HexColor("#CFC8B8"))
        bx = M + 162
        self.box(bx, y - bh, W - M - bx, bh, fill=white)
        self.text(bx + 12, y - 16, "VÌ SAO RA CON SỐ NÀY", "S", 7.2, BRONZE)
        yy = y - 31
        for p in (ba or {}).get("chi_tiet", []):
            self.text(bx + 12, yy, p["ten"], "S", 8)
            self.text(bx + 90, yy, p["giai_thich"], "R", 7.8, MUTE)
            d = p["delta"]
            self.text(W - M - 44, yy, f"{d:+.1f} năm" if d else "0 năm", "B", 8,
                      HexColor(LV[1] if d > 0 else LV[5] if d < 0 else "#6C6860"))
            yy -= 12.5
        self.text(bx + 12, y - bh + 8, "Tuổi cơ thể = tuổi thật ± mỡ ± mỡ nội tạng ± khối cơ ± thể lực (công thức ước tính Hoàng Anh Coaching, "
                  "ước tính — không phải chẩn đoán y khoa)" + (f" · Máy InBody in: {ba['tuoi_may']} tuổi" if ba and
                                                             ba.get("tuoi_may") else ""), "R", 6, MUTE, width=W - M - bx - 20)
        y -= bh + 16
        if not self.f2:                                   # bản chỉ F1: ảnh phiếu InBody thay cho số đo vòng
            bh = 120
            self.text(M, y, "PHIẾU INBODY BUỔI F1", "S", 8, BRONZE)
            y -= 8
            self.box(M, y - bh, W - 2 * M, bh, fill=white)
            tx = M + 14
            if h.get("_anh_inbody") and self.photo(h["_anh_inbody"], M + 8, y - bh + 8, 140, bh - 16, contain=True):
                tx = M + 162
            self.text(tx, y - 22, "Số đo các vòng (cổ, ngực, eo, bụng, hông, đùi, bắp tay, bắp chân)", "B", 9.5)
            self.text(tx, y - 38, "và tỉ lệ eo/hông được đo ở buổi F2 — bổ sung trong báo cáo đầy đủ.", "R", 8.5, MUTE,
                      width=W - M - tx - 14)
            return
        # vòng đo F2
        self.text(M, y, "SỐ ĐO CÁC VÒNG (BUỔI F2)", "S", 8, BRONZE)
        y -= 8
        vw = r.get("vong_eo")
        tbl = [(lab, h.get(f"v_{k}")) for k, lab in tv.VONG]
        bh = 112
        self.box(M, y - bh, (W - 2 * M) * 0.56, bh, fill=white)
        self.icon("vong", M + 10, y - 32, 22)
        for i, (lab, v) in enumerate(tbl):
            col = M + 42 + (i % 2) * ((W - 2 * M) * 0.26)
            yy = y - 16 - (i // 2) * 20
            self.text(col, yy, lab, "R", 7.3, MUTE)
            self.text(col + 78, yy, f"{v} cm" if v not in (None, "") else "—", "B", 8.8)
        bx = M + (W - 2 * M) * 0.56 + 12
        bw = (W - 2 * M) * 0.44 - 12
        self.box(bx, y - bh, bw, bh, fill=white)
        self.text(bx + 14, y - 16, "NGUY CƠ MỠ BỤNG", "S", 7.5, BRONZE)
        if vw:
            self.text(bx + 14, y - 34, f"Vòng eo {vw['eo']:g} cm", "B", 10.5)
            self.pill(bx + 120, y - 34, ("Vượt" if vw["eo_vuot"] else "Dưới") + f" ngưỡng {vw['nguong_eo']} cm",
                      2 if vw["eo_vuot"] else 5)
            if "whr" in vw:
                self.text(bx + 14, y - 56, f"Tỉ lệ eo/hông {vw['whr']}", "B", 9.5)
                self.pill(bx + 120, y - 56, "Tăng nguy cơ" if vw["whr_vuot"] else "Đạt", 2 if vw["whr_vuot"] else 5)
            if "whtr" in vw:
                self.text(bx + 14, y - 78, f"Eo/chiều cao {vw['whtr']} (nên < 0,5)", "R", 8.5)
            self.text(bx + 14, y - bh + 8, "Chuẩn WHO châu Á – Thái Bình Dương", "R", 6.3, MUTE)
        else:
            self.text(bx + 14, y - 40, "Đo ở buổi F2", "R", 9, MUTE)

    def p_posture(self):
        h, r = self.h, self.r
        y = self.new_page("Tư thế & chất lượng vận động", "Trang 3 · Tư thế tĩnh · Overhead Squat (NASM)")
        photos = [(lab, h.get(f"_anh_{k}")) for k, lab in (("truoc", "Trước"), ("ben", "Bên"), ("sau", "Sau"))]
        pw = (W - 2 * M - 24) / 3
        for i, (lab, data) in enumerate(photos):
            bx = M + i * (pw + 12)
            self.box(bx, y - 200, pw, 200, fill=white)
            if data:
                try:
                    img = ImageReader(io.BytesIO(data))
                    self.c.drawImage(img, bx + 6, y - 180, width=pw - 12, height=172, preserveAspectRatio=True, anchor="c")
                except Exception:
                    pass
            else:
                self.text(bx + pw / 2 - 30, y - 100, "Chưa có ảnh", "R", 8, MUTE)
            self.text(bx + 8, y - 194, f"Góc {lab.lower()}", "S", 7.5, MUTE)
        y -= 214
        # nhận xét tư thế tĩnh
        issues = [f"{goc} · {phan}: {h.get(f'tt_{goc}_{phan}')}" for goc, parts in tv.norms()["tu_the"].items()
                  for phan, opts in parts.items() if h.get(f"tt_{goc}_{phan}") and h.get(f"tt_{goc}_{phan}") != opts[0]]
        self.text(M, y, "TƯ THẾ TĨNH", "S", 8, BRONZE)
        y = self.text(M + 110, y, "; ".join(issues) if issues else "Không ghi nhận lệch đáng kể.", "R", 8.5, INK,
                      width=W - 2 * M - 110) - 6
        # OHS
        ohs = r["ohs"]
        self.text(M, y, "OVERHEAD SQUAT", "S", 8, BRONZE)
        if ohs["so_loi"] is None:
            self.text(M + 110, y, "Chưa đánh giá.", "R", 8.5, MUTE)
            return
        self.text(M + 110, y, f"{ohs['so_loi']} điểm bù trừ: " + (", ".join(ohs["ten"]) if ohs["ten"] else "không có — vận động tốt"),
                  "B", 8.5, width=W - 2 * M - 110)
        y -= 26
        tbl = tv.norms()["ohs"]
        pics = [k for k in ohs["loi"] if tbl[k]["anh"]][:3]
        if pics:
            pw = (W - 2 * M - 12 * (len(pics) - 1)) / max(len(pics), 1)
            pw = min(pw, 160)
            for i, k in enumerate(pics):
                im = _img(tbl[k]["anh"])
                bx = M + i * (pw + 12)
                if im:
                    self.c.drawImage(im, bx, y - pw * 0.75, width=pw, height=pw * 0.75, preserveAspectRatio=True)
                self.text(bx, y - pw * 0.75 - 11, "Minh hoạ: " + tbl[k]["ten"].lower(), "R", 6.8, MUTE, width=pw)
            y -= pw * 0.75 + 24
        half = (W - 2 * M - 12) / 2
        for i, (ttl, items, col) in enumerate((("Cơ đang căng (cần giãn, lăn)", ohs["cang"], LV[1]),
                                               ("Cơ đang yếu (cần tăng cường)", ohs["yeu"], "#2E6DA4"))):
            bx = M + i * (half + 12)
            hh = 18 + 13 * max(len(items), 1) + 10
            self.box(bx, y - hh, half, hh, fill=white)
            self.text(bx + 12, y - 15, ttl.upper(), "S", 7, HexColor(col))
            yy = y - 30
            for it in items or ["—"]:
                yy = self.text(bx + 12, yy, "• " + it, "R", 8.2, INK, width=half - 20, leading=13)
        y -= 18 + 13 * max(len(ohs["cang"]), len(ohs["yeu"]), 1) + 24
        self.text(M, y, "BÀI SỬA ĐƯA VÀO KHỞI ĐỘNG MỖI BUỔI", "S", 8, HexColor(LV[5]))
        y -= 14
        for it in ohs["sua"] or ["Duy trì khởi động động 8–10 phút."]:
            y = self.text(M + 8, y, "›  " + it, "R", 8.8, INK, width=W - 2 * M - 16)
        if h.get("ohs_ghi_chu"):
            self.text(M, y - 6, "Ghi chú HLV: " + h["ohs_ghi_chu"], "R", 8, MUTE, width=W - 2 * M)

    def _test_card(self, y, k, name, mean, how, res, segs, lo, hi, unit, img, src, eq=None, show=None):
        """1 thẻ bài test: ảnh mẫu + ảnh khách · tên · ý nghĩa · cách làm · thang màu · nguồn. Trả y mới."""
        h = self.h
        bh = 116
        self.box(M, y - bh, W - 2 * M, bh, fill=white)
        pics = [(lab, d) for lab, d in (("MẪU CHUẨN", _img(img) if img else None), ("KHÁCH", h.get(f"_anh_t_{k}"))) if d]
        tx = M + 14
        pw, ph = (104, 78) if len(pics) == 2 else (110, 82)
        for i, (lab, d) in enumerate(pics):
            px = M + 10 + i * (pw + 6)
            if self.photo(d, px, y - 16 - ph, pw, ph):
                self.c.setFillColor(INK if lab == "KHÁCH" else HexColor(LV[5]))
                self.c.roundRect(px + 4, y - 16 - ph + 4, pdfmetrics.stringWidth(lab, "S", 6) + 10, 11, 5.5, stroke=0, fill=1)
                self.text(px + 9, y - 16 - ph + 7.3, lab, "S", 6, white)
            tx = px + pw + 12
        tw = W - M - 14 - tx
        room = tw - (pdfmetrics.stringWidth(res["nhan"], "S", 7.5) + 24 if res else 0)
        fs = 11
        while fs > 8 and pdfmetrics.stringWidth(name, "B", fs) > room:
            fs -= 0.5
        self.text(tx, y - 20, name, "B", fs)
        if res:
            self.pill(W - M - 14 - pdfmetrics.stringWidth(res["nhan"], "S", 7.5) - 14, y - 20, res["nhan"], res["diem"])
        yy = self.text(tx, y - 33, "Đánh giá: " + mean, "S", 7, BRONZE_D, width=tw, leading=9.5)
        self.text(tx, yy - 1, how, "R", 6.9, MUTE, width=tw, leading=9)
        if segs:
            val = eq if (res and eq is not None) else (res["gia_tri"] if res else None)
            self.scale_bar(tx, y - 88, tw, segs, show if show is not None else val, lo, hi,
                           "" if eq is not None else unit, "≈ {:g}" if eq is not None else "{:g}")
        self.text(tx, y - 106, "Chuẩn: " + src, "R", 6, MUTE, width=tw)
        return y - bh - 8

    def p_tests(self):
        h, r = self.h, self.r
        nm = tv.norms()
        yn = nm["y_nghia"]
        sk = tv.sex_key(h.get("gioi_tinh"))

        def age_segs(res, key):                      # bảng theo tuổi (squat, hít đất): mốc tối thiểu → đoạn tăng dần
            if not res or not res.get("moc"):
                return [], 0, 50
            th = list(res["moc"].items())
            levels = [{"tu": v, "nhan": k_, "diem": nm[key]["diem"][i]} for i, (k_, v) in enumerate(th)]
            val = res["quy_doi"] if res.get("quy_doi") is not None else res["gia_tri"]
            top = max(th[0][1] + 10, (val or 0) + 5)
            return self.segs_from(levels, 0, top), 0, top

        # 1 Tim mạch — YMCA: nhịp tim thấp là tốt (xanh bên trái) · Rockport: VO₂max · bước 2 phút: khoảng chuẩn
        bt_tm = tv.variant("tim_mach", h.get("bt_ymca"))
        ym = r.get("ymca")
        ym_segs, ym_lo, ym_hi, ym_unit = [], 60, 160, " l/p"
        if ym and ym.get("kieu") == "vo2":
            (ym_segs, _, ym_hi), ym_lo, ym_unit = age_segs(ym, "vo2max"), 10, ""
            ym_how = (f"Đi bộ nhanh 1,6 km trong {h.get('rp_phut', '—')} phút {h.get('rp_giay') or 0} giây, nhịp tim lúc dừng "
                      f"{h.get('rp_hr', '—')} › VO₂max ước tính {ym['gia_tri']:g} ml/kg/phút (Rockport).")
        elif ym and ym.get("kieu") == "buoc":
            lo_, hi_ = ym["khoang"]
            ym_lo, ym_hi = 0, hi_ + 40
            ym_segs = [(0, lo_, 2, "Dưới chuẩn"), (lo_, hi_, 4, "Đạt chuẩn"), (hi_, hi_ + 40, 5, "Trên chuẩn")]
            ym_how, ym_unit = f"{ym['gia_tri']:g} lần nâng gối trong 2 phút (chuẩn {lo_}–{hi_} lần).", " lần"
        else:
            if ym:
                cuts = list(ym["moc"].values())
                ym_lo, ym_hi = cuts[0] - 20, cuts[-1] + 25
                edges = [ym_lo] + cuts + [ym_hi]
                ym_segs = [(edges[i], edges[i + 1], nm["ymca"]["diem"][i], nm["ymca"]["nhan"][i]) for i in range(len(edges) - 1)]
            ym_how = f"Nhịp tim 1 phút sau test: {h.get('ymca_hr', '—')} lần/phút — càng thấp càng tốt."
        # 2 Squat
        bt_sq = tv.variant("squat", h.get("bt_squat"))
        sq = r.get("squat")
        if bt_sq["kieu"] == "ohs":
            sq_segs = [(0, 1, 5, "0"), (1, 2, 4, "1"), (2, 3, 3, "2"), (3, 4, 2, "3"), (4, 6, 1, "≥ 4")]
            sq_lo, sq_hi, sq_show = 0, 6, (sq["gia_tri"] + 0.5 if sq else None)
            sq_how = ("Số điểm bù trừ khi squat giơ tay qua đầu: " + (", ".join(r["ohs"]["ten"]) if r["ohs"]["ten"] else "không có")
                      if sq else "Chưa đánh giá.")
        else:
            (sq_segs, sq_lo, sq_hi), sq_show = age_segs(sq, "squat_1phut"), None
            sq_how = (f"{h.get('squat_reps', '—')} lần trong 60 giây" + (f" · tạ {h.get('squat_kg')} kg" if h.get("squat_kg") else "")
                      + (f" · quy đổi ≈ {sq['quy_doi']:g} lần tay không (ước tính)" if sq and sq.get("quy_doi") else ""))
        # 3 Kéo
        bt_k = tv.variant("keo", h.get("bt_keo") or ("lat_pulldown" if tv.num(h.get("keo_xo_kg")) else None))
        kx = r.get("keo_xo") or {}
        k_tbl = nm[bt_k["bang"]][sk]
        if bt_k["kieu"] == "so_lan":
            k_how = f"{h.get('keo_xo_reps', '—')} lần" + (" trong 60 giây" if bt_k["id"] == "banded_row" else " hoàn chỉnh") + "."
            k_hi, k_unit = k_tbl[0]["tu"] * 1.3, " lần"
        else:
            k_how = (f"Tạ {h.get('keo_xo_kg', '—')} kg × {h.get('keo_xo_reps', '—')} lần › 1RM ước tính "
                     f"{kx.get('rm', '—')} kg (Epley); so với cân nặng.")
            k_hi, k_unit = round(k_tbl[0]["tu"] * 1.15, 2), "× cân nặng"
        src_k = {"banded_row": "keo_day", "lat_pulldown": "keo_xo", "cable_row": "keo_ngang", "ta_don": "keo_ta_don",
                 "xa_thap": "xa_thap", "hit_xa": "hit_xa"}[bt_k["id"]]
        # 4 Hít đất
        bt_pu = tv.variant("hit_dat", h.get("bt_hit_dat"), h.get("gioi_tinh"))
        pu = r.get("hit_dat")
        pu_segs, _, pu_hi = age_segs(pu, "hit_dat")
        # 5 Plank · 6 Dẻo
        bt_pl = tv.variant("plank", h.get("bt_plank"))
        pl = r.get("plank")
        bt_d = tv.variant("deo", h.get("bt_deo"))
        pl_tbl = nm[bt_pl["bang"]][sk] if bt_pl.get("bang") else nm["plank"]
        pl_hi = pl_tbl[0]["tu"] * 1.4 if bt_pl.get("bang") else 300

        y = self.new_page("Bài kiểm tra thể lực", "Trang 4 · Bài test 1–4 · so với thang chuẩn theo giới & tuổi")
        y = self._test_card(y, "ymca", "1 · " + bt_tm["ten"], yn["ymca"], ym_how, ym, ym_segs, ym_lo, ym_hi, ym_unit,
                            bt_tm.get("anh"), nm["nguon"][{"ymca": "ymca", "rockport": "rockport",
                                                           "buoc_2phut": "buoc_2phut"}[bt_tm["id"]]])
        y = self._test_card(y, "squat", "2 · " + bt_sq["ten"], yn["squat"], sq_how, sq, sq_segs, sq_lo, sq_hi, " lần",
                            bt_sq.get("anh"), nm["nguon"]["ohs_diem" if bt_sq["kieu"] == "ohs" else "squat_1phut"],
                            sq.get("quy_doi") if sq and bt_sq["kieu"] != "ohs" else None, sq_show)
        y = self._test_card(y, "keo", "3 · " + bt_k["ten"], yn["keo"], k_how, r.get("keo_xo"),
                            self.segs_from(k_tbl, 0, k_hi), 0, k_hi, k_unit, bt_k.get("anh"), nm["nguon"][src_k])
        y = self._test_card(y, "hit_dat", "4 · " + bt_pu["ten"], yn["hit_dat"],
                            "Làm liên tục tới khi hỏng kỹ thuật" + (f" · quy đổi ≈ {pu['quy_doi']:g} lần {pu['bai_chuan']}"
                                                                    if pu and pu.get("quy_doi") is not None else "") + ".",
                            pu, pu_segs, 0, pu_hi, " lần", bt_pu.get("anh"), nm["nguon"]["hit_dat"],
                            pu.get("quy_doi") if pu else None)

        y = self.new_page("Bài kiểm tra thể lực", "Trang 5 · Bài test 5–7" + (" · giáo án buổi F2" if self.f2 else ""))
        y = self._test_card(y, "plank", "5 · " + bt_pl["ten"], yn["plank"],
                            "Giữ thân thẳng tới khi hông võng hoặc chổng mông" + (f" · quy đổi ≈ {pl['quy_doi']:g} giây plank cẳng tay"
                                                                                if pl and pl.get("quy_doi") is not None else "") + ".",
                            pl, self.segs_from(pl_tbl, 0, pl_hi), 0, pl_hi, " giây", bt_pl.get("anh"),
                            nm["nguon"]["plank_nghieng" if bt_pl.get("bang") else "plank"], pl.get("quy_doi") if pl else None)
        y = self._test_card(y, "deo", "6 · " + bt_d["ten"], yn["deo"],
                            "Gối thẳng, với hai tay về trước; 0 = chạm mũi chân, số âm = chưa chạm.",
                            r.get("deo_dai"), self.segs_from(nm["deo_dai"], -20, 20), -20, 20, " cm", bt_d.get("anh"),
                            nm["nguon"]["deo_dai"])
        if str(h.get("sm_co")).lower() in ("true", "1"):
            sm = next((v for v in nm["strongman"] if v["id"] == h.get("bt_sm")), nm["strongman"][0])
            kq = " · ".join(x for x in (h.get("sm_ket_qua") or "", f"{h['sm_kg']:g} kg" if tv.num(h.get("sm_kg")) else "",
                                        f"RPE {h.get('sm_rpe')}" if h.get("sm_rpe") else "") if x)
            y = self._test_card(y, "sm", "7 · " + sm["ten"], yn["strongman"],
                                f"Kết quả: {kq or '—'}" + (f". Nhận xét: {h['sm_ghi_chu']}" if h.get("sm_ghi_chu") else ""),
                                None, [], 0, 1, "", sm.get("anh"), "Bài trải nghiệm kết buổi — không tính vào điểm thể chất.")
        rows = h.get("f2_tap") or []
        if isinstance(rows, str):
            try:
                import json
                rows = json.loads(rows)
            except ValueError:
                rows = []
        if self.f2 and (rows or h.get("cardio_phut")):
            goal = h.get("muc_tieu", "giam_mo")
            self.text(M, y - 2, f"GIÁO ÁN BUỔI F2 · {tv.GOALS.get(goal, '').upper()} · COMPOUND › MULTI › ISOLATE", "S", 8, BRONZE)
            y -= 16
            hdr = [("#", 0), ("Loại", 14), ("Bài tập", 64), ("Hiệp × lần", 262), ("Tạ", 330), ("Tiếp thu", 372), ("Cảm nhận cơ", 428)]
            for t, dx in hdr:
                self.text(M + 8 + dx, y, t, "S", 7, MUTE)
            y -= 12
            cols = {"Compound": "#1C1B19", "Multi": "#A3803C", "Isolate": "#5BA36B", "Core": "#2E6DA4"}
            for row in rows[:9]:
                if y < 70:
                    break
                lo = str(row.get("Loại") or "")
                tt, cn = tv.num(row.get("Tiếp thu (1-5)")), tv.num(row.get("Cảm nhận cơ (1-5)"))
                ta = tv.num(row.get("Tạ (kg)"))
                self.text(M + 8, y, str(row.get("Thứ tự") or ""), "B", 8)
                if lo:
                    self.c.setFillColor(HexColor(cols.get(lo, "#8B8577")))
                    self.c.roundRect(M + 22, y - 2.5, pdfmetrics.stringWidth(lo, "S", 6) + 8, 10, 3, stroke=0, fill=1)
                    self.text(M + 26, y, lo, "S", 6, white)
                vals = [(row.get("Bài tập", ""), 64), (row.get("Hiệp × lần", ""), 262), (f"{ta:g} kg" if ta else "", 330),
                        (f"{tt:.0f}/5" if tt else "", 372), (f"{cn:.0f}/5" if cn else "", 428)]
                for v, dx in vals:
                    self.text(M + 8 + dx, y, str(v)[:40], "R", 8)
                y -= 12
            tpl = tv.f2_template(goal)
            self.text(M + 8, y - 2, "Cường độ: " + tpl["cuong_do"], "R", 7.3, MUTE, width=W - 2 * M - 16)
            y -= 11
            if h.get("cardio_phut"):
                self.text(M + 8, y - 2, f"Cardio: {h.get('cardio_may', '')} {h.get('cardio_phut')} phút · RPE {h.get('cardio_rpe', '—')}"
                          + (" · đã giãn cơ" if str(h.get("da_gian_co")).lower() in ("true", "1") else ""), "R", 7.3, MUTE)

    def p_roadmap(self):
        rm = self.rm
        y = self.new_page("Lộ trình 12 tuần", f"Trang 6 · Mục tiêu: {rm['muc_tieu_ten']}")
        # dự kiến
        self.box(M, y - 190, W - 2 * M, 190, fill=white)
        self.text(M + 14, y - 20, "KẾT QUẢ DỰ KIẾN NẾU TẬP ĐỀU " + f"{rm['buoi_tuan']} BUỔI/TUẦN VÀ ĂN THEO THỰC ĐƠN",
                  "S", 7.5, BRONZE)
        xs = [p["tuan"] for p in rm["proj"]]
        ser = []
        if rm["proj"][0]["can_nang"]:
            ser.append(("Cân nặng (kg)", [p["can_nang"] for p in rm["proj"]], "#1C1B19"))
        self.line_chart(M + 50, y - 160, W - 2 * M - 160, 120, ser, xs, "")
        if rm["proj"][0]["pbf"] is not None:
            p0, p1 = rm["proj"][0]["pbf"], rm["proj"][-1]["pbf"]
            self.text(W - M - 100, y - 60, "% mỡ", "R", 7.5, MUTE)
            self.text(W - M - 100, y - 78, f"{p0} › {p1}", "B", 12, HexColor(LV[5]))
        self.text(M + 14, y - 184, "Ước tính an toàn ~0,5–1 % cân nặng mỗi tuần; con số thực tế phụ thuộc ăn uống, giấc ngủ, đi tập đều.",
                  "R", 6.8, MUTE)
        y -= 206
        # 3 giai đoạn
        pw = (W - 2 * M - 24) / 3
        for i, ph in enumerate(rm["phases"]):
            bx = M + i * (pw + 12)
            self.box(bx, y - 210, pw, 210, fill=white)
            self.c.setFillColor(BRONZE if i == 1 else INK)
            self.c.roundRect(bx, y - 30, pw, 30, 8, stroke=0, fill=1)
            self.c.rect(bx, y - 30, pw, 12, stroke=0, fill=1)
            self.text(bx + 10, y - 13, ph["tuan"].upper(), "S", 7, white)
            self.text(bx + 10, y - 25, ph["ten"].split("·")[-1].strip(), "B", 9.5, white)
            yy = self.text(bx + 10, y - 46, ph["muc_tieu"], "S", 7.8, INK, width=pw - 20)
            yy -= 2
            for it in ph["noi_dung"]:
                yy = self.text(bx + 10, yy, "• " + it, "R", 7.4, INK, width=pw - 20, leading=10.5)
            self.text(bx + 10, y - 200, "📏 " + ph["do"] if False else "Mốc đo: " + ph["do"], "R", 6.8, BRONZE_D, width=pw - 20)
        y -= 228
        # lịch tuần + trọng tâm
        self.text(M, y, f"LỊCH MẪU {rm['buoi_tuan']} BUỔI / TUẦN", "S", 8, BRONZE)
        y -= 14
        for a, b in tv.week_split(rm["buoi_tuan"]):
            y = self.text(M + 8, y, f"{a}  ·  {b}", "R", 8.8)
        if rm["focus"]:
            y -= 6
            self.text(M, y, "TRỌNG TÂM RIÊNG CỦA BẠN", "S", 8, BRONZE)
            y -= 14
            for f in rm["focus"]:
                y = self.text(M + 8, y, "»  " + f, "R", 8.8, INK, width=W - 2 * M - 16)

    def p_package(self):
        h, rm = self.h, self.rm
        y = self.new_page("Gói tập đề xuất", "Trang 7 · Tư vấn & cam kết")
        g = rm["goi"]
        ds = g["ds"][:3]
        n_ = max(len(ds), 1)
        pw = (W - 2 * M - 16 * (n_ - 1)) / n_
        for i, p in enumerate(ds):
            bx = M + i * (pw + 16)
            hot = p["goi_y"]
            self.box(bx, y - 200, pw, 200, fill=white, stroke=BRONZE if hot else RULE)
            if hot:
                self.c.setFillColor(BRONZE)
                self.c.roundRect(bx + pw - 112, y - 16, 100, 18, 9, stroke=0, fill=1)
                self.text(bx + pw - 104, y - 10, "ĐỀ XUẤT CHO BẠN", "S", 7, white)
            self.text(bx + 18, y - 40, p["ten"].upper()[:34], "S", 9 if n_ < 3 else 7.5, BRONZE_D)
            self.text(bx + 18, y - 72, tv.vnd(p["gia"]), "B", 22 if n_ < 3 else 17)
            self.text(bx + 18, y - 92, f"≈ {tv.vnd(p['gia_buoi'])} / buổi · khoảng {p['tuan']:g} tuần", "R", 8.5 if n_ < 3 else 7, MUTE)
            yy = y - 118
            for it in [f"{p['buoi']} buổi kèm 1-1 với HLV", "Đo InBody định kỳ, báo cáo tiến độ",
                       "Thực đơn đầu khoá + nhắn tin theo dõi mỗi ngày",
                       (f"Tiết kiệm {tv.vnd(p['tiet_kiem'])} so với gói 12 buổi" if p["tiet_kiem"] else "Phù hợp để bắt đầu, làm quen")]:
                yy = self.text(bx + 18, yy, "›  " + it, "R", 8.8 if n_ < 3 else 7.4, width=pw - 30)
        y -= 220
        self.box(M, y - 46, W - 2 * M, 46, fill=SOFT, stroke=SOFT)
        self.text(M + 16, y - 19, "QUÀ TẶNG KHI ĐĂNG KÝ HÔM NAY", "S", 7.5, BRONZE_D)
        self.text(M + 16, y - 35, (g.get("bonus") or "")[:120], "B", 9.3)
        y -= 66
        self.text(M, y, "BƯỚC TIẾP THEO", "S", 8, BRONZE)
        y -= 14
        for it in [f"Lịch tập cố định: {h.get('lich_co_dinh') or '……………………………………'}",
                   "HLV gửi thực đơn và lịch tuần đầu trong 24 giờ",
                   "Video buổi tập F1" + (" và F2" if self.f2 else "") + " được gửi kèm báo cáo này qua Zalo"]:
            y = self.text(M + 8, y, "»  " + it, "R", 9)
        # video
        y -= 8
        vids = [("Video F1", h.get("video_f1"))] + ([("Video F2", h.get("video_f2"))] if self.f2 else [])
        for lab, link in vids:
            y = self.text(M + 8, y, f"{lab}: {link or 'chưa gửi'}", "R", 8, MUTE, width=W - 2 * M - 16)
        if h.get("ghi_chu_hlv"):
            y -= 6
            self.text(M, y, "LỜI NHẮN TỪ HUẤN LUYỆN VIÊN", "S", 8, BRONZE)
            y = self.text(M, y - 14, h["ghi_chu_hlv"], "R", 9, INK, width=W - 2 * M)
        # chữ ký
        yy = 120
        for i, (lab, name, av) in enumerate((("Khách hàng", h.get("ho_ten", ""), h.get("anh_dai_dien")),
                                             ("Huấn luyện viên", h.get("hlv", ""), h.get("_anh_hlv")))):
            bx = M + i * ((W - 2 * M) / 2)
            self.c.setStrokeColor(RULE)
            self.c.line(bx + 20, yy, bx + (W - 2 * M) / 2 - 20, yy)
            self.avatar(bx + 34, yy - 22, 14, av, name, ring=BRONZE if i == 0 else INK)
            self.text(bx + 56, yy - 14, lab.upper(), "S", 7, MUTE)
            self.text(bx + 56, yy - 27, name, "B", 9)

    def build(self) -> bytes:
        self.p_overview()
        self.p_body()
        self.p_posture()
        self.p_tests()
        self.p_roadmap()
        self.p_package()
        self.c.save()
        return self.buf.getvalue()


def make_pdf(h: dict, f2: bool = True, goi: dict | None = None) -> bytes:
    """f2=False: bản gửi ngay sau buổi F1 — bỏ số đo vòng, giáo án và video buổi F2. goi: gói của HLV (thay gói mặc định)."""
    r = tv.evaluate(h)
    if not f2:                                            # bỏ dữ liệu F2 khỏi mọi phép tính hiển thị
        h = {k: v for k, v in h.items() if not (k.startswith(("v_", "f2_")) or k in ("cardio_phut", "video_f2"))}
        r = tv.evaluate(h)
    rm = tv.roadmap(h, r)
    if goi:
        rm["goi"] = goi
    return Doc(h, r, rm, f2).build()
