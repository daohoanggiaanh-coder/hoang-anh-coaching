# Hoàng Anh Coaching v1.0 (2026-10-31) — kiểm tra lõi: lưu trữ, đăng nhập, lịch, dinh dưỡng, giáo án, chuyển dữ liệu Atlas
import json
from datetime import date

import pytest

from core import auth, config, db, dinh_duong as dd, giao_an as ga, store, tien_do as td


@pytest.fixture(autouse=True)
def tam(tmp_path, monkeypatch):
    import os
    monkeypatch.setattr(config, "LOCAL_DIR", tmp_path)
    monkeypatch.setattr(config, "get", lambda key, default=None: os.environ.get(key, default))   # không bao giờ đọc Secrets thật
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


# ------------------------------------------------------------------ v1.1: giáo án Atlas, lộ trình
def test_giao_an_atlas_luu_va_cong_khach():
    from core import ga_atlas as ga
    _khach()
    plan = ga.generate("recomp", 1, 3, "Nữ", ["Lưng dưới"], "truoc_sau")
    assert all(len(b["bai"]) == 8 for b in plan)
    assert not any(it["id"] in ga.HAN_CHE["Lưng dưới"] for b in plan for it in b["bai"])
    assert ga.save("R001", {"muc_tieu": "recomp", "trinh_do": 1, "buoi_tuan": 3, "han_che": ["Lưng dưới"],
                            "ngay_bat_dau": "2026-10-29", "kieu": "truoc_sau"}, plan, "HLV")
    cur = ga.current("R001")
    assert cur and cur["buoi"] == plan
    s = ga.to_simple(db.latest("GiaoAn", "R001")[ga.KHOA.format("R001")], date(2026, 11, 2))
    assert s["buoi"][0]["bai"][0]["hiep"] >= 2 and s["buoi"][0]["bai"][0]["lan"]


def test_ghi_buoi_hlv_va_goi_y_ta():
    from core import buoi
    _khach()
    buoi.save("R001", {"ngay": date(2026, 10, 30), "buoi_ma": "A", "bai": [
        {"id": "leg_press", "ten": "Leg Press (máy)", "hiep": [{"kg": 60, "lan": 12}] * 3}], "ghi_chu_hlv": "bí mật"}, "HLV")
    last = buoi.last_for("R001", "leg_press")
    assert last and last["hiep"][0]["kg"] == 60
    assert buoi.target_kg({"ten": "Leg Press (máy)"}, "3×10–12", last) == 62.5
    assert ga.lich_su_bai("R001").iloc[0]["top_kg"] == 60


def test_lo_trinh_tien_do():
    from core import lo_trinh as lt
    _khach(can_muc_tieu=56, muc_tieu_loai="giam_mo")
    u = {"name": "HLV"}
    td.luu_so_do("R001", date(2026, 10, 1), "dau_khoa", {"can_nang": 62, "pbf": 33, "v_eo": 80}, "", u)
    for i, kg in enumerate([62, 61.6, 61.2, 60.8, 60.4]):
        td.luu_can("R001", date(2026, 10, 1 + 7 * i), kg, u)
    kq = lt.tien_do(store.client("R001"), date(2026, 10, 30))
    can = next(r for r in kq["rows"] if r["ma"] == "can_nang")
    assert can["dich"] == 56 and can["pct"] > 0 and can["toc_do_tuan"] < 0 and can["du_kien"]


def test_goi_theo_thoi_gian():
    k = _khach("R002", goi_buoi="", goi_ten="Online 12 tuần", goi_loai="tuan", goi_so=12, ngay_bat_dau="2026-10-29")
    assert store.han_goi(k) == date(2026, 1, 21).replace(year=2027)
    assert store.con_ngay(k, date(2026, 10, 31)) == 82
    assert store.con_lai(k) is None
    assert "còn 82 ngày" in store.mo_ta_goi(k, hom_nay=date(2026, 10, 31))
    t = _khach("R003", goi_loai="thang", goi_so=1, ngay_bat_dau="2026-01-31")
    assert store.han_goi(t) == date(2026, 2, 28)
    assert store.save_goi_list([{"ten": "Online 1 tháng", "loai": "thang", "so": 1, "gia": 2500000}], "HLV")
    assert store.goi_list()[0]["gia"] == 2500000


