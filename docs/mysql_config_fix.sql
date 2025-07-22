-- MySQL配置优化脚本
-- 解决锁表问题

-- 1. 增加InnoDB缓冲池大小
SET GLOBAL innodb_buffer_pool_size = 2147483648;  -- 2GB

-- 2. 增加锁等待超时时间
SET GLOBAL innodb_lock_wait_timeout = 300;

-- 3. 优化其他相关参数
SET GLOBAL innodb_log_file_size = 268435456;      -- 256MB
SET GLOBAL innodb_log_buffer_size = 67108864;     -- 64MB
SET GLOBAL innodb_flush_log_at_trx_commit = 2;
SET GLOBAL innodb_flush_method = 'O_DIRECT';

-- 4. 刷新表缓存
FLUSH TABLES;

-- 5. 查看当前配置
SHOW VARIABLES LIKE 'innodb_buffer_pool_size';
SHOW VARIABLES LIKE 'innodb_lock_wait_timeout';

-- 6. 查看当前锁状态
SHOW ENGINE INNODB STATUS\G