-- ============================================================
-- 典籍语料库 + 字-句反向索引
-- ============================================================

-- 典籍原文表
CREATE TABLE IF NOT EXISTS classics (
    ref_id          SERIAL       PRIMARY KEY,
    book            VARCHAR(50)  NOT NULL,                  -- "诗经"、"楚辞"、"论语" 等
    chapter         VARCHAR(100),                           -- "关雎"、"离骚"、"学而" 等
    section         VARCHAR(50),                            -- 篇章细分（卷X、第X章）
    line_text       TEXT         NOT NULL,                  -- 原文句子
    translation     TEXT,                                   -- 白话翻译（可选）
    annotation      TEXT,                                   -- 注解（可选）
    line_index      INTEGER,                                -- 在该篇章中的位置
    era             VARCHAR(20),                            -- "先秦"/"唐"/"宋" 等
    author          VARCHAR(50),                            -- 作者（如有）
    created_at      TIMESTAMP    DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_classics_book ON classics (book);
CREATE INDEX IF NOT EXISTS idx_classics_book_chapter ON classics (book, chapter);

-- 字-典籍反向索引（多对多）
CREATE TABLE IF NOT EXISTS character_classics (
    char            VARCHAR(4)   NOT NULL,
    ref_id          INTEGER      NOT NULL,
    position        SMALLINT,                               -- 该字在句中的位置
    is_keyword      BOOLEAN      DEFAULT FALSE,             -- 是否为该句的关键字
    PRIMARY KEY (char, ref_id),
    FOREIGN KEY (char) REFERENCES characters(char) ON DELETE CASCADE,
    FOREIGN KEY (ref_id) REFERENCES classics(ref_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_char_classics_char ON character_classics (char);
CREATE INDEX IF NOT EXISTS idx_char_classics_ref ON character_classics (ref_id);

-- ============================================================
-- 设计说明
-- ============================================================
-- classics 表存原文，character_classics 表是反向索引。
-- 导入流程：
--   1. 先把诗经/楚辞等典籍按"句"拆分入 classics 表
--   2. 遍历每句的每个字，写入 character_classics
--   3. 更新 characters.classics_count 冗余字段
-- 查询场景：
--   "查找含「芷」字的所有典籍引用" → JOIN 一次即可
