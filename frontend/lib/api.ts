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
  llm_provider?: "deepseek" | "anthropic" | "none";
  llm_enabled?: boolean;
  llm_api_key?: string | null;
  llm_model?: string | null;
  llm_base_url?: string | null;
  top_n?: number;
}

export interface AiReviewRequest {
  bazi: GenerateNameResponse["bazi"];
  naming_wuxing: GenerateNameResponse["naming_wuxing"];
  candidates: CandidateName[];
  llm_provider?: "deepseek" | "anthropic" | "none";
  llm_api_key?: string | null;
  llm_model?: string | null;
  llm_base_url?: string | null;
  max_count?: number;
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

export interface WugeResult {
  tiange?: number;
  renge?: number;
  dige?: number;
  waige?: number;
  zongge?: number;
  sancai_heaven?: string;
  sancai_person?: string;
  sancai_earth?: string;
  sancai_relation?: {
    heaven_person?: string;
    person_earth?: string;
    rating?: string;
  };
  all_grids_lucky?: boolean;
  has_taboo?: boolean;
  taboo_details?: string[];
  tiange_info?: Record<string, unknown>;
  renge_info?: Record<string, unknown>;
  dige_info?: Record<string, unknown>;
  waige_info?: Record<string, unknown>;
  zongge_info?: Record<string, unknown>;
}

export interface CandidateName {
  full_name: string;
  surname: string;
  given_chars: string[];
  total_score: number;
  scores: Record<string, DimensionScore>;
  wuge_result: WugeResult;
  highlight?: string;
  llm_score?: number | null;
  issues?: string[];
}

export interface GenerateNameResponse {
  bazi: {
    input_datetime?: string;
    bazi_string: string;
    year_gan?: string;
    year_zhi?: string;
    month_gan?: string;
    month_zhi?: string;
    day_gan?: string;
    day_zhi?: string;
    hour_gan?: string;
    hour_zhi?: string;
    day_master: string;
    day_master_wuxing: string;
    birth_month_zhi?: string;
    month_name?: string;
    wuxing_count?: Record<string, number>;
    wuxing_score?: Record<string, number>;
    tiaohou?: Record<string, unknown>;
  };
  naming_wuxing: {
    primary: string;
    secondary: string;
    avoid: string[];
    reasoning: string;
  };
  candidates: CandidateName[];
  trace: string[];
  stats: {
    pool_size?: number;
    considered?: number;
    valid_wuge?: number;
    unique?: number;
    returned?: number;
    [key: string]: unknown;
  };
}

export interface AiReviewResponse {
  provider: string;
  model: string;
  prompt: {
    system: string;
    user: string;
  };
  raw_response: string;
  reviews: unknown[];
  candidates: CandidateName[];
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

type GenerateStreamHandlers = {
  onLog?: (message: string) => void;
  onResult?: (result: GenerateNameResponse) => void;
};

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

export function aiReview(payload: AiReviewRequest) {
  return postJson<AiReviewResponse>("/api/ai-review", payload);
}

export async function generateNamesStream(
  payload: GenerateNameRequest,
  handlers: GenerateStreamHandlers = {},
) {
  const response = await fetch(`${API_BASE_URL}/api/generate/stream`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Accept": "text/event-stream",
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok || !response.body) {
    const errorBody = await response.json().catch(() => null);
    const detail = errorBody?.detail;
    throw new Error(typeof detail === "string" ? detail : `请求失败：${response.status}`);
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder("utf-8");
  let buffer = "";

  function handleChunk(chunk: string) {
    buffer += chunk;
    const blocks = buffer.split("\n\n");
    buffer = blocks.pop() ?? "";

    for (const block of blocks) {
      let event = "message";
      const dataLines: string[] = [];
      for (const line of block.split("\n")) {
        if (line.startsWith("event:")) {
          event = line.slice("event:".length).trim();
        } else if (line.startsWith("data:")) {
          dataLines.push(line.slice("data:".length).trimStart());
        }
      }

      if (!dataLines.length) continue;
      const data = JSON.parse(dataLines.join("\n"));
      if (event === "log") {
        handlers.onLog?.(data.message);
      } else if (event === "result") {
        handlers.onResult?.(data as GenerateNameResponse);
      } else if (event === "error") {
        throw new Error(data.message || "生成失败");
      }
    }
  }

  while (true) {
    const { value, done } = await reader.read();
    if (value) {
      handleChunk(decoder.decode(value, { stream: !done }));
    }
    if (done) {
      handleChunk(decoder.decode());
      break;
    }
  }
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
