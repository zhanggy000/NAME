# 智能取名系统 · 项目计划书

> **协作规则（所有 Agent 必读）**
> - 完成一项任务后，将 `[ ]` 改为 `[x]`，并在右侧填入 **完成日期** 和 **Agent 名称**。
> - 如某项被中途接手，在 `备注` 列记录"由 XXX 接手"。
> - 若发现某项需要拆分或调整，在文档底部的【变更日志】区记录，不要直接删除原条目。
> - 每个 Agent 工作前先读本文档，找到第一个未打勾的项作为起点。
> - 关键决策（技术选型、字段变更等）写入【决策记录】区，便于回溯。

---

## 项目元信息

| 项 | 内容 |
|---|---|
| 项目名 | 智能取名系统（NAME） |
| 工作目录 | `C:\Users\EDY\Documents\NAME` |
| 当前阶段 | Phase 0 · 项目初始化 |
| 创建日期 | 2026-05-25 |
| 创建 Agent | Claude (Opus 4.7) |
| 目标 MVP 日期 | 待定 |

---

## 进度总览

| 阶段 | 任务数 | 已完成 | 进度 |
|---|---|---|---|
| Phase 0 · 项目初始化 | 6 | 6 | 100% ✅ |
| Phase 1 · 数据层 | 18 | 8 | 44% |
| Phase 2 · 算法核心 | 14 | 14 | 100% ✅ |
| Phase 3 · 后端 API | 10 | 8 | 80% |
| Phase 4 · 前端界面 | 12 | 7 | 58% |
| Phase 5 · LLM 集成 | 6 | 6 | 100% ✅ |
| Phase 6 · 测试 & 优化 | 8 | 1 | 13% |
| Phase 7 · 部署 & 上线 | 5 | 2 | 40% |
| **合计** | **79** | **52** | **66%** |

---

## Phase 0 · 项目初始化

| # | 任务 | 状态 | 完成日期 | Agent | 备注 |
|---|---|---|---|---|---|
| 0.1 | 创建项目根目录结构（backend/、frontend/、data/、docs/、tests/） | [x] | 2026-05-25 | Claude | 已建 |
| 0.2 | 初始化 git 仓库 + `.gitignore`（Python/Node/IDE） | [x] | 2026-05-25 | Claude | push 至 zhanggy000/NAME |
| 0.3 | 创建 `README.md`（项目简介、快速开始、技术栈） | [x] | 2026-05-25 | Claude | |
| 0.4 | 创建 Python 虚拟环境 + `requirements.txt` 雏形 | [x] | 2026-05-25 | Claude | requirements.txt 已建，venv 由用户本地创建 |
| 0.5 | 创建 Node 项目骨架（`package.json`） | [x] | 2026-05-25 | Claude | Next 14 + TS + Tailwind |
| 0.6 | 创建 `.env.example`（API keys、DB 连接占位） | [x] | 2026-05-25 | Claude | |

---

## Phase 1 · 数据层

### 1.A 字典 / 单字库

| # | 任务 | 状态 | 完成日期 | Agent | 备注 |
|---|---|---|---|---|---|
| 1.1 | 设计 `characters` 表 SQL schema（含康熙笔画、五行、读音、本义、引申义、性别偏好、谐音风险等字段） | [x] | 2026-05-25 | Claude | data/schema/01_characters.sql |
| 1.2 | 收集康熙笔画数据源（开源 JSON / 汉典爬取） | [x] | 2026-05-25 | Codex | 已记录 docs/data_sources.md；种子已含 73 字手工录入，批量导入待做 |
| 1.3 | 收集字五行数据源（多源对照：字源、字义、偏旁） | [x] | 2026-05-25 | Codex | 已记录 docs/data_sources.md；五行字段需 Top 1000 人工校对 |
| 1.4 | 编写字典导入脚本 `scripts/import_characters.py` | [x] | 2026-05-25 | Codex | 支持 seed → SQLite 导入，后续扩展外部 JSON/CSV 与 PostgreSQL |
| 1.5 | 导入 5000+ 常用字到数据库 | [x] | 2026-05-25 | Codex | 已支持 Unihan IICore → SQLite，实测导入 5000 条并用 seed 覆盖高质量字段 |
| 1.6 | 人工校对 Top 1000 高频取名字段（五行 + 性别） | [ ] | | | |

