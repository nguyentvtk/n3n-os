#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
n3n_bridge.py - Cầu nối điều phối giữa Hermes Agent (Zalo) và Second Brain n3n OS.
Cho phép truy vấn dữ liệu dự án, nhật ký công trình, bảng việc Kanban và gửi câu hỏi sang n3n OS.
"""

import sys
import os
import re
import json
import sqlite3
import argparse
import unicodedata
from datetime import datetime
from pathlib import Path
import urllib.request
import urllib.parse

ROOT_DIR = Path(__file__).resolve().parent.parent
BRAINS_DIR = ROOT_DIR / "brains"
KANBAN_DB = ROOT_DIR / "server" / "kanban.sqlite3"
N3N_SERVER_URL = "http://127.0.0.1:7777"


def remove_accents(input_str: str) -> str:
    """Loại bỏ dấu tiếng Việt để tìm kiếm mờ (fuzzy search)."""
    if not input_str:
        return ""
    nfkd = unicodedata.normalize('NFKD', input_str)
    return ''.join([c for c in nfkd if not unicodedata.combining(c)]).lower()


def find_project_brain(query: str):
    """Tìm thư mục brain phù hợp với từ khóa tìm kiếm."""
    if not BRAINS_DIR.exists():
        return None

    query_clean = remove_accents(query.strip())
    candidates = [p for p in BRAINS_DIR.iterdir() if p.is_dir() and not p.name.startswith(".")]

    # 1. Khớp chính xác tên
    for p in candidates:
        if query_clean in remove_accents(p.name):
            return p

    # 2. Khớp từ khóa cụ thể
    kw_map = {
        "thu06": "8179903",
        "thu.06": "8179903",
        "thu 06": "8179903",
        "bau chau e": "8179906",
        "chau e": "8179906",
        "luong dinh cua": "Lương Định Của",
        "tan hung": "Tân Hưng",
        "quan su": "BCH quân sự",
        "bch": "BCH quân sự",
        "thu74b": "8179905",
        "thu.74b": "8179905",
        "thu01": "8179900",
        "thu.01": "8179900",
    }
    for kw, target in kw_map.items():
        if kw in query_clean:
            for p in candidates:
                if target in p.name:
                    return p

    return None


def cmd_list_projects(args):
    """Liệt kê toàn bộ dự án hiện có trong Second Brain n3n OS."""
    if not BRAINS_DIR.exists():
        print("Chưa tìm thấy thư mục brains của n3n OS.")
        return

    projects = sorted([p for p in BRAINS_DIR.iterdir() if p.is_dir() and not p.name.startswith(".")], key=lambda x: x.name)
    if not projects:
        print("Hiện chưa có dự án nào trong Second Brain n3n OS.")
        return

    print("📋 **DANH SÁCH DỰ ÁN TRÊN N3N OS (SECOND BRAIN):**\n")
    for idx, p in enumerate(projects, 1):
        clean_name = p.name
        # Thống kê nhanh tài liệu
        doc_count = len(list(p.rglob("*.md")))
        sources_count = len(list((p / "sources").glob("*"))) if (p / "sources").exists() else 0
        has_dashboard = "✅" if (p / "00 - Dashboard").exists() else "⚪"
        has_log = "✅" if (p / "01 - Daily Log").exists() else "⚪"

        print(f"{idx}. **{clean_name}**")
        print(f"   - Tài liệu: {doc_count} ghi chú, {sources_count} tệp nguồn")
        print(f"   - Dashboard: {has_dashboard} | Nhật ký: {has_log}")
        print()


def cmd_project_info(args):
    """Xem thông tin chi tiết và tiến độ dự án."""
    brain = find_project_brain(args.project)
    if not brain:
        print(f"❌ Không tìm thấy dự án nào khớp với từ khóa: '{args.project}'.")
        print("💡 Hãy dùng lệnh list-projects để xem danh sách dự án hiện có.")
        return

    print(f"🏗️ **THÔNG TIN DỰ ÁN: {brain.name}**\n")

    # 1. Đọc Dashboard nếu có
    dash_file = brain / "00 - Dashboard" / "Dashboard.md"
    if dash_file.exists():
        try:
            content = dash_file.read_text(encoding="utf-8").strip()
            print("📊 **Dashboard Dự án:**")
            print(content[:600] + ("..." if len(content) > 600 else ""))
            print()
        except Exception:
            pass

    # 2. Đọc Wiki / Index nếu có
    wiki_index = brain / "wiki" / "index.md"
    if wiki_index.exists():
        try:
            wiki_content = wiki_index.read_text(encoding="utf-8").strip()
            print("📖 **Mô tả / Tổng quan (Wiki):**")
            print(wiki_content[:600] + ("..." if len(wiki_content) > 600 else ""))
            print()
        except Exception:
            pass

    # 3. Đọc Nhật ký gần nhất (Daily Log)
    log_dir = brain / "01 - Daily Log"
    if log_dir.exists():
        log_files = sorted([f for f in log_dir.glob("*.md")], reverse=True)
        if log_files:
            latest_log = log_files[0]
            try:
                log_text = latest_log.read_text(encoding="utf-8").strip()
                print(f"📝 **Nhật ký gần nhất ({latest_log.name}):**")
                print(log_text[:500] + ("..." if len(log_text) > 500 else ""))
                print()
            except Exception:
                pass
        else:
            print("📝 **Nhật ký:** Chưa có mục nhật ký nào được ghi.\n")

    # 4. Danh sách tài liệu nguồn trong sources/
    sources_dir = brain / "sources"
    if sources_dir.exists():
        src_files = sorted([f for f in sources_dir.glob("*.md") if not f.name.startswith(".")])
        if src_files:
            print(f"📑 **Hồ sơ tài liệu nguồn ({len(src_files)} tệp):**")
            for sf in src_files[:15]:
                print(f"   • {sf.stem}")
            if len(src_files) > 15:
                print(f"   • ... và {len(src_files) - 15} tài liệu khác.")
            print()

    print(f"📁 Thư mục lưu trữ: `{brain}`")


def cmd_add_log(args):
    """Ghi nhật ký công trình vào dự án."""
    brain = find_project_brain(args.project)
    if not brain:
        print(f"❌ Không tìm thấy dự án nào khớp với từ khóa: '{args.project}'.")
        return

    log_dir = brain / "01 - Daily Log"
    log_dir.mkdir(parents=True, exist_ok=True)

    today_str = datetime.now().strftime("%Y-%m-%d")
    now_time = datetime.now().strftime("%H:%M")
    log_file = log_dir / f"{today_str}.md"

    entry = f"- [{now_time}] {args.text.strip()}\n"

    try:
        if not log_file.exists():
            log_file.write_text(f"# Nhật ký ngày {today_str}\n\n", encoding="utf-8")

        with open(log_file, "a", encoding="utf-8") as f:
            f.write(entry)

        print(f"✅ Đã ghi nhận nhật ký cho dự án **{brain.name}** thành công!")
        print(f"📅 Ngày: {today_str} lúc {now_time}")
        print(f"📝 Nội dung: {args.text.strip()}")
        print(f"📄 Tệp lưu: `{log_file.name}`")
    except Exception as e:
        print(f"❌ Lỗi khi ghi tệp nhật ký: {e}")


def cmd_kanban(args):
    """Xem danh sách thẻ công việc trên bảng Kanban của dự án."""
    if not KANBAN_DB.exists():
        print("❌ Cơ sở dữ liệu Kanban chưa được khởi tạo.")
        return

    conn = sqlite3.connect(KANBAN_DB)
    cursor = conn.cursor()

    query = "SELECT id, brain_root, title, priority, status, created_at FROM tasks"
    params = []

    brain = None
    if args.project:
        brain = find_project_brain(args.project)
        if brain:
            query += " WHERE brain_root LIKE ?"
            params.append(f"%{brain.name}%")

    query += " ORDER BY priority ASC, created_at DESC"
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        proj_hint = f" của dự án '{brain.name}'" if brain else ""
        print(f"ℹ️ Chưa có thẻ công việc nào trên bảng Kanban{proj_hint}.")
        return

    header = f"📌 **BẢNG VIỆC KANBAN ({brain.name if brain else 'TẤT CẢ DỰ ÁN'}):**\n"
    print(header)

    status_map = {
        "triage": "📥 Chờ tiếp nhận",
        "todo": "📋 Cần làm",
        "doing": "⏳ Đang thực hiện",
        "review": "🔍 Đang thẩm định / duyệt",
        "done": "✅ Đã hoàn thành",
        "blocked": "⛔ Bị nghẽn / vướng"
    }

    by_status = {}
    for r in rows:
        st = r[4]
        by_status.setdefault(st, []).append(r)

    for st, tasks in by_status.items():
        st_label = status_map.get(st, f"Trạng thái: {st}")
        print(f"**{st_label}** ({len(tasks)} việc):")
        for t in tasks:
            tid, broot, title, prio, _, cat = t
            prio_stars = "⭐" * max(1, min(5, 6 - prio))
            b_name = Path(broot).name if broot else "Chung"
            print(f"  • [{prio_stars}] **{title}** (Dự án: {b_name})")
        print()


def cmd_add_task(args):
    """Thêm một nhiệm vụ / thẻ việc mới vào Kanban."""
    if not KANBAN_DB.exists():
        print("❌ Cơ sở dữ liệu Kanban chưa được khởi tạo.")
        return

    brain = find_project_brain(args.project)
    brain_root = str(brain) if brain else ""

    import uuid
    import time

    task_id = f"task_{uuid.uuid4().hex[:12]}"
    now = time.time()
    title = args.title.strip()
    norm_title = remove_accents(title)
    priority = int(args.priority) if args.priority else 2

    try:
        conn = sqlite3.connect(KANBAN_DB)
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO tasks (id, brain_root, title, normalized_title, priority, status, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, 'triage', ?, ?)""",
            (task_id, brain_root, title, norm_title, priority, now, now)
        )
        conn.commit()
        conn.close()

        proj_name = brain.name if brain else "Mặc định"
        print(f"✅ Đã tạo thẻ việc mới trên Kanban thành công!")
        print(f"🏷️ Tiêu đề: **{title}**")
        print(f"🏗️ Dự án: **{proj_name}**")
        print(f"⚡ Trạng thái ban đầu: 📥 Chờ tiếp nhận (Triage)")
        print(f"🔑 Task ID: `{task_id}`")
    except Exception as e:
        print(f"❌ Lỗi khi thêm task vào Kanban: {e}")


