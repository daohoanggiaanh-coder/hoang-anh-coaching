"""v3.1 — 🧠 Thấu hiểu khách (CHỈ HLV thấy).

Ghi lại những gì HLV quan sát / hỏi được trong tư vấn và buổi tập → web gợi ý cách nói chuyện, lên giáo án,
giữ chân, và thời điểm + cách xin giới thiệu khách. Đây là gợi ý huấn luyện dựa trên quan sát của HLV,
KHÔNG phải trắc nghiệm hay chẩn đoán tâm lý.

Khung tham khảo (đều là khung phổ biến trong coaching, dùng ở mức đơn giản):
  • Động lực nội tại / ngoại tại (gợi từ Thuyết Tự quyết — Self-Determination Theory, Deci & Ryan).
  • Giai đoạn thay đổi hành vi (Transtheoretical Model — Prochaska & DiClemente).
  • 4 phong cách giao tiếp quan sát được (kiểu chia 4 nhóm hay dùng trong bán hàng / huấn luyện) — chỉ để chọn cách nói,
    không dán nhãn con người.
  • Điểm giới thiệu 0–10 (kiểu câu hỏi NPS: "Khả năng anh/chị giới thiệu mình cho bạn bè?").
DinhDuong keys:  th|ma (hồ sơ) · th_nk|ma|ngày (nhật ký quan sát) · lead|id (khách tiềm năng) · th_muc_tieu (mục tiêu nguồn khách).
"""
from __future__ import annotations

import uuid
from datetime import date, timedelta

from core import db, store

# ------------------------------------------------------------------ danh mục
PHONG_CACH = {
    "ket_qua": ("🎯 Thích kết quả nhanh", "Nói thẳng, quyết nhanh, ghét vòng vo, thích thử thách và con số tiến bộ."),
    "nhiet_tinh": ("🔥 Nhiệt tình – thích giao lưu", "Vui vẻ, nói nhiều, thích được khen, thích mới lạ, dễ chán nếu lặp lại."),
    "on_dinh": ("🌿 Ổn định – cần an toàn", "Nhẹ nhàng, ngại thay đổi đột ngột, cần thấy an toàn và được quan tâm, trung thành lâu dài."),
    "phan_tich": ("📊 Phân tích – cần lý do", "Hỏi nhiều 'tại sao', thích số liệu, kỹ tính, cần hiểu mới làm hết sức."),
}
# 8 dấu hiệu quan sát — mỗi dấu hiệu cộng điểm cho 1 phong cách
DAU_HIEU = [
    ("Hay hỏi 'bao lâu thì có kết quả', muốn đi thẳng vào việc", "ket_qua"),
    ("Thích được thử thách, tăng tạ, phá kỷ lục", "ket_qua"),
    ("Nói chuyện nhiều, hay kể chuyện, thích chụp hình / check-in", "nhiet_tinh"),
    ("Hào hứng với bài mới, chán khi lặp lại giáo án", "nhiet_tinh"),
    ("Ngại đổi giờ / đổi bài, thích lịch cố định", "on_dinh"),
    ("Ít nói, hay lo bị đau / chấn thương, cần trấn an", "on_dinh"),
    ("Hay hỏi 'tại sao tập bài này', đọc kỹ số đo / InBody", "phan_tich"),
    ("Ghi chép, làm đúng từng chi tiết, không thích ước chừng", "phan_tich"),
]
DONG_LUC = ["Sức khoẻ / bệnh nền", "Ngoại hình – vóc dáng", "Tự tin bản thân", "Sức bền – hiệu suất",
            "Sự kiện sắp tới (cưới, du lịch, chụp ảnh…)", "Bác sĩ khuyên", "Giảm stress – tinh thần", "Làm gương cho con / gia đình",
            "Bạn bè / người thân rủ"]
GIAI_DOAN = {
    "chuan_bi": "🌱 Mới bắt đầu (< 1 tháng)",
    "hanh_dong": "🏃 Đang thay đổi (1–6 tháng)",
    "duy_tri": "🏆 Duy trì (> 6 tháng)",
    "chao_dao": "⚠️ Đang chao đảo / có dấu hiệu bỏ",
}
RAO_CAN = ["Bận công việc / hay tăng ca", "Đi công tác", "Con nhỏ / gia đình", "Ăn ngoài, tiếp khách nhiều", "Ngủ ít / stress",
           "Đau mỏi / chấn thương cũ", "Mau chán", "Ngại chi phí", "Thiếu kiên nhẫn với kết quả", "Ngại tập nơi đông người"]
