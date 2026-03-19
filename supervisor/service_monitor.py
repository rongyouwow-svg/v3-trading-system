#!/usr/bin/env python3
"""
🦞 服务监控和故障告警

功能:
    - 监控所有服务状态
    - 服务宕机立即告警 (Telegram)
    - 服务宕机立即重启
    - 定期健康检查
"""

import time
import subprocess
import requests
from datetime import datetime
from pathlib import Path

from modules.utils.logger import setup_logger

logger = setup_logger("service_monitor", log_file="logs/service_monitor.log")

# ==================== 配置 ====================

SUPERVISORCTL = "/root/.pyenv/versions/3.10.13/bin/supervisorctl"
SUPERVISOR_CONF = "/root/.openclaw/workspace/quant/v3-architecture/supervisor/supervisord.conf"
TELEGRAM_BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
TELEGRAM_CHAT_ID = "1233887750"

# 监控的服务
MONITORED_SERVICES = [
    "quant-web",
    
    
    "quant-strategy-eth",
    "quant-strategy-avax",
    "quant-strategy-link",
]

# Dashboard 健康检查
DASHBOARD_HEALTH_URL = "http://localhost:3000/api/health"

# 告警配置
CHECK_INTERVAL = 30  # 30 秒检查一次
MAX_RESTART_ATTEMPTS = 3  # 最大重启次数
RESTART_COOLDOWN = 300  # 重启冷却时间 (5 分钟)

# ==================== 告警函数 ====================

def send_telegram_alert(message: str, level: str = "WARNING"):
    """发送 Telegram 告警"""
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        data = {
            'chat_id': TELEGRAM_CHAT_ID,
            'text': f"🚨 **服务告警** [{level}]\n\n{message}",
            'parse_mode': 'Markdown'
        }
        response = requests.post(url, json=data, timeout=10)
        if response.status_code == 200:
            logger.info(f"✅ Telegram 告警已发送")
            return True
        else:
            logger.error(f"❌ Telegram 告警失败：{response.text}")
            return False
    except Exception as e:
        logger.error(f"❌ 发送告警异常：{e}")
        return False


# ==================== 监控函数 ====================

def get_service_status(service_name: str) -> str:
    """获取服务状态"""
    try:
        result = subprocess.run(
            [SUPERVISORCTL, "-c", SUPERVISOR_CONF, "status", service_name],
            capture_output=True,
            text=True,
            timeout=10
        )
        status_line = result.stdout.strip()
        
        if "RUNNING" in status_line:
            return "RUNNING"
        elif "STOPPED" in status_line:
            return "STOPPED"
        elif "FATAL" in status_line:
            return "FATAL"
        elif "BACKOFF" in status_line:
            return "BACKOFF"
        else:
            return "UNKNOWN"
    except Exception as e:
        logger.error(f"获取 {service_name} 状态失败：{e}")
        return "ERROR"


def restart_service(service_name: str) -> bool:
    """重启服务"""
    try:
        logger.info(f"🔄 重启服务：{service_name}")
        
        # 停止
        subprocess.run(
            [SUPERVISORCTL, "-c", SUPERVISOR_CONF, "stop", service_name],
            capture_output=True,
            timeout=30
        )
        time.sleep(2)
        
        # 启动
        result = subprocess.run(
            [SUPERVISORCTL, "-c", SUPERVISOR_CONF, "start", service_name],
            capture_output=True,
            timeout=30
        )
        
        time.sleep(3)
        
        # 验证启动
        status = get_service_status(service_name)
        if status == "RUNNING":
            logger.info(f"✅ {service_name} 重启成功")
            return True
        else:
            logger.error(f"❌ {service_name} 重启失败，状态：{status}")
            return False
            
    except Exception as e:
        logger.error(f"重启 {service_name} 异常：{e}")
        return False