def test_quyen_mac_dinh_va_tat():
    from core import store
    q = store.quyen({})
    assert all(q.values()) and set(q) == set(store.QUYEN)
    q2 = store.quyen({"quyen": '{"thuc_don": false, "can": false, "so_do": false}'})
    tr = store.trang_khach(q2)
    assert not q2["thuc_don"] and tr == {"tap": True, "an": False, "tien_do": False, "cardio": True, "thanh_qua": True, "lo_trinh": True}


def test_dam_cao_va_trai_cay():
    from core import dinh_duong as dd
    h = dd.HoSo.tu_dict({"gioi_tinh": "Nữ", "tuoi": 35, "cao": 158, "kg": 58, "pbf": 34, "muc_tieu": "giam_mo", "so_bua": 4})
    kq = dd.tinh(h)
    assert kq["dam_g_kg"] >= 1.6
    ngay = dd.thuc_don_ngay(h, kq, True, 0, "R9", None, set())
    F = dd.foods()
    assert any(F[m]["nhom"] == "trai_cay" for b in ngay for m in b["mon"])
    assert dd.bo_sung(h) and all("bang_chung" in x for x in dd.bo_sung(h))


def test_dam_2g_kg_va_mon_viet():
    from core import dinh_duong as dd
    h = dd.HoSo.tu_dict({"gioi_tinh": "Nữ", "tuoi": 38, "cao": 158, "kg": 62, "pbf": 35, "muc_tieu": "giam_mo", "so_bua": 4})
    kq = dd.tinh(h)
    assert kq["dam"] == 124
    ngay = dd.thuc_don_ngay(h, kq, True, 0, "R9")
    assert sum(b["thuc"]["p"] for b in ngay) >= 0.97 * kq["tap"]["p"]
    mv = [b["mon_id"] for b in ngay if b.get("mon_id")]
    assert len(mv) >= 3 and len(set(mv)) == len(mv)
    h2 = dd.HoSo.tu_dict({**h.__dict__, "che_do": ["thuan_chay"]})
    for b in dd.thuc_don_ngay(h2, dd.tinh(h2), False, 1, "R9"):
        F = dd.foods()
        assert all(dd.duoc_an(F[m], ["thuan_chay"]) for m in b["mon"])


def test_cardio_bu_chia_deu():
    from datetime import date
    from core import cardio as cd
    c = cd.cai_dat("X")
    w = cd.tuan(c, [0, 1, 3, 4], [{"ngay": "2026-10-26", "phut": 0}], date(2026, 10, 28))
    them = [d["bu"] for d in w["ngay"] if not d["qua"]]
    assert w["thieu"] == 50 and sum(them) >= 45
    c["ranh"] = False
    w = cd.tuan(c, [0, 1, 3, 4], [], date(2026, 11, 1))                 # CN, cả tuần chưa làm: không dồn quá trần
    assert w["ngay"][6]["target"] <= c["nghi"]["toi_da"] and w["khong_bu"] > 0


def test_core_moi_buoi_lung_yeu():
    from core import ga_atlas as g
    for lv in (0, 1, 2):
        for b in g.generate("giam_mo", lv, 4, "Nữ", ["Lưng dưới"], "truoc_sau"):
            ids = [x["id"] for x in b["bai"]]
            assert any(x["nhom"] == "core" for x in b["bai"])
            assert "cable_crunch" not in ids and "lying_leg_raise" not in ids


def test_chuoi_lua_va_khien():
    from datetime import date, timedelta
    from core import dong_luc as dl
    hom = date(2026, 10, 31)
    D = {"can": set(), "tap_log": set(), "cardio": {}, "checkin": {}, "ngay_tap": set(), "q": {"can": True},
         "goc": {t: {"phut": 0} for t in range(7)}}
    for i in range(1, 9):                                   # 8 ngày trước: đủ cân + check-in
        d = hom - timedelta(days=i)
        D["can"].add(d)
        D["checkin"][d] = {}
    nv = dl.nhiem_vu(D, hom - timedelta(days=1))
    assert [x["id"] for x in nv] == ["can", "checkin"] and all(x["xong"] for x in nv)
    assert not any(x["xong"] for x in dl.nhiem_vu(D, hom))


def test_minh_hoa_bai():
    from core import minh_hoa as MH
    m = MH.tim("dead_bug")
    assert m and len(m["anh"]) == 2 and m["loi"]
    assert MH.tim(None, "Leg Press (máy)")["id"] == "leg_press"


