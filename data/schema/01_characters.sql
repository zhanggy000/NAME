-- ============================================================
-- 单字字典表
-- 取名系统的基石。每条记录代表一个汉字的全维度元数据。
-- ============================================================

CREATE TABLE IF NOT EXISTS characters (
    -- 主键
    char            VARCHAR(4)   PRIMARY KEY,                       -- 汉字本身，如"雯"

    -- 读音
    pinyin          VARCHAR(20)  NOT NULL,                          -- 全拼，如 "wén"
    tone            SMALLINT     NOT NULL CHECK (tone BETWEEN 1 AND 5),  -- 1-4 声 + 5 轻声
    initial         VARCHAR(5),                                     -- 声母 "w"
    final           VARCHAR(10),                                    -- 韵母 "en"

    -- 笔画（取名核心）
    kangxi_strokes      SMALLINT NOT NULL,                          -- 康熙繁体笔画（数理用此）
    simplified_strokes  SMALLINT NOT NULL,                          -- 简体笔画
    traditional_form    VARCHAR(4),                                 -- 繁体写法，如 "雲"

    -- 五行（取名核心）
    wuxing          CHAR(1)      NOT NULL CHECK (wuxing IN ('木','火','土','金','水')),
    wuxing_source   VARCHAR(50),                                    -- 五行依据：字源/字义/偏旁/音
    wuxing_confidence SMALLINT   DEFAULT 80 CHECK (wuxing_confidence BETWEEN 0 AND 100), -- 五行判定置信度

    -- 字形
    radical         VARCHAR(4),                                     -- 偏旁部首 "雨"
    structure       VARCHAR(20),                                    -- 结构：上下/左右/独体/全包围 等

    -- 字义
    meaning_primary    TEXT       NOT NULL,                         -- 本义
    meaning_extended   TEXT,                                        -- 引申义
    meaning_naming     TEXT,                                        -- 取名常用意涵

    -- 取名特征
    gender_pref     VARCHAR(10)  DEFAULT '中性' CHECK (gender_pref IN ('男','女','中性')),
    style_tags      JSONB,                                          -- ["古典","婉约","大气"]

    -- 频次与合规
    freq_rank       INTEGER,                                        -- 现代取名使用频次排名（越小越常用）
    is_common       BOOLEAN      DEFAULT TRUE,                      -- 是否常用字
    is_rare         BOOLEAN      DEFAULT FALSE,                     -- 是否生僻字
    is_taboo        BOOLEAN      DEFAULT FALSE,                     -- 是否取名忌讳字（如"夭""亡"）
    taboo_reason    TEXT,                                           -- 忌讳原因

    -- 谐音风险
    homophone_risk  JSONB,                                          -- [{"word":"...","lang":"普通话","severity":"high"}]

    -- 经典出处（指向 character_classics 关联表）
    classics_count  INTEGER      DEFAULT 0,                         -- 在典籍中出现的次数（冗余字段，便于排序）
    famous_count    INTEGER      DEFAULT 0,                         -- 名人中使用此字的人数（冗余字段）

    -- 元数据
    created_at      TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
    data_source     VARCHAR(100)                                    -- 数据来源标记
);

-- ============================================================
-- 索引
-- ============================================================

-- 按笔画筛选（最高频查询：找特定笔画的字）
CREATE INDEX IF NOT EXISTS idx_char_kangxi ON characters (kangxi_strokes);

-- 按五行筛选（用神匹配）
CREATE INDEX IF NOT EXISTS idx_char_wuxing ON characters (wuxing);

-- 复合：笔画 + 五行（核心查询）
CREATE INDEX IF NOT EXISTS idx_char_strokes_wuxing ON characters (kangxi_strokes, wuxing);

-- 按性别偏好
CREATE INDEX IF NOT EXISTS idx_char_gender ON characters (gender_pref);

-- 按拼音（音律检查）
CREATE INDEX IF NOT EXISTS idx_char_pinyin ON characters (pinyin);

-- 按是否常用（避免生僻字）
CREATE INDEX IF NOT EXISTS idx_char_common ON characters (is_common, is_rare);

-- ============================================================
-- 字段说明
-- ============================================================
--
-- char: 汉字主键，使用 VARCHAR(4) 兼容生僻字与扩展平面汉字
--
-- kangxi_strokes 与 simplified_strokes 分开存储
--   - 数理计算必用 kangxi_strokes (取名学传统)
--   - 现代书写美观参考 simplified_strokes
--
-- wuxing_confidence 用于解决五行判定的流派分歧
--   - 80+ : 主流共识
--   - 60-79: 多数派
--   - <60 : 分歧较大，需在前端展示来源
--
-- style_tags 与 homophone_risk 用 JSONB
--   - PostgreSQL 原生支持 JSON 查询
--   - 标签可扩展不破坏 schema
