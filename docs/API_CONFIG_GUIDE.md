# API 配置管理模块使用指南

**创建时间**: 2026-03-13 18:55  
**模块**: `modules/config/api_config.py`

---

## 📋 功能说明

API 配置管理模块提供安全、统一的 API Key 管理方式：

- ✅ 支持配置文件和环境变量两种方式
- ✅ 支持多环境配置（测试网/实盘）
- ✅ 环境变量优先（更安全）
- ✅ 配置验证
- ✅ 配置模板生成

---

## 🚀 快速开始

### 方式 1: 使用配置文件（推荐）

**步骤 1: 创建配置文件**

```bash
cd /root/.openclaw/workspace/quant/v3-architecture

# 复制模板
cp config/api_keys.json.example config/api_keys.json

# 编辑配置文件
vim config/api_keys.json
```

**步骤 2: 填写 API Key**

```json
{
  "binance": {
    "testnet": {
      "api_key": "你的测试网 API Key",
      "secret_key": "你的测试网 Secret Key"
    },
    "mainnet": {
      "api_key": "你的实盘 API Key",
      "secret_key": "你的实盘 Secret Key"
    }
  },
  "default_testnet": true
}
```

**步骤 3: 使用配置**

```python
from modules.config.api_config import APIConfig

# 创建配置管理器
config = APIConfig()

# 获取币安配置（测试网）
binance_config = config.get_binance_config('testnet')

# 创建连接器
from connectors.binance.usdt_futures import BinanceUSDTFuturesConnector

connector = BinanceUSDTFuturesConnector(
    api_key=binance_config['api_key'],
    secret_key=binance_config['secret_key'],
    testnet=True
)
```

---

### 方式 2: 使用环境变量（最安全）

**步骤 1: 设置环境变量**

```bash
# 临时设置（当前终端有效）
export BINANCE_API_KEY="your_api_key"
export BINANCE_SECRET_KEY="your_secret_key"
export BINANCE_TESTNET="true"

# 永久设置（添加到~/.bashrc）
echo 'export BINANCE_API_KEY="your_api_key"' >> ~/.bashrc
echo 'export BINANCE_SECRET_KEY="your_secret_key"' >> ~/.bashrc
echo 'export BINANCE_TESTNET="true"' >> ~/.bashrc
source ~/.bashrc
```

**步骤 2: 使用配置**

```python
from modules.config.api_config import APIConfig

# 自动从环境变量加载
config = APIConfig()

# 获取 API Key
api_key = config.get_api_key()
secret_key = config.get_secret_key()
```

---

## 📖 API 参考

### APIConfig 类

#### 初始化

```python
config = APIConfig(config_file='config/api_keys.json')
```

**参数**:
- `config_file` (str, optional): 配置文件路径，默认 `config/api_keys.json`

---

#### 获取配置

```python
# 获取币安配置
binance_config = config.get_binance_config('testnet')

# 获取 API Key
api_key = config.get_api_key('testnet')

# 获取 Secret Key
secret_key = config.get_secret_key('testnet')

# 是否测试网
is_testnet = config.is_testnet()
```

---

#### 验证配置

```python
result = config.validate_config()

if result.is_success:
    print("✅ 配置验证通过")
else:
    print(f"❌ 配置验证失败：{result.message}")
```

---

#### 获取配置信息

```python
info = config.get_config_info()
print(info)
# 输出:
# {
#   'config_file': 'config/api_keys.json',
#   'config_file_exists': True,
#   'has_testnet_config': True,
#   'has_mainnet_config': True,
#   'is_testnet': True,
#   'load_from_env': False
# }
```

---

#### 创建配置模板

```python
# 创建模板文件
config.create_config_template('config/api_keys.json.example')

# 获取模板内容
template = config.create_config_template()
print(template)
```

---

### 便捷函数

```python
from modules.config.api_config import (
    get_api_config,
    get_binance_api_key,
    get_binance_secret_key,
    is_binance_testnet
)

# 获取全局配置实例
config = get_api_config()

# 获取 API Key
api_key = get_binance_api_key()

# 获取 Secret Key
secret_key = get_binance_secret_key()

# 是否测试网
is_testnet = is_binance_testnet()
```

---

## 🔒 安全建议

### 1. 配置文件加入 .gitignore

```bash
# .gitignore
config/api_keys.json
.env
*.env
```

✅ 已配置！

---

### 2. 使用环境变量（生产环境）