def test_cat_avatar():
    import io
    from PIL import Image
    from core import hinh
    buf = io.BytesIO()
    Image.new("RGB", (900, 1600), "red").save(buf, "JPEG")
    out = hinh.cat_vuong(buf.getvalue(), 14, 62)
    assert Image.open(io.BytesIO(out)).size == (320, 320)


def test_an_ngoai_con_lai():
    from core import an_ngoai as an
    td = [{"bua": "sang", "kcal": 400, "p": 30, "c": 40, "f": 12, "thuc": {"kcal": 400, "p": 30, "c": 40, "f": 12}},
          {"bua": "trua", "kcal": 600, "p": 40, "c": 60, "f": 20, "thuc": {"kcal": 600, "p": 40, "c": 60, "f": 20}},
          {"bua": "toi", "kcal": 600, "p": 40, "c": 60, "f": 20, "thuc": {"kcal": 600, "p": 40, "c": 60, "f": 20}}]
    m = {"kcal": 1600, "p": 110, "c": 160, "f": 52}
    pho = an.mon()["com_tam"]
    logs = {"sang": {"loai": "dung"}, "trua": {"loai": "ngoai"} | an.macro(pho)}
    t = an.tong_ngay(td, logs, m)
    assert t["so_chua"] == 1 and set(t["chia"]) == {"toi"}
    assert abs(t["da"]["kcal"] - (400 + pho["kcal"])) < 1
    assert abs(t["chia"]["toi"]["kcal"] - (1600 - 400 - pho["kcal"])) < 1
    assert an.loi_khuyen(t)
    g = an.goi_y("giam_mo", t["chia"]["toi"], ["pho_bo"])
    assert g and all(x["hop"] != "han_che" for x in g)
    for x in an.data()["mon"]:   # macro khớp kcal trong khoảng hợp lý (trừ bia: cồn)
        if x["id"] != "bia":
            assert abs(x["p"] * 4 + x["c"] * 4 + x["f"] * 9 - x["kcal"]) / x["kcal"] < 0.15, x["id"]


def test_giai_doan():
    from core import cardio as cd, giai_doan as gd
    c = {k: (dict(v) if isinstance(v, dict) else v) for k, v in cd.MAC_DINH.items()}
    for n, so in ((12, 3), (4, 2), (1, 1), (8, 3), (16, 3)):
        G = gd.ke_hoach("giam_mo", n, 4, c, 9000, 2.0, True)
        assert len(G) == so and G[0]["tu"] == 1 and G[-1]["den"] == n
        assert all(G[i]["den"] + 1 == G[i + 1]["tu"] for i in range(len(G) - 1))
        assert all(g["tap"] and g["cardio"] and g["an"] and g["do"] and g["buoc"] >= 5000 for g in G)
    G = gd.ke_hoach("giam_mo", 12, 4, c, 9000, 2.0, True)
    assert G[0]["buoc"] < G[1]["buoc"] < G[2]["buoc"]
    assert any("bơ" in x for x in G[0]["an"])


def test_volume():
    from core import volume as vo
    from core import tu_van as tv
    ids = {b["id"] for n in tv.library()["nhom"].values() for b in n["bai"] if b["loai"] in ("C", "M", "I", "Core")}
    assert ids <= set(MAP_ := vo.MAP), sorted(ids - set(MAP_))          # bài tạ / core nào cũng có cơ
    out = {}
    vo.tinh_bai("bb_bench", 4, out)
    assert out == {"nguc": 4, "tay_sau": 2, "vai_truoc": 2}
    rows = {r["co"]: r for r in vo.danh_gia({"mong": 14, "nguc": 1}, "tb", ["mong"], True)}
    assert rows["mong"]["uu_tien"] and rows["mong"]["dat"] and rows["nguc"]["tt"] == "thieu" and rows["xo"]["tt"] == "chua"
    assert vo.moc("mong", "moi")[0] < vo.moc("mong", "cao")[2]
    assert any("thiếu" in x for x in vo.nhan_xet(list(vo.danh_gia({"mong": 3}, "tb", ["mong"], True)), ["mong"]))