def cmd_search(args):
    """Tìm kiếm nội dung tài liệu trong Second Brain."""
    if not BRAINS_DIR.exists():
        print("Chưa tìm thấy thư mục brains của n3n OS.")
        return

    query_norm = remove_accents(args.keyword)
    matches = []

    for md_file in BRAINS_DIR.rglob("*.md"):
        if ".git" in md_file.parts:
            continue
        try:
            text = md_file.read_text(encoding="utf-8", errors="ignore")
            if query_norm in remove_accents(text):
                # Tìm trích đoạn
                lines = text.splitlines()
                snippet = ""
                for line in lines:
                    if query_norm in remove_accents(line):
                        snippet = line.strip()
                        break
                proj = md_file.relative_to(BRAINS_DIR).parts[0]
                matches.append((proj, md_file.name, snippet))
        except Exception:
            continue

    if not matches:
        print(f"ℹ️ Không tìm thấy tài liệu nào chứa từ khóa: '{args.keyword}'.")
        return

    print(f"🔍 **KẾT QUẢ TÌM KIẾM TRONG SECOND BRAIN CHO '{args.keyword}':**\n")
    for proj, fname, snippet in matches[:10]:
        print(f"📄 **{fname}** (Dự án: *{proj}*)")
        if snippet:
            print(f"   > \"{snippet[:180]}\"")
        print()


