# 🛡️ 监控系统深度优化方案

**创建时间**: 2026-03-16 10:15  
**问题**: 09:14 后监控失效 52 分钟  
**目标**: 确保监控 7×24 小时不间断运行

---

## 🔍 问题根因

### 1. 架构设计缺陷
```
当前设计:
监控系统 → 依赖 → Web API (端口 3000)
            ↓
        Web 服务挂 = 监控挂

问题设计:
监控系统 → 直连 → 币安 API
        ↓
    独立运行，不依赖 Web 服务
```

### 2. 无进程守护
```
当前：nohup python monitor.py &
问题：崩溃后不重启

解决：systemd 守护进程
```

### 3. 无健康检查
```
问题：监控自己挂了没人知道
解决：看门狗机制（watchdog）
```

### 4. 日志无轮转
```
问题：monitor_alerts.log → 2.3MB 单文件
解决：RotatingFileHandler（10MB/文件，保留 5 个）
```

---

## 🔧 实施方案

### 方案 1: 独立监控进程（最高优先级）

**修改**: `scripts/enhanced_monitor.py`

```python
# 不依赖 Web API，直连币安
import requests

class IndependentMonitor:
    def __init__(self):
        # 币安测试网 API
        self.binance_url = "https://testnet.binancefuture.com"
        self.api_key = "xxx"
        self.secret = "xxx"
    
    def get_positions(self):
        # 直连币安，不通过 Web API
        response = requests.get(
            f"{self.binance_url}/fapi/v2/positionRisk",
            headers={'X-MBX-APIKEY': self.api_key}
        )
        return response.json()
    
    def run(self):
        while True:
            try:
                positions = self.get_positions()
                # 检查持仓、止损单等
                time.sleep(60)
            except Exception as e:
                # 记录错误，继续运行
                self.log_error(e)
                time.sleep(60)
```

**优势**:
- ✅ 不依赖 Web 服务
- ✅ Web 挂了监控仍能告警
- ✅ 更可靠

---

### 方案 2: systemd 进程守护

**创建**: `/etc/systemd/system/quant-monitor.service`

```ini
[Unit]
Description=Quant Trading Monitor
After=network.target

[Service]
Type=simple
User=admin
WorkingDirectory=/root/.openclaw/workspace/quant/v3-architecture
ExecStart=/root/.openclaw/workspace/quant/.venv/bin/python scripts/enhanced_monitor.py
Restart=always
RestartSec=10
StandardOutput=append:/root/.openclaw/workspace/quant/v3-architecture/logs/monitor_stdout.log
StandardError=append:/root/.openclaw/workspace/quant/v3-architecture/logs/monitor_stderr.log

# 资源限制
MemoryLimit=500M
CPUQuota=50%

# 环境
Environment="PYTHONPATH=/root/.openclaw/workspace/quant/v3-architecture"

[Install]
WantedBy=multi-user.target
```

**启用**:
```bash
sudo systemctl daemon-reload
sudo systemctl enable quant-monitor
sudo systemctl start quant-monitor
sudo systemctl status quant-monitor
```

**优势**:
- ✅ 崩溃自动重启
- ✅ 开机自启动
- ✅ 资源限制
- ✅ 日志分离

---

### 方案 3: 看门狗机制

**修改**: `scripts/enhanced_monitor.py`

```python
import requests
import time

WATCHDOG_URL = "http://localhost:3000/api/health/monitor"

class WatchdogMonitor:
    def __init__(self):
        self.last_heartbeat = time.time()
    
    def send_heartbeat(self):
        """每 60 秒发送心跳"""
        try:
            requests.post(WATCHDOG_URL, timeout=5)
            self.last_heartbeat = time.time()
        except:
            pass
    
    def check_monitor_health(self):
        """检查监控是否存活"""
        if time.time() - self.last_heartbeat > 120:  # 2 分钟无心跳
            # 重启监控
            subprocess.run(['systemctl', 'restart', 'quant-monitor'])
```

**优势**:
- ✅ 监控自己挂了能自动恢复
- ✅ 双重保障

---

### 方案 4: 日志轮转

**修改**: `scripts/enhanced_monitor.py`

```python
from logging.handlers import RotatingFileHandler
import logging

# 创建 logger
logger = logging.getLogger('monitor')
logger.setLevel(logging.INFO)

# 轮转文件处理器
handler = RotatingFileHandler(
    'logs/monitor.log',
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5,           # 保留 5 个文件
    encoding='utf-8'
)

# 格式化
formatter = logging.Formatter(
    '[%(asctime)s] [%(levelname)s] %(message)s'
)
handler.setFormatter(formatter)
logger.addHandler(handler)
```

**效果**:
```
monitor.log         # 当前日志
monitor.log.1       # 最近备份
monitor.log.2
monitor.log.3
monitor.log.4
monitor.log.5       # 最旧备份（超过则删除）
```

---

## 📋 实施清单

### 阶段 1: 紧急修复（今天）
- [ ] 添加日志轮转（30 分钟）
- [ ] 添加看门狗心跳（1 小时）
- [ ] 测试独立监控（2 小时）

### 阶段 2: 系统加固（明天）
- [ ] 创建 systemd 服务（1 小时）
- [ ] 配置自动重启（30 分钟）
- [ ] 测试崩溃恢复（1 小时）

### 阶段 3: 长期优化（本周）
- [ ] 监控直连币安 API（2 小时）
- [ ] 添加备用监控（2 小时）
- [ ] 压力测试（1 小时）

---

## 🎯 验收标准

### 可靠性
- [ ] 监控 7×24 小时运行
- [ ] 崩溃后 10 秒内自动重启
- [ ] 无单点故障

### 可维护性
- [ ] 日志轮转正常
- [ ] systemd 状态可查
- [ ] 心跳监控正常

### 可观测性
- [ ] 监控自身有监控
- [ ] 告警渠道多元化（Telegram + 邮件）
- [ ] 日志集中管理

---

*🦞 龙虾王量化交易系统 - 监控优化方案*  
*最后更新：2026-03-16 10:15*  
*状态：待实施*