KHEN = ["Khen trực tiếp trong buổi", "Nhắn riêng sau buổi", "Đưa số liệu tiến bộ", "Khen trước người khác / đăng MXH (khi khách đồng ý)"]
NHAN = ["Ít tin nhắn, chỉ việc cần", "Vừa phải (2–3 lần / tuần)", "Thích được hỏi thăm thường xuyên"]
LEAD_TT = ["Mới có tên", "Đã nhắn / gọi", "Đã tư vấn", "Đã tập thử", "Đã đăng ký ✅", "Chưa hợp / để sau"]


# ------------------------------------------------------------------ đọc / ghi
def _dd() -> dict:
    return db.latest("DinhDuong")


def ho_so(ma: str) -> dict:
    v = _dd().get(f"th|{ma}", {})
    return {k: x for k, x in v.items() if not str(k).startswith("_")} if isinstance(v, dict) else {}


def luu(ma: str, hs: dict, nguoi: str) -> bool:
    return db.append("DinhDuong", f"th|{ma}", {**hs, "cap_nhat": db.now_vn().date().isoformat()}, nguoi, ma)


def nhat_ky(ma: str) -> list[dict]:
    out = []
    for k, v in _dd().items():
        if str(k).startswith(f"th_nk|{ma}|") and isinstance(v, dict) and not v.get("xoa"):
            out.append({**v, "_key": k})
    return sorted(out, key=lambda x: str(x.get("ngay", "")), reverse=True)


def ghi_nhat_ky(ma: str, ngay: date, noi_dung: str, nhan: str, nguoi: str) -> bool:
    key = f"th_nk|{ma}|{ngay.isoformat()}|{uuid.uuid4().hex[:6]}"
    return db.append("DinhDuong", key, {"ngay": ngay.isoformat(), "noi_dung": noi_dung, "nhan": nhan}, nguoi, ma)


def leads() -> list[dict]:
    out = [{**v, "id": k.split("|", 1)[1]} for k, v in _dd().items()
           if str(k).startswith("lead|") and isinstance(v, dict) and not v.get("xoa")]
    return sorted(out, key=lambda x: str(x.get("ngay", "")), reverse=True)


def luu_lead(ld: dict, nguoi: str) -> bool:
    lid = ld.get("id") or uuid.uuid4().hex[:10]
    data = {k: v for k, v in ld.items() if k != "id" and not str(k).startswith("_")}
    return db.append("DinhDuong", f"lead|{lid}", data, nguoi, data.get("nguon_ma", ""))


def muc_tieu_nguon() -> dict:
    v = _dd().get("th_muc_tieu", {})
    return v if isinstance(v, dict) else {}


# ------------------------------------------------------------------ phân tích
def phong_cach(hs: dict) -> tuple[str | None, dict[str, int]]:
    """Phong cách chính: HLV chọn tay > đếm dấu hiệu quan sát."""
    diem = {k: 0 for k in PHONG_CACH}
    for i, (_, pc) in enumerate(DAU_HIEU):
        if hs.get(f"dh{i}"):
            diem[pc] += 1
    tay = hs.get("phong_cach_tay")
    if tay in PHONG_CACH:
        return tay, diem
    top = max(diem.values())
    return (max(diem, key=diem.get) if top else None), diem


def chuyen_can(k: dict, hom: date, ngay: int = 21) -> dict:
    """Tỉ lệ đi tập ~3 tuần qua (buổi đã qua: xong / (xong + huỷ + chưa chấm))."""
    B = [b for b in store.buoi([k], hom - timedelta(days=ngay), hom - timedelta(days=1)) if b["ma"] == k["ma"]]
    xong = sum(b["trang_thai"] == "xong" for b in B)
    huy = sum(b["trang_thai"] == "huy" for b in B)
    tong = len(B)
    # anh chưa chấm buổi nào (toàn "hẹn") → không đủ dữ liệu, không tính để khỏi báo động nhầm
    return {"tong": tong, "xong": xong, "huy": huy, "ti_le": (xong / tong) if tong and (xong + huy) else None}


