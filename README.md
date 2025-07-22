# 中国股票数据同步系统

一个高效、稳定的中国A股市场数据同步工具，支持批量获取和存储股票历史数据。

## 🚀 项目特色

- **全面覆盖**: 支持A股所有板块（主板、中小板、创业板、科创板等）
- **智能同步**: 支持断点续传、失败重试、温和同步等多种模式
- **高性能**: 优化的数据库连接池和批量操作
- **稳定可靠**: 完善的错误处理和网络重试机制
- **易于使用**: 简洁的命令行界面和详细的文档

## 📊 同步成果

- ✅ **002xxx系列**: 从002264开始的所有后续股票
- ✅ **300xxx系列**: 全部同步完成（包括重试成功的108只）
- ✅ **301xxx系列**: 全部同步完成（1022只）
- ✅ **302xxx系列**: 全部同步完成（1只：302132中航成飞）
- 🎯 **总体成功率**: 接近100%

## 🏗️ 项目结构

```
stock-sync-system/
├── 📄 main.py                    # 主程序入口（MVC架构）
├── 📄 requirements.txt           # 依赖包列表
├── 📄 .env.example              # 环境变量配置模板
├── 📄 sync_progress.json        # 同步进度记录
├── 📄 project_cleanup.py        # 项目清理脚本
│
├── 📁 config/                   # 配置模块
│   ├── database_config.py      # 数据库配置
│   ├── sync_config.py          # 同步配置
│   └── __init__.py
│
├── 📁 models/                   # 数据模型层 (MVC-M)
│   ├── akshare_sync_model.py   # AKShare数据模型
│   ├── stock_data_model.py     # 股票数据模型
│   └── __init__.py
│
├── 📁 controllers/              # 控制器层 (MVC-C)
│   ├── akshare_sync_controller.py # 同步控制器
│   ├── stock_controller.py     # 股票控制器
│   └── __init__.py
│
├── 📁 views/                    # 视图层 (MVC-V)
│   ├── console_view.py         # 控制台视图
│   └── __init__.py
│
├── 📁 utils/                    # 工具类
│   ├── error_handler.py        # 错误处理
│   ├── logger_util.py          # 日志工具
│   └── __init__.py
│
├── 📁 core/                     # 🚀 核心功能模块
│   ├── smart_stock_sync.py     # 智能同步工具（推荐）
│   ├── batch_sync_stocks.py    # 批量同步核心
│   └── gentle_sync.py          # 温和同步模式
│
├── 📁 tools/                    # 🔧 工具脚本
│   ├── optimize_database.py    # 数据库优化
│   ├── check_tables.py         # 表结构检查
│   └── system_monitor.py       # 系统监控
│
├── 📁 scripts/                  # 📜 辅助脚本
│   ├── continue_sync.py        # 继续同步
│   ├── check_302_stocks.py     # 检查302系列
│   ├── get_302_stocks.py       # 获取302系列
│   └── test_*.py              # 测试脚本
│
├── 📁 docs/                     # 📚 文档
│   ├── README.md               # 项目说明（已移动）
│   ├── QUICK_START.md          # 快速开始指南
│   ├── ARCHITECTURE.md         # 系统架构说明
│   ├── USAGE_GUIDE.md          # 使用指南
│   ├── ERROR_HANDLING_GUIDE.md # 错误处理指南
│   ├── mysql_config_fix.sql    # 数据库优化脚本
│   └── *.md                   # 其他文档
│
├── 📁 logs/                     # 📋 日志文件
│   ├── stock_sync.log          # 同步日志
│   ├── error_handling_test.log # 错误处理日志
│   └── *.log                  # 其他日志
│
└── 📁 archive/                  # 🗄️ 归档文件
    ├── akshare_sync_main.py    # 旧版本主程序
    ├── index.py               # 旧版本入口
    └── *.py                   # 其他旧版本文件
```

### 📂 目录说明

