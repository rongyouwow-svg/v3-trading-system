# 🛡️ v3.1 灾难恢复方案

**分析时间**: 2026-03-14 19:30  
**问题**: 程序退出/系统崩溃后如何恢复策略运行？

---

## 📊 当前持久化机制

### ✅ 已实现的持久化

| 数据类型 | 文件位置 | 更新频率 | 状态 |
|---------|---------|---------|------|
| **策略状态** | `logs/strategy_pids.json` | 每根 K 线 | ✅ 正常 |
| **监测数据** | `logs/live_test_monitor.json` | 30 秒 | ✅ 正常 |
| **交易记录** | 交易所 API | 实时 | ✅ 正常 |
| **持仓信息** | 交易所 API | 实时 | ✅ 正常 |
| **止损单** | 交易所 API | 实时 | ✅ 正常 |

### ❌ 缺失的持久化

| 数据类型 | 说明 | 影响 |
|---------|------|------|
| **RSI 历史数据** | 未持久化 | 重启后需重新计算 |
| **2 根 K 线确认状态** | waiting_confirmation 未保存 | 重启后丢失 |
| **分批建仓进度** | current_scale_index 未保存 | 重启后从头开始 |
| **止损单本地缓存** | stop_orders.json 为空 | 无法快速恢复 |

---

## 🔍 当前恢复能力分析

### 场景 1: 策略进程退出（Web 服务正常）

**影响**:
- ❌ 策略状态丢失（内存中）
- ✅ 持仓仍在交易所
- ✅ 止损单仍在交易所
- ❌ RSI 历史数据丢失
- ❌ 2 根 K 线确认状态丢失

**恢复流程**:
```bash
# 1. 重启策略
python3 scripts/start_all_strategies.py

# 2. 策略从交易所同步持仓
position = connector.get_positions(symbol)

# 3. 策略从策略状态文件恢复
if os.path.exists('logs/strategy_pids.json'):
    old_state = json.load(f)
    # 恢复部分状态
```

**问题**:
- ⚠️ 重新计算 RSI 需要历史 K 线
- ⚠️ 2 根 K 线确认状态丢失，可能误触发
- ⚠️ 分批建仓进度丢失，可能重复开仓

---

### 场景 2: Web 服务崩溃

**影响**:
- ❌ API 无法访问
- ❌ 策略进程可能仍在运行
- ✅ 持仓和止损单在交易所安全

**恢复流程**:
```bash
# supervisor 自动重启 Web 服务
supervisorctl restart web_dashboard

# 或自动重启脚本
./scripts/auto_restart.sh
```

**问题**:
- ⚠️ 策略进程可能成为孤儿进程
- ⚠️ 需要手动检查策略状态

---

### 场景 3: 系统崩溃重启

**影响**:
- ❌ 所有进程停止
- ✅ 持仓和止损单在交易所安全
- ❌ 所有内存状态丢失

**恢复流程**:
```bash
# 1. 系统启动后自动启动 supervisor
systemctl start supervisord

# 2. supervisor 启动 Web Dashboard
supervisorctl start web_dashboard

# 3. 手动启动策略
python3 scripts/start_all_strategies.py

# 4. 从交易所同步状态
positions = connector.get_positions()
stop_orders = connector.get_stop_orders()
```

**问题**:
- ⚠️ 需要手动启动策略
- ⚠️ RSI 历史数据完全丢失
- ⚠️ 可能重复开仓

---

## ✅ 建议的改进方案

### 方案 A: 增强状态持久化（推荐）

**实施内容**:

1. **保存完整策略状态**
```python
# 每根 K 线后保存
def save_state(self):
    state = {
        'symbol': self.symbol,
        'last_rsi': self.last_rsi,
        'waiting_confirmation': self.waiting_confirmation,
        'signal_rsi': self.signal_rsi,
        'position': self.position,
        'entry_price': float(self.entry_price),
        'current_scale_index': self.current_scale_index,  # 分批进度
        'scale_in_count': self.scale_in_count,
        'total_invested': self.total_invested,
        'last_update': datetime.now().isoformat()
    }
    
    with open(f'logs/strategy_{self.symbol}_state.json', 'w') as f:
        json.dump(state, f, indent=2)
```

