#!/usr/bin/env node
/**
 * n3n OS MCP Server - Kết nối Second Brain & Quản lý Dự án n3n OS với Hermes Agent.
 */
import { McpServer } from "../../abs-zalo-bot/node_modules/@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "../../abs-zalo-bot/node_modules/@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "../../abs-zalo-bot/node_modules/zod/lib/index.mjs";
import { execFile } from "node:child_process";
import { promisify } from "node:util";
import path from "node:path";
import { fileURLToPath } from "node:url";

const execFileAsync = promisify(execFile);
const __dirname = path.dirname(fileURLToPath(import.meta.url));
const BRIDGE_PY = path.join(__dirname, "n3n_bridge.py");

const server = new McpServer({
  name: "n3n-os-bridge",
  version: "1.0.0",
});

async function runBridge(args) {
  try {
    const { stdout, stderr } = await execFileAsync("python3", [BRIDGE_PY, ...args], {
      timeout: 30000,
      env: { ...process.env, PYTHONIOENCODING: "utf-8" },
    });
    return {
      content: [{ type: "text", text: stdout.trim() || stderr.trim() || "Thực hiện thành công." }],
    };
  } catch (error) {
    return {
      content: [{ type: "text", text: `Lỗi khi gọi n3n_bridge: ${error.message}\n${error.stdout || ""}` }],
      isError: true,
    };
  }
}

// 1. n3n_list_projects
server.tool(
  "n3n_list_projects",
  "Liệt kê danh sách tất cả các dự án đầu tư xây dựng hiện có trên Second Brain n3n OS.",
  {},
  async () => runBridge(["list-projects"])
);

// 2. n3n_project_info
server.tool(
  "n3n_project_info",
  "Xem chi tiết thông tin, tiến độ, Dashboard, wiki và nhật ký gần nhất của một dự án trên n3n OS (ví dụ 'Đường THU.06', 'Bàu Châu É', 'Lương Định Của', 'Tân Hưng', 'Quân sự'...).",
  {
    project: z.string().describe("Tên hoặc từ khóa viết tắt của dự án (ví dụ 'THU.06', 'Bàu Châu É', 'Lương Định Của')"),
  },
  async ({ project }) => runBridge(["project-info", project])
);

// 3. n3n_add_daily_log
server.tool(
  "n3n_add_daily_log",
  "Ghi nhật ký công trường / tiến độ công việc trong ngày vào dự án tương ứng trên n3n OS.",
  {
    project: z.string().describe("Tên hoặc từ khóa dự án"),
    text: z.string().describe("Nội dung sự việc / công việc / tiến độ cần ghi vào nhật ký"),
  },
  async ({ project, text }) => runBridge(["add-log", project, text])
);

// 4. n3n_kanban_tasks
server.tool(
  "n3n_kanban_tasks",
  "Xem danh sách thẻ công việc trên bảng Kanban của một dự án hoặc toàn bộ hệ thống.",
  {
    project: z.string().optional().describe("Tên dự án cần lọc (để trống để xem tất cả dự án)"),
  },
  async ({ project }) => {
    const args = ["kanban"];
    if (project) args.push("--project", project);
    return runBridge(args);
  }
);

// 5. n3n_add_kanban_task
server.tool(
  "n3n_add_kanban_task",
  "Tạo một thẻ việc (nhiệm vụ) mới trên bảng Kanban n3n OS.",
  {
    project: z.string().describe("Dự án áp dụng"),
    title: z.string().describe("Tiêu đề nhiệm vụ cần làm"),
    priority: z.number().optional().describe("Mức ưu tiên từ 1 (cao nhất) đến 5 (thấp nhất), mặc định là 2"),
  },
  async ({ project, title, priority = 2 }) => {
    return runBridge(["add-task", project, title, "--priority", String(priority)]);
  }
);

// 6. n3n_search_second_brain
server.tool(
  "n3n_search_second_brain",
  "Tìm kiếm văn bản, số quyết định, nhà thầu, nội dung ghi chú trong toàn bộ kho tài liệu Second Brain n3n OS.",
  {
    keyword: z.string().describe("Từ khóa cần tìm kiếm"),
  },
  async ({ keyword }) => runBridge(["search", keyword])
);

// 7. n3n_ask_ai
server.tool(
  "n3n_ask_ai",
  "Gửi câu hỏi tới trí tuệ nhân tạo n3n OS để được giải đáp, suy luận sâu về dự án hoặc tri thức quản lý.",
  {
    message: z.string().describe("Nội dung câu hỏi"),
    project: z.string().optional().describe("Tên dự án chỉ định (nếu có)"),
  },
  async ({ message, project }) => {
    const args = ["ask-ai", message];
    if (project) args.push("--brain", project);
    return runBridge(args);
  }
);

async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
}

main().catch((err) => {
  console.error("Lỗi khởi động n3n OS MCP server:", err);
  process.exit(1);
});
