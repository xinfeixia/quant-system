# 集成Tushare/AkShare数据源方案

## 🎯 目标

将 `stock-analysis-system` 中成熟的 Tushare/AkShare 数据源集成到 `longport-quant-system`，解决长桥API的频率限制问题。

---

## 📊 当前状况

### longport-quant-system
- ✅ **港股**: 95只，数据完整
- ⚠️ **美股**: 7只，数据不足
- ❌ **A股**: 10只，受API限制严重

### stock-analysis-system
- ✅ **完整的Tushare集成**
- ✅ **完整的AkShare集成**
- ✅ **成熟的数据获取流程**
- ✅ **完善的错误处理**

---

## 🔄 集成方案

### 方案A：复制数据源模块（推荐）

**优点**:
- 快速实现
- 代码成熟稳定
- 已经过测试

**步骤**:

1. **复制数据源文件**
   ```bash
   # 复制Tushare数据源
   cp stock-analysis-system/data_collection/sources/tushare_source.py longport-quant-system/data_collection/
   
   # 复制AkShare数据源
   cp stock-analysis-system/data_collection/sources/akshare_source.py longport-quant-system/data_collection/
   
   # 复制基类
   cp stock-analysis-system/data_collection/sources/base_source.py longport-quant-system/data_collection/
   ```

2. **复制辅助工具**
   ```bash
   # 复制重试装饰器
   cp stock-analysis-system/utils/retry.py longport-quant-system/utils/
   
   # 复制辅助函数
   cp stock-analysis-system/utils/helpers.py longport-quant-system/utils/
   ```

3. **更新配置文件**
   
   在 `config/api_config.yaml` 中添加：
   ```yaml
   tushare:
     token: "YOUR_TUSHARE_TOKEN_HERE"
     request_interval: 0.2  # 请求间隔（秒）
   
   akshare:
     request_interval: 1.0  # 请求间隔（秒）
   ```

4. **创建适配器**
   
   创建 `data_collection/tushare_adapter.py`，将Tushare数据格式转换为系统格式

5. **创建获取脚本**
   
   创建 `scripts/fetch_a_stocks_tushare.py`，使用Tushare获取A股数据

---

### 方案B：直接使用stock-analysis-system数据库

**优点**:
- 无需重新获取数据
- 立即可用

**步骤**:

1. **导出数据**
   ```bash
   # 从stock-analysis-system导出A股数据
   python export_a_stock_data.py
   ```

2. **导入数据**
   ```bash
   # 导入到longport-quant-system
   python import_a_stock_data.py
   ```

---

## 🚀 推荐实施步骤

### 第1步：准备Tushare Token（5分钟）

1. 访问 https://tushare.pro/register
2. 注册账号
3. 获取Token
4. 填入配置文件

### 第2步：复制数据源代码（10分钟）

我将帮您：
1. 复制所有必要的文件
2. 调整导入路径
3. 适配数据格式

### 第3步：创建获取脚本（15分钟）

创建专门的A股数据获取脚本：
- 使用Tushare获取历史数据
- 自动转换为系统格式
- 保存到数据库

### 第4步：获取A股数据（1-2小时）

运行脚本获取152只A股的历史数据：
- 无频率限制问题
- 数据质量高
- 自动重试机制

### 第5步：计算指标和选股（10分钟）

```bash
# 计算技术指标
python scripts/calculate_indicators.py --batch --market CN

# 运行选股
python scripts/run_stock_selection.py --market CN --top 50
```

---

## 📁 需要创建的文件

### 1. data_collection/tushare_source.py
- Tushare数据源实现
- 从stock-analysis-system复制并适配

### 2. data_collection/akshare_source.py
- AkShare数据源实现
- 从stock-analysis-system复制并适配

### 3. data_collection/base_source.py
- 数据源基类
- 定义统一接口

### 4. utils/retry.py
- 重试装饰器
- 处理网络错误

### 5. utils/helpers.py
- 辅助函数
- 股票代码转换等

### 6. scripts/fetch_a_stocks_tushare.py
- A股数据获取脚本
- 使用Tushare API

### 7. scripts/fetch_a_stocks_akshare.py
- A股数据获取脚本（备选）
- 使用AkShare API

