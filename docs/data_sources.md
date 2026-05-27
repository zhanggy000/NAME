# 数据源规划

本文档记录 NAME 数据层的候选数据源、用途、许可证注意事项与导入策略。原则是先使用许可清晰、可自动化处理的数据源，再对取名高频字段做人工校对。

## 单字库

### 真实名用字频率

| 数据集 | 来源 | 用途 | 许可/风险 | 导入策略 |
|---|---|---|---|---|
| ChinAPIs `given_name_df` | CRAN / ChinAPIs，Chinese Name Database 1930-2008 派生整理 | 2614 个真实中文名用字，含男女频次、年代频次、总体频率、情感/温暖/能力评分 | ChinAPIs 为 MIT 许可；仍需在发布说明中保留来源 | `scripts/fetch_chinapis_given_names.py` 下载 CRAN 包并导出 CSV，`scripts/import_name_char_stats.py` 汇总到 `name_char_stats` |
| Wikidata 名人姓名 | Wikidata / Wikipedia | 名人姓名拆字证据、样例名、知名度权重 | CC BY-SA；需过滤译名、争议人物和非中文姓名 | 仅作为辅助证据，不直接替代人工可取名字库 |

| 数据域 | 首选来源 | 用途 | 许可/风险 | 导入策略 |
|---|---|---|---|---|
| Unicode 编码、基础笔画 | Unicode Unihan Database | `char`、基础笔画、普通话读音参考 | Unicode 数据许可，适合作为基础字段来源 | 下载 Unihan zip，解析 `Unihan_DictionaryLikeData.txt`、`Unihan_Readings.txt` |
| 拼音与释义 | CC-CEDICT | `pinyin`、基础释义、繁简映射辅助 | CC BY-SA 4.0，需保留 attribution；修改再分发需遵循相同许可 | 解析词典行，优先抽取单字条目 |
| 字形结构/部件 | CHISE IDS / cjkvi-ids | `radical`、`structure`、部件五行辅助 | 开源数据，需在导入脚本与文档中保留来源说明 | 后续作为补充源，不作为首版阻塞项 |
| 康熙笔画 | 手工校对表 + Unihan 参考 | `kangxi_strokes` | 不同流派存在差异，取名计算必须人工复核 | Top 1000 取名字单独维护人工校对覆盖表 |
| 五行归属 | 手工校对表 + 偏旁/字义/音韵规则辅助 | `wuxing`、`wuxing_source`、`wuxing_confidence` | 五行没有统一标准，不能完全自动化 | 自动给候选值和置信度，Top 1000 人工确认 |

参考链接：

- Unicode Unihan Database: https://www.unicode.org/charts/unihan.html
- Unicode UAX #38: https://www.unicode.org/reports/tr38/
- CC-CEDICT: https://www.mdbg.net/chinese/dictionary?page=cc-cedict
- CHISE: https://www.chise.org/
- cjkvi-ids: https://github.com/cjkvi/cjkvi-ids

## 典籍语料库

| 数据域 | 首选来源 | 用途 | 许可/风险 | 导入策略 |
|---|---|---|---|---|
| 诗词语料 | chinese-poetry 开源库 | 唐诗、宋词等句子反查 | 需检查仓库许可证并保留来源 | 解析 JSON，建立 `char -> lines` 反向索引 |
| 儒道经典 | 公开整理文本 + 人工校对 | 论语、周易、道德经等 | 版本差异较多，需记录版本 | 首版导入固定篇目，保留书名/篇章/原文 |
| 诗经/楚辞 | 公开整理文本 + 人工校对 | 古典出处权重 | 版本差异较多，需记录版本 | 先导入正文句，再补篇章名 |

参考链接：

- chinese-poetry: https://github.com/chinese-poetry/chinese-poetry

## 名人库

| 数据域 | 首选来源 | 用途 | 许可/风险 | 导入策略 |
|---|---|---|---|---|
| 历史人物 | Wikidata / Wikipedia dump | `famous_names`、时代、类别 | 需遵守 CC BY-SA attribution | 通过 Wikidata ID 做去重，名字拆字建索引 |
| 现代公众人物 | Wikidata / 公开名单 | 名人参照 | 需过滤争议人物与负面实体 | 加 `fame_score`、`risk_tags`，低置信度不参与强推荐 |

## 数据质量规则

1. 自动导入的数据必须带 `data_source`。
2. 康熙笔画、五行、性别偏好必须有置信度或人工校对标记。
3. 取名生成默认只使用 `is_common=true`、`is_rare=false`、`is_taboo=false` 的字。
4. 五行分歧较大的字不直接丢弃，但 `wuxing_confidence < 60` 时应降低排序权重或提示分歧。
5. 任何外部数据源进入发布包前，必须在 README 或数据说明中保留 attribution。

## 首版落地顺序

1. 保留当前 `characters_seed.py` 作为测试夹具。
2. 新增 `scripts/import_characters.py`，把 seed 或 JSON/CSV 导入 SQLite/PostgreSQL。
3. 新增人工校对覆盖文件，优先覆盖 Top 1000 高频取名字。
4. 后端生成逻辑增加 repository 层，先支持 seed 与数据库双数据源。
