# 路书规划Multi-Agent系统架构设计文档

基于AgentScope Meta-Planner架构的智能旅行规划系统设计方案

## 1. 系统概述

本系统基于AgentScope框架中的meta_planner_agent架构，设计了一个专门用于旅行路书规划的multi-agent系统。系统采用分治策略，将复杂的旅行规划任务分解为多个子任务，由不同的专家agent协作完成。

### 1.1 设计理念

- **专业化分工**: 每个agent专注于特定领域的任务
- **协作式规划**: 多个agent协同工作，信息共享
- **动态优化**: 基于实时信息动态调整规划方案
- **用户中心**: 以用户需求和偏好为核心驱动

## 2. 系统架构

### 2.1 核心组件架构

```
TravelPlannerAgent (主规划器)
├── TravelNotebook (旅行规划笔记本)
├── RouteManager (路线管理器) 
├── SpecialistManager (专家管理器)
├── RealTimeMonitor (实时监听器) ← 新增
├── DynamicReplanner (动态重规划器) ← 新增
└── SpecialistPool (专家池)
    ├── RouteOptimizationAgent (路线优化专家)
    ├── POIResearchAgent (景点研究专家)
    ├── AccommodationAgent (住宿专家)
    ├── BudgetAnalysisAgent (预算分析专家)
    └── LocalExpertAgent (当地专家)
```

### 2.2 组件详细说明

#### TravelPlannerAgent (主规划器)
继承自Meta-Planner架构，负责：
- 用户需求分析和任务分解
- 专家agent的动态创建和管理
- 子任务分配和执行协调
- 结果整合和最终路书生成

#### TravelNotebook (旅行规划笔记本)
存储和管理规划过程中的所有信息：
- 用户需求和偏好
- 目的地分析结果
- 各专家的研究成果
- 路线优化方案
- 预算分析报告

### 2.3 专家Agent通信协调架构

```
                    TravelPlannerAgent (主规划器)
                           │
                           │ 任务分配与结果收集
                           ▼
                    TravelNotebook (共享数据中心)
                          ╱│╲
                         ╱ │ ╲
                        ╱  │  ╲
                       ▼   ▼   ▼
            POIResearchAgent │ AccommodationAgent
            (景点研究专家)    │  (住宿专家)
                      ╲     │     ╱
                       ╲    ▼    ╱
                        RouteOptimizationAgent
                           (路线优化专家)
                              │
                              ▼
                        LocalExpertAgent ←→ BudgetAnalysisAgent
                         (当地专家)        (预算分析专家)
                              │                │
                              └────────────────┘
                                       │
                                       ▼
                                TravelPlannerAgent
```

**双向协作机制:**
- 所有专家通过 **TravelNotebook** 进行信息共享和双向通信
- **POIResearchAgent** ↔ **RouteOptimizationAgent**: 景点信息与路线反馈
- **RouteOptimizationAgent** ↔ **AccommodationAgent**: 路线与住宿位置互相优化
- **LocalExpertAgent** 为所有专家提供当地信息支持
- **BudgetAnalysisAgent** 汇总所有专家的成本信息
- 支持迭代优化：专家可根据其他专家的反馈调整自己的方案

### 2.4 专家Agent信息广播详图

```
POIResearchAgent (景点研究专家)
├─ 广播给 RouteOptimizationAgent: 
│  • 景点GPS坐标
│  • 开放时间和闭馆时间
│  • 建议游览时长
│  • 停车场信息
├─ 广播给 BudgetAnalysisAgent:
│  • 门票价格明细
│  • 停车费用
├─ 广播给 LocalExpertAgent:
│  • 景点文化背景查询需求
└─ 广播给 TravelNotebook: 完整景点数据库

RouteOptimizationAgent (路线优化专家)
├─ 广播给 AccommodationAgent:
│  • 每日最后一个景点位置
│  • 建议住宿区域范围
│  • 次日首个景点位置
├─ 广播给 BudgetAnalysisAgent:
│  • 自驾路线总里程
│  • 预估油费和过路费
│  • 停车费用汇总
└─ 广播给 TravelNotebook: 优化路线方案

AccommodationAgent (住宿专家)
├─ 广播给 RouteOptimizationAgent:
│  • 确定住宿地点坐标
│  • 酒店停车设施信息
├─ 广播给 BudgetAnalysisAgent:
│  • 住宿费用明细
│  • 额外服务费用
└─ 广播给 TravelNotebook: 住宿推荐方案

LocalExpertAgent (当地专家)
├─ 广播给 POIResearchAgent:
│  • 当地文化禁忌和注意事项
│  • 最佳游览时间建议
├─ 广播给 RouteOptimizationAgent:
│  • 当地交通规则和限行信息
│  • 路况和施工信息
│  • 停车规定和收费标准
├─ 广播给 AccommodationAgent:
│  • 当地住宿习惯和推荐区域
│  • 安全区域建议
├─ 广播给 BudgetAnalysisAgent:
│  • 当地消费水平指导
│  • 小费和服务费习惯
└─ 广播给 TravelNotebook: 当地实用信息集合

BudgetAnalysisAgent (预算分析专家)
├─ 接收所有专家的成本信息
├─ 汇总分析后广播给 TravelPlannerAgent:
│  • 总预算明细表
│  • 不同档次方案对比
│  • 省钱建议和优化方案
└─ 广播给 TravelNotebook: 完整预算分析报告

TravelNotebook (数据广播中心)
└─ 向所有专家实时广播:
   • 用户需求更新
   • 其他专家的最新研究成果
   • 任务进度和状态变更
```

