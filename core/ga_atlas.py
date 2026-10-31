# Hoàng Anh Coaching v1.1 (2026-10-31) — chuyển nguyên từ Atlas Academy v3.59: giáo án tuần tự động cho khách PT (theo mục tiêu, trình độ, số buổi, hạn chế,
# dạng lịch: toàn thân · chuỗi trước/sau · Push-Pull-Legs · tăng mông nữ · circuit · tăng chiều cao · sửa sai lệch)
"""
Luật xếp bài theo nguyên tắc của quản lý Atlas:
  - trong 1 tuần không lặp cùng một bài; xoay biến thể (squat 2 chân → 1 chân → sumo…)
  - kéo có cả kéo dọc và kéo ngang; tên bài ghi rõ thanh đòn / tạ đơn / máy
  - squat Smith/thanh đòn → bài hinge cùng buổi ưu tiên Dumbbell RDL; không 2 bài hinge nặng cùng buổi
  - không chồng nhiều bài đùi trước cùng buổi; Back Extension chỉ ở buổi có hinge / mông
  - bài bụng xoay, không lặp 2 buổi liền; khách nữ: tay trước tuỳ chọn (thay bằng bài mông)
  - 4–5 buổi/tuần chia chuỗi trước (đẩy: ngực, vai trước, tay sau, đùi trước) / chuỗi sau (kéo: lưng, vai sau,
    tay trước, đùi sau, mông)
  - thứ tự trong buổi: Compound → Multi → Isolate → Core
Lưu kiểu chỉ ghi thêm vào sheet LichTap: bản mới nhất theo ma_kh là giáo án đang dùng.
"""
from __future__ import annotations

from datetime import date, datetime


from core import db, tu_van as tv

LEVELS = ["Người mới", "Sơ trung cấp", "Trung cấp", "Nâng cao", "Chuyên nghiệp"]
GOALS = tv.GOALS
HAN_CHE = {  # vùng cần tránh → bài loại khỏi giáo án
    "Lưng dưới": {"bb_deadlift", "bb_row", "bb_rdl", "smith_sumo", "kb_swing", "ball_slam", "db_thruster",      # v3.64: + bài bật / ném
                  "cable_crunch", "lying_leg_raise"},            # HAC v1.4: lưng yếu → bỏ bài gập bụng có tải / nâng chân nằm
    "Gối": {"db_walking_lunge", "db_bulgarian", "leg_ext", "smith_sumo", "db_stepup", "curtsy_lunge", "box_jump", "jump_squat",
            "tuck_jump", "broad_jump", "skater_jump", "burpee", "jumping_jack", "high_knees", "squat_thrust"},
    "Vai": {"smith_ohp", "db_shoulder", "pull_up", "bb_bench", "bb_incline", "cable_overhead_ext", "overhead_carry", "battle_rope",
            "ball_slam"},
    "Cổ tay": {"push_up", "bb_row", "burpee", "mountain_climber", "squat_thrust", "kb_rack_carry"},
}
MIN_LV = {"bb_deadlift": 3, "pull_up": 3, "bb_row": 2, "bb_rdl": 2, "bb_bench": 1, "bb_incline": 1, "smith_ohp": 1,
          "db_bulgarian": 1, "db_walking_lunge": 1, "bb_hip_thrust": 1, "smith_inverted": 1, "smith_sumo": 1}
HEAVY_HINGE = {"bb_deadlift", "bb_rdl", "db_rdl"}
QUAD = {"smith_squat", "smith_sumo", "db_goblet", "leg_press", "db_bulgarian", "db_stepup",
        "db_walking_lunge", "db_reverse_lunge", "curtsy_lunge"}     # v3.58: đùi trước nặng (squat + 1 bài 1 chân / buổi; leg ext là cô lập)
TIME_CORE = {"weighted_plank", "side_plank", "bird_dog_core"}
# HAC v1.4: core giữ thẳng cột sống (chống duỗi / chống xoay / chống nghiêng) — ưu tiên khi lưng dưới yếu / đau
CORE_LUNG = ["dead_bug", "bird_dog_core", "side_plank", "pallof_press", "mcgill_curl_up", "weighted_plank"]

