# Hoàng Anh Coaching v1.0 (2026-10-31) — kiểm tra lõi: lưu trữ, đăng nhập, lịch, dinh dưỡng, giáo án, chuyển dữ liệu Atlas
import json
from datetime import date

import pytest

from core import auth, config, db, dinh_duong as dd, giao_an as ga, store, tien_do as td


@pytest.fixture(autouse=True)
def tam(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "LOCAL_DIR", tmp_path)
    for k in ("SHEETS_WEBAPP_URL", "COACH_PASSWORD", "COACH_USERNAME"):
        monkeypatch.delenv(k, raising=False)
    db.clear()
    auth._FAILS.clear()
    yield
    db.clear()


def _khach(ma="R001", **kw):
    k = {"ma": ma, "ho_ten": "Nguyễn Thị Lan", "goi_khach": "chị Lan", "xung_toi": "em", "goi_buoi": 12,
         "ngay_bat_dau": "2026-10-01", "lich": [{"thu": 0, "gio": "18:00"}, {"thu": 2, "gio": "18:00"}],
         "gioi_tinh": "Nữ", "chieu_cao": 158, "can_muc_tieu": 55, **kw}
    assert store.save_client(k, "HLV")
    return store.client(ma)


# ------------------------------------------------------------------ lưu trữ
def test_latest_va_xoa():
    db.append("KhachHang", "R001", {"ma": "R001", "ho_ten": "A"}, "x", "R001")
    db.append("KhachHang", "R001", {"ma": "R001", "ho_ten": "B"}, "x", "R001")
    db.append("KhachHang", "R002", {"ma": "R002", "ho_ten": "C", "xoa": 1}, "x", "R002")
    d = db.latest("KhachHang")
    assert d["R001"]["ho_ten"] == "B" and "R002" not in d
    assert "R002" in db.latest("KhachHang", ca_xoa=True)


def test_loc_theo_khach():
    db.append("CanNang", "R001|2026-10-01", {"ma": "R001", "ngay": "2026-10-01", "kg": 60}, "x", "R001")
    db.append("CanNang", "R002|2026-10-01", {"ma": "R002", "ngay": "2026-10-01", "kg": 80}, "x", "R002")
    assert list(db.latest("CanNang", "R001")) == ["R001|2026-10-01"]
    assert td.can_ngay("R002")["kg"].tolist() == [80]


# ------------------------------------------------------------------ đăng nhập
def test_mat_khau_bam():
    salt, h = auth.hash_pw("abc123")
    assert auth.check_pw("abc123", salt, h) and not auth.check_pw("abc124", salt, h)
    assert "abc123" not in h


def test_dang_nhap_khach_va_khoa():
    _khach()
    ok, loi = auth.save_account("R001", "Lan.Nguyen", "matkhau1", "HLV")
    assert ok, loi
    u, _ = auth.login("lan.nguyen", "matkhau1")
    assert u and u["role"] == "client" and u["ma_kh"] == "R001"
    assert auth.login("lan.nguyen", "sai")[0] is None
    tok = auth.make_token(u)
    assert auth.read_token(tok)["ma_kh"] == "R001"
    auth.save_account("R001", "lan.nguyen", "matkhau2", "HLV")            # đặt lại mật khẩu → vé cũ hết hiệu lực
    assert auth.read_token(tok) is None
    acc = auth.account_of("R001")
    auth.save_account("R001", "lan.nguyen", None, "HLV", khoa=True, cu=acc)
    assert auth.login("lan.nguyen", "matkhau2")[0] is None


def test_trung_ten_va_doi_ten():
    _khach("R001")
    _khach("R002", ho_ten="Trần Văn B")
    assert auth.save_account("R001", "lan", "matkhau1", "HLV")[0]
    assert not auth.save_account("R002", "lan", "matkhau1", "HLV")[0]
    assert auth.save_account("R001", "lan2", None, "HLV")[0]                # đổi tên, giữ mật khẩu
    assert "lan" not in auth.accounts() and auth.login("lan2", "matkhau1")[0]


def test_khoa_thu_5_lan():
    _khach()
    auth.save_account("R001", "lan", "matkhau1", "HLV")
    for _ in range(5):
        auth.login("lan", "sai")
    u, loi = auth.login("lan", "matkhau1")
    assert u is None and "5 phút" in loi


def test_hlv_demo_chi_khi_chay_thu(monkeypatch):
    assert auth.login("demo", "demo")[0]["role"] == "coach"
    monkeypatch.setenv("SHEETS_WEBAPP_URL", "https://x")
    assert auth.login("demo", "demo")[0] is None                          # đã nối Sheets mà chưa đặt mật khẩu → không vào được


# ------------------------------------------------------------------ lịch & đếm buổi
def test_lich_va_dem_buoi():
    k = _khach()
    store.ghi_hen("R001", date(2026, 10, 5), "18:00", "xong", "HLV", goc="R001|2026-10-05|18:00")
    store.ghi_hen("R001", date(2026, 10, 7), "18:00", "huy", "HLV", goc="R001|2026-10-07|18:00")
    H = store.hens()
    B = store.buoi([k], date(2026, 10, 5), date(2026, 10, 11), H)
    assert [b["trang_thai"] for b in B] == ["xong", "huy"]
    assert store.da_tap(k, H) == 1 and store.con_lai(k, H) == 11


# ------------------------------------------------------------------ dinh dưỡng
def test_mifflin_va_katch():
    h = dd.HoSo(gioi_tinh="Nam", tuoi=30, cao=175, kg=75, van_dong="ngoi", buoi_tuan=0, muc_tieu="giu")
    kq = dd.tinh(h)
    assert kq["bmr_m"] == round(10 * 75 + 6.25 * 175 - 5 * 30 + 5)
    h.pbf = 20
    kq = dd.tinh(h)
    assert kq["bmr"] == round(370 + 21.6 * 60)


