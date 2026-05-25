# LLM 成本与降级策略

当前 LLM 只用于候选名字复审和一句话推荐理由，不参与八字、五格、字义等核心评分。没有 `ANTHROPIC_API_KEY` 时系统会自动降级为规则版摘要，主流程不受影响。

## 当前调用边界

- 入口：`backend/app/services/llm_review.py`
- 调用函数：`review_top_candidates(candidates, bazi, naming_wuxing, max_count=10)`
- 默认只复审 Top N 候选，避免把全部枚举候选发送给模型。
- System Prompt 已使用 Anthropic Prompt Caching 标记。
- `/api/generate` 外层已接入 Redis 缓存，命中时不会再次触发 LLM 复审。

## 成本控制策略

1. 先规则排序，LLM 只看 Top 10。
2. Prompt Caching 缓存固定系统提示。
3. Redis 缓存完整生成结果，按请求参数生成稳定 cache key。
4. LLM 异常或无 key 时降级为规则版 highlight。
5. 后续可增加 `ENABLE_LLM_REVIEW=false` 开关，用于测试和低成本部署。

## 建议监控指标

| 指标 | 目的 |
|---|---|
| `llm_review.calls` | 统计真实调用次数 |
| `llm_review.failures` | 观察降级频率 |
| `llm_review.latency_ms` | 衡量复审耗时 |
| `llm_review.input_tokens` / `output_tokens` | 估算成本 |
| `generate.cache.hit` / `miss` | 衡量 Redis 缓存收益 |

## 下一步优化

1. 在 LLM 返回中记录 token usage 到结构化日志。
2. 为 `review_top_candidates` 增加显式开关，允许完全跳过 LLM。
3. 将候选简表进一步压缩，只传必要评分和风险字段。
4. 对同一八字与偏好组合预热缓存。