def test_goi_khoa_bao_luu():
    from datetime import date
    from core import goi
    assert goi.tien("6.000.000") == 6_000_000 and goi.tien("2tr5") == 2_500_000 and goi.tien("6tr") == 6_000_000
    k = {"ma": "X1", "ho_ten": "A", "goi_loai": "tuan", "goi_so": 4, "ngay_bat_dau": "2026-10-01", "gia": "2tr5",
         "thanh_toan": [{"ngay": "2026-10-01", "so_tien": 1_000_000}], "trang_thai": "Đang tập"}
    assert goi.ngay_ket_thuc(k) == date(2026, 10, 28)
    assert goi.cong_no(k)["con_no"] == 1_500_000
    assert goi.trang_thai(k, date(2026, 10, 20), {})["vao"]
    assert not goi.trang_thai(k, date(2026, 10, 29), {})["vao"]
    k["bao_luu"] = [{"tu": "2026-10-10", "den": "2026-10-16", "ly_do": "ốm"}]
    assert goi.ngay_ket_thuc(k) == date(2026, 11, 4)
    t = goi.trang_thai(k, date(2026, 10, 12), {})
    assert t["ma"] == "bao_luu" and not t["vao"]
    assert goi.trang_thai(k, date(2026, 10, 30), {})["vao"]
    k["cho_vao"] = True
    assert goi.trang_thai(k, date(2026, 12, 1), {})["vao"]


def test_chu_ky_va_thong_tin():
    from datetime import date
    from core import chu_ky as ck, thong_tin as ttin
    c = {**ck.MAC_DINH, "ngay_bd": [date(2026, 9, 1), date(2026, 9, 30), date(2026, 10, 29)]}
    assert ck.do_dai_tb(c) == 29
    assert ck.ngay_thu(c, date(2026, 10, 30)) == (2, False)
    assert ck.ngay_thu(c, date(2026, 11, 27)) == (1, True)            # dự đoán kỳ tới
    assert ck.ngay_thu(c, date(2026, 11, 10)) is None
    assert ttin.SANG_DD[ttin.muc_tieu({"muc_tieu_loai": "suc_manh"})] == "giu"
    assert ttin.tu_dd("giu", {"muc_tieu_loai": "suc_manh"}) == "suc_manh"
    assert ttin.trinh_do({"kinh_nghiem": "1–3 năm"}) == 2 and ttin.trinh_do({"trinh_do": 3, "kinh_nghiem": "Dưới 6 tháng"}) == 3


def test_wow_ky_luc_va_xung_ho():
    from core import wow, xung_ho
    hist = [{"ngay": None, "bai": [{"id": "bb_hip_thrust", "ten": "Hip", "hiep": [{"kg": 50, "lan": 10}]}]}]
    moi = [{"id": "bb_hip_thrust", "ten": "Hip", "hiep": [{"kg": 60, "lan": 10}]}]
    pr = wow.ky_luc_moi(moi, hist)
    assert pr and pr[0]["kg"] == 60 and pr[0]["tang"] > 0
    assert not wow.ky_luc_moi(hist[0]["bai"], [{"bai": moi}])
    assert wow.the_ky_luc_png("A", pr[0], __import__("datetime").date(2026, 11, 5))[:4] == b"\x89PNG"
    assert xung_ho.doi("Chào bạn, kế hoạch của bạn. Bạn giỏi lắm. bạn bè", "chị Ngân") == \
        "Chào chị Ngân, kế hoạch của chị Ngân. Chị Ngân giỏi lắm. bạn bè"


def test_telegram_lien_ket(monkeypatch):
    from core import thong_bao as tb
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "t")
    code = tb.ma_lien_ket("R001")
    assert code.startswith("R001_") and code != tb.ma_lien_ket("R002")
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "khac")
    assert tb.ma_lien_ket("R001") != code                       # đổi token → mã cũ hết hiệu lực


def test_an_ai_offline_va_bua_them():
    from core import an_ai, an_ngoai as an
    r = an_ai.uoc_luong_offline("150g ức gà, 1 chén cơm trắng, 2 trứng gà", {"kcal": 500, "p": 40, "c": 50, "f": 15})
    assert len(r["mon"]) == 3 and 500 < r["tong"]["kcal"] < 700 and r["do_tin_cay"] == "thap"
    assert an_ai._sach({"mon": [{"ten": "Cơm", "kcal": "200", "p": 4, "c": 45, "f": 1}], "do_tin_cay": "xyz"})["do_tin_cay"] == "vua"
    td = [{"bua": "sang", "kcal": 400, "p": 30, "c": 40, "f": 10, "thuc": {"kcal": 400, "p": 30, "c": 40, "f": 10}}]
    t = an.tong_ngay(td, {"them_101010": {"loai": "ghi", "kcal": 200, "p": 10, "c": 20, "f": 5}}, {"kcal": 1500, "p": 100, "c": 150, "f": 50})
    assert t["da"]["kcal"] == 200 and t["so_chua"] == 1