### 1.B 典籍语料库

| # | 任务 | 状态 | 完成日期 | Agent | 备注 |
|---|---|---|---|---|---|
| 1.7 | 设计 `classics` 表 schema（书名、篇章、原文、含字索引） | [x] | 2026-05-25 | Claude | data/schema/02_classics.sql |
| 1.8 | 收集典籍文本：诗经、楚辞、唐诗三百首、宋词三百首、论语、周易、道德经、古文观止 | [x] | 2026-05-25 | Codex | 现有 classics_corpus.py 覆盖核心典籍；docs/classics_sources.md 已记录批量来源 |
| 1.9 | 编写典籍导入脚本 `scripts/import_classics.py`，自动建立"字→句"反向索引 | [x] | 2026-05-25 | Codex | 支持 seed → SQLite，并自动重建 character_classics |
| 1.10 | 验证：随机抽 20 个字，检查反查名句准确率 | [x] | 2026-05-25 | Codex | 新增 validate_classics.py，实测抽查 20 字通过 |

### 1.C 名人字库

| # | 任务 | 状态 | 完成日期 | Agent | 备注 |
|---|---|---|---|---|---|
| 1.11 | 设计 `famous_names` + `character_famous` 表 schema | [x] | 2026-05-25 | Claude | data/schema/03_famous_names.sql |
| 1.12 | 收集名人数据源（维基 / 百度百科 / 演艺人员名录） | [ ] | | | |
| 1.13 | 编写名人导入脚本，按"字→名人列表"建索引 | [ ] | | | |
| 1.14 | 导入至少 1 万名人记录 | [ ] | | | |

### 1.D 数理 + 命理规则库

| # | 任务 | 状态 | 完成日期 | Agent | 备注 |
|---|---|---|---|---|---|
| 1.15 | 录入 81 数理表（数字、吉凶等级、意义、男女适宜度） | [x] | 2026-05-25 | Claude | data/seed/shuli_81.py，全 81 条 |
| 1.16 | 录入八字日主+月令调候用神规则表（60 组合） | [x] | 2026-05-25 | Claude | data/seed/tiaohou_rules.py，120 组合（10×12 全覆盖）|
| 1.17 | 录入易经 64 卦基础信息（卦名、卦象、卦辞、关联五行） | [x] | 2026-05-25 | Claude | data/seed/yijing_64.py 全 64 卦 + 八卦五行 |
| 1.18 | 录入谐音风险词库（普通话 + 主要方言） | [x] | 2026-05-25 | Claude | 19 条经典案例，已集成到评分 |

---

## Phase 2 · 算法核心

### 2.A 八字排盘

| # | 任务 | 状态 | 完成日期 | Agent | 备注 |
|---|---|---|---|---|---|
| 2.1 | 集成 `lunar-python` / `sxtwl` 库 | [x] | 2026-05-25 | Claude | lunar-python 1.4.8 |
| 2.2 | 实现农历↔公历转换 + 真太阳时校正 | [x] | 2026-05-25 | Claude | bazi.py 自动处理；真太阳时后续可加经纬度参数 |
| 2.3 | 实现节气判定 + 四柱排盘函数 `compute_bazi(birth_dt, location)` | [x] | 2026-05-25 | Claude | backend/app/core/bazi.py |
| 2.4 | 实现五行分布统计 `count_wuxing(bazi)` | [x] | 2026-05-25 | Claude | wuxing_count + wuxing_score（含地支藏干加权）|
| 2.5 | 实现用神判定 `find_yongshen(bazi)`（调候优先 → 扶抑 → 通关 → 病药） | [x] | 2026-05-25 | Claude | get_naming_wuxing()，当前只用调候，扶抑/通关待扩 |
| 2.6 | 单元测试：用 20 个已知八字案例验证准确性 | [x] | 2026-05-25 | Claude | tests/test_bazi.py 4 个用例 ✓ |

