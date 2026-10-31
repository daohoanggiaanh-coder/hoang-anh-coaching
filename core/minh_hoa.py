# Hoàng Anh Coaching v1.5 (2026-10-31) — hình minh hoạ + mẹo + lỗi hay sai cho từng bài tập
# Ảnh: free-exercise-db (public domain — github.com/yuhonas/free-exercise-db), đã thu nhỏ, lưu trong assets/bai/.
from __future__ import annotations

import functools
import re
from pathlib import Path

from core import config

ANH = Path(__file__).resolve().parent.parent / "assets" / "bai"


@functools.lru_cache(maxsize=1)
def _du_lieu() -> tuple[dict, dict]:
    hd = config.load_json("huong_dan_bai.json")["bai"]
    lib = config.load_json("thu_vien_bai_tap.json")["nhom"]
    ten = {}
    for n in lib.values():
        for b in n["bai"]:
            ten[_chuan(b["ten"])] = b["id"]
            ten[_chuan(b["ten"].split("(")[0])] = b["id"]
    return hd, ten


def _chuan(s: str) -> str:
    return re.sub(r"\s+", " ", str(s or "").lower()).strip()


def tim(eid: str | None = None, ten: str | None = None) -> dict | None:
    """{meo, loi, anh: [đường dẫn ảnh], gan_dung} theo id bài, hoặc theo tên (giáo án tự soạn)."""
    hd, T = _du_lieu()
    i = eid if eid in hd else T.get(_chuan(ten)) or T.get(_chuan(str(ten or "").split("(")[0]))
    if not i or i not in hd:
        return None
    v = hd[i]
    anh = [str(ANH / f"{v['anh']}_{j}.jpg") for j in (0, 1)] if v.get("anh") else []
    return {"id": i, "meo": v.get("meo", ""), "loi": v.get("loi", []), "anh": [a for a in anh if Path(a).exists()],
            "gan_dung": bool(v.get("gan_dung"))}
