#!/bin/bash
# 🦞 强制大内存进程使用 Swap 脚本

# 配置
GATEWAY_MEM_LIMIT="400M"  # gateway 限制 400MB
TUI_MEM_LIMIT="200M"      # tui 限制 200MB

# 创建 cgroup
sudo cgcreate -g memory:/openclaw_limit

# 设置内存限制
sudo cgset -r memory.limit_in_bytes=$GATEWAY_MEM_LIMIT openclaw_limit

# 获取 gateway PID
GATEWAY_PID=$(pgrep -f "openclaw-gateway" | head -1)

if [ -n "$GATEWAY_PID" ]; then
    echo "✅ 找到 gateway 进程 (PID: $GATEWAY_PID)"
    
    # 将进程加入 cgroup
    sudo cgclassify -g memory:openclaw_limit $GATEWAY_PID
    echo "✅ 已将 gateway 加入内存限制 cgroup"
    
    # 验证
    echo "📊 当前内存限制:"
    sudo cgget -r memory.limit_in_bytes openclaw_limit
else
    echo "❌ 未找到 gateway 进程"
fi
