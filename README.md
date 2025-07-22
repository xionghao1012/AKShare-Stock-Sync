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
│   └── test_*.py              # 测试脚本
│
├── 📁 docs/                     # 📚 文档
│   ├── README.md               # 项目说明
│   ├── QUICK_START.md          # 快速开始指南
│   └── 其他文档
│
├── 📁 logs/                     # 📋 日志文件
└── 📁 archive/                  # 🗄️ 归档文件
```

## 🛠️ 安装配置

### 1. 环境要求
- Python 3.12.10+
- MySQL 5.7+
- 网络连接

### 2. 安装依赖
```bash
# 克隆项目
git clone https://github.com/xionghao1012/AKShare-Stock-Sync.git
cd AKShare-Stock-Sync

# 安装依赖
pip install -r requirements.txt
```

### 3. 数据库配置
```bash
# 复制配置模板
cp .env.example .env

# 编辑配置文件，设置数据库连接信息
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

## 📖 详细文档

请查看 [docs/](docs/) 目录下的详细文档：
- [快速开始指南](docs/QUICK_START.md)
- [系统架构说明](docs/ARCHITECTURE.md)
- [使用指南](docs/USAGE_GUIDE.md)
- [错误处理指南](docs/ERROR_HANDLING_GUIDE.md)

## 🤝 贡献

欢迎提交Issue和Pull Request来改进这个项目！

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件