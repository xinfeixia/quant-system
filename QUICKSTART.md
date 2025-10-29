# 快速开始指南

## 🚀 5分钟快速体验

### 前提条件

1. ✅ Python 3.7+ 已安装
2. ✅ 已申请长桥证券API权限（[申请地址](https://open.longportapp.com)）
3. ✅ 获得 App Key、App Secret、Access Token

---

## 步骤1: 安装依赖（2分钟）

### Windows用户

```powershell
# 创建虚拟环境
python -m venv venv
venv\Scripts\activate

# 安装核心依赖
pip install longport Flask SQLAlchemy pandas numpy PyYAML loguru Flask-CORS python-dateutil requests
```

### macOS/Linux用户

```bash
# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装核心依赖
pip install longport Flask SQLAlchemy pandas numpy PyYAML loguru Flask-CORS python-dateutil requests
```

**注意**: TA-Lib可以稍后安装，不影响系统启动。

---

## 步骤2: 配置API密钥（1分钟）

### 方法1: 使用环境变量（推荐）

**Windows (PowerShell):**
```powershell
$env:LONGPORT_APP_KEY="你的App Key"
$env:LONGPORT_APP_SECRET="你的App Secret"
$env:LONGPORT_ACCESS_TOKEN="你的Access Token"
```

**macOS/Linux:**
```bash
export LONGPORT_APP_KEY="你的App Key"
export LONGPORT_APP_SECRET="你的App Secret"
export LONGPORT_ACCESS_TOKEN="你的Access Token"
```

### 方法2: 修改配置文件

编辑 `config/api_config.yaml`:

```yaml
longport:
  app_key: "你的App Key"
  app_secret: "你的App Secret"
  access_token: "你的Access Token"
```

---

## 步骤3: 初始化数据库（30秒）

```bash
python scripts/init_database.py
```

**预期输出:**
```
============================================================
初始化数据库
============================================================
2025-10-07 10:00:00 | INFO | 使用SQLite数据库: data/longport_quant.db
2025-10-07 10:00:00 | INFO | 数据库表创建成功
============================================================
数据库初始化完成！
============================================================
```

---

## 步骤4: 启动系统（30秒）

```bash
python run.py
```

**预期输出:**
```
============================================================
长桥证券量化交易系统启动中...
============================================================
2025-10-07 10:00:00 | INFO | 长桥API配置初始化成功
2025-10-07 10:00:00 | INFO | Web服务器启动成功: http://0.0.0.0:5000
============================================================
 * Running on http://0.0.0.0:5000
```

---

## 步骤5: 访问Web界面（1分钟）

打开浏览器，访问:

```
http://localhost:5000
```

你将看到系统Dashboard，包含：
- 📊 数据采集模块
- 📈 技术分析模块
- 🎯 智能选股模块
- 🔄 回测系统模块

点击 **"测试API连接"** 按钮，验证长桥API是否配置成功。

---

## 🎯 下一步操作

### 1. 测试API连接

在Web界面点击 "测试API连接" 按钮，或访问:

```
http://localhost:5000/api/health
```

应该返回:
```json
{
  "status": "ok",
  "message": "长桥证券量化交易系统运行中"
}
```

### 2. 获取股票列表（可选）

```bash
# 获取港股列表
python scripts/fetch_stock_list.py --market HK

# 获取美股列表
python scripts/fetch_stock_list.py --market US
```

**注意**: 这个脚本会获取您的自选股列表。

### 3. 查看API文档

访问以下端点测试API:

- `GET /api/health` - 健康检查
- `GET /api/stocks?market=HK` - 获取港股列表
- `GET /api/stock/700.HK` - 获取腾讯控股详情
- `GET /api/selections` - 获取选股结果

---

## ❓ 常见问题

### Q: 安装依赖时出错

**A**: 使用国内镜像加速:
```bash
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple longport Flask SQLAlchemy pandas numpy PyYAML loguru Flask-CORS
```

### Q: API连接失败

**A**: 检查以下几点:
1. API密钥是否正确
2. 网络连接是否正常
3. 是否已开通行情权限
4. 查看日志文件 `logs/longport_quant.log`

### Q: 端口5000被占用

**A**: 修改 `config/config.yaml` 中的端口:
```yaml
web:
  port: 5001  # 改为其他端口
```

### Q: 数据库初始化失败

**A**: 
1. 确保有写入权限
2. 手动创建 `data/` 目录
3. 检查磁盘空间

---

## 📚 更多资源

- **详细安装指南**: [INSTALL_GUIDE.md](INSTALL_GUIDE.md)
- **项目总结**: [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)
- **完整文档**: [README.md](README.md)
- **长桥API文档**: https://open.longportapp.com/docs

---

## 🎉 恭喜！

你已经成功启动了长桥证券量化交易系统！

接下来可以:
1. 📊 开发数据采集模块，获取历史数据
2. 📈 实现技术指标计算
3. 🎯 开发选股策略
4. 🔄 构建回测系统
5. 💻 完善Web可视化界面

---

## ⚠️ 重要提示

- 本系统仅供学习和研究使用
- 不构成任何投资建议
- 股市有风险，投资需谨慎
- 请遵守相关法律法规

---

**祝你使用愉快！** 🚀📈

