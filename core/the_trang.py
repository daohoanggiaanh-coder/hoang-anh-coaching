# Atlas Academy v3.64 (2026-10-22) — Thể trạng đầu buổi: HLV hỏi khách hôm nay thấy thế nào → giáo án đề xuất
# tăng tạ / giữ tạ / giảm tạ / đổi hình thức tập, và tự chỉnh mức tạ gợi ý, số hiệp, RPE mục tiêu của buổi.
from __future__ import annotations

import re

# mức: tang · giu · giam · doi (đổi hình thức). kg = hệ số mức tạ gợi ý; hiep = bớt số hiệp; rpe = hạ RPE mục tiêu.
TINH_TRANG: dict[str, dict] = {
    "Rất khoẻ": {"icon": "💪", "muc": "tang", "kg": 1.0, "hiep": 0, "rpe": 0,
                 "loi": "Khách sung sức — bài compound / multi tăng 1 bậc tạ (đã đủ lần buổi trước thì lên tạ, chưa đủ thì cố thêm lần)."},
    "Khoẻ": {"icon": "🙂", "muc": "giu", "kg": 1.0, "hiep": 0, "rpe": 0,
             "loi": "Tập đúng giáo án — tăng tạ theo gợi ý từng bài."},
    "Hơi mệt": {"icon": "😐", "muc": "giam", "kg": 0.9, "hiep": 0, "rpe": 1,
                "loi": "Giảm khoảng 10% tạ, giữ số hiệp, ưu tiên kỹ thuật chuẩn; khởi động kỹ hơn 3–5 phút."},
    "Mệt / thiếu ngủ": {"icon": "😴", "muc": "giam", "kg": 0.85, "hiep": 1, "rpe": 2,
                        "loi": "Giảm ~15% tạ, bớt 1 hiệp mỗi bài, không thử tạ nặng; nhắc khách ngủ đủ 7–8 tiếng."},
    "Đau nhức cơ": {"icon": "🥵", "muc": "giam", "kg": 0.9, "hiep": 1, "rpe": 1,
                    "loi": "Đau mỏi cơ sau buổi trước (DOMS): khởi động lâu hơn, giảm ~10% tạ, bớt 1 hiệp ở nhóm cơ còn đau; "
                           "ưu tiên máy, biên độ kiểm soát."},
    "Đau khớp / chấn thương": {"icon": "🩹", "muc": "doi", "kg": 0.8, "hiep": 1, "rpe": 2,
                               "loi": "Không tập vào vùng đau: đổi bài ở vùng đó (bấm tên bài → chọn bài khác) hoặc ghi vào "
                                      "“Vùng cần tránh”; tạ nhẹ, không đau mới tập. Đau nhói / sưng → dừng, khuyên khách đi khám."},
    "Ốm / bệnh": {"icon": "🤒", "muc": "doi", "kg": 0.7, "hiep": 1, "rpe": 3, "nhe": True,
                  "loi": "Đổi sang buổi phục hồi nhẹ: giãn cơ, kích hoạt, đi bộ nhẹ 15–20 phút. Sốt, ho nhiều, "
                         "triệu chứng dưới cổ (ngực, bụng) → cho khách nghỉ hẳn, hẹn buổi khác."},
    "Tới tháng": {"icon": "🌸", "muc": "giam", "kg": 0.85, "hiep": 1, "rpe": 1, "nu": True, "core_nhe": True,
                  "loi": "Ngày đầu chu kỳ: giảm 10–20% tạ, bớt 1 hiệp; tránh bài ép bụng mạnh, treo / nâng chân; "
                         "ưu tiên thân trên và máy, cardio nhẹ. Khách thấy khoẻ thì tập như bình thường."},
}
MUC = {"tang": ("TĂNG TẠ", "#1E7B4A"), "giu": ("GIỮ GIÁO ÁN", "#A3803C"), "giam": ("GIẢM TẠ", "#D98E04"),
       "doi": ("ĐỔI HÌNH THỨC", "#C0392B")}
