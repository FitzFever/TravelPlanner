# AgentScope Multi-Agent开发经验总结

## 🎯 项目背景

本项目是一个基于AgentScope框架的旅行规划Multi-Agent系统。在开发过程中，我遇到了多个技术挑战，特别是关于用户输入和Multi-Agent协作的问题。以下是完整的开发经验总结。

## 🔍 关键问题与解决方案

### 1. Studio用户输入问题

#### 问题描述
在AgentScope Studio中显示"No user input is requested"，用户无法输入。

#### 问题根源
- 过度复杂的代码逻辑
- 自定义Agent类重写了`reply`方法
- 错误的消息初始化方式

#### 解决方案
```python
# ❌ 错误：过度复杂
class TravelPlannerAgent(ReActAgent):
    async def reply(self, x, **kwargs):  # 不要重写核心方法！
        # 复杂逻辑...
        
# ✅ 正确：使用标准ReActAgent
planner = ReActAgent(
    name="AI旅行规划师",
    model=model,
    toolkit=toolkit,
    sys_prompt="..."
)

# ✅ 正确的消息循环
msg = Msg(name="AI助手", content="欢迎", role="assistant")
while True:
    msg = await user(msg)  # 用户输入
    msg = await planner(msg)  # Agent处理
```

### 2. 依赖版本冲突

#### 问题描述
Pydantic、MCP、FastAPI等包之间存在版本冲突。

#### 解决方案
```txt
# requirements.txt
agentscope>=0.1.0
pydantic>=2.11.0,<3.0.0
mcp>=1.13.0
fastapi>=0.115.0
pydantic-settings>=2.0.0
```

### 3. Multi-Agent协作模式

#### 问题描述
如何正确实现Multi-Agent协作，避免过度封装。

#### 解决方案
使用AgentScope的MsgHub进行协作：

```python
from agentscope.pipeline import MsgHub

# 使用MsgHub进行Multi-Agent协作
async with MsgHub(participants=[agent1, agent2, agent3]):
    msg1 = await agent1(user_msg)
    msg2 = await agent2(msg1)
    msg3 = await agent3(msg2)
```

## 📚 最佳实践

### 1. 保持简单

**原则**: AgentScope强调简单高效，避免过度封装。

```python
# ❌ 错误：过度封装
class ComplexAgent(ReActAgent):
    def __init__(self, ...):
        # 100行初始化代码
    
    async def complex_method(self):
        # 复杂的业务逻辑
        
# ✅ 正确：简洁明了
def create_agent(name: str, prompt: str):
    return ReActAgent(
        name=name,
        model=model,
        sys_prompt=prompt
    )
```

### 2. 显式消息传递

**原则**: 消息流转应该透明可追踪。

```python
# ✅ 显式消息传递
msg = await user(msg)  # 用户输入
msg = await agent1(msg)  # Agent1处理
msg = await agent2(msg)  # Agent2处理
```

### 3. 参考官方示例

**原则**: 遵循官方示例的模式和架构。

关键参考：
- Multi-Agent Debate示例
- meta_planner示例
- 官方文档的Key Concepts

### 4. 工具函数设计

**原则**: 工具函数应该简单、独立、可测试。

```python
from agentscope.tool import ToolResponse

def simple_tool(param: str) -> ToolResponse:
    """简单的工具函数"""
    return ToolResponse(
        content=[{
            "type": "text",
            "text": f"处理结果: {param}"
        }]
    )

# 注册工具
toolkit = Toolkit()
toolkit.register_tool_function(simple_tool)
```

## 🚫 常见陷阱

### 1. 不要重写核心方法

```python
# ❌ 错误
class MyAgent(ReActAgent):
    async def reply(self, x, **kwargs):
        # 不要重写reply方法！
```

### 2. 不要过度使用复杂逻辑

```python
# ❌ 错误：复杂的条件判断
if condition1 and condition2:
    if subcondition:
        # 嵌套逻辑
        
# ✅ 正确：让Agent自己决定
msg = await agent(user_msg)  # Agent会根据prompt处理
```

### 3. 不要忽视异步

```python
# ❌ 错误：同步调用
msg = user(msg)

# ✅ 正确：异步调用
msg = await user(msg)
```

## 🔧 调试技巧

### 1. 使用Studio可视化

- 访问 http://localhost:3000
- 观察消息流转
- 查看Agent状态

### 2. 简化测试

创建最小可复现示例：