---

## 🔧 代码适配要点

### 1. 数据格式转换

**Tushare格式** → **系统格式**

```python
# Tushare返回
{
    'trade_date': '20251009',
    'open': 10.5,
    'close': 10.8,
    'high': 11.0,
    'low': 10.3,
    'vol': 1000000,
    'amount': 10800000
}

# 转换为系统格式
{
    'symbol': '000001.SZ',
    'trade_date': datetime(2025, 10, 9),
    'open': 10.5,
    'close': 10.8,
    'high': 11.0,
    'low': 10.3,
    'volume': 1000000,
    'turnover': 10800000
}
```

### 2. 股票代码转换

```python
# 系统格式: 000001.SZ
# Tushare格式: 000001.SZ (相同)
# 需要处理的情况:
# - 去除市场前缀: sh000001 → 000001
# - 添加市场后缀: 000001 → 000001.SZ
```

### 3. 日期格式转换

```python
# Tushare: '20251009' (YYYYMMDD)
# 系统: datetime(2025, 10, 9) 或 '2025-10-09'
```

---

## 💡 使用示例

### 获取单只股票数据

```python
from data_collection.tushare_source import TushareDataSource

# 初始化
config = {'token': 'your_token_here'}
source = TushareDataSource(config)

# 获取日线数据
df = source.get_daily_data(
    stock_code='000001.SZ',
    start_date='2024-10-09',
    end_date='2025-10-09'
)

print(f"获取到 {len(df)} 条数据")
```

### 批量获取A股数据

```bash
# 使用Tushare获取所有152只A股
python scripts/fetch_a_stocks_tushare.py --days 365

# 预计时间: 1-2小时
# 无频率限制问题
```

---

## 📊 预期效果

### 数据获取速度

| 数据源 | 单只股票 | 152只A股 | 限制 |
|--------|---------|---------|------|
| **长桥API** | 30秒 | 76分钟 | ❌ 严格限制 |
| **Tushare** | 0.5秒 | 1.3分钟 | ✅ 宽松限制 |
| **AkShare** | 1秒 | 2.5分钟 | ✅ 无限制 |

### 数据质量

| 项目 | 长桥API | Tushare | AkShare |
|------|---------|---------|---------|
| **准确性** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **完整性** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **稳定性** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **实时性** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |

---

## 🎯 最终架构

### 多数据源策略

```
longport-quant-system
├── 港股数据 → 长桥API ✅
├── 美股数据 → 长桥API ⚠️
└── A股数据 → Tushare/AkShare ✅
```

### 优势

1. ✅ **充分利用各数据源优势**
   - 长桥API: 港股、美股实时数据
   - Tushare: A股历史数据
   - AkShare: 备用数据源

2. ✅ **避免单点故障**
   - 一个数据源失败，可切换到另一个
   - 提高系统可靠性

3. ✅ **降低成本**
   - Tushare免费版足够使用
   - AkShare完全免费
   - 长桥API用于港股美股

---

## 📝 下一步行动

### 立即可做

1. **注册Tushare账号**
   - 访问 https://tushare.pro/register
   - 获取Token

2. **准备好Token**
   - 复制Token
   - 准备填入配置

### 等我帮您完成

1. **复制数据源代码**
   - 从stock-analysis-system复制
   - 适配到longport-quant-system

2. **创建获取脚本**
   - 编写A股数据获取脚本
   - 测试数据获取

3. **获取A股数据**
   - 运行脚本
   - 获取152只A股历史数据

4. **完成分析**
   - 计算技术指标
   - 运行选股
   - 查看结果

---

## 🎉 预期结果

完成后，您将拥有：

- ✅ **340只股票** 的完整数据
  - 136只港股 ✅
  - 52只美股 ⚠️
  - 152只A股 ✅

- ✅ **多数据源支持**
  - 长桥API（港股、美股）
  - Tushare（A股）
  - AkShare（备用）

- ✅ **完整的分析系统**
  - 技术指标计算
  - 智能选股
  - 买卖信号
  - 可视化展示

---

**准备好开始了吗？请告诉我您的Tushare Token，我将立即开始集成！** 🚀

