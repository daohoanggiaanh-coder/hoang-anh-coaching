"""v3.6 — Bảng hỏi tính cách & động lực (khách tự trả lời hoặc HLV hỏi trong buổi F1).

Mục đích: giúp HLV chọn cách nói chuyện, cách khen, lên giáo án, giữ chân và thời điểm xin giới thiệu — dùng chung với
🧠 Thấu hiểu khách (core/thau_hieu). Đây là bảng hỏi coaching đơn giản dựa trên các khung phổ biến (4 phong cách giao tiếp,
động lực nội tại / ngoại tại theo Thuyết Tự quyết, giai đoạn thay đổi hành vi) — KHÔNG phải trắc nghiệm tâm lý đã chuẩn hoá,
nên chỉ dùng làm gợi ý, HLV quan sát thêm trong buổi tập để chỉnh.
"""
from __future__ import annotations

from core import thau_hieu as th

# ------------------------------------------------------------------ 6 câu phong cách (mỗi lựa chọn → 1 phong cách)
PC = ["ket_qua", "nhiet_tinh", "on_dinh", "phan_tich"]
CAU_PC = [
    ("Khi bắt đầu một việc mới, bạn thường…",
     ["Đặt mục tiêu rõ và muốn thấy kết quả nhanh", "Hào hứng, rủ thêm bạn bè cùng làm",
      "Từ từ làm quen, cần thấy an toàn rồi mới tăng dần", "Tìm hiểu kỹ cách làm và lý do trước khi bắt tay"]),
    ("Buổi tập lý tưởng với bạn là…",
     ["Thử thách, mệt nhưng thấy rõ mình tiến bộ", "Vui, nhiều năng lượng, bài tập mới lạ",
      "Đều đặn, vừa sức, không bị quá tải", "Có kế hoạch rõ, biết vì sao tập từng bài"]),
    ("Khi bạn tập sai kỹ thuật, bạn muốn HLV…",
     ["Nói thẳng, ngắn gọn để sửa ngay", "Góp ý kèm lời động viên",
      "Nhẹ nhàng, hướng dẫn từ từ", "Giải thích nguyên nhân và cách sửa chi tiết"]),
    ("Điều dễ khiến bạn bỏ tập nhất…",
     ["Tập mãi không thấy kết quả", "Lặp lại mãi một kiểu, thấy nhàm chán",
      "Bị đau, sợ chấn thương hoặc lịch bị xáo trộn", "Không hiểu mình đang tập gì, thiếu kế hoạch"]),
    ("Khi quyết định một khoản chi lớn (VD gói tập), bạn thường…",
     ["Quyết nhanh nếu thấy hợp lý", "Theo cảm hứng hoặc người quen giới thiệu",
      "Cần thời gian, hỏi ý người thân", "So sánh kỹ thông tin và giá trị nhận được"]),
    ("Bạn thấy vui nhất khi được ghi nhận bằng…",
     ["Con số tiến bộ (cân, số đo, mức tạ)", "Lời khen, được chia sẻ thành quả",
      "Sự quan tâm, hỏi thăm thường xuyên", "Báo cáo chi tiết, biểu đồ rõ ràng"]),
]
KHEN_THEO_PC = {"ket_qua": "Đưa số liệu tiến bộ", "nhiet_tinh": "Khen trước người khác / đăng MXH (khi khách đồng ý)",
                "on_dinh": "Nhắn riêng sau buổi", "phan_tich": "Đưa số liệu tiến bộ"}

# ------------------------------------------------------------------ các câu còn lại
DONG_LUC_NOI = [("Vì tôi thích cảm giác khoẻ, nhẹ người hơn", 8), ("Vì muốn chứng minh bản thân làm được", 7),
                ("Vì muốn đẹp hơn, được người khác khen", 4), ("Vì bác sĩ / người thân khuyên", 2)]
DUY_TRI = [("Chưa từng tập đều đặn", "chuan_bi"), ("Từng tập nhưng dưới 1 tháng là bỏ", "chuan_bi"),
           ("Đang tập đều được 1–6 tháng", "hanh_dong"), ("Tập đều hơn 6 tháng", "duy_tri")]
CHIA_SE = ["Rất sẵn lòng — có thể đăng mạng xã hội", "Chỉ chia sẻ với người thân, bạn bè", "Muốn giữ riêng tư"]
NHAN_KS = th.NHAN

