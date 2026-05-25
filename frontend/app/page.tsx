"use client";

import { useState } from "react";
import { generateNames, type GenerateNameResponse } from "@/lib/api";
import { wuxingColor, scoreBadgeClass, cn } from "@/lib/utils";

const STYLE_OPTIONS = ["典雅","大气","婉约","清新","古意","稳重","明朗","厚重","君子"];

export default function HomePage() {
  const [form, setForm] = useState({
    surname: "张",
    gender: "男" as "男" | "女",
    date: "2023-01-14",
    time: "11:33",
    is_lunar: false,
    must_include: "",
    must_include_position: "any" as "first"|"second"|"any",
    style_prefs: [] as string[],
    top_n: 10,
  });
  const [result, setResult] = useState<GenerateNameResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [expanded, setExpanded] = useState<string | null>(null);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError("");
    setResult(null);
    try {
      const [y, m, d] = form.date.split("-").map(Number);
      const [h, mi] = form.time.split(":").map(Number);
      const res = await generateNames({
        surname: form.surname,
        gender: form.gender,
        year: y, month: m, day: d, hour: h, minute: mi,
        is_lunar: form.is_lunar,
        must_include: form.must_include || null,
        must_include_position: form.must_include_position,
        style_prefs: form.style_prefs.length ? form.style_prefs : null,
        top_n: form.top_n,
      });
      setResult(res);
    } catch (err: any) {
      setError(err.message || "生成失败");
    } finally {
      setLoading(false);
    }
  }

  function toggleStyle(s: string) {
    setForm(f => ({
      ...f,
      style_prefs: f.style_prefs.includes(s)
        ? f.style_prefs.filter(x => x !== s)
        : [...f.style_prefs, s],
    }));
  }

  return (
    <div className="space-y-10">
      <div>
        <h1 className="font-serif-cn text-3xl md:text-4xl font-bold mb-3">
          为孩子起一个有据可循的名字
        </h1>
        <p className="text-stone-500 leading-relaxed">
          基于八字调候用神 · 三才五格 · 典籍出处 · 名人参照 · AI 复审 — 五维评分排序。
          每个推荐都可解释，每个字都有来历。
        </p>
      </div>

      <form onSubmit={submit} className="grid md:grid-cols-2 gap-6 p-6 rounded-2xl border border-stone-200 dark:border-stone-800 bg-white dark:bg-stone-900">
        <div>
          <label className="block text-sm font-medium mb-2">姓氏</label>
          <input
            type="text"
            value={form.surname}
            onChange={e => setForm({...form, surname: e.target.value})}
            maxLength={2}
            required
            className="w-full px-3 py-2 rounded-lg border border-stone-300 dark:border-stone-700 bg-transparent"
          />
        </div>
        <div>
          <label className="block text-sm font-medium mb-2">性别</label>
          <div className="flex gap-2">
            {(["男","女"] as const).map(g => (
              <button
                key={g}
                type="button"
                onClick={() => setForm({...form, gender: g})}
                className={cn(
                  "flex-1 py-2 rounded-lg border",
                  form.gender === g
                    ? "border-stone-900 bg-stone-900 text-white dark:border-stone-100 dark:bg-stone-100 dark:text-stone-900"
                    : "border-stone-300 dark:border-stone-700"
                )}
              >{g}</button>
            ))}
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium mb-2">出生日期</label>
          <input
            type="date"
            value={form.date}
            onChange={e => setForm({...form, date: e.target.value})}
            required
            className="w-full px-3 py-2 rounded-lg border border-stone-300 dark:border-stone-700 bg-transparent"
          />
          <label className="text-xs text-stone-500 flex items-center gap-2 mt-2">
            <input
              type="checkbox"
              checked={form.is_lunar}
              onChange={e => setForm({...form, is_lunar: e.target.checked})}
            />
            农历
          </label>
        </div>
        <div>
          <label className="block text-sm font-medium mb-2">出生时间</label>
          <input
            type="time"
            value={form.time}
            onChange={e => setForm({...form, time: e.target.value})}
            required
            className="w-full px-3 py-2 rounded-lg border border-stone-300 dark:border-stone-700 bg-transparent"
          />
        </div>

        <div className="md:col-span-2">
          <label className="block text-sm font-medium mb-2">
            必含字（可选）
            <span className="text-xs text-stone-500 font-normal ml-2">如希望名字含某个特定字</span>
          </label>
          <div className="flex gap-3">
            <input
              type="text"
              value={form.must_include}
              onChange={e => setForm({...form, must_include: e.target.value.slice(0,1)})}
              maxLength={1}
              placeholder="如：雯"
              className="w-24 px-3 py-2 rounded-lg border border-stone-300 dark:border-stone-700 bg-transparent text-center text-xl"
            />
            <select
              value={form.must_include_position}
              onChange={e => setForm({...form, must_include_position: e.target.value as any})}
              className="px-3 py-2 rounded-lg border border-stone-300 dark:border-stone-700 bg-transparent"
            >
              <option value="any">位置不限</option>
              <option value="first">首字</option>
              <option value="second">末字</option>
            </select>
          </div>
        </div>

        <div className="md:col-span-2">
          <label className="block text-sm font-medium mb-2">风格偏好（可多选）</label>
          <div className="flex flex-wrap gap-2">
            {STYLE_OPTIONS.map(s => (
              <button
                key={s}
                type="button"
                onClick={() => toggleStyle(s)}
                className={cn(
                  "px-3 py-1 rounded-full text-sm border",
                  form.style_prefs.includes(s)
                    ? "border-stone-900 bg-stone-900 text-white dark:border-stone-100 dark:bg-stone-100 dark:text-stone-900"
                    : "border-stone-300 dark:border-stone-700"
                )}
              >{s}</button>
            ))}
          </div>
        </div>

        <div className="md:col-span-2 flex justify-end">
          <button
            type="submit"
            disabled={loading}
            className="px-8 py-3 rounded-xl bg-stone-900 text-white dark:bg-stone-100 dark:text-stone-900 font-medium disabled:opacity-50"
          >
            {loading ? "正在排盘生成…" : "开始生成"}
          </button>
        </div>
      </form>

      {error && (
        <div className="p-4 rounded-lg bg-red-50 dark:bg-red-950/50 text-red-700 dark:text-red-200">
          {error}
        </div>
      )}

      {result && (
        <div className="space-y-8">
          {/* 八字概况 */}
          <div className="p-6 rounded-2xl border border-stone-200 dark:border-stone-800">
            <h2 className="font-serif-cn text-xl font-semibold mb-4">命盘速览</h2>
            <div className="grid md:grid-cols-3 gap-4 text-sm">
              <div>
                <div className="text-stone-500 mb-1">四柱八字</div>
                <div className="font-mono text-lg">{result.bazi.bazi_string}</div>
              </div>
              <div>
                <div className="text-stone-500 mb-1">日主 / 月令</div>
                <div>
                  <span className={cn("px-2 py-0.5 rounded", wuxingColor(result.bazi.day_master_wuxing))}>
                    {result.bazi.day_master}（{result.bazi.day_master_wuxing}）
                  </span>
                  <span className="ml-2 text-stone-500">生于 {result.bazi.birth_month_zhi} 月</span>
                </div>
              </div>
              <div>
                <div className="text-stone-500 mb-1">取名用神</div>
                <div>
                  <span className={cn("px-2 py-0.5 rounded font-bold", wuxingColor(result.naming_wuxing.primary))}>
                    {result.naming_wuxing.primary}
                  </span>
                  <span className="text-stone-400 mx-1">/</span>
                  <span className={cn("px-2 py-0.5 rounded", wuxingColor(result.naming_wuxing.secondary))}>
                    {result.naming_wuxing.secondary}
                  </span>
                  {result.naming_wuxing.avoid.length > 0 && (
                    <span className="ml-3 text-xs text-red-600">
                      忌：{result.naming_wuxing.avoid.join(",")}
                    </span>
                  )}
                </div>
              </div>
            </div>
            <p className="mt-3 text-xs text-stone-500 leading-relaxed">
              {result.naming_wuxing.reasoning}
            </p>
          </div>

          {/* Top N */}
          <div>
            <h2 className="font-serif-cn text-xl font-semibold mb-4">
              Top {result.candidates.length} 候选
            </h2>
            <div className="space-y-3">
              {result.candidates.map((c, i) => (
                <div key={c.full_name}
                  className="p-5 rounded-xl border border-stone-200 dark:border-stone-800 hover:border-stone-400 dark:hover:border-stone-600 transition">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-baseline gap-3">
                      <span className="text-stone-400 font-mono text-sm">#{i+1}</span>
                      <span className="font-serif-cn text-2xl font-bold tracking-wider">
                        {c.full_name}
                      </span>
                      {c.highlight && (
                        <span className="text-xs text-stone-500">{c.highlight}</span>
                      )}
                    </div>
                    <div className="flex items-center gap-2">
                      <span className={cn("px-2 py-1 rounded font-bold text-sm", scoreBadgeClass(c.total_score))}>
                        {c.total_score.toFixed(1)}
                      </span>
                      <button
                        onClick={() => setExpanded(expanded === c.full_name ? null : c.full_name)}
                        className="text-xs px-3 py-1 rounded border border-stone-300 dark:border-stone-700"
                      >
                        {expanded === c.full_name ? "收起" : "评分卡"}
                      </button>
                    </div>
                  </div>
                  <div className="flex gap-1 text-xs">
                    {Object.entries(c.scores).map(([k, v]) => (
                      <span key={k} className="px-2 py-0.5 rounded bg-stone-100 dark:bg-stone-800">
                        {v.name} {v.raw_score.toFixed(0)}
                      </span>
                    ))}
                  </div>
                  {expanded === c.full_name && (
                    <div className="mt-4 pt-4 border-t border-stone-200 dark:border-stone-800 space-y-3">
                      {Object.entries(c.scores).map(([k, v]) => (
                        <div key={k}>
                          <div className="flex justify-between mb-1">
                            <span className="font-medium text-sm">{v.name}</span>
                            <span className="text-xs text-stone-500">
                              {v.raw_score.toFixed(1)} × 权重 = {v.weighted_score.toFixed(2)}
                            </span>
                          </div>
                          <ul className="text-xs space-y-0.5 ml-4">
                            {v.breakdown.map((b, idx) => (
                              <li key={idx} className="flex gap-2">
                                <span className="text-stone-500">{b.item}:</span>
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
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
