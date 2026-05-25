import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function wuxingColor(wuxing: string) {
  const colorMap: Record<string, string> = {
    木: "bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-200",
    火: "bg-red-100 text-red-800 dark:bg-red-950 dark:text-red-200",
    土: "bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-200",
    金: "bg-zinc-100 text-zinc-800 dark:bg-zinc-800 dark:text-zinc-100",
    水: "bg-sky-100 text-sky-800 dark:bg-sky-950 dark:text-sky-200",
  };

  return colorMap[wuxing] ?? "bg-stone-100 text-stone-800 dark:bg-stone-800 dark:text-stone-100";
}

export function scoreBadgeClass(score: number) {
  if (score >= 85) {
    return "bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-200";
  }

  if (score >= 75) {
    return "bg-sky-100 text-sky-800 dark:bg-sky-950 dark:text-sky-200";
  }

  if (score >= 60) {
    return "bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-200";
  }

  return "bg-red-100 text-red-800 dark:bg-red-950 dark:text-red-200";
}
