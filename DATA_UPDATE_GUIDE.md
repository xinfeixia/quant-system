# 📊 数据更新指南

## 🎯 如何获取今天/最新的交易数据

### 方法1：更新单只股票（推荐）

```bash
python scripts/fetch_historical_data.py --symbol 0700.HK --days 10
```

**说明**：
- `--symbol`: 股票代码（如 0700.HK）
- `--days`: 获取最近几天的数据（默认365天）
- 系统会自动过滤已存在的数据，只保存新数据

**示例**：
```bash
# 更新腾讯控股最近10天的数据
python scripts/fetch_historical_data.py --symbol 0700.HK --days 10

# 更新阿里巴巴最近10天的数据
python scripts/fetch_historical_data.py --symbol 9988.HK --days 10
```

---

### 方法2：批量更新所有股票

```bash
python scripts/fetch_historical_data.py --batch --market HK --days 10
```

**说明**：
- `--batch`: 批量模式
- `--market`: 市场代码（HK/US/CN）
- `--days`: 获取最近几天的数据

**注意**：批量更新需要较长时间，建议在非交易时间运行

---

### 方法3：检查数据状态

```bash
python scripts/check_data.py
```

**输出示例**：
```
================================================================================
📊 数据获取情况检查
================================================================================

📊 历史数据统计:
--------------------------------------------------------------------------------
代码           名称                       数据条数         最早日期         最新日期
--------------------------------------------------------------------------------
700.HK       腾讯控股                      248   2024-10-07   2025-10-07  ✅
9988.HK      阿里巴巴-W                    248   2024-10-07   2025-10-07  ✅
3690.HK      美团-W                      247   2024-10-07   2025-10-06  ⚠️
```

---

## 📅 港股交易时间和数据更新时间

### 港股交易时间
- **早盘**: 09:30 - 12:00
- **午盘**: 13:00 - 16:00

### 数据更新时间
- **实时数据**: 交易时间内实时更新（15分钟延迟）
- **日线数据**: 收盘后（16:00后）可获取当天完整数据
- **最佳更新时间**: 每天 **16:30** 之后

---

## 🔄 更新流程

### 每日更新流程

#### 步骤1：检查数据状态
```bash
python scripts/check_data.py
```

#### 步骤2：更新最新数据
```bash
# 更新所有港股（推荐在16:30后运行）
python scripts/fetch_historical_data.py --batch --market HK --days 5
```

#### 步骤3：计算技术指标
```bash
# 批量计算所有股票的技术指标
python scripts/calculate_indicators.py --batch --market HK
```

#### 步骤4：运行选股分析
```bash
# 运行选股，获取Top 50推荐
python scripts/run_stock_selection.py --market HK --top 50
```

---

## 🤖 自动化更新

### 使用定时任务（推荐）

```bash
# 启动定时任务（每天9:00和15:30自动运行）
python scripts/daily_selection.py --schedule
```

**功能**：
- ✅ 自动更新数据
- ✅ 自动计算技术指标
- ✅ 自动运行选股
- ✅ 自动导出Excel报告

**输出**：
- 选股结果保存在 `reports/选股结果_HK_YYYYMMDD.xlsx`

---

## 📊 数据说明

### 数据来源
- **港股**: 长桥证券API（15分钟延迟）
- **美股**: 长桥证券API（Nasdaq Basic）
- **A股**: 长桥证券API（实时行情）

### 数据内容
- **K线数据**: 开盘价、最高价、最低价、收盘价、成交量、成交额
- **技术指标**: MA、MACD、RSI、KDJ、布林带、ATR、OBV等20+指标
- **选股评分**: 技术、量价、趋势、形态四维度评分

### 数据存储
- **数据库**: SQLite（`data/longport_quant.db`）
- **表结构**:
  - `stock_info`: 股票基本信息
  - `daily_data`: 日线数据
  - `technical_indicators`: 技术指标
  - `stock_selection`: 选股结果

---

## ⚠️ 常见问题

### Q1: 为什么获取不到今天的数据？

**A**: 可能的原因：
1. **交易时间未结束**: 港股16:00收盘，建议16:30后更新
2. **非交易日**: 周末和节假日没有交易数据
3. **API延迟**: 长桥API有15分钟延迟

**解决方法**：
- 在16:30后运行更新脚本
- 检查今天是否为交易日

---

### Q2: 数据更新失败怎么办？

**A**: 检查以下几点：
1. **API配置**: 检查 `config/api_config.yaml` 中的API密钥是否正确
2. **网络连接**: 确保网络正常
3. **API额度**: 检查是否超过API调用限制

**解决方法**：
```bash
# 查看详细错误日志
python scripts/fetch_historical_data.py --symbol 0700.HK --days 10
```

---

### Q3: 如何知道数据是否最新？

**A**: 运行检查脚本：
```bash
python scripts/check_data.py
```

查看"最新日期"列：
- ✅ 如果是昨天或今天 → 数据最新
- ⚠️ 如果是更早的日期 → 需要更新

---

### Q4: 批量更新需要多长时间？

**A**: 取决于股票数量：
- **120只港股**: 约5-10分钟
- **单只股票**: 约2-3秒

**建议**：
- 首次获取：使用 `--days 365` 获取1年数据
- 日常更新：使用 `--days 5` 获取最近5天数据

---

## 💡 最佳实践

### 1. 每日更新策略

**时间**: 每天 **16:30**（港股收盘后）

**命令**：
```bash
# 一键更新（推荐）
python scripts/daily_selection.py
```

或手动执行：
```bash
# 1. 更新数据
python scripts/fetch_historical_data.py --batch --market HK --days 5

# 2. 计算指标
python scripts/calculate_indicators.py --batch --market HK

# 3. 运行选股
python scripts/run_stock_selection.py --market HK --top 50
```

---

### 2. 周末/节假日

**不需要更新**，因为没有交易数据。

---

### 3. 数据备份

**定期备份数据库**：
```bash
# 复制数据库文件
copy data\longport_quant.db data\backup\longport_quant_20251008.db
```

---

## 🚀 快速开始

### 今天就想看最新数据？

```bash
# 1. 更新单只股票（2-3秒）
python scripts/fetch_historical_data.py --symbol 0700.HK --days 10

# 2. 计算技术指标
python scripts/calculate_indicators.py --symbol 0700.HK

# 3. 查看买卖信号
python scripts/analyze_trading_points.py --symbol 0700.HK
```

或者访问网页：
```
http://localhost:5000/trading-signals
```
输入 `0700.HK` 查看最新分析！

---

## 📖 相关文档

- [功能说明](FEATURES.md) - 完整功能列表
- [买卖信号指南](TRADING_SIGNALS_GUIDE.md) - 买卖点分析使用指南
- [API文档](README.md) - API接口文档

---

**祝您投资顺利！** 🎉💰