def cmd_ask_ai(args):
    """Gửi câu hỏi trực tiếp sang n3n OS API server."""
    brain = None
    if args.brain:
        b = find_project_brain(args.brain)
        if b:
            brain = b.name

    payload = {
        "message": args.message,
        "brain": brain or "",
    }
    data = urllib.parse.urlencode(payload).encode("utf-8")
    req = urllib.request.Request(f"{N3N_SERVER_URL}/chat", data=data)

    timeout = int(args.timeout) if args.timeout else 25
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            res_json = json.loads(resp.read().decode("utf-8"))
            if res_json.get("ok"):
                print(res_json.get("text", "").strip())
            else:
                print(f"⚠️ n3n OS phản hồi: {res_json.get('text') or res_json.get('error')}")
    except Exception as e:
        # Fallback tự động khi n3n OS AI timeout hoặc đang bận
        print(f"[🧠 n3n OS - Fallback Thông minh]: Máy chủ AI đang bận hoặc phản hồi chậm ({e}).")
        print("Đang tự động chuyển sang chế độ tra cứu dữ liệu Second Brain trực tiếp:")
        if brain:
            class Dummy:
                project = brain
            cmd_project_info(Dummy())
        else:
            class DummySearch:
                keyword = args.message
            cmd_search(DummySearch())


