const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";

type Gender = "男" | "女";
type MustIncludePosition = "first" | "second" | "any";

export interface GenerateNameRequest {
  surname: string;
  gender: Gender;
  year: number;
  month: number;
  day: number;
  hour: number;
  minute: number;
  is_lunar: boolean;
  must_include?: string | null;
  must_include_position?: MustIncludePosition;
  style_prefs?: string[] | null;
  weights?: ScoreWeights | null;
  top_n?: number;
}

export interface ScoreWeights {
  bazi: number;
  wuge: number;
  meaning: number;
  phonetic: number;
  visual: number;
}

export interface DimensionScore {
  name: string;
  raw_score: number;
  weighted_score: number;
  breakdown: Array<{
    item: string;
    delta: number;
    reason: string;
  }>;
}

export interface CandidateName {
  full_name: string;
  surname: string;
  given_chars: string[];
  total_score: number;
  scores: Record<string, DimensionScore>;
  wuge_result: Record<string, unknown>;
  highlight?: string;
}

export interface GenerateNameResponse {
  bazi: {
    bazi_string: string;
    day_master: string;
    day_master_wuxing: string;
    birth_month_zhi?: string;
    month_zhi?: string;
  };
  naming_wuxing: {
    primary: string;
    secondary: string;
    avoid: string[];
    reasoning: string;
  };
  candidates: CandidateName[];
  stats: Record<string, unknown>;
}

export interface ScoreNameRequest {
  surname: string;
  given_chars: string[];
  gender: Gender;
  year: number;
  month: number;
  day: number;
  hour: number;
  minute: number;
  is_lunar: boolean;
  style_prefs?: string[] | null;
  weights?: ScoreWeights | null;
}

async function postJson<T>(path: string, body: unknown): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
  });

  if (!response.ok) {
    const errorBody = await response.json().catch(() => null);
    const detail = errorBody?.detail;
    throw new Error(typeof detail === "string" ? detail : `请求失败：${response.status}`);
  }

  return response.json();
}

export function generateNames(payload: GenerateNameRequest) {
  return postJson<GenerateNameResponse>("/api/generate", payload);
}

export function scoreName(payload: ScoreNameRequest) {
  return postJson("/api/score", payload);
}

export async function getCharacter(ch: string) {
  const response = await fetch(`${API_BASE_URL}/api/character/${encodeURIComponent(ch)}`);

  if (!response.ok) {
    const errorBody = await response.json().catch(() => null);
    const detail = errorBody?.detail;
    throw new Error(typeof detail === "string" ? detail : `查询失败：${response.status}`);
  }

  return response.json();
}
