# Claude 模型配置指南

## 🤖 项目已支持 Claude 模型！

本项目现已完整支持 Anthropic Claude 模型，包括最新的 Claude 3.5 Sonnet 和 Claude 3 Opus。

## 🚀 快速配置

### 1. 获取 Claude API Key

1. 访问 [Anthropic Console](https://console.anthropic.com/)
2. 注册/登录账号
3. 创建 API Key
4. 复制 API Key（格式：`sk-ant-api...`）

### 2. 配置 API Key 和 Base URL

#### 方法 A: 修改 config.py（不推荐，会暴露密钥）

```python
# config.py
anthropic_api_key: str = "your-actual-api-key-here"
anthropic_base_url: str = "https://api.anthropic.com/v1"  # 或你的代理地址
```

#### 方法 B: 使用环境变量（推荐）

```bash
# 设置环境变量
export ANTHROPIC_API_KEY="sk-ant-api..."
export ANTHROPIC_BASE_URL="https://api.anthropic.com/v1"

# 或在 .env 文件中
ANTHROPIC_API_KEY=sk-ant-api...
ANTHROPIC_BASE_URL=https://api.anthropic.com/v1
```

#### 使用代理或自定义端点

如果你使用 Claude API 代理服务，可以配置自定义的 base URL：

```python
# config.py
anthropic_base_url: str = "https://api.mjdjourney.cn/v1"  # 代理地址
# 或其他兼容的 Claude API 端点
```

### 3. 选择 Claude 模型

在 `config.py` 中设置：

```python
# 启用 Claude 模型
model_type: str = "claude"

# 选择具体模型（推荐）
claude_model: str = "claude-3-5-sonnet-20241022"  # 最新最强

# 其他可选模型：
# - claude-3-opus-20240229     # 最强大，适合复杂任务
# - claude-3-sonnet-20240229   # 平衡性能
# - claude-3-haiku-20240307    # 最快速
```

### 4. 切换模型

#### 使用 Claude：
```python
# config.py
model_type: str = "claude"
```

#### 切回原模型（Moonshot/Kimi）：
```python
# config.py  
model_type: str = "openai"
```

## 🧪 测试 Claude 集成

```bash
# 运行 Claude 测试脚本
python test_claude.py
```

## 🎯 Claude vs Kimi 对比

| 特性 | Claude | Kimi/Moonshot |
|-----|--------|---------------|
| 上下文长度 | 200K tokens | 256K tokens |
| 工具调用 | ✅ 原生支持 | ⚠️ 兼容性问题 |
| 响应速度 | 快 | 中等 |
| 中文能力 | 优秀 | 优秀 |
| 成本 | 中等 | 较低 |
| 稳定性 | 高 | 中等 |

## 🔧 技术细节

### 架构设计

1. **模型层**：`AnthropicChatModel` (AgentScope 原生支持)
2. **Formatter层**：`AnthropicChatFormatter` (AgentScope 原生，正确处理tool_use/tool_result)
3. **配置层**：支持动态切换模型类型

### 文件变更

- `config.py` - 添加 Claude 配置
- `agent_factory.py` - 支持 Claude 模型创建，使用原生 AnthropicChatFormatter
- `test_claude.py` - Claude 测试脚本

## ⚠️ 注意事项

1. **API Key 格式**
   - Claude: `sk-ant-api...`
   - Kimi: `sk-...`
   - 确保使用正确的 API Key

2. **模型名称**
   - 使用完整的模型名称（包含日期）
   - 查看 [Anthropic 文档](https://docs.anthropic.com/claude/docs/models-overview) 获取最新模型列表

3. **工具调用兼容性**
   - Claude 原生支持工具调用
   - 但 AgentScope 的工具接口可能需要适配
   - 建议先测试纯对话功能

4. **成本控制**
   - Claude 按 token 计费
   - 建议设置 `max_tokens` 限制
   - 监控 API 使用量

## 🐛 常见问题

### Q1: "Invalid API key" 错误
**解决**: 检查 API Key 是否正确，格式应为 `sk-ant-api...`

### Q2: 模型名称错误
**解决**: 使用完整的模型名称，如 `claude-3-5-sonnet-20241022`

### Q3: 工具调用失败
**解决**: Claude 的工具调用格式可能与 AgentScope 期望的不同，建议先使用无工具模式

### Q4: 响应被截断
**解决**: 在 `agent_factory.py` 中增加 `max_tokens` 值

## 📝 使用示例

### 基础对话

```python
from config import get_settings
from agent_factory import create_model, get_formatter
from agentscope.agent import ReActAgent

settings = get_settings()
settings.model_type = "claude"

agent = ReActAgent(
    name="Claude助手",
    model=create_model(settings),
    formatter=get_formatter(settings),
    sys_prompt="你是一个智能助手"
)

# 使用 agent 进行对话
```

### Multi-Agent 协作

```python
# main.py 会自动使用配置的模型类型
# 只需设置 model_type = "claude" 即可
python main.py
```

## 🎉 完成！

现在你的项目已经支持 Claude 模型了！可以根据需求在 Claude 和 Kimi 之间灵活切换。

---

*提示：Claude 在理解复杂指令、代码生成、多轮对话等方面表现优秀，特别适合旅行规划这种需要理解上下文和提供详细建议的场景。*