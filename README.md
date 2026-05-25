# NAME · 智能取名系统

> 一套综合**中国传统命理 + 文化典籍 + 现代 AI 复审**的取名工具。
> 输入孩子生辰与偏好，输出经五维评分排序的候选名字，每个名字都可解释、可溯源。

## 核心理念

> **八字定方向，字义定气质，五格守底线。**

详见 [REQUIREMENTS.md](REQUIREMENTS.md#六甲取名核心理念重中之重)。

## 演示输出

```
【男宝壬水冬生（2023-01-14）】用神火
排名 名字     总分   八字  五格  字义  音律  字形  亮点
1   张煜明   86.2   100   80   82    82   75   用神补益到位，字义典雅，有典籍出处，有名人参照
2   张晋宁   85.9   100   94   60    82   81   用神补益到位，五格全吉，有典籍出处

【女宝必含雯（2026-05-25）】用神水/火
排名 名字     总分   八字  五格  字义  音律  字形
1   张清雯   84.9   100   79   79    75   81
2   张涵雯   80.9   100   79   59    75   81
```

## 五维评分体系

| 维度 | 权重 | 作用 | 含
|---|---|---|---|
| 八字补益 | 30% | 灵魂 · 决定方向 | 调候用神、五行平衡 |
| 三才五格 | 25% | 避坑 · 决定下限 | 康熙繁体笔画、81 数理 |
| 字义寓意 | 20% | 气质 · 决定格调 | 典籍出处、名人参照 |
| 音律读音 | 15% | 日常 · 决定使用体验 | 声调、谐音、声母韵母 |
| 字形书写 | 10% | 美观 · 决定第一印象 | 笔画均衡、偏旁、结构 |

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

### 一键演示（最快上手）
```bash
pip install -r backend/requirements.txt
python scripts/demo.py
```

### 命令行模式
```bash
# 排八字
python scripts/cli.py bazi 2023-01-14 11:33 --gender 男

# 生成名字 Top 10
python scripts/cli.py gen 张 男 2023-01-14 11:33

# 必含字
python scripts/cli.py gen 张 女 2026-05-25 14:30 --must 雯 --pos second

# 给具体名字评分
python scripts/cli.py score 张 维城 男 2023-01-14 11:33 -v
```

### 后端 + 前端
```bash
# 后端 (http://localhost:8000/docs)
cd backend
python -m venv .venv
.venv\Scripts\activate         # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload

# 前端 (http://localhost:3000)
cd frontend
npm install
npm run dev
```

### Docker 一键启动
```bash
docker-compose up --build
curl http://localhost:8000/health
```

### 运行测试
```bash
pytest                  # 46 个测试 (单测 + API + 语料)
```

## 协作约定

- 任务清单见 [PROJECT_PLAN.md](PROJECT_PLAN.md)
- 完成任务后回到 PLAN 文件打勾 + 填日期 + 填 Agent 名
- 提交信息格式：**中文标题 + 修改内容**
- 重大决策记录到 PLAN 的【决策记录】区

## License

MIT