CAU_HOI_IN = [  # dùng cho phiếu giấy (trang 3) — cùng nội dung với bảng hỏi trên web
    *[(q, opts) for q, opts in CAU_PC],
    ("Lý do sâu xa khiến bạn muốn tập lúc này (chọn nhiều)", th.DONG_LUC),
    ("Bạn tập chủ yếu vì…", [x for x, _ in DONG_LUC_NOI]),
    ("Trước đây bạn duy trì tập luyện được bao lâu?", [x for x, _ in DUY_TRI]),
    ("Điều có thể cản trở bạn tập đều (chọn nhiều)", th.RAO_CAN),
    ("Bạn muốn HLV nhắn tin hỏi thăm…", NHAN_KS),
    ("Bạn thường sinh hoạt cùng nhóm nào (chọn nhiều)", th.MANG_LUOI),
    ("Khi có kết quả tốt, bạn có muốn chia sẻ hành trình của mình?", CHIA_SE),
]


def cham(ans: dict) -> dict:
    """ans: {pc0..pc5: chỉ số lựa chọn 0–3, dong_luc: [..], noi: chỉ số, duy_tri: chỉ số, rao_can: [..], nhan: str,
    mang_luoi: [..], chia_se: str, so_thich: str, ly_do_sau: str} → điểm phong cách + các trường cho hồ sơ Thấu hiểu."""
    diem = {p: 0 for p in PC}
    so = 0
    for i in range(len(CAU_PC)):
        v = ans.get(f"pc{i}")
        if isinstance(v, int) and 0 <= v < 4:
            diem[PC[v]] += 1
            so += 1
    top = max(diem.values()) if so else 0
    chinh = [p for p in PC if diem[p] == top] if top else []
    out = {"ks_diem": diem, "ks_so_cau": so, "ks_phong_cach": chinh[0] if len(chinh) == 1 else (chinh[0] if chinh else None),
           "ks_phong_cach_phu": [p for p in PC if p not in chinh[:1] and diem[p] >= max(2, top - 1)] if top else []}
    if isinstance(ans.get("noi"), int) and 0 <= ans["noi"] < len(DONG_LUC_NOI):
        out["dong_luc_noi"] = DONG_LUC_NOI[ans["noi"]][1]
    if isinstance(ans.get("duy_tri"), int) and 0 <= ans["duy_tri"] < len(DUY_TRI):
        out["giai_doan"] = DUY_TRI[ans["duy_tri"]][1]
    for f in ("dong_luc", "rao_can", "mang_luoi"):
        if ans.get(f):
            out[f] = list(ans[f])
    for f in ("nhan", "chia_se", "so_thich", "ly_do_sau"):
        if ans.get(f):
            out[f] = ans[f]
    if out.get("ks_phong_cach"):
        out["khen"] = [KHEN_THEO_PC[out["ks_phong_cach"]]]
    return out


def ap_vao_ho_so(hs: dict, ans: dict, ngay: str) -> dict:
    """Gộp kết quả bảng hỏi vào hồ sơ Thấu hiểu: danh sách thì gộp, ô đơn chỉ điền khi HLV chưa ghi (không ghi đè quan sát của HLV)."""
    kq = cham(ans)
    moi = {**hs, "ks": ans, "ks_ngay": ngay, "ks_diem": kq["ks_diem"], "ks_phong_cach": kq.get("ks_phong_cach"),
           "ks_phong_cach_phu": kq.get("ks_phong_cach_phu", [])}
    for f in ("dong_luc", "rao_can", "mang_luoi", "khen"):
        if kq.get(f):
            moi[f] = list(dict.fromkeys(list(hs.get(f) or []) + kq[f]))
    for f in ("dong_luc_noi", "giai_doan", "nhan", "so_thich", "ly_do_sau", "chia_se"):
        if kq.get(f) not in (None, "") and hs.get(f) in (None, "", []):
            moi[f] = kq[f]
    return moi


def tom_tat(hs: dict) -> list[str]:
    """Vài dòng gợi ý từ bảng hỏi cho HLV."""
    out = []
    pc = hs.get("ks_phong_cach")
    if pc in th.PHONG_CACH:
        ten, mo_ta = th.PHONG_CACH[pc]
        phu = [th.PHONG_CACH[p][0] for p in hs.get("ks_phong_cach_phu") or [] if p in th.PHONG_CACH]
        out.append(f"Bảng hỏi: phong cách chính **{ten}**" + (f", pha {', '.join(phu)}" if phu else "") + f" — {mo_ta}")
    cs = hs.get("chia_se")
    if cs == CHIA_SE[0]:
        out.append("Khách **sẵn lòng chia sẻ hành trình** → xin phép chụp ảnh tiến độ từ đầu; khi có kết quả rủ khách đăng câu chuyện "
                   "và mời bạn bè tập thử cùng.")
    elif cs == CHIA_SE[2]:
        out.append("Khách **muốn giữ riêng tư** → không đăng ảnh / tên; xin giới thiệu bằng cách nhờ khách rủ 1 người thân tập thử, "
                   "không nhắc tới mạng xã hội.")
    return out
