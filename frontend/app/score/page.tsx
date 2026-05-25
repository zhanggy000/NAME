"use client";

import { useState } from "react";
import { scoreName } from "@/lib/api";
import { cn, scoreBadgeClass, wuxingColor } from "@/lib/utils";

export default function ScorePage() {
  const [form, setForm] = useState({
    surname: "张",
    given: "维城",
    gender: "男" as "男" | "女",
    date: "2023-01-14",
    time: "11:33",
    is_lunar: false,
  });
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      const [y, m, d] = form.date.split("-").map(Number);
      const [h, mi] = form.time.split(":").map(Number);
      const res = await scoreName({
        surname: form.surname,
        given_chars: form.given.split(""),
        gender: form.gender,
        year: y, month: m, day: d, hour: h, minute: mi,
        is_lunar: form.is_lunar,
      });
      setResult(res);
    } catch (err: any) {
      setError(err.message || "评分失败");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-8">
      <h1 className="font-serif-cn text-3xl font-bold">名字评分</h1>
      <p className="text-stone-500">输入已有的名字 + 孩子生辰，获取详细五维评分卡。</p>

      <form onSubmit={submit} className="grid md:grid-cols-3 gap-4 p-6 rounded-2xl border border-stone-200 dark:border-stone-800">
        <div>
          <label className="block text-sm font-medium mb-2">姓</label>
          <input value={form.surname} onChange={e => setForm({...form, surname: e.target.value})}
            maxLength={2}
            className="w-full px-3 py-2 rounded-lg border border-stone-300 dark:border-stone-700 bg-transparent" />
        </div>
        <div>
          <label className="block text-sm font-medium mb-2">名（不含姓）</label>
          <input value={form.given} onChange={e => setForm({...form, given: e.target.value})}
            maxLength={2}
            className="w-full px-3 py-2 rounded-lg border border-stone-300 dark:border-stone-700 bg-transparent" />
        </div>
        <div>
          <label className="block text-sm font-medium mb-2">性别</label>
          <div className="flex gap-2">
            {(["男","女"] as const).map(g => (
              <button key={g} type="button"
                onClick={() => setForm({...form, gender: g})}
                className={cn("flex-1 py-2 rounded-lg border",
                  form.gender === g
                    ? "border-stone-900 bg-stone-900 text-white dark:border-stone-100 dark:bg-stone-100 dark:text-stone-900"
                    : "border-stone-300 dark:border-stone-700")}>
                {g}
              </button>
            ))}
          </div>
        </div>
        <div>
          <label className="block text-sm font-medium mb-2">出生日期</label>
          <input type="date" value={form.date} onChange={e => setForm({...form, date: e.target.value})}
            className="w-full px-3 py-2 rounded-lg border border-stone-300 dark:border-stone-700 bg-transparent" />
        </div>
        <div>
          <label className="block text-sm font-medium mb-2">出生时间</label>
          <input type="time" value={form.time} onChange={e => setForm({...form, time: e.target.value})}
            className="w-full px-3 py-2 rounded-lg border border-stone-300 dark:border-stone-700 bg-transparent" />
        </div>
        <div className="flex items-end">
          <button type="submit" disabled={loading}
            className="w-full px-6 py-2 rounded-lg bg-stone-900 text-white dark:bg-stone-100 dark:text-stone-900 font-medium disabled:opacity-50">
            {loading ? "评分中…" : "开始评分"}
          </button>
        </div>
      </form>

      {error && (
        <div className="p-4 rounded-lg bg-red-50 dark:bg-red-950/50 text-red-700 dark:text-red-200">
          {error}
        </div>
      )}

      {result && (
        <div className="p-6 rounded-2xl border border-stone-200 dark:border-stone-800">
          <div className="flex items-center justify-between mb-6">
            <span className="font-serif-cn text-3xl font-bold tracking-wider">{result.full_name}</span>
            <span className={cn("px-4 py-2 rounded-lg font-bold text-xl", scoreBadgeClass(result.total_score))}>
              {result.total_score.toFixed(1)}
            </span>
          </div>

          <div className="grid md:grid-cols-3 gap-4 text-sm mb-6 p-4 rounded-lg bg-stone-50 dark:bg-stone-900">
            <div><span className="text-stone-500">八字：</span><span className="font-mono">{result.bazi.bazi_string}</span></div>
            <div><span className="text-stone-500">日主：</span>
              <span className={cn("px-2 py-0.5 rounded", wuxingColor(result.bazi.day_master_wuxing))}>
                {result.bazi.day_master}（{result.bazi.day_master_wuxing}）
              </span>
            </div>
            <div><span className="text-stone-500">用神：</span>
              <span className={cn("px-2 py-0.5 rounded", wuxingColor(result.naming_wuxing.primary))}>
                {result.naming_wuxing.primary}
              </span>
            </div>
          </div>

          <div className="space-y-4">
            {Object.entries(result.scores as Record<string, any>).map(([k, v]) => (
              <div key={k}>
                <div className="flex justify-between mb-2">
                  <span className="font-medium">{v.name}</span>
                  <span className="text-sm text-stone-500">
                    {v.raw_score.toFixed(1)} (×权重 → {v.weighted_score.toFixed(2)})
                  </span>
                </div>
                <div className="h-2 bg-stone-100 dark:bg-stone-800 rounded overflow-hidden mb-2">
                  <div className="h-full bg-stone-900 dark:bg-stone-100"
                    style={{ width: `${v.raw_score}%` }} />
                </div>
                <ul className="text-xs space-y-0.5 ml-2">
                  {v.breakdown.map((b: any, idx: number) => (
                    <li key={idx} className="flex gap-2">
                      <span className="text-stone-500 min-w-20">{b.item}:</span>
                      <span className={b.delta >= 0 ? "text-emerald-600" : "text-red-600"}>
                        {b.delta >= 0 ? "+" : ""}{b.delta}
                      </span>
                      <span className="text-stone-600 dark:text-stone-400">{b.reason}</span>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