def nguy_co(k: dict, hs: dict, cc: dict) -> tuple[int, list[str]]:
    """Điểm nguy cơ bỏ tập 0–100 + lý do (quy tắc đơn giản, chỉ để ưu tiên chăm sóc)."""
    d, ly = 0, []
    if cc["ti_le"] is not None and cc["tong"] >= 3:
        if cc["ti_le"] < 0.5:
            d += 40
            ly.append(f"đi tập {cc['xong']}/{cc['tong']} buổi 3 tuần qua")
        elif cc["ti_le"] < 0.75:
            d += 20
            ly.append(f"nghỉ {cc['tong'] - cc['xong']}/{cc['tong']} buổi 3 tuần qua")
    if hs.get("giai_doan") == "chao_dao":
        d += 25
        ly.append("anh đánh giá đang chao đảo")
    elif hs.get("giai_doan") == "chuan_bi":
        d += 10
        ly.append("mới bắt đầu — giai đoạn dễ bỏ nhất")
    rc = hs.get("rao_can") or []
    if len(rc) >= 3:
        d += 15
        ly.append(f"{len(rc)} rào cản")
    try:
        hl = int(hs.get("hai_long"))
        if hl <= 6:
            d += 20
            ly.append(f"mức hài lòng {hl}/10")
    except (TypeError, ValueError):
        pass
    try:
        if int(hs.get("dong_luc_noi", 5)) <= 3:
            d += 10
            ly.append("động lực chủ yếu từ bên ngoài")
    except (TypeError, ValueError):
        pass
    cl = store.con_lai(k)
    if cl is not None and cl <= 3:
        d += 10
        ly.append(f"gói còn {cl} buổi — thời điểm dễ không gia hạn")
    return min(d, 100), ly


def san_sang_gioi_thieu(k: dict, hs: dict, cc: dict) -> tuple[int, list[str]]:
    """Điểm sẵn sàng giới thiệu 0–100: hài lòng + đã thấy kết quả + gắn bó + có mạng lưới."""
    d, ly = 0, []
    try:
        hl = int(hs.get("hai_long"))
        d += {10: 40, 9: 35, 8: 20, 7: 10}.get(hl, 0)
        if hl >= 9:
            ly.append(f"hài lòng {hl}/10")
    except (TypeError, ValueError):
        ly.append("chưa hỏi mức hài lòng")
    if hs.get("da_thay_ket_qua"):
        d += 20
        ly.append("khách đã thấy kết quả")
    n = store.da_tap(k)
    if n >= 12:
        d += 15
        ly.append(f"đã tập {n} buổi")
    elif n >= 6:
        d += 8
    if cc["ti_le"] is not None and cc["ti_le"] >= 0.8:
        d += 10
    mang = hs.get("mang_luoi") or []
    if mang:
        d += min(15, 5 * len(mang))
        ly.append("có mạng lưới: " + ", ".join(mang[:3]))
    return min(d, 100), ly


MANG_LUOI = ["Đồng nghiệp công ty", "Nhóm bạn thân", "Gia đình / họ hàng", "Hội phụ huynh", "Khách hàng / đối tác của khách",
             "Hội nhóm sở thích (chạy bộ, golf, yoga…)", "Có ảnh hưởng MXH (nhiều người theo dõi)"]


# ------------------------------------------------------------------ hướng dẫn cụ thể
def _xh(k: dict) -> str:
    return store.xung(k)[0] if hasattr(store, "xung") else "bạn"


