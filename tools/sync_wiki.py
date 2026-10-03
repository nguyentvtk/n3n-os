#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
sync_wiki.py - Module tự động thu thập tri thức tự học của n3n OS
và đồng bộ trực tiếp lên GitHub Wiki (https://github.com/nguyentvtk/n3n-os/wiki)
"""
import os
import sys
import glob
import re
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WIKI_DIR = ROOT / "wiki"
BRAINS_DIR = ROOT / "brains"
WIKI_REMOTE_URL = "https://github.com/nguyentvtk/n3n-os.wiki.git"
MAIN_REMOTE_URL = "https://github.com/nguyentvtk/n3n-os.git"

def log(msg: str):
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [WikiSync] {msg}", flush=True)

def scan_learned_knowledge():
    """Quét toàn bộ tri thức trong các Brain (cả Brain Default và các dự án)"""
    knowledge = {
        "wiki_notes": [],
        "facts": [],
        "projects": []
    }

    if not BRAINS_DIR.exists():
        return knowledge

    # 1. Quét danh sách dự án
    for brain_path in BRAINS_DIR.iterdir():
        if brain_path.is_dir() and not brain_path.name.startswith("."):
            sources_dir = brain_path / "sources"
            source_count = len(list(sources_dir.glob("*.md"))) if sources_dir.exists() else 0
            knowledge["projects"].append({
                "name": brain_path.name,
                "sources_count": source_count
            })

            # 2. Quét wiki notes trong từng brain
            wiki_path = brain_path / "wiki"
            if wiki_path.exists():
                for md_file in wiki_path.glob("*.md"):
                    if md_file.name.startswith("_") or md_file.stem in ("index", "log"):
                        continue
                    try:
                        content = md_file.read_text(encoding="utf-8")
                        title = md_file.stem
                        knowledge["wiki_notes"].append({
                            "title": title,
                            "filename": md_file.name,
                            "content": content,
                            "brain": brain_path.name
                        })
                    except Exception as e:
                        log(f"Lỗi đọc file {md_file}: {e}")

            # 3. Quét facts trong memory
            facts_path = brain_path / "memory" / "facts"
            if facts_path.exists():
                for md_file in facts_path.glob("*.md"):
                    try:
                        content = md_file.read_text(encoding="utf-8")
                        knowledge["facts"].append({
                            "title": md_file.stem,
                            "content": content,
                            "brain": brain_path.name
                        })
                    except Exception as e:
                        log(f"Lỗi đọc fact {md_file}: {e}")

    return knowledge

def generate_wiki_content(knowledge):
    """Tạo cấu trúc các trang Markdown chuẩn hóa cho GitHub Wiki"""
    WIKI_DIR.mkdir(parents=True, exist_ok=True)
    now_str = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    # 1. Trang Home.md (Trang chủ Wiki)
    home_content = f"""# 🧠 n3n OS - Hệ Thống Tri Thức Tự Học & Quản Trị Dự Án

Chào mừng đến với Wiki Tri Thức của **n3n OS** (Hệ điều hành AI phục vụ Quản lý Dự án Đầu tư Xây dựng & Chuyển đổi số).

> [!NOTE]
> Hệ thống Wiki này được **n3n OS tự động đúc kết và cập nhật** từ quá trình tương tác, xử lý hồ sơ dự án, và phân tích tài liệu thực tế của Ban Quản lý Dự án.

---

### 📌 Danh Mục Chuyên Đề Chính

* 🏗️ **[[Quản lý Dự án ĐTXD|Quan-ly-Du-an-DTXD]]**: Quy trình thẩm định, lựa chọn nhà thầu, quản lý hợp đồng thi công, nghiệm thu và quyết toán dự án.
* 💻 **[[Chuyển đổi số & Tự động hoá|Chuyen-doi-so-va-Tu-dong-hoa]]**: Giải pháp văn phòng số, kết nối lưu trữ đa đám mây, bóc tách dữ liệu thông minh.
* 🤖 **[[Cơ chế Tự học AI|Co-che-Tu-hoc-AI]]**: Mô hình học tăng cường từ dữ liệu cục bộ, phân loại tri thức, bảo mật dữ liệu tuyệt đối.
* 💬 **[[Tích hợp Bot Zalo & Telegram|Tich-hop-Bot-Zalo-va-Telegram]]**: Kết nối trợ lý AI với Hermes Agent và Ollama Local (`qwen2.5:14b`).
* 📜 **[[Nhật ký & Bài học Tự học|Nhat-ky-Tu-hoc]]**: Bảng tổng hợp các bài học kinh nghiệm và kiến thức mới nhất do AI tự ghi nhận.

---

### 📊 Thống Kê Kho Tri Thức Hiện Tại

| Chỉ số | Số lượng | Ghi chú |
| :--- | :--- | :--- |
| **Dự án được quản lý** | {len(knowledge['projects'])} | Các dự án đầu tư xây dựng thực tế |
| **Tài liệu nguồn đã phân rã** | {sum(p['sources_count'] for p in knowledge['projects'])} | Hợp đồng, quyết định, kế hoạch LCNT |
| **Khái niệm Wiki đúc kết** | {len(knowledge['wiki_notes'])} | Khái niệm & quy trình tái sử dụng |
| **Facts & Ký ức ghi nhớ** | {len(knowledge['facts'])} | Thông tin thực chứng đã xác thực |

---

### 📁 Danh Sách Dự Án Đang Được Theo Dõi
"""
    for p in sorted(knowledge["projects"], key=lambda x: x["name"]):
        home_content += f"- **{p['name']}**: `{p['sources_count']}` tài liệu nguồn đã nạp vào Brain.\n"

    home_content += f"\n*Được cập nhật tự động lúc: {now_str}*\n"
    (WIKI_DIR / "Home.md").write_text(home_content, encoding="utf-8")

    # 2. Trang _Sidebar.md (Thanh điều hướng Sidebar của GitHub Wiki)
    sidebar_content = """### 🧭 Điều Hướng Wiki
* [[🏠 Trang Chủ|Home]]
* [[🏗️ Quản lý Dự án ĐTXD|Quan-ly-Du-an-DTXD]]
* [[💻 Chuyển Đổi Số|Chuyen-doi-so-va-Tu-dong-hoa]]
* [[🤖 Cơ Chế Tự Học AI|Co-che-Tu-hoc-AI]]
* [[💬 Bot Zalo & Telegram|Tich-hop-Bot-Zalo-va-Telegram]]
* [[📜 Nhật Ký Tự Học|Nhat-ky-Tu-hoc]]

---
### 🔗 Liên Kết
* [GitHub Repository](https://github.com/nguyentvtk/n3n-os)
* [n3n OS Local Dashboard](http://127.0.0.1:7777)
"""
    (WIKI_DIR / "_Sidebar.md").write_text(sidebar_content, encoding="utf-8")

    # 3. Trang _Footer.md
    footer_content = f"""---
*n3n OS Wiki Knowledge Base • Tự động đồng bộ bởi Engine n3n OS • Lần cập nhật cuối: {now_str}*
"""
    (WIKI_DIR / "_Footer.md").write_text(footer_content, encoding="utf-8")

    # 4. Trang Quan-ly-Du-an-DTXD.md
    dtxd_content = f"""# 🏗️ Quy Trình & Nghiệp Vụ Quản Lý Dự Án Đầu Tư Xây Dựng

Trang này tổng hợp các chuẩn nghiệp vụ và quy trình mà n3n OS áp dụng để hỗ trợ Ban Quản lý Dự án:

### 1. Chu trình Dự án Đầu tư Xây dựng Công
1. **Chuẩn bị dự án**:
   - Khảo sát, lập Báo cáo nghiên cứu khả thi (hoặc Báo cáo kinh tế - kỹ thuật).
   - Thẩm định và Phê duyệt dự án đầu tư.
2. **Thực hiện dự án**:
   - Lập, thẩm định và phê duyệt Kế hoạch lựa chọn nhà thầu (KHLCNT).
   - Tổ chức đấu thầu qua mạng (Hệ thống Mạng đấu thầu Quốc gia).
   - Thương thảo, ký kết Hợp đồng thi công xây dựng (Ví dụ: Hợp đồng số `06/2026/HĐ-XD` trị giá 12,05 tỷ VNĐ dự án Đường THU.06).
   - Quản lý chất lượng, tiến độ thi công, an toàn lao động và bảo vệ môi trường.
   - Nghiệm thu khối lượng hoàn thành, lập hồ sơ giải ngân và thanh toán theo đợt.
3. **Kết thúc xây dựng & Bàn giao đưa vào sử dụng**:
   - Nghiệm thu hoàn thành công trình đưa vào sử dụng.
   - Lập hồ sơ Quyết toán vốn đầu tư dự án hoàn thành theo Thông tư của Bộ Tài chính.

### 2. Nguyên tắc Kiểm soát Rủi ro Hợp đồng
* Kiểm soát chặt chẽ giá trị tạm ứng, thời hạn bảo lãnh tạm ứng và bảo lãnh thực hiện hợp đồng.
* Đối chiếu khối lượng thanh toán thực tế với hồ sơ thiết kế bản vẽ thi công đã duyệt.
* Cảnh báo sớm các vướng mắc về giải phóng mặt bằng (GPMB) và di dời hạ tầng kỹ thuật.

*Cập nhật tự động: {now_str}*
"""
    (WIKI_DIR / "Quan-ly-Du-an-DTXD.md").write_text(dtxd_content, encoding="utf-8")

    # 5. Trang Chuyen-doi-so-va-Tu-dong-hoa.md
    cds_content = f"""# 💻 Chuyển Đổi Số & Tự Động Hoá Ban Quản Lý Dự Án

### 1. Mô hình Văn phòng Số Không Giấy Tờ
* **Lưu trữ dữ liệu tập trung**: Hồ sơ dự án được đồng bộ tự động từ Google Drive, Dropbox và OneDrive về Second Brain của n3n OS.
* **Bóc tách văn bản thông minh**: Sử dụng các thư viện `pypdf`, `python-docx`, `openpyxl` kết hợp AI để chuyển đổi hồ sơ scan/văn bản PDF sang Markdown chuẩn hóa.
* **Tìm kiếm ngữ nghĩa (Semantic Search)**: Truy xuất ngay lập tức các điều khoản hợp đồng, số tiền, ngày ký, nhà thầu trúng thầu mà không cần lục tìm văn bản giấy.

### 2. Tự Động Hoá Phê Duyệt & Tra Cứu
* Tích hợp Bot Zalo cá nhân & nhóm Zalo thông qua **Hermes Agent** và **n3n Bridge**.
* Cán bộ quản lý có thể gửi câu hỏi bằng giọng nói hoặc tin nhắn văn bản, hệ thống đọc trực tiếp từ Brain dự án để trả lời tức thì.

*Cập nhật tự động: {now_str}*
"""
    (WIKI_DIR / "Chuyen-doi-so-va-Tu-dong-hoa.md").write_text(cds_content, encoding="utf-8")

    # 6. Trang Co-che-Tu-hoc-AI.md
    learn_content = f"""# 🤖 Cơ Chế Tự Học Của n3n OS (Self-Learning Engine)

n3n OS được trang bị Engine Tự Học độc lập (`server/learn.py`), vận hành theo các nguyên tắc an toàn dữ liệu khắt khe:

### 1. Chu Trình Tự Học (Learning Lifecycle)
```mermaid
flowchart LR
    A[Hội thoại / Tài liệu mới] --> B[Phân tích & Tách Fact/Wiki]
    B --> C{{Kiểm tra An toàn}}
    C -->|Đạt chuẩn| D[Ghi vào Brain Vault]
    C -->|Chưa nguồn| E[Xếp vào Cần xác minh]
    D --> F[Đồng bộ sang GitHub Wiki]
```

### 2. Các Tầng Tri Thức (Provenance Tiers)
1. **Facts (Ký ức thực chứng)**: Lưu lại các thông tin chắc chắn về dự án (nhà thầu, giá trị, thời hạn, văn bản chỉ đạo).
2. **Wiki Concepts (Khái niệm tái dùng)**: Các quy trình, biểu mẫu, cách thức giải quyết công việc có tính quy luật.
3. **Skills (Kỹ năng mới)**: Khi AI học được cách xử lý một loại công việc mới, nó tự sinh skill để tái sử dụng.

### 3. Đồng Bộ Trực Tiếp Lên GitHub Wiki
* Bất cứ khi nào hệ thống đúc kết được kiến thức mới, module `sync_wiki.py` sẽ tự động chuyển hóa thành các trang tài liệu Markdown và đẩy lên kho lưu trữ GitHub Wiki của đơn vị.

*Cập nhật tự động: {now_str}*
"""
    (WIKI_DIR / "Co-che-Tu-hoc-AI.md").write_text(learn_content, encoding="utf-8")

    # 7. Trang Tich-hop-Bot-Zalo-va-Telegram.md
    bot_content = f"""# 💬 Tích Hợp Bot Zalo & Telegram Với n3n OS

### 1. Kiến Trúc Kết Nối
* **Trí tuệ nhân tạo cục bộ**: Chạy trên Ollama Local với mô hình **`qwen2.5:14b`** (nạp 100% vào VRAM GPU Apple Silicon để đạt tốc độ cao nhất, không bị lỗi hoán đổi RAM).
* **Hermes Agent Gateway**: Đóng vai trò điều phối viên, kết nối tài khoản Zalo cá nhân (`zca-js`) và Bot Telegram.
* **n3n Bridge**: Công cụ bắc cầu kết nối Hermes với Second Brain của n3n OS (cổng 7777).

### 2. Cú Pháp Tra Cứu Dự Án
* **Tra cứu thông tin dự án**: 
  - `"Tình hình dự án Đường THU.06 thế nào?"`
  - `"Cho biết giá trị hợp đồng xây lắp của dự án THU.06"`
* **Tra cứu trong nhóm Zalo**: Tag tên Bot `@Nguyên DXC` kèm câu hỏi.

*Cập nhật tự động: {now_str}*
"""
    (WIKI_DIR / "Tich-hop-Bot-Zalo-va-Telegram.md").write_text(bot_content, encoding="utf-8")

    # 8. Trang Nhat-ky-Tu-hoc.md
    log_content = f"""# 📜 Nhật Ký & Danh Sách Tri Thức Đã Tự Học

Trang này lưu vết toàn bộ các bài học, quy trình và ghi chép tri thức mà AI đã tích lũy:

### 1. Các Khái Niệm Wiki ({len(knowledge['wiki_notes'])} mục)
"""
    if knowledge["wiki_notes"]:
        for note in knowledge["wiki_notes"]:
            log_content += f"- **{note['title']}** *(Brain: {note['brain']})*\n"
    else:
        log_content += "*Chưa có ghi chép wiki nào mới. Hệ thống sẽ tự động cập nhật khi bạn hội thoại và nạp thêm tài liệu.*\n"

    log_content += f"\n### 2. Các Ký Ức Thực Chứng (Facts: {len(knowledge['facts'])} mục)\n"
    if knowledge["facts"]:
        for fact in knowledge["facts"]:
            log_content += f"- **{fact['title']}** *(Brain: {fact['brain']})*\n"
    else:
        log_content += "*Chưa có ký ức fact riêng biệt.*\n"

    log_content += f"\n*Cập nhật tự động: {now_str}*\n"
    (WIKI_DIR / "Nhat-ky-Tu-hoc.md").write_text(log_content, encoding="utf-8")

    # 9. Ghi các wiki notes riêng lẻ ra WIKI_DIR
    for note in knowledge["wiki_notes"]:
        clean_name = re.sub(r"[^\w\s-]", "", note["title"]).strip().replace(" ", "-")
        if clean_name and clean_name not in ("Home", "_Sidebar", "_Footer"):
            target_path = WIKI_DIR / f"{clean_name}.md"
            target_path.write_text(note["content"], encoding="utf-8")

    log(f"Đã tạo {len(list(WIKI_DIR.glob('*.md')))} trang tài liệu trong thư mục wiki/")

def sync_to_github():
    """Đồng bộ các file Wiki lên GitHub"""
    # 1. Commit và push vào nhánh chính của repo n3n-os (đảm bảo wiki/ luôn được backup trong repo code)
    try:
        subprocess.run(["git", "add", "wiki/"], cwd=str(ROOT), capture_output=True, text=True)
        r = subprocess.run(["git", "status", "--porcelain", "wiki/"], cwd=str(ROOT), capture_output=True, text=True)
        if r.stdout.strip():
            msg = f"docs(wiki): update self-learned knowledge [{datetime.now().strftime('%Y-%m-%d %H:%M')}]"
            subprocess.run(["git", "commit", "-m", msg], cwd=str(ROOT), capture_output=True, text=True)
            subprocess.run(["git", "push", "origin", "main"], cwd=str(ROOT), capture_output=True, text=True)
            log("Đã đồng bộ thư mục wiki/ vào kho lưu trữ chính GitHub.")
    except Exception as e:
        log(f"Lỗi commit wiki vào repo chính: {e}")

    # 2. Thử đồng bộ trực tiếp sang GitHub Wiki Git repo (https://github.com/nguyentvtk/n3n-os.wiki.git)
    wiki_repo_dir = ROOT / ".wiki_git_clone"
    try:
        # Kiểm tra xem GitHub Wiki đã được kích hoạt hay chưa
        r_check = subprocess.run(["git", "ls-remote", WIKI_REMOTE_URL], capture_output=True, text=True, timeout=15)
        if r_check.returncode == 0:
            log("Phát hiện GitHub Wiki Git remote đã sẵn sàng. Tiến hành đẩy dữ liệu trực tiếp...")
            if not wiki_repo_dir.exists():
                subprocess.run(["git", "clone", WIKI_REMOTE_URL, str(wiki_repo_dir)], capture_output=True, text=True)
            else:
                subprocess.run(["git", "-C", str(wiki_repo_dir), "pull"], capture_output=True, text=True)

            # Copy toàn bộ file md từ WIKI_DIR sang wiki_repo_dir
            for f in WIKI_DIR.glob("*.md"):
                shutil.copy2(f, wiki_repo_dir / f.name)

            subprocess.run(["git", "-C", str(wiki_repo_dir), "add", "-A"], capture_output=True, text=True)
            r_st = subprocess.run(["git", "-C", str(wiki_repo_dir), "status", "--porcelain"], capture_output=True, text=True)
            if r_st.stdout.strip():
                subprocess.run(["git", "-C", str(wiki_repo_dir), "commit", "-m", f"docs: auto-sync wiki {datetime.now().strftime('%Y-%m-%d %H:%M')}"], capture_output=True, text=True)
                push_res = subprocess.run(["git", "-C", str(wiki_repo_dir), "push", "origin", "HEAD:master"], capture_output=True, text=True)
                if push_res.returncode == 0:
                    log("Đã đẩy thành công toàn bộ tri thức tự học lên GitHub Wiki!")
                else:
                    subprocess.run(["git", "-C", str(wiki_repo_dir), "push", "origin", "HEAD:main"], capture_output=True, text=True)
        else:
            log("Ghi chú: Kho GitHub Wiki (.wiki.git) chưa khởi tạo trang đầu trên web.")
            log("Tri thức tự học hiện đã được lưu và đẩy an toàn vào thư mục wiki/ trên GitHub.")
            log("👉 Để hiển thị trực tiếp trên tab Wiki GitHub, bạn chỉ cần mở https://github.com/nguyentvtk/n3n-os/wiki và bấm 'Create the first page'.")
    except Exception as e:
        log(f"Lưu ý khi đồng bộ .wiki.git: {e}")

def main():
    log("=== BẮT ĐẦU QUÁ TRÌNH TỰ ĐỘNG THU THẬP & ĐỒNG BỘ WIKI n3n OS ===")
    knowledge = scan_learned_knowledge()
    generate_wiki_content(knowledge)
    sync_to_github()
    log("=== HOÀN TẤT ĐỒNG BỘ WIKI ===")

if __name__ == "__main__":
    main()