def main():
    parser = argparse.ArgumentParser(description="n3n OS - Hermes Agent Bridge CLI")
    subparsers = parser.add_subparsers(dest="command")

    # 1. list-projects
    p_list = subparsers.add_parser("list-projects", help="Liệt kê danh sách dự án")

    # 2. project-info
    p_info = subparsers.add_parser("project-info", help="Xem chi tiết dự án")
    p_info.add_argument("project", help="Tên hoặc từ khóa dự án")

    # 3. add-log
    p_log = subparsers.add_parser("add-log", help="Ghi nhật ký công trình")
    p_log.add_argument("project", help="Tên dự án")
    p_log.add_argument("text", help="Nội dung nhật ký")

    # 4. kanban
    p_kanban = subparsers.add_parser("kanban", help="Xem bảng việc Kanban")
    p_kanban.add_argument("--project", "-p", default="", help="Lọc theo dự án")

    # 5. add-task
    p_task = subparsers.add_parser("add-task", help="Thêm task mới")
    p_task.add_argument("project", help="Dự án")
    p_task.add_argument("title", help="Tiêu đề việc")
    p_task.add_argument("--priority", default=2, type=int, help="Độ ưu tiên (1 cao nhất, 5 thấp nhất)")

    # 6. search
    p_search = subparsers.add_parser("search", help="Tìm kiếm tài liệu Second Brain")
    p_search.add_argument("keyword", help="Từ khóa tìm kiếm")

    # 7. ask-ai
    p_ask = subparsers.add_parser("ask-ai", help="Hỏi n3n OS qua API")
    p_ask.add_argument("message", help="Nội dung câu hỏi")
    p_ask.add_argument("--brain", "-b", default="", help="Dự án chỉ định")
    p_ask.add_argument("--timeout", "-t", default=25, type=int, help="Thời gian chờ giây")

    args = parser.parse_args()

    if args.command == "list-projects":
        cmd_list_projects(args)
    elif args.command == "project-info":
        cmd_project_info(args)
    elif args.command == "add-log":
        cmd_add_log(args)
    elif args.command == "kanban":
        cmd_kanban(args)
    elif args.command == "add-task":
        cmd_add_task(args)
    elif args.command == "search":
        cmd_search(args)
    elif args.command == "ask-ai":
        cmd_ask_ai(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