_T = {  # khuôn buổi: (nhóm, thứ tự ưu tiên bài)
    "FB1": ("Toàn thân 1 · trọng tâm đùi trước", [
        ("squat", ["smith_squat", "db_goblet", "leg_press"]), ("day_ngang", ["db_bench", "bb_bench", "chest_press", "push_up"]),
        ("hinge", ["db_rdl", "glute_trainer", "bb_rdl"]), ("keo_dung", ["lat_pulldown", "assisted_pullup", "pull_up"]),
        ("iso_vai_nguc", ["db_lateral", "cable_face_pull"]), ("core", ["weighted_plank", "dead_bug"])]),
    "FB2": ("Toàn thân 2 · trọng tâm mông", [
        ("mot_chan", ["db_reverse_lunge", "db_stepup", "db_bulgarian"]), ("keo_ngang", ["db_row", "cable_row", "smith_inverted", "bb_row"]),
        ("hinge", ["bb_hip_thrust", "glute_trainer", "db_rdl"]), ("day_dung", ["db_shoulder", "shoulder_press", "smith_ohp"]),
        ("iso_tay", ["cable_pushdown", "db_curl"]), ("core", ["lying_leg_raise", "cable_crunch"])]),
    "FB3": ("Toàn thân 3 · thân trên + khép háng", [
        ("squat", ["smith_sumo", "leg_press", "db_goblet"]), ("day_ngang", ["db_incline", "bb_incline", "chest_press", "push_up"]),
        ("keo_ngang", ["cable_row", "db_row", "smith_inverted"]), ("keo_dung", ["assisted_pullup", "lat_pulldown", "pull_up"]),
        ("iso_chan", ["leg_curl", "abduction"]), ("core", ["side_plank", "cable_crunch", "dead_bug"])]),
    "TR1": ("Chuỗi trước 1 · đẩy + đùi trước", [
        ("squat", ["smith_squat", "db_goblet", "leg_press"]), ("day_ngang", ["bb_bench", "db_bench", "chest_press", "push_up"]),
        ("day_dung", ["db_shoulder", "shoulder_press", "smith_ohp"]), ("iso_vai_nguc", ["db_lateral", "pec_deck"]),
        ("iso_tay", ["cable_pushdown", "cable_overhead_ext"]), ("core", ["weighted_plank", "dead_bug"])]),
    "SAU1": ("Chuỗi sau 1 · kéo + đùi sau", [
        ("hinge", ["db_rdl", "bb_rdl", "bb_deadlift"]), ("keo_dung", ["lat_pulldown", "assisted_pullup", "pull_up"]),
        ("keo_ngang", ["db_row", "cable_row", "bb_row"]), ("iso_chan", ["leg_curl", "cable_kickback", "abduction"]),
        ("iso_vai_nguc", ["rear_delt", "cable_face_pull"]), ("iso_tay", ["db_curl", "db_hammer"]),
        ("core", ["lying_leg_raise", "cable_crunch"])]),
    "TR2": ("Chuỗi trước 2 · đẩy + một chân", [
        ("mot_chan", ["db_bulgarian", "db_reverse_lunge", "db_stepup", "leg_press"]),
        ("day_ngang", ["db_incline", "bb_incline", "chest_press"]), ("day_dung", ["shoulder_press", "smith_ohp", "db_shoulder"]),
        ("iso_vai_nguc", ["cable_crossover", "pec_deck", "db_lateral"]), ("iso_tay", ["cable_overhead_ext", "cable_pushdown"]),
        ("core", ["cable_crunch", "side_plank"])]),
    "SAU2": ("Chuỗi sau 2 · kéo + mông", [
        ("hinge", ["bb_hip_thrust", "glute_trainer", "bb_rdl"]), ("keo_ngang", ["cable_row", "smith_inverted", "db_row"]),
        ("keo_dung", ["assisted_pullup", "pull_up", "lat_pulldown"]), ("hinge", ["back_ext"]),
        ("iso_chan", ["abduction", "cable_kickback", "leg_curl"]), ("iso_vai_nguc", ["cable_face_pull", "rear_delt"]),
        ("iso_tay", ["db_hammer", "db_curl"]), ("core", ["dead_bug", "side_plank", "weighted_plank"])]),
    "TL": ("Thể lực toàn thân · mạch bài", [
        ("mot_chan", ["db_walking_lunge", "db_stepup", "db_reverse_lunge"]), ("day_ngang", ["push_up", "chest_press"]),
        ("keo_ngang", ["smith_inverted", "cable_row"]), ("iso_chan", ["cable_kickback", "abduction"]),
        ("core", ["dead_bug", "side_plank"])]),
}
# ------------------------------------------------------------------ v3.55: các dạng lịch
_T.update({
    "FB4": ("Toàn thân 4 · sức mạnh tổng hợp", [
        ("hinge", ["db_rdl", "b_stance_rdl", "bb_deadlift"]), ("day_dung", ["shoulder_press", "db_shoulder", "smith_ohp"]),
        ("mot_chan", ["db_walking_lunge", "db_stepup", "curtsy_lunge"]), ("keo_ngang", ["smith_inverted", "db_row", "cable_row"]),
        ("iso_vai_nguc", ["rear_delt", "cable_face_pull"]), ("core", ["dead_bug", "side_plank"])]),
    # Push · Pull · Legs
    "PUSH1": ("Push 1 · đẩy: ngực, vai, tay sau", [
        ("day_ngang", ["bb_bench", "db_bench", "chest_press", "push_up"]), ("day_dung", ["db_shoulder", "shoulder_press", "smith_ohp"]),
        ("day_ngang", ["db_incline", "bb_incline", "chest_press"]), ("iso_vai_nguc", ["db_lateral", "cable_crossover"]),
        ("iso_tay", ["cable_pushdown", "cable_overhead_ext"]), ("core", ["weighted_plank", "cable_crunch"])]),
    "PULL1": ("Pull 1 · kéo: lưng, vai sau, tay trước", [
        ("keo_dung", ["lat_pulldown", "assisted_pullup", "pull_up"]), ("keo_ngang", ["db_row", "cable_row", "bb_row"]),
        ("keo_ngang", ["smith_inverted", "cable_row"]), ("iso_vai_nguc", ["cable_face_pull", "rear_delt"]),
        ("iso_tay", ["db_curl", "db_hammer"]), ("core", ["lying_leg_raise", "dead_bug"])]),
    "LEG1": ("Legs 1 · chân + mông", [
        ("squat", ["smith_squat", "db_goblet", "leg_press"]), ("hinge", ["db_rdl", "b_stance_rdl", "bb_rdl"]),
        ("mot_chan", ["db_reverse_lunge", "db_bulgarian", "db_stepup"]), ("iso_chan", ["leg_curl", "leg_ext"]),
        ("iso_chan", ["abduction", "cable_kickback"]), ("core", ["side_plank", "dead_bug"])]),
    "PUSH2": ("Push 2 · vai + ngực trên", [
        ("day_dung", ["smith_ohp", "shoulder_press", "db_shoulder"]), ("day_ngang", ["db_incline", "chest_press", "push_up"]),
        ("iso_vai_nguc", ["db_lateral", "pec_deck"]), ("iso_vai_nguc", ["cable_crossover", "pec_deck"]),
        ("iso_tay", ["cable_overhead_ext", "cable_pushdown"]), ("core", ["cable_crunch", "weighted_plank"])]),
    "PULL2": ("Pull 2 · lưng xô + đùi sau", [
        ("keo_dung", ["assisted_pullup", "pull_up", "lat_pulldown"]), ("hinge", ["bb_rdl", "db_rdl", "bb_deadlift"]),
        ("keo_ngang", ["cable_row", "db_row"]), ("iso_vai_nguc", ["rear_delt", "cable_face_pull"]),
        ("iso_tay", ["db_hammer", "db_curl"]), ("core", ["dead_bug", "lying_leg_raise"])]),
    "LEG2": ("Legs 2 · mông + một chân", [
        ("hinge", ["bb_hip_thrust", "glute_trainer", "sl_hip_thrust"]), ("squat", ["leg_press", "smith_sumo", "db_goblet"]),
        ("mot_chan", ["db_bulgarian", "curtsy_lunge", "db_walking_lunge"]), ("iso_chan", ["leg_curl", "cable_kickback"]),
        ("hinge", ["back_ext", "cable_pull_through"]), ("core", ["side_plank", "weighted_plank"])]),
    # Tăng mông (nữ): mông 2–3 buổi/tuần, thân trên giữ dáng
    "G1": ("Mông 1 · hip thrust nặng + hinge", [
        ("phuc_hoi", ["glute_bridge", "side_lying_clam"]), ("hinge", ["bb_hip_thrust", "glute_trainer"]),
        ("hinge", ["db_rdl", "b_stance_rdl"]), ("mot_chan", ["db_bulgarian", "db_reverse_lunge"]),
        ("iso_chan", ["abduction", "cable_kickback"]), ("core", ["dead_bug", "side_plank"])]),
    "G2": ("Mông 2 · một chân + kéo cáp", [
        ("phuc_hoi", ["side_lying_clam", "glute_bridge"]), ("mot_chan", ["db_stepup", "curtsy_lunge", "db_walking_lunge"]),
        ("hinge", ["sl_hip_thrust", "glute_trainer", "bb_hip_thrust"]), ("hinge", ["cable_pull_through", "back_ext"]),
        ("iso_chan", ["cable_kickback", "leg_curl"]), ("core", ["side_plank", "weighted_plank"])]),
    "G3": ("Mông 3 · bơm cơ (pump) + đùi sau", [
        ("phuc_hoi", ["glute_bridge", "side_lying_clam"]), ("squat", ["smith_sumo", "leg_press"]),
        ("hinge", ["glute_trainer", "bb_hip_thrust"]), ("iso_chan", ["frog_pump", "abduction"]),
        ("iso_chan", ["leg_curl", "cable_kickback"]), ("core", ["dead_bug", "lying_leg_raise"])]),
    "TREN": ("Thân trên · lưng, vai, tay — giữ dáng", [
        ("keo_dung", ["lat_pulldown", "assisted_pullup"]), ("day_ngang", ["db_bench", "chest_press", "push_up"]),
        ("keo_ngang", ["cable_row", "db_row"]), ("day_dung", ["db_shoulder", "shoulder_press"]),
        ("iso_vai_nguc", ["db_lateral", "rear_delt"]), ("iso_tay", ["cable_pushdown", "cable_overhead_ext"])]),
    "TREN2": ("Thân trên 2 · lưng + vai sau", [
        ("keo_ngang", ["smith_inverted", "db_row"]), ("keo_dung", ["assisted_pullup", "lat_pulldown"]),
        ("day_dung", ["shoulder_press", "db_shoulder"]), ("iso_vai_nguc", ["cable_face_pull", "rear_delt"]),
        ("iso_vai_nguc", ["db_lateral", "pec_deck"]), ("core", ["weighted_plank", "cable_crunch"])]),
    # Circuit training: làm liên tiếp các trạm theo giây, hết vòng mới nghỉ
    "C1": ("Circuit 1 · toàn thân sức mạnh – sức bền", [
        ("squat", ["db_goblet", "leg_press"]), ("day_ngang", ["push_up", "chest_press"]), ("the_luc", ["kb_swing", "ball_slam"]),
        ("keo_ngang", ["cable_row", "smith_inverted"]), ("the_luc", ["mountain_climber", "battle_rope"]),
        ("mot_chan", ["db_reverse_lunge", "db_stepup"]), ("the_luc", ["air_bike_sprint", "jump_rope"])]),
    "C2": ("Circuit 2 · đốt mỡ cường độ cao", [
        ("the_luc", ["db_thruster", "kb_swing"]), ("keo_dung", ["lat_pulldown", "assisted_pullup"]),
        ("the_luc", ["battle_rope", "ball_slam"]), ("mot_chan", ["db_walking_lunge", "curtsy_lunge"]),
        ("the_luc", ["burpee", "mountain_climber"]), ("day_dung", ["db_shoulder", "shoulder_press"]),
        ("the_luc", ["farmer_carry", "air_bike_sprint"])]),
    "C3": ("Circuit 3 · thể lực + core", [
        ("hinge", ["db_rdl", "glute_trainer"]), ("the_luc", ["ball_slam", "battle_rope"]), ("day_ngang", ["db_bench", "push_up"]),
        ("the_luc", ["suitcase_carry", "farmer_carry"]), ("bat_nhay", ["jump_rope", "skater_jump"]),
        ("core", ["dead_bug", "side_plank"]), ("the_luc", ["air_bike_sprint", "mountain_climber"])]),
    # Tăng chiều cao (tuổi đang lớn): bật nhảy, treo, kéo dọc, tư thế thẳng, core — tạ vừa phải
    "H1": ("Chiều cao 1 · bật nhảy + treo xà", [
        ("phuc_hoi", ["cat_cow", "open_book"]), ("bat_nhay", ["box_jump", "jump_squat"]), ("bat_nhay", ["jump_rope", "skater_jump"]),
        ("keo_dung", ["assisted_pullup", "lat_pulldown", "pull_up"]), ("phuc_hoi", ["dead_hang"]),
        ("squat", ["db_goblet", "leg_press"]), ("core", ["dead_bug", "side_plank"])]),
    "H2": ("Chiều cao 2 · sức bật một chân + tư thế", [
        ("phuc_hoi", ["wall_angel", "chin_tuck"]), ("bat_nhay", ["broad_jump", "tuck_jump"]),
        ("mot_chan", ["db_stepup", "db_reverse_lunge"]), ("keo_ngang", ["cable_row", "smith_inverted"]),
        ("phuc_hoi", ["hang_knee_raise", "dead_hang"]), ("day_dung", ["db_shoulder", "shoulder_press"]),
        ("core", ["side_plank", "dead_bug"])]),
    "H3": ("Chiều cao 3 · thể lực + giãn cơ", [
        ("phuc_hoi", ["open_book", "cat_cow"]), ("bat_nhay", ["skater_jump", "jump_rope"]), ("the_luc", ["air_bike_sprint", "battle_rope"]),
        ("keo_dung", ["lat_pulldown", "assisted_pullup"]), ("phuc_hoi", ["dead_hang"]), ("hinge", ["glute_trainer", "db_rdl"]),
        ("phuc_hoi", ["hip_flexor_stretch", "pec_stretch"])]),
    # Cải thiện sai lệch tư thế
    "S1": ("Sai lệch 1 · gù lưng, đầu đưa trước, vai tròn", [
        ("phuc_hoi", ["chin_tuck", "wall_angel"]), ("phuc_hoi", ["pec_stretch", "open_book"]),
        ("phuc_hoi", ["band_pull_apart"]), ("keo_ngang", ["cable_row", "db_row", "smith_inverted"]),
        ("iso_vai_nguc", ["cable_face_pull", "rear_delt"]), ("keo_dung", ["lat_pulldown", "assisted_pullup"]),
        ("core", ["dead_bug", "weighted_plank"])]),
    "S2": ("Sai lệch 2 · hông đổ trước, ưỡn lưng, mông yếu", [
        ("phuc_hoi", ["hip_flexor_stretch", "cat_cow"]), ("phuc_hoi", ["glute_bridge", "bird_dog"]),
        ("hinge", ["glute_trainer", "bb_hip_thrust", "db_rdl"]), ("mot_chan", ["db_reverse_lunge", "db_stepup"]),
        ("iso_chan", ["leg_curl", "abduction"]), ("core", ["dead_bug", "side_plank"])]),
    "S3": ("Sai lệch 3 · lệch vai, lệch hông (tập từng bên)", [
        ("phuc_hoi", ["side_lying_clam", "bird_dog"]), ("keo_ngang", ["db_row", "cable_row"]),
        ("mot_chan", ["db_stepup", "db_bulgarian", "db_reverse_lunge"]), ("the_luc", ["suitcase_carry", "farmer_carry"]),
        ("day_dung", ["db_shoulder", "shoulder_press"]), ("core", ["side_plank", "bird_dog"])]),
})
# ------------------------------------------------------------------ v3.58: phong cách Atlas — 8 bài / buổi
# Compound → Compound / Multi → Multi → Multi → Isolate → Isolate → Core / bụng → Strongman (mang vác cuối buổi).
# VD chuỗi trước: squat đầu buổi, leg extension giữa / cuối buổi. HLV dư bài thì xoá hoặc không nhập.
_CORE_A = ["cable_crunch", "lying_leg_raise", "weighted_plank"]
_CORE_B = ["dead_bug", "side_plank", "weighted_plank"]
_T.update({
    "TR1": ("Chuỗi trước 1 · đùi trước + ngực, vai", [
        ("squat", ["smith_squat", "db_goblet", "leg_press"]), ("day_ngang", ["bb_bench", "db_bench", "chest_press", "push_up"]),
        ("mot_chan", ["db_bulgarian", "db_reverse_lunge", "db_stepup"]), ("day_dung", ["db_shoulder", "shoulder_press", "smith_ohp"]),
        ("iso_chan", ["leg_ext"]), ("iso_vai_nguc", ["db_lateral", "cable_crossover"]),
        ("core", _CORE_A), ("strongman", ["front_plate_carry", "farmer_carry"])]),
    "SAU1": ("Chuỗi sau 1 · đùi sau, mông + lưng", [
        ("hinge", ["bb_rdl", "db_rdl", "bb_deadlift"]), ("keo_dung", ["assisted_pullup", "pull_up", "lat_pulldown"]),
        ("hinge", ["bb_hip_thrust", "glute_trainer", "sl_hip_thrust"]), ("keo_ngang", ["db_row", "cable_row", "bb_row"]),
        ("iso_chan", ["leg_curl"]), ("iso_vai_nguc", ["cable_face_pull", "rear_delt"]),
        ("core", _CORE_B), ("strongman", ["farmer_carry", "suitcase_carry"])]),
    "TR2": ("Chuỗi trước 2 · đùi trước một chân + ngực trên, tay sau", [
        ("squat", ["db_goblet", "smith_sumo", "leg_press"]), ("day_ngang", ["db_incline", "bb_incline", "push_up", "chest_press"]),
        ("mot_chan", ["db_stepup", "db_walking_lunge", "db_reverse_lunge"]), ("day_dung", ["shoulder_press", "smith_ohp", "db_shoulder"]),
        ("iso_chan", ["leg_ext"]), ("iso_tay", ["cable_pushdown", "cable_overhead_ext"]),
        ("core", ["lying_leg_raise", "cable_crunch", "weighted_plank"]), ("strongman", ["overhead_carry", "kb_rack_carry", "front_plate_carry"])]),
    "SAU2": ("Chuỗi sau 2 · mông + lưng xô, tay trước", [
        ("hinge", ["b_stance_rdl", "db_rdl", "bb_deadlift"]), ("keo_ngang", ["bb_row", "db_row", "cable_row"]),
        ("hinge", ["glute_trainer", "sl_hip_thrust", "cable_pull_through"]), ("keo_dung", ["lat_pulldown", "assisted_pullup"]),
        ("iso_chan", ["cable_kickback", "abduction", "leg_curl"]), ("iso_tay", ["db_curl", "db_hammer"]),
        ("core", ["side_plank", "dead_bug"]), ("strongman", ["suitcase_carry", "farmer_carry"])]),
    "FB1": ("Toàn thân 1 · trọng tâm đùi trước", [
        ("squat", ["smith_squat", "db_goblet", "leg_press"]), ("day_ngang", ["db_bench", "bb_bench", "chest_press", "push_up"]),
        ("keo_dung", ["lat_pulldown", "assisted_pullup", "pull_up"]), ("hinge", ["glute_trainer", "bb_hip_thrust"]),
        ("iso_chan", ["leg_ext"]), ("iso_vai_nguc", ["db_lateral", "cable_face_pull"]),
        ("core", _CORE_A), ("strongman", ["farmer_carry", "front_plate_carry"])]),
    "FB2": ("Toàn thân 2 · trọng tâm chuỗi sau", [
        ("hinge", ["db_rdl", "bb_rdl", "b_stance_rdl"]), ("keo_ngang", ["db_row", "bb_row", "cable_row"]),
        ("mot_chan", ["db_reverse_lunge", "db_stepup", "db_bulgarian"]), ("day_dung", ["shoulder_press", "db_shoulder", "smith_ohp"]),
        ("iso_chan", ["leg_curl"]), ("iso_tay", ["cable_pushdown", "db_curl"]),
        ("core", _CORE_B), ("strongman", ["suitcase_carry", "farmer_carry"])]),
    "FB3": ("Toàn thân 3 · thân trên + một chân", [
        ("squat", ["smith_sumo", "db_goblet", "leg_press"]), ("keo_dung", ["assisted_pullup", "pull_up", "lat_pulldown"]),
        ("day_ngang", ["db_incline", "bb_incline", "chest_press", "push_up"]), ("keo_ngang", ["cable_row", "smith_inverted", "db_row"]),
        ("iso_chan", ["abduction", "leg_ext"]), ("iso_vai_nguc", ["cable_face_pull", "rear_delt"]),
        ("core", ["lying_leg_raise", "cable_crunch"]), ("strongman", ["front_plate_carry", "kb_rack_carry"])]),
    "FB4": ("Toàn thân 4 · sức mạnh tổng hợp", [
        ("hinge", ["b_stance_rdl", "db_rdl", "bb_deadlift"]), ("day_dung", ["db_shoulder", "smith_ohp", "shoulder_press"]),
        ("mot_chan", ["db_walking_lunge", "db_stepup", "curtsy_lunge"]), ("keo_ngang", ["smith_inverted", "db_row", "cable_row"]),
        ("iso_vai_nguc", ["rear_delt", "db_lateral"]), ("iso_tay", ["db_hammer", "cable_overhead_ext"]),
        ("core", ["side_plank", "weighted_plank"]), ("strongman", ["overhead_carry", "farmer_carry"])]),
    "PUSH1": ("Push 1 · ngực, vai, tay sau", [
        ("day_ngang", ["bb_bench", "db_bench", "chest_press", "push_up"]), ("day_dung", ["db_shoulder", "smith_ohp", "shoulder_press"]),
        ("day_ngang", ["db_incline", "bb_incline", "push_up"]), ("day_ngang", ["chest_press", "push_up"]),
        ("iso_vai_nguc", ["db_lateral", "cable_crossover"]), ("iso_tay", ["cable_pushdown", "cable_overhead_ext"]),
        ("core", _CORE_A), ("strongman", ["front_plate_carry", "overhead_carry"])]),
    "PULL1": ("Pull 1 · lưng, vai sau, tay trước", [
        ("keo_dung", ["assisted_pullup", "pull_up", "lat_pulldown"]), ("keo_ngang", ["bb_row", "db_row", "cable_row"]),
        ("keo_dung", ["lat_pulldown", "assisted_pullup"]), ("keo_ngang", ["cable_row", "smith_inverted"]),
        ("iso_vai_nguc", ["cable_face_pull", "rear_delt"]), ("iso_tay", ["db_curl", "db_hammer"]),
        ("core", _CORE_B), ("strongman", ["farmer_carry", "suitcase_carry"])]),
    "LEG1": ("Legs 1 · đùi trước + mông", [
        ("squat", ["smith_squat", "db_goblet", "leg_press"]), ("hinge", ["db_rdl", "bb_rdl", "b_stance_rdl"]),
        ("mot_chan", ["db_bulgarian", "db_reverse_lunge", "db_stepup"]), ("hinge", ["bb_hip_thrust", "glute_trainer"]),
        ("iso_chan", ["leg_ext"]), ("iso_chan", ["leg_curl"]),
        ("core", ["lying_leg_raise", "dead_bug"]), ("strongman", ["suitcase_carry", "farmer_carry"])]),
    "PUSH2": ("Push 2 · vai + ngực trên", [
        ("day_dung", ["smith_ohp", "db_shoulder", "shoulder_press"]), ("day_ngang", ["db_bench", "bb_incline", "push_up"]),
        ("day_dung", ["shoulder_press", "db_shoulder"]), ("day_ngang", ["push_up", "chest_press"]),
        ("iso_vai_nguc", ["pec_deck", "cable_crossover", "db_lateral"]), ("iso_tay", ["cable_overhead_ext", "cable_pushdown"]),
        ("core", ["weighted_plank", "cable_crunch"]), ("strongman", ["kb_rack_carry", "front_plate_carry"])]),
    "PULL2": ("Pull 2 · lưng dày + đùi sau", [
        ("keo_ngang", ["db_row", "bb_row", "cable_row"]), ("hinge", ["bb_deadlift", "bb_rdl", "db_rdl"]),
        ("keo_dung", ["lat_pulldown", "assisted_pullup", "pull_up"]), ("keo_ngang", ["smith_inverted", "cable_row"]),
        ("iso_vai_nguc", ["rear_delt", "band_pull_apart"]), ("iso_tay", ["db_hammer", "db_curl"]),
        ("core", ["dead_bug", "side_plank"]), ("strongman", ["ball_carry", "farmer_carry"])]),
    "LEG2": ("Legs 2 · mông + một chân", [
        ("squat", ["smith_sumo", "db_goblet", "leg_press"]), ("hinge", ["glute_trainer", "bb_hip_thrust", "sl_hip_thrust"]),
        ("mot_chan", ["db_walking_lunge", "curtsy_lunge", "db_stepup"]), ("hinge", ["back_ext", "cable_pull_through"]),
        ("iso_chan", ["leg_ext", "leg_curl"]), ("iso_chan", ["abduction", "cable_kickback"]),
        ("core", ["side_plank", "weighted_plank"]), ("strongman", ["farmer_carry", "suitcase_carry"])]),
    # Upper · Lower (thân trên / thân dưới)
    "UP1": ("Thân trên 1 · đẩy ngang + kéo ngang", [
        ("day_ngang", ["bb_bench", "db_bench", "chest_press", "push_up"]), ("keo_ngang", ["db_row", "bb_row", "cable_row"]),
        ("day_dung", ["db_shoulder", "shoulder_press", "smith_ohp"]), ("keo_dung", ["lat_pulldown", "assisted_pullup"]),
        ("iso_vai_nguc", ["db_lateral", "cable_crossover"]), ("iso_tay", ["cable_pushdown", "db_curl"]),
        ("core", _CORE_A), ("strongman", ["front_plate_carry", "farmer_carry"])]),
    "LO1": ("Thân dưới 1 · đùi trước + mông", [
        ("squat", ["smith_squat", "db_goblet", "leg_press"]), ("hinge", ["db_rdl", "bb_rdl", "b_stance_rdl"]),
        ("mot_chan", ["db_bulgarian", "db_reverse_lunge", "db_stepup"]), ("hinge", ["bb_hip_thrust", "glute_trainer"]),
        ("iso_chan", ["leg_ext"]), ("iso_chan", ["leg_curl"]),
        ("core", _CORE_B), ("strongman", ["farmer_carry", "suitcase_carry"])]),
    "UP2": ("Thân trên 2 · kéo dọc + đẩy dọc", [
        ("keo_dung", ["assisted_pullup", "pull_up", "lat_pulldown"]), ("day_ngang", ["db_incline", "bb_incline", "push_up"]),
        ("keo_ngang", ["cable_row", "smith_inverted", "db_row"]), ("day_dung", ["shoulder_press", "smith_ohp", "db_shoulder"]),
        ("iso_vai_nguc", ["cable_face_pull", "rear_delt"]), ("iso_tay", ["cable_overhead_ext", "db_hammer"]),
        ("core", ["lying_leg_raise", "weighted_plank"]), ("strongman", ["overhead_carry", "kb_rack_carry"])]),
    "LO2": ("Thân dưới 2 · đùi sau + một chân", [
        ("hinge", ["b_stance_rdl", "bb_deadlift", "db_rdl"]), ("squat", ["db_goblet", "smith_sumo", "leg_press"]),
        ("mot_chan", ["db_stepup", "db_walking_lunge", "curtsy_lunge"]), ("hinge", ["glute_trainer", "sl_hip_thrust", "back_ext"]),
        ("iso_chan", ["leg_curl"]), ("iso_chan", ["abduction", "cable_kickback"]),
        ("core", ["side_plank", "dead_bug"]), ("strongman", ["suitcase_carry", "ball_carry"])]),
    # Tăng mông (nữ) — kích hoạt đầu buổi, 8 bài
    "G1": ("Mông 1 · hip thrust nặng + hinge", [
        ("phuc_hoi", ["glute_bridge", "side_lying_clam"]), ("hinge", ["bb_hip_thrust", "glute_trainer"]),
        ("hinge", ["db_rdl", "b_stance_rdl"]), ("mot_chan", ["db_bulgarian", "db_reverse_lunge"]),
        ("iso_chan", ["abduction"]), ("iso_chan", ["cable_kickback", "frog_pump"]),
        ("core", _CORE_B), ("strongman", ["suitcase_carry", "farmer_carry"])]),
    "G2": ("Mông 2 · một chân + kéo cáp", [
        ("phuc_hoi", ["side_lying_clam", "glute_bridge"]), ("mot_chan", ["db_stepup", "curtsy_lunge", "db_walking_lunge"]),
        ("hinge", ["sl_hip_thrust", "glute_trainer", "bb_hip_thrust"]), ("hinge", ["cable_pull_through", "back_ext"]),
        ("iso_chan", ["cable_kickback", "frog_pump"]), ("iso_chan", ["leg_curl"]),
        ("core", ["side_plank", "weighted_plank"]), ("strongman", ["farmer_carry", "kb_rack_carry"])]),
    "G3": ("Mông 3 · bơm cơ (pump) + đùi sau", [
        ("phuc_hoi", ["glute_bridge", "side_lying_clam"]), ("squat", ["smith_sumo", "leg_press"]),
        ("hinge", ["glute_trainer", "bb_hip_thrust"]), ("mot_chan", ["curtsy_lunge", "db_reverse_lunge"]),
        ("iso_chan", ["frog_pump", "abduction"]), ("iso_chan", ["leg_curl", "cable_kickback"]),
        ("core", ["dead_bug", "lying_leg_raise"]), ("strongman", ["front_plate_carry", "suitcase_carry"])]),
    "TREN": ("Thân trên 1 · lưng, vai, tay — giữ dáng", [
        ("keo_dung", ["lat_pulldown", "assisted_pullup"]), ("day_ngang", ["db_bench", "chest_press", "push_up"]),
        ("keo_ngang", ["cable_row", "db_row"]), ("day_dung", ["db_shoulder", "shoulder_press"]),
        ("iso_vai_nguc", ["db_lateral", "rear_delt"]), ("iso_tay", ["cable_pushdown", "cable_overhead_ext"]),
        ("core", _CORE_A), ("strongman", ["farmer_carry", "front_plate_carry"])]),
    "TREN2": ("Thân trên 2 · lưng + vai sau", [
        ("keo_ngang", ["db_row", "smith_inverted"]), ("keo_dung", ["assisted_pullup", "lat_pulldown"]),
        ("day_dung", ["shoulder_press", "db_shoulder"]), ("day_ngang", ["db_incline", "push_up"]),
        ("iso_vai_nguc", ["cable_face_pull", "rear_delt"]), ("iso_vai_nguc", ["db_lateral", "pec_deck"]),
        ("core", ["weighted_plank", "cable_crunch"]), ("strongman", ["kb_rack_carry", "suitcase_carry"])]),
})
# ------------------------------------------------------------------ v3.59: chuỗi trước theo tầng (Atlas: lầu 1 máy chân + ghế bụng,
# lầu 2 tạ tự do, Smith, cáp, máy ngực / vai / lưng). VD: Leg Press → Leg Extension superset Lying Leg Raise (lầu 1) →
# lên lầu 2: đẩy ngực, ép ngực, vai, tay sau.
_T.update({
    "TR1": ("Chuỗi trước 1 · đùi trước + ngực, vai, tay sau", [
        ("squat", ["leg_press", "smith_squat", "db_goblet"]), ("iso_chan", ["leg_ext"]),
        ("core", ["lying_leg_raise", "dead_bug"]), ("day_ngang", ["bb_bench", "db_bench", "chest_press", "push_up"]),
        ("iso_vai_nguc", ["pec_deck", "cable_crossover"]), ("day_dung", ["shoulder_press", "db_shoulder", "smith_ohp"]),
        ("iso_tay", ["cable_pushdown", "cable_overhead_ext"]), ("strongman", ["sled_push", "ball_slam"])]),
    "TR2": ("Chuỗi trước 2 · đùi trước một chân + ngực trên, vai", [
        ("squat", ["smith_squat", "db_goblet", "smith_sumo"]), ("mot_chan", ["db_bulgarian", "db_reverse_lunge", "db_stepup"]),
        ("day_ngang", ["db_incline", "bb_incline", "push_up"]), ("day_dung", ["db_shoulder", "smith_ohp", "shoulder_press"]),
        ("iso_vai_nguc", ["cable_crossover", "db_lateral", "pec_deck"]), ("iso_chan", ["leg_ext"]),
        ("core", ["weighted_plank", "dead_bug", "cable_crunch"]), ("strongman", ["ball_slam", "sled_push"])]),
    "SAU1": ("Chuỗi sau 1 · đùi sau, mông + lưng", [
        ("hinge", ["bb_rdl", "db_rdl", "bb_deadlift"]), ("keo_dung", ["assisted_pullup", "pull_up", "lat_pulldown"]),
        ("keo_ngang", ["db_row", "cable_row", "bb_row"]), ("iso_vai_nguc", ["cable_face_pull", "rear_delt"]),
        ("hinge", ["glute_trainer", "bb_hip_thrust"]), ("iso_chan", ["leg_curl"]),
        ("core", ["lying_leg_raise", "dead_bug"]), ("strongman", ["sled_pull", "farmer_carry"])]),
})
# bài kết buổi: strongman (sled, slam, mang vác — xoay vòng, ít bài cầm nắm) · khách giảm mỡ: HIIT
KET_BUOI = {"TR1": "sled_push", "SAU1": "sled_pull", "TR2": "ball_slam", "SAU2": "farmer_carry", "FB1": "sled_push",
            "FB2": "ball_slam", "FB3": "suitcase_carry", "FB4": "sled_pull", "PUSH1": "sled_push", "PULL1": "sled_pull",
            "LEG1": "farmer_carry", "PUSH2": "ball_slam", "PULL2": "ball_carry", "LEG2": "sled_push", "UP1": "sled_push",
            "LO1": "farmer_carry", "UP2": "sled_pull", "LO2": "ball_slam", "G1": "sled_push", "G2": "suitcase_carry",
            "G3": "sled_pull", "TREN": "ball_slam", "TREN2": "sled_pull"}
