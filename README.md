# Hoàng Anh Coaching · v1.1 · 2026-10-31

**Mới ở v1.1:** 🏋️ **Giáo án khách phong cách Atlas** (chuyển nguyên từ Atlas Academy v3.64): giáo án tuần tự xếp theo mục tiêu ·
trình độ · số buổi · 9 dạng lịch (toàn thân, chuỗi trước/sau, PPL, trên/dưới, tăng mông nữ, circuit, chiều cao, sai lệch tư thế) ·
vùng chấn thương; 8 bài / buổi theo lầu, bụng superset bài cô lập, kết buổi strongman / HIIT; liều tự đổi theo giai đoạn tuần 1–4 / 5–8 / 9–12;
bảng sửa từng buổi; đổi bài khi thiếu máy; ghi buổi có thể trạng đầu buổi + điểm sẵn sàng + gợi ý tạ; khách thấy giáo án trên cổng khách.
📷 **Quét phiếu InBody** (Tiến độ › Số đo — cần `GEMINI_API_KEY`). 🎯 **Lộ trình & mục tiêu** (chỉ HLV): % hoàn thành so với thời gian,
tốc độ thật / tuần, ngày dự kiến đạt đích, chuyên cần, gợi ý điều chỉnh, lộ trình 12 tuần.


Web riêng cho khách cá nhân của HLV Hoàng Anh (tách khỏi Atlas Academy). Chi phí server 0 đồng:
Streamlit Community Cloud + Google Sheets / Drive đứng tên Gmail cá nhân.

## Có gì

**Trang HLV** (đăng nhập bằng tài khoản trong Secrets)
- 📅 **Lịch & nhắc tập**: hôm nay · ngày mai · tuần này · tuần sau · chưa đánh dấu; nút Đã tập / Nghỉ / Dời / Nhắc; đếm buổi còn lại.
- 👤 **Khách & tài khoản**: hồ sơ (hình thức Trực tiếp / Online / Kết hợp, lịch cố định, gói, chấn thương, hồ sơ đầu khoá)
  và **cấp tài khoản cổng khách** (web tạo mật khẩu, soạn sẵn tin Zalo gửi link + tài khoản; đặt lại / khoá được).
- 🏋️ **Giáo án & số tạ**: soạn giáo án nhiều buổi (hiệp, lần, kg, RPE, nghỉ, tempo, superset), tạo nhanh từ mẫu, ghi buổi, xem khách tự ghi.
- 🍽 **Dinh dưỡng**: năng lượng ngày tập / ngày nghỉ, macro, nước, thực đơn hôm nay + 7 ngày theo lịch tập thật, đổi món tự tính lại gram,
  bảng đổi tương đương, danh sách đi chợ, mục **Cách tính** ghi rõ công thức và nguồn.
  v1.3: thẻ bữa ăn cao cấp, **trái cây mỗi ngày** (rau + quả ≥ 400 g, đổi loại theo ngày), **mức đạm** (vừa / cao / rất cao — mặc định cao
  cho khách tập tạ), mục **💊 Bổ sung** khuyến nghị theo mục tiêu (HLV chọn cho từng khách, có liều, lưu ý, mức bằng chứng).
- 🏃 **Cardio** (v1.4): HLV đặt target ngày tập (20–30 phút) / ngày nghỉ (45–90 phút) gồm máy, độ dốc, tốc độ, thời gian;
  khách tự nhập kết quả hoặc HLV nhập từ ảnh màn hình máy (có khoá AI thì web tự đọc số). Cộng thành target tuần, ngày thiếu
  được **bù chia đều** cho các ngày còn lại (có mức tối đa / ngày, khách rảnh mới cho vượt), biểu đồ hoàn thành tuần + 8 tuần.
- 🍽 v1.4: thực đơn **món Việt** (phở, bún, hủ tiếu, xôi, cháo, cơm phần…) — web vẫn tính gram từng thành phần; đạm mặc định
  **2 g / kg cân nặng**. Giáo án: buổi nào cũng có ≥ 1 bài core; lưng dưới yếu → chỉ core giữ thẳng cột sống.
