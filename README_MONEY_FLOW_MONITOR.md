# 📊 资金流入监控系统

## 🎯 功能简介

资金流入监控系统是一个**分钟级别**的实时监控工具，能够自动检测股票市场中的大量资金流入情况，并通过邮件及时提醒投资者。

### ✨ 核心特性

- ✅ **分钟级别监控**：每分钟获取股票实时行情，及时发现资金异动
- ✅ **智能告警**：自动计算成交量、成交额倍数，识别异常资金流入
- ✅ **邮件通知**：检测到大量资金涌入时，自动发送邮件提醒
- ✅ **自动筛选**：自动监控高分股票，也可手动指定监控列表
- ✅ **数据存储**：保存分钟数据和告警记录，便于后续分析
- ✅ **去重机制**：同一股票5分钟内只发送一次告警，避免重复打扰

---

## 🚀 快速开始（3步）

### 第1步：配置邮件通知

编辑 `config/config.yaml`，配置您的邮箱：

```yaml
notification:
  email:
    enabled: true
    smtp_server: smtp.gmail.com      # Gmail用户
    smtp_port: 587
    username: your_email@gmail.com
    password: your_app_password      # Gmail需要使用"应用专用密码"
    from_addr: your_email@gmail.com
    to_addrs:
      - recipient@example.com
```

**其他邮箱配置请参考：** `config/email_config_example.yaml`

### 第2步：启用监控

编辑 `config/config.yaml`，启用资金流入监控：

```yaml
money_flow_monitor:
  enabled: true                      # 启用监控
  interval: 60                       # 监控间隔（秒）
  volume_ratio_threshold: 3.0        # 成交量倍数阈值
  turnover_ratio_threshold: 3.0      # 成交额倍数阈值
  price_change_threshold: 0.05       # 价格变动阈值（5%）
```

### 第3步：启动监控

运行快速启动脚本：

```bash
cd longport-quant-system
python scripts/quick_start_monitor.py
```

脚本会自动：
1. ✅ 检查配置是否正确
2. ✅ 测试邮件发送（可选）
3. ✅ 检查监控列表
4. ✅ 启动监控

---

## 📖 详细使用说明

### 方式1：自动监控高分股票

系统会自动从最新选股结果中选择评分>=70的股票：

```bash
python scripts/monitor_money_flow.py
```

### 方式2：手动指定监控股票

```bash
python scripts/monitor_money_flow.py --symbols 0700.HK 9988.HK 0941.HK
```

### 方式3：自定义监控间隔

```bash
python scripts/monitor_money_flow.py --interval 120  # 2分钟
```

### 测试邮件配置

```bash
python scripts/monitor_money_flow.py --test-email
```

---

## 📧 告警邮件示例

当检测到资金流入时，您将收到如下邮件：

**主题：** 🚨 资金流入告警 - 2025-10-23 14:30:00

| 股票代码 | 股票名称 | 告警类型 | 当前价格 | 价格变动 | 成交量倍数 | 成交额倍数 | 告警时间 |
|---------|---------|---------|---------|---------|-----------|-----------|---------|
| 0700.HK | 腾讯控股 | 成交量激增 | ¥350.00 | +3.50% | **5.2x** | **4.8x** | 14:30:00 |
| 9988.HK | 阿里巴巴 | 综合异动 | ¥85.00 | +2.10% | **3.5x** | **3.2x** | 14:31:00 |

---

## ⚙️ 配置参数说明

### 监控参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `enabled` | false | 是否启用监控 |
| `interval` | 60 | 监控间隔（秒），建议60-300 |
| `lookback_minutes` | 30 | 回溯时间（分钟），用于计算平均值 |
| `volume_ratio_threshold` | 3.0 | 成交量倍数阈值 |
| `turnover_ratio_threshold` | 3.0 | 成交额倍数阈值 |
| `price_change_threshold` | 0.05 | 价格变动阈值（5%） |

