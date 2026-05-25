"use client";

import { useEffect, useState } from "react";

const HISTORY_KEY = "name_history";

interface HistoryEntry {
  id: string;
  created_at: string;
  surname: string;
  gender: "男" | "女";
  birth: string;
  must_include?: string;
  candidates: Array<{
    full_name: string;
    total_score: number;
  }>;
}

export default function HistoryPage() {
  const [entries, setEntries] = useState<HistoryEntry[]>([]);

  useEffect(() => {
    const raw = localStorage.getItem(HISTORY_KEY);
    setEntries(raw ? JSON.parse(raw) : []);
  }, []);

  function clearHistory() {
    localStorage.removeItem(HISTORY_KEY);
    setEntries([]);
  }

  return (
    <div className="space-y-8">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="font-serif-cn text-3xl font-bold">历史记录</h1>
          <p className="text-stone-500 mt-2">最近 20 次本机生成记录。</p>
        </div>
        {entries.length > 0 && (
          <button
            type="button"
            onClick={clearHistory}
            className="px-3 py-2 rounded-lg border border-stone-300 dark:border-stone-700 text-sm"
          >
            清空
          </button>
        )}
      </div>

      {entries.length === 0 ? (
        <div className="rounded-xl border border-stone-200 dark:border-stone-800 p-6 text-stone-500">
          暂无历史记录
        </div>
      ) : (
        <div className="space-y-4">
          {entries.map(entry => (
            <div key={entry.id} className="rounded-xl border border-stone-200 dark:border-stone-800 p-5">
              <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
                <div>
                  <div className="font-medium">
                    {entry.surname}姓 · {entry.gender} · {entry.birth}
                    {entry.must_include ? ` · 含「${entry.must_include}」` : ""}
                  </div>
                  <div className="text-xs text-stone-500 mt-1">
                    {new Date(entry.created_at).toLocaleString("zh-CN")}
                  </div>
                </div>
              </div>
              <div className="flex flex-wrap gap-2">
                {entry.candidates.map(candidate => (
                  <span key={candidate.full_name} className="px-3 py-1 rounded-lg bg-stone-100 dark:bg-stone-800 text-sm">
                    {candidate.full_name} · {candidate.total_score.toFixed(1)}
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
