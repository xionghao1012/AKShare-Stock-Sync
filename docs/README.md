# 中国股票数据收集系统 (MVC 架构版)

这是一个采用 MVC 架构设计的中国金融市场数据收集和存储应用程序。

## 🏗️ 架构特性

- 🎯 **MVC 架构**: 清晰的模型-视图-控制器分离
- 🔧 **模块化设计**: 高内聚、低耦合的代码结构
- 🔄 **可扩展性**: 易于添加新功能和数据源
- 🎮 **多运行模式**: 支持自动模式和交互模式
- 📊 **丰富的用户界面**: 美观的控制台输出和进度显示

## 📁 项目结构

```
├── main.py                    # 主程序入口
├── index.py                   # 旧版本（保留兼容）
├── config/                    # 配置模块
│   ├── __init__.py
│   └── database_config.py     # 数据库配置管理
├── models/                    # 数据模型
│   ├── __init__.py
│   └── stock_data_model.py    # 股票数据模型
├── views/                     # 视图层
│   ├── __init__.py
│   └── console_view.py        # 控制台视图
├── controllers/               # 控制器
│   ├── __init__.py
│   └── stock_controller.py    # 股票数据控制器
├── utils/                     # 工具类
│   ├── __init__.py
│   └── logger_util.py         # 日志工具
├── .env                       # 环境变量配置
├── .env.example              # 配置模板
└── requirements.txt          # 依赖包列表
```

## 🚀 功能特性

- 🔄 自动获取期货收益率数据（支持螺纹钢等品种）
- 🗄️ 数据自动存储到 MySQL 数据库
- 🧹 内置数据清洗和去重功能
- 📊 完整的日志记录和错误处理
- ⚡ 优化的数据库连接池和批量插入
- 🔒 事务安全保证数据一致性
- 🎮 交互式用户界面
- 📈 数据预览和统计信息

## 🛠️ 环境要求

- Python 3.12.10+
- MySQL 5.7+ 或 8.0+

## 📦 安装步骤

### 1. 安装依赖包

```bash
# 使用pip安装所有依赖
pip install -r requirements.txt
```

### 2. 数据库配置

1. 确保 MySQL 服务正在运行
2. 创建数据库：

```sql
CREATE DATABASE stock CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 3. 环境变量配置

1. 复制配置文件模板：

```bash
copy .env.example .env
```

2. 编辑 `.env` 文件，填入您的数据库信息：

```env
DB_USER=root
DB_PASSWORD=your_actual_password
DB_HOST=localhost
DB_PORT=3306
DB_NAME=stock
TABLE_NAME=roll_yield_bar
LOG_LEVEL=INFO
```

## 🎮 运行程序

### 自动模式（推荐）

```bash
# 使用默认参数运行
python main.py

# 指定参数运行
python main.py --var RB --start-day 20180618 --end-day 20180718
```

### 交互模式

```bash
# 启动交互模式
python main.py --interactive
```

### 兼容模式

```bash
# 运行旧版本
python index.py
```

## 📋 命令行参数

| 参数            | 简写 | 说明                | 默认值   |
| --------------- | ---- | ------------------- | -------- |
| `--interactive` | `-i` | 启用交互模式        | False    |
| `--var`         |      | 品种代码            | RB       |
| `--start-day`   |      | 开始日期 (YYYYMMDD) | 20180618 |
| `--end-day`     |      | 结束日期 (YYYYMMDD) | 20180718 |
| `--log-level`   |      | 日志级别            | INFO     |

## 🎨 MVC 架构说明

### 📊 Model (模型层)

- `models/stock_data_model.py`: 负责数据获取、清洗和存储
- 处理与 akshare API 的交互
- 管理数据库操作和事务

### 👁️ View (视图层)

- `views/console_view.py`: 负责用户界面显示
- 提供美观的控制台输出
- 处理用户输入和交互

### 🎮 Controller (控制器层)

- `controllers/stock_controller.py`: 协调模型和视图
- 处理业务逻辑流程
- 管理系统状态和错误处理

### ⚙️ Config (配置层)

- `config/database_config.py`: 数据库配置管理
- 环境变量处理
- 连接参数优化

### 🔧 Utils (工具层)

- `utils/logger_util.py`: 日志系统管理
- 提供通用工具函数

## 📊 程序输出示例

```
============================================================
🚀 中国股票数据收集系统
============================================================
✅ 系统初始化完成
⏳ [1/4] 获取股票数据
✅ 成功获取 100 条原始数据
⏳ [2/4] 清洗数据
✅ 数据清洗完成，剩余 98 条有效数据
⏳ [3/4] 生成数据预览

📊 数据预览:
----------------------------------------
数据形状: (98, 5)
数据列: ['date', 'open', 'high', 'low', 'close']
内存使用: 3.85 KB

⏳ [4/4] 保存数据到数据库
✅ 数据保存成功

📈 数据汇总:
----------------------------------------
表名: roll_yield_bar
总记录数: 98