2. **启动时恢复状态**
```python
def load_state(self):
    state_file = f'logs/strategy_{self.symbol}_state.json'
    
    if os.path.exists(state_file):
        with open(state_file, 'r') as f:
            state = json.load(f)
        
        self.last_rsi = state['last_rsi']
        self.waiting_confirmation = state['waiting_confirmation']
        self.current_scale_index = state['current_scale_index']
        # ... 恢复所有状态
        
        logger.info(f"✅ 策略状态已恢复：{self.symbol}")
    else:
        logger.info(f"ℹ️ 无历史状态，从头开始：{self.symbol}")
```

3. **从交易所同步持仓和止损单**
```python
def sync_from_exchange(self):
    # 同步持仓
    positions = self.connector.get_positions(self.symbol)
    if positions:
        self.position = 'LONG' if positions[0]['positionAmt'] > 0 else 'SHORT'
        self.entry_price = Decimal(positions[0]['entryPrice'])
    
    # 同步止损单
    stop_orders = self.connector.get_stop_orders(self.symbol)
    if stop_orders:
        logger.info(f"✅ 发现现有止损单：{len(stop_orders)} 个")
```

**优点**:
- ✅ 重启后快速恢复
- ✅ 保留分批建仓进度
- ✅ 保留 2 根 K 线确认状态
- ✅ 避免重复开仓

**缺点**:
- ⚠️ 需要修改策略代码
- ⚠️ 增加磁盘 I/O

---

### 方案 B: 自动启动脚本（简单）

**实施内容**:

1. **创建系统服务**
```ini
# /etc/systemd/system/quant-strategies.service
[Unit]
Description=大王量化策略服务
After=network.target

[Service]
Type=simple
User=admin
WorkingDirectory=/home/admin/.openclaw/workspace/quant/v3-architecture
ExecStart=/home/admin/.pyenv/versions/3.10.0/bin/python3 scripts/start_all_strategies.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

2. **启用服务**
```bash
sudo systemctl enable quant-strategies
sudo systemctl start quant-strategies
```

**优点**:
- ✅ 系统重启后自动启动
- ✅ 崩溃后自动重启
- ✅ 无需手动干预

**缺点**:
- ⚠️ 状态仍然丢失
- ⚠️ 可能重复开仓

---

### 方案 C: 混合方案（最佳）

**结合方案 A + B**:

1. **策略状态持久化** (方案 A)
2. **系统服务自动启动** (方案 B)
3. **从交易所同步状态** (通用)

**恢复流程**:
```bash
# 系统重启后
1. supervisor 自动启动 Web Dashboard
2. systemd 自动启动策略服务
3. 策略从文件恢复状态
4. 策略从交易所同步持仓和止损单
5. 继续正常运行
```

---

## 📝 实施建议

### 短期（立即实施）

1. ✅ **添加策略状态持久化**
   - 每根 K 线后保存状态
   - 启动时恢复状态

2. ✅ **添加系统服务**
   - 创建 systemd service
   - 启用自动启动

3. ✅ **添加恢复检查**
   - 启动时检查交易所持仓
   - 启动时检查交易所止损单

### 中期（1 周内）

1. ⏳ **完善状态持久化**
   - 保存 RSI 历史数据
   - 保存分批建仓进度

2. ⏳ **添加健康检查**
   - 定期检查策略状态
   - 自动恢复异常策略

### 长期（1 月内）

1. ⏳ **数据库持久化**
   - 使用 SQLite/PostgreSQL
   - 完整交易历史

2. ⏳ **分布式部署**
   - 主备策略进程
   - 自动故障转移

---

## 🎯 结论

### 当前状态

**问题**:
- ❌ 策略进程退出后状态丢失
- ❌ 系统重启后需手动启动策略
- ❌ 可能重复开仓

**安全**:
- ✅ 持仓在交易所安全
- ✅ 止损单在交易所安全

### 建议行动

**立即实施**:
1. 添加策略状态持久化（30 分钟）
2. 创建 systemd service（15 分钟）
3. 添加恢复检查（15 分钟）

**总工时**: 约 1 小时

**效果**:
- ✅ 系统重启后自动恢复
- ✅ 保留策略状态
- ✅ 避免重复开仓

---

**报告生成时间**: 2026-03-14 19:30  
**分析负责人**: AI Assistant  
**建议优先级**: P0（立即实施）
