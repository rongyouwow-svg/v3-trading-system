# 🚨 V3 系统严重问题深度分析

**分析时间**: 2026-03-18 20:55  
**状态**: 🔴 **CRITICAL - 多个严重问题**

---

## 📋 当前告警汇总

| 告警 | 级别 | 状态 | 原因 |
|------|------|------|------|
| **AVAX 策略 FATAL** | 🔴 CRITICAL | 未修复 | 代码 bug + Supervisor 配置问题 |
| **ETH 持仓无止损** | 🔴 CRITICAL | 未修复 | 策略与执行器职责不清 |
| **账户余额 0** | 🟡 WARNING | API 问题 | 币安测试网 API 问题 |
| **UNI Strategy 未找到** | 🟡 WARNING | 未修复 | 3 策略脚本未运行 |
| **AVAX RSI 3.06** | 🟢 INFO | 正常 | RSI 超卖告警 |

---

## 🔍 深度分析：V3 系统架构问题

### 问题 1: 策略执行器 vs 策略内部止损 - 职责不清 ❌

**现象**:
- ETH 持仓 0.017 @ 2259.98 **无止损单**
- 策略代码有 `create_stop_loss()` 方法
- 执行器也有止损管理
- **两边都没创建止损单！**

**根本原因**:
```
V3 系统设计存在职责不清：

方案 A: 策略自己管理止损（strategy_template_v2.py）
  ✅ 优点：策略完全控制
  ❌ 缺点：容易忘记创建

方案 B: 执行器统一管理止损（strategy_executor.py）
  ✅ 优点：集中管理，不易遗漏
  ❌ 缺点：策略不知道止损状态

当前问题：
- 旧策略（rsi_1min_strategy.py）使用方案 A
- 新策略（eth_bb_rsi_strategy.py）使用方案 B
- **但 strategy_executor.py 的 start_strategy() 从未被调用！**
- **旧策略的 create_stop_loss() 可能失败但无错误处理！**
```

**修复方案**:
```python
# 统一使用方案 B：执行器管理止损
# 修改所有策略，使用 executor.start_strategy()

# 在策略启动时：
result = executor.start_strategy(
    symbol="ETHUSDT",
    strategy_name="eth_bb_rsi",
    leverage=3,
    amount_usd=300,
    stop_loss_pct=0.05,
    trailing_stop_pct=0.02
)

# executor 会自动：
# 1. 互斥检查
# 2. 设置杠杆
# 3. 开单
# 4. 创建止损单
# 5. 启动跟车止损
# 6. 注册策略
```

---

### 问题 2: 3 策略脚本未纳入 Supervisor 监控 ❌

**现象**:
- `start_top3_strategies.py` **没有被 Supervisor 管理**
- 脚本停止无告警
- 脚本崩溃无自动重启
- **ps aux | grep start_top3 无结果！**

**根本原因**:
```
V3 系统设计遗漏：
- 只监控了 Supervisor 管理的服务
- 遗漏了独立运行的脚本
- Service Monitor 的 MONITORED_SERVICES 列表没有 top3-strategies

监控盲点：
- 脚本运行状态未知
- 脚本崩溃无人知道
- 需要手动检查和重启
```

**修复方案**:
```bash
# 1. 添加到 Supervisor 配置
cat > supervisor/top3-strategies.conf << 'EOF'
[program:top3-strategies]
command=/root/.pyenv/versions/3.10.13/bin/python3 -u start_top3_strategies.py
directory=/root/.openclaw/workspace/quant/v3-architecture
autostart=true
autorestart=true
startretries=3
stderr_logfile=logs/top3-strategies_err.log
stdout_logfile=logs/top3-strategies_out.log