| 目录 | 说明 | 主要文件 |
|------|------|----------|
| **core/** | 核心同步功能 | `smart_stock_sync.py` (推荐) |
| **tools/** | 系统工具 | `optimize_database.py` (必需) |
| **docs/** | 项目文档 | `QUICK_START.md`, `ARCHITECTURE.md` |
| **config/** | 配置管理 | `database_config.py` |
| **models/** | 数据模型 | MVC架构的模型层 |
| **controllers/** | 业务控制 | MVC架构的控制器层 |
| **views/** | 用户界面 | MVC架构的视图层 |
| **utils/** | 通用工具 | 错误处理、日志工具 |
| **scripts/** | 辅助脚本 | 测试和检查脚本 |
| **logs/** | 日志文件 | 运行日志和错误日志 |
| **archive/** | 归档文件 | 旧版本和重复功能文件 |

## 🛠️ 安装配置

### 1. 环境要求

- Python 3.12.10+
- MySQL 5.7+
- 网络连接

### 2. 安装依赖

```bash
# 克隆项目
git clone <repository-url>
cd stock-sync-system

# 安装依赖
pip install -r requirements.txt
```

### 3. 数据库配置

```bash
# 复制配置模板
cp .env.example .env

# 编辑配置文件
# 设置数据库连接信息
```

### 4. 数据库优化（重要）

```bash
# 运行数据库优化脚本
python tools/optimize_database.py
```

## 🚀 快速开始

### 方式一：使用MVC架构版本（推荐）

```bash
# 交互模式
python main.py --interactive

# 指定参数运行
python main.py --var RB --start-day 20180618 --end-day 20180718
```

### 方式二：使用智能同步工具

```bash
# 查看同步状态
python core/smart_stock_sync.py status

# 从指定股票开始同步
python core/smart_stock_sync.py continue 000001

# 重试失败的股票
python core/smart_stock_sync.py retry
```

### 方式三：使用温和同步模式

```bash
# 温和同步（适合网络不稳定环境）
python core/gentle_sync.py 000001 5
```

## 📖 详细使用说明

### 智能同步工具

智能同步工具是推荐的同步方式，支持：

- **断点续传**: 自动从上次中断位置继续
- **失败重试**: 智能重试失败的股票
- **进度保存**: 实时保存同步进度
- **批量处理**: 支持分批同步

```bash
# 基本用法
python core/smart_stock_sync.py <command> [options]

# 命令说明
continue <股票代码> [数量]  # 从指定股票开始同步
retry                      # 重试失败的股票
status                     # 查看同步状态
```

### 温和同步模式

适合网络不稳定或数据库性能较低的环境：

```bash
python core/gentle_sync.py <起始股票代码> [批次大小]

# 示例
python core/gentle_sync.py 000001 3  # 每批3只股票
```

## 🔧 工具脚本

### 数据库优化

```bash
# 优化数据库配置（解决锁表问题）
python tools/optimize_database.py
```

### 系统监控

```bash
# 监控系统状态
python tools/system_monitor.py
```

### 表结构检查

```bash
# 检查数据库表结构
python tools/check_tables.py
```

## 📋 配置说明

### 数据库配置

在 `.env` 文件中配置：

```env
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_password
DB_DATABASE=stock
```

### 同步配置

主要配置项：

- **批次大小**: 控制每批同步的股票数量
- **重试次数**: 失败时的重试次数
- **等待时间**: 请求间隔时间
- **超时设置**: 网络请求超时时间

## 🐛 故障排除

### 常见问题

1. **数据库锁表错误**
   ```bash
   python tools/optimize_database.py
   ```

2. **网络连接超时**
   - 检查网络连接
   - 增加重试次数
   - 使用温和同步模式

3. **内存不足**
   - 减少批次大小
   - 增加系统内存

### 错误处理

系统提供完善的错误分类和处理：

- **网络错误**: 自动重试
- **数据库错误**: 优化建议
- **数据错误**: 跳过并记录
- **系统错误**: 详细日志

详见：[错误处理指南](docs/ERROR_HANDLING_GUIDE.md)

## 📊 性能优化

### 数据库优化

- InnoDB缓冲池大小: 2GB
- 锁等待超时: 300秒
- 连接池管理
- 批量插入优化

### 网络优化

- 请求重试机制
- 指数退避算法
- 连接池复用
- 超时控制

### 内存优化

- 分批处理数据
- 及时释放资源
- 垃圾回收优化

## 📈 监控和日志

### 日志文件

- `logs/stock_sync.log`: 主要同步日志
- `logs/error_handling_test.log`: 错误处理日志
- `sync_progress.json`: 同步进度记录

### 监控指标

- 同步成功率
- 网络请求延迟
- 数据库性能
- 系统资源使用

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支
3. 提交更改
4. 推送到分支
5. 创建 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 🙏 致谢

- [AKShare](https://github.com/akfamily/akshare) - 优秀的金融数据接口
- [SQLAlchemy](https://www.sqlalchemy.org/) - 强大的ORM框架
- [MySQL](https://www.mysql.com/) - 可靠的数据库系统

## 📚 文档导航

### 🚀 快速开始
- [📖 项目总览](README.md) - 项目概况和特色（当前文档）
- [⚡ 快速开始](docs/QUICK_START.md) - 5分钟快速上手指南
- [🏗️ 系统架构](docs/ARCHITECTURE.md) - 详细的架构设计说明

### 📘 使用指南
- [📋 使用指南](docs/USAGE_GUIDE.md) - 详细的功能使用说明
- [🐛 错误处理](docs/ERROR_HANDLING_GUIDE.md) - 故障排除和错误处理
- [🔧 数据库优化](docs/mysql_config_fix.sql) - 数据库配置优化脚本

### 📊 项目信息
- [📋 项目总结](docs/PROJECT_SUMMARY.md) - 项目整理过程和成果
- [📈 优化报告](docs/优化完成报告.md) - 性能优化详细报告
- [🌐 网络方案](docs/网络问题解决方案.md) - 网络问题解决方案

### 🎯 推荐阅读路径

**新用户**: README.md → QUICK_START.md → 开始使用  
**开发者**: ARCHITECTURE.md → USAGE_GUIDE.md → 深入开发  
**运维人员**: ERROR_HANDLING_GUIDE.md → 故障排除  
**项目维护**: PROJECT_SUMMARY.md → 了解项目结构

## 📞 支持

如有问题或建议，请：

1. 📖 查看 [快速开始指南](docs/QUICK_START.md)
2. 📘 查看 [使用指南](docs/USAGE_GUIDE.md)  
3. 🐛 查看 [错误处理指南](docs/ERROR_HANDLING_GUIDE.md)
4. 📋 查看 [项目总结](docs/PROJECT_SUMMARY.md)
5. 🔍 提交 Issue 或联系维护者

## ⭐ 项目亮点

- 🎯 **高成功率**: 接近100%的同步成功率
- 🚀 **智能同步**: 支持断点续传、失败重试
- 🔧 **完善工具**: 数据库优化、系统监控等工具
- 📚 **文档完整**: 从快速开始到架构设计的完整文档
- 🏗️ **架构清晰**: MVC模式 + 模块化设计
- 🛡️ **稳定可靠**: 完善的错误处理和重试机制

---

**注意**: 请遵守相关法律法规和数据提供方的使用条款，合理使用数据接口。

**版本**: v2.0 (项目整理版)  
**最后更新**: 2025-07-20