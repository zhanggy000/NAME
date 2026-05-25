# NAME · 智能取名系统

> 一套综合**中国传统命理 + 文化典籍 + 现代 AI 复审**的取名工具。
> 输入孩子生辰与偏好，输出经五维评分排序的候选名字，每个名字都可解释、可溯源。

## 核心理念

> **八字定方向，字义定气质，五格守底线。**

详见 [REQUIREMENTS.md](REQUIREMENTS.md#六甲取名核心理念重中之重)。

## 技术栈

| 层 | 选型 |
|---|---|
| 后端 | Python 3.11 + FastAPI + SQLAlchemy |
| 前端 | Next.js 14 + TypeScript + Tailwind + shadcn/ui |
| 数据库 | PostgreSQL + Redis |
| LLM | Claude API (Anthropic) |
| 命理库 | lunar-python / sxtwl |

## 项目结构

```
NAME/
├── backend/          # FastAPI 后端
│   └── app/
│       ├── api/      # 路由层
│       ├── core/     # 核心算法（八字、五格、评分）
│       ├── models/   # SQLAlchemy 模型
│       ├── services/ # 业务逻辑
│       └── db/       # 数据库连接
├── frontend/         # Next.js 前端
├── data/             # 数据资源
│   ├── raw/          # 原始爬取数据（不入库）
│   ├── seed/         # 入库种子数据
│   └── schema/       # SQL 建表脚本
├── docs/             # 设计文档
├── scripts/          # 工具脚本（数据导入等）
└── tests/            # 测试
```

## 快速开始

```bash
# 后端
cd backend
python -m venv .venv
.venv\Scripts\activate         # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload

# 前端
cd frontend
npm install
npm run dev
```

## 协作约定

- 任务清单见 [PROJECT_PLAN.md](PROJECT_PLAN.md)
- 完成任务后回到 PLAN 文件打勾 + 填日期 + 填 Agent 名
- 提交信息格式：**中文标题 + 修改内容**
- 重大决策记录到 PLAN 的【决策记录】区

## License

MIT
