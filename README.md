# 长桥证券量化交易分析系统

基于长桥证券（LongPort）OpenAPI的港股、美股量化交易分析系统。

## 📊 系统特点

- **多市场支持**：港股、美股、A股数据采集
- **实时行情**：支持实时行情订阅和推送
- **历史数据**：获取历史K线数据（日线、周线、月线等）
- **技术分析**：20+技术指标（MACD、KDJ、RSI、布林带等）
- **智能选股**：多维度评分系统
- **回测系统**：验证策略历史表现
- **Web可视化**：交互式图表和数据展示

## 🏗️ 项目结构

```
longport-quant-system/
├── config/                 # 配置文件
│   ├── config.yaml        # 主配置文件
│   └── api_config.yaml    # API密钥配置
├── data_collection/       # 数据采集模块
│   ├── __init__.py
│   ├── longport_client.py # 长桥API客户端
│   ├── quote_fetcher.py   # 行情数据获取
│   └── realtime_stream.py # 实时行情订阅
├── database/              # 数据库模块
│   ├── __init__.py
│   ├── models.py          # 数据模型
│   └── db_manager.py      # 数据库管理
├── analysis/              # 分析模块
│   ├── __init__.py
│   ├── technical_indicators.py  # 技术指标
│   ├── scoring_engine.py        # 评分引擎
│   └── pattern_recognition.py   # 形态识别
├── backtest/              # 回测模块
│   ├── __init__.py
│   ├── backtest_engine.py # 回测引擎
│   └── strategy.py        # 策略定义
├── web/                   # Web界面
│   ├── __init__.py
│   ├── app.py            # Flask应用
│   ├── routes.py         # 路由定义
│   └── templates/        # HTML模板
│       ├── base.html
│       ├── dashboard.html
│       ├── analysis.html
│       └── stock_detail.html
├── utils/                 # 工具模块
│   ├── __init__.py
│   ├── config_loader.py  # 配置加载
│   └── logger.py         # 日志工具
├── scripts/               # 脚本文件
│   ├── fetch_stock_list.py    # 获取股票列表
│   ├── fetch_historical_data.py # 获取历史数据
│   └── run_analysis.py        # 运行分析
├── logs/                  # 日志目录
├── data/                  # 数据目录
├── requirements.txt       # 依赖包
├── README.md             # 说明文档
└── run.py                # 主运行脚本
```

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置API密钥

访问 [长桥开发者平台](https://open.longportapp.com) 申请API权限，获取：
- App Key
- App Secret
- Access Token

编辑 `config/api_config.yaml`：

```yaml
longport:
  app_key: "your_app_key_here"
  app_secret: "your_app_secret_here"
  access_token: "your_access_token_here"
```

### 3. 初始化数据库

```bash
python scripts/init_database.py
```

### 4. 获取股票列表

```bash
# 获取港股列表
python scripts/fetch_stock_list.py --market HK

# 获取美股列表
python scripts/fetch_stock_list.py --market US
```

### 5. 获取历史数据

```bash
# 获取指定股票的历史数据
python scripts/fetch_historical_data.py --symbol 700.HK --days 365

# 批量获取
python scripts/fetch_historical_data.py --batch --market HK --limit 100
```

### 6. 运行选股分析

```bash
python scripts/run_analysis.py --market HK --top 50
```

### 7. 启动Web界面

```bash
python run.py
```

访问 http://localhost:5000 查看可视化界面

## 📈 功能说明

### 数据采集

- **股票列表**：获取港股、美股、A股的股票列表
- **历史K线**：日线、周线、月线、分钟线数据
- **实时行情**：WebSocket实时推送
- **基本信息**：股票名称、行业、市值等

### 技术分析

支持的技术指标：
- **趋势指标**：MA、EMA、MACD
- **震荡指标**：RSI、KDJ、CCI
- **波动指标**：布林带、ATR
- **成交量指标**：OBV、成交量MA

### 选股策略

多维度评分系统：
- **技术指标分**（30%）：MACD、KDJ、RSI等
- **量价分析分**（25%）：放量上涨、缩量下跌
- **趋势分析分**（25%）：上升趋势、突破信号
- **形态识别分**（20%）：经典K线形态

### 回测系统

- **策略回测**：验证选股策略历史表现
- **性能指标**：收益率、夏普比率、最大回撤
- **交易统计**：胜率、盈亏比、交易次数
- **可视化**：净值曲线、回撤曲线

## 🔧 配置说明

### config/config.yaml

```yaml
# 数据库配置
database:
  type: sqlite  # sqlite 或 postgresql
  path: data/longport_quant.db  # SQLite路径
  # PostgreSQL配置（可选）
  # host: localhost
  # port: 5432
  # database: longport_quant
  # user: postgres
  # password: your_password

# 数据采集配置
data_collection:
  markets:
    - HK  # 港股
    - US  # 美股
  update_interval: 3600  # 更新间隔（秒）
  batch_size: 50  # 批量获取数量

# 分析配置
analysis:
  technical_indicators:
    - MACD
    - KDJ
    - RSI
    - BOLL
  scoring_weights:
    technical: 0.30
    volume: 0.25
    trend: 0.25
    pattern: 0.20

# 回测配置
backtest:
  initial_capital: 1000000  # 初始资金
  commission: 0.0003  # 手续费率
  slippage: 0.001  # 滑点

# Web配置
web:
  host: 0.0.0.0
  port: 5000
  debug: false
```

## 📊 API限制

长桥OpenAPI的限制：
- **行情权限**：需要申请行情权限
- **请求频率**：根据账户等级有不同限制
- **数据延迟**：实时行情可能有延迟

详见：https://open.longportapp.com/docs

## ⚠️ 风险提示

- 本系统仅供学习和研究使用
- 不构成任何投资建议
- 股市有风险，投资需谨慎
- 请遵守相关法律法规

## 📝 开发计划

- [x] 项目框架搭建
- [x] 长桥API集成
- [x] 数据库设计
- [ ] 数据采集模块
- [ ] 技术分析模块
- [ ] 选股引擎
- [ ] 回测系统
- [ ] Web可视化
- [ ] 实时行情推送
- [ ] 策略优化

## 📄 许可证

MIT License

## 🤝 贡献

欢迎提交Issue和Pull Request！

## 📧 联系方式

如有问题，请提交Issue或联系开发者。