def test_bmr_inbody():
    from core import dinh_duong as dd
    h = dd.HoSo.tu_dict({"gioi_tinh": "Nam", "tuoi": 30, "cao": 175, "kg": 75, "bmr_inbody": "1700"})
    assert dd.tinh(h)["bmr"] == 1700
    h2 = dd.HoSo.tu_dict({"gioi_tinh": "Nam", "tuoi": 30, "cao": 175, "kg": 75})
    assert dd.tinh(h2)["bmr"] != 1700


def test_nhap_kh_atlas():
    from core import nhap_kh_atlas as NA
    assert NA.cung_pt("Đào Hoàng Anh", "Hoàng Anh") and not NA.cung_pt("Nguyễn Văn B", "Hoàng Anh")
    R = NA.khach_atlas([{"ma_kh": "KH1", "ho_ten": "A", "thoi_gian": "1"}, {"ma_kh": "KH1", "ho_ten": "A2", "thoi_gian": "2"},
                        {"ma_kh": "KH2", "ho_ten": "B", "xoa": "1", "thoi_gian": "1"}])
    assert [r["ho_ten"] for r in R] == ["A2"]
    L = NA.lich_atlas([{"ma_kh": "KH1", "loai": "mau", "tu_ngay": "2026-01-01", "lich": '[{"thu": 0, "gio": "06:00"}]'},
                       {"ma_kh": "KH1", "loai": "mau", "tu_ngay": "2026-05-01", "lich": '[{"thu": 2, "gio": "18:30:00"}]'}])
    assert L["KH1"] == [{"thu": 2, "gio": "18:30"}]
    B = NA.buoi_atlas([{"ma_kh": "KH1", "id": "g1", "ngay": "2026-10-01"}, {"ma_kh": "KH1", "id": "g2", "ngay": "2026-10-02"},
                       {"ma_kh": "", "huy_id": "g2", "ngay": "", "xoa": "1"}])
    assert [r["id"] for r in B["KH1"]] == ["g1"]
    a = {"ma_kh": "KH1", "ho_ten": "Chị Ngân", "gioi_tinh": "Nữ", "so_buoi_goi": "24", "buoi_da_tap_truoc": "3",
         "moc_buoi_web": "1", "trang_thai": "Đã kết thúc", "ngay_het_han": "2026-12-31", "sdt": "'0901"}
    k = NA.chuyen_khach(a, [{"ma": "R004"}], "Atlas", 5, L["KH1"])
    assert k["ma"] == "R005" and k["da_tap_truoc"] == 7 and k["trang_thai"] == "Ngưng tập"
    assert k["phong_tap"] == "Atlas" and k["ma_atlas"] == "KH1" and k["sdt"] == "0901" and k["ngay_ket_thuc"] == "2026-12-31"
    k2 = NA.chuyen_khach(a, [{"ma": "R004", "ma_atlas": "KH1"}], "Atlas", 5, None)
    assert k2["ma"] == "R004"


def test_inbody_han(monkeypatch):
    from datetime import date
    from core import inbody
    monkeypatch.setattr(inbody, "lan_cuoi", lambda ma: date(2026, 11, 1))
    t = inbody.trang_thai({"ma": "R1"}, date(2026, 11, 7))
    assert t["han"] == date(2026, 11, 8) and t["con"] == 1 and not t["can"]
    assert inbody.trang_thai({"ma": "R1", "inbody_ky": 0}, date(2026, 11, 7)) is None
    t2 = inbody.trang_thai({"ma": "R1", "inbody_ky": "14"}, date(2026, 11, 20))
    assert t2["con"] == -5 and t2["can"]
    monkeypatch.setattr(inbody, "lan_cuoi", lambda ma: None)
    assert inbody.trang_thai({"ma": "R1"}, date(2026, 11, 7))["can"]
    B = [{"ma": "R1", "ngay": date(2026, 11, 6), "trang_thai": "xong", "gio": "6"},
         {"ma": "R1", "ngay": date(2026, 11, 9), "trang_thai": "hen", "gio": "6"}]
    assert inbody.buoi_do({"ma": "R1"}, {"han": date(2026, 11, 7)}, B, date(2026, 11, 7))["ngay"] == date(2026, 11, 9)