## 3. 数据模型设计

### 3.1 核心数据结构

```python
class TravelPlanningRequest(BaseModel):
    """用户旅行规划请求"""
    destination: str = Field(description="目的地城市/国家")
    duration: str = Field(description="旅行天数")
    budget_range: str = Field(description="预算范围")
    travel_style: str = Field(description="旅行风格(休闲/冒险/文化/美食等)")
    group_size: int = Field(description="旅行人数")
    special_requirements: str = Field(description="特殊需求(老人/儿童/残障等)")
    travel_dates: str = Field(description="出行日期范围")
    preferences: List[str] = Field(description="兴趣偏好列表")

class POI(BaseModel):
    """景点信息"""
    name: str = Field(description="景点名称")
    location: dict = Field(description="地理坐标")
    category: str = Field(description="景点类型")
    rating: float = Field(description="评分")
    opening_hours: dict = Field(description="开放时间")
    ticket_price: dict = Field(description="门票价格")
    estimated_visit_time: int = Field(description="建议游览时间(分钟)")
    description: str = Field(description="景点描述")

class DayItinerary(BaseModel):
    """单日行程安排"""
    day: int = Field(description="第几天")
    date: str = Field(description="具体日期")
    morning_activities: List[POI] = Field(description="上午活动")
    afternoon_activities: List[POI] = Field(description="下午活动")
    evening_activities: List[POI] = Field(description="晚上活动")
    transportation: dict = Field(description="交通安排")
    accommodation: dict = Field(description="住宿信息")
    meals: dict = Field(description="餐饮推荐")
    estimated_cost: float = Field(description="预估费用")
    notes: str = Field(description="特别说明")

class TravelNotebook(BaseModel):
    """旅行规划笔记本"""
    user_request: TravelPlanningRequest
    destination_analysis: str = Field(description="目的地分析报告")
    route_optimization: str = Field(description="路线优化说明")
    daily_itineraries: List[DayItinerary] = Field(description="每日行程")
    budget_breakdown: dict = Field(description="预算明细")
    accommodation_options: List[dict] = Field(description="住宿选项")
    transportation_plan: dict = Field(description="交通计划")
    packing_checklist: List[str] = Field(description="行李清单")
    emergency_contacts: dict = Field(description="紧急联系方式")
    local_tips: List[str] = Field(description="当地贴士")
    generated_documents: dict = Field(description="生成的路书文档")
```

## 4. 专家Agent设计

### 4.1 RouteOptimizationAgent (路线优化专家)

**职责范围:**
- 地理位置聚类分析
- 最优路径规划算法
- 时间安排优化
- 交通连接分析

**核心工具:**
- Google Maps API / 高德地图API
- 路径规划算法(TSP变种)
- 时间估算模型
- 交通状况分析

**输出内容:**
- 每日最优游览路线
- 景点间交通方式建议
- 时间分配方案
- 路线备选方案

### 4.2 POIResearchAgent (景点研究专家)

**职责范围:**
- 景点信息收集和分析
- 用户评价分析
- 热门程度评估
- 季节性因素分析

**核心工具:**
- 旅游网站爬虫(携程、马蜂窝、TripAdvisor)
- 社交媒体分析工具
- 图像识别和分类
- 情感分析算法

**输出内容:**
- 推荐景点清单
- 景点详细信息
- 用户评价摘要
- 最佳游览时间建议

### 4.3 AccommodationAgent (住宿专家)

**职责范围:**
- 酒店/民宿推荐
- 价格对比分析
- 位置便利性评估
- 设施和服务分析