============================================================
🎉 程序执行成功完成！
============================================================
```

## 🔧 故障排除

### 常见问题

1. **数据库连接失败**

   - 检查 MySQL 服务是否启动
   - 验证 `.env` 文件中的数据库配置
   - 确认数据库名称存在

2. **模块导入错误**

   - 确保所有依赖包已安装
   - 检查 Python 路径配置

3. **权限错误**
   - 确保数据库用户有创建表的权限
   - 检查文件写入权限（日志文件）

### 日志文件

查看 `stock_data.log` 文件获取详细的执行信息和错误详情。

## 🚀 扩展开发

### 添加新的数据源

1. 在 `models/` 中创建新的数据模型
2. 在 `controllers/` 中添加对应的控制器
3. 更新视图以支持新的数据显示

### 添加新的输出格式

1. 在 `views/` 中创建新的视图类
2. 在控制器中集成新视图
3. 更新主程序以支持新的输出选项

### 数据库扩展

1. 修改 `config/database_config.py` 添加新的配置
2. 在模型中添加新的数据库操作方法
3. 更新相关的业务逻辑

## 📈 性能优化

- **数据库连接池**: 复用连接，减少开销
- **批量操作**: 大数据集分批处理
- **事务管理**: 确保数据一致性
- **内存优化**: 及时释放资源
- **异步处理**: 支持并发操作（可扩展）

## 🎯 完整的 AKShare 数据同步系统

### 系统组件

#### 1. 数据同步模块

- **akshare_sync_main.py**: 手动数据同步
- **scheduler_main.py**: 自动定时同步
- **models/akshare_sync_model.py**: 数据同步核心逻辑

#### 2. 数据管理模块

- **data_manager_main.py**: 数据管理工具
- **utils/data_manager.py**: 数据管理核心功能

#### 3. 系统监控模块

- **system_monitor.py**: 实时系统监控面板
- **utils/scheduler.py**: 调度器管理

#### 4. 统一启动器

- **start.py**: 系统启动器，提供统一入口

### 🚀 快速开始

#### 方法 1: 使用启动器（推荐）

```bash
# 启动系统启动器
python start.py

# 或直接启动特定模式
python start.py --mode sync      # 数据同步
python start.py --mode scheduler # 自动调度
python start.py --mode manager   # 数据管理
python start.py --mode monitor   # 系统监控
```

#### 方法 2: 直接运行

```bash
# 手动数据同步
python akshare_sync_main.py --interactive
python akshare_sync_main.py --category stock
python akshare_sync_main.py --all

# 启动自动调度器
python scheduler_main.py

# 数据管理
python data_manager_main.py --list-tables
python data_manager_main.py --table-info stock_stock_info
python data_manager_main.py --sample stock_stock_info

# 系统监控
python system_monitor.py
```

### 📊 数据同步功能

#### 支持的数据类型

- **股票数据**: 基本信息、历史数据、财务数据、个股信息
- **期货数据**: 主力合约、现货数据、收益率数据
- **基金数据**: ETF 分类、开放式基金信息
- **债券数据**: 中美国债收益率、中国国债收益率
- **外汇数据**: 中行外汇牌价、实时汇率
- **宏观数据**: GDP、CPI、PPI、PMI 等经济指标
- **新闻数据**: 股票新闻、央视新闻
- **行业数据**: 行业板块、概念板块

#### 自动调度功能

- 股票数据: 每 5 分钟同步
- 期货数据: 每 3 分钟同步
- 基金数据: 每 10 分钟同步
- 债券数据: 每 30 分钟同步
- 外汇数据: 每 1 分钟同步
- 宏观数据: 每 1 小时同步
- 新闻数据: 每 15 分钟同步
- 行业数据: 每 30 分钟同步

### 🛠️ 数据管理功能

#### 表管理

```bash
# 列出所有表
python data_manager_main.py --list-tables

# 查看表详细信息
python data_manager_main.py --table-info stock_stock_info

# 查看数据样本
python data_manager_main.py --sample stock_stock_info

# 导出表数据
python data_manager_main.py --export stock_stock_info --output stock_info.csv
```

#### 交互式管理

```bash
python data_manager_main.py
```

### 📈 系统监控

实时监控面板显示：

- 系统资源使用情况（CPU、内存、磁盘）
- 数据库连接状态和大小
- 各表的记录数统计
- 自动刷新（每 5 秒）

```bash
python system_monitor.py
```

### ⚙️ 配置说明

#### 环境变量配置 (.env)

```env
# 数据库配置
DB_USER=root
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=3306
DB_NAME=stock
TABLE_NAME=roll_yield_bar

# 日志配置
LOG_LEVEL=INFO
LOG_FILE=stock_data.log

# 数据库连接池配置
DB_POOL_SIZE=5
DB_MAX_OVERFLOW=10
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=3600
```

### 📋 数据表结构

同步后的数据表命名规则：`{category}_{data_name}`

例如：

- `stock_stock_info`: 股票基本信息
- `stock_stock_zh_a_hist`: A 股历史数据
- `futures_futures_main_sina`: 期货主力合约
- `macro_macro_china_gdp`: 中国 GDP 数据

### 🔧 高级功能

#### 1. 批量数据同步

```bash
# 同步所有数据
python akshare_sync_main.py --all

# 同步特定分类
python akshare_sync_main.py --category stock
```

#### 2. 定时任务管理

```bash
# 启动调度器（后台运行）
nohup python scheduler_main.py > scheduler.log 2>&1 &

# 停止调度器
pkill -f scheduler_main.py
```

#### 3. 数据导出和备份

```bash
# 导出所有表数据
for table in $(python -c "from utils.data_manager import DataManager; from config.database_config import DatabaseConfig; dm = DataManager(DatabaseConfig()); print(' '.join(dm.get_table_list()))"); do
    python data_manager_main.py --export $table --output "backup_${table}.csv"
done
```

### 🚨 注意事项

1. **API 限制**: akshare 有访问频率限制，系统已内置延时机制
2. **数据量**: 某些历史数据量较大，首次同步可能需要较长时间
3. **网络稳定性**: 建议在网络稳定的环境下运行
4. **数据库权限**: 确保数据库用户有创建表和写入数据的权限
5. **磁盘空间**: 预留足够的磁盘空间存储数据

### 📞 技术支持

如遇到问题，请检查：

1. 日志文件 `stock_data.log`
2. 数据库连接配置
3. 网络连接状态
4. akshare 库版本兼容性

现在您拥有了一个完整的、专业的 AKShare 数据同步系统！
