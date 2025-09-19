# 🛠️ Agent工具调用功能说明

## ✅ 已完成功能

### 1. 工具函数集 (tools.py)
已创建6个旅行规划工具：
- `search_destination` - 搜索城市信息
- `search_poi` - 搜索景点 
- `calculate_route` - 计算路线
- `get_weather` - 天气查询
- `search_hotels` - 酒店搜索
- `estimate_budget` - 预算估算

### 2. Agent工厂 (agent_factory.py)
- 每个Agent配备独立的Toolkit实例（避免重复注册）
- 支持三种配置模式：
  - 基础版：3个专家
  - 标准版：4个专家
  - 完整版：5-6个专家

### 3. 主程序集成 (main.py)
- 根据AGENT_MODE环境变量动态创建Agent团队
- 专家并行使用工具获取信息
- 协调员整合各专家建议生成方案

## 🔍 测试结果

从测试输出可以看到：
1. **工具调用成功**：Agent能正确调用search_destination和search_poi工具
2. **数据返回正常**：工具返回了上海的城市信息和5个景点
3. **降级策略生效**：使用了模拟数据（因为没有真实API）

## 📝 使用示例

### 启动系统
```bash
# 基础版（3个专家）
python main.py

# 标准版（4个专家）  
AGENT_MODE=standard python main.py

# 完整版（5-6个专家）
AGENT_MODE=full python main.py
```

### 在Studio中输入
```
示例1：我想去上海旅行3天，预算舒适型，喜欢文化和美食，2个人
示例2：计划一个北京5天深度游，经济型预算
示例3：东京7天自由行，奢华型，重点是购物和美食
```

## 🎯 工具调用流程

1. **用户输入需求** → Studio界面
2. **协调员分析** → 提取关键信息（目的地、天数、预算）
3. **专家并行工作**：
   - 搜索专家：调用search_destination、search_poi获取信息
   - 规划专家：调用calculate_route优化路线
   - 预算专家：调用estimate_budget分析费用
4. **协调员整合** → 生成完整方案
5. **返回用户** → 结构化的旅行规划

## 💡 特色功能

### 降级策略
```python
try:
    # 优先使用真实API
    if os.getenv("TAVILY_API_KEY"):
        return tavily_search(query)
except:
    # 失败时使用模拟数据
    return MOCK_DATA[city]
```

### 灵活配置
通过环境变量控制专家数量，适应不同场景需求：
- 开发测试：3个专家，快速响应
- 日常使用：4个专家，功能平衡
- 高端定制：5-6个专家，深度服务

## 🚀 下一步优化

1. 集成真实的Tavily搜索API
2. 添加缓存机制避免重复搜索
3. 支持更多城市的模拟数据
4. 优化工具响应格式
5. 添加更多实用工具（如：汇率转换、签证查询等）