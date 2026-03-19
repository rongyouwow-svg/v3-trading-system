# 🦞 龙虾王自我诊断日志

**诊断时间**: 2026-03-18 22:30  
**问题**: 为什么老是卡住？

---

## 🔍 可能原因分析

### 1. 进程被杀死 ❓

**现象**:
- 执行到一半进程消失
- 工具调用无响应
- 会话中断

**可能原因**:
- 内存不足被 OOM killer 杀死
- 超时被系统杀死
- 父进程退出导致子进程退出

**检查**:
```bash
# 检查 OOM
dmesg | grep -i "killed process"

# 检查内存
free -h

# 检查进程
ps aux | grep python
```

---

### 2. 网络超时 ❓

**现象**:
- Telegram API 调用超时
- Dashboard API 无响应
- 工具调用卡住

**可能原因**:
- 网络延迟
- API 限流
- DNS 解析失败

**检查**:
```bash
# 测试网络
ping api.telegram.org

# 测试 API
curl https://api.telegram.org/bot<TOKEN>/getMe

# 检查 DNS
cat /etc/resolv.conf
```

---

### 3. 资源耗尽 ❓

**现象**:
- 系统变慢
- 进程无响应
- 工具调用超时

**可能原因**:
- CPU 满载
- 内存耗尽
- 磁盘空间不足
- 文件句柄耗尽

**检查**:
```bash
# CPU
top -bn1 | head -5

# 内存
free -h

# 磁盘
df -h

# 文件句柄
ulimit -n
```

---

### 4. Python 环境问题 ❓

**现象**:
- 脚本报错
- 模块找不到
- 路径错误

**可能原因**:
- Python 版本不匹配
- 虚拟环境未激活
- 依赖未安装

**检查**:
```bash
# Python 版本
python3 --version

# 虚拟环境
which python3

# 依赖
pip3 list
```

---

## 🔧 解决方案

### 方案 1: 保持进程活跃

```bash
# 使用 nohup
nohup python3 script.py > output.log 2>&1 &

# 使用 screen
screen -S mysession
python3 script.py
# Ctrl+A, D 退出

# 使用 tmux
tmux new -s mysession
python3 script.py
# Ctrl+B, D 退出
```

### 方案 2: 添加重试机制

```python
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# 配置重试
session = requests.Session()
retry = Retry(
    total=3,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504]
)
adapter = HTTPAdapter(max_retries=retry)
session.mount('http://', adapter)
session.mount('https://', adapter)

# 使用
response = session.get(url, timeout=30)
```

### 方案 3: 添加心跳

```python
import time
import requests

def heartbeat():
    while True:
        try:
            requests.post(
                "https://api.telegram.org/bot<TOKEN>/sendMessage",
                json={
                    'chat_id': '<CHAT_ID>',
                    'text': '💓 心跳检测'
                },
                timeout=10
            )
        except Exception as e:
            print(f"心跳失败：{e}")
        
        time.sleep(300)  # 每 5 分钟

# 后台运行
import threading
threading.Thread(target=heartbeat, daemon=True).start()
```

### 方案 4: 优化资源使用

```python
# 限制内存使用
import resource
resource.setrlimit(resource.RLIMIT_AS, (1024*1024*1024, 1024*1024*1024))  # 1GB

# 定期清理
import gc
gc.collect()

# 关闭未使用的连接
session.close()
```

---

## 📊 实时监控

### 监控脚本

```bash
#!/bin/bash
# monitor_self.sh

LOG_FILE="self_monitor.log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

while true; do
    # 检查进程
    if ! pgrep -f "python.*dashboard" > /dev/null; then
        log "🚨 Dashboard 进程丢失！"
    fi
    
    # 检查内存
    mem=$(free | grep Mem | awk '{print $3/$2 * 100.0}')
    log "💾 内存使用：${mem}%"
    
    # 检查 CPU
    cpu=$(top -bn1 | grep "Cpu(s)" | awk '{print $2 + $4}')
    log "📊 CPU 使用：${cpu}%"
    
    # 检查磁盘
    disk=$(df / | tail -1 | awk '{print $5}')
    log "💿 磁盘使用：${disk}"
    
    sleep 60
done
```

---

## 🎯 立即行动

### 1. 添加心跳 (立即)

```python
# 每 5 分钟发送心跳
import time
import requests

while True:
    try:
        requests.post(
            "https://api.telegram.org/bot8611422539:AAHK2M7Mt-wfQmf5zz1aZUjnCRpkZT1wmVI/sendMessage",
            json={
                'chat_id': '1233887750',
                'text': f'💓 心跳 - {time.strftime("%H:%M:%S")}'
            },
            timeout=10
        )
    except:
        pass
    time.sleep(300)
```

### 2. 优化超时设置

```python
# 所有请求添加超时
requests.get(url, timeout=30)  # 30 秒超时

# 添加重试
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

session = requests.Session()
retry = Retry(total=3, backoff_factor=1)
session.mount('http://', HTTPAdapter(max_retries=retry))
```

### 3. 使用后台进程

```bash
# 所有长时间运行的脚本使用 nohup
nohup python3 script.py > output.log 2>&1 &

# 或者使用 systemd
sudo systemctl start myservice
```

---

## 📝 诊断结果

### 当前状态

| 检查项 | 状态 | 数值 |
|--------|------|------|
| 内存 | ⏳ 检查中 | - |
| CPU | ⏳ 检查中 | - |
| 磁盘 | ⏳ 检查中 | - |
| 网络 | ⏳ 检查中 | - |
| 进程 | ⏳ 检查中 | - |

### 根本原因

待诊断...

### 修复方案

待实施...

---

**诊断人**: 龙虾王 🦞  
**诊断时间**: 2026-03-18 22:30  
**状态**: 诊断中...