def test_ngay_tap_nhieu_hon_ngay_nghi_va_san():
    h = dd.HoSo(gioi_tinh="Nữ", tuoi=30, cao=155, kg=50, van_dong="ngoi", buoi_tuan=3, muc_tieu="giam_mo", toc_do="nhanh")
    kq = dd.tinh(h)
    assert kq["tap"]["kcal"] >= kq["nghi"]["kcal"] >= kq["san"] >= 1200
    assert kq["tap"]["p"] == kq["nghi"]["p"]


def test_thuc_don_khop_macro_va_che_do():
    F = dd.foods()
    for h in (dd.HoSo(gioi_tinh="Nam", tuoi=28, cao=172, kg=68, buoi_tuan=4, muc_tieu="tang_co", so_bua=5, che_do=["thuan_chay"]),
              dd.HoSo(gioi_tinh="Nữ", tuoi=35, cao=160, kg=65, pbf=34, buoi_tuan=3, muc_tieu="giam_mo", so_bua=4, gio_tap="toi",
                      che_do=["khong_hai_san", "khong_bo"])):
        kq = dd.tinh(h)
        for d in dd.thuc_don_tuan(h, kq, "R001"):
            m = kq["tap"] if d["tap"] else kq["nghi"]
            t = {x: sum(b["thuc"][x] for b in d["bua"]) for x in ("kcal", "p")}
            assert abs(t["kcal"] - m["kcal"]) / m["kcal"] < 0.08
            assert abs(t["p"] - m["p"]) <= 12
            for b in d["bua"]:
                for mon in b["mon"]:
                    assert dd.duoc_an(F[mon], h.che_do), mon


# ------------------------------------------------------------------ giáo án & số tạ
def test_e1rm_va_goi_y():
    assert ga.e1rm(100, 1) == 100 and ga.e1rm(100, 10) == pytest.approx(133.3, 0.01)
    bai = {"bai": "Barbell Back Squat", "nhom": "squat", "lan": "8-10", "hiep": 3}
    kg, _ = ga.goi_y(bai, {"sets": [{"kg": 60, "lan": 10}] * 3})
    assert kg == 65
    kg, _ = ga.goi_y({**bai, "nhom": "day_ngang"}, {"sets": [{"kg": 40, "lan": 10}, {"kg": 40, "lan": 8}]})
    assert kg == 40


def test_nhat_ky_va_ky_luc():
    _khach()
    ga.save_log("R001", {"ngay": "2026-10-01", "bai": [{"bai": "Dumbbell Bench Press", "sets": [{"kg": 14, "lan": 10}]}]}, "Lan")
    ga.save_log("R001", {"ngay": "2026-10-08", "bai": [{"bai": "Dumbbell Bench Press", "sets": [{"kg": 16, "lan": 8}]}]}, "Lan")
    ls = ga.lich_su_bai("R001")
    assert len(ls) == 2
    assert ga.ky_luc(ls).iloc[0]["top_kg"] == 16
    assert ga.lan_truoc("R001", "Dumbbell Bench Press")["sets"][0]["kg"] == 16


def test_giao_an_mau_hop_le():
    from views.common import config_mau
    mau = config_mau()
    tv = ga.thu_vien()
    assert set(mau) >= {"giam_mo", "tang_co"}
    for m in mau.values():
        assert m["bai"] and all(b["bai"] in tv for b in m["bai"])


# ------------------------------------------------------------------ chuyển dữ liệu Atlas
def test_chuyen_atlas():
    from views.coach import chuyen_atlas
    kh = {"ma": "R001", "ho_ten": "Lan", "goi_buoi": 12, "lich": [{"thu": 0, "gio": "18:00"}]}
    rows = [
        {"thoi_gian": "2026-10-20 08:00:00", "loai": "rieng_kh", "su_kien": "R001", "noi_dung": json.dumps({**kh, "ho_ten": "Lan cũ"})},
        {"thoi_gian": "2026-10-21 08:00:00", "loai": "rieng_kh", "su_kien": "R001", "noi_dung": json.dumps(kh)},
        {"thoi_gian": "2026-10-21 09:00:00", "loai": "rieng_hen", "su_kien": "R001|2026-10-20|18:00",
         "noi_dung": json.dumps({"ma": "R001", "ngay": "2026-10-20", "gio": "18:00", "trang_thai": "xong"})},
        {"thoi_gian": "2026-10-22 07:00:00", "loai": "rieng_can", "su_kien": "R001|2026-10-22",
         "noi_dung": json.dumps({"ma": "R001", "ngay": "2026-10-22", "kg": 61.2})},
        {"thoi_gian": "2026-10-22 07:00:00", "loai": "quiz", "su_kien": "x", "noi_dung": "{}"},          # dữ liệu Atlas: bỏ qua
        {"thoi_gian": "2026-10-22 07:00:00", "loai": "rieng_cho", "su_kien": "abc", "noi_dung": "{}"},   # hàng chờ: bỏ qua
    ]
    dem = chuyen_atlas(rows, "test", False)
    assert dem["KhachHang"] == 1 and dem["LichHen"] == 1 and dem["CanNang"] == 1
    k = store.client("R001")
    assert k["ho_ten"] == "Lan" and store.da_tap(k) == 1
    assert chuyen_atlas(rows, "test", False)["KhachHang"] == 0                # chạy lại không nhân đôi
