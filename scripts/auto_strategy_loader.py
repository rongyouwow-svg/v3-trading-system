#!/usr/bin/env python3
"""
🔌 策略热插拔自动加载器

功能:
1. 监控 strategies/ 目录
2. 自动发现新策略文件
3. 自动生成 Supervisor 配置
4. 自动重启/停止策略进程
5. 无需手动修改 Supervisor 配置

使用方式:
    python3 scripts/auto_strategy_loader.py

守护运行:
    nohup python3 scripts/auto_strategy_loader.py > logs/auto_loader.log 2>&1 &
"""

import os
import sys
import time
import hashlib
from pathlib import Path
from datetime import datetime

# 配置
STRATEGIES_DIR = Path(__file__).parent.parent / "strategies"
SUPERVISOR_CONF_DIR = Path(__file__).parent.parent / "supervisor"
AUTO_CONF_FILE = SUPERVISOR_CONF_DIR / "auto_strategies.conf"
STATE_FILE = Path(__file__).parent.parent / "logs" / ".strategy_loader_state"
LOG_FILE = Path(__file__).parent.parent / "logs" / "auto_loader.log"

# 排除文件
EXCLUDE_FILES = {
    'base_strategy.py',
    'strategy_template.py',
    'strategy_template_v2.py',
    '__init__.py',
    'loader.py',
    'strategy_status_api.py',
    'auto_sim_strategy.py',
    'demo_strategy.py',
    'simple_strategy.py',
    'test_rsi_1min.py',
}

# 需要运行的策略（通过文件标记）
ACTIVE_STRATEGIES_FILE = STRATEGIES_DIR.parent / ".active_strategies"

def log(message):
    """记录日志"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_msg = f"[{timestamp}] {message}"
    print(log_msg)
    with open(LOG_FILE, 'a') as f:
        f.write(log_msg + '\n')

def get_file_hash(filepath):
    """获取文件 MD5 哈希"""
    with open(filepath, 'rb') as f:
        return hashlib.md5(f.read()).hexdigest()

def load_state():
    """加载状态"""
    if STATE_FILE.exists():
        with open(STATE_FILE, 'r') as f:
            return eval(f.read())
    return {}

def save_state(state):
    """保存状态"""
    with open(STATE_FILE, 'w') as f:
        f.write(str(state))

def load_active_strategies():
    """加载激活的策略列表"""
    if ACTIVE_STRATEGIES_FILE.exists():
        with open(ACTIVE_STRATEGIES_FILE, 'r') as f:
            return [line.strip() for line in f if line.strip() and not line.startswith('#')]
    # 默认激活所有策略
    return []

def generate_supervisor_config(strategy_file):
    """生成 Supervisor 配置"""
    strategy_name = strategy_file.stem
    config_name = f"quant-strategy-{strategy_name}"
    
    config = f"""[program:{config_name}]
command=/root/.pyenv/versions/3.10.13/bin/python3 -u strategies/{strategy_file.name}
directory=/root/.openclaw/workspace/quant/v3-architecture
user=root
group=root
autostart=true
autorestart=true
startretries=10
retrywait=5
stderr_logfile=/root/.openclaw/workspace/quant/v3-architecture/logs/supervisor_{strategy_name}_err.log
stdout_logfile=/root/.openclaw/workspace/quant/v3-architecture/logs/supervisor_{strategy_name}_out.log
environment=PYTHONPATH="/root/.openclaw/workspace/quant/v3-architecture"
numprocs=1
process_name=%(program_name)s
startsecs=5
stopwaitsecs=10
stopsignal=TERM

"""
    return config_name, config

def scan_strategies():
    """扫描策略文件"""
    strategies = {}
    
    for file in STRATEGIES_DIR.glob("*.py"):
        if file.name in EXCLUDE_FILES:
            continue
        
        # 检查是否包含 Strategy 类
        try:
            content = file.read_text(encoding='utf-8')
            if 'class' in content and 'Strategy' in content:
                strategies[file.stem] = {
                    'file': file.name,
                    'hash': get_file_hash(file),
                    'mtime': file.stat().st_mtime
                }
        except Exception as e:
            log(f"⚠️ 读取 {file.name} 失败：{e}")
    
    return strategies

def update_supervisor_config(active_strategies, strategy_files):
    """更新 Supervisor 配置"""
    config_lines = ["# Auto-generated strategy configurations\n# DO NOT EDIT MANUALLY\n\n"]
    
    for strategy_name in active_strategies:
        if strategy_name in strategy_files:
            config_name, config = generate_supervisor_config(
                type('obj', (object,), {'stem': strategy_name, 'name': strategy_files[strategy_name]['file']})()
            )
            config_lines.append(config)
    
    # 写入配置文件
    with open(AUTO_CONF_FILE, 'w') as f:
        f.writelines(config_lines)
    
    log(f"✅ Supervisor 配置已更新 ({len(active_strategies)} 个策略)")
    return True

def reload_supervisor():
    """通知 Supervisor 重新加载配置"""
    try:
        import subprocess
        result = subprocess.run(
            ['/root/.pyenv/versions/3.10.13/bin/supervisorctl', '-s', 
             'unix:///root/.openclaw/workspace/quant/v3-architecture/logs/supervisor.sock',
             'reread'],
            capture_output=True, text=True, timeout=10
        )
        log(f"Supervisor reread: {result.stdout.strip()}")
        
        result = subprocess.run(
            ['/root/.pyenv/versions/3.10.13/bin/supervisorctl', '-s',
             'unix:///root/.openclaw/workspace/quant/v3-architecture/logs/supervisor.sock',
             'update'],
            capture_output=True, text=True, timeout=10
        )
        log(f"Supervisor update: {result.stdout.strip()}")
        
        return True
    except Exception as e:
        log(f"❌ Supervisor 重载失败：{e}")
        return False

def main():
    """主循环"""
    log("🔌 策略热插拔加载器启动")
    log(f"📂 监控目录：{STRATEGIES_DIR}")
    log(f"📝 配置文件：{AUTO_CONF_FILE}")
    
    state = load_state()
    last_check = state.get('last_check', 0)
    
    while True:
        try:
            # 扫描策略文件
            strategies = scan_strategies()
            log(f"🔍 发现 {len(strategies)} 个策略文件")
            
            # 加载激活的策略列表
            active_strategies = load_active_strategies()
            
            # 如果没有指定激活列表，使用默认策略
            if not active_strategies:
                active_strategies = ['rsi_1min_strategy', 'link_rsi_detailed_strategy', 'rsi_scale_in_strategy']
                log(f"⚠️ 未指定激活策略，使用默认：{active_strategies}")
            
            # 更新 Supervisor 配置
            update_supervisor_config(active_strategies, strategies)
            
            # 重载 Supervisor
            reload_supervisor()
            
            # 保存状态
            state['last_check'] = time.time()
            state['strategies'] = list(strategies.keys())
            save_state(state)
            
            log(f"✅ 检查完成，下次检查在 60 秒后")
            
        except Exception as e:
            log(f"❌ 检查失败：{e}")
        
        # 每 60 秒检查一次
        time.sleep(60)

if __name__ == '__main__':
    main()
