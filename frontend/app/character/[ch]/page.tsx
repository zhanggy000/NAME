"use client";

import { useEffect, useState } from "react";
import { getCharacter } from "@/lib/api";
import { wuxingColor, cn } from "@/lib/utils";

export default function CharacterPage({ params }: { params: { ch: string } }) {
  const ch = decodeURIComponent(params.ch);
  const [info, setInfo] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    getCharacter(ch)
      .then(setInfo)
      .catch(e => setError(e.message))
      .finally(() => setLoading(false));
  }, [ch]);

  if (loading) return <p className="text-stone-500">加载中…</p>;
  if (error) return <p className="text-red-600">{error}</p>;
  if (!info) return null;

  return (
    <div className="space-y-8">
      <div className="flex items-start gap-8">
        <div className="font-serif-cn text-9xl font-bold leading-none">{info.char}</div>
        <div className="space-y-3 pt-2">
          <div className="text-2xl text-stone-500">
            {info.pinyin} <span className="text-sm">第{info.tone}声</span>
          </div>
          <div className="flex gap-2 flex-wrap">
            <span className={cn("px-3 py-1 rounded text-sm", wuxingColor(info.wuxing))}>
              {info.wuxing} 行
            </span>
            <span className="px-3 py-1 rounded text-sm bg-stone-100 dark:bg-stone-800">
              康熙 {info.kangxi} 画
            </span>
            <span className="px-3 py-1 rounded text-sm bg-stone-100 dark:bg-stone-800">
              简体 {info.simplified} 画
            </span>
            <span className="px-3 py-1 rounded text-sm bg-stone-100 dark:bg-stone-800">
              部首：{info.radical}
            </span>
            <span className="px-3 py-1 rounded text-sm bg-stone-100 dark:bg-stone-800">
              适用：{info.gender_pref}
            </span>
          </div>
          {info.style_tags?.length > 0 && (
            <div className="flex gap-1 flex-wrap">
              {info.style_tags.map((t: string) => (
                <span key={t} className="px-2 py-0.5 rounded-full bg-stone-50 dark:bg-stone-900 text-xs border border-stone-200 dark:border-stone-700">
                  {t}
                </span>
              ))}
            </div>
          )}
        </div>
      </div>

      <div className="p-5 rounded-xl border border-stone-200 dark:border-stone-800">
        <h2 className="font-semibold mb-2">字义</h2>
        <p>{info.meaning}</p>
      </div>

      {info.classics_refs?.length > 0 && (
        <div className="p-5 rounded-xl border border-stone-200 dark:border-stone-800">
          <h2 className="font-semibold mb-3">典籍出处（{info.classics_refs.length}）</h2>
          <ul className="space-y-2">
            {info.classics_refs.map((r: string, i: number) => (
              <li key={i} className="text-sm leading-relaxed font-serif-cn">
                <span className="text-stone-400 mr-2">•</span>{r}
              </li>
            ))}
          </ul>
        </div>
      )}

      {info.famous_refs?.length > 0 && (
        <div className="p-5 rounded-xl border border-stone-200 dark:border-stone-800">
          <h2 className="font-semibold mb-3">同字名人（{info.famous_refs.length}）</h2>
          <ul className="space-y-2">
            {info.famous_refs.map((r: string, i: number) => (
              <li key={i} className="text-sm">
                <span className="text-stone-400 mr-2">•</span>{r}
              </li>
            ))}
          </ul>
        </div>
      )}

      <a href="/" className="text-sm text-stone-500 hover:text-stone-900 dark:hover:text-stone-100">
        ← 返回首页
      </a>
    </div>
  );
}
