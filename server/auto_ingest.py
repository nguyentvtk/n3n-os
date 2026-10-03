# -*- coding: utf-8 -*-
"""
Auto-ingest interceptor for n3n OS.
Tự động chuyển đổi tài liệu đính kèm (PDF, DOCX, XLSX, TXT) sang định dạng Markdown
lưu vào sources/ của Brain, chuyển file gốc vào attachments/, và chuẩn bị ngữ cảnh
phân tích trực tiếp cho LLM mà không cần qua vòng lặp tool calling chậm chạp/dễ lỗi.
"""

import os
import re
import shutil
import unicodedata
from datetime import datetime
from pathlib import Path


def _sanitize_filename(name: str) -> str:
    name = re.sub(r'[\\/*?:"<>|]', "", name)
    name = unicodedata.normalize("NFC", name)
    return name.strip()


def extract_text_from_file(file_path: Path) -> str:
    """Trích xuất văn bản từ PDF, DOCX, XLSX, TXT."""
    if not file_path.is_file():
        return ""
    ext = file_path.suffix.lower()
    
    # 1. PDF
    if ext == ".pdf":
        try:
            from pypdf import PdfReader
            reader = PdfReader(str(file_path))
            pages = []
            for i, page in enumerate(reader.pages):
                txt = page.extract_text() or ""
                if txt.strip():
                    pages.append(f"### Trang {i+1}\n{txt.strip()}")
            return "\n\n".join(pages)
        except Exception as e:
            return f"(Không thể trích xuất PDF: {e})"

    # 2. DOCX
    elif ext in (".docx", ".doc"):
        try:
            import docx
            doc = docx.Document(str(file_path))
            pars = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
            tables_txt = []
            for table in doc.tables:
                t_lines = []
                for row in table.rows:
                    cells = [c.text.strip().replace("\n", " ") for c in row.cells]
                    if any(cells):
                        t_lines.append(" | ".join(cells))
                if t_lines:
                    tables_txt.append("\n".join(t_lines))
            full = "\n\n".join(pars)
            if tables_txt:
                full += "\n\n### Bảng dữ liệu:\n" + "\n\n".join(tables_txt)
            return full
        except Exception as e:
            return f"(Không thể trích xuất DOCX: {e})"

    # 3. XLSX
    elif ext in (".xlsx", ".xls"):
        try:
            import openpyxl
            wb = openpyxl.load_workbook(str(file_path), data_only=True)
            lines = []
            for s in wb.worksheets:
                lines.append(f"## Bảng tính: {s.title}")
                for row in s.iter_rows(values_only=True):
                    r_vals = [str(v).strip() if v is not None else "" for v in row]
                    if any(r_vals):
                        lines.append(" | ".join(r_vals))
            return "\n".join(lines)
        except Exception as e:
            return f"(Không thể trích xuất XLSX: {e})"

    # 4. Text / MD
    else:
        try:
            return file_path.read_text(encoding="utf-8", errors="replace").strip()
        except Exception as e:
            return f"(Không thể đọc tệp văn bản: {e})"


def ingest_single_file(source_path: Path, brain_root: Path) -> dict:
    """Chuyển 1 file sang .md lưu trong sources/ và chuyển bản gốc sang attachments/."""
    if not source_path.is_file():
        return {"ok": False, "error": f"File không tồn tại: {source_path}"}
    
    sources_dir = brain_root / "sources"
    attachments_dir = brain_root / "attachments"
    sources_dir.mkdir(parents=True, exist_ok=True)
    attachments_dir.mkdir(parents=True, exist_ok=True)
    
    orig_name = source_path.name
    stem = source_path.stem
    clean_stem = _sanitize_filename(stem)
    md_name = f"{clean_stem}.md"
    md_path = sources_dir / md_name
    
    # Trích xuất nội dung
    content = extract_text_from_file(source_path)
    today_str = datetime.now().strftime("%Y-%m-%d")
    
    # Frontmatter
    frontmatter = (
        "---\n"
        "type: source\n"
        "source_kind: document\n"
        "status: unprocessed\n"
        f"created: {today_str}\n"
        f"original: {orig_name}\n"
        "---\n\n"
    )
    
    body = content if content.strip() else f"*(Tài liệu {orig_name} không có lớp văn bản thô)*"
    full_md = frontmatter + body
    
    # Ghi file .md
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(full_md)
        
    # Chép file gốc sang attachments
    dest_attach = attachments_dir / orig_name
    try:
        shutil.copy2(str(source_path), str(dest_attach))
    except Exception:
        pass
        
    # Xoá file trong staging nếu đang nằm trong staging
    if ".staging" in str(source_path.resolve()):
        try:
            source_path.unlink()
        except Exception:
            pass
            
    return {
        "ok": True,
        "md_path": str(md_path),
        "md_name": md_name,
        "orig_name": orig_name,
        "content_length": len(body),
        "preview": body[:500]
    }


