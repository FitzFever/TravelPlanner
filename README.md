# 🌏 AI旅行规划师 - Multi-Agent系统

基于AgentScope官方最佳实践的智能旅行规划Multi-Agent系统。

## 🎯 项目特色

- **官方最佳实践**: 基于AgentScope官方Multi-Agent Debate模式设计
- **MsgHub协作**: 使用MsgHub进行多Agent消息广播和协作
- **异步执行**: 完全支持async/await异步模式
- **Studio集成**: 支持AgentScope Studio可视化调试
- **简洁架构**: 显式消息传递，避免过度封装

## 🏗️ 系统架构

### 灵活的Agent配置

系统支持三种配置模式，可根据需求灵活调整：

#### 基础版（默认）
```
旅行规划师 (Coordinator) - 主协调
├── 搜索专家 - POI和当地信息搜索
├── 规划专家 - 路线优化和行程安排  
└── 预算专家 - 预算分析（含住宿）

适合：快速Demo、开发测试
```

#### 标准版
```
旅行规划师 (Coordinator) - 主协调
├── POI专家 - 景点推荐分析
├── 路线专家 - 交通路线优化
├── 预算专家 - 详细预算分析
└── 当地专家 - 文化美食信息

适合：一般旅行规划需求
```

#### 完整版
```
旅行规划师 (Coordinator) - 主协调
├── POI专家 - 景点深度研究
├── 路线专家 - 多方案路线规划
├── 预算专家 - 精细化预算管理
├── 当地专家 - 深度文化体验
└── 住宿专家 - 酒店民宿推荐

适合：高端定制化需求
```

通过MsgHub进行消息广播和协作

## 🚀 快速启动

### 1. 环境准备

