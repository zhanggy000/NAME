# 名人库来源说明

当前 MVP 使用 `data/seed/famous_names_corpus.py` 中的精选名人数据，覆盖古代思想家、政治家、军事家、文学家、现代公众人物与科学家。该 seed 层用于测试和高质量示例，不等同于完整名人库。

## 批量导入候选来源

| 来源 | 覆盖内容 | 用途 | 注意事项 |
|---|---|---|---|
| Wikidata | 历史人物、现代公众人物、职业、年代、性别 | 构建去重后的基础名人库 | 需保留实体 ID 与 attribution |
| Wikipedia dump | 人物简介与知名度辅助 | 补充 brief 与类别 | 需遵守 CC BY-SA |
| 公开人物名单 | 文学家、科学家、运动员等专题 | 提升领域覆盖 | 需要过滤负面人物、争议人物 |
| 当前 seed | 精选高置信示例 | 测试夹具与高质量覆盖 | 保持手工维护 |

## 导入原则

1. 名人记录必须保留 `full_name`、`surname`、`given_name`、`category`、`era`、`gender`。
2. 以 `full_name + era + category` 做基础去重，后续接 Wikidata 后以实体 ID 去重。
3. 建立 `character_famous` 反向索引时只索引名，不索引姓。
4. `fame_score` 只作为排序辅助，不直接代表正面程度。
5. 后续完整库必须加入 `risk_tags` 或黑名单机制，避免负面人物进入强推荐理由。
