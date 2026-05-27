-- ============================================================
-- Given-name character statistics
-- ============================================================

CREATE TABLE IF NOT EXISTS name_char_stats (
    char                  VARCHAR(4)   PRIMARY KEY,
    total_count           INTEGER      NOT NULL DEFAULT 0,
    distinct_name_count   INTEGER      NOT NULL DEFAULT 0,
    male_count            INTEGER      NOT NULL DEFAULT 0,
    female_count          INTEGER      NOT NULL DEFAULT 0,
    unknown_gender_count  INTEGER      NOT NULL DEFAULT 0,
    position_1_count      INTEGER      NOT NULL DEFAULT 0,
    position_2_count      INTEGER      NOT NULL DEFAULT 0,
    position_other_count  INTEGER      NOT NULL DEFAULT 0,
    weighted_fame         INTEGER      NOT NULL DEFAULT 0,
    source_count          INTEGER      NOT NULL DEFAULT 0,
    sources               TEXT         NOT NULL DEFAULT '[]',
    sample_names          TEXT         NOT NULL DEFAULT '[]',
    updated_at            TIMESTAMP    DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_name_char_stats_total
    ON name_char_stats (total_count DESC);
CREATE INDEX IF NOT EXISTS idx_name_char_stats_distinct
    ON name_char_stats (distinct_name_count DESC);
CREATE INDEX IF NOT EXISTS idx_name_char_stats_fame
    ON name_char_stats (weighted_fame DESC);
