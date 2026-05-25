# NAME · 前端

Next.js 14 + TypeScript + Tailwind CSS

## 开发

```bash
cd frontend
npm install
npm run dev
```

后端 API 默认指向 `http://localhost:8000`，可通过环境变量 `NEXT_PUBLIC_API_BASE_URL` 覆盖。

启动后端：
```bash
cd ../backend
uvicorn app.main:app --reload
```

## 页面

- `/` — 取名主表单 + Top N 结果
- `/score` — 单名字详细评分
- `/about` — 项目说明

## 技术栈

- Next.js 14 (App Router)
- React 18
- TypeScript
- Tailwind CSS 3.4
- lucide-react 图标
