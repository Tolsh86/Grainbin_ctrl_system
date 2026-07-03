-- Grainbin System 数据库初始化脚本
-- 启用必要扩展

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";

-- 验证扩展
SELECT extname, extversion FROM pg_extension WHERE extname IN ('uuid-ossp', 'vector');
