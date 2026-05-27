-- ============================================================
-- NAME 智能取名系统 · 数据库初始化总入口
-- ============================================================
-- 使用方式：
--   psql -U postgres -d name_db -f data/schema/00_init.sql
-- 顺序执行所有 schema 脚本。
-- ============================================================

\echo '=== 创建数据库 schema ==='

\i 01_characters.sql
\echo '✓ characters'

\i 02_classics.sql
\echo '✓ classics + character_classics'

\i 03_famous_names.sql
\echo '✓ famous_names + character_famous'

\i 04_rules.sql
\i 05_name_char_stats.sql
\echo '✓ 81数理 + 调候用神 + 易经 + 谐音风险'

\echo '=== 全部 schema 创建完成 ==='