```python
# test_minimal.py
import asyncio
from agentscope.agent import UserAgent, ReActAgent

async def main():
    user = UserAgent("用户")
    agent = ReActAgent(name="测试", ...)
    
    msg = None
    while True:
        msg = await user(msg)
        msg = await agent(msg)

asyncio.run(main())
```

### 3. 逐步构建

1. 先测试单个Agent
2. 再测试两个Agent协作
3. 最后构建完整系统

## 💡 性能优化

### 1. 并行处理

```python
# 并行执行多个Agent
tasks = [
    agent1.process(msg),
    agent2.process(msg),
    agent3.process(msg)
]
results = await asyncio.gather(*tasks)
```

### 2. 缓存策略

```python
from functools import lru_cache

@lru_cache(maxsize=128)
def expensive_operation(param):
    # 缓存昂贵的操作
    return result
```

## 📝 项目结构建议

### 最简结构（推荐）

```
project/
├── main.py          # 主程序
├── config.py        # 配置
├── requirements.txt # 依赖
└── README.md        # 文档
```

### 扩展结构

```
project/
├── main.py          # 主程序
├── agents/          # Agent定义
├── tools/           # 工具函数
├── config.py        # 配置
└── tests/           # 测试
```

## 🎓 学习资源

1. **官方文档**: https://doc.agentscope.io/
2. **GitHub示例**: https://github.com/agentscope-ai/agentscope/tree/main/examples
3. **关键概念**: Key Concepts, Pipeline, MsgHub
4. **示例代码**: Multi-Agent Debate, meta_planner

## 🏆 成功要素

1. **理解框架理念**: 简单、高效、透明
2. **参考官方示例**: 不要重新发明轮子
3. **保持代码简洁**: 少即是多
4. **测试驱动开发**: 先写测试，再写代码
5. **逐步迭代**: 从简单到复杂

## 🐛 故障排查清单

遇到问题时，按以下顺序检查：

1. □ 检查API密钥配置
2. □ 验证依赖版本兼容性
3. □ 确认使用了async/await
4. □ 查看Studio调试信息
5. □ 创建最小可复现示例
6. □ 参考官方示例代码
7. □ 检查是否重写了核心方法
8. □ 验证消息格式正确

## 📊 开发时间线

1. **初始开发**: 创建复杂的Multi-Agent系统
2. **遇到问题**: Studio用户输入失败
3. **尝试修复**: 各种复杂的解决方案
4. **深入分析**: 发现过度封装问题
5. **重新设计**: 基于官方最佳实践
6. **最终成功**: 简洁高效的实现

## 🌟 核心洞察

> "AgentScope的设计理念是简单高效。当你的代码变得复杂时，往往意味着你偏离了正确的方向。回归简单，参考官方示例，让框架为你工作，而不是与框架对抗。"

## 📌 记住

- **简单优于复杂**
- **显式优于隐式**
- **标准优于自定义**
- **官方示例是最好的老师**

## 🚀 项目独立运行

### 独立化改造说明

项目已完成独立化改造，不再依赖AgentScope源码路径：

1. **依赖安装**: AgentScope作为pip包安装 (`agentscope>=0.1.0`)
2. **路径清理**: 移除所有 `sys.path.append` 语句
3. **本地Formatter**: `KimiMultiAgentFormatter` 在 `formatter/` 模块中实现
4. **简化配置**: 移除非必需的 `InMemoryMemory` 参数

### ⚠️ 已知限制

脱离源码后可能遇到的问题：

1. **工具调用兼容性**: Moonshot/Kimi API 的工具调用格式与 OpenAI 不完全兼容
2. **Formatter 完整性**: 本地 formatter 可能缺少某些边缘情况处理
3. **版本差异**: PyPI 版本与源码开发版本可能略有不同

**建议**: 
- 优先使用无工具的纯 LLM 模式
- 如需工具调用，考虑切换到 OpenAI 或其他兼容 API
- 详见 `TROUBLESHOOTING.md` 获取完整故障排查指南

### 快速开始

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置环境变量
cp .env.template .env
# 编辑 .env 文件添加API密钥

# 3. 运行程序
python main.py
```

详见 `SETUP.md` 获取完整安装指南。

---

*本文档基于实际开发经验总结，希望能帮助其他开发者避免相同的陷阱，更快地构建优秀的Multi-Agent应用。*
- 150 -  1. **官方文档**: https://doc.agentscope.io/