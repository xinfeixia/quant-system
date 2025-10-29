# 🚀 长桥量化系统 - 功能说明

## 📋 目录

- [核心功能](#核心功能)
- [Web界面](#web界面)
- [命令行工具](#命令行工具)
- [API接口](#api接口)
- [使用指南](#使用指南)

---

## 🎯 核心功能

### 1. 数据采集
- ✅ 支持港股、美股、A股数据
- ✅ 历史K线数据获取（多周期）
- ✅ 实时行情推送
- ✅ 股票基本信息

### 2. 技术分析
- ✅ 20+ 技术指标计算
  - 趋势指标：MA、EMA、MACD
  - 震荡指标：RSI、KDJ
  - 波动指标：布林带、ATR
  - 成交量指标：OBV、成交量均线
- ✅ K线形态识别
- ✅ 支持自定义参数

### 3. 智能选股 ⭐
- ✅ 多维度评分系统（100分制）
  - 技术指标评分（30分）
  - 量价分析评分（25分）
  - 趋势分析评分（25分）
  - 形态识别评分（20分）
- ✅ 自动筛选Top 50股票
- ✅ 支持自定义最低分数
- ✅ 生成详细评分报告

### 4. 数据可视化
- ✅ 交互式K线图表
- ✅ 技术指标叠加显示
- ✅ 缩放、拖拽、十字光标
- ✅ 选股结果展示
- ✅ 股票对比分析

### 5. 数据导出
- ✅ 导出为Excel（.xlsx）
- ✅ 导出为CSV
- ✅ 网页端一键导出

### 6. 定时任务
- ✅ 每日自动选股
- ✅ 自动导出报告
- ✅ 可配置运行时间

---

## 🌐 Web界面

### 访问地址
```
http://localhost:5000
```

### 页面列表

#### 1. 首页 `/`
- 📊 数据统计概览
- ⚡ 快速操作入口
- 🎯 功能模块导航

#### 2. 选股结果 `/selections`
- 🏆 Top 50 股票排行榜
- 📈 多维度评分展示
- 🥇🥈🥉 前三名特殊标识
- 📊 评分进度条可视化
- 📥 一键导出CSV
- 🔍 点击查看K线详情

#### 3. K线图表 `/kline`
- 📈 交互式K线图
- 📊 技术指标叠加（MACD、RSI、KDJ）
- 🔍 缩放、拖拽、十字光标
- 📋 实时指标数据显示

#### 4. 股票对比 `/compare`
- 📊 多股票对比（最多5只）
- 📈 价格走势对比图
- 📉 技术指标对比图
- 📋 指标数据对比表

---

## 💻 命令行工具

### 1. 数据采集

#### 导入股票列表
```bash
python scripts/fetch_stock_list.py --market HK
```

#### 获取历史数据
```bash
# 单只股票
python scripts/fetch_historical_data.py --symbol 0700.HK

# 批量获取
python scripts/fetch_historical_data.py --batch --market HK

# 指定时间范围
python scripts/fetch_historical_data.py --symbol 0700.HK --days 365
```

### 2. 技术指标计算

```bash
# 单只股票
python scripts/calculate_indicators.py --symbol 0700.HK

# 批量计算
python scripts/calculate_indicators.py --batch --market HK
```

### 3. 智能选股

```bash
# 选出Top 50
python scripts/run_stock_selection.py --market HK --top 50

# 设置最低分数
python scripts/run_stock_selection.py --market HK --min-score 60 --top 100
```

### 4. 导出结果

```bash
# 导出为Excel
python scripts/export_selections.py --market HK

# 指定输出文件
python scripts/export_selections.py --market HK --output results.xlsx
```

### 5. 定时任务

```bash
# 运行一次
python scripts/daily_selection.py

# 启动定时调度器
python scripts/daily_selection.py --schedule
```

### 6. 数据检查

```bash
# 查看数据统计
python scripts/check_data.py

# 统计股票数量
python scripts/count_stocks.py
```

---

## 🔌 API接口

### 基础URL
```
http://localhost:5000/api
```

### 接口列表

#### 1. 健康检查
```
GET /api/health
```

#### 2. 股票列表
```
GET /api/stocks?market=HK&page=1&per_page=20
```

#### 3. 股票详情
```
GET /api/stock/{symbol}
```

#### 4. K线数据
```
GET /api/stock/{symbol}/kline?days=90
```

#### 5. 选股结果
```
GET /api/selections?market=HK
```

---

## 📖 使用指南

### 快速开始

#### 1. 启动Web服务
```bash
python run.py
```

#### 2. 访问首页
```
http://localhost:5000
```

#### 3. 查看选股结果
```
http://localhost:5000/selections
```

### 完整工作流程

#### 步骤1：导入股票数据
```bash
# 导入港股列表
python scripts/fetch_stock_list.py --market HK

# 获取历史数据
python scripts/fetch_historical_data.py --batch --market HK
```

#### 步骤2：计算技术指标
```bash
python scripts/calculate_indicators.py --batch --market HK
```

#### 步骤3：运行选股分析
```bash
python scripts/run_stock_selection.py --market HK --top 50
```

#### 步骤4：查看结果
- 网页查看：`http://localhost:5000/selections`
- 导出Excel：`python scripts/export_selections.py --market HK`

### 高级功能

#### 1. 股票对比
1. 访问 `http://localhost:5000/compare`
2. 输入股票代码（如：0700.HK）
3. 点击"添加股票"
4. 添加2-5只股票
5. 点击"开始对比"

#### 2. 定时自动选股
```bash
# 启动定时任务（每天9:00和15:30运行）
python scripts/daily_selection.py --schedule
```

#### 3. 自定义评分参数
编辑 `analysis/scoring_engine.py` 文件，调整各维度权重和评分逻辑。

---

## 🎨 界面特性

### 选股结果页面
- 🏆 **排行榜展示**：清晰的排名和评分
- 🥇 **前三名标识**：金银铜牌特殊显示
- 📊 **进度条可视化**：直观的分数展示
- 🏷️ **评级标签**：优秀/良好/中等/一般
- 📈 **点击查看详情**：直接跳转K线图
- 📥 **一键导出**：导出CSV文件

### K线图表页面
- 📈 **蜡烛图**：完整的OHLC数据
- 📊 **技术指标**：MACD、RSI、KDJ叠加显示
- 🔍 **交互功能**：缩放、拖拽、十字光标
- 📋 **实时数据**：最新指标数值显示
- 🎨 **美观设计**：专业的金融图表样式

### 股票对比页面
- ➕ **灵活添加**：支持添加2-5只股票
- 📊 **多维对比**：价格、技术指标全面对比
- 📈 **图表展示**：走势图、RSI图等
- 📋 **数据表格**：详细的指标对比表

---

## 📊 数据说明

### 评分维度

#### 1. 技术指标评分（30分）
- MACD金叉/死叉
- RSI超买超卖
- KDJ信号

#### 2. 量价分析评分（25分）
- 放量上涨
- 成交量趋势

#### 3. 趋势分析评分（25分）
- 均线排列（多头/空头）
- 价格位置（布林带）

#### 4. 形态识别评分（20分）
- K线形态（大阳线、锤子线等）
- 突破信号

### 评级标准
- **优秀**：80分以上
- **良好**：70-80分
- **中等**：60-70分
- **一般**：50-60分

---

## 🔧 配置说明

### API配置
编辑 `config/api_config.yaml`：
```yaml
longport:
  app_key: "your_app_key"
  app_secret: "your_app_secret"
  access_token: "your_access_token"
```

### 定时任务配置
编辑 `scripts/daily_selection.py`：
```python
# 修改运行时间
schedule.every().day.at("09:00").do(daily_selection_task)
schedule.every().day.at("15:30").do(daily_selection_task)
```

---

## 📝 注意事项

1. **API限制**：注意长桥API的调用频率限制
2. **数据更新**：建议每日收盘后更新数据
3. **评分调整**：可根据实际情况调整评分权重
4. **浏览器兼容**：推荐使用Chrome、Edge等现代浏览器

---

## 🚀 下一步计划

- [ ] 回测系统
- [ ] 实时监控和预警
- [ ] 策略编辑器
- [ ] 移动端适配
- [ ] 更多技术指标
- [ ] AI选股模型

---

## 📞 技术支持

如有问题，请查看：
- 项目文档：`README.md`
- 安装指南：`INSTALL_GUIDE.md`
- 快速开始：`QUICKSTART.md`

---

**享受量化交易的乐趣！** 🎉