```bash
# 在~/.bashrc 中添加
export BINANCE_API_KEY="your_api_key"
export BINANCE_SECRET_KEY="your_secret_key"
```

---

### 3. 不要硬编码 API Key

```python
# ❌ 错误：硬编码
api_key = "q3BX9K88wS4Dzco6DxVp5fhkRc5OOUu3tKFK5VBHkpcweVJ1NDDgATDV6Db0TTOg"

# ✅ 正确：从配置读取
from modules.config.api_config import get_binance_api_key
api_key = get_binance_api_key()
```

---

### 4. 区分测试网和实盘

```json
{
  "binance": {
    "testnet": {
      "api_key": "test_api_key",
      "secret_key": "test_secret_key"
    },
    "mainnet": {
      "api_key": "real_api_key",
      "secret_key": "real_secret_key"
    }
  },
  "default_testnet": true
}
```

---

## 📝 配置文件格式

```json
{
  "binance": {
    "testnet": {
      "api_key": "测试网 API Key",
      "secret_key": "测试网 Secret Key"
    },
    "mainnet": {
      "api_key": "实盘 API Key",
      "secret_key": "实盘 Secret Key"
    }
  },
  "default_testnet": true
}
```

**字段说明**:
- `binance.testnet.api_key`: 测试网 API Key
- `binance.testnet.secret_key`: 测试网 Secret Key
- `binance.mainnet.api_key`: 实盘 API Key
- `binance.mainnet.secret_key`: 实盘 Secret Key
- `default_testnet`: 默认使用测试网（true/false）

---

## 🧪 测试

```bash
cd /root/.openclaw/workspace/quant/v3-architecture

# 运行测试
python -m pytest tests/unit/test_api_config.py -v
```

**测试覆盖**:
- ✅ 配置文件加载
- ✅ 环境变量加载
- ✅ 获取配置
- ✅ 配置验证
- ✅ 配置模板
- ✅ 环境变量优先级

---

## 🎯 使用示例

### 示例 1: 创建币安连接器

```python
from modules.config.api_config import APIConfig
from connectors.binance.usdt_futures import BinanceUSDTFuturesConnector

# 获取配置
config = APIConfig()
binance_config = config.get_binance_config('testnet')

# 创建连接器
connector = BinanceUSDTFuturesConnector(
    api_key=binance_config['api_key'],
    secret_key=binance_config['secret_key'],
    testnet=config.is_testnet()
)

# 测试连接
result = connector.health_check()
print(result)
```

---

### 示例 2: 切换测试网/实盘

```python
from modules.config.api_config import APIConfig

config = APIConfig()

# 使用测试网
testnet_config = config.get_binance_config('testnet')

# 使用实盘
mainnet_config = config.get_binance_config('mainnet')
```

---

### 示例 3: 配置验证

```python
from modules.config.api_config import APIConfig

config = APIConfig()
result = config.validate_config()

if result.is_success:
    print("✅ 配置有效，可以开始交易")
else:
    print(f"❌ 配置无效：{result.message}")
```

---

## 📊 配置加载优先级

1. **环境变量** (最高优先级) ⭐
2. **配置文件**
3. **默认配置** (最低优先级)

---

## 🚨 常见问题

### Q1: 配置加载失败？

**检查**:
1. 配置文件路径是否正确
2. JSON 格式是否正确
3. 环境变量是否设置

**解决**:
```python
config = APIConfig(config_file='config/api_keys.json')
info = config.get_config_info()
print(info)  # 查看配置信息
```

---

### Q2: 如何切换测试网/实盘？

**方法 1**: 修改配置文件
```json
{
  "default_testnet": false  // 改为 false 使用实盘
}
```

**方法 2**: 修改环境变量
```bash
export BINANCE_TESTNET="false"
```

**方法 3**: 代码指定
```python
config = APIConfig()
mainnet_config = config.get_binance_config('mainnet')
```

---

### Q3: 配置文件在哪里？

**默认路径**: `config/api_keys.json`

**相对于**: `/root/.openclaw/workspace/quant/v3-architecture/`

---

## 📝 总结

- ✅ 配置文件：`config/api_keys.json`
- ✅ 环境变量：`BINANCE_API_KEY`, `BINANCE_SECRET_KEY`
- ✅ 优先级：环境变量 > 配置文件 > 默认配置
- ✅ 安全：配置文件已加入 .gitignore
- ✅ 测试：14 个测试用例，100% 通过

---

**文档时间**: 2026-03-13 18:55  
**实施者**: 龙虾王 AI 助手