**核心工具:**
- 预订平台API(Booking.com, Airbnb)
- 价格监控系统
- 地理位置分析
- 评分权重算法

**输出内容:**
- 住宿推荐列表
- 价格趋势分析
- 位置便利性评分
- 预订建议和时机

### 4.4 TransportationAgent (交通专家)

**职责范围:**
- 交通方式选择分析
- 时刻表和票价查询
- 交通衔接优化
- 替代方案规划

**核心工具:**
- 航班查询API
- 火车票查询系统
- 公共交通API
- 实时交通信息

**输出内容:**
- 交通方案推荐
- 票价对比分析
- 时刻表信息
- 交通预订建议

### 4.5 BudgetAnalysisAgent (预算分析专家)

**职责范围:**
- 成本估算和分解
- 预算分配优化
- 性价比分析
- 省钱策略建议

**核心工具:**
- 价格数据库
- 汇率换算API
- 成本建模算法
- 历史价格分析

**输出内容:**
- 详细预算表
- 成本分析报告
- 省钱建议
- 不同预算档次方案

### 4.6 LocalExpertAgent (当地专家)

**职责范围:**
- 当地文化和习俗介绍
- 安全注意事项
- 隐藏景点推荐
- 实用信息提供

**核心工具:**
- 当地论坛和社区爬虫
- 文化数据库
- 安全信息API
- 天气预报服务

**输出内容:**
- 文化指南
- 安全提醒
- 当地特色推荐
- 实用贴士

## 5. 工作流程设计

### 5.1 主要工作流程

```python
async def plan_travel_itinerary(user_request: str):
    """旅行规划主流程"""
    
    # 阶段1: 需求分析和任务分解
    await decompose_travel_planning_task(
        user_request=user_request,
        destination_analysis="分析目的地特点、最佳旅行时间、文化背景",
        detailed_plan="制定详细的任务分解计划",
        subtasks=[
            {
                "name": "目的地和景点研究",
                "description": "收集目的地信息，筛选推荐景点",
                "expected_output": "景点清单、开放时间、门票信息",
                "assigned_agent": "POIResearchAgent"
            },
            {
                "name": "住宿方案制定",
                "description": "根据预算和位置要求推荐住宿",
                "expected_output": "住宿推荐列表、价格对比、预订建议",
                "assigned_agent": "AccommodationAgent"
            },
            {
                "name": "交通规划",
                "description": "制定大交通和当地交通方案",
                "expected_output": "交通时刻表、票价信息、预订建议",
                "assigned_agent": "TransportationAgent"
            },
            {
                "name": "路线优化",
                "description": "优化每日游览路线和时间安排",
                "expected_output": "最优路线方案、时间分配、备选路线",
                "assigned_agent": "RouteOptimizationAgent"
            },
            {
                "name": "预算分析",
                "description": "制定详细预算方案和成本控制",
                "expected_output": "预算明细表、省钱建议、不同档次方案",
                "assigned_agent": "BudgetAnalysisAgent"
            },
            {
                "name": "当地信息整理",
                "description": "收集当地文化、安全、实用信息",
                "expected_output": "文化指南、安全提醒、实用贴士",
                "assigned_agent": "LocalExpertAgent"
            }
        ]
    )
    
    # 阶段2: 动态创建专家agents
    await create_specialist_agents()
    
    # 阶段3: 并行执行专家任务
    await execute_parallel_research()
    
    # 阶段4: 结果整合和优化
    await integrate_and_optimize_results()
    
    # 阶段5: 生成最终路书文档
    await generate_travel_guide_documents()
    
    # 阶段6: 启动实时监听和动态调整 ← 新增
    await start_real_time_monitoring_and_replanning()

async def start_real_time_monitoring_and_replanning():
    """启动实时监听和动态重规划"""
    
    # 初始化实时监听器
    real_time_monitor = RealTimeMonitor(travel_notebook)
    dynamic_replanner = DynamicReplanner(specialist_manager)
    
    # 开始持续监听
    while travel_in_progress:
        # 检测变化
        changes = await real_time_monitor.detect_changes()
        
        if changes:
            # 评估影响并决定重规划策略
            replanning_plan = await dynamic_replanner.evaluate_replanning_necessity(changes)
            
            # 通知用户并等待确认
            user_approval = await notify_user_and_get_approval(replanning_plan)
            
            if user_approval:
                # 执行动态重规划
                await execute_dynamic_replanning(replanning_plan)
                # 更新TravelNotebook
                await update_travel_notebook_with_new_plan()
        
        # 等待下一次检查
        await asyncio.sleep(MONITORING_INTERVAL)
```

