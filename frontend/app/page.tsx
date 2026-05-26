"use client";

import { useEffect, useState } from "react";
import { aiReview, generateNamesStream, getCharacter, type AiReviewResponse, type GenerateNameResponse } from "@/lib/api";
import { wuxingColor, scoreBadgeClass, cn } from "@/lib/utils";

const STYLE_OPTIONS = ["典雅","大气","婉约","清新","古意","稳重","明朗","厚重","君子"];
const WEIGHT_LABELS = {
  bazi: "八字",
  wuge: "五格",
  meaning: "字义",
  phonetic: "音律",
  visual: "字形",
} as const;
const HISTORY_KEY = "name_history";
const MODEL_SETTINGS_KEY = "name_model_settings";
const SCORE_ORDER = ["bazi", "wuge", "meaning", "phonetic", "visual"] as const;
const DEFAULT_TOP_N = 100;

function firstCharacter(value: string) {
  return Array.from(value).slice(0, 1).join("");
}

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
    custom_weights: false,
    weights: {
      bazi: 30,
      wuge: 25,
      meaning: 20,
      phonetic: 15,
      visual: 10,
    },
    top_n: DEFAULT_TOP_N,
    llm: {
      provider: "deepseek" as "deepseek" | "anthropic" | "none",
      enabled: false,
      api_key: "",
      model: "deepseek-v4-flash",
      base_url: "https://api.deepseek.com",
      remember: true,
    },
  });
  const [result, setResult] = useState<GenerateNameResponse | null>(null);
  const [aiReviewByName, setAiReviewByName] = useState<Record<string, AiReviewResponse>>({});
  const [aiReviewLoadingName, setAiReviewLoadingName] = useState<string | null>(null);
  const [liveTrace, setLiveTrace] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [expanded, setExpanded] = useState<string | null>(null);
  const [charDetails, setCharDetails] = useState<Record<string, any>>({});
  const [isMustIncludeComposing, setIsMustIncludeComposing] = useState(false);

  useEffect(() => {
    const raw = localStorage.getItem(MODEL_SETTINGS_KEY);
    if (!raw) return;
    try {
      const saved = JSON.parse(raw);
      setForm(current => ({
        ...current,
        llm: {
          ...current.llm,
          ...saved,
          api_key: saved.api_key ?? "",
          remember: saved.remember ?? true,
        },
      }));
    } catch {
      localStorage.removeItem(MODEL_SETTINGS_KEY);
    }
  }, []);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError("");
    setResult(null);
    setAiReviewByName({});
    setLiveTrace([]);
    try {
      const [y, m, d] = form.date.split("-").map(Number);
      const [h, mi] = form.time.split(":").map(Number);
      const payload = {
        surname: form.surname,
        gender: form.gender,
        year: y, month: m, day: d, hour: h, minute: mi,
        is_lunar: form.is_lunar,
        must_include: form.must_include || null,
        must_include_position: form.must_include_position,
        style_prefs: form.style_prefs.length ? form.style_prefs : null,
        weights: form.custom_weights
          ? {
              bazi: form.weights.bazi / 100,
              wuge: form.weights.wuge / 100,
              meaning: form.weights.meaning / 100,
              phonetic: form.weights.phonetic / 100,
              visual: form.weights.visual / 100,
            }
          : null,
        llm_provider: form.llm.provider,
        llm_enabled: false,
        llm_api_key: null,
        llm_model: null,
        llm_base_url: null,
        top_n: DEFAULT_TOP_N,
      };

      if (form.llm.remember) {
        localStorage.setItem(MODEL_SETTINGS_KEY, JSON.stringify(form.llm));
      } else {
        localStorage.removeItem(MODEL_SETTINGS_KEY);
      }

      await generateNamesStream(payload, {
        onLog: message => {
          setLiveTrace(current => [...current, message]);
        },
        onResult: res => {
          setResult(res);
          if (res.trace?.length) {
            setLiveTrace(res.trace);
          }
          saveHistory({
            id: `${Date.now()}`,
            created_at: new Date().toISOString(),
            surname: form.surname,
            gender: form.gender,
            birth: `${form.date} ${form.time}`,
            must_include: form.must_include || "",
            candidates: res.candidates.slice(0, 5).map(c => ({
              full_name: c.full_name,
              total_score: c.total_score,
            })),
          });
        },
      });
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

  function updateWeight(key: keyof typeof WEIGHT_LABELS, value: number) {
    setForm(f => ({
      ...f,
      weights: {
        ...f.weights,
        [key]: value,
      },
    }));
  }

  async function toggleCandidate(fullName: string, givenChars: string[]) {
    const next = expanded === fullName ? null : fullName;
    setExpanded(next);
    if (!next) return;

    const missing = givenChars.filter(ch => !charDetails[ch]);
    if (!missing.length) return;

    const entries = await Promise.all(
      missing.map(async ch => [ch, await getCharacter(ch)] as const)
    );
    setCharDetails(current => ({
      ...current,
      ...Object.fromEntries(entries),
    }));
  }

  async function runAiReview(candidate: GenerateNameResponse["candidates"][number]) {
    if (!result) return;
    setError("");
    setAiReviewLoadingName(candidate.full_name);
    try {
      if (form.llm.provider === "none") {
        throw new Error("请选择一个 AI 供应商。");
      }
      if (!form.llm.api_key.trim()) {
        throw new Error("要使用 AI 复核，请先填写 API Key。");
      }
      if (form.llm.remember) {
        localStorage.setItem(MODEL_SETTINGS_KEY, JSON.stringify(form.llm));
      } else {
        localStorage.removeItem(MODEL_SETTINGS_KEY);
      }
      const review = await aiReview({
        bazi: result.bazi,
        naming_wuxing: result.naming_wuxing,
        candidates: [candidate],
        llm_provider: form.llm.provider,
        llm_api_key: form.llm.api_key,
        llm_model: form.llm.model,
        llm_base_url: form.llm.base_url,
        max_count: 1,
      });
      setAiReviewByName(current => ({...current, [candidate.full_name]: review}));
      setResult(current => current ? {
        ...current,
        candidates: current.candidates.map(item =>
          item.full_name === candidate.full_name ? review.candidates[0] : item
        ),
      } : current);
    } catch (err: any) {
      setError(err.message || "AI 复核失败");
    } finally {
      setAiReviewLoadingName(null);
    }
  }

  const totalWeight = Object.values(form.weights).reduce((sum, value) => sum + value, 0);
  const traceLines = liveTrace.length ? liveTrace : result?.trace ?? [];

  function saveHistory(entry: any) {
    const raw = localStorage.getItem(HISTORY_KEY);
    const current = raw ? JSON.parse(raw) : [];
    localStorage.setItem(HISTORY_KEY, JSON.stringify([entry, ...current].slice(0, 20)));
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
              onChange={e => {
                const value = e.target.value;
                setForm({
                  ...form,
                  must_include: isMustIncludeComposing ? value : firstCharacter(value),
                });
              }}
              onCompositionStart={() => setIsMustIncludeComposing(true)}
              onCompositionEnd={e => {
                setIsMustIncludeComposing(false);
                setForm({...form, must_include: firstCharacter(e.currentTarget.value)});
              }}
              onBlur={e => setForm({...form, must_include: firstCharacter(e.target.value)})}
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

        <div className="md:col-span-2 border-t border-stone-200 dark:border-stone-800 pt-5">
          <label className="text-sm font-medium flex items-center gap-2">
            <input
              type="checkbox"
              checked={form.custom_weights}
              onChange={e => setForm({...form, custom_weights: e.target.checked})}
            />
            高级权重
            <span className="text-xs text-stone-500 font-normal">
              合计 {totalWeight}%
            </span>
          </label>
          {form.custom_weights && (
            <div className="grid md:grid-cols-5 gap-3 mt-3">
              {(Object.keys(WEIGHT_LABELS) as Array<keyof typeof WEIGHT_LABELS>).map(key => (
                <label key={key} className="space-y-2 text-sm">
                  <span className="flex justify-between">
                    <span>{WEIGHT_LABELS[key]}</span>
                    <span className="text-stone-500">{form.weights[key]}%</span>
                  </span>
                  <input
                    type="range"
                    min={0}
                    max={60}
                    step={5}
                    value={form.weights[key]}
                    onChange={e => updateWeight(key, Number(e.target.value))}
                    className="w-full accent-stone-900 dark:accent-stone-100"
                  />
                </label>
              ))}
            </div>
          )}
        </div>

        <div className="md:col-span-2 border-t border-stone-200 dark:border-stone-800 pt-5">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-2 mb-3">
            <div>
              <div className="text-sm font-medium">AI 复核设置</div>
              <div className="text-xs text-stone-500 mt-1">
                生成名字时不会自动调用 AI；只有点击某个名字旁边的「AI复核」按钮时，才会调用这里配置的模型。
              </div>
            </div>
            <label className="text-xs text-stone-500 flex items-center gap-2">
              <input
                type="checkbox"
                checked={form.llm.remember}
                onChange={e => setForm({...form, llm: {...form.llm, remember: e.target.checked}})}
              />
              保存在本机浏览器
            </label>
          </div>

          <div className="grid md:grid-cols-4 gap-3">
            <label className="space-y-2 text-sm">
              <span className="text-stone-600 dark:text-stone-300">供应商</span>
              <select
                value={form.llm.provider}
                onChange={e => {
                  const provider = e.target.value as "deepseek" | "anthropic" | "none";
                  setForm({
                    ...form,
                    llm: {
                      ...form.llm,
                      provider,
                      model: provider === "deepseek"
                        ? "deepseek-v4-flash"
                        : provider === "anthropic"
                          ? "claude-opus-4-7"
                          : "",
                      base_url: provider === "deepseek"
                        ? "https://api.deepseek.com"
                        : provider === "anthropic"
                          ? "https://api.anthropic.com"
                          : "",
                    },
                  });
                }}
                className="w-full px-3 py-2 rounded-lg border border-stone-300 dark:border-stone-700 bg-transparent"
              >
                <option value="deepseek">DeepSeek</option>
                <option value="anthropic">Anthropic</option>
                <option value="none">关闭 AI 复审</option>
              </select>
            </label>

            <label className="space-y-2 text-sm">
              <span className="text-stone-600 dark:text-stone-300">模型</span>
              <input
                value={form.llm.model}
                onChange={e => setForm({...form, llm: {...form.llm, model: e.target.value}})}
                placeholder="deepseek-v4-flash"
                disabled={form.llm.provider === "none"}
                className="w-full px-3 py-2 rounded-lg border border-stone-300 dark:border-stone-700 bg-transparent disabled:opacity-50"
              />
            </label>

            <label className="space-y-2 text-sm">
              <span className="text-stone-600 dark:text-stone-300">Base URL</span>
              <input
                value={form.llm.base_url}
                onChange={e => setForm({...form, llm: {...form.llm, base_url: e.target.value}})}
                placeholder="https://api.deepseek.com"
                disabled={form.llm.provider === "none"}
                className="w-full px-3 py-2 rounded-lg border border-stone-300 dark:border-stone-700 bg-transparent disabled:opacity-50"
              />
            </label>

            <label className="space-y-2 text-sm">
              <span className="text-stone-600 dark:text-stone-300">API Key</span>
              <input
                type="password"
                value={form.llm.api_key}
                onChange={e => setForm({...form, llm: {...form.llm, api_key: e.target.value}})}
                placeholder="sk-..."
                disabled={form.llm.provider === "none"}
                className="w-full px-3 py-2 rounded-lg border border-stone-300 dark:border-stone-700 bg-transparent disabled:opacity-50"
              />
            </label>
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

      {traceLines.length > 0 && (
        <section className="rounded-xl overflow-hidden border border-stone-800 bg-stone-950 text-stone-100 shadow-sm">
          <div className="flex items-center justify-between border-b border-stone-800 px-4 py-2 bg-stone-900">
            <div className="flex items-center gap-2">
              <span className="h-3 w-3 rounded-full bg-red-500" />
              <span className="h-3 w-3 rounded-full bg-amber-400" />
              <span className="h-3 w-3 rounded-full bg-emerald-500" />
              <span className="ml-2 text-xs font-mono text-stone-400">
                实时运行日志
              </span>
            </div>
            <span className="text-xs font-mono text-stone-500">
              {loading ? "running" : "done"} · {traceLines.length} lines
            </span>
          </div>
          <pre className="max-h-[620px] overflow-auto whitespace-pre-wrap break-words p-4 text-[13px] leading-7 font-mono">
            {traceLines.join("\n")}
          </pre>
        </section>
      )}

      {result && (
        <div className="space-y-8 print:space-y-5">
          <div className="flex justify-end print:hidden">
            <button
              type="button"
              onClick={() => window.print()}
              className="px-4 py-2 rounded-lg border border-stone-300 dark:border-stone-700 text-sm"
            >
              导出 PDF
            </button>
          </div>
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
              {result.candidates.map((c, i) => {
                const review = aiReviewByName[c.full_name];
                const isReviewing = aiReviewLoadingName === c.full_name;
                return (
                <div key={c.full_name}
                  className="p-5 rounded-xl border border-stone-200 dark:border-stone-800 hover:border-stone-400 dark:hover:border-stone-600 transition">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-baseline gap-3">
                      <span className="text-stone-400 font-mono text-sm">#{i+1}</span>
                      <span className="font-serif-cn text-2xl font-bold tracking-wider">
                        {c.full_name}
                      </span>
                      {c.llm_score != null && (
                        <span className="rounded bg-indigo-50 px-2 py-0.5 text-xs font-medium text-indigo-700 dark:bg-indigo-950 dark:text-indigo-200">
                          AI复审 {c.llm_score.toFixed(1)}
                        </span>
                      )}
                      {(review || c.llm_score != null) && c.highlight && (
                        <span className="max-w-md text-xs leading-relaxed text-stone-500">{c.highlight}</span>
                      )}
                    </div>
                    <div className="flex items-center gap-2">
                      <span className={cn("px-2 py-1 rounded font-bold text-sm", scoreBadgeClass(c.total_score))}>
                        {c.total_score.toFixed(1)}
                      </span>
                      <button
                        onClick={() => toggleCandidate(c.full_name, c.given_chars)}
                        className="text-xs px-3 py-1 rounded border border-stone-300 dark:border-stone-700"
                      >
                        {expanded === c.full_name ? "收起" : "评分卡"}
                      </button>
                      <button
                        type="button"
                        onClick={() => runAiReview(c)}
                        disabled={isReviewing}
                        className="text-xs px-3 py-1 rounded border border-indigo-300 bg-indigo-50 text-indigo-700 disabled:opacity-50 dark:border-indigo-800 dark:bg-indigo-950 dark:text-indigo-200"
                      >
                        {isReviewing ? "AI复核中…" : "AI复核"}
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
                  {(review || c.llm_score != null) && (c.llm_score != null || c.highlight || c.issues?.length) && (
                    <div className="mt-3 rounded-lg border border-indigo-100 bg-indigo-50/70 p-3 text-xs leading-relaxed text-indigo-950 dark:border-indigo-900 dark:bg-indigo-950/40 dark:text-indigo-100">
                      <div className="mb-1 font-medium">AI 语感复审</div>
                      <div>
                        {c.llm_score != null ? `复审分：${c.llm_score.toFixed(1)}。` : ""}
                        {c.highlight ? ` 亮点：${c.highlight}。` : ""}
                      </div>
                      {c.issues?.length ? (
                        <div className="mt-1 text-red-700 dark:text-red-300">
                          注意：{c.issues.join("；")}
                        </div>
                      ) : null}
                    </div>
                  )}
                  {review && (
                    <div className="mt-3 space-y-3 rounded-lg border border-stone-200 bg-stone-50 p-3 text-xs dark:border-stone-800 dark:bg-stone-900">
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="font-medium">AI 原始复核记录</span>
                        <span className="text-stone-500">{review.provider} / {review.model}</span>
                      </div>
                      <div>
                        <div className="mb-1 font-medium text-stone-700 dark:text-stone-200">发给 AI 的 Prompt</div>
                        <pre className="max-h-72 overflow-auto whitespace-pre-wrap rounded bg-white p-3 leading-6 text-stone-700 dark:bg-stone-950 dark:text-stone-200">
{`[System]\n${review.prompt.system}\n\n[User]\n${review.prompt.user}`}
                        </pre>
                      </div>
                      <div>
                        <div className="mb-1 font-medium text-stone-700 dark:text-stone-200">AI 原始回复</div>
                        <pre className="max-h-72 overflow-auto whitespace-pre-wrap rounded bg-white p-3 leading-6 text-stone-700 dark:bg-stone-950 dark:text-stone-200">
                          {review.raw_response}
                        </pre>
                      </div>
                    </div>
                  )}
                  {expanded === c.full_name && (
                    <div className="mt-4 pt-4 border-t border-stone-200 dark:border-stone-800 space-y-3">
                      <div className="grid md:grid-cols-2 gap-3 text-xs">
                        <div className="rounded-lg bg-stone-50 dark:bg-stone-900 p-3">
                          <div className="font-medium text-sm mb-2">总分计算</div>
                          <div className="space-y-1">
                            {SCORE_ORDER.map(key => {
                              const v = c.scores[key];
                              return (
                                <div key={key} className="flex justify-between gap-3">
                                  <span className="text-stone-500">{v.name}</span>
                                  <span>{v.raw_score.toFixed(1)} → {v.weighted_score.toFixed(2)}</span>
                                </div>
                              );
                            })}
                            <div className="border-t border-stone-200 dark:border-stone-800 pt-1 mt-1 flex justify-between font-medium">
                              <span>合计</span>
                              <span>{c.total_score.toFixed(2)}</span>
                            </div>
                          </div>
                        </div>
                        <div className="rounded-lg bg-stone-50 dark:bg-stone-900 p-3">
                          <div className="font-medium text-sm mb-2">三才五格</div>
                          <div className="grid grid-cols-5 gap-2 text-center">
                            {[
                              ["天", c.wuge_result.tiange],
                              ["人", c.wuge_result.renge],
                              ["地", c.wuge_result.dige],
                              ["外", c.wuge_result.waige],
                              ["总", c.wuge_result.zongge],
                            ].map(([label, value]) => (
                              <div key={label} className="rounded bg-white dark:bg-stone-950 py-2">
                                <div className="text-stone-500">{label}格</div>
                                <div className="font-mono text-base">{String(value ?? "-")}</div>
                              </div>
                            ))}
                          </div>
                          <div className="mt-2 text-stone-600 dark:text-stone-400">
                            三才：{c.wuge_result.sancai_heaven ?? "-"}-{c.wuge_result.sancai_person ?? "-"}-{c.wuge_result.sancai_earth ?? "-"}
                            <span className="ml-2">判定：{c.wuge_result.sancai_relation?.rating ?? "-"}</span>
                          </div>
                          {c.wuge_result.has_taboo && (
                            <div className="mt-2 text-red-600">
                              忌数：{c.wuge_result.taboo_details?.join("；")}
                            </div>
                          )}
                        </div>
                      </div>
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
                      <div>
                        <div className="font-medium text-sm mb-2">同字名人</div>
                        <div className="grid md:grid-cols-2 gap-3 text-xs">
                          {c.given_chars.map(ch => {
                            const detail = charDetails[ch];
                            return (
                              <div key={ch} className="rounded-lg bg-stone-50 dark:bg-stone-900 p-3">
                                <div className="font-serif-cn text-lg font-bold mb-1">{ch}</div>
                                {detail?.famous_refs?.length ? (
                                  <ul className="space-y-1">
                                    {detail.famous_refs.slice(0, 3).map((ref: string, idx: number) => (
                                      <li key={idx}>{ref}</li>
                                    ))}
                                  </ul>
                                ) : (
                                  <div className="text-stone-500">暂无同字名人</div>
                                )}
                              </div>
                            );
                          })}
                        </div>
                      </div>
                      <div>
                        <div className="font-medium text-sm mb-2">典籍出处</div>
                        <div className="grid md:grid-cols-2 gap-3 text-xs">
                          {c.given_chars.map(ch => {
                            const detail = charDetails[ch];
                            return (
                              <div key={ch} className="rounded-lg bg-stone-50 dark:bg-stone-900 p-3">
                                <div className="font-serif-cn text-lg font-bold mb-1">{ch}</div>
                                {detail?.classics_refs?.length ? (
                                  <ul className="space-y-1 leading-relaxed">
                                    {detail.classics_refs.slice(0, 3).map((ref: string, idx: number) => (
                                      <li key={idx}>{ref}</li>
                                    ))}
                                  </ul>
                                ) : (
                                  <div className="text-stone-500">暂无典籍出处</div>
                                )}
                              </div>
                            );
                          })}
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              );
              })}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