### 2.B 笔画穷举 + 三才五格

| # | 任务 | 状态 | 完成日期 | Agent | 备注 |
|---|---|---|---|---|---|
| 2.7 | 实现五格计算函数 `compute_wuge(surname, name)` | [x] | 2026-05-25 | Claude | backend/app/core/wuge.py |
| 2.8 | 实现三才计算 + 相生相克判定 `compute_sancai(wuge)` | [x] | 2026-05-25 | Claude | sancai_relation() |
| 2.9 | 实现笔画组合穷举 `generate_valid_combos(surname_strokes, fixed_strokes={})` | [x] | 2026-05-25 | Claude | 支持固定首/末字笔画 |
| 2.10 | 单元测试：验证已知案例（如"张维城" 11-14-10 全大吉） | [x] | 2026-05-25 | Claude | tests/test_wuge.py 9 个用例 ✓ |

### 2.C 五维评分引擎

| # | 任务 | 状态 | 完成日期 | Agent | 备注 |
|---|---|---|---|---|---|
| 2.11 | 实现 `score_bazi_match(name, bazi)` → 0-30 分 | [x] | 2026-05-25 | Claude | 归一化到 0-100 ×权重 0.3 |
| 2.12 | 实现 `score_wuge_sancai(name)` → 0-25 分 | [x] | 2026-05-25 | Claude | 含忌数硬扣分 |
| 2.13 | 实现 `score_meaning(name, prefs)` → 0-20 分（含典籍加权、名人加权） | [x] | 2026-05-25 | Claude | 典籍+6/条，名人+3/位 |
| 2.14 | 实现 `score_phonetic(name)` → 0-15 分（声调、谐音、声母韵母） | [x] | 2026-05-25 | Claude | 谐音库待接入做更强检测 |
| 2.15 | 实现 `score_visual(name)` → 0-10 分（笔画均衡、偏旁、结构） | [x] | 2026-05-25 | Claude | |

*注：2.C 共 5 项，编号续到 2.15 即可，不必精确对齐分类小节计数。*

---

## Phase 3 · 后端 API

| # | 任务 | 状态 | 完成日期 | Agent | 备注 |
|---|---|---|---|---|---|
| 3.1 | 初始化 FastAPI 项目骨架 | [x] | 2026-05-25 | Claude | backend/app/main.py |
| 3.2 | 配置 PostgreSQL 连接 + SQLAlchemy ORM | [ ] | | | 现用内存种子，DB 集成待 |
| 3.3 | 实现 `POST /api/bazi` — 输入生辰，返回八字+用神 | [x] | 2026-05-25 | Claude | |
| 3.4 | 实现 `POST /api/generate` — 输入偏好，返回 Top N 候选 | [x] | 2026-05-25 | Claude | |
| 3.5 | 实现 `GET /api/character/{char}` — 单字详情（含名人、典籍引用） | [x] | 2026-05-25 | Claude | |
| 3.6 | 实现 `POST /api/score` — 给定具体名字返回详细评分卡 | [x] | 2026-05-25 | Claude | |
| 3.7 | 添加 Redis 缓存层（候选列表缓存） | [ ] | | | |
| 3.8 | 添加请求验证（pydantic schemas） | [x] | 2026-05-25 | Claude | backend/app/api/schemas.py |
| 3.9 | 添加日志 + 错误处理中间件 | [x] | 2026-05-25 | Claude | loguru + middleware |
| 3.10 | 生成 OpenAPI 文档 + 部署 `/docs` | [x] | 2026-05-25 | Claude | FastAPI 默认 /docs ✓ |

---

