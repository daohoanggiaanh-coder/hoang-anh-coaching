# Hoàng Anh Coaching v3.6 (port từ Atlas Academy v3.28) — phiếu thông tin khách hàng in giấy (buổi tư vấn F1)
"""Phiếu trống A4 2 trang, có logo, email nhận báo cáo, sàng lọc sức khoẻ và chữ ký. Khách tự điền trước buổi F1."""
from __future__ import annotations

import io
from functools import lru_cache

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from core import config
from core.bao_cao import BRONZE, INK, MUTE, RULE, SOFT, _fonts, _img

W, H = A4
M = 40
WHITE_INK = INK


class _Phieu:
    def __init__(self):
        _fonts()
        self.buf = io.BytesIO()
        self.c = canvas.Canvas(self.buf, pagesize=A4)
        self.c.setTitle("Phiếu thông tin khách hàng — Hoàng Anh Coaching")
        self.c.setAuthor("Hoàng Anh Coaching")
        self.page = 0
        self.y = 0

    # ---------------------------------------------------------------- khung
    def new_page(self, first: bool):
        c = self.c
        if self.page:
            c.showPage()
        self.page += 1
        logo = _img("icon-512.png")
        if first:
            if logo:
                c.drawImage(logo, M, H - 112, width=66, height=73, mask="auto", preserveAspectRatio=True)
            x = M + 80
            c.setFillColor(BRONZE)
            c.setFont("S", 8)
            c.drawString(x, H - 56, "HOÀNG ANH COACHING  ·  BUỔI TƯ VẤN F1")
            c.setFillColor(INK)
            c.setFont("B", 20)
            c.drawString(x, H - 80, "Phiếu thông tin khách hàng")
            c.setFont("R", 8.5)
            c.setFillColor(MUTE)
            c.drawString(x, H - 95, "Giúp huấn luyện viên hiểu bạn trước khi thiết kế lộ trình.")
            c.drawString(x, H - 106, "Mọi thông tin được giữ kín, chỉ dùng cho việc tập luyện của bạn.")
            # ô mã khách / ngày
            bx, bw = W - M - 132, 132
            c.setStrokeColor(RULE)
            c.setLineWidth(0.8)
            c.roundRect(bx, H - 108, bw, 56, 6, stroke=1, fill=0)
            c.setFont("R", 7.5)
            c.setFillColor(MUTE)
            c.drawString(bx + 10, H - 68, "MÃ KHÁCH")
            c.drawString(bx + 10, H - 94, "NGÀY")
            self._dots(bx + 52, H - 68, bx + bw - 10)
            c.setFont("R", 9)
            c.setFillColor(INK)
            c.drawString(bx + 52, H - 94, "......  /  ......  /  20......")
            top = H - 126
        else:
            if logo:
                c.drawImage(logo, M, H - 66, width=30, height=33, mask="auto", preserveAspectRatio=True)
            c.setFillColor(INK)
            c.setFont("B", 10.5)
            c.drawString(M + 40, H - 46, "HOÀNG ANH COACHING")
            c.setFont("R", 7.5)
            c.setFillColor(MUTE)
            c.drawString(M + 40, H - 58, "Phiếu thông tin khách hàng · Buổi tư vấn F1")
            c.drawRightString(W - M, H - 46, "Họ tên: ..............................................")
            top = H - 76
        c.setStrokeColor(BRONZE)
        c.setLineWidth(1.2)
        c.line(M, top, W - M, top)
        # chân trang
        c.setStrokeColor(RULE)
        c.setLineWidth(0.6)
        c.line(M, 44, W - M, 44)
        c.setFont("R", 7)
        c.setFillColor(MUTE)
        c.drawString(M, 32, "Hoàng Anh Coaching · Huấn luyện cá nhân 1-1 · Thông tin chỉ dùng cho việc huấn luyện")
        c.drawRightString(W - M, 32, f"Trang {self.page} · Mẫu {config.VERSION_LABEL}")
        self.y = top - 26

    # ---------------------------------------------------------------- nét vẽ
    def _dots(self, x0, y, x1):
        c = self.c
        c.setStrokeColor(MUTE)
        c.setLineWidth(0.6)
        c.setDash(0.8, 2.2)
        c.line(x0, y - 2, x1, y - 2)
        c.setDash()

    def _box(self, x, y, s=7.5):
        c = self.c
        c.setStrokeColor(INK)
        c.setLineWidth(0.7)
        c.rect(x, y - 1, s, s, stroke=1, fill=0)

    def section(self, no: str, title: str, note: str = ""):
        c = self.c
        self.y -= 6
        c.setFillColor(BRONZE)
        c.setFont("B", 15)
        c.drawString(M, self.y, no)
        c.setFillColor(INK)
        c.setFont("B", 10.5)
        c.drawString(M + 28, self.y + 1, title.upper())
        if note:
            c.setFont("R", 7.5)
            c.setFillColor(MUTE)
            c.drawRightString(W - M, self.y + 1, note)
        c.setStrokeColor(RULE)
        c.setLineWidth(0.6)
        c.line(M, self.y - 7, W - M, self.y - 7)
        self.y -= 26

    def label(self, x, y, s, bold=False, size=9, color=INK):
        c = self.c
        c.setFont("S" if bold else "R", size)
        c.setFillColor(color)
        c.drawString(x, y, s)
        return x + c.stringWidth(s, "S" if bold else "R", size)

    def field(self, x, w, lab, y=None, hint=""):
        y = self.y if y is None else y
        e = self.label(x, y, lab, bold=True)
        if hint:
            e = self.label(e + 4, y, hint, size=7.5, color=MUTE)
        self._dots(e + 6, y, x + w)

    def row(self, *items, gap=18):
        """items: (label, ty_le, hint)"""
        tot = sum(t for _, t, *_ in items)
        x, full = M, W - 2 * M - gap * (len(items) - 1)
        for it in items:
            lab, t = it[0], it[1]
            w = full * t / tot
            self.field(x, w, lab, hint=it[2] if len(it) > 2 else "")
            x += w + gap
        self.y -= 22

    def opts(self, lab, items, x=None, y=None, step=None, size=9):
        x = M if x is None else x
        y = self.y if y is None else y
        e = self.label(x, y, lab, bold=True) + 10 if lab else x
        for i, s in enumerate(items):
            xx = e + (i * step if step else 0)
            self._box(xx, y)
            end = self.label(xx + 12, y, s, size=size)
            if not step:
                e = end + 14
        return e

    def opts_line(self, lab, items, step=None):
        self.opts(lab, items, step=step)
        self.y -= 20

    def grid(self, items, cols=2, extra=None):
        cw = (W - 2 * M) / cols
        for i, s in enumerate(items):
            r, k = divmod(i, cols)
            x, y = M + k * cw, self.y - r * 18
            self._box(x, y)
            e = self.label(x + 12, y, s)
            if extra and s in extra:
                self._dots(e + 4, y, x + cw - 14)
        self.y -= 18 * ((len(items) + cols - 1) // cols) + 4

    def lines(self, n=1, lab=""):
        for i in range(n):
            if i == 0 and lab:
                self.field(M, W - 2 * M, lab)
            else:
                self._dots(M, self.y, W - M)
            self.y -= 20

    def q(self, s):
        self.label(M, self.y, s, bold=True)
        self.y -= 17

    def yes_no(self, items):
        """Bảng sàng lọc sức khoẻ: câu hỏi · Có · Không."""
        c = self.c
        xc, xk = W - M - 82, W - M - 34
        c.setFont("S", 7.5)
        c.setFillColor(MUTE)
        c.drawCentredString(xc + 4, self.y + 2, "CÓ")
        c.drawCentredString(xk + 4, self.y + 2, "KHÔNG")
        self.y -= 16
        for i, s in enumerate(items):
            if i % 2 == 0:
                c.setFillColor(SOFT)
                c.rect(M - 4, self.y - 5, W - 2 * M + 8, 17, stroke=0, fill=1)
            self.label(M + 2, self.y, f"{i + 1}.  {s}")
            self._box(xc, self.y)
            self._box(xk, self.y)
            self.y -= 17
        self.y -= 4

    # ---------------------------------------------------------------- nội dung
    def build(self) -> bytes:
        self.new_page(first=True)
        self.section("01", "Thông tin cá nhân")
        self.row(("Họ và tên", 2.2), ("Năm sinh", 1))
        self.opts("Giới tính", ["Nam", "Nữ"], x=M)
        self.field(M + 170, W - 2 * M - 170, "Số điện thoại (Zalo)")
        self.y -= 22
        self.row(("Email", 1, "(nhận báo cáo tiến độ hằng tuần)"))
        self.row(("Nghề nghiệp", 1), ("Liên hệ khẩn cấp", 1.35, "(tên · SĐT)"))
        self.opts_line("Tính chất công việc", ["Ngồi nhiều / văn phòng", "Đi lại nhiều", "Lao động nặng"])
        self.opts_line("Mức căng thẳng hiện tại", ["Thấp", "Trung bình", "Cao", "Rất cao"])

        self.section("02", "Sức khoẻ & an toàn", "Đánh dấu một ô cho mỗi câu")
        self.yes_no(["Bác sĩ từng nói bạn có bệnh tim, huyết áp cao hoặc tiểu đường?",
                     "Bạn từng đau ngực, khó thở bất thường hoặc choáng, ngất khi vận động?",
                     "Bạn đang đau hoặc từng chấn thương lưng, cổ, vai, gối, cổ chân?",
                     "Bạn đang dùng thuốc điều trị dài ngày?",
                     "Bạn phẫu thuật trong 12 tháng gần đây?",
                     "Nữ: đang mang thai hoặc sinh con chưa quá 6 tháng?"])
        self.lines(1, "Nếu có, ghi rõ")
        self.y -= 2

        self.section("03", "Thói quen & dinh dưỡng")
        e = self.label(M, self.y, "Ngủ trung bình", bold=True)
        e = self.label(e + 6, self.y, "........ tiếng / đêm")
        self.opts("Chất lượng", ["Ngủ sâu", "Hay thức giấc / khó ngủ"], x=e + 26)
        self.y -= 20
        self.opts_line("Ăn uống", ["Tự nấu", "Ăn ngoài / gọi đồ", "Bỏ bữa / ăn thất thường"])
        self.opts_line("Rượu bia, thuốc lá", ["Không", "Thỉnh thoảng", "Thường xuyên"])
        e = self.label(M, self.y, "Tự chấm chế độ ăn hiện tại", bold=True)
        e = self.label(e + 6, self.y, "........ / 10")
        self.opts("Cần HLV lên thực đơn?", ["Có", "Không"], x=e + 26)
        self.y -= 20

        self.section("04", "Trải nghiệm trước đây")
        self.q("Bạn từng tập ở đâu chưa?")
        self.grid(["Chưa từng", "Tự tập ở nhà / công viên", "Phòng tập khác:"], cols=3, extra={"Phòng tập khác:"})
        self.q("Điều gì khiến bạn chưa hài lòng ở lần tập trước?")
        self.grid(["Không biết tập gì / sai kỹ thuật", "Không có người hướng dẫn, PT thiếu quan tâm",
                   "Phòng tập đông, thiếu sạch sẽ", "Tập mãi không thấy kết quả", "Khác:"], cols=2, extra={"Khác:"})
        self.lines(1, "Bạn từng bỏ tập giữa chừng? Lý do chính")

        # ------------------------------------------------ trang 2
        self.new_page(first=False)
        self.section("05", "Mục tiêu & động lực")
        self.q("Mục tiêu quan trọng nhất trong 3–6 tháng tới")
        self.grid(["Giảm mỡ (giảm ...... kg)", "Tăng cơ / tăng cân (tăng ...... kg)", "Săn chắc, cải thiện vóc dáng",
                   "Tăng sức bền, tim mạch", "Giảm đau lưng, cổ vai gáy", "Khác:"], cols=2, extra={"Khác:"})
        self.q("Sự kiện sắp tới khiến bạn muốn thay đổi")
        self.grid(["Đám cưới", "Du lịch / đi biển", "Tết, lễ hội", "Khác:"], cols=4, extra={"Khác:"})
        self.lines(2, "Nếu 6 tháng tới chưa đạt mục tiêu, điều gì sẽ xảy ra với bạn?")

        self.section("06", "Mong muốn về huấn luyện viên")
        self.q("Phong cách huấn luyện bạn thích")
        self.grid(["Nghiêm khắc, kỷ luật — thúc đẩy mạnh", "Nhẹ nhàng, động viên — lắng nghe",
                   "Khoa học, chi tiết — giải thích kỹ"], cols=1)
        self.row(("Số buổi tập được", 1, "(buổi / tuần)"), ("Khung giờ", 1.4))
        self.opts_line("Người ảnh hưởng đến quyết định tập", ["Bản thân", "Vợ / chồng", "Bố mẹ", "Bạn bè"])

        # cam kết + chữ ký
        c = self.c
        self.y -= 2
        self._box(M, self.y)
        self.label(M + 12, self.y, "Tôi đồng ý nhận báo cáo tiến độ qua email / Zalo và cam kết thông tin sức khoẻ ở trên là đúng.",
                   size=8.5)
        self.y -= 30
        half = (W - 2 * M - 30) / 2
        for i, t in enumerate(["Khách hàng", "Huấn luyện viên tư vấn"]):
            x = M + i * (half + 30)
            self.label(x, self.y, t, bold=True)
            self.label(x, self.y - 12, "Ký và ghi rõ họ tên", size=7.5, color=MUTE)
            c.setStrokeColor(RULE)
            c.line(x, self.y - 52, x + half, self.y - 52)
        self.y -= 72

        # ô dành cho HLV
        bh = 118
        c.setFillColor(SOFT)
        c.roundRect(M - 4, self.y - bh + 12, W - 2 * M + 8, bh, 6, stroke=0, fill=1)
        self.label(M + 6, self.y, "DÀNH CHO HUẤN LUYỆN VIÊN", bold=True, size=7.5, color=BRONZE)
        self.opts("Kết quả", ["Đăng ký gói ........................", "Online", "Hẹn lại", "Chưa phù hợp"],
                  x=M + 6, y=self.y - 20, size=8.5)
        y = self.y - 42
        half = (W - 2 * M - 30) / 2
        self.field(M + 6, half - 6, "HLV phụ trách", y=y)
        self.field(M + half + 24, half - 18, "Ngày bắt đầu gói", y=y)
        self.field(M + 6, W - 2 * M - 18, "Ghi chú", y=y - 22)
        self._dots(M + 6, y - 44, W - M - 12)
        self.y -= bh
        self.tinh_cach()
        self.c.save()
        return self.buf.getvalue()

    # ---------------------------------------------------------------- v3.6: trang bảng hỏi tính cách & động lực
    def tinh_cach(self):
        from core import khao_sat as ks
        self.new_page(first=False)
        self.section("07", "Hiểu bạn hơn", "Không có đáp án đúng / sai — chọn ý gần với bạn nhất")
        multi = {6, 9, 11}                                    # câu chọn nhiều (theo thứ tự trong CAU_HOI_IN)
        for i, (q, opts) in enumerate(ks.CAU_HOI_IN):
            cols = 1 if max(len(o) for o in opts) > 46 else 2
            need = 17 + 18 * ((len(opts) + cols - 1) // cols) + 8
            if self.y - need < 70:
                self.new_page(first=False)
            self.q(f"{i + 1}. {q}" + (" — chọn nhiều" if i in multi and "chọn nhiều" not in q else ""))
            self.grid(list(opts), cols=cols)
        if self.y - 60 < 70:
            self.new_page(first=False)
        self.lines(2, "Nếu 3 tháng nữa đạt mục tiêu, điều gì trong cuộc sống của bạn sẽ khác đi?")


@lru_cache(maxsize=1)
def make_pdf() -> bytes:
    return _Phieu().build()


FILE_NAME = f"{config.VERSION}_{config.VERSION_DATE}_Phieu_thong_tin_khach_hang_HoangAnhCoaching_F1.pdf"