### 5.2 并行执行策略

系统支持多个专家agent并行工作，提高效率：

1. **信息收集阶段**: POI研究、住宿、交通信息可并行收集
2. **分析阶段**: 预算分析和当地信息可并行处理
3. **优化阶段**: 路线优化基于前面收集的信息进行

## 6. 特色功能设计

### 6.1 实时监听与动态重规划

**核心理念:**
旅行过程中用户的实际情况往往与原计划存在差异，系统需要具备实时感知和动态调整的能力。

#### 6.1.1 实时监听机制

```python
class RealTimeMonitor:
    """实时监听器"""
    
    def __init__(self, travel_notebook: TravelNotebook):
        self.travel_notebook = travel_notebook
        self.event_handlers = {
            "location_change": self.handle_location_change,
            "route_deviation": self.handle_route_deviation,
            "time_delay": self.handle_time_delay,
            "plan_modification": self.handle_plan_modification,
            "emergency_event": self.handle_emergency_event
        }
    
    async def monitor_travel_status(self):
        """持续监听旅行状态变化"""
        while True:
            # 监听GPS位置变化
            current_location = await self.get_current_location()
            # 监听用户主动更新
            user_updates = await self.check_user_updates()
            # 监听外部事件（天气、交通、景点关闭等）
            external_events = await self.check_external_events()
            
            if self.detect_significant_change():
                await self.trigger_replanning()
```

#### 6.1.2 变化检测类型

**位置偏差检测:**
- GPS轨迹与计划路线的偏离程度
- 用户是否按计划到达检查点
- 意外绕行或走错路的识别

**时间偏差检测:**
- 景点游览时间超出或不足预期
- 交通用时与预估的差异
- 整体行程进度的滞后或提前

**用户主动变更:**
- 临时增加或取消景点
- 改变住宿地点
- 调整预算范围
- 修改旅行偏好

**外部突发事件:**
- 天气变化影响行程
- 景点临时关闭或维修
- 交通管制或事故
- 当地突发事件

#### 6.1.3 动态重规划触发机制

```python
class DynamicReplanner:
    """动态重规划器"""
    
    async def evaluate_replanning_necessity(self, change_event):
        """评估是否需要重新规划"""
        impact_score = await self.calculate_impact_score(change_event)
        
        if impact_score >= CRITICAL_THRESHOLD:
            return await self.trigger_full_replanning()
        elif impact_score >= MODERATE_THRESHOLD:
            return await self.trigger_partial_replanning()
        else:
            return await self.trigger_minor_adjustment()
    
    async def trigger_full_replanning(self):
        """触发完整重规划"""
        # 重新激活所有专家Agent
        await self.reactivate_all_specialists([
            "RouteOptimizationAgent",
            "AccommodationAgent", 
            "BudgetAnalysisAgent",
            "LocalExpertAgent"
        ])
        
    async def trigger_partial_replanning(self):
        """触发部分重规划"""
        # 只激活相关专家Agent
        affected_agents = await self.identify_affected_agents()
        await self.reactivate_specialists(affected_agents)
```

#### 6.1.4 专家Agent重新分工策略

**RouteOptimizationAgent (路线重优化):**
- 基于当前位置重新计算最优路径
- 考虑剩余时间和未完成景点
- 提供多种备选方案

**AccommodationAgent (住宿重新安排):**
- 根据新路线调整住宿位置
- 处理临时订房需求
- 协助取消或修改原有预订

**BudgetAnalysisAgent (预算重新分析):**
- 计算变更带来的额外成本
- 更新剩余预算分配
- 提供成本控制建议

**LocalExpertAgent (实时信息更新):**
- 提供当前位置的最新信息
- 推荐附近的替代方案
- 更新安全和实用信息

#### 6.1.5 用户交互界面

```python
class RealTimeInterface:
    """实时交互界面"""
    
    async def notify_user_of_changes(self, replanning_result):
        """通知用户重规划结果"""
        notification = {
            "type": "replanning_suggestion",
            "urgency": replanning_result.urgency_level,
            "changes": replanning_result.proposed_changes,
            "impact": replanning_result.cost_time_impact,
            "alternatives": replanning_result.alternative_options
        }
        
        # 发送推送通知
        await self.send_push_notification(notification)
        
        # 等待用户确认
        user_response = await self.wait_for_user_response()
        
        if user_response.approved:
            await self.execute_replanning(replanning_result)
        else:
            await self.handle_user_rejection(user_response)
```

### 6.2 智能路线优化

