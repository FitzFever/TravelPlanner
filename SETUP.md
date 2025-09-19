# 独立运行设置指南

本项目已经脱离 AgentScope 源码依赖，可以作为独立项目运行。

## 安装步骤

### 1. 创建虚拟环境（推荐）

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# macOS/Linux:
source venv/bin/activate
# Windows:
venv\Scripts\activate
```

### 2. 安装依赖

```bash
# 安装所有依赖包，包括 AgentScope
pip install -r requirements.txt
```

### 3. 配置环境变量

创建或编辑 `.env` 文件：

```env
# API配置
API_KEY=your-moonshot-api-key
BASE_URL=https://api.moonshot.cn/v1
TAVILY_API_KEY=your-tavily-api-key

# Studio配置
STUDIO_URL=http://localhost:3000
ENABLE_STUDIO=true

# Agent配置
AGENT_MODE=basic  # basic, standard, full
DEBUG=true
```

## 运行项目

### 启动主程序

```bash
python main.py
```

### 运行测试

```bash
# 测试纯LLM功能（无工具调用）
python test_simple.py

# 测试工具调用功能
python test_tools.py
```

## 项目结构

```
TravelPlanner/
├── main.py              # 主程序
├── config.py            # 配置管理
├── agent_factory.py     # Agent创建工厂
├── tools.py             # 工具函数定义
├── formatter/           # 本地Formatter实现
│   ├── __init__.py
│   └── kimi_formatter.py  # KimiMultiAgentFormatter
├── test_simple.py       # 简单测试
├── test_tools.py        # 工具测试
├── requirements.txt     # 依赖包列表
└── .env                 # 环境变量配置
```

## 关键修改说明

1. **移除源码路径依赖**: 不再需要 `sys.path.append('../../src')`
2. **AgentScope作为包安装**: 通过 pip 从 PyPI 安装
3. **本地Formatter实现**: `KimiMultiAgentFormatter` 在本地 `formatter` 模块中实现
   - 实现了异步 `format` 方法兼容 AgentScope 接口
   - 支持 Msg 对象和字典格式的消息
4. **简化内存管理**: 移除了 `InMemoryMemory` 参数（非必需）

## 注意事项

### Moonshot/Kimi API 工具调用问题

当前 Moonshot API 的工具调用格式与 AgentScope 默认格式存在兼容性问题。如果遇到以下错误：

```
Invalid request: an assistant message with 'tool_calls' must be followed by tool messages
```

解决方案：
1. 使用不带工具的纯 LLM 对话模式
2. 或切换到其他兼容的 LLM API（如 OpenAI）
3. 或等待 AgentScope 更新对 Moonshot API 的支持

## 故障排查

1. **ImportError**: 确保已正确安装 agentscope 包
   ```bash
   pip install agentscope>=0.1.0
   ```

2. **API 连接错误**: 检查 `.env` 文件中的 API 密钥配置

3. **Module not found**: 确保在项目根目录运行，且虚拟环境已激活

## 更多信息

- AgentScope 官方文档: https://doc.agentscope.io/
- GitHub 仓库: https://github.com/agentscope-ai/agentscope