def test_thau_hieu_phong_cach_va_diem(monkeypatch):
    from datetime import date
    from core import store, thau_hieu as th
    hs = {"dh6": True, "dh7": True, "dh0": True}
    assert th.phong_cach(hs)[0] == "phan_tich"
    assert th.phong_cach({**hs, "phong_cach_tay": "on_dinh"})[0] == "on_dinh"
    assert th.phong_cach({})[0] is None
    monkeypatch.setattr(store, "con_lai", lambda k, H=None: 2)
    monkeypatch.setattr(store, "da_tap", lambda k, H=None: 20)
    cc = {"tong": 6, "xong": 2, "huy": 4, "ti_le": 2 / 6}
    d, ly = th.nguy_co({"ma": "R1"}, {"giai_doan": "chao_dao", "hai_long": 5}, cc)
    assert d >= 80 and ly
    g, _ = th.san_sang_gioi_thieu({"ma": "R1"}, {"hai_long": 10, "da_thay_ket_qua": True, "mang_luoi": ["Đồng nghiệp công ty"]},
                                   {"tong": 6, "xong": 6, "huy": 0, "ti_le": 1.0})
    assert g >= 80
    assert th.muc(65) == "Cao" and th.muc(10) == "Thấp"
    _ = date


def test_thuc_don_loi_khuan_trai_cay_chat_luong():
    F = dd.foods()
    for cd in (["thuong"], ["khong_sua"]):
        h = dd.HoSo(gioi_tinh="Nữ", tuoi=30, cao=158, kg=58, buoi_tuan=3, muc_tieu="giam_mo", so_bua=4, che_do=cd)
        kq = dd.tinh(h)
        tuan = dd.thuc_don_tuan(h, kq, "R009")
        for d in tuan:
            assert any("len_men" in F[x].get("tag", []) for b in d["bua"] for x in b["mon"]), (cd, d["thu"])
            for b in d["bua"]:
                for x in b["mon"]:
                    if F[x]["nhom"] == "trai_cay" and b["mau"] not in ("truoc", "sau"):
                        assert x in dd.TRAI_CAY_MT["giam_mo"], x
        q = dd.chat_luong_ngay(tuan[0]["bua"], h, tuan[0]["tap"])
        assert any(c["ten"].startswith("Lợi khuẩn") and c["ok"] for c in q)
        assert len(dd.chat_luong_tuan(tuan)) == 3 and dd.vi_chat(h)


def test_quet_inbody_khop_ten_va_luu_gop(tmp_path, monkeypatch):
    from datetime import date

    from core import quet_inbody as qi, tien_do as td, tu_van as tv
    DS = [{"ma": "A1", "ho_ten": "Nguyễn Thị Lan", "phong_tap": "Atlas"},
          {"ma": "A2", "ho_ten": "Trần Văn Hùng", "phong_tap": "Gold Gym"},
          {"ma": "A3", "ho_ten": "Lê Thị Lan", "phong_tap": "Online"}]
    assert qi.khop_khach("NGUYEN THI LAN", DS)[0] == "A1"
    assert qi.khop_khach("Tran Van Hung", DS)[0] == "A2"
    assert qi.khop_khach("Lan", DS)[0] is None          # 2 khách tên Lan → để HLV chọn
    assert qi.khop_khach("Pham Minh", DS)[0] is None
    r = tv.clean_inbody({"ten": "Nguyen Thi Lan", "ngay_do": "2019.01.01", "can_nang": 60, "bmr": 1300})
    assert r["ten"] == "Nguyen Thi Lan" and "ngay_do" not in r and r["bmr"] == 1300
    u = {"name": "test"}
    td.luu_so_do("A1", date(2026, 11, 2), "tuan", {"v_eo": 70}, "", u)
    td.luu_so_do("A1", date(2026, 11, 2), "tuan", {"pbf": 25, "bmr": 1300}, "", u, gop=True)
    sd = td.so_do("A1")
    assert sd.iloc[-1]["v_eo"] == 70 and sd.iloc[-1]["pbf"] == 25


