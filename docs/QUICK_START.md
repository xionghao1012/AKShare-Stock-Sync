# 快速开始指南

本指南将帮助你快速上手中国股票数据同步系统。

## 🎯 5分钟快速开始

### 第1步：环境准备

```bash
# 1. 确保Python版本
python --version  # 需要 3.12.10+

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置数据库
cp .env.example .env
# 编辑 .env 文件，设置数据库连接信息
```

### 第2步：数据库优化

```bash
# 运行数据库优化（重要！）
python tools/optimize_database.py
```

### 第3步：开始同步

```bash
# 方式1：智能同步（推荐）
python core/smart_stock_sync.py continue 000001

# 方式2：MVC架构版本
python main.py --interactive

# 方式3：温和同步（网络不稳定时）
python core/gentle_sync.py 000001 3
```

## 🛠️ 详细配置

### 数据库配置

编辑 `.env` 文件：

```env
# 数据库配置
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_password
DB_DATABASE=stock

# 可选配置
DB_PORT=3306
DB_CHARSET=utf8mb4
```

### MySQL数据库准备

```sql
-- 创建数据库
CREATE DATABASE stock CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 创建用户（可选）
CREATE USER 'stock_user'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON stock.* TO 'stock_user'@'localhost';
FLUSH PRIVILEGES;
```

## 🚀 同步模式选择

### 1. 智能同步模式（推荐）

**适用场景**: 大部分情况下的首选

**特点**:
- 支持断点续传
- 自动重试失败股票
- 实时进度保存
- 智能错误处理

**使用方法**:
```bash
# 查看状态
python core/smart_stock_sync.py status

# 从指定股票开始同步
python core/smart_stock_sync.py continue 000001

# 限制同步数量
python core/smart_stock_sync.py continue 000001 100

# 重试失败的股票
python core/smart_stock_sync.py retry
```

### 2. 温和同步模式

**适用场景**: 网络不稳定或数据库性能较低

**特点**:
- 更小的批次大小
- 更长的等待间隔
- 减少数据库压力
- 更稳定的同步过程

**使用方法**:
```bash
# 基本用法
python core/gentle_sync.py <起始股票代码> [批次大小]

# 示例
python core/gentle_sync.py 000001 3    # 每批3只股票
python core/gentle_sync.py 300001 5    # 每批5只股票
```

### 3. MVC架构模式

**适用场景**: 需要更多控制和自定义的场景

**特点**:
- 完整的MVC架构
- 支持交互模式
- 灵活的参数配置
- 适合开发和调试

**使用方法**:
```bash
# 交互模式
python main.py --interactive

# 指定参数
python main.py --var RB --start-day 20180618 --end-day 20180718
```

## 📊 监控同步进度

### 查看同步状态

```bash
# 智能同步状态
python core/smart_stock_sync.py status

# 输出示例：
# 同步进度:
#   当前股票: 000100
#   成功数量: 1500
#   失败数量: 5
#   最后更新: 2025-07-20T10:30:00
```

### 查看日志

```bash
# 实时查看同步日志
tail -f logs/stock_sync.log

# 查看错误日志
grep "ERROR" logs/stock_sync.log
```

### 进度文件

同步进度保存在 `sync_progress.json` 文件中：

```json
{
  "current_stock": "000100",
  "success_count": 1500,
  "failed_count": 5,
  "failed_stocks": [...],
  "last_update": "2025-07-20T10:30:00"
}
```

## 🔧 常用操作

### 从特定股票开始同步

```bash
# 从000001开始同步所有后续股票
python core/smart_stock_sync.py continue 000001

# 从300001开始同步创业板股票
python core/smart_stock_sync.py continue 300001

# 只同步100只股票
python core/smart_stock_sync.py continue 000001 100
```

### 重试失败的股票

```bash
# 重试所有失败的股票
python core/smart_stock_sync.py retry

# 查看失败股票列表
cat failed_stocks.json
```

### 检查数据库状态

```bash
# 检查表结构
python tools/check_tables.py

# 优化数据库
python tools/optimize_database.py

# 系统监控
python tools/system_monitor.py
```

## ⚠️ 注意事项

### 1. 数据库优化

**必须运行数据库优化脚本**，否则可能遇到锁表问题：

```bash
python tools/optimize_database.py
```

### 2. 网络稳定性

- 确保网络连接稳定
- 如遇网络问题，使用温和同步模式
- 系统会自动重试网络错误

### 3. 系统资源

- 确保有足够的磁盘空间
- 监控内存使用情况
- 数据库需要足够的存储空间

### 4. 合规使用

- 遵守数据提供方的使用条款
- 合理控制请求频率
- 不要过度频繁地请求数据

## 🐛 常见问题

### Q1: 出现数据库锁表错误

**解决方案**:
```bash
python tools/optimize_database.py
```

### Q2: 网络连接超时

**解决方案**:
1. 检查网络连接
2. 使用温和同步模式
3. 减少批次大小

### Q3: 同步中断后如何继续

**解决方案**:
```bash
# 系统会自动从上次中断位置继续
python core/smart_stock_sync.py continue <last_stock_code>
```

### Q4: 如何清理重新开始

**解决方案**:
```bash
# 删除进度文件
rm sync_progress.json failed_stocks.json

# 清空数据库表（谨慎操作）
# TRUNCATE TABLE stock_stock_zh_a_hist;
```

## 📈 性能调优

### 批次大小调整

```bash
# 网络好、数据库性能高：大批次
python core/smart_stock_sync.py continue 000001 50

# 网络差、数据库性能低：小批次
python core/gentle_sync.py 000001 3
```

### 数据库优化

```sql
-- 增加InnoDB缓冲池
SET GLOBAL innodb_buffer_pool_size = 2147483648;  -- 2GB

-- 增加锁等待时间
SET GLOBAL innodb_lock_wait_timeout = 300;
```

## 🎉 完成同步

当看到以下信息时，表示同步完成：

```
🎉 同步完成 - 成功: 1500, 失败: 0
```

可以通过以下方式验证：

```bash
# 查看数据库记录数
python tools/check_tables.py

# 查看同步状态
python core/smart_stock_sync.py status
```

---

**下一步**: 查看 [错误处理指南](ERROR_HANDLING_GUIDE.md) 了解如何处理各种错误情况。