GOI_Y_PC = {
    "ket_qua": {
        "noi": ["Vào thẳng việc: mục tiêu buổi hôm nay là gì, đo bằng gì.", "Báo con số tiến bộ ngắn gọn (kg, buổi, % mỡ) — không kể dài.",
                "Cho khách quyền chọn giữa 2 phương án — họ thích được làm chủ."],
        "tap": ["Có 1 bài 'thử thách' mỗi buổi (tăng tạ / rep / thời gian) và ghi lại kỷ lục.", "Đặt mốc ngắn 2–4 tuần, công bố trước.",
                "Tránh để khách ngồi chờ — nhịp buổi tập nhanh, gọn."],
        "tranh": "Tránh giải thích lý thuyết dài, hứa hẹn mơ hồ, hoặc để buổi tập 'nhẹ quá'.",
        "gt": "Xin giới thiệu ngay sau khi phá kỷ lục / đạt mốc: “Kết quả này người quen anh/chị cũng muốn có — ai đang cần thì cho em xin số, em tư vấn miễn phí 1 buổi.”",
    },
    "nhiet_tinh": {
        "noi": ["Hỏi thăm chuyện đời sống 2–3 phút đầu buổi.", "Khen nhiệt tình, cụ thể (‘form squat hôm nay đẹp nhất từ trước tới giờ’).",
                "Chụp ảnh / quay clip tiến bộ để khách đăng (khi khách muốn)."],
        "tap": ["Đổi bài / dụng cụ mỗi 2–3 tuần để khỏi chán.", "Thêm trò chơi, thử thách cặp, buổi tập đôi với bạn của khách.",
                "Mỗi tháng có 1 ‘sự kiện nhỏ’ (đo InBody so sánh, buổi tập chủ đề)."],
        "tranh": "Tránh giáo án lặp lại y nguyên, tin nhắn khô khan, lạnh lùng.",
        "gt": "Rủ khách dẫn 1 người bạn tới ‘buổi tập đôi miễn phí’ — kiểu khách này giới thiệu tự nhiên nhất khi được tập cùng bạn.",
    },
    "on_dinh": {
        "noi": ["Giọng nhẹ nhàng, nhắc khách mình luôn để ý an toàn cho khách.", "Báo trước mọi thay đổi (giờ, bài, cường độ) ít nhất 1 buổi.",
                "Hỏi cảm giác cơ thể sau mỗi bài, ghi nhận lo lắng của khách."],
        "tap": ["Giữ lịch cố định, cùng khung giờ, tăng tải từ từ (≤ 5–10%/tuần).", "Khởi động kỹ, giải thích kỹ thuật an toàn.",
                "Ghi chú các bài khách tự tin để mở đầu buổi bằng bài đó."],
        "tranh": "Tránh ép tăng tạ đột ngột, đổi giờ sát giờ, hoặc so sánh khách với người khác.",
        "gt": "Không xin dồn dập. Sau 2–3 tháng, nói nhẹ: “Nếu có người thân của chị muốn tập an toàn như chị, chị cứ giới thiệu em nhé.” — người thân trong gia đình là nguồn tốt nhất.",
    },
    "phan_tich": {
        "noi": ["Giải thích ‘tại sao’ của từng giai đoạn giáo án (1–2 câu, có số liệu).", "Gửi bảng số đo / biểu đồ trước – sau.",
                "Trả lời câu hỏi bằng dữ liệu; chưa chắc thì hẹn tìm hiểu rồi trả lời, không đoán."],
        "tap": ["Cho khách xem volume tuần, kỷ lục, % mỡ theo thời gian.", "Lên kế hoạch rõ ràng theo tuần, ít thay đổi bất ngờ.",
                "Dạy khách tự ghi chép ăn uống / buổi tập."],
        "tranh": "Tránh nói chung chung (‘cứ tập là lên’), sai số liệu, hoặc thay đổi mà không giải thích.",
        "gt": "Đưa khách ‘bằng chứng’: báo cáo tiến độ đẹp để khách tự gửi người quen; xin giới thiệu theo hướng ‘ai đang cần một lộ trình bài bản’.",
    },
}

