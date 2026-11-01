# Hoàng Anh Coaching v1.0 (2026-10-31) — điểm vào: đăng nhập → trang HLV hoặc cổng khách
# Chạy local:  streamlit run app.py   (chưa nối Google Sheets → dữ liệu lưu data/_local, HLV đăng nhập demo / demo)
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).parent
st.set_page_config(page_title="Hoàng Anh Coaching", page_icon=str(ROOT / "assets" / "app" / "icon-192.png")
                   if (ROOT / "assets" / "app" / "icon-192.png").exists() else "💪", layout="wide")

def _fresh_core():
    """Streamlit Cloud sau mỗi lần đẩy bản mới đôi khi nạp lại trang (views) nhưng giữ module core.* cũ → AttributeError.
    File VERSION khác bản đang chạy → nạp lại toàn bộ core.* (config trước), rồi views.* (giống Atlas Academy v3.30)."""
    import importlib
    import sys
    cfg = sys.modules.get("core.config")
    if not cfg:
        return
    try:
        v = (ROOT / "VERSION").read_text(encoding="utf-8").split("·")[0].strip()
    except OSError:
        return
    if v and v != getattr(cfg, "VERSION", v):
        importlib.reload(cfg)
        for n in sorted(m for m in list(sys.modules) if m.startswith(("core.", "views.")) and m != "core.config"):
            try:
                importlib.reload(sys.modules[n])
            except Exception:  # noqa: BLE001
                pass


_fresh_core()
from core import auth, config, db, pwa, ui  # noqa: E402

ui.setup()
auth.sync_cookie()


def _duong_dan() -> str:
    from urllib.parse import urlparse
    try:
        return urlparse(st.context.url or "").path.strip("/").split("/")[-1]
    except Exception:  # noqa: BLE001
        return ""


pwa.chen_icon()


def man_dang_nhap():
    if "_dich" not in st.session_state:
        st.session_state["_dich"] = _duong_dan()        # mở link trang con → đăng nhập xong vào thẳng trang đó
    auth.read_browser()
    st.markdown("<style>[data-testid='stSidebar'],[data-testid='stSidebarCollapsedControl']{display:none!important}</style>",
                unsafe_allow_html=True)
    _, giua, _ = st.columns([1, 1.3, 1])
    with giua:
        st.markdown("<div style='height:4vh'></div>"
                    f"<div style='text-align:center;margin-bottom:10px'><img src='data:image/png;base64,{pwa.logo_b64()}' "
                    "style='width:92px;height:92px;border-radius:22px;box-shadow:0 10px 30px rgba(0,0,0,.25)'></div>",
                    unsafe_allow_html=True)
        ui.hero(config.BRAND, "Chào mừng bạn quay lại 💪", "Giáo án · thực đơn · số tạ · tiến độ — riêng cho bạn.")
        with st.form("login"):
            u = st.text_input("Tên đăng nhập", autocomplete="username")
            p = st.text_input("Mật khẩu", type="password", autocomplete="current-password")
            nho = st.checkbox("Ghi nhớ đăng nhập trên máy này", value=True)
            if st.form_submit_button("Đăng nhập", type="primary", use_container_width=True):
                user, loi = auth.login(u, p)
                if user:
                    auth.set_user(user, nho)
                    st.rerun()
                st.error(loi)
        st.caption("Chưa có tài khoản hoặc quên mật khẩu? Nhắn HLV Hoàng Anh để được cấp lại.")
        if not db._url():
            st.caption("🧪 Đang chạy thử (chưa nối Google Sheets) — HLV đăng nhập **demo / demo**.")
    ui.footer()


user = auth.current_user()
if not user:
    man_dang_nhap()
    st.stop()

if user["role"] == "coach":
    from views import coach as V
    pages = {
        "Huấn luyện": [st.Page(V.lich, title="Lịch & nhắc tập", icon="📅", url_path="lich", default=True),
                       st.Page(V.cam_ket, title="Cam kết khách", icon="🔥", url_path="cam_ket"),
                       st.Page(V.ho_so, title="Hồ sơ HLV & thành quả", icon="🏆", url_path="ho_so"),
                       st.Page(V.khach, title="Khách & tài khoản", icon="👤", url_path="khach"),
                       st.Page(V.tap, title="Giáo án khách", icon="🏋️", url_path="tap"),
                       st.Page(V.cardio, title="Cardio", icon="🏃", url_path="cardio"),
                       st.Page(V.an, title="Dinh dưỡng", icon="🍽", url_path="dinh_duong"),
                       st.Page(V.tien_do, title="Tiến độ & báo cáo", icon="📈", url_path="tien_do"),
                       st.Page(V.lo_trinh, title="Lộ trình & mục tiêu 🔒", icon="🎯", url_path="lo_trinh"),
                       st.Page(V.khach_thay, title="Khách thấy gì", icon="👁", url_path="khach_thay")],
        "Công cụ": [st.Page(V.soan_tin, title="Soạn tin Zalo", icon="✉️", url_path="soan_tin"),
                    st.Page(V.thuc_pham, title="Bảng thực phẩm", icon="🥗", url_path="thuc_pham"),
                    st.Page(V.nhap_atlas, title="Chuyển dữ liệu từ Atlas", icon="📥", url_path="nhap_atlas")],
    }
else:
    from views import client as V
    from core import store as _st
    _tr = _st.trang_khach(_st.quyen(_st.client(user.get("ma_kh", ""))))
    pages = [st.Page(V.trang_chu, title="Tổng quan", icon="🏠", url_path="tong_quan", default=True)]
    pages += [p for p, on in ((st.Page(V.tap, title="Tập luyện", icon="🏋️", url_path="tap_luyen"), _tr["tap"]),
                              (st.Page(V.cardio, title="Cardio", icon="🏃", url_path="cardio"), _tr["cardio"]),
                              (st.Page(V.an, title="Thực đơn", icon="🍽", url_path="thuc_don"), _tr["an"]),
                              (st.Page(V.tien_do, title="Cân & số đo", icon="📈", url_path="can_so_do"), _tr["tien_do"]),
                              (st.Page(V.thanh_qua, title="Thành quả", icon="🏆", url_path="thanh_qua"), _tr["thanh_qua"])) if on]
    pages.append(st.Page(V.tai_khoan, title="Tài khoản", icon="🔐", url_path="tai_khoan"))

st.logo(str(ROOT / "assets" / "app" / "wordmark-dark.png"), size="large", icon_image=str(ROOT / "assets" / "app" / "icon-192.png"))
with st.sidebar:
    st.markdown(f"<div style='font-size:.7rem;letter-spacing:.14em;color:#A8A091;font-weight:700'>"
                f"{'HUẤN LUYỆN VIÊN' if user['role'] == 'coach' else 'HỌC VIÊN'}</div>"
                f"<div style='font-size:1.05rem;font-weight:800;margin:2px 0 10px'>{ui.E(user['name'])}</div>", unsafe_allow_html=True)
nav = st.navigation(pages, position="top" if user["role"] == "client" else "sidebar")
with st.sidebar:
    if st.button("Đăng xuất", use_container_width=True):
        auth.logout()
        st.rerun()
    st.caption(f"Dữ liệu: {db.backend()}")
_dich = st.session_state.pop("_dich", None)
if _dich and _dich != nav.url_path:
    _all = [x for g in (pages.values() if isinstance(pages, dict) else [pages]) for x in g]
    _to = next((x for x in _all if x.url_path == _dich), None)
    if _to:
        st.switch_page(_to)
nav.run()
ui.footer()