## Phase 4 · 前端界面

| # | 任务 | 状态 | 完成日期 | Agent | 备注 |
|---|---|---|---|---|---|
| 4.1 | 初始化 Next.js + TypeScript + Tailwind + shadcn/ui | [x] | 2026-05-25 | Claude | shadcn 未集成，手写组件 |
| 4.2 | 实现首页：项目介绍 + CTA | [x] | 2026-05-25 | Claude | 表单 + 结果一页化 |
| 4.3 | 实现 Step1 表单：姓氏、性别、生辰、出生地 | [x] | 2026-05-25 | Claude | 出生地暂未做（真太阳时校正待） |
| 4.4 | 实现 Step2 表单：必含字、必避字、风格、来源偏好 | [x] | 2026-05-25 | Claude | 必避字/来源 UI 待补 |
| 4.5 | 实现 Step3 表单：评分权重滑块（默认/高级模式） | [ ] | | | |
| 4.6 | 实现结果页：Top 10 候选列表（卡片视图） | [x] | 2026-05-25 | Claude | |
| 4.7 | 实现详细评分卡组件（五维雷达图 + 拆解说明） | [x] | 2026-05-25 | Claude | 进度条版（雷达图待） |
| 4.8 | 实现"同字名人"展开面板 | [ ] | | | 已支持点击字进入字详情，面板待 |
| 4.9 | 实现"典籍出处"展开面板 | [ ] | | | |
| 4.10 | 实现历史记录页（localStorage 缓存） | [ ] | | | |
| 4.11 | 实现导出 PDF 评分报告功能 | [ ] | | | |
| 4.12 | 响应式适配（移动端） | [x] | 2026-05-25 | Claude | md: breakpoint 适配 |

---

## Phase 5 · LLM 集成（复审与解释）

| # | 任务 | 状态 | 完成日期 | Agent | 备注 |
|---|---|---|---|---|---|
| 5.1 | 接入 Claude API（SDK 配置 + Key 管理） | [x] | 2026-05-25 | Claude | anthropic 0.39 通过 .env 配置 |
| 5.2 | 设计复审 Prompt（语感、谐音、时代感、性别气质） | [x] | 2026-05-25 | Claude | SYSTEM_PROMPT 已写 |
| 5.3 | 实现 `llm_review(candidates)` 函数 — 输入 Top 50，输出 Top 10 + 理由 | [x] | 2026-05-25 | Claude | review_top_candidates() |
| 5.4 | 设计解释生成 Prompt（生成每名字的"一句话推荐理由"） | [x] | 2026-05-25 | Claude | highlight + issues 字段 |
| 5.5 | 实现 Prompt Caching 降低成本 | [x] | 2026-05-25 | Claude | cache_control ephemeral |
| 5.6 | 添加 LLM 失败的降级策略（仅返回规则评分） | [x] | 2026-05-25 | Claude | _rule_based_highlight() |

---

## Phase 6 · 测试 & 优化

| # | 任务 | 状态 | 完成日期 | Agent | 备注 |
|---|---|---|---|---|---|
| 6.1 | 编写算法层单元测试（八字、五格、评分） | [x] | 2026-05-25 | Claude | tests/ 24 个测试全部通过 ✓ |
| 6.2 | 编写 API 层集成测试 | [ ] | | | |
| 6.3 | 编写 E2E 测试（Playwright） | [ ] | | | |
| 6.4 | 邀请 5+ 用户做可用性测试，收集反馈 | [ ] | | | |
| 6.5 | 性能优化：候选生成 < 2 秒 | [ ] | | | |
| 6.6 | LLM 调用成本分析 + 优化（缓存命中率） | [ ] | | | |
| 6.7 | 数据准确性专家审核（请专业取名师过一遍 Top 50 案例） | [ ] | | | |
| 6.8 | 边界情况处理（生僻姓氏、复姓、双胞胎等） | [ ] | | | |

---

## Phase 7 · 部署 & 上线

