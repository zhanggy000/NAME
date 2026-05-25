-- ============================================================
-- 名人字库 + 字-名人反向索引
-- ============================================================

CREATE TABLE IF NOT EXISTS famous_names (
    name_id         SERIAL       PRIMARY KEY,
    full_name       VARCHAR(50)  NOT NULL,                  -- "刘诗雯"
    surname         VARCHAR(20),                            -- "刘"
    given_name      VARCHAR(20)  NOT NULL,                  -- "诗雯"
    category        VARCHAR(30),                            -- 演员/作家/科学家/运动员/历史人物/古人/政治家
    sub_category    VARCHAR(50),                            -- 如运动员下的"乒乓球"
    era             VARCHAR(20),                            -- "现代"/"民国"/"清"/"明"/"宋"/"唐"/"先秦"
    birth_year      INTEGER,
    death_year      INTEGER,
    gender          VARCHAR(10)  CHECK (gender IN ('男','女','未知')),
    brief           TEXT,                                   -- 简介
    achievements    TEXT,                                   -- 主要成就
    reference_url   VARCHAR(500),                           -- 维基/百科链接
    fame_score      SMALLINT     DEFAULT 50,                -- 知名度 0-100，用于排序
    source          VARCHAR(100),                           -- 数据来源
    created_at      TIMESTAMP    DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_famous_surname ON famous_names (surname);
CREATE INDEX IF NOT EXISTS idx_famous_category ON famous_names (category);
CREATE INDEX IF NOT EXISTS idx_famous_era ON famous_names (era);
CREATE INDEX IF NOT EXISTS idx_famous_gender ON famous_names (gender);
CREATE INDEX IF NOT EXISTS idx_famous_fame ON famous_names (fame_score DESC);

-- 字-名人反向索引（多对多）
CREATE TABLE IF NOT EXISTS character_famous (
    char            VARCHAR(4)   NOT NULL,
    name_id         INTEGER      NOT NULL,
    position        SMALLINT,                               -- 该字在名（不含姓）中的位置
    PRIMARY KEY (char, name_id),
    FOREIGN KEY (char) REFERENCES characters(char) ON DELETE CASCADE,
    FOREIGN KEY (name_id) REFERENCES famous_names(name_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_char_famous_char ON character_famous (char);
CREATE INDEX IF NOT EXISTS idx_char_famous_name ON character_famous (name_id);

-- ============================================================
-- 字段说明
-- ============================================================
-- fame_score 区间：
--   90-100 : 顶级历史人物（孔子、李白、苏轼）/ 国民级现代名人
--   70-89  : 知名作家、艺术家、科学家
--   50-69  : 普通可查名人
--   <50    : 边缘条目（仅做字源参考）
-- 用于在"查询含某字的名人"时按知名度倒序展示。
