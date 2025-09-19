# 故障排查指南

## 🔍 为什么脱离源码后会报错？

### 核心原因分析

当项目脱离 AgentScope 源码独立运行后，出现错误的主要原因：

1. **Formatter 实现差异**
   - 源码中的 formatter 是完整实现，包含所有边缘情况处理
   - 本地简化版可能缺少某些功能
   - 特别是工具调用（tool_use/tool_result）的处理

2. **API 兼容性问题**
   - Moonshot/Kimi API 与标准 OpenAI API 存在差异
   - 工具调用格式不完全兼容
   - 消息格式要求更严格

3. **依赖版本差异**
   - 从源码运行使用的是开发版本
   - PyPI 安装的版本可能略有不同
   - 某些内部接口可能已更改

## 🚫 常见错误及解决方案

### 错误 1: "Invalid part type: tool_use"

**错误信息**：
```
Invalid request: the message at position 3 with role 'assistant' contains an invalid part type: tool_use
```

**原因**：
- Moonshot API 不接受 `tool_use` 类型的内容块
- 需要将其转换为 `tool_calls` 格式

**解决方案**：
已在 `formatter/kimi_formatter.py` 中实现转换逻辑

### 错误 2: "Tool calls must be followed by tool messages"

**错误信息**：
```
Invalid request: an assistant message with 'tool_calls' must be followed by tool messages
```

**原因**：
- API 期望工具调用后立即有工具响应
- 消息顺序不正确

**解决方案**：
1. 使用不带工具的 Agent（推荐）
2. 确保工具响应紧跟工具调用

### 错误 3: "KimiMultiAgentFormatter.format() got an unexpected keyword argument"

**原因**：
- 本地 formatter 接口与 AgentScope 期望的不匹配
- 缺少必要的方法参数

**解决方案**：
已更新 formatter 实现以匹配正确的接口

## ✅ 推荐解决方案

### 方案 1: 使用无工具模式（最稳定）

```python
# 创建不带工具的 Agent
agent = ReActAgent(
    name="助手",
    model=model,
    formatter=KimiMultiAgentFormatter(),
    # 不添加 toolkit 参数
    sys_prompt="你是一个智能助手..."
)
```

### 方案 2: 切换到兼容的 LLM API

如果需要工具调用功能，建议使用：
- OpenAI API
- Anthropic Claude API
- 其他完全兼容 OpenAI 格式的 API

### 方案 3: 使用原始 formatter（如果有权访问）

如果有 AgentScope 源码，可以直接复制完整的 formatter 实现：
```bash
cp /path/to/agentscope/src/agentscope/formatter/_kimi_formatter.py formatter/
```

## 🔧 调试建议

### 1. 启用详细日志

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### 2. 检查消息格式

```python
# 在 formatter 中添加调试输出
async def _format(self, msgs: list):
    print(f"Formatting {len(msgs)} messages")
    for msg in msgs:
        print(f"  - Role: {msg.role}, Type: {type(msg)}")
    # ... 格式化逻辑
```

### 3. 测试不同配置

```bash
# 测试纯 LLM（无工具）
python test_simple.py

# 测试带工具（可能失败）
python test_tools.py
```

## 📊 兼容性矩阵

| 功能 | 源码运行 | 独立运行 | 说明 |
|-----|---------|---------|-----|
| 基础对话 | ✅ | ✅ | 完全支持 |
| 工具调用 | ✅ | ⚠️ | Moonshot API 限制 |
| 多模态 | ✅ | ✅ | 支持图像 |
| 流式输出 | ✅ | ✅ | 支持 |

## 🎯 最佳实践

1. **优先使用纯 LLM 模式**
   - 更稳定
   - 更少的格式问题
   - 适合大多数对话场景

2. **逐步测试功能**
   - 先测试基础对话
   - 再测试工具调用
   - 最后测试复杂场景

3. **保持 formatter 更新**
   - 定期检查 AgentScope 更新
   - 同步 formatter 实现
   - 测试新功能兼容性

## 📚 参考资源

- [AgentScope 官方文档](https://doc.agentscope.io/)
- [Moonshot API 文档](https://platform.moonshot.cn/docs)
- [OpenAI API 参考](https://platform.openai.com/docs)

## 💬 获取帮助

如果问题持续存在：
1. 检查 [AgentScope Issues](https://github.com/agentscope-ai/agentscope/issues)
2. 查看 [Moonshot API 状态](https://status.moonshot.cn/)
3. 尝试使用开发版本：`pip install git+https://github.com/agentscope-ai/agentscope.git`