def test_goi_buoi_da_tap_gia_han_va_doi_lich():
    from core import goi
    k = _khach()
    store.ghi_hen("R001", date(2026, 10, 5), "18:00", "xong", "HLV", goc="R001|2026-10-05|18:00")
    store.ghi_hen("R001", date(2026, 10, 7), "18:00", "xong", "HLV", goc="R001|2026-10-07|18:00")
    t = goi.tong_quan(k, hom=date(2026, 10, 8))
    assert (t["tong"], t["da"], t["con"]) == (12, 2, 10)
    # sổ PT nói đã tập 7 buổi → chỉnh; buổi ✅ sau đó vẫn cộng tiếp
    assert store.save_client(goi.dat_da_tap(k, 7), "HLV")
    store.ghi_hen("R001", date(2026, 10, 12), "18:00", "xong", "HLV", goc="R001|2026-10-12|18:00")
    k = store.client("R001")
    assert goi.tong_quan(k, hom=date(2026, 10, 13))["da"] == 8
    # gia hạn 24 buổi, cộng dồn 4 buổi còn
    k2 = goi.gia_han(k, "Gói 24 buổi", 24, date(2026, 10, 14), "9500000", cong_don=True)
    assert store.save_client(k2, "HLV")
    t = goi.tong_quan(store.client("R001"), hom=date(2026, 10, 14))
    assert (t["tong"], t["da"], t["so_goi"], t["tong_mua"]) == (28, 0, 2, 40)
    # dời buổi thứ 2 sang thứ 3 19:00 từ 19/10, các tuần trước giữ nguyên
    L = store.doi_lich_co_dinh(store.client("R001"), 0, "18:00", date(2026, 10, 19), 1, "19:00")
    k3 = {**store.client("R001"), "lich": json.dumps(L)}
    assert store.save_client(k3, "HLV")
    B = store.buoi([store.client("R001")], date(2026, 10, 12), date(2026, 10, 25))
    ngay = [(b["ngay"], b["gio"]) for b in B]
    assert (date(2026, 10, 12), "18:00") in ngay and (date(2026, 10, 20), "19:00") in ngay
    assert (date(2026, 10, 19), "18:00") not in ngay


def test_f1_sang_khach_khao_sat_va_tuoi_co_the():
    from core import f1, khao_sat as ks, thau_hieu as th, tu_van as tv
    store.save_goi_list([{"ten": "Gói 24 buổi", "loai": "buoi", "so": 24, "gia": 9500000}], "HLV")
    h = {"ho_ten": "Trần Văn Mới", "sdt": "0901234567", "gioi_tinh": "Nam", "tuoi": 35, "ngay_f1": "2026-11-10",
         "chieu_cao": 170, "can_nang": 80, "pbf": 27, "smm": 31, "mo_noi_tang": 11, "bmr": 1600, "v_eo": 92, "v_dui_p": 58,
         "ket_qua": "Đăng ký Gói 24 buổi", "muc_tieu": "giam_mo",
         "ks": {"pc0": 3, "pc1": 3, "pc2": 0, "pc3": 3, "pc4": 3, "pc5": 1, "chia_se": ks.CHIA_SE[0], "duy_tri": 1,
                "rao_can": ["Mau chán"], "ly_do_sau": "chạy được với con"}}
    ma = f1.sang_khach(h, "HLV")
    k = store.client(ma)
    assert k["goi_buoi"] in (24, "24") and k["goi_ten"] == "Gói 24 buổi"
    sd = td.so_do(ma, them=True)
    assert sd.iloc[-1]["pbf"] == 27 and sd.iloc[-1]["v_eo"] == 92 and sd.iloc[-1]["v_dui"] == 58 and sd.iloc[-1]["tuoi"] == 35
    hs = th.ho_so(ma)
    assert hs["ks_phong_cach"] == "phan_tich" and hs["giai_doan"] == "chuan_bi" and "Mau chán" in hs["rao_can"]
    assert th.phong_cach(hs)[0] == "phan_tich"
    # gửi lại lần 2 không tạo trùng khách
    assert f1.sang_khach(h, "HLV") == ma
    from views import chi_so_ui
    ev = tv.evaluate(chi_so_ui.ho_so_do(k, sd.iloc[-1].to_dict()))
    assert ev["tuoi_co_the"]["gia_tri"] > 35
