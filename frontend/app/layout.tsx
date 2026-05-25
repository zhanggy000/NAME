import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "NAME · 智能取名系统",
  description: "综合八字命理 + 文化典籍 + AI 复审的取名工具",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="zh-CN">
      <body>
        <div className="min-h-screen">
          <header className="border-b border-stone-200 dark:border-stone-800">
            <div className="max-w-5xl mx-auto px-6 py-4 flex items-center justify-between">
              <a href="/" className="font-serif-cn text-2xl font-bold tracking-wider">
                名 · NAME
              </a>
              <nav className="text-sm text-stone-500 space-x-6">
                <a href="/" className="hover:text-stone-900 dark:hover:text-stone-100">取名</a>
                <a href="/score" className="hover:text-stone-900 dark:hover:text-stone-100">评分</a>
                <a href="/about" className="hover:text-stone-900 dark:hover:text-stone-100">关于</a>
              </nav>
            </div>
          </header>
          <main className="max-w-5xl mx-auto px-6 py-10">{children}</main>
          <footer className="border-t border-stone-200 dark:border-stone-800 mt-20">
            <div className="max-w-5xl mx-auto px-6 py-6 text-xs text-stone-500">
              八字定方向，字义定气质，五格守底线。
              <span className="float-right">
                <a href="https://github.com/zhanggy000/NAME" className="underline">
                  GitHub
                </a>
              </span>
            </div>
          </footer>
        </div>
      </body>
    </html>
  );
}
