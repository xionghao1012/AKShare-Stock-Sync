# 股票数据同步使用指南

## 🚨 重要提示

根据测试结果，当前akshare的股票历史数据接口(`stock_zh_a_hist`)存在网络连接问题。建议采用以下替代方案：

## 📋 可用功能

### ✅ 正常工作的功能
1. **股票基本信息同步** - 完全正常
2. **个股实时信息获取** - 完全正常
3. **数据库连接和存储** - 完全正常

### ⚠️ 有问题的功能
1. **股票历史数据同步** - 网络连接不稳定

## 🛠️ 推荐使用方法

### 方法1：使用现有稳定功能
```bash
# 获取股票基本信息（推荐）
python -c "
import akshare as ak
from config.database_config import DatabaseConfig
from models.akshare_sync_model import AKShareSyncModel

# 初始化
db_config = DatabaseConfig()
model = AKShareSyncModel(db_config)
model.connect_database()

# 同步股票基本信息
data = model.fetch_data_by_category('stock')
print('同步完成')
"
```

### 方法2：分步骤数据获取
```bash
# 1. 先获取股票列表
python -c "
import akshare as ak
df = ak.stock_info_sz_name_code()
print(f'获取到 {len(df)} 只股票信息')
print(df.head())
"

# 2. 获取个股详细信息
python -c "
import akshare as ak
df = ak.stock_individual_info_em(symbol='000001')
print('平安银行详细信息:')
print(df)
"
```

### 方法3：使用修复后的批量同步（小批量）
```bash
# 测试网络修复效果
python network_fix.py

# 小批量同步测试（建议从1-3只开始）
python batch_sync_stocks.py 1
```

## 🔧 故障排除步骤

### 步骤1：检查网络环境
```bash
# 运行网络诊断
python network_fix.py
```

### 步骤2：测试基础功能
```bash
# 测试数据库连接
python -c "
from config.database_config import DatabaseConfig
db_config = DatabaseConfig()
print('数据库配置正常')
"

# 测试akshare基础接口
python -c "
import akshare as ak
df = ak.stock_info_sz_name_code()
print(f'akshare基础接口正常: {len(df)} 条数据')
"
```

### 步骤3：逐步测试同步功能
```bash
# 测试单只股票基础信息
python -c "
import akshare as ak
df = ak.stock_individual_info_em(symbol='000001')
print('个股信息获取正常')
print(df)
"
```

## 📊 当前可用的数据类型

### 1. 股票基本信息
- **接口**: `ak.stock_info_sz_name_code()`
- **状态**: ✅ 正常
- **数据量**: 2867条
- **包含**: 股票代码、名称、上市日期、行业等

### 2. 个股实时信息
- **接口**: `ak.stock_individual_info_em(symbol='000001')`
- **状态**: ✅ 正常
- **包含**: 最新价、总股本、流通股、市值等

### 3. 其他可用数据
- 期货主力合约信息
- 基金ETF信息
- 债券收益率数据
- 外汇汇率数据

## 🎯 建议的工作流程

### 日常使用流程
1. **每日更新基础信息**
   ```bash
   python models/akshare_sync_model.py
   ```

2. **获取特定股票详情**
   ```bash
   python -c "
   import akshare as ak
   # 替换为你需要的股票代码
   df = ak.stock_individual_info_em(symbol='000001')
   print(df)
   "
   ```

3. **监控同步状态**
   ```bash
   tail -f stock_data.log
   ```

### 问题解决流程
1. **遇到网络错误时**
   - 运行 `python network_fix.py`
   - 检查网络连接
   - 尝试更换网络环境

2. **数据同步失败时**
   - 检查日志文件 `stock_sync.log`
   - 使用小批量测试
   - 增加重试间隔

## 🔄 替代解决方案

### 方案A：使用其他数据源
考虑集成其他金融数据API：
- Tushare
- 聚宽(JoinQuant)
- 东方财富API

### 方案B：本地数据缓存
建立本地数据缓存机制，减少对外部API的依赖。

### 方案C：定时同步策略
在网络状况较好的时段（如凌晨）进行批量同步。

## 📞 技术支持

### 常见问题
1. **Q: 为什么历史数据接口总是失败？**
   A: 这是akshare特定接口的网络连接问题，建议使用替代方案。

2. **Q: 如何提高同步成功率？**
   A: 使用小批量同步，增加重试间隔，选择网络较好的时段。

3. **Q: 数据不完整怎么办？**
   A: 可以组合使用多个接口获取完整数据。

### 联系方式
- 查看日志文件获取详细错误信息
- 使用网络诊断工具排查问题
- 考虑网络环境优化

---

**最后更新**: 2025-07-17
**状态**: 基础功能正常，历史数据接口需要网络优化