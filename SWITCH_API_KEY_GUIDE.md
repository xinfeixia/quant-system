# 切换API Key绕过频率限制指南

## 💡 核心思路

如果长桥API的频率限制是基于**App Key**而非账户或IP，那么切换到新的App Key可以绕过限制。

---

## 🔍 限制机制分析

### 可能的限制方式

| 限制类型 | 是否可以通过换Key绕过 | 说明 |
|---------|---------------------|------|
| **基于App Key** | ✅ 可以 | 每个App Key独立计数 |
| **基于账户** | ❌ 不可以 | 同一账户下所有Key共享限制 |
| **基于IP地址** | ❌ 不可以 | 需要更换网络环境 |
| **混合限制** | ⚠️ 部分可以 | 取决于具体实现 |

### 如何判断？

**测试方法**: 使用新的App Key尝试获取数据

---

## 📋 准备工作

### 方案1: 同一账户创建新的App Key

**步骤**:
1. 登录长桥开放平台: https://open.longportapp.com
2. 进入"应用管理"
3. 创建新的应用或查看现有应用
4. 获取新的App Key、App Secret、Access Token

**优点**:
- 简单快速
- 使用同一账户

**缺点**:
- 如果限制是基于账户，无法绕过

---

### 方案2: 使用不同账户的App Key

**步骤**:
1. 注册新的长桥账户
2. 开通API权限
3. 创建应用获取凭证

**优点**:
- 更可能绕过限制
- 独立的配额

**缺点**:
- 需要额外账户
- 可能需要额外认证

---

## 🚀 操作步骤

### 步骤1: 测试新的API Key

运行测试脚本验证新Key是否可用：

```bash
python scripts/test_api_with_new_key.py
```

**交互式输入**:
```
请输入新的API凭证：

App Key: [输入新的App Key]
App Secret: [输入新的App Secret]
Access Token: [输入新的Access Token]
```

**测试结果**:
- ✅ 如果可以获取历史K线数据 → 继续下一步
- ❌ 如果仍然报301607错误 → 限制不是基于App Key

---

### 步骤2: 切换API配置

#### 方法A: 使用配置切换工具（推荐）

```bash
python scripts/switch_api_config.py
```

**操作流程**:
1. 选择 `2. 更新API凭证`
2. 输入新的App Key、App Secret、Access Token
3. 工具会自动备份旧配置并更新

#### 方法B: 手动编辑配置文件

1. **备份当前配置**:
   ```bash
   copy config\api_config.yaml config\api_config_backup.yaml
   ```

2. **编辑配置文件**:
   打开 `config/api_config.yaml`
   
   ```yaml
   longport:
     app_key: "新的App Key"
     app_secret: "新的App Secret"
     access_token: "新的Access Token"
   ```

3. **保存文件**

---

### 步骤3: 验证新配置

运行简单测试：

```bash
python scripts/test_a_stock_simple.py
```

**预期结果**:
- ✅ 可以获取历史K线数据
- ✅ 没有301607错误

---

### 步骤4: 开始获取A股数据

如果验证成功，开始获取数据：

```bash
# 先获取10只测试
python scripts/fetch_a_stocks_slowly.py --days 365 --delay 30 --limit 10
```

**如果成功**:
```bash
# 继续获取更多
python scripts/fetch_a_stocks_slowly.py --days 365 --delay 30 --start-from 10 --limit 20
```

---

## 📊 不同场景的策略

### 场景1: 新Key可以获取数据 ✅

**说明**: 限制是基于App Key的

**策略**:
1. 使用新Key快速获取所有A股数据
2. 建议仍然使用适当延迟（30-60秒/股票）
3. 避免再次触发限制

**执行**:
```bash
# 获取所有152只A股（约2-3小时）
python scripts/fetch_a_stocks_slowly.py --days 365 --delay 30 --limit 152
```

---

### 场景2: 新Key仍然受限 ❌

**说明**: 限制可能是基于账户或IP

**策略**:
1. 如果是同一账户的新Key → 尝试不同账户
2. 如果是不同账户 → 可能是IP限制，尝试更换网络
3. 或者等待限制恢复（6-12小时）

**建议**:
- 联系长桥客服了解限制机制
- 考虑使用其他数据源（Tushare、AkShare等）

---

## 🔄 多Key轮换策略

如果有多个可用的App Key，可以轮换使用：

### 策略A: 手动轮换

