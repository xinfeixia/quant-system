# 🤖 自动交易系统

## 🎯 系统简介

自动交易系统是一个**全自动**的量化交易系统，能够：

1. ✅ **监控资金流入**：实时监控股票市场，检测大量资金涌入
2. ✅ **自动买入**：检测到资金流入时，自动生成并执行买入信号
3. ✅ **自动止盈止损**：监控持仓，达到目标利润或止损点时自动卖出
4. ✅ **无需人工干预**：全程自动化，24小时运行

---

## 🚀 快速开始（3步）

### 第1步：配置自动交易

编辑 `config/config.yaml`：

```yaml
# 资金流入监控配置
money_flow_monitor:
  enabled: true                    # 启用监控
  auto_trade: true                 # 启用自动交易（重要！）
  send_email: false                # 不发送邮件
  interval: 60                     # 监控间隔（秒）
  volume_ratio_threshold: 3.0      # 成交量倍数阈值
  turnover_ratio_threshold: 3.0    # 成交额倍数阈值
  price_change_threshold: 0.05     # 价格变动阈值（5%）

# 自动交易配置
auto_trading:
  enabled: true                    # 启用自动交易
  engine_type: local_paper         # 交易引擎（local_paper=模拟，longport=真实）
  execution_interval: 30           # 执行间隔（秒）
  
  # 止盈配置
  take_profit:
    enabled: true
    target_profit_pct: 0.10        # 目标利润 10%
  
  # 止损配置
  stop_loss:
    enabled: true
    stop_loss_pct: -0.05           # 止损比例 -5%
  
  # 移动止损配置（可选）
  trailing_stop:
    enabled: false
    trailing_stop_pct: 0.03        # 移动止损 3%
```

### 第2步：启动系统

运行自动交易系统：

```bash
cd longport-quant-system
python scripts/run_auto_trading.py
```

### 第3步：观察运行

系统会自动：
1. 监控股票资金流入
2. 检测到资金流入时自动买入
3. 持仓达到10%利润时自动卖出
4. 持仓亏损达到-5%时自动止损

---

## 📊 系统架构

系统由3个模块组成，通过多线程并行运行：

### 1️⃣ 资金流入监控器（MoneyFlowMonitor）

**功能：**
- 每分钟获取股票行情数据
- 计算成交量、成交额倍数
- 检测异常资金流入
- 自动生成买入信号

**触发条件：**
- 成交量 >= 平均成交量 × 3.0
- 成交额 >= 平均成交额 × 3.0
- 价格变动 >= 5%

### 2️⃣ 自动交易执行器（AutoTrader）

**功能：**
- 每30秒检查待执行信号
- 自动执行买入信号
- 自动执行卖出信号
- 记录交易订单

**风控：**
- 单只股票最大仓位：总资金的20%
- 总仓位限制：总资金的80%
- 避免重复买入

### 3️⃣ 止盈监控器（ProfitMonitor）

**功能：**
- 每30秒检查所有持仓
- 计算盈亏比例
- 触发止盈/止损时生成卖出信号

**策略：**
- **止盈**：盈利 >= 10% 时卖出
- **止损**：亏损 >= -5% 时卖出
- **移动止损**（可选）：从最高价回撤 >= 3% 时卖出

---

## 🎮 使用方式

### 完整系统（推荐）

运行所有3个模块：

```bash
python scripts/run_auto_trading.py
```

### 指定监控股票

```bash
python scripts/run_auto_trading.py --symbols 0700.HK 9988.HK 0941.HK
```

### 仅运行资金流入监控

```bash
python scripts/run_auto_trading.py --money-flow-only
```

### 仅运行自动交易执行器

```bash
python scripts/run_auto_trading.py --trader-only
```

### 仅运行止盈监控器

```bash
python scripts/run_auto_trading.py --profit-only
```

---

## 📈 运行示例

```
================================================================================
🚀 自动交易系统启动
================================================================================
交易引擎: local_paper
执行间隔: 30秒
止盈策略: 10.0%
止损策略: -5.0%
资金流入监控间隔: 60秒
成交量倍数阈值: 3.0x
成交额倍数阈值: 3.0x
价格变动阈值: 5.0%
================================================================================
模式: 完整自动交易系统
启动3个模块:
  1. 资金流入监控 - 检测资金流入并生成买入信号
  2. 自动交易执行器 - 执行买入/卖出信号
  3. 止盈监控器 - 监控持仓并生成卖出信号
================================================================================
✅ 启动线程: MoneyFlowMonitor
✅ 启动线程: AutoTrader
✅ 启动线程: ProfitMonitor
================================================================================
所有模块已启动，按 Ctrl+C 停止
================================================================================

[14:30:00] 执行监控...
开始监控 50 只股票...

🚨 资金流入告警: 0700.HK - volume_surge | 成交量倍数: 5.20x | 成交额倍数: 4.80x
✅ 创建买入信号: 0700.HK (腾讯控股) | 强度: 0.50 | 价格: 350.00

[14:30:15] 检查待执行信号...
发现 1 个待执行信号
处理信号: 0700.HK BUY | 来源: money_flow_monitor
执行买入: 0700.HK @ 350.00
✅ 买入成功: 0700.HK

[14:35:00] 检查持仓...
检查 1 个持仓...

[15:00:00] 检查持仓...
检查 1 个持仓...
🔔 0700.HK 触发卖出: 止盈: 收益率10.50% >= 10.00%
✅ 创建卖出信号: 0700.HK | 价格: 387.00 | 盈亏: +10.50%

[15:00:15] 检查待执行信号...
发现 1 个待执行信号
处理信号: 0700.HK SELL | 来源: profit_monitor
执行卖出: 0700.HK @ 387.00 x 100
✅ 卖出成功: 0700.HK
```