def should_auto_ingest(message: str) -> bool:
    """Kiểm tra xem người dùng có ý định lưu/ingest/phân tích hồ sơ đính kèm không."""
    low = message.lower()
    intent_keywords = [
        "lưu vào source", "lưu vào nguồn", "lưu vào sources",
        "chuyển đổi", "chuyen doi", "sang định dạng .md", "sang .md",
        "ingest", "ghi vào second brain", "lưu vào brain",
        "phân tích hồ sơ", "phan tich ho so", "phân tích dự án",
        "tóm tắt hồ sơ", "lưu hồ sơ", "đưa vào source"
    ]
    return any(k in low for k in intent_keywords)


def extract_staged_paths(message: str) -> list[Path]:
    """Tìm tất cả đường dẫn tệp đính kèm trong nội dung tin nhắn."""
    paths = []
    # Pattern đường dẫn dạng bullet: - /Users/... hoặc - C:\...
    pattern = r"[-*]\s+((?:[A-Za-z]:[\\/]|/)[^\r\n]+?\.(?:pdf|docx|doc|xlsx|xls|txt|csv|png|jpg|jpeg))"
    matches = re.findall(pattern, message, re.IGNORECASE)
    for m in matches:
        p = Path(m.strip())
        if p.exists() and p not in paths:
            paths.append(p)
            
    # Pattern phụ: bất kỳ file nào có trong .staging
    staging_pattern = r"((?:[A-Za-z]:[\\/]|/)[^\r\n\"\'`]+?/\.staging/[^\r\n\"\'`]+?\.(?:pdf|docx|doc|xlsx|xls|txt|csv|png|jpg|jpeg))"
    for m in re.findall(staging_pattern, message, re.IGNORECASE):
        p = Path(m.strip())
        if p.exists() and p not in paths:
            paths.append(p)
            
    return paths


def perform_auto_ingest_and_build_prompt(user_message: str, brain_root_str: str) -> tuple[bool, str, list[dict]]:
    """
    Nếu thỏa mãn điều kiện, tự động chuyển đổi toàn bộ file sang .md trong sources/
    và xây dựng prompt chuyên sâu trực tiếp cho LLM.
    Trả về: (has_ingested, new_user_prompt, results)
    """
    staged_paths = extract_staged_paths(user_message)
    if not staged_paths:
        return False, user_message, []
        
    if not should_auto_ingest(user_message):
        return False, user_message, []
        
    brain_root = Path(brain_root_str)
    results = []
    summaries = []
    
    for sp in staged_paths:
        res = ingest_single_file(sp, brain_root)
        results.append(res)
        if res.get("ok"):
            orig = res.get("orig_name")
            preview = res.get("preview", "").replace("\n", " ")[:300]
            summaries.append(f"📄 **{orig}**:\n{preview}...\n")
            
    # Xây dựng prompt mới trực tiếp cho LLM
    # Tách yêu cầu thật sự của người dùng (bỏ qua khối [File đính kèm...])
    user_actual_query = re.sub(r"\[File đính kèm.*?\]", "", user_message, flags=re.DOTALL).strip()
    if not user_actual_query:
        user_actual_query = "Phân tích toàn bộ hồ sơ dự án này một cách chi tiết và toàn diện."
        
    summary_block = "\n".join(summaries)
    new_prompt = (
        f"Hệ thống n3n OS đã tự động chuyển đổi và lưu thành công {len(results)} tài liệu vào thư mục Sources của dự án.\n\n"
        f"### DANH SÁCH VÀ TRÍCH YẾU CÁC TÀI LIỆU VỪA LƯU VÀO SOURCES:\n"
        f"{summary_block}\n\n"
        f"### YÊU CẦU PHÂN TÍCH:\n"
        f"{user_actual_query}\n\n"
        f"HƯỚNG DẪN THỰC HIỆN DÀNH CHO BẠN:\n"
        f"1. Tổng hợp và phân tích chi tiết hồ sơ dự án dựa trên các tài liệu đã nạp ở trên:\n"
        f"   - Tên dự án, Chủ đầu tư, Cơ quan phê duyệt.\n"
        f"   - Tên gói thầu, Đơn vị trúng thầu (nhà thầu), Hình thức lựa chọn nhà thầu.\n"
        f"   - Số Hợp đồng, Ngày ký hợp đồng, Giá trị hợp đồng (ghi rõ bằng số và chữ), Thời gian thực hiện hợp đồng.\n"
        f"   - Các Quyết định phê duyệt quan trọng (Phê duyệt dự án, KHLCNT, Dự toán, E-HSMT, KQLCNT).\n"
        f"   - Tiến độ thực hiện, bảo lãnh hợp đồng, bảo hiểm công trình, các mốc thanh toán.\n"
        f"   - Đánh giá tính pháp lý và các điểm cần lưu ý trong quá trình triển khai dự án.\n"
        f"2. Trình bày bài phân tích mạch lạc, chuyên nghiệp, sử dụng bảng biểu nếu cần.\n"
        f"3. TUYỆT ĐỐI KHÔNG hỏi lại người dùng, KHÔNG nói về công cụ hệ thống hay tool calling, BẮT ĐẦU PHÂN TÍCH NGAY LẬP TỨC."
    )
    
    return True, new_prompt, results