```bash
# 使用Key 1获取前50只
python scripts/switch_api_config.py  # 切换到Key 1
python scripts/fetch_a_stocks_slowly.py --days 365 --delay 30 --limit 50

# 使用Key 2获取接下来50只
python scripts/switch_api_config.py  # 切换到Key 2
python scripts/fetch_a_stocks_slowly.py --days 365 --delay 30 --start-from 50 --limit 50

# 使用Key 3获取最后52只
python scripts/switch_api_config.py  # 切换到Key 3
python scripts/fetch_a_stocks_slowly.py --days 365 --delay 30 --start-from 100 --limit 52
```

### 策略B: 自动轮换（高级）

可以开发一个脚本自动在多个Key之间轮换，但需要注意：
- 每个Key的配额管理
- 避免过度使用导致封禁
- 遵守API使用条款

---

## ⚠️ 注意事项

### 1. 遵守服务条款

- 不要滥用API
- 遵守长桥的使用条款
- 合理使用频率限制

### 2. 数据一致性

- 确保使用的Key有相同的市场权限
- 验证数据质量
- 定期检查数据完整性

### 3. 安全性

- 妥善保管所有API凭证
- 不要在公开场合泄露
- 定期更换Access Token

### 4. 备份配置

- 每次切换前自动备份
- 保留所有配置的备份
- 可以随时恢复到之前的配置

---

## 🛠️ 工具使用说明

### test_api_with_new_key.py

**功能**: 测试新的API Key是否可以获取数据

**用法**:
```bash
python scripts/test_api_with_new_key.py
```

**输出**:
- 测试A股、港股、美股各一只
- 显示是否可以获取历史K线
- 给出下一步建议

---

### switch_api_config.py

**功能**: 管理API配置，支持切换和恢复

**用法**:
```bash
python scripts/switch_api_config.py
```

**功能菜单**:
1. 查看当前配置
2. 更新API凭证
3. 查看备份配置
4. 恢复备份配置
5. 退出

---

## 📈 预期效果

### 如果成功切换

**时间估算**:
- 152只A股 × 30秒/只 = **约76分钟**
- 加上数据处理时间 = **约1.5-2小时**

**数据量**:
- 每只股票约365条K线数据
- 总计约 **55,000条** 历史数据

**后续操作**:
```bash
# 计算技术指标
python scripts/calculate_indicators.py --batch --market CN

# 运行选股
python scripts/run_stock_selection.py --market CN --top 50

# 查看结果
http://localhost:5000/selections?market=CN
```

---

### 如果无法切换

**备选方案**:

1. **等待恢复** (推荐)
   - 等待6-12小时或明天
   - 使用原Key重试

2. **使用其他数据源**
   - Tushare: https://tushare.pro
   - AkShare: https://akshare.akfamily.xyz
   - 需要额外集成工作

3. **联系客服**
   - 咨询限制详情
   - 申请提升配额
   - 了解付费方案

---

## 💡 最佳实践

### 建议的获取策略

1. **测试优先**: 先用新Key测试1-2只股票
2. **小批量开始**: 成功后先获取10-20只
3. **监控状态**: 观察是否触发新的限制
4. **逐步扩大**: 确认稳定后增加批量
5. **保持延迟**: 即使可以快速获取，也保持30-60秒延迟

### 长期维护

1. **定期更新**: 每天更新最新数据
2. **配额管理**: 跟踪每个Key的使用情况
3. **备份数据**: 定期备份数据库
4. **监控日志**: 关注API错误和限制

---

## 📞 获取帮助

### 长桥开放平台

- 官网: https://open.longportapp.com
- 文档: https://open.longportapp.com/docs
- 客服: 通过官网联系

### 常见问题

**Q: 同一账户可以创建多个App吗？**
A: 可以，但限制可能是共享的

**Q: 不同账户的Key是否独立？**
A: 理论上是，但需要实际测试

**Q: 切换Key会影响已有数据吗？**
A: 不会，数据存储在本地数据库中

**Q: 可以同时使用多个Key吗？**
A: 可以，但需要手动切换配置

---

## 🎯 总结

### 立即尝试

1. ✅ 运行测试脚本: `python scripts/test_api_with_new_key.py`
2. ✅ 如果成功，切换配置: `python scripts/switch_api_config.py`
3. ✅ 开始获取数据: `python scripts/fetch_a_stocks_slowly.py`

### 如果不成功

1. ⏰ 等待6-12小时后重试
2. 📞 联系长桥客服
3. 🔄 考虑其他数据源

---

**祝您成功获取A股数据！** 🚀

