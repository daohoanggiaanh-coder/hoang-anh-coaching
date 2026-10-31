# Hoàng Anh Coaching v1.0 (2026-10-31) — đăng nhập: huấn luyện viên (Secrets) + khách (tài khoản do HLV cấp)
"""
- HLV: COACH_USERNAME + COACH_PASSWORD trong Secrets.
- Khách: tài khoản do HLV tạo ở trang Khách & tài khoản. Mật khẩu lưu dạng băm PBKDF2-SHA256 (có muối),
  không ai đọc lại được mật khẩu gốc — quên thì HLV đặt lại.
- Ghi nhớ đăng nhập: cookie "hac_dn" có chữ ký HMAC. Vé của khách gắn với dấu mật khẩu hiện tại
  → HLV đặt lại mật khẩu hoặc khoá tài khoản thì mọi máy đang nhớ đăng nhập tự bị đăng xuất.
- Sai mật khẩu 5 lần liên tiếp → khoá thử 5 phút (theo tên đăng nhập, trên máy chủ).
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import string
import time
import unicodedata

from core import config, db

COOKIE = "hac_dn"
REMEMBER_DAYS = 60
ITER = 200_000
_FAILS: dict[str, list[float]] = {}


# ------------------------------------------------------------------ mật khẩu
def hash_pw(pw: str, salt: str | None = None) -> tuple[str, str]:
    salt = salt or secrets.token_hex(16)
    h = hashlib.pbkdf2_hmac("sha256", pw.encode("utf-8"), bytes.fromhex(salt), ITER).hex()
    return salt, h


def check_pw(pw: str, salt: str, h: str) -> bool:
    try:
        return hmac.compare_digest(hash_pw(pw, salt)[1], str(h))
    except (ValueError, TypeError):
        return False


def tao_mat_khau(n: int = 8) -> str:
    """Mật khẩu dễ đọc qua Zalo: bỏ ký tự dễ nhầm (0/O, 1/l/I)."""
    bang = "".join(c for c in string.ascii_lowercase + string.digits if c not in "0o1li")
    return "".join(secrets.choice(bang) for _ in range(n))


def norm_user(u: str) -> str:
    u = unicodedata.normalize("NFKD", str(u or "")).encode("ascii", "ignore").decode()
    return "".join(c for c in u.lower().strip() if c.isalnum() or c in "._-")


# ------------------------------------------------------------------ tài khoản khách
def accounts() -> dict[str, dict]:
    """{username: tài khoản} — bản mới nhất theo username."""
    return {k: v for k, v in db.latest("TaiKhoan").items()}


def account_of(ma_kh: str) -> dict | None:
    for v in accounts().values():
        if v.get("ma_kh") == ma_kh:
            return v
    return None


def save_account(ma_kh: str, username: str, password: str | None, nguoi: str, khoa: bool = False,
                 cu: dict | None = None) -> tuple[bool, str]:
    """Tạo / đổi mật khẩu / khoá. password=None → giữ mật khẩu cũ."""
    u = norm_user(username)
    if len(u) < 3:
        return False, "Tên đăng nhập cần ít nhất 3 ký tự (chữ không dấu, số, . _ -)."
    if u == norm_user(config.get("COACH_USERNAME", "")):
        return False, "Tên này trùng tài khoản HLV."
    ds = accounts()
    if u in ds and ds[u].get("ma_kh") != ma_kh:
        return False, "Tên đăng nhập đã có người dùng."
    cu = cu or account_of(ma_kh)
    if password is not None:
        if len(password) < 6:
            return False, "Mật khẩu cần ít nhất 6 ký tự."
        salt, h = hash_pw(password)
    elif cu:
        salt, h = cu.get("salt", ""), cu.get("hash", "")
    else:
        return False, "Cần đặt mật khẩu."
    if cu and norm_user(cu.get("_khoa")) != u:            # đổi tên đăng nhập → xoá tên cũ
        db.append("TaiKhoan", cu["_khoa"], {"ma_kh": ma_kh, "xoa": 1}, nguoi, ma_kh)
    ok = db.append("TaiKhoan", u, {"ma_kh": ma_kh, "salt": salt, "hash": h, "khoa": bool(khoa)}, nguoi, ma_kh)
    return ok, "" if ok else "Chưa lưu được — kiểm tra kết nối."


# ------------------------------------------------------------------ đăng nhập
def _bi_khoa(u: str) -> bool:
    t = [x for x in _FAILS.get(u, []) if time.time() - x < 300]
    _FAILS[u] = t
    return len(t) >= 5


def login(username: str, password: str) -> tuple[dict | None, str]:
    u = norm_user(username)
    if not u or not password:
        return None, "Nhập tên đăng nhập và mật khẩu."
    if _bi_khoa(u):
        return None, "Sai quá 5 lần — thử lại sau 5 phút."
    cu, cp = norm_user(config.get("COACH_USERNAME", "")), str(config.get("COACH_PASSWORD", "") or "")
    if not cp and not db._url():                       # chạy thử cục bộ: HLV demo / demo
        cu, cp = cu or "demo", "demo"
    if cu and cp and hmac.compare_digest(u, cu) and hmac.compare_digest(password.encode(), cp.encode()):
        return {"role": "coach", "name": str(config.get("COACH_NAME", "Hoàng Anh")), "username": u}, ""
    acc = accounts().get(u)
    if acc and not acc.get("khoa") and check_pw(password, acc.get("salt", ""), acc.get("hash", "")):
        from core import store
        k = store.client(acc["ma_kh"])
        if k:
            _FAILS.pop(u, None)
            return {"role": "client", "name": k.get("ho_ten", ""), "username": u, "ma_kh": acc["ma_kh"]}, ""
    _FAILS.setdefault(u, []).append(time.time())
    return None, "Sai tên đăng nhập hoặc mật khẩu."


# ------------------------------------------------------------------ vé ghi nhớ
def _secret() -> bytes:
    raw = "|".join(str(config.get(k, "")) for k in ("COOKIE_SECRET", "COACH_PASSWORD", "SHEETS_TOKEN"))
    return hashlib.sha256(("hac|" + raw).encode()).digest()


def _dau(user: dict) -> str:
    """Dấu tài khoản: đổi mật khẩu / khoá → dấu đổi → vé cũ hết hiệu lực."""
    if user.get("role") == "coach":
        return hashlib.sha256(str(config.get("COACH_PASSWORD", "")).encode()).hexdigest()[:10]
    acc = accounts().get(user.get("username", "")) or {}
    return "x" if acc.get("khoa") else str(acc.get("hash", ""))[:10]


def make_token(user: dict) -> str:
    body = json.dumps({"u": user["username"], "r": user["role"], "d": _dau(user),
                       "e": int(time.time()) + REMEMBER_DAYS * 86400}, separators=(",", ":"))
    data = base64.urlsafe_b64encode(body.encode()).decode().rstrip("=")
    return f"{data}.{hmac.new(_secret(), data.encode(), hashlib.sha256).hexdigest()[:40]}"


def read_token(tok: str | None) -> dict | None:
    try:
        data, sig = str(tok or "").split(".", 1)
        if not hmac.compare_digest(sig, hmac.new(_secret(), data.encode(), hashlib.sha256).hexdigest()[:40]):
            return None
        d = json.loads(base64.urlsafe_b64decode(data + "=" * (-len(data) % 4)))
        if int(d["e"]) < time.time():
            return None
        if d["r"] == "coach":
            u = {"role": "coach", "name": str(config.get("COACH_NAME", "Hoàng Anh")), "username": d["u"]}
        else:
            acc = accounts().get(d["u"])
            if not acc:
                return None
            from core import store
            k = store.client(acc["ma_kh"])
            if not k:
                return None
            u = {"role": "client", "name": k.get("ho_ten", ""), "username": d["u"], "ma_kh": acc["ma_kh"]}
        return u if hmac.compare_digest(_dau(u), str(d.get("d"))) else None
    except (ValueError, KeyError, TypeError):
        return None


# ------------------------------------------------------------------ phần dính Streamlit
def current_user() -> dict | None:
    import streamlit as st
    u = st.session_state.get("user")
    return u if isinstance(u, dict) else None


def run_js(code: str) -> None:
    import streamlit as st
    import streamlit.components.v1 as components
    html = f"<script>{code}</script>"
    if hasattr(st, "iframe"):
        try:
            st.iframe(html, height=1)
            return
        except Exception:  # noqa: BLE001
            pass
    components.html(html, height=0)


def read_browser() -> None:
    """Đọc vé ghi nhớ trong trình duyệt bằng 1 thành phần ẩn → đăng nhập thẳng."""
    import streamlit as st
    if st.session_state.get("user") or st.session_state.get("_da_dang_xuat"):
        return
    try:
        import streamlit.components.v1 as components
        comp = components.declare_component("hac_dn", path=str(config.ROOT / "components" / "hac_dn"))
        got = comp(key="_hac_dn_reader", default=None)
    except Exception:  # noqa: BLE001
        return
    if isinstance(got, dict) and got.get("dn"):
        u = read_token(got["dn"])
        if u:
            st.session_state.user = u
            st.session_state["_cookie_set"] = make_token(u)
            st.rerun()


def sync_cookie() -> None:
    import streamlit as st
    tok, drop = st.session_state.pop("_cookie_set", None), st.session_state.pop("_cookie_del", False)
    if not tok and not drop:
        return
    val = f"{COOKIE}={tok}; Max-Age={REMEMBER_DAYS * 86400}" if tok else f"{COOKIE}=; Max-Age=0"
    ls = f"localStorage.setItem('{COOKIE}','{tok}')" if tok else f"localStorage.removeItem('{COOKIE}')"
    run_js(f"(function(){{var c='{val}; Path=/; SameSite=Lax; Secure';"
           "try{window.parent.document.cookie=c;}catch(e){} try{document.cookie=c;}catch(e){}"
           f"try{{window.parent.{ls};}}catch(e){{}} try{{window.{ls};}}catch(e){{}}}})();")


def set_user(u: dict, nho: bool = True) -> None:
    import streamlit as st
    st.session_state.user = u
    st.session_state.pop("_da_dang_xuat", None)
    if nho:
        st.session_state["_cookie_set"] = make_token(u)


def logout() -> None:
    import streamlit as st
    for k in list(st.session_state.keys()):
        del st.session_state[k]
    st.session_state["_da_dang_xuat"] = True
    st.session_state["_cookie_del"] = True
