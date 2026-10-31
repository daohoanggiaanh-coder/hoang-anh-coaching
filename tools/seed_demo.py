# Hoàng Anh Coaching v1.0 — dữ liệu mẫu để chạy thử cục bộ (KHÔNG chạy khi đã nối Google Sheets)
import random
import sys
from datetime import timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from core import auth, db, giao_an as ga, store, tien_do as td  # noqa: E402

assert not db._url(), "Đã nối Google Sheets — không tạo dữ liệu mẫu"
hom = db.now_vn().date()
bd = hom - timedelta(days=28)
store.save_client({"ma": "R001", "ho_ten": "Nguyễn Thị Lan", "goi_khach": "chị Lan", "xung_toi": "em", "goi_buoi": 24, "ngay_bat_dau": bd.isoformat(),
                   "lich": [{"thu": 0, "gio": "18:30"}, {"thu": 2, "gio": "18:30"}, {"thu": 4, "gio": "18:30"}], "gioi_tinh": "Nữ",
                   "chieu_cao": 158, "can_muc_tieu": 56, "muc_tieu": "Giảm mỡ bụng, gọn eo", "ngay_sinh": "1992-05-14",
                   "hinh_thuc": "Kết hợp", "dia_diem": "Aqua City", "sdt": "0901234567", "ten_zalo": "Lan Nguyễn"}, "HLV")
store.save_client({"ma": "R002", "ho_ten": "Trần Minh Tuấn", "goi_khach": "anh Tuấn", "xung_toi": "em", "goi_buoi": 12,
                   "ngay_bat_dau": (hom - timedelta(days=10)).isoformat(), "lich": [{"thu": 1, "gio": "06:00"}, {"thu": 3, "gio": "06:00"}],
                   "gioi_tinh": "Nam", "chieu_cao": 172, "muc_tieu": "Tăng cơ", "hinh_thuc": "Online", "ngay_sinh": "1996-02-02"}, "HLV")
auth.save_account("R001", "lan", "lan12345", "HLV")
u = {"name": "Hoàng Anh"}
random.seed(1)
kg = 63.4
for i in range(29):
    d = bd + timedelta(days=i)
    kg -= 0.06
    td.luu_can("R001", d, round(kg + random.uniform(-0.5, 0.5), 1), u)
    if d.weekday() in (0, 2, 4) and d < hom:
        store.ghi_hen("R001", d, "18:30", "xong", "HLV", goc=store.hen_id("R001", d, "18:30"))
td.luu_so_do("R001", bd, "dau_khoa", {"can_nang": 63.4, "pbf": 34.1, "smm": 22.0, "v_eo": 80, "v_bung": 88, "v_hong": 98, "mo_noi_tang": 7}, "", u)
td.luu_so_do("R001", hom - timedelta(days=1), "tuan", {"can_nang": 61.8, "pbf": 32.4, "smm": 22.3, "v_eo": 76.5, "v_bung": 84, "v_hong": 97}, "", u)
g = {"ten": "Giáo án tháng 10 · 3 buổi", "dang_dung": True, "tac_gia": "hlv", "ghi_chu": "Khởi động 8 phút xe đạp + mở khớp hông, vai.",
     "buoi": [{"ten": "Buổi A — Thân dưới", "bai": [
         {"bai": "Smith Machine Squat", "nhom": "squat", "hiep": 4, "lan": "8-10", "kg": 30, "rpe": 8, "nghi": 120},
         {"bai": "Dumbbell Romanian Deadlift", "nhom": "hinge", "hiep": 3, "lan": "10-12", "kg": 12, "rpe": 8, "nghi": 90},
         {"bai": "Dumbbell Reverse Lunge", "nhom": "mot_chan", "hiep": 3, "lan": "10", "kg": 6, "nghi": 60, "ss": "A"},
         {"bai": "Barbell Hip Thrust", "nhom": "hinge", "hiep": 3, "lan": "12-15", "kg": 40, "nghi": 60, "ss": "A"}]},
              {"ten": "Buổi B — Thân trên", "bai": [
         {"bai": "Dumbbell Bench Press", "nhom": "day_ngang", "hiep": 3, "lan": "8-10", "kg": 8, "rpe": 8, "nghi": 90},
         {"bai": "Lat Pulldown (máy)", "nhom": "keo_dung", "hiep": 3, "lan": "10-12", "kg": 25, "nghi": 90}]}]}
ga.save_plan("R001", g, "Hoàng Anh")
for j, w in enumerate((1, 2, 3, 4)):
    d = bd + timedelta(days=7 * j)
    ga.save_log("R001", {"ngay": d.isoformat(), "buoi": "Buổi A — Thân dưới", "nguoi_ghi": "hlv", "bai": [
        {"bai": "Smith Machine Squat", "sets": [{"kg": 25 + 2.5 * j, "lan": 10}] * 4},
        {"bai": "Barbell Hip Thrust", "sets": [{"kg": 30 + 5 * j, "lan": 12}] * 3}]}, "Hoàng Anh")
db.append("DinhDuong", "hs|R001", {"van_dong": "ngoi", "buoi_tuan": 3, "phut_buoi": 60, "cuong_do": "vua", "muc_tieu": "giam_mo",
                                   "toc_do": "vua", "so_bua": 4, "gio_tap": "toi", "che_do": ["thuong"]}, "HLV", "R001")
print("ok")
