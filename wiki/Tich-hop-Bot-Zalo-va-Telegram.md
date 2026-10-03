# 💬 Tích Hợp Bot Zalo & Telegram Với n3n OS

### 1. Kiến Trúc Kết Nối
* **Trí tuệ nhân tạo cục bộ**: Chạy trên Ollama Local với mô hình **`qwen2.5:14b`** (nạp 100% vào VRAM GPU Apple Silicon để đạt tốc độ cao nhất, không bị lỗi hoán đổi RAM).
* **Hermes Agent Gateway**: Đóng vai trò điều phối viên, kết nối tài khoản Zalo cá nhân (`zca-js`) và Bot Telegram.
* **n3n Bridge**: Công cụ bắc cầu kết nối Hermes với Second Brain của n3n OS (cổng 7777).

### 2. Cú Pháp Tra Cứu Dự Án
* **Tra cứu thông tin dự án**: 
  - `"Tình hình dự án Đường THU.06 thế nào?"`
  - `"Cho biết giá trị hợp đồng xây lắp của dự án THU.06"`
* **Tra cứu trong nhóm Zalo**: Tag tên Bot `@Nguyên DXC` kèm câu hỏi.

*Cập nhật tự động: 03/10/2026 09:08:15*