CORE_NANG = {"lying_leg_raise", "cable_crunch", "hang_knee_raise", "weighted_plank"}
CORE_NHE = ["dead_bug", "bird_dog", "side_plank"]


def lua_chon(gioi: str = "") -> list[str]:
    return [k for k, v in TINH_TRANG.items() if not v.get("nu") or gioi == "Nữ"]


def get(tt: str | None) -> dict:
    return TINH_TRANG.get(tt or "", TINH_TRANG["Khoẻ"])


def kg_goi_y(tk: float | None, tt: str | None, loai: str, buoc: float) -> float | None:
    """Mức tạ gợi ý sau khi chỉnh theo thể trạng (làm tròn theo bậc tạ của bài)."""
    if not tk:
        return tk
    c = get(tt)
    if c["muc"] == "tang" and loai in ("C", "M"):
        return tk + buoc
    if c["kg"] >= 1:
        return tk
    return max(buoc, round(tk * c["kg"] / buoc) * buoc)


def so_hiep(n: int, tt: str | None, loai: str) -> int:
    c = get(tt)
    return n if loai in ("A",) else max(1, n - c["hiep"]) if n > 2 else n


def rpe(rpe_txt: str, tt: str | None) -> str:
    """'RPE 7–8' hạ theo thể trạng → 'RPE 6–7'."""
    d = get(tt)["rpe"]
    if not d or not rpe_txt:
        return rpe_txt
    return re.sub(r"\d+", lambda m: str(max(5, int(m.group()) - d)), rpe_txt)


def nhan_xet(tt: str | None, en: bool = False) -> str:
    """Câu cho báo cáo gửi khách (không nêu chi tiết riêng tư như chu kỳ)."""
    c = get(tt)
    if c["muc"] == "tang":
        return "Strong day — we pushed the main lifts up a notch." if en else \
            "Hôm nay thể trạng rất tốt nên tăng tạ ở các bài chính."
    if c["muc"] in ("giam", "doi"):
        return ("Your body wasn't at 100% today, so we lowered the intensity to focus on technique and recovery." if en else
                "Hôm nay cơ thể chưa ở trạng thái tốt nhất nên giảm cường độ, ưu tiên kỹ thuật và hồi phục.")
    return ""


# ------------------------------------------------------------------ v3.64: điểm sẵn sàng tập (4 câu, mỗi câu 1–5, 5 = tốt nhất)
CAU = [("ngu", "😴 Giấc ngủ đêm qua", ["Rất tệ", "Tệ", "Bình thường", "Tốt", "Rất ngon"]),
       ("nang_luong", "⚡ Năng lượng lúc này", ["Kiệt sức", "Mệt", "Bình thường", "Khoẻ", "Rất sung"]),
       ("dau_co", "🥵 Đau mỏi cơ", ["Rất đau", "Đau", "Hơi mỏi", "Ít", "Không"]),
       ("cang_thang", "🧠 Căng thẳng / áp lực", ["Rất nhiều", "Nhiều", "Vừa", "Ít", "Thoải mái"])]


def diem_san_sang(tl: dict) -> tuple[int, str]:
    """{ngu, nang_luong, dau_co, cang_thang: 1–5} → (điểm 0–100, thể trạng đề xuất trong TINH_TRANG)."""
    v = {k: int(tl.get(k) or 3) for k, *_ in CAU}
    diem = round((sum(v.values()) - 4) / 16 * 100)
    if v["dau_co"] <= 2 and min(v["ngu"], v["nang_luong"]) >= 3:
        return diem, "Đau nhức cơ"
    if diem >= 85:
        return diem, "Rất khoẻ"
    if diem >= 65:
        return diem, "Khoẻ"
    if diem >= 50:
        return diem, "Hơi mệt"
    return diem, "Mệt / thiếu ngủ"


def mau_diem(d: int) -> str:
    return "#1E7B4A" if d >= 85 else "#5BA36B" if d >= 65 else "#D98E04" if d >= 50 else "#C0392B"
