# 长桥证券量化交易系统 - 安装使用指南

## 📋 目录

1. [系统要求](#系统要求)
2. [安装步骤](#安装步骤)
3. [API配置](#api配置)
4. [快速开始](#快速开始)
5. [常见问题](#常见问题)
6. [进阶使用](#进阶使用)

---

## 系统要求

### 硬件要求
- CPU: 2核心及以上
- 内存: 4GB及以上
- 硬盘: 10GB可用空间

### 软件要求
- **Python**: 3.7 或更高版本
- **操作系统**: Windows 10/11, macOS 10.14+, Linux (Ubuntu 18.04+)
- **数据库**: SQLite (默认) 或 PostgreSQL (可选)

---

## 安装步骤

### 1. 克隆或下载项目

```bash
# 如果使用Git
git clone <repository_url>
cd longport-quant-system

# 或直接下载ZIP并解压
```

### 2. 创建Python虚拟环境（推荐）

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. 安装依赖包

#### 方法1：使用pip（推荐）

```bash
pip install -r requirements.txt
```

#### 方法2：手动安装核心依赖

```bash
# 核心依赖
pip install longport>=3.0.14
pip install Flask>=2.3.0
pip install SQLAlchemy>=2.0.0
pip install pandas>=2.0.0
pip install numpy>=1.24.0
pip install PyYAML>=6.0
pip install loguru>=0.7.0
```

### 4. 安装TA-Lib（技术分析库）

TA-Lib需要先安装C库，然后再安装Python包。

#### Windows:

1. 下载预编译的wheel文件：
   - 访问 https://www.lfd.uci.edu/~gohlke/pythonlibs/#ta-lib
   - 下载对应Python版本的whl文件（如 TA_Lib‑0.4.28‑cp311‑cp311‑win_amd64.whl）

2. 安装：
```bash
pip install TA_Lib‑0.4.28‑cp311‑cp311‑win_amd64.whl
```

#### macOS:

```bash
# 使用Homebrew安装C库
brew install ta-lib

# 安装Python包
pip install TA-Lib
```

#### Linux (Ubuntu/Debian):

```bash
# 安装依赖
sudo apt-get update
sudo apt-get install build-essential wget

# 下载并编译TA-Lib
wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz
tar -xzf ta-lib-0.4.0-src.tar.gz
cd ta-lib/
./configure --prefix=/usr
make
sudo make install

# 安装Python包
pip install TA-Lib
```

**注意**: 如果TA-Lib安装失败，可以使用替代方案 `pandas-ta`:

```bash
pip install pandas-ta
```

---

## API配置

### 1. 申请长桥证券API权限

1. 访问 [长桥开发者平台](https://open.longportapp.com)
2. 注册并登录账号
3. 进入"开发者中心"
4. 完成开发者认证
5. 创建应用，获取：
   - **App Key**
   - **App Secret**
   - **Access Token**

### 2. 配置API密钥

#### 方法1：修改配置文件（简单）

编辑 `config/api_config.yaml`:

```yaml
longport:
  app_key: "your_app_key_here"
  app_secret: "your_app_secret_here"
  access_token: "your_access_token_here"
  environment: production
  quote_level: 1
  language: zh-CN
```

#### 方法2：使用环境变量（推荐，更安全）

**Windows (PowerShell):**
```powershell
$env:LONGPORT_APP_KEY="your_app_key"
$env:LONGPORT_APP_SECRET="your_app_secret"
$env:LONGPORT_ACCESS_TOKEN="your_access_token"
```

**Windows (CMD):**
```cmd
set LONGPORT_APP_KEY=your_app_key
set LONGPORT_APP_SECRET=your_app_secret
set LONGPORT_ACCESS_TOKEN=your_access_token
```

**macOS/Linux:**
```bash
export LONGPORT_APP_KEY="your_app_key"
export LONGPORT_APP_SECRET="your_app_secret"
export LONGPORT_ACCESS_TOKEN="your_access_token"
```

**永久设置（添加到 ~/.bashrc 或 ~/.zshrc）:**
```bash
echo 'export LONGPORT_APP_KEY="your_app_key"' >> ~/.bashrc
echo 'export LONGPORT_APP_SECRET="your_app_secret"' >> ~/.bashrc
echo 'export LONGPORT_ACCESS_TOKEN="your_access_token"' >> ~/.bashrc
source ~/.bashrc
```

---

## 快速开始

### 1. 初始化数据库

```bash
python scripts/init_database.py
```

**预期输出:**
```
============================================================
初始化数据库
============================================================
2025-10-07 10:00:00 | INFO | 使用SQLite数据库: data/longport_quant.db
2025-10-07 10:00:00 | INFO | 创建数据库表...
2025-10-07 10:00:00 | INFO | 数据库表创建成功
============================================================
数据库初始化完成！
============================================================
```

### 2. 获取股票列表

```bash
# 获取港股列表
python scripts/fetch_stock_list.py --market HK

# 获取美股列表
python scripts/fetch_stock_list.py --market US
```

**注意**: 这个脚本会获取您的自选股列表。如需获取完整市场股票列表，需要根据长桥API文档调整代码。

### 3. 启动Web服务器

```bash
python run.py
```

**预期输出:**
```
============================================================
长桥证券量化交易系统启动中...
============================================================
2025-10-07 10:00:00 | INFO | 加载配置文件成功: config/config.yaml
2025-10-07 10:00:00 | INFO | 加载API配置文件成功: config/api_config.yaml
2025-10-07 10:00:00 | INFO | 初始化数据库...
2025-10-07 10:00:00 | INFO | 使用SQLite数据库: data/longport_quant.db
2025-10-07 10:00:00 | INFO | 初始化长桥API客户端...
2025-10-07 10:00:00 | INFO | 长桥API配置初始化成功
2025-10-07 10:00:00 | INFO | 启动Web服务器...
2025-10-07 10:00:00 | INFO | Web服务器启动成功: http://0.0.0.0:5000
============================================================
 * Running on http://0.0.0.0:5000
```

### 4. 访问Web界面

打开浏览器，访问：
```
http://localhost:5000
```

---

## 常见问题

### Q1: 安装依赖时出现错误

**A**: 
1. 确保Python版本 >= 3.7
2. 升级pip: `pip install --upgrade pip`
3. 如果是网络问题，使用国内镜像:
   ```bash
   pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
   ```

### Q2: TA-Lib安装失败

**A**: 
1. 使用替代方案 `pandas-ta`:
   ```bash
   pip install pandas-ta
   ```
2. 修改代码中的技术指标计算部分，使用pandas-ta替代TA-Lib

### Q3: 长桥API连接失败

**A**: 
1. 检查API密钥是否正确配置
2. 确认网络连接正常
3. 检查API权限是否已开通
4. 查看日志文件 `logs/longport_quant.log` 获取详细错误信息

### Q4: 数据库连接错误

**A**: 
1. 确保 `data/` 目录存在且有写入权限
2. 如果使用PostgreSQL，检查数据库服务是否启动
3. 检查 `config/config.yaml` 中的数据库配置

### Q5: Web服务器启动失败（端口被占用）

**A**: 
修改 `config/config.yaml` 中的端口号:
```yaml
web:
  port: 5001  # 改为其他端口
```

---

## 进阶使用

### 1. 使用PostgreSQL数据库

编辑 `config/config.yaml`:

```yaml
database:
  type: postgresql
  postgresql:
    host: localhost
    port: 5432
    database: longport_quant
    user: postgres
    password: your_password
```

安装PostgreSQL驱动:
```bash
pip install psycopg2-binary
```

### 2. 配置定时任务

系统支持定时任务，编辑 `config/config.yaml`:

```yaml
scheduler:
  enabled: true
  tasks:
    - name: update_stock_list
      schedule: "0 0 * * *"  # 每天0点
      enabled: true
```

### 3. 自定义评分权重

编辑 `config/config.yaml`:

```yaml
analysis:
  scoring_weights:
    technical_indicators: 0.35  # 提高技术指标权重
    volume_analysis: 0.30
    trend_analysis: 0.25
    pattern_recognition: 0.10   # 降低形态识别权重
```

### 4. 启用实时行情

编辑 `config/config.yaml`:

```yaml
data_collection:
  realtime:
    enabled: true
    reconnect_interval: 5
```

---

## 🎯 下一步

1. **数据采集**: 运行 `scripts/fetch_historical_data.py` 获取历史数据
2. **技术分析**: 开发技术指标计算模块
3. **选股策略**: 实现选股评分引擎
4. **回测系统**: 验证策略效果
5. **可视化**: 完善Web界面，添加图表展示

---

## 📞 获取帮助

- **长桥API文档**: https://open.longportapp.com/docs
- **项目Issues**: 提交问题和建议
- **日志文件**: `logs/longport_quant.log`

---

## ⚠️ 免责声明

本系统仅供学习和研究使用，不构成任何投资建议。股市有风险，投资需谨慎。

