-- ============================================================
-- 命理规则库：81 数理、八字用神规则、易经卦象、谐音风险词库
-- ============================================================

-- ------------------------------------------------------------
-- 81 数理表（熊崎健翁姓名学）
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS shuli_81 (
    number          SMALLINT     PRIMARY KEY CHECK (number BETWEEN 1 AND 81),
    level           VARCHAR(10)  NOT NULL CHECK (level IN ('大吉','吉','半吉','凶','大凶')),
    meaning         VARCHAR(50)  NOT NULL,                  -- "明月中天"
    description     TEXT         NOT NULL,                  -- 详细说明
    male_pref       SMALLINT     DEFAULT 5 CHECK (male_pref BETWEEN 0 AND 10),    -- 男命适宜度
    female_pref     SMALLINT     DEFAULT 5 CHECK (female_pref BETWEEN 0 AND 10),  -- 女命适宜度
    wuxing          CHAR(1)      CHECK (wuxing IN ('木','火','土','金','水'))     -- 数理对应五行（末位个位数）
);

-- ------------------------------------------------------------
-- 八字日主+月令调候用神规则
-- 共 10 天干 × 12 月支 = 120 组合
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS bazi_tiaohou_rules (
    rule_id         SERIAL       PRIMARY KEY,
    day_master      CHAR(1)      NOT NULL,                  -- "甲"乙丙丁戊己庚辛壬癸
    birth_month     CHAR(1)      NOT NULL,                  -- 月支地支 "子丑寅..."
    primary_yongshen   VARCHAR(20),                         -- 主用神，如 "丙"
    secondary_yongshen VARCHAR(20),                         -- 次用神
    primary_wuxing  CHAR(1)      CHECK (primary_wuxing IN ('木','火','土','金','水')),
    secondary_wuxing CHAR(1)     CHECK (secondary_wuxing IN ('木','火','土','金','水')),
    avoid_wuxing    VARCHAR(20),                            -- 忌神五行，如 "水"
    explanation     TEXT,                                   -- 取用理由（取自《穷通宝鉴》等）
    UNIQUE (day_master, birth_month)
);

CREATE INDEX IF NOT EXISTS idx_tiaohou_lookup ON bazi_tiaohou_rules (day_master, birth_month);

-- ------------------------------------------------------------
-- 易经 64 卦基础信息
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS yijing_gua (
    gua_number      SMALLINT     PRIMARY KEY CHECK (gua_number BETWEEN 1 AND 64),
    gua_name        VARCHAR(10)  NOT NULL,                  -- "乾"
    upper_trigram   VARCHAR(10)  NOT NULL,                  -- 上卦 "乾"
    lower_trigram   VARCHAR(10)  NOT NULL,                  -- 下卦 "乾"
    gua_xiang       TEXT,                                   -- 卦象描述
    gua_ci          TEXT,                                   -- 卦辞
    judgement       VARCHAR(50),                            -- 元亨利贞 等
    wuxing_attr     CHAR(1)      CHECK (wuxing_attr IN ('木','火','土','金','水')),
    auspicious      VARCHAR(20),                            -- "大吉"/"吉"/"平"/"凶"
    recommended_chars JSONB                                 -- 契合本卦意象的字 ["健","乾","元"]
);

-- ------------------------------------------------------------
-- 谐音风险词库
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS homophone_risks (
    risk_id         SERIAL       PRIMARY KEY,
    char_or_word    VARCHAR(20)  NOT NULL,                  -- 触发谐音的字或词组
    sounds_like     VARCHAR(50)  NOT NULL,                  -- 易被听成什么
    language        VARCHAR(20)  DEFAULT '普通话',          -- 普通话/粤语/吴语/闽南/川渝
    severity        VARCHAR(10)  CHECK (severity IN ('low','medium','high')),
    category        VARCHAR(20),                            -- 不雅/负面/搞笑/政治敏感
    explanation     TEXT
);

CREATE INDEX IF NOT EXISTS idx_homophone_char ON homophone_risks (char_or_word);
CREATE INDEX IF NOT EXISTS idx_homophone_lang ON homophone_risks (language);

-- ============================================================
-- 数据规模预期
-- ============================================================
-- shuli_81           : 81 行（固定）
-- bazi_tiaohou_rules : ~120 行（10 天干 × 12 月支）
-- yijing_gua         : 64 行（固定）
-- homophone_risks    : 数百～数千行（持续收集）