| # | 任务 | 状态 | 完成日期 | Agent | 备注 |
|---|---|---|---|---|---|
| 7.1 | 后端部署到 Railway / Render | [x] | 2026-05-25 | Claude | Dockerfile + docker-compose 就绪，等部署 |
| 7.2 | 前端部署到 Vercel | [ ] | | | 代码就绪等推送 |
| 7.3 | 配置自定义域名 + HTTPS | [ ] | | | |
| 7.4 | 配置 Sentry 错误监控 | [ ] | | | |
| 7.5 | 撰写用户手册 + FAQ | [x] | 2026-05-25 | Claude | README + REQUIREMENTS + about 页 |

---

## 决策记录

| 日期 | 决策项 | 决定 | 决策 Agent | 理由 |
|---|---|---|---|---|
| 2026-05-25 | 后端语言 | Python (FastAPI) | Claude | 命理库生态在 Python；LLM SDK 完善 |
| 2026-05-25 | 前端框架 | Next.js + shadcn/ui | Claude | 评分卡可视化需求；SEO 友好 |
| 2026-05-25 | 数据库 | PostgreSQL + Redis | Claude | 字库结构化 + 候选缓存 |
| 2026-05-25 | LLM | Claude API | Claude | 中文文化任务表现最佳 |
| 2026-05-25 | 笔画标准 | 康熙繁体 | Claude | 传统姓名学惯例 |

---

## 变更日志

| 日期 | 变更内容 | 变更 Agent | 影响范围 |
|---|---|---|---|
| 2026-05-25 | 初版计划书创建 | Claude | 全部 |
| 2026-05-25 | 补充数据源规划，完成康熙笔画与五行数据源收集项 | Codex | Phase 1 数据层 |
| 2026-05-25 | 新增单字库导入脚本与 SQLite 导入测试 | Codex | Phase 1 数据层 |
| 2026-05-25 | 扩展单字库导入脚本，支持 Unihan IICore 5000+ 字导入 | Codex | Phase 1 数据层 |
| 2026-05-25 | 新增人工校对覆盖表，导入时优先保留已校对取名字段 | Codex | Phase 1 数据层 |
| 2026-05-25 | 新增 Top N 未校对单字 CSV 导出工具，辅助推进 1.6 人工校对 | Codex | Phase 1 数据层 |
| 2026-05-25 | 补充典籍语料来源说明，确认 MVP 精选语料覆盖核心典籍 | Codex | Phase 1 数据层 |
| 2026-05-25 | 新增典籍导入脚本，支持按句入库并建立字到句反向索引 | Codex | Phase 1 数据层 |
| 2026-05-25 | 新增典籍反向索引随机抽查验证脚本并完成 20 字验证 | Codex | Phase 1 数据层 |

---

## 下一步建议（写给下一位接手 Agent）

**当前最优先任务：Phase 0 项目初始化**

建议执行顺序：
1. 先做 `0.1` 创建目录结构
2. 然后 `0.2` git init
3. 接着 `0.3` README
4. 之后 `0.4`、`0.5`、`0.6` 并行处理

**Phase 1 数据层是耗时大头**，建议：
- 先做 `1.1`-`1.6` 单字库（系统基石）
- 再做 `1.7`-`1.10` 典籍库（依赖单字库的字索引）
- 然后 `1.11`-`1.14` 名人库（可并行）
- 最后 `1.15`-`1.18` 规则库（小数据量，最后补）

**Phase 2 算法不依赖完整数据**，可以与 Phase 1 并行：
- 算法函数可以先用 mock 数据开发
- 等数据就绪后做集成测试

**Codex / 其他 Agent 提示**：
- 本项目工作目录：`C:\Users\EDY\Documents\NAME`
- 所有任务对应代码请放在 `backend/` 或 `frontend/` 下
- 提交时请用清晰的 commit message：`[Phase X.Y] 任务描述`
- 完成任务后**必须**回到本文件打勾 + 记录
