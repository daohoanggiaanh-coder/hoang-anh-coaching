# Hoàng Anh Coaching v1.1 (2026-10-31) — lớp nối nhật ký buổi tập (bảng NhatKy) với bộ gợi ý tạ kiểu Atlas
"""Nhật ký buổi lưu 1 dạng chung cho cả HLV ghi (giao diện Atlas) và khách tự ghi:
    bai: [{id, bai (tên), ten, sets: [{kg, lan}], hiep: [{kg, lan}] (bản sao), ghi_chu}]
HLV ghi thêm: buoi_ma, tuan, tinh_trang, san_sang, cardio, cam_nhan, rpe, ghi_chu_hlv (KHÁCH KHÔNG THẤY), loi_nhan (khách thấy)."""
from __future__ import annotations

from datetime import date

from core import db, ga_atlas as ga, giao_an as gsimple, tu_van as tv

CAM_NHAN = ["Rất mệt", "Hơi mệt", "Bình thường", "Khoẻ", "Rất sung"]


def _d(v) -> date:
    try:
        return date.fromisoformat(str(v)[:10])
    except ValueError:
        return date.min


def sessions(ma: str) -> list[dict]:
    """Buổi đã ghi (cũ → mới), mỗi bài có id (map từ tên nếu khách tự ghi) + hiep."""
    ids = ga.ten_id()
    out = []
    for nk in gsimple.logs(ma):
        bai = []
        for b in nk.get("bai", []):
            ten = b.get("ten") or b.get("bai") or ""
            hs = b.get("hiep") if isinstance(b.get("hiep"), list) else b.get("sets") or []
            bai.append({**b, "id": b.get("id") or ids.get(ten, ten), "ten": ten, "hiep": hs})
        out.append({**nk, "ngay": _d(nk.get("ngay")), "bai": bai})
    return sorted(out, key=lambda s: (s["ngay"], str(s.get("_luc"))))


def tonnage(bai: list[dict]) -> float:
    return round(sum((tv.num(s.get("kg"), 0) or 0) * (tv.num(s.get("lan"), 0) or 0) for b in bai for s in b.get("hiep", [])), 1)


def best_1rm(b: dict) -> float | None:
    vals = [tv.one_rm(tv.num(s.get("kg")), tv.num(s.get("lan"))) for s in b.get("hiep", [])
            if (tv.num(s.get("kg"), 0) or 0) > 0 and (tv.num(s.get("lan"), 0) or 0) > 0]
    vals = [v for v in vals if v]
    return max(vals) if vals else None


def last_for(ma: str, eid: str, hist: list[dict] | None = None) -> dict | None:
    hist = sessions(ma) if hist is None else hist
    for s in reversed(hist):
        for b in s["bai"]:
            if b.get("id") == eid and b.get("hiep"):
                return {"ngay": s["ngay"], **b}
    return None


def _step(item: dict) -> float:
    return 1 if "Dumbbell" in item.get("ten", "") or "tạ đơn" in str(item.get("dung_cu", "")).lower() else 2.5


def target_kg(item: dict, lieu: str, last: dict | None) -> float | None:
    hs = [h for h in (last or {}).get("hiep", []) if tv.num(h.get("lan"))]
    kg = max((tv.num(h.get("kg"), 0) or 0 for h in hs), default=0)
    if not kg:
        return None
    top = ga.rep_top(lieu)
    return kg + _step(item) if top and min(int(tv.num(h.get("lan"), 0)) for h in hs) >= top else kg


def suggest(item: dict, lieu: str, last: dict | None) -> str:
    if not last:
        return "Buổi đầu: chọn mức tạ làm được đủ số lần mà vẫn chừa 2–3 lần"
    hs = [h for h in last.get("hiep", []) if tv.num(h.get("lan"))]
    if not hs:
        return ""
    kg = max(tv.num(h.get("kg"), 0) or 0 for h in hs)
    top = ga.rep_top(lieu)
    lan = [int(tv.num(h.get("lan"), 0)) for h in hs]
    if "giây" in lieu:
        return f"Lần trước {'/'.join(map(str, lan))} giây → giữ form, thêm 5–10 giây mỗi hiệp"
    prev = f"Lần trước {kg:g} kg × {'/'.join(map(str, lan))}"
    if not kg:
        return prev + " → thêm 1–2 lần mỗi hiệp"
    if top and min(lan) >= top:
        return f"{prev} → tăng lên {kg + _step(item):g} kg"
    return f"{prev} → giữ {kg:g} kg, cố thêm 1 lần"


def save(ma: str, s: dict, nguoi: str) -> str:
    bai = [{"id": b["id"], "bai": b["ten"], "ten": b["ten"], "sets": b["hiep"], "hiep": b["hiep"],
            **{k: b[k] for k in ("ghi_chu", "thay_cho", "ss", "giay") if b.get(k)}} for b in s["bai"] if b.get("hiep")]
    return gsimple.save_log(ma, {**s, "ngay": str(s["ngay"])[:10], "bai": bai, "nguoi_ghi": s.get("nguoi_ghi") or "hlv"}, nguoi)


def today() -> date:
    return db.now_vn().date()