- 👁 **Khách thấy gì** (v1.3): bật / tắt 13 mục cổng khách cho từng khách + **xem trước đúng màn hình khách**.
- 📈 **Tiến độ & báo cáo**: cân hằng ngày (TB 7 ngày), số đo theo đợt, ảnh 3 góc, báo cáo đầu khoá / tiến độ (tin Zalo + PDF).
- ✉️ Soạn tin Zalo · 🥗 Bảng thực phẩm (sửa số theo nhãn) · 📥 Chuyển dữ liệu từ Atlas.

**Cổng khách** (tài khoản + mật khẩu do HLV cấp, mỗi khách chỉ thấy dữ liệu của mình và những mục HLV mở)
- 🏠 Tổng quan: buổi đã tập / còn lại, lịch 2 tuần, cân, % tới mục tiêu, kỷ lục gần đây.
- 🏋️ Tập luyện: xem giáo án, **ghi kg × lần từng hiệp** (điền sẵn gợi ý tăng tạ), **tự tạo plan** khi tập một mình, số tạ & kỷ lục, lịch sử.
- 🍽 Thực đơn: như trang HLV nhưng khách chỉ chỉnh sở thích (số bữa, giờ tập, chế độ ăn, món không ăn).
- 📈 Cân & số đo: khách tự nhập cân mỗi sáng; xem số đo, ảnh trước / hiện tại.
- 🔐 Tài khoản: đổi mật khẩu.

## Cài đặt (1 lần)

1. **Google Sheets riêng**: làm theo hướng dẫn đầu file `apps_script/Code.gs` (tạo sheet bằng Gmail cá nhân → dán code → chạy `caiDat`
   → triển khai Ứng dụng web). Ghi lại `SHEETS_WEBAPP_URL` và `SHEETS_TOKEN`.
2. **GitHub**: đưa thư mục này lên 1 repo **private**.
3. **Streamlit Cloud** (share.streamlit.io): New app → chọn repo, file `app.py` → Advanced settings → Secrets: dán theo
   `.streamlit/secrets.toml.example` (đặt `COACH_PASSWORD` mạnh, `COOKIE_SECRET` ngẫu nhiên, `APP_URL` = link web).
4. Đăng nhập bằng `COACH_USERNAME` / `COACH_PASSWORD` → 📥 Chuyển dữ liệu từ Atlas → kiểm tra từng khách → cấp tài khoản.

Chạy thử trên máy: `pip install -r requirements.txt && streamlit run app.py` (chưa có Secrets → lưu `data/_local`, HLV đăng nhập `demo / demo`;
`python tools/seed_demo.py` tạo 2 khách mẫu, khách đăng nhập `lan / lan12345`).

## Bảo mật
- Mật khẩu khách lưu dạng băm PBKDF2-SHA256 có muối; đặt lại mật khẩu / khoá tài khoản → mọi máy đang nhớ đăng nhập tự đăng xuất.
- Sai mật khẩu 5 lần → khoá thử 5 phút.
- Khách không gọi thẳng Google Sheets; máy chủ lọc dữ liệu theo mã khách đang đăng nhập.
- Đã nối Google Sheets mà chưa đặt `COACH_PASSWORD` → không ai đăng nhập được trang HLV (tài khoản demo chỉ có khi chạy thử).

## Giới hạn cần biết
- Bản miễn phí của Streamlit Cloud cho web "ngủ" khi lâu không ai dùng → người mở đầu tiên chờ web khởi động lại.
- Bảng thực phẩm là **ước tính** theo USDA FoodData Central (món Việt dùng loại gần nhất), sai số ±10–15 %.
- Năng lượng tính theo công thức → **ước tính ban đầu**; chỉnh theo cân trung bình 7 ngày sau 2–3 tuần.
- Khách có bệnh nền / mang thai: thực đơn cần bác sĩ hoặc chuyên gia dinh dưỡng duyệt.

## Kiểm tra
`python -m pytest -q tests` — 15 bài kiểm tra: lưu trữ, đăng nhập & khoá, lịch, công thức dinh dưỡng, thực đơn khớp macro + chế độ ăn,
giáo án & kỷ lục, chuyển dữ liệu Atlas.
