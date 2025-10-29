# 股票数据扩充指南

## 📊 当前股票数量

- **港股 (HK)**: 120只 ✅ (已有完整数据)
- **美股 (US)**: 52只 ⚠️ (刚添加，需获取数据)
- **总计**: 172只股票

---

## 🎉 已完成的工作

### 1. 添加了45只美股
包括：
- **科技巨头**: Apple, Microsoft, Google, Amazon, Meta, NVIDIA, Tesla
- **芯片半导体**: AMD, Intel, QCOM, Broadcom, TSM, ASML
- **软件云计算**: Salesforce, Oracle, Adobe, ServiceNow, Snowflake
- **电商零售**: 阿里巴巴, 京东, 拼多多, Shopify
- **电动车**: 蔚来, 小鹏, 理想, Rivian, Lucid
- **金融支付**: Visa, Mastercard, PayPal, Block
- **银行**: JPMorgan, Bank of America, Wells Fargo, Goldman Sachs
- **消费品牌**: Nike, Starbucks, McDonald's, Coca-Cola, Pepsi
- **医药生物**: Pfizer, Johnson & Johnson, Moderna, AbbVie
- **娱乐传媒**: Disney, Netflix, Spotify
- **其他**: Uber, Airbnb, Coinbase

### 2. 港股数据完整
120只港股都有完整的历史数据和技术指标

---

## ⚠️ API限制问题

### 问题描述
长桥API对历史K线数据有频率限制：
```
OpenApiException: (code=301607) history kline symbol count out of limit
```

### 限制说明
- **每分钟请求限制**: 约5-10只股票
- **每天请求限制**: 根据API套餐不同
- **解决方案**: 分批获取，添加延迟

---

## 🔧 获取美股数据的方法

### 方法1：分批获取（推荐）

每次获取5只股票，避免触发限制：

```bash
# 第1批（前5只）
python scripts/fetch_historical_data.py --symbol AAPL.US --days 365
python scripts/fetch_historical_data.py --symbol MSFT.US --days 365
python scripts/fetch_historical_data.py --symbol GOOGL.US --days 365
python scripts/fetch_historical_data.py --symbol AMZN.US --days 365
python scripts/fetch_historical_data.py --symbol TSLA.US --days 365

# 等待1分钟后继续...

# 第2批
python scripts/fetch_historical_data.py --symbol NVDA.US --days 365
python scripts/fetch_historical_data.py --symbol META.US --days 365
python scripts/fetch_historical_data.py --symbol GOOG.US --days 365
python scripts/fetch_historical_data.py --symbol AMD.US --days 365
python scripts/fetch_historical_data.py --symbol INTC.US --days 365
```

### 方法2：使用自动化脚本

创建一个带延迟的批量获取脚本：

```python
# scripts/fetch_us_stocks_slowly.py
import time
from fetch_historical_data import fetch_single_stock

us_stocks = ['AAPL.US', 'MSFT.US', 'GOOGL.US', ...]

for i, symbol in enumerate(us_stocks):
    print(f"[{i+1}/{len(us_stocks)}] 获取 {symbol}")
    fetch_single_stock(symbol, days=365)
    
    # 每5只股票休息60秒
    if (i + 1) % 5 == 0:
        print("休息60秒...")
        time.sleep(60)
    else:
        time.sleep(2)  # 每只股票间隔2秒
```

### 方法3：分多天获取

如果API有每日限制，可以分多天获取：
- **第1天**: 获取前20只
- **第2天**: 获取第21-40只
- **第3天**: 获取剩余股票

---

## 📈 添加更多股票

### 添加港股

编辑 `scripts/add_more_stocks.py` 中的 `HK_STOCKS` 字典：

```python
HK_STOCKS = {
    '1234.HK': '股票名称',
    # 添加更多...
}
```

然后运行：
```bash
python scripts/add_more_stocks.py --market HK
```

### 添加美股

编辑 `scripts/add_more_stocks.py` 中的 `US_STOCKS` 字典：

```python
US_STOCKS = {
    'SYMBOL.US': 'Stock Name',
    # 添加更多...
}
```

然后运行：
```bash
python scripts/add_more_stocks.py --market US
```

---

## 🎯 推荐的扩充方向

### 港股可以添加：
1. **更多科技股**: 快手、哔哩哔哩、知乎等
2. **更多新能源**: 宁德时代、赣锋锂业等
3. **更多医药**: 药明康德、康龙化成等
4. **更多消费**: 海天味业、伊利股份等

### 美股可以添加：
1. **更多科技**: Palantir, Snowflake, Datadog等
2. **更多芯片**: Marvell, Micron, Applied Materials等
3. **更多生物**: Illumina, Regeneron, Vertex等
4. **更多金融**: Charles Schwab, BlackRock等

---

## 💡 使用建议

### 当前最佳实践

1. **专注港股选股**
   - 120只港股数据完整
   - 可以立即运行选股分析
   - 技术指标齐全

2. **逐步获取美股数据**
   - 每天获取10-20只
   - 避免触发API限制
   - 优先获取热门股票

3. **分市场运行选股**
   ```bash
   # 港股选股（立即可用）
   python scripts/run_stock_selection.py --market HK --top 50
   
   # 美股选股（数据完整后）
   python scripts/run_stock_selection.py --market US --top 30
   ```

---

## 📊 数据完整性检查

### 查看股票数量
```bash
python scripts/count_stocks.py
```

### 查看数据状态
```bash
python scripts/check_data.py
```

### 查看特定股票数据
```bash
python scripts/check_data.py --symbol AAPL.US
```

---

## 🚀 下一步操作

### 立即可做：
1. ✅ 运行港股选股分析
2. ✅ 查看买卖信号
3. ✅ 导出选股结果

### 需要时间：
1. ⏳ 分批获取美股历史数据（每天10-20只）
2. ⏳ 计算美股技术指标
3. ⏳ 运行美股选股分析

---

## 📞 API升级建议

如果需要更高的API限制，可以考虑：

1. **升级长桥API套餐**
   - 更高的请求频率
   - 更多的每日请求量
   - 实时行情数据

2. **使用多个API账号**
   - 轮流使用不同账号
   - 提高整体获取速度

3. **购买历史数据包**
   - 一次性获取所有历史数据
   - 避免频率限制

---

## 📝 总结

✅ **已完成**:
- 添加了45只美股到数据库
- 港股120只数据完整
- 总计172只股票

⚠️ **待完成**:
- 美股历史数据获取（受API限制）
- 美股技术指标计算
- 美股选股分析

💡 **建议**:
- 先使用港股进行选股分析
- 逐步获取美股数据
- 考虑升级API套餐

---

**现在可以立即使用港股数据进行选股分析！** 🎉

```bash
python scripts/run_stock_selection.py --market HK --top 50
```