### 告警触发条件

系统会在以下情况下触发告警：

1. **成交量激增**：当前成交量 >= 平均成交量 × 3.0
2. **成交额激增**：当前成交额 >= 平均成交额 × 3.0
3. **价格异动**：价格变动 >= 5%
4. **综合异动**：成交量和成交额都超过阈值的80%

### 灵敏度调整

- **高灵敏度**（更多告警）：
  ```yaml
  volume_ratio_threshold: 2.0
  turnover_ratio_threshold: 2.0
  price_change_threshold: 0.03  # 3%
  ```

- **低灵敏度**（更少告警）：
  ```yaml
  volume_ratio_threshold: 5.0
  turnover_ratio_threshold: 5.0
  price_change_threshold: 0.08  # 8%
  ```

---

## 🗄️ 数据库表

系统会自动创建以下表：

### 1. minute_data（分钟数据表）

存储分钟级别的K线数据，用于计算资金流入指标。

### 2. money_flow_alerts（告警记录表）

存储所有告警记录，包括：
- 告警时间
- 告警类型
- 成交量/成交额倍数
- 价格变动
- 是否已发送邮件

---

## 🔧 常见问题

### Q1: 邮件发送失败怎么办？

**A:** 请检查：
1. Gmail用户需要使用"应用专用密码"，不是登录密码
2. QQ/163邮箱需要使用"授权码"
3. SMTP服务器和端口是否正确
4. 网络连接是否正常

详细配置说明：`config/email_config_example.yaml`

### Q2: 监控列表为空怎么办？

**A:** 请先运行选股分析：
```bash
python scripts/run_stock_selection.py --market CN --min-score 50
```

或手动指定监控股票：
```bash
python scripts/monitor_money_flow.py --symbols 0700.HK 9988.HK
```

### Q3: 没有收到告警邮件？

**A:** 可能原因：
1. 没有股票触发告警条件（成交量/成交额未达到阈值）
2. 邮件配置未启用
3. 邮件被拦截（检查垃圾邮件文件夹）
4. 告警去重（同一股票5分钟内只发送一次）

### Q4: API调用频率限制？

**A:** 增加监控间隔：
```bash
python scripts/monitor_money_flow.py --interval 300  # 5分钟
```

---

## 📈 使用建议

### 1. 监控间隔设置

- **激进型**：60秒（1分钟），适合短线交易
- **稳健型**：180秒（3分钟），适合中短线交易
- **保守型**：300秒（5分钟），适合中长线交易

### 2. 监控时间

建议只在交易时间内运行：
- **A股**：09:30-11:30, 13:00-15:00
- **港股**：09:30-12:00, 13:00-16:00

### 3. 监控股票数量

建议监控20-50只股票，太多会增加API调用频率。

---

## 📚 相关文档

- **详细使用指南**：`MONEY_FLOW_MONITOR_GUIDE.md`
- **邮件配置示例**：`config/email_config_example.yaml`
- **API文档**：`API_RATE_LIMIT_GUIDE.md`

---

## ⚠️ 风险提示

1. **资金流入不等于上涨**：大量资金流入可能是主力出货
2. **虚假信号**：短期成交量激增可能是偶然事件
3. **延迟问题**：分钟数据有一定延迟
4. **API限制**：频繁调用可能触发限流

**投资有风险，入市需谨慎！**

---

## 🎯 下一步

1. **优化阈值**：根据历史告警记录，调整阈值参数
2. **策略整合**：将资金流入信号整合到交易策略
3. **多维度监控**：结合技术指标、新闻舆情等
4. **自动交易**：基于资金流入信号自动下单（需谨慎）

---

## 📞 技术支持

如有问题，请查看：
- 详细文档：`MONEY_FLOW_MONITOR_GUIDE.md`
- 配置示例：`config/email_config_example.yaml`
- 日志文件：`logs/longport_quant.log`