**核心算法:**
- 改进的旅行商问题(TSP)算法
- 考虑时间窗口的约束优化
- 多目标优化(时间、成本、体验)

**优化因素:**
- 地理位置聚类
- 景点开放时间
- 预计排队时间
- 交通便利性
- 用户体力分配

### 6.2 多维度预算分析

**预算分类:**
- 交通费用(大交通、当地交通)
- 住宿费用(不同档次选项)
- 餐饮费用(正餐、小食、特色美食)
- 景点门票(必游、可选)
- 购物预算(纪念品、特产)
- 应急备用金

**智能建议:**
- 基于历史数据的成本预测
- 淡旺季价格提醒
- 早鸟优惠和促销信息
- 本地消费水平指导

### 6.3 个性化推荐引擎

**推荐维度:**
- 兴趣偏好匹配
- 年龄段适宜性
- 体力要求评估
- 季节性因素考虑

**数据源整合:**
- 用户历史行为
- 社交媒体热度
- 专业旅游评价
- 实时用户反馈

### 6.4 实时信息集成

**动态更新内容:**
- 天气预报和预警
- 交通状况监控
- 景点客流量实时数据
- 突发事件和安全提醒
- 价格变动通知

## 7. 输出文档格式

### 7.1 多格式路书生成

**PDF精美路书:**
- 专业排版设计
- 地图和图片集成
- 可打印版本
- 离线使用支持

**交互式数字版本:**
- 手机端适配
- 实时位置导航
- 一键预订功能
- 社交分享支持

**表格格式:**
- Excel详细行程表
- Google Sheets云端同步
- 预算计算器
- 可编辑模板

### 7.2 文档结构设计

```
旅行路书目录结构:
├── 01-行程概览
├── 02-目的地介绍
├── 03-详细日程安排
├── 04-住宿推荐
├── 05-交通指南
├── 06-美食推荐
├── 07-购物指南
├── 08-预算明细
├── 09-实用信息
├── 10-紧急联系
└── 11-附录(地图、清单等)
```

## 8. 技术实现要点

### 8.1 基于Meta-Planner的扩展

```python
class TravelPlanner(MetaPlanner):
    """旅行规划专用Meta-Planner"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.travel_notebook = TravelNotebook()
        self.specialist_manager = SpecialistManager()
        self.route_manager = RouteManager()
    
    async def plan_travel(self, user_request: str):
        """主要规划入口"""
        # 继承MetaPlanner的任务分解能力
        await self.enter_solving_complicated_task_mode("travel_planning")
        # 执行旅行专用规划流程
        return await self.execute_travel_planning_workflow(user_request)
```

### 8.2 专家Agent工厂模式

```python
class SpecialistAgentFactory:
    """专家Agent创建工厂"""
    
    @staticmethod
    def create_specialist(agent_type: str, **config) -> ReActAgent:
        """根据类型创建专家agent"""
        specialist_configs = {
            "poi_research": POIResearchConfig,
            "accommodation": AccommodationConfig,
            "transportation": TransportationConfig,
            # ... 其他专家配置
        }
        return specialist_configs[agent_type](**config)
```

### 8.3 工具集成策略

每个专家agent配备专门的工具集：
- 通用工具: 文件操作、网络请求、数据处理
- 专用工具: 特定API、算法库、数据库访问
- 外部服务: 地图服务、预订平台、信息查询

## 9. 部署和扩展

### 9.1 系统部署架构

- **核心服务**: TravelPlanner主服务
- **专家服务池**: 可动态扩缩容的专家agent实例
- **数据服务**: 缓存、数据库、文件存储
- **外部接口**: API网关、第三方服务集成

### 9.2 扩展能力

**水平扩展:**
- 支持新增专家agent类型
- 支持新的目的地和文化背景
- 支持新的旅行主题(商务、亲子、蜜月等)

**垂直扩展:**
- 增强现有专家的能力
- 提升算法精度和效率
- 集成更多数据源和服务

## 10. 总结

本设计方案充分利用了AgentScope Meta-Planner的分治思想和协作能力，将复杂的旅行规划任务分解为多个专业化的子任务，通过专家agent的协作完成。相比单一agent解决方案，该架构具有以下优势：

1. **专业性强**: 每个专家专注于特定领域，提供专业化服务
2. **可扩展性好**: 易于添加新的专家类型和功能模块
3. **容错能力强**: 单个专家的问题不会影响整体规划
4. **效率更高**: 并行处理能力显著提升规划速度
5. **用户体验佳**: 提供全面、个性化的旅行规划服务

该系统可作为智能旅行助手的核心引擎，为用户提供专业、全面、个性化的旅行规划服务。