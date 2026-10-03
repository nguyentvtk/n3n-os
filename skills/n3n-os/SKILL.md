---
name: n3n-os
description: "Điều phối và truy vấn Second Brain n3n OS (Javis OS) phục vụ Quản lý Dự án Đầu tư Xây dựng & Chuyển đổi số. Quản lý danh sách dự án, tiến độ, ghi nhật ký công trường, tra cứu hồ sơ và bảng việc Kanban."
version: 1.0.0
author: Antigravity & Hermes Team
license: MIT
platforms: [macos, linux, windows]
metadata:
  hermes:
    tags: [Construction, Project-Management, Second-Brain, n3n-OS, Javis, Zalo, Ban-QLDA]
---

# Kỹ năng n3n OS (Second Brain & Quản lý Dự án Đầu tư Xây dựng)

Kỹ năng này kết nối Hermes Agent với hệ thống **n3n OS** (Second Brain cá nhân và quản lý dự án Ban QLDA).

## Khi nào sử dụng (Triggers)
Kích hoạt kỹ năng này khi người dùng nhắn tin qua Zalo hoặc Terminal:
1. Có tiền tố/thẻ nhắc: `@n3n`, `@javis`, `n3n`, `javis`.
2. Hỏi về các dự án cụ thể của Ban Quản lý Dự án:
   - `Đường THU.06` (Mã 8179903)
   - `Nạo vét kênh tiêu Bàu Châu É` (Mã 8179906)
   - `Trường Tiểu học Lương Định Của` (Mã 817990)
   - `Trường Tiểu học Tân Hưng` (Mã 8179901)
   - `Nâng cấp, sửa chữa Nhà làm việc BCH quân sự xã` (Mã 817990)
   - `Đường THU.74B` (Mã 8179905)
   - `Đường THU.01` (Mã 8179900)
3. Các yêu cầu về:
   - "Xem danh sách dự án", "Tiến độ dự án...", "Thông tin dự án..."
   - "Ghi nhật ký...", "Nhật ký công trình hôm nay..."
   - "Xem bảng việc Kanban", "Việc cần làm của dự án..."
   - "Tạo task mới...", "Thêm việc cho dự án..."
   - "Tìm tài liệu...", "Tra cứu quyết định / văn bản..."

---

## Công cụ thực thi (Execution Tool)

Mọi thao tác truy vấn và cập nhật dữ liệu được thực hiện thông qua công cụ CLI:
`/Users/n3n/Documents/Antigravity 2.0/n3n OS/bridge/n3n_bridge.py`

### 1. Liệt kê toàn bộ dự án
Chạy lệnh khi người dùng hỏi: *"Có những dự án nào?", "Danh sách dự án", "Các công trình đang quản lý"*:
```bash
python3 "/Users/n3n/Documents/Antigravity 2.0/n3n OS/bridge/n3n_bridge.py" list-projects
```

### 2. Xem thông tin chi tiết / tiến độ dự án
Chạy lệnh khi người dùng hỏi về một dự án cụ thể:
```bash
python3 "/Users/n3n/Documents/Antigravity 2.0/n3n OS/bridge/n3n_bridge.py" project-info "<tên_hoặc_từ_khóa_dự_án>"
```
*Ví dụ:* `python3 "/Users/n3n/Documents/Antigravity 2.0/n3n OS/bridge/n3n_bridge.py" project-info "THU.06"`

### 3. Ghi nhật ký công trình (Daily Log)
Chạy lệnh khi người dùng yêu cầu ghi nhật ký hiện trường:
```bash
python3 "/Users/n3n/Documents/Antigravity 2.0/n3n OS/bridge/n3n_bridge.py" add-log "<tên_dự_án>" "<nội dung nhật ký>"
```
*Ví dụ:* `python3 "/Users/n3n/Documents/Antigravity 2.0/n3n OS/bridge/n3n_bridge.py" add-log "Bàu Châu É" "Nhà thầu thi công nạo vét đạt 100m đoạn qua cống số 2, thời tiết nắng ráo."`

### 4. Tra cứu bảng việc Kanban
Chạy lệnh khi người dùng hỏi về công việc, tiến độ phân công:
```bash
# Xem tất cả task
python3 "/Users/n3n/Documents/Antigravity 2.0/n3n OS/bridge/n3n_bridge.py" kanban

# Hoặc lọc theo dự án
python3 "/Users/n3n/Documents/Antigravity 2.0/n3n OS/bridge/n3n_bridge.py" kanban --project "Lương Định Của"
```

### 5. Thêm việc mới vào Kanban
Chạy lệnh khi người dùng giao việc hoặc tạo việc cần làm:
```bash
python3 "/Users/n3n/Documents/Antigravity 2.0/n3n OS/bridge/n3n_bridge.py" add-task "<tên_dự_án>" "<tiêu đề việc>" --priority 1
```

### 6. Tìm kiếm hồ sơ, văn bản, quyết định trong Second Brain
Chạy lệnh khi người dùng hỏi về văn bản hoặc trích đoạn tài liệu:
```bash
python3 "/Users/n3n/Documents/Antigravity 2.0/n3n OS/bridge/n3n_bridge.py" search "<từ khóa>"
```

### 7. Hỏi n3n OS AI tổng hợp
Dùng khi người dùng có câu hỏi phức tạp cần n3n OS suy luận:
```bash
python3 "/Users/n3n/Documents/Antigravity 2.0/n3n OS/bridge/n3n_bridge.py" ask-ai "<câu hỏi>" --brain "<tên_dự_án>"
```

---

## Định dạng câu trả lời gửi về Zalo
Khi trả lời người dùng qua Zalo về các vấn đề dự án:
- Luôn đặt tiền tố: `[🧠 n3n OS - Quản trị Dự án]`
- Trình bày ngắn gọn, rõ ràng, gạch đầu dòng các ý chính.
- Nêu rõ tên dự án, thời gian, trạng thái và tệp lưu trữ nếu có.
