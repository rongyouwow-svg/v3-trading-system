#!/usr/bin/env python3
"""
🔍 监控错误检查脚本

每 2 小时自动检查监控日志，发现新错误时记录到 error_tracking.md
直接复制原始报错日志，格式：
2026-03-15 08:42:31 INFO
ETHUSDT 有持仓但无止损单！持仓：0.15 @ 2075.12
"""

import os
import re
from datetime import datetime, timedelta
from typing import List, Dict, Tuple

LOGS_DIR = os.path.dirname(__file__)
ERROR_TRACKING_FILE = os.path.join(LOGS_DIR, 'error_tracking.md')
MONITOR_LOG = os.path.join(LOGS_DIR, 'monitor_alerts.log')
ENHANCED_MONITOR_LOG = os.path.join(LOGS_DIR, 'enhanced_monitor.log')

def parse_monitor_logs() -> List[Dict]:
    """解析监控日志，提取错误信息和原始日志"""
    errors = []
    
    # 检查的文件列表
    log_files = [
        MONITOR_LOG,
        os.path.join(LOGS_DIR, 'monitor_alerts.log'),
    ]
    
    now = datetime.now()
    two_hours_ago = now - timedelta(hours=2)
    
    for log_file in log_files:
        if not os.path.exists(log_file):
            continue
        
        with open(log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        i = 0
        while i < len(lines):
            line = lines[i]
            
            # 匹配错误日志行
            if '[🚨 ALERT' in line or '[ERROR]' in line or 'CRITICAL' in line or 'WARNING' in line:
                # 提取时间戳
                time_match = re.search(r'\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\]', line)
                
                if time_match:
                    try:
                        log_time = datetime.strptime(time_match.group(1), '%Y-%m-%d %H:%M:%S')
                        
                        if log_time >= two_hours_ago:
                            # 提取错误级别
                            level = 'CRITICAL' if 'CRITICAL' in line else ('WARNING' if 'WARNING' in line else 'ALERT')
                            
                            # 提取错误消息（去掉时间戳和级别）
                            msg_match = re.search(r'\] (.+)$', line)
                            message = msg_match.group(1).strip() if msg_match else line.strip()
                            
                            # 收集原始日志（当前行 + 下一行如果有关联信息）
                            raw_logs = []
                            
                            # 添加当前行（格式化）
                            raw_logs.append(f"{time_match.group(1)} [{level}]")
                            raw_logs.append(message)
                            
                            # 检查下一行是否有相关内容
                            if i + 1 < len(lines):
                                next_line = lines[i + 1].strip()
                                if next_line and not re.match(r'^\[\d{4}-\d{2}-\d{2}', next_line):
                                    raw_logs.append(next_line)
                            
                            # 生成错误标题（从消息提取关键信息）
                            title = message.split('！')[0] if '！' in message else message[:50]
                            
                            errors.append({
                                'time': log_time.strftime('%Y-%m-%d %H:%M:%S'),
                                'level': level,
                                'message': message,
                                'title': title,
                                'raw_logs': '\n'.join(raw_logs),
                                'log_file': os.path.basename(log_file)
                            })
                    except Exception as e:
                        pass
            i += 1
    
    # 去重（基于标题 + 时间）
    seen = set()
    unique_errors = []
    for error in errors:
        key = f"{error['title']}_{error['time']}"
        if key not in seen:
            seen.add(key)
            unique_errors.append(error)
    
    return unique_errors

def load_existing_errors() -> Dict:
    """加载已有的错误记录"""
    existing = {}
    
    if not os.path.exists(ERROR_TRACKING_FILE):
        return existing
    
    with open(ERROR_TRACKING_FILE, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 提取已有的错误标题
    for match in re.finditer(r'### 错误 #\d+ - (.+?)(?: ✅| ⏳|$)', content):
        title = match.group(1).strip()
        existing[title] = True
    
    return existing

def get_next_error_id() -> str:
    """获取下一个错误 ID"""
    if not os.path.exists(ERROR_TRACKING_FILE):
        return "001"
    
    with open(ERROR_TRACKING_FILE, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 找到最大的错误 ID
    max_id = 0
    for match in re.finditer(r'### 错误 #(\d+)', content):
        id_num = int(match.group(1))
        if id_num > max_id:
            max_id = id_num
    
    return f"{max_id + 1:03d}"

def append_error_to_tracking(error: Dict, error_id: str):
    """追加新错误到追踪文件"""
    # 读取现有内容
    if os.path.exists(ERROR_TRACKING_FILE):
        with open(ERROR_TRACKING_FILE, 'r', encoding='utf-8') as f:
            content = f.read()
    else:
        content = f"""# 🚨 量化系统错误追踪记录

**创建时间**: {datetime.now().strftime('%Y-%m-%d %H:%M')}
**检查频率**: 每 2 小时自动检查
**Cron 任务 ID**: `9c3ecf56-fe13-45c3-8e86-52b789789980`

---

## 📋 错误记录列表

---

## 📊 统计信息

| 状态 | 数量 |
|------|------|
| 待处理 | 0 |
| 调查中 | 0 |
| 已解决 | 0 |
| **总计** | **0** |

---

**最后更新**: {datetime.now().strftime('%Y-%m-%d %H:%M')}

"""
    
    # 找到插入位置（在"## 📋 错误记录列表"之后，下一个"---"之前）
    insert_marker = "## 📋 错误记录列表\n"
    insert_pos = content.find(insert_marker)
    
    if insert_pos == -1:
        insert_pos = len(content)
    else:
        insert_pos += len(insert_marker)
        # 找到下一个分隔线
        next_sep = content.find('\n---\n', insert_pos)
        if next_sep != -1:
            insert_pos = next_sep + 1
    
    # 生成新错误记录
    new_entry = f"""
### 错误 #{error_id} - {error.get('title', '未命名错误')} ⏳ 待处理

| 项目 | 内容 |
|------|------|
| **发现时间** | {error.get('time', '未知')} |
| **错误级别** | {error.get('level', 'UNKNOWN')} |
| **涉及组件** | 待分析 |
| **根本原因** | 待分析 |
| **修复方案** | 待制定 |
| **状态** | ⏳ 待处理 |

**原始报错日志**:
```
{error.get('raw_logs', '无')}
```

---
"""
    
    # 插入新错误
    new_content = content[:insert_pos] + new_entry + content[insert_pos:]
    
    # 更新统计信息
    total_match = re.search(r'\| \*\*总计\*\* \| (\d+) \|', new_content)
    if total_match:
        old_total = int(total_match.group(1))
        new_total = old_total + 1
        new_content = re.sub(
            r'\| 待处理 \| \d+ \|',
            f'| 待处理 | {new_total} |',
            new_content
        )
        new_content = re.sub(
            r'\| \*\*总计\*\* \| \d+ \|',
            f'| **总计** | **{new_total}** |',
            new_content
        )
    
    # 更新最后更新时间
    new_content = re.sub(
        r'\*\*最后更新\*\*: .+',
        f'**最后更新**: {datetime.now().strftime("%Y-%m-%d %H:%M")}',
        new_content
    )
    
    # 保存
    with open(ERROR_TRACKING_FILE, 'w', encoding='utf-8') as f:
        f.write(new_content)

def check_and_log_errors():
    """主检查函数"""
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 开始检查监控错误...")
    
    # 获取最近的错误
    errors = parse_monitor_logs()
    
    if not errors:
        print("✅ 未发现新错误")
        return
    
    # 加载已有错误
    existing = load_existing_errors()
    
    # 检查新错误
    new_count = 0
    for error in errors:
        title = error['title']
        
        # 检查是否已存在
        if title not in existing:
            new_count += 1
            error_id = get_next_error_id()
            append_error_to_tracking(error, error_id)
            print(f"🚨 发现新错误 #{error_id}: {title}")
        else:
            print(f"⏭️  已存在错误：{title}")
    
    print(f"检查完成：发现 {new_count} 个新错误")

if __name__ == '__main__':
    check_and_log_errors()
