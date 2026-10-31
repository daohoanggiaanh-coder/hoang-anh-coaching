/**
 * Hoàng Anh Coaching v1.0 (2026-10-31) — database riêng trên Google Sheets (miễn phí), đứng tên Gmail của anh.
 *
 * CÁCH CÀI (1 lần, ~5 phút):
 *  1. Vào sheets.new bằng Gmail cá nhân → đặt tên "Hoàng Anh Coaching · Dữ liệu".
 *  2. Tiện ích mở rộng → Apps Script → xoá hết code mẫu → dán toàn bộ file này → Lưu.
 *  3. Chọn hàm caiDat → Chạy → cấp quyền (Google hỏi quyền Sheets + Drive) → mở Nhật ký thực thi,
 *     chép dòng SHEETS_TOKEN = ... vào Secrets của web.
 *  4. Triển khai → Tùy chọn triển khai mới → Loại: Ứng dụng web
 *     · Thực thi với tư cách: Tôi · Ai có quyền truy cập: Bất kỳ ai → Triển khai → chép URL (…/exec) vào
 *     SHEETS_WEBAPP_URL trong Secrets.
 *  ("Bất kỳ ai" chỉ là ai cũng GỌI được URL; không có TOKEN thì không đọc / ghi được gì.)
 *
 * Web app nhận:
 *   POST {token, action:"append", sheet, row:{...}}   → ghi thêm 1 dòng (tự tạo cột)
 *   GET  ?token&action=read&sheet=...                  → toàn bộ dòng của 1 sheet dạng JSON
 *   POST {token, action:"upload", files:[{name,data}]} → lưu ảnh JPEG vào thư mục Drive riêng, trả id
 *   GET  ?token&action=images&ids=a,b                   → {id: base64} (chỉ ảnh trong thư mục riêng)
 */

const SHEETS = ['KhachHang', 'TaiKhoan', 'LichHen', 'CanNang', 'SoDo', 'Anh', 'GiaoAn', 'NhatKy', 'DinhDuong', 'HangCho'];
const COLS = ['thoi_gian', 'khoa', 'ma_kh', 'nguoi', 'du_lieu'];

function token_() { return PropertiesService.getScriptProperties().getProperty('TOKEN'); }

function json_(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj)).setMimeType(ContentService.MimeType.JSON);
}

function doPost(e) {
  try {
    const b = JSON.parse(e.postData.contents);
    if (!token_() || b.token !== token_()) return json_({ ok: false, error: 'sai token' });
    if (b.action === 'upload') {
      const f = folder_();
      const ids = (b.files || []).map(function (x) {
        return f.createFile(Utilities.newBlob(Utilities.base64Decode(x.data), 'image/jpeg', String(x.name || 'anh.jpg'))).getId();
      });
      return json_({ ok: true, ids: ids });
    }
    if (b.action !== 'append' || SHEETS.indexOf(b.sheet) === -1) return json_({ ok: false, error: 'yêu cầu không hợp lệ' });
    const lock = LockService.getScriptLock();
    lock.waitLock(20000);
    try {
      const sh = sheet_(b.sheet);
      const r = b.row || {};
      sh.appendRow(COLS.map(function (c) { return r[c] === undefined || r[c] === null ? '' : String(r[c]); }));
    } finally {
      lock.releaseLock();
    }
    return json_({ ok: true });
  } catch (err) {
    return json_({ ok: false, error: String(err) });
  }
}

function doGet(e) {
  const p = e.parameter || {};
  if (!token_() || p.token !== token_()) return json_({ ok: false, error: 'sai token' });
  if (p.action === 'images') {
    const out = {};
    String(p.ids || '').split(',').filter(String).slice(0, 20).forEach(function (id) {
      try {
        const f = DriveApp.getFileById(id);
        if (inFolder_(f)) out[id] = Utilities.base64Encode(f.getBlob().getBytes());
      } catch (err) { /* ảnh đã xoá */ }
    });
    return json_({ ok: true, images: out });
  }
  if (p.action !== 'read' || SHEETS.indexOf(p.sheet) === -1) return json_({ ok: false, error: 'yêu cầu không hợp lệ' });
  const sh = sheet_(p.sheet);
  if (sh.getLastRow() < 2) return json_({ ok: true, rows: [] });
  const v = sh.getRange(2, 1, sh.getLastRow() - 1, COLS.length).getDisplayValues();
  return json_({ ok: true, rows: v.map(function (r) { const o = {}; COLS.forEach(function (c, i) { o[c] = r[i]; }); return o; }) });
}

function sheet_(name) {
  const ss = SpreadsheetApp.getActive();
  let sh = ss.getSheetByName(name);
  if (!sh) sh = ss.insertSheet(name);
  if (sh.getLastRow() === 0) {
    sh.getRange(1, 1, 1, COLS.length).setValues([COLS]).setFontWeight('bold').setBackground('#1F1F1F').setFontColor('#C8A24A');
    sh.setFrozenRows(1);
    sh.getRange('A:E').setNumberFormat('@');          // giữ nguyên chữ — Sheets không tự đổi SĐT / ngày
  }
  return sh;
}

function folder_() {
  const props = PropertiesService.getScriptProperties();
  const id = props.getProperty('FOLDER_ID');
  if (id) { try { return DriveApp.getFolderById(id); } catch (err) { /* thư mục bị xoá → tạo lại */ } }
  const f = DriveApp.createFolder('Hoàng Anh Coaching · Ảnh khách');
  props.setProperty('FOLDER_ID', f.getId());
  return f;
}

function inFolder_(file) {
  const fid = folder_().getId();
  const it = file.getParents();
  while (it.hasNext()) { if (it.next().getId() === fid) return true; }
  return false;
}

/** CHẠY 1 LẦN: tạo TOKEN, các sheet, thư mục ảnh; in TOKEN ra Nhật ký thực thi. */
function caiDat() {
  const props = PropertiesService.getScriptProperties();
  let t = props.getProperty('TOKEN');
  if (!t) {
    t = Utilities.getUuid().replace(/-/g, '') + Utilities.getUuid().replace(/-/g, '').slice(0, 8);
    props.setProperty('TOKEN', t);
  }
  SHEETS.forEach(sheet_);
  const ss = SpreadsheetApp.getActive();
  const dau = ss.getSheets()[0];
  if (SHEETS.indexOf(dau.getName()) === -1 && dau.getLastRow() === 0) ss.deleteSheet(dau);
  Logger.log('Thư mục ảnh: ' + folder_().getUrl());
  Logger.log('SHEETS_TOKEN = ' + t);
}

/** Đổi TOKEN (khi nghi bị lộ) — nhớ cập nhật lại Secrets của web. */
function doiToken() {
  PropertiesService.getScriptProperties().deleteProperty('TOKEN');
  caiDat();
}