```bash
# 进入项目目录
cd examples/travel_planner_hackathon

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置环境变量

系统提供了两种配置方式：

#### 方式A：使用.env文件（推荐）
项目已包含 `.env` 文件，你可以直接修改其中的值：

```bash
# 编辑 .env 文件
API_KEY=your-moonshot-api-key
BASE_URL=https://api.moonshot.cn/v1
TAVILY_API_KEY=your-tavily-api-key
STUDIO_URL=http://localhost:3000
ENABLE_STUDIO=true
DEBUG=true
AGENT_MODE=basic  # 可选: basic, standard, full
```

#### 方式B：直接修改config.py
也可以直接在 `config.py` 中修改默认值（不推荐用于敏感信息）

#### 配置说明
- **config.py**: 定义配置结构和默认值
- **.env文件**: 存储实际配置值，会自动覆盖config.py中的默认值
- **优先级**: .env文件 > config.py默认值

### 3. 启动应用

```bash
# 启动Multi-Agent旅行规划系统
python main.py
```

系统会自动连接到AgentScope Studio (http://localhost:3000)

### 4. 使用方式

1. 启动系统后，访问 **AgentScope Studio**: http://localhost:3000
2. 在对话界面中输入您的旅行需求，例如：
   - "我想去上海旅行2天，预算中等，喜欢文化和美食"
   - "计划一个北京3日游，经济型预算"
3. 系统会通过MsgHub协调多个Agent为您制定完整方案
4. 在Studio中可视化观察整个Multi-Agent协作过程

## 📁 项目结构

```
travel_planner_hackathon/
├── main.py                  # 主程序入口
├── config.py               # 配置管理
├── requirements.txt        # 依赖列表
├── .env.template          # 环境变量模板
├── .env                   # 环境变量配置
└── README.md             # 项目说明
```

## 🔧 核心组件

### Agent层

根据配置模式（AGENT_MODE）动态创建：

**基础版（basic）**：
- **协调Agent**: 主协调器，管理整个规划流程
- **搜索专家**: 整合POI和当地信息搜索
- **规划专家**: 路线优化和行程安排
- **预算专家**: 预算分析（含住宿）

**标准版（standard）**：
- **协调Agent**: 主协调器
- **POI专家**: 景点搜索和分析
- **路线专家**: 交通路线优化
- **当地专家**: 文化和美食信息
- **预算专家**: 详细预算分析

**完整版（full）**：
- 包含标准版所有Agent
- **住宿专家**: 酒店和民宿推荐
- **美食专家**: 餐厅推荐（可选）

### 工具层

- **SearchMCP**: 集成Tavily搜索API
- **MapsTools**: 地理计算和路线优化
- **DataSources**: 模拟数据源，确保演示稳定

### 数据层

- **TravelNotebook**: 内存共享数据中心
- **DataModels**: Pydantic数据模型定义

## 💡 使用示例

### Web界面方式
1. **输入旅行需求**（在表单中填写）
   - 目的地: 东京
   - 时长: 5天
   - 预算: 舒适型
   - 风格: 文化探索

2. **观察AI分析过程**（在Studio中可视化）
   - 景点专家: 搜索文化类景点
   - 当地专家: 收集文化背景信息
   - 路线专家: 优化游览路线
   - 预算专家: 分析总体费用

3. **获得完整方案**
   - 每日详细行程
   - 景点推荐和时间安排
   - 预算明细和分析
   - 当地实用贴士

### Studio对话方式
在Studio聊天界面输入：
```
"我想去东京旅行5天，预算舒适型，喜欢文化探索，我们是2个人"
```

AI会立即开始协调各专家Agent制定方案，你可以实时观察整个协作过程！

## 🛠️ 技术栈

- **后端**: FastAPI + WebSocket
- **Agent框架**: AgentScope + KimiMultiAgentFormatter
- **LLM**: Moonshot Kimi K2 Turbo
- **前端**: 原生HTML/CSS/JavaScript
- **工具**: MCP (Tavily搜索)

## 📝 API接口

### POST /api/plan
创建旅行规划会话

```json
{
  "destination": "东京",
  "duration": 5,
  "budget": "舒适",
  "travel_style": "文化",
  "group_size": 1
}
```

### WebSocket /ws/{session_id}
实时接收规划进度和结果

## 🎬 演示亮点

1. **实时Agent协作**: 可视化展示4个专家Agent的工作状态
2. **AgentScope Studio集成**: 实时观察Multi-Agent交互流程
3. **智能数据共享**: Agent间通过TravelNotebook进行信息交换
4. **优雅降级策略**: 确保即使外部API失败也能正常演示
5. **响应式界面**: 适配移动端，用户体验佳

## 🎨 AgentScope Studio调试功能

### Studio界面功能
- **实时Agent状态**: 查看每个Agent的运行状态和进度
- **消息追踪**: 观察Agent间的消息传递和协作过程
- **可视化流程**: 图形化展示Multi-Agent工作流
- **调试信息**: 详细的Agent执行日志和错误信息

### 调试流程
1. 启动Studio和应用后，先访问Studio界面 (http://localhost:3000)
2. 在旅行规划界面输入需求，触发Agent工作流
3. 在Studio中实时观察Agent协作过程：
   - POIAgent搜索景点信息
   - LocalAgent收集当地信息
   - RouteAgent优化路线规划
   - BudgetAgent分析预算明细
4. 查看Agent间的数据共享和状态更新

## 🔍 故障排查

### 常见问题

1. **API密钥错误**: 检查`.env`文件中的API配置
2. **端口占用**: 修改`app.py`中的端口号
3. **依赖缺失**: 确保安装了所有requirements.txt中的包

### 调试模式

启用调试模式查看详细日志：

```bash
DEBUG=true python app.py
```

## 🚀 部署建议

### 本地开发
```bash
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

### 生产部署
```bash
uvicorn app:app --host 0.0.0.0 --port 8000 --workers 4
```

## 🤝 贡献指南

1. Fork 项目
2. 创建特性分支
3. 提交更改
4. 推送到分支
5. 创建 Pull Request

## 📄 许可证

本项目基于AgentScope框架开发，遵循相应的开源许可证。

---

🎉 **享受AI驱动的旅行规划体验！**