GOI_Y_RC = {
    "Bận công việc / hay tăng ca": "Chuẩn bị sẵn giáo án rút gọn 30 phút; cho phép dời lịch linh hoạt trong tuần thay vì huỷ.",
    "Đi công tác": "Gửi bài tập khách sạn / không dụng cụ 20 phút; hẹn ngày quay lại trước khi khách đi.",
    "Con nhỏ / gia đình": "Chọn khung giờ cố định ít bị gián đoạn; gợi ý bài tập tại nhà 10–15 phút những tuần khó.",
    "Ăn ngoài, tiếp khách nhiều": "Dùng mục 🍽 ăn ngoài để chọn món; dạy quy tắc đĩa ăn đơn giản thay vì đếm calo chi tiết.",
    "Ngủ ít / stress": "Giảm cường độ những ngày ngủ < 6 tiếng; thêm bài thở / giãn cơ cuối buổi; hỏi về giấc ngủ đầu buổi.",
    "Đau mỏi / chấn thương cũ": "Kiểm tra kỹ trước buổi; có phương án thay bài; ghi chú vị trí đau vào hồ sơ để không quên.",
    "Mau chán": "Đổi bài mỗi 2–3 tuần, thêm thử thách nhỏ, tổ chức buổi tập chủ đề.",
    "Ngại chi phí": "Nhấn mạnh giá trị từng buổi (kết quả đo được); gợi ý gói dài hơn có lợi hơn — không ép.",
    "Thiếu kiên nhẫn với kết quả": "Đặt mốc nhỏ 2 tuần ngoài cân nặng (vòng eo, sức mạnh, giấc ngủ) và cho khách thấy tiến bộ thường xuyên.",
    "Ngại tập nơi đông người": "Xếp giờ vắng; góc tập riêng; đây cũng là khách tiềm năng cho private studio.",
}

GOI_Y_GD = {
    "chuan_bi": "4 tuần đầu quyết định: ưu tiên để khách THÍCH buổi tập hơn là mệt. Mỗi buổi kết thúc bằng 1 điều khách làm tốt. Nhắn hỏi thăm sau buổi 1, 3, 6.",
    "hanh_dong": "Cho khách thấy tiến bộ thường xuyên (đo 1–2 tuần / lần), đặt mốc kế tiếp rõ ràng, chuẩn bị trước kế hoạch cho tuần bận.",
    "duy_tri": "Làm mới mục tiêu (mục tiêu sức mạnh, sự kiện thể thao, thử thách mới). Đây là nhóm giới thiệu khách tốt nhất — chủ động xin.",
    "chao_dao": "Gặp nói chuyện riêng 5 phút: hỏi điều gì đang khó, giảm kỳ vọng tạm thời (tối thiểu 2 buổi/tuần), hẹn lại mục tiêu nhỏ trong 2 tuần.",
}


def huong_dan(k: dict, hs: dict, hom: date) -> dict:
    """Gom toàn bộ gợi ý cho 1 khách + 3 việc ưu tiên tuần này."""
    pc, diem = phong_cach(hs)
    cc = chuyen_can(k, hom)
    nc, ly_nc = nguy_co(k, hs, cc)
    gt, ly_gt = san_sang_gioi_thieu(k, hs, cc)
    viec: list[str] = []
    if nc >= 50:
        viec.append("🚨 Gọi / gặp riêng tuần này: hỏi điều gì đang khó (" + "; ".join(ly_nc[:2]) + ").")
    if not hs.get("hai_long"):
        viec.append("❓ Hỏi khách 1 câu: “Từ 0–10, khả năng anh/chị giới thiệu em cho bạn bè là bao nhiêu? Điều gì làm nó cao hơn?”")
    if not pc:
        viec.append("👀 Quan sát thêm 1–2 buổi rồi tick dấu hiệu tính cách để web gợi ý cách nói chuyện.")
    if not hs.get("ly_do_sau"):
        viec.append("💬 Hỏi ‘lý do thật sự’: “Nếu 3 tháng nữa đạt mục tiêu, điều gì trong cuộc sống của anh/chị sẽ khác?”")
    if hs.get("giai_doan") in GOI_Y_GD and len(viec) < 3:
        viec.append("🧭 " + GOI_Y_GD[hs["giai_doan"]].split(".")[0] + ".")
    if gt >= 60 and len(viec) < 3:
        viec.append("🤝 Khách đang ở thời điểm tốt để xin giới thiệu — dùng câu gợi ý ở mục Giới thiệu.")
    rc = hs.get("rao_can") or []
    if rc and len(viec) < 3:
        viec.append("🧱 " + GOI_Y_RC.get(rc[0], rc[0]))
    if pc and len(viec) < 3:
        viec.append("🗣 " + GOI_Y_PC[pc]["noi"][0])
    return {"pc": pc, "diem": diem, "cc": cc, "nguy_co": nc, "ly_nc": ly_nc, "gt": gt, "ly_gt": ly_gt, "viec": viec[:4]}


def muc(d: int, cao: str = "Cao", tb: str = "Trung bình", thap: str = "Thấp") -> str:
    return cao if d >= 60 else (tb if d >= 30 else thap)