---

## ⚙️ 配置参数详解

### 资金流入监控

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `enabled` | false | 是否启用监控 |
| `auto_trade` | false | 是否自动生成买入信号（重要！） |
| `send_email` | false | 是否发送邮件通知 |
| `interval` | 60 | 监控间隔（秒） |
| `volume_ratio_threshold` | 3.0 | 成交量倍数阈值 |
| `turnover_ratio_threshold` | 3.0 | 成交额倍数阈值 |
| `price_change_threshold` | 0.05 | 价格变动阈值（5%） |

### 自动交易

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `enabled` | false | 是否启用自动交易 |
| `engine_type` | local_paper | 交易引擎类型 |
| `execution_interval` | 30 | 执行间隔（秒） |
| `take_profit.enabled` | true | 是否启用止盈 |
| `take_profit.target_profit_pct` | 0.10 | 目标利润（10%） |
| `stop_loss.enabled` | true | 是否启用止损 |
| `stop_loss.stop_loss_pct` | -0.05 | 止损比例（-5%） |
| `trailing_stop.enabled` | false | 是否启用移动止损 |
| `trailing_stop.trailing_stop_pct` | 0.03 | 移动止损比例（3%） |

---

## 🔧 策略调整

### 激进策略（高频交易）

```yaml
money_flow_monitor:
  interval: 30                     # 30秒监控一次
  volume_ratio_threshold: 2.0      # 降低阈值，更容易触发
  turnover_ratio_threshold: 2.0

auto_trading:
  execution_interval: 15           # 15秒执行一次
  take_profit:
    target_profit_pct: 0.05        # 5%止盈
  stop_loss:
    stop_loss_pct: -0.03           # -3%止损
```

### 稳健策略（中长线）

```yaml
money_flow_monitor:
  interval: 300                    # 5分钟监控一次
  volume_ratio_threshold: 5.0      # 提高阈值，减少误触发
  turnover_ratio_threshold: 5.0

auto_trading:
  execution_interval: 60           # 1分钟执行一次
  take_profit:
    target_profit_pct: 0.20        # 20%止盈
  stop_loss:
    stop_loss_pct: -0.10           # -10%止损
  trailing_stop:
    enabled: true                  # 启用移动止损
    trailing_stop_pct: 0.05        # 5%移动止损
```

---

## ⚠️ 重要提示

### 1. 模拟交易 vs 真实交易

**模拟交易（local_paper）：**
- ✅ 安全，不会真实下单
- ✅ 适合测试策略
- ✅ 数据保存在本地数据库

**真实交易（longport）：**
- ⚠️ 会真实下单，有资金风险
- ⚠️ 需要LongPort账户和API权限
- ⚠️ 建议先用模拟交易测试

### 2. 风险控制

- ✅ 设置合理的止盈止损比例
- ✅ 控制单只股票仓位（默认20%）
- ✅ 控制总仓位（默认80%）
- ✅ 定期检查交易记录
- ✅ 避免在重大新闻/公告前后交易

### 3. 监控建议

- ✅ 定期查看日志文件：`logs/longport_quant.log`
- ✅ 定期检查持仓和订单
- ✅ 定期备份数据库
- ✅ 监控API调用频率，避免超限

---

## 📊 数据库表

系统会使用以下数据库表：

- `minute_data`：分钟K线数据
- `money_flow_alerts`：资金流入告警记录
- `trading_signals`：交易信号
- `orders`：订单记录
- `executions`：成交记录
- `positions`：持仓记录

---

## 🔍 故障排查

### Q1: 系统启动失败

**A:** 检查配置：
```bash
# 确保以下配置都为 true
money_flow_monitor.enabled = true
money_flow_monitor.auto_trade = true
auto_trading.enabled = true
```

### Q2: 没有生成买入信号

**A:** 可能原因：
1. 没有股票触发资金流入条件
2. 阈值设置过高，降低阈值试试
3. 监控股票列表为空

### Q3: 买入信号未执行

**A:** 检查：
1. 自动交易执行器是否正常运行
2. 是否已持有该股票
3. 是否有足够资金

### Q4: 没有生成卖出信号

**A:** 检查：
1. 持仓是否达到止盈/止损条件
2. 止盈止损策略是否启用
3. 价格数据是否更新

---

## 📚 相关文档

- **资金流入监控指南**：`README_MONEY_FLOW_MONITOR.md`
- **详细使用指南**：`MONEY_FLOW_MONITOR_GUIDE.md`
- **配置文件**：`config/config.yaml`

---

## 🎯 下一步

1. **优化策略参数**：根据回测结果调整阈值
2. **添加更多策略**：结合技术指标、基本面等
3. **风险管理**：设置最大亏损、最大回撤等
4. **性能监控**：记录策略表现，持续优化

---

**投资有风险，入市需谨慎！自动交易系统仅供学习研究，不构成投资建议。**