HIIT = ["burpee", "mountain_climber", "jumping_jack", "high_knees", "battle_rope", "squat_thrust"]
_KET_TRON = ["sled_push", "ball_slam", "sled_pull", "farmer_carry", "suitcase_carry", "ball_carry"]


def tang(eid: str) -> int | None:
    """Tầng của bài ở Atlas: 1 = máy chân, ghế bụng, air bike · 2 = tạ tự do, Smith, cáp, máy thân trên · None = tập đâu cũng được."""
    dc = str(ex(eid).get("dung_cu") or "")
    if dc.startswith("Tầng 1") or dc == "Air bike":
        return 1
    if dc.startswith("Tầng 2") or any(w in dc for w in ("Tạ đơn", "Thanh đòn", "Smith", "Cáp", "Ghế", "Xà")):
        return 2
    return None


def xep_tang(rows: list[dict]) -> list[dict]:
    """v3.59: xếp buổi theo tầng — tập hết tầng của bài chính đầu buổi rồi mới chuyển tầng (1 lần), trong mỗi tầng
    bài chính theo thứ tự mẫu → Isolate; bài bụng superset với bài cô lập cùng tầng (VD Leg Extension + Lying Leg Raise);
    strongman / HIIT cuối buổi."""
    if not rows:
        return rows
    rows = [{k: v for k, v in r.items() if k != "ss"} for r in rows]
    ket = [r for r in rows if r.get("loai") in ("S", "T")]
    con = [r for r in rows if r.get("loai") not in ("S", "T")]
    if not con:
        return ket
    dau = next((tang(r["id"]) for r in con if tang(r["id"])), None) or 2
    tangs = [dau] + [t for t in (1, 2) if t != dau]
    nha = 1 if 1 in {tang(r["id"]) for r in con} else dau            # bài tập đâu cũng được (thảm, tạ bánh…) → lầu 1
    khoi = {t: [r for r in con if (tang(r["id"]) or nha) == t] for t in tangs}
    out = []
    for t in tangs:
        b = sorted(khoi[t], key=lambda r: {"A": -1, "P": -1, "I": 1, "Core": 2}.get(r.get("loai", ""), 0))  # giữ thứ tự mẫu
        core = [r for r in b if r.get("loai") == "Core"]
        iso = [r for r in b if r.get("loai") == "I"]
        if core and iso:                                   # bụng superset với bài cô lập đầu tiên cùng tầng
            c0, i0 = core[0], iso[0]
            b = [r for r in b if r is not c0]
            b.insert(b.index(i0) + 1, c0)
            ss = "ABCDEFGH"[sum(1 for r in out if r.get("ss")) // 2]
            i0["ss"] = c0["ss"] = ss
        out += b
    return out + ket


KIEU_LICH = {
    "auto": "Tự động theo số buổi",
    "toan_than": "Toàn thân (Full body)",
    "truoc_sau": "Chuỗi trước · Chuỗi sau",
    "ppl": "Push · Pull · Legs",
    "tren_duoi": "Thân trên · Thân dưới (Upper · Lower)",
    "mong_nu": "Tăng mông (nữ)",
    "circuit": "Circuit training (mạch bài)",
    "chieu_cao": "Tăng chiều cao (tuổi đang lớn)",
    "sai_lech": "Cải thiện sai lệch tư thế",
}
KIEU_MO_TA = {
    "toan_than": "Mỗi buổi tập cả thân trên + thân dưới — hợp người mới, khách bận (2–3 buổi/tuần).",
    "truoc_sau": "Chuỗi trước = đẩy + đùi trước; chuỗi sau = kéo + đùi sau, mông. Hợp 4–5 buổi/tuần.",
    "tren_duoi": "Thân trên / thân dưới xen kẽ, mỗi kiểu 2 biến thể: Trên 1 · Dưới 1 · Trên 2 · Dưới 2.",
    "ppl": "Push (ngực, vai, tay sau) · Pull (lưng, vai sau, tay trước) · Legs (chân, mông). Cần tối thiểu 3 buổi/tuần.",
    "mong_nu": "Mông 2–3 buổi/tuần (hip thrust, hinge, một chân, dạng háng) + thân trên giữ dáng. Đầu buổi kích hoạt mông.",
    "circuit": "Làm liên tiếp các trạm 40 giây làm / 20 giây nghỉ, hết vòng nghỉ 2 phút, 3–4 vòng. Đốt mỡ, tăng thể lực.",
    "chieu_cao": "Dành cho tuổi đang lớn (sụn tăng trưởng chưa đóng): bật nhảy, treo xà, kéo dọc, tư thế thẳng, tạ vừa phải. "
                 "Người đã trưởng thành không cao thêm — mục tiêu là đứng thẳng, cột sống khoẻ. Ngủ đủ + ăn đủ đạm, canxi.",
    "sai_lech": "Đầu buổi giãn cơ bị co ngắn + kích hoạt cơ yếu, sau đó tập sức mạnh cân bằng 2 bên. "
                "Đau nhiều, tê lan, vẹo cột sống nặng → gửi bác sĩ / vật lý trị liệu trước.",
}
KIEU_SPLIT = {  # v3.58: chu kỳ buổi — tập theo thứ tự, hết tuần chưa đủ chu kỳ thì buổi kế tiếp nối sang đầu tuần sau
    "toan_than": {2: ["FB1", "FB2"], 3: ["FB1", "FB2", "FB3"], 4: ["FB1", "FB2", "FB3", "FB4"], 5: ["FB1", "FB2", "FB3", "FB4"]},
    "truoc_sau": {n: ["TR1", "SAU1", "TR2", "SAU2"] for n in (2, 3, 4, 5)},
    "tren_duoi": {n: ["UP1", "LO1", "UP2", "LO2"] for n in (2, 3, 4, 5)},
    "ppl": {n: ["PUSH1", "PULL1", "LEG1", "PUSH2", "PULL2", "LEG2"] for n in (2, 3, 4, 5)},
    "mong_nu": {2: ["G1", "G2"], 3: ["G1", "TREN", "G2", "TREN2"], 4: ["G1", "TREN", "G2", "TREN2"],
                5: ["G1", "TREN", "G2", "TREN2", "G3"]},
    "circuit": {2: ["C1", "C2"], 3: ["C1", "C2", "C3"], 4: ["C1", "FB1", "C2", "C3"], 5: ["C1", "FB1", "C2", "FB2", "C3"]},
    "chieu_cao": {2: ["H1", "H2"], 3: ["H1", "H2", "H3"], 4: ["H1", "H2", "H3", "FB1"], 5: ["H1", "H2", "H3", "FB1", "H1"]},
    "sai_lech": {2: ["S1", "S2"], 3: ["S1", "S2", "S3"], 4: ["S1", "S2", "S3", "FB1"], 5: ["S1", "S2", "S3", "FB1", "FB2"]},
}
CHU_KY = {"truoc_sau", "tren_duoi", "ppl", "mong_nu"}          # dạng lịch chạy theo chu kỳ, không theo số buổi / tuần
TAM_BAI = {"auto", "toan_than", "truoc_sau", "tren_duoi", "ppl", "mong_nu"}   # dạng lịch 8 bài / buổi (phong cách Atlas)
KIEU_MAX_BAI = {"circuit": 7, "chieu_cao": 7, "sai_lech": 7, "mong_nu": 8}     # số trạm / bài tối đa của dạng lịch đặc biệt
LAP_DUOC = {"phuc_hoi", "bat_nhay", "the_luc", "strongman"}
GIU_THU_TU = {"mong_nu", "circuit", "chieu_cao", "sai_lech"}     # buổi mẫu đã xếp thứ tự chủ đích → không xếp lại theo loại      # nhóm được lặp trong tuần (kích hoạt, bật nhảy, trạm thể lực)
SPLIT = {2: ["FB1", "FB2"], 3: ["FB1", "FB2", "FB3"], 4: ["TR1", "SAU1", "TR2", "SAU2"],
         5: ["TR1", "SAU1", "TR2", "SAU2"]}
CARDIO = {
    "giam_mo": ["Kết buổi: đi bộ dốc 15 phút, vẫn nói chuyện được (RPE 5–6)",
                "Kết buổi: đi bộ dốc 20 phút + 5 phút air bike nhẹ",
                "Kết buổi: air bike 8 × (20 giây nhanh / 40 giây chậm) + đi bộ dốc 10 phút"],
    "tang_co": ["Đi bộ nhẹ 8–10 phút để hồi phục"] * 3,
    "recomp": ["Kết buổi: đi bộ dốc 12–15 phút", "Kết buổi: đi bộ dốc 15 phút",
               "Kết buổi: air bike 6 × (20 giây nhanh / 40 giây chậm)"],
    "suc_khoe": ["Đi bộ 15–20 phút, nhịp tim vừa phải", "Đi bộ dốc 20 phút", "Đi bộ dốc 20 phút + giãn cơ 5 phút"],
    "suc_manh": ["Đi bộ nhẹ 5–10 phút"] * 3,
}
RX = {  # (hiệp × lần, RIR, nghỉ) theo giai đoạn 1 · 2 · 3 cho bài Compound / Multi
    "giam_mo": [("3×12–15", "chừa 3 lần", "45–60 giây"), ("4×10–12", "chừa 2 lần", "45–60 giây"),
                ("4×8–12", "chừa 1–2 lần", "60 giây")],
    "tang_co": [("3×10–12", "chừa 3 lần", "90 giây"), ("4×8–10", "chừa 2 lần", "90–120 giây"),
                ("4×6–10", "chừa 1 lần", "2 phút")],
    "recomp": [("3×10–12", "chừa 3 lần", "60 giây"), ("4×8–12", "chừa 2 lần", "60–90 giây"),
               ("4×6–10", "chừa 1–2 lần", "90 giây")],
    "suc_khoe": [("3×12–15", "chừa 3–4 lần", "60 giây"), ("3×10–12", "chừa 3 lần", "60 giây"),
                 ("3×10–12", "chừa 2 lần", "60 giây")],
    "suc_manh": [("4×6–8", "chừa 3 lần", "2 phút"), ("5×4–6", "chừa 2 lần", "2–3 phút"),
                 ("5×3–5", "chừa 1–2 lần", "3 phút")],
}
PHASES = ["Giai đoạn 1 · Nền tảng", "Giai đoạn 2 · Phát triển", "Giai đoạn 3 · Bứt phá"]


# ------------------------------------------------------------------ tiện ích
def guess_goal(text: str) -> str:
    t = str(text or "").lower()
    if t in GOALS:
        return t
    for k, ten in GOALS.items():
        if t and t == ten.lower():
            return k
    for kw, k in (("săn", "recomp"), ("tăng cơ", "tang_co"), ("tăng cân", "tang_co"), ("sức mạnh", "suc_manh"),
                  ("đau", "suc_khoe"), ("sức khoẻ", "suc_khoe"), ("sức khỏe", "suc_khoe"), ("giảm", "giam_mo")):
        if kw in t:
            return k
    return "giam_mo"


def guess_limits(text: str) -> list[str]:
    t = str(text or "").lower()
    out = []
    for k, kws in (("Lưng dưới", ("lưng",)), ("Gối", ("gối",)), ("Vai", ("vai",)), ("Cổ tay", ("cổ tay",))):
        if any(w in t for w in kws):
            out.append(k)
    return out


def ex(eid: str) -> dict:
    return tv.exercise(eid) or {"id": eid, "ten": eid, "loai": "M", "dung_cu": "", "nhom": "", "nhom_ten": ""}


def allowed(eid: str, level: int, limits: list[str]) -> bool:
    if MIN_LV.get(eid, 0) > level:
        return False
    return not any(eid in HAN_CHE.get(x, set()) for x in limits)


def phase_of(week: int) -> int:
    return 0 if week <= 4 else 1 if week <= 8 else 2


def week_no(start, today: date | None = None) -> int:
    today = today or date.today()
    try:
        s = start if isinstance(start, date) else datetime.strptime(str(start)[:10], "%Y-%m-%d").date()
    except ValueError:
        return 1
    return max(1, (today - s).days // 7 + 1)


# ------------------------------------------------------------------ sinh giáo án
def generate(goal: str, level: int, per_week: int, gioi: str = "Nam", limits: list[str] | None = None,
             kieu: str = "auto") -> list[dict]:
    """Trả danh sách buổi [{ma, khuon, ten, bai:[{id, ten, nhom, loai, dung_cu}]}]. kieu = dạng lịch (KIEU_LICH)."""
    limits = limits or []
    lib = tv.library()["nhom"]
    used: set[str] = set()
    per_week = min(max(int(per_week), 2), 5)
    max_bai = 8 if kieu in TAM_BAI else 5 if level == 0 else 6 if level == 1 else 7      # v3.58: phong cách Atlas 8 bài
    if kieu in KIEU_MAX_BAI:
        max_bai = max(max_bai, KIEU_MAX_BAI[kieu] - (1 if level == 0 and kieu == "mong_nu" else 0))
    seq = KIEU_SPLIT.get(kieu, {}).get(per_week) or SPLIT[per_week]
    out = []
    for i, key in enumerate(seq):
        ten, slots = _T[key]
        if gioi == "Nữ" and kieu in ("auto", "toan_than", "truoc_sau"):     # nữ: tay trước tuỳ chọn → thay bằng bài mông
            slots = [("iso_chan", ["abduction", "cable_kickback"]) if (g == "iso_tay" and p[0] in ("db_curl", "db_hammer"))
                     else (g, p) for g, p in slots]
        if any(g == "strongman" for g, _ in slots):                         # v3.59: bài kết buổi
            if goal == "giam_mo":
                ket = ("the_luc", HIIT[i % len(HIIT):] + HIIT[:i % len(HIIT)])
            else:
                k0 = KET_BUOI.get(key, _KET_TRON[i % len(_KET_TRON)])
                ket = ("strongman", [k0] + [x for x in _KET_TRON if x != k0])
            slots = [ket if g == "strongman" else (g, pr) for g, pr in slots]
        if goal == "suc_manh" and key in ("FB1", "FB3", "TR1", "TR2"):
            slots = [s for s in slots if s[0] != "iso_tay"] if level < 2 else slots
        if "Lưng dưới" in limits:                                           # HAC v1.4: core an toàn cho lưng, xoay vòng theo buổi
            slots = [(g, CORE_LUNG[i % 3:] + CORE_LUNG[:i % 3]) if g == "core" else (g, pr) for g, pr in slots]
        picked: list[str] = []
        for si, (g, prefs) in enumerate(slots):
            cands = prefs + [b["id"] for b in lib.get(g, {}).get("bai", []) if b["id"] not in prefs]
            cands = [c for c in cands if allowed(c, level, limits)]
            if g.startswith("iso") and CO_DICH.get(prefs[0] if prefs else ""):      # v3.58: cô lập đúng cơ đích (VD leg extension)
                cands = [c for c in cands if CO_DICH.get(c) == CO_DICH[prefs[0]]] or cands

            def ok(c):
                if c in picked:
                    return False
                if c in HEAVY_HINGE and any(p in HEAVY_HINGE for p in picked):
                    return False
                if c in QUAD and sum(p in QUAD for p in picked) >= 2:
                    return False
                if c == "back_ext" and not any(ex(p)["nhom"] == "hinge" for p in picked):
                    return False
                return True
            if g in LAP_DUOC:                  # kích hoạt / treo / bật nhảy / trạm thể lực: theo đúng bài mẫu, lặp được trong tuần
                choice = next((c for c in prefs if c in cands and ok(c)), None) or next((c for c in cands if ok(c)), None)
            else:
                choice = next((c for c in cands if ok(c) and c not in used), None)
            if not choice and (si < 2 or g in LAP_DUOC or g.startswith("iso") or g == "core" or kieu in TAM_BAI):
                truoc = {x["id"] for x in out[-1]["bai"]} if out else set()           # cho lặp khi hết bài khác,
                choice = next((c for c in cands if ok(c) and c not in truoc), None) \
                    or next((c for c in cands if ok(c)), None)                       # tránh lặp buổi liền trước
            if choice:
                picked.append(choice)
                used.add(choice)
        # giới hạn số bài theo trình độ: bỏ bớt cô lập trước
        drop_order = ["iso_tay", "iso_vai_nguc", "iso_chan", "phuc_hoi"]
        while len(picked) > max_bai:
            for dg in drop_order + ["hinge"]:
                cand = [p for p in picked if ex(p)["nhom"] == dg and (dg != "hinge" or p == "back_ext")]
                if cand:
                    picked.remove(cand[-1])
                    break
            else:
                bo = next((p for p in reversed(picked[:-1]) if ex(p)["nhom"] != "core"), picked[-2])
                picked.remove(bo)
        if not any(ex(p)["nhom"] == "core" for p in picked):            # HAC v1.4: buổi nào cũng có ≥ 1 bài bụng / core
            pool = (CORE_LUNG if "Lưng dưới" in limits else []) + [b["id"] for b in lib["core"]["bai"]]
            truoc = {x["id"] for x in out[-1]["bai"]} if out else set()
            cc = [c for c in dict.fromkeys(pool) if allowed(c, level, limits)]
            cc = next((c for c in cc if c not in used and c not in truoc), None) or next((c for c in cc if c not in truoc), None) \
                or (cc[0] if cc else None)
            if cc:
                if len(picked) >= max_bai:
                    bo = next((p for p in reversed(picked) if ex(p)["nhom"].startswith("iso")), None)
                    picked.remove(bo) if bo else None
                picked.append(cc)
                used.add(cc)
        rows = [{k: ex(p)[k] for k in ("id", "ten", "nhom", "loai", "dung_cu")} for p in picked]
        giu = kieu in GIU_THU_TU and key[0] in "GHSC" and key not in ("FB1", "FB2", "FB3", "FB4")
        if not giu and kieu in TAM_BAI:
            rows = xep_tang(rows)                                            # v3.59: theo tầng, bụng superset cô lập
        elif not giu:
            rows = sorted(rows, key=lambda r: tv.order_rank(r["loai"]))
        mach = kieu == "circuit" and key.startswith("C")
        if giu and not mach:
            out.append({"ma": "ABCDEFGH"[i], "khuon": key, "ten": ten, "bai": rows, "giu_thu_tu": True})
            continue
        if mach:                                               # mạch bài: giữ thứ tự trạm xen kẽ, không xếp theo loại
            rows = [{**{k: ex(p)[k] for k in ("id", "ten", "nhom", "loai", "dung_cu")}, "circuit": True} for p in picked]
        out.append({"ma": "ABCDEFGH"[i], "khuon": key, "ten": ten, "bai": rows, **({"circuit": True} if mach else {})})
    return out


# ------------------------------------------------------------------ v3.56: đổi bài tương đương (không có máy / máy bận)
LIEN_QUAN = {  # nhóm gần nhất khi trong nhóm hết bài thay
    "squat": ["mot_chan"], "mot_chan": ["squat"], "hinge": ["iso_chan", "mot_chan"], "keo_dung": ["keo_ngang"],
    "keo_ngang": ["keo_dung"], "day_ngang": ["day_dung"], "day_dung": ["day_ngang"], "iso_chan": ["hinge", "mot_chan"],
    "iso_vai_nguc": ["day_dung", "keo_ngang"], "iso_tay": ["iso_vai_nguc"], "core": ["phuc_hoi"], "phuc_hoi": ["core"],
    "bat_nhay": ["the_luc", "mot_chan"], "the_luc": ["bat_nhay", "core"], "strongman": ["the_luc", "core"],
}
_BAC = {"C": 2, "M": 1, "T": 1, "P": 1, "I": 0, "Core": 0, "A": 0, "S": 1}
CO_DICH = {  # cơ đích của bài cô lập (cùng nhóm "iso_*" nhưng khác cơ) → đổi bài đúng cơ
    "leg_ext": "dui_truoc", "leg_curl": "dui_sau", "abduction": "mong", "cable_kickback": "mong", "frog_pump": "mong", "glute_bridge": "mong",
    "db_lateral": "vai_giua", "rear_delt": "vai_sau", "cable_face_pull": "vai_sau", "band_pull_apart": "vai_sau",
    "pec_deck": "nguc", "cable_crossover": "nguc", "db_curl": "tay_truoc", "db_hammer": "tay_truoc",
    "cable_pushdown": "tay_sau", "cable_overhead_ext": "tay_sau",
}
CO_GAN = {"dui_truoc": ["squat", "mot_chan"], "dui_sau": ["hinge"], "mong": ["hinge", "mot_chan"], "vai_giua": ["day_dung"],
          "vai_sau": ["keo_ngang"], "nguc": ["day_ngang"], "tay_truoc": ["keo_dung", "keo_ngang"], "tay_sau": ["day_ngang", "day_dung"]}


def do_kho(eid: str) -> int:
    """Độ khó tương đối của bài: trình độ tối thiểu + mức đa khớp (compound > multi > isolate)."""
    return MIN_LV.get(eid, 0) + _BAC.get(ex(eid).get("loai"), 1)


def ung_vien(eid: str, tranh: set[str] | None = None, level: int = 4, limits: list[str] | None = None,
             tranh_dc: set[str] | None = None, n: int = 8) -> list[str]:
    """v3.57: các bài thay cho `eid`, tốt nhất trước — cùng nhóm cơ (bài cô lập: cùng cơ đích), cùng dạng
    (compound / multi / isolate), độ khó gần nhất, ưu tiên khác dụng cụ; hết thì nhóm cơ gần.
    tranh = id bài không dùng được / đã có trong buổi; tranh_dc = loại dụng cụ đang không có (VD "Smith", "Cáp")."""
    tranh, tranh_dc, limits = set(tranh or ()) | {eid}, set(tranh_dc or ()), list(limits or [])
    goc = ex(eid)
    lib = tv.library()["nhom"]
    co = CO_DICH.get(eid)

    def ok(b):
        return b["id"] not in tranh and b.get("dung_cu") not in tranh_dc and allowed(b["id"], level, limits)
    tang: list[list[str]] = []
    if co:                                             # bài cô lập: cùng cơ đích trước, rồi nhóm đa khớp dùng cơ đó
        tang.append([b["id"] for nh in lib.values() for b in nh["bai"] if CO_DICH.get(b["id"]) == co and ok(b)])
        tang += [[b["id"] for b in lib.get(nh, {}).get("bai", []) if ok(b)] for nh in CO_GAN.get(co, [])]
    else:
        tang += [[b["id"] for b in lib.get(nh, {}).get("bai", []) if ok(b) and not CO_DICH.get(b["id"])]
                 for nh in [goc["nhom"]] + LIEN_QUAN.get(goc["nhom"], [])]
    out: list[str] = []
    for cands in tang:
        for c in sorted(cands, key=lambda c: (ex(c)["loai"] != goc["loai"], abs(do_kho(c) - do_kho(eid)),
                                              ex(c)["dung_cu"] == goc["dung_cu"], cands.index(c))):
            if c not in out:
                out.append(c)
    return out[:n]


def thay_the(eid: str, tranh: set[str] | None = None, level: int = 4, limits: list[str] | None = None,
             tranh_dc: set[str] | None = None) -> str | None:
    """Bài thay tốt nhất cho `eid` (xem ung_vien)."""
    c = ung_vien(eid, tranh, level, limits, tranh_dc, 1)
    return c[0] if c else None


DANG = {"C": "Compound", "M": "Multi", "I": "Isolate", "Core": "Core / bụng", "A": "Kích hoạt", "P": "Bật nhảy", "T": "Thể lực",
        "S": "Strongman"}


def dang(eid_or_loai: str) -> tuple[str, str]:
    """(nhãn dạng bài, màu) — Compound / Multi / Isolate / Core / Kích hoạt / Bật nhảy / Thể lực."""
    lo = eid_or_loai if eid_or_loai in DANG else ex(eid_or_loai).get("loai", "")
    return DANG.get(lo, lo or "—"), tv.library()["loai"].get(lo, {}).get("mau", "#8b8577")


def rpe_tu_rir(rir: str) -> str:
    """'chừa 2 lần' → 'RPE 8'; 'chừa 1–2 lần' → 'RPE 8–9'; không phải số lần chừa → ''."""
    import re
    m = re.search(r"chừa\s*(\d+)(?:\s*[–-]\s*(\d+))?", str(rir or ""))
    if not m:
        return ""
    a, b = int(m.group(1)), int(m.group(2) or m.group(1))
    lo, hi = 10 - b, 10 - a
    return f"RPE {lo}" if lo == hi else f"RPE {lo}–{hi}"


def doi_bai(plan: list[dict], bo: set[str], level: int = 4, limits: list[str] | None = None,
            tranh_dc: set[str] | None = None) -> tuple[list[dict], list[tuple[str, str]]]:
    """Đổi trong cả giáo án các bài thuộc `bo` (hoặc dùng dụng cụ trong tranh_dc) → bài tương đương; giữ liều / superset
    HLV đã chỉnh. Trả (giáo án mới, [(tên cũ, tên mới)])."""
    out, doi = [], []
    tranh_dc = set(tranh_dc or ())
    for bu in plan:
        ids = {x["id"] for x in bu["bai"]}
        rows = []
        for it in bu["bai"]:
            if it["id"] in bo or ex(it["id"]).get("dung_cu") in tranh_dc:
                moi = thay_the(it["id"], set(bo) | ids, level, limits, tranh_dc)
                if moi:
                    e = ex(moi)
                    rows.append({**it, **{k: e[k] for k in ("id", "ten", "nhom", "loai", "dung_cu")}, "thay_cho": it["ten"]})
                    ids.add(moi)
                    doi.append((it["ten"], e["ten"]))
                    continue
            rows.append(it)
        out.append({**bu, "bai": rows})
    return out, doi


def rx(item: dict, goal: str, week: int, level: int = 1) -> dict:
    """v3.56: liều tự tính theo mục tiêu + giai đoạn, rồi ghi đè phần HLV chỉnh (item rx = hiệp × lần, nghi = thời gian nghỉ)."""
    base = _rx(item, goal, week, level)
    if item.get("rx"):
        base = {**base, "lieu": str(item["rx"]), "rir": base["rir"] if str(item["rx"]) == base["lieu"] else ""}
    if item.get("nghi"):
        base = {**base, "nghi": str(item["nghi"])}
    if item.get("ss"):
        base = {**base, "ss": str(item["ss"]).strip().upper()}
    base["rpe"] = str(item["rpe"]) if item.get("rpe") else rpe_tu_rir(base.get("rir", ""))   # v3.57
    return base


def _rx(item: dict, goal: str, week: int, level: int = 1) -> dict:
    """Liều tập của 1 bài theo mục tiêu + giai đoạn (PT có thể ghi đè bằng item['rx'])."""
    ph = phase_of(week)
    if item.get("circuit"):                       # v3.55: trạm trong mạch bài
        return {"lieu": f"{3 if ph == 0 else 4} vòng × {30 if ph == 0 else 40} giây", "rir": "làm liên tục giữa các trạm",
                "nghi": "20 giây giữa trạm · 2 phút giữa vòng"}
    if item.get("loai") == "A":
        hold = item.get("id") in {"dead_hang", "pec_stretch", "hip_flexor_stretch"}
        return {"lieu": "2–3×20–40 giây" if hold else "2×10–12 chậm", "rir": "kiểm soát, không đau", "nghi": "20–30 giây"}
    if item.get("loai") == "P":
        lieu = "3×30–60 giây" if item.get("id") == "jump_rope" else ("3×5" if ph == 0 else "4×5")
        return {"lieu": lieu, "rir": "bật hết sức, tiếp đất êm", "nghi": "60–90 giây"}
    if item.get("loai") == "T":
        carry = item.get("id") in {"farmer_carry", "suitcase_carry"}
        return {"lieu": "3×30–40 m" if carry else "4×30 giây", "rir": "nhanh nhưng đúng kỹ thuật", "nghi": "30–60 giây"}
    if item.get("loai") == "S":                    # v3.58: strongman cuối buổi
        if item.get("id") == "ball_slam":
            return {"lieu": "3×10–12" if ph < 2 else "4×10–12", "rir": "ném hết sức, siết bụng", "nghi": "60 giây"}
        if str(item.get("id", "")).startswith("sled"):
            return {"lieu": "4×20 m" if ph < 2 else "5×20 m", "rir": "nặng, bước ngắn đều, lưng thẳng", "nghi": "60–90 giây"}
        return {"lieu": "3×30–40 m" if ph < 2 else "4×30–40 m", "rir": "nặng nhưng giữ thân thẳng, bước đều",
                "nghi": "60–90 giây"}
    if item.get("loai") == "Core":
        lieu = "3×30–45 giây" if item.get("id") in TIME_CORE else "3×12–15"
        return {"lieu": lieu, "rir": "", "nghi": "30–45 giây"}
    if item.get("loai") == "I":
        return {"lieu": "2–3×12–15" if level == 0 or ph == 0 else "3×12–15", "rir": "chừa 1–2 lần", "nghi": "45 giây"}
    lieu, rir, nghi = RX.get(goal, RX["giam_mo"])[ph]
    if goal == "suc_manh" and item.get("loai") == "M":
        lieu, nghi = "3×8–10", "90 giây"
    if level == 0 and ph == 0:
        lieu = "2–" + lieu
    return {"lieu": lieu, "rir": rir, "nghi": nghi}


def rep_top(lieu: str) -> int | None:
    """'4×8–12' → 12; '3×30–45 giây' → None (bài tính giây)."""
    if "giây" in lieu:
        return None
    try:
        return int(lieu.split("×")[1].split("–")[-1].split("/")[0].strip())
    except (IndexError, ValueError):
        return None


def cardio(goal: str, week: int) -> str:
    return CARDIO.get(goal, CARDIO["giam_mo"])[phase_of(week)]


def check(plan: list[dict], kieu: str = "auto") -> list[str]:
    """Soát lại giáo án sau khi PT sửa tay: báo vi phạm nguyên tắc (dạng lịch đặc biệt bỏ qua luật cân bằng đẩy / kéo)."""
    warn = []
    seen: dict[str, str] = {}
    for b in plan:
        ids = [x["id"] for x in b["bai"]]
        for i in ids:
            if ex(i)["nhom"] in LAP_DUOC or ex(i).get("loai") in ("I", "Core", "S"):
                continue
            if i in seen and seen[i] != b["ma"] and kieu != "ppl":       # PPL 6 buổi: lặp bài cách 3 buổi là bình thường
                warn.append(f"{ex(i)['ten']} lặp ở buổi {seen[i]} và {b['ma']} — nên xoay biến thể.")
            seen.setdefault(i, b["ma"])
        if sum(i in HEAVY_HINGE for i in ids) > 1:
            warn.append(f"Buổi {b['ma']}: 2 bài hinge nặng cùng buổi — quá tải lưng dưới.")
        if sum(i in QUAD for i in ids) > 2:
            warn.append(f"Buổi {b['ma']}: nhiều bài đùi trước cùng buổi.")
        if "back_ext" in ids and not any(ex(i)["nhom"] == "hinge" and i != "back_ext" for i in ids):
            warn.append(f"Buổi {b['ma']}: Back Extension nên đặt ở buổi có hinge / mông.")
    nh = {ex(x["id"])["nhom"] for b in plan for x in b["bai"]}
    if kieu in ("circuit", "chieu_cao", "sai_lech", "mong_nu"):
        return list(dict.fromkeys(warn))
    if "keo_dung" not in nh or "keo_ngang" not in nh:
        warn.append("Tuần thiếu " + ("kéo dọc" if "keo_dung" not in nh else "kéo ngang") + ".")
    if not nh & {"day_ngang", "day_dung"}:
        warn.append("Tuần chưa có bài đẩy.")
    cores = [next((x["id"] for x in b["bai"] if x["loai"] == "Core"), None) for b in plan]
    for a, c in zip(cores, cores[1:]):
        if a and a == c:
            warn.append(f"Bài bụng {ex(a)['ten']} lặp ở 2 buổi liền nhau.")
    return list(dict.fromkeys(warn))


# ------------------------------------------------------------------ lưu / đọc
KHOA = "atlas|{}"          # khoá giáo án HLV trong bảng GiaoAn (1 giáo án đang dùng / khách)


def save(ma_kh: str, info: dict, plan: list[dict], pt: str) -> bool:
    row = {"ma_kh": ma_kh, "id": KHOA.format(ma_kh), "loai_ga": "atlas", "tac_gia": "hlv", "dang_dung": True,
           "ten": "Giáo án HLV · " + KIEU_LICH.get(info.get("kieu", "auto"), ""), "pt": pt,
           "muc_tieu": info["muc_tieu"], "trinh_do": int(info["trinh_do"]), "buoi_tuan": int(info["buoi_tuan"]),
           "han_che": list(info.get("han_che", [])), "ngay_bat_dau": str(info["ngay_bat_dau"])[:10],
           "ghi_chu": info.get("ghi_chu", ""), "kieu": info.get("kieu", "auto"), "buoi": plan}
    return db.append("GiaoAn", KHOA.format(ma_kh), row, pt, ma_kh)


def current(ma_kh: str, df=None) -> dict | None:
    r = db.latest("GiaoAn", ma_kh).get(KHOA.format(ma_kh))
    if not r or not r.get("buoi"):
        return None
    return {"muc_tieu": str(r.get("muc_tieu") or "giam_mo"), "trinh_do": int(r.get("trinh_do") or 0),
            "buoi_tuan": int(r.get("buoi_tuan") or 3), "han_che": list(r.get("han_che") or []),
            "ngay_bat_dau": str(r.get("ngay_bat_dau") or "")[:10], "ghi_chu": str(r.get("ghi_chu") or ""),
            "pt": str(r.get("pt") or ""), "buoi": r["buoi"], "thoi_gian": str(r.get("_luc") or ""),
            "kieu": str(r.get("kieu") or "auto")}


def _so_hiep(lieu: str) -> int:
    import re
    m = re.match(r"\s*(\d+)(?:\s*[–-]\s*(\d+))?\s*(?:×|vòng)", str(lieu))
    return int(m.group(2) or m.group(1)) if m else 3


def to_simple(r: dict, today: date | None = None) -> dict:
    """Giáo án HLV (dạng Atlas) → dạng xem / ghi buổi của cổng khách: liều tự tính theo mục tiêu + tuần hiện tại."""
    goal, lv = str(r.get("muc_tieu") or "giam_mo"), int(r.get("trinh_do") or 0)
    wk = week_no(r.get("ngay_bat_dau"), today)
    buoi = []
    for bu in r.get("buoi") or []:
        bai = []
        for it in bu.get("bai", []):
            x = rx({**it, **({"circuit": True} if bu.get("circuit") else {})}, goal, wk, lv)
            lieu = x["lieu"]
            lan = lieu.split("×", 1)[1].strip() if "×" in lieu else lieu
            bai.append({"bai": it["ten"], "id": it["id"], "nhom": it.get("nhom", ""), "hiep": _so_hiep(lieu), "lan": lan,
                        "rpe_txt": x.get("rpe") or "", "nghi_txt": x.get("nghi") or "", "ss": it.get("ss", ""),
                        "ghi_chu": x.get("rir") if x.get("rir") and x.get("rir") != x.get("rpe") else ""})
        buoi.append({"ten": f"Buổi {bu['ma']} · {bu['ten']}", "ma": bu["ma"], "bai": bai})
    return {**r, "buoi": buoi, "ghi_chu": (r.get("ghi_chu") or "") + (f"\nTuần {wk} · {PHASES[phase_of(wk)]} · cardio: {cardio(goal, wk)}")}


# ------------------------------------------------------------------ v3.56: bảng sửa giáo án (STT · bài · superset · liều · nghỉ)
def ten_id() -> dict:
    """Tên bài → id (tên trong thư viện là duy nhất)."""
    return {b["ten"]: b["id"] for n in tv.library()["nhom"].values() for b in n["bai"]}


def bang_buoi(bu: dict, goal: str, week: int, level: int = 1) -> list[dict]:
    """Một buổi → các hàng cho bảng sửa. Liều / nghỉ hiện giá trị đang áp dụng (tự tính hoặc HLV đã chỉnh)."""
    out = []
    for j, it in enumerate(bu["bai"]):
        r = rx({**it, **({"circuit": True} if bu.get("circuit") else {})}, goal, week, level)
        out.append({"STT": j + 1, "Bài": it["ten"], "Dạng": dang(it.get("loai") or it["id"])[0],
                    "Lầu": str(tang(it["id"]) or "—"),
                    "Superset": str(it.get("ss") or ""), "Hiệp × lần": r["lieu"], "RPE": r["rpe"].replace("RPE ", ""),
                    "Nghỉ": r["nghi"]})
    return out


def _sach(v) -> str:
    s = "" if v is None else str(v).strip()
    return "" if s.lower() in {"nan", "none", "<na>"} else s


def tu_bang(bu: dict, rows: list[dict], goal: str, week: int, level: int = 1) -> dict:
    """Hàng bảng sửa → buổi mới. Sắp theo STT (hàng mới không ghi STT xuống cuối); chỉ lưu rx / nghỉ khi khác số tự tính,
    để giáo án vẫn tự đổi liều theo giai đoạn ở các bài HLV không chỉnh."""
    ids = ten_id()
    cu = {it["id"]: it for it in bu["bai"]}
    tam = []
    for j, r in enumerate(rows):
        eid = ids.get(_sach(r.get("Bài")))
        if not eid:
            continue
        try:
            stt = float(_sach(r.get("STT")) or "nan")
        except ValueError:
            stt = float("nan")
        tam.append((stt if stt == stt else 1e6 + j, j, eid, r))
    out = []
    for _, _, eid, r in sorted(tam, key=lambda t: (t[0], t[1])):
        e = ex(eid)
        it = {k: v for k, v in cu.get(eid, {}).items() if k not in ("rx", "nghi", "ss", "rpe")}
        it.update({k: e[k] for k in ("id", "ten", "nhom", "loai", "dung_cu")})
        if bu.get("circuit"):
            it["circuit"] = True
        auto = _rx(it, goal, week, level)
        lieu, nghi, ss = _sach(r.get("Hiệp × lần")), _sach(r.get("Nghỉ")), _sach(r.get("Superset")).upper()[:2]
        lieu = lieu.replace("x", "×").replace("X", "×").replace("*", "×")
        if lieu and lieu != auto["lieu"]:
            it["rx"] = lieu
        if nghi and nghi != auto["nghi"]:
            it["nghi"] = nghi
        if ss:
            it["ss"] = ss
        rpe = _sach(r.get("RPE")).replace("RPE", "").replace("-", "–").strip()
        if rpe and f"RPE {rpe}" != rpe_tu_rir(auto.get("rir", "")):
            it["rpe"] = f"RPE {rpe}"
        out.append(it)
    gom = []                                           # bài cùng chữ superset kéo về liền nhau (theo vị trí bài đầu tiên)
    for it in out:
        if it in gom:
            continue
        gom.append(it)
        if it.get("ss"):
            gom += [x for x in out if x is not it and x.get("ss") == it["ss"] and x not in gom]
    return {**bu, "bai": gom}


def nhan_ss(bai: list[dict]) -> list[str]:
    """Nhãn superset A1 / A2 … cho các bài liền nhau cùng chữ; bài lẻ trả ''."""
    out = [""] * len(bai)
    j = 0
    while j < len(bai):
        s = str(bai[j].get("ss") or "").strip().upper()
        n = j
        while n + 1 < len(bai) and s and str(bai[n + 1].get("ss") or "").strip().upper() == s:
            n += 1
        if s and n > j:
            for t in range(j, n + 1):
                out[t] = f"{s}{t - j + 1}"
        j = n + 1
    return out


# ------------------------------------------------------------------ v3.58: buổi phục hồi nhẹ (khách ốm nhẹ / đau / quá mệt)
def buoi_nhe(level: int = 0, limits: list[str] | None = None) -> dict:
    """Buổi thay thế khi thể trạng kém: giãn cơ, kích hoạt, core nhẹ — không tính vào chu kỳ giáo án (mã PH)."""
    ids = ["cat_cow", "open_book", "hip_flexor_stretch", "glute_bridge", "bird_dog", "band_pull_apart", "dead_bug", "pec_stretch"]
    bai = [{k: ex(i)[k] for k in ("id", "ten", "nhom", "loai", "dung_cu")} for i in ids
           if tv.exercise(i) and allowed(i, 4, limits or [])]
    return {"ma": "PH", "khuon": "PH", "ten": "Buổi phục hồi nhẹ · giãn cơ, kích hoạt + đi bộ nhẹ 15–20 phút", "bai": bai,
            "giu_thu_tu": True}


def buoi_tiep(plan: dict | None, hist: list[dict]) -> dict | None:
    """v3.58: buổi kế tiếp trong chu kỳ — theo buổi giáo án gần nhất khách đã tập (bỏ qua buổi tick nhanh / phục hồi),
    nên khách tập 3 buổi/tuần với chu kỳ 4 buổi thì tuần sau bắt đầu từ buổi còn lại."""
    if not plan or not plan.get("buoi"):
        return None
    mas = [b["ma"] for b in plan["buoi"]]
    last = next((h.get("buoi_ma") for h in reversed(hist or []) if h.get("buoi_ma") in mas), None)
    return plan["buoi"][(mas.index(last) + 1) % len(mas)] if last else plan["buoi"][0]