def check_dashboard_health() -> bool:
    """检查 Dashboard 健康状态"""
    try:
        response = requests.get(DASHBOARD_HEALTH_URL, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'ok':
                return True
        return False
    except Exception as e:
        logger.error(f"Dashboard 健康检查失败：{e}")
        return False


# ==================== 主监控循环 ====================

# 重启计数
restart_counts = {service: 0 for service in MONITORED_SERVICES}
last_restart_time = {service: 0 for service in MONITORED_SERVICES}

def monitor_loop():
    """主监控循环"""
    logger.info("=" * 60)
    logger.info("🦞 服务监控已启动")
    logger.info("=" * 60)
    logger.info(f"监控服务：{len(MONITORED_SERVICES)} 个")
    logger.info(f"检查间隔：{CHECK_INTERVAL} 秒")
    logger.info(f"最大重启：{MAX_RESTART_ATTEMPTS} 次")
    logger.info(f"冷却时间：{RESTART_COOLDOWN} 秒")
    logger.info("=" * 60)
    
    # 发送启动通知
    send_telegram_alert(
        "✅ **服务监控已启动**\n\n"
        f"监控服务：{len(MONITORED_SERVICES)} 个\n"
        f"检查间隔：{CHECK_INTERVAL} 秒",
        "INFO"
    )
    
    while True:
        try:
            current_time = time.time()
            
            # 检查 Dashboard 健康
            dashboard_ok = check_dashboard_health()
            if not dashboard_ok:
                logger.error("❌ Dashboard 健康检查失败！")
                send_telegram_alert(
                    "🚨 **Dashboard 故障**\n\n"
                    "健康检查失败，正在重启...",
                    "CRITICAL"
                )
                restart_service("quant-web")
            
            # 检查所有服务
            for service in MONITORED_SERVICES:
                status = get_service_status(service)
                
                if status == "RUNNING":
                    # 服务正常，重置计数
                    restart_counts[service] = 0
                    logger.debug(f"✅ {service}: {status}")
                    
                elif status in ["STOPPED", "FATAL", "BACKOFF"]:
                    logger.error(f"❌ {service}: {status}")
                    
                    # 检查冷却时间
                    if current_time - last_restart_time[service] < RESTART_COOLDOWN:
                        logger.warning(f"⏳ {service} 在冷却期内，暂不重启")
                        continue
                    
                    # 检查重启次数
                    if restart_counts[service] >= MAX_RESTART_ATTEMPTS:
                        logger.error(f"🚫 {service} 已达到最大重启次数，停止重启")
                        send_telegram_alert(
                            f"🚨 **服务故障**\n\n"
                            f"服务：{service}\n"
                            f"状态：{status}\n"
                            f"已达到最大重启次数 ({MAX_RESTART_ATTEMPTS})，请手动检查！",
                            "CRITICAL"
                        )
                        continue
                    
                    # 发送告警
                    send_telegram_alert(
                        f"🚨 **服务故障告警**\n\n"
                        f"服务：{service}\n"
                        f"状态：{status}\n"
                        f"重启次数：{restart_counts[service] + 1}/{MAX_RESTART_ATTEMPTS}\n"
                        f"正在自动重启...",
                        "WARNING"
                    )
                    
                    # 重启服务
                    if restart_service(service):
                        restart_counts[service] += 1
                        last_restart_time[service] = current_time
                    else:
                        restart_counts[service] += 1
                        last_restart_time[service] = current_time
                        
                        send_telegram_alert(
                            f"❌ **重启失败**\n\n"
                            f"服务：{service}\n"
                            f"请手动检查！",
                            "CRITICAL"
                        )
                
                else:
                    logger.warning(f"⚠️ {service}: {status}")
            
            time.sleep(CHECK_INTERVAL)
            
        except KeyboardInterrupt:
            logger.info("⏹️ 监控停止")
            send_telegram_alert("⏹️ **服务监控已停止**", "INFO")
            break
        except Exception as e:
            logger.error(f"监控循环异常：{e}", exc_info=True)
            time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    monitor_loop()
