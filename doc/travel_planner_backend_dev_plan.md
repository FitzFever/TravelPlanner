# 旅行规划Multi-Agent系统后端开发实现计划

基于AgentScope框架的旅行规划智能系统后端开发全面实施方案

## 1. 项目概述与目标

### 1.1 项目定位
构建一个基于AgentScope框架的intelligent travel planning system，通过5个专家Agent的协作，为用户提供个性化、智能化的旅行规划服务。

### 1.2 核心目标
- **智能化**: 通过Multi-Agent协作实现智能决策
- **个性化**: 基于用户偏好提供定制化方案
- **实时性**: 支持实时信息更新和动态重规划
- **可扩展**: 模块化设计，便于功能扩展
- **高性能**: 支持并发处理和快速响应

## 2. 技术架构设计

### 2.1 整体架构图

```
┌─────────────────────────────────────────────────────────────┐
│                    用户接口层 (API Layer)                    │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐  │
│  │   RESTful API   │  │   WebSocket     │  │  GraphQL     │  │
│  └─────────────────┘  └─────────────────┘  └──────────────┘  │
├─────────────────────────────────────────────────────────────┤
│                   业务编排层 (Orchestration)                 │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │              TravelPlannerAgent (主协调器)              │ │
│  └─────────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│                    Agent协作层 (Multi-Agent)                │
│ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌──────────┐ │
│ │RouteOptimi- │ │POIResearch  │ │Accommoda-   │ │Budget    │ │
│ │zationAgent  │ │Agent        │ │tionAgent    │ │Analysis  │ │
│ └─────────────┘ └─────────────┘ └─────────────┘ └──────────┘ │
│ ┌─────────────┐ ┌─────────────────────────────────────────┐ │
│ │LocalExpert  │ │         TravelNotebook                  │ │
│ │Agent        │ │        (共享数据中心)                    │ │
│ └─────────────┘ └─────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│                     工具层 (Tools & MCP)                    │
│ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌──────────┐ │
│ │地图工具     │ │搜索工具     │ │预订工具     │ │分析工具   │ │
│ └─────────────┘ └─────────────┘ └─────────────┘ └──────────┘ │
├─────────────────────────────────────────────────────────────┤
│                   数据持久层 (Data Layer)                    │
│ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌──────────┐ │
│ │PostgreSQL   │ │Redis Cache  │ │Vector DB    │ │File      │ │
│ │(主数据库)   │ │(缓存/队列)  │ │(向量搜索)   │ │Storage   │ │
│ └─────────────┘ └─────────────┘ └─────────────┘ └──────────┘ │
├─────────────────────────────────────────────────────────────┤
│                   外部服务层 (External APIs)                 │
│ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌──────────┐ │
│ │地图服务API  │ │旅游数据API  │ │预订平台API  │ │支付API   │ │
│ └─────────────┘ └─────────────┘ └─────────────┘ └──────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 技术栈选择

#### 核心框架和语言
- **主框架**: AgentScope (Multi-Agent) + FastAPI (Web框架)
- **编程语言**: Python 3.11+
- **异步处理**: asyncio + uvloop
- **任务调度**: Celery + Redis

#### 数据存储
- **主数据库**: PostgreSQL 14+ (ACID事务支持)
- **缓存系统**: Redis 7+ (缓存 + 消息队列)
- **向量数据库**: Chroma/Pinecone (语义搜索)
- **文件存储**: MinIO/AWS S3 (文档和图片)

#### 部署和运维
- **容器化**: Docker + Docker Compose
- **编排**: Kubernetes (生产环境)
- **监控**: Prometheus + Grafana + Jaeger
- **日志**: ELK Stack (Elasticsearch + Logstash + Kibana)

## 3. 数据库设计

### 3.1 核心表结构

```sql
-- 用户表
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    phone VARCHAR(20),
    preferences JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 旅行请求表
CREATE TABLE travel_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    destination VARCHAR(100) NOT NULL,
    duration INTEGER NOT NULL,
    budget_range VARCHAR(50),
    travel_style VARCHAR(50),
    group_size INTEGER DEFAULT 1,
    travel_dates DATERANGE,
    special_requirements TEXT,
    preferences JSONB,
    status VARCHAR(20) DEFAULT 'planning',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 旅行笔记本表 (TravelNotebook核心数据)
CREATE TABLE travel_notebooks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    request_id UUID REFERENCES travel_requests(id),
    destination_analysis TEXT,
    route_optimization JSONB,
    daily_itineraries JSONB,
    budget_breakdown JSONB,
    accommodation_options JSONB,
    transportation_plan JSONB,
    local_tips JSONB,
    generated_documents JSONB,
    version INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Agent状态表
CREATE TABLE agent_states (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    request_id UUID REFERENCES travel_requests(id),
    agent_name VARCHAR(50) NOT NULL,
    agent_type VARCHAR(50) NOT NULL,
    current_state JSONB,
    execution_log JSONB,
    last_activity TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW()
);

-- POI数据库
CREATE TABLE poi_database (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200) NOT NULL,
    location GEOGRAPHY(POINT),
    city VARCHAR(100),
    country VARCHAR(100),
    category VARCHAR(50),
    rating DECIMAL(3,2),
    opening_hours JSONB,
    ticket_price JSONB,
    estimated_visit_time INTEGER,
    description TEXT,
    features JSONB,
    images JSONB,
    reviews_summary JSONB,
    data_source VARCHAR(100),
    last_updated TIMESTAMP DEFAULT NOW()
);

-- 住宿信息表
CREATE TABLE accommodations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200) NOT NULL,
    location GEOGRAPHY(POINT),
    city VARCHAR(100),
    accommodation_type VARCHAR(50),
    rating DECIMAL(3,2),
    price_range JSONB,
    amenities JSONB,
    policies JSONB,
    contact_info JSONB,
    booking_links JSONB,
    data_source VARCHAR(100),
    last_updated TIMESTAMP DEFAULT NOW()
);

-- 路线信息表
CREATE TABLE routes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    request_id UUID REFERENCES travel_requests(id),
    day_number INTEGER,
    route_points JSONB,
    transportation_modes JSONB,
    estimated_time JSONB,
    estimated_cost JSONB,
    optimization_score DECIMAL(5,2),
    alternative_routes JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 预算信息表
CREATE TABLE budgets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    request_id UUID REFERENCES travel_requests(id),
    budget_type VARCHAR(50), -- economy, comfort, luxury
    total_budget DECIMAL(10,2),
    category_breakdown JSONB,
    cost_analysis JSONB,
    saving_suggestions JSONB,
    currency VARCHAR(3) DEFAULT 'CNY',
    created_at TIMESTAMP DEFAULT NOW()
);

-- 本地信息表
CREATE TABLE local_info (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    city VARCHAR(100),
    country VARCHAR(100),
    category VARCHAR(50), -- culture, safety, transport, etc.
    info_type VARCHAR(50),
    content TEXT,
    importance_level INTEGER DEFAULT 1,
    tags JSONB,
    data_source VARCHAR(100),
    last_updated TIMESTAMP DEFAULT NOW()
);
```

### 3.2 索引优化策略

```sql
-- 地理位置索引
CREATE INDEX idx_poi_location ON poi_database USING GIST(location);
CREATE INDEX idx_accommodation_location ON accommodations USING GIST(location);

-- 查询优化索引
CREATE INDEX idx_travel_requests_user_status ON travel_requests(user_id, status);
CREATE INDEX idx_poi_city_category ON poi_database(city, category);
CREATE INDEX idx_local_info_location ON local_info(city, country, category);

-- JSONB索引
CREATE INDEX idx_travel_notebooks_itineraries ON travel_notebooks USING GIN(daily_itineraries);
CREATE INDEX idx_poi_features ON poi_database USING GIN(features);
```

## 4. 开发阶段详细计划

### Phase 1: 基础架构搭建 (3周)

#### Week 1: 项目初始化和基础设施
**目标**: 建立开发环境和基础项目结构

**具体任务**:
```
├── travel_planner/
│   ├── __init__.py
│   ├── config/
│   │   ├── __init__.py
│   │   ├── settings.py          # 配置管理
│   │   └── database.py          # 数据库配置
│   ├── core/
│   │   ├── __init__.py
│   │   ├── agents/              # Agent基类
│   │   ├── tools/               # 工具基类
│   │   └── utils/               # 通用工具
│   ├── models/
│   │   ├── __init__.py
│   │   ├── database.py          # SQLAlchemy模型
│   │   └── schemas.py           # Pydantic模型
│   ├── api/
│   │   ├── __init__.py
│   │   ├── v1/                  # API v1版本
│   │   └── dependencies.py      # API依赖
│   └── tests/
│       ├── __init__.py
│       └── unit/
├── docker-compose.yml           # 开发环境
├── Dockerfile
├── requirements.txt
└── README.md
```

**开发任务**:
1. 创建项目目录结构
2. 配置开发环境 (Docker + PostgreSQL + Redis)
3. 建立基础的FastAPI应用框架
4. 配置数据库连接和ORM
5. 设置日志和配置管理系统

#### Week 2: 数据模型和基础Agent框架
**目标**: 建立数据模型和Agent基础架构

**开发任务**:
1. 实现所有数据库表和模型
2. 创建Agent基类和接口定义
3. 实现TravelNotebook核心数据结构
4. 建立Agent间通信基础机制
5. 编写基础的单元测试

**代码示例**:
```python
# core/agents/base_agent.py
from abc import ABC, abstractmethod
from agentscope.agent import ReActAgent
from agentscope.tool import Toolkit, ToolResponse

class TravelAgentBase(ReActAgent):
    """旅行规划Agent基类"""
    
    def __init__(self, name: str, agent_type: str, **kwargs):
        super().__init__(name=name, **kwargs)
        self.agent_type = agent_type
        self.travel_notebook = None
        self.collaboration_channels = {}
    
    @abstractmethod
    async def process_request(self, request_data: dict) -> ToolResponse:
        """处理请求的抽象方法"""
        pass
    
    async def broadcast_info(self, target_agents: list, info_type: str, data: dict):
        """向其他Agent广播信息"""
        for agent in target_agents:
            await self.send_message(agent, {
                "type": info_type,
                "data": data,
                "sender": self.name
            })
```

#### Week 3: 工具系统和外部服务基础
**目标**: 建立工具系统和外部服务集成框架

**开发任务**:
1. 创建工具基类和工具管理器
2. 实现地图服务集成基础
3. 建立外部API调用框架
4. 实现缓存和限流机制
5. 配置监控和健康检查

### Phase 2: 核心Agent开发 (4周)

#### Week 4-5: POIResearchAgent 和 LocalExpertAgent
**目标**: 实现景点研究和本地专家Agent

**POIResearchAgent核心功能**:
```python
# agents/poi_research_agent.py
class POIResearchAgent(TravelAgentBase):
    def __init__(self, **kwargs):
        super().__init__(name="POIResearchAgent", agent_type="poi_research", **kwargs)
        self.poi_tools = [
            "search_attractions",
            "analyze_reviews", 
            "get_poi_details",
            "check_opening_hours"
        ]
    
    async def research_destination_pois(self, destination: str, preferences: dict) -> ToolResponse:
        """研究目的地景点"""
        # 1. 搜索景点
        attractions = await self.search_attractions(destination, preferences)
        
        # 2. 分析评价
        for attraction in attractions:
            reviews = await self.analyze_reviews(attraction['id'])
            attraction['review_summary'] = reviews
        
        # 3. 筛选和排序
        filtered_attractions = self.filter_by_preferences(attractions, preferences)
        
        # 4. 广播给其他Agent
        await self.broadcast_to_route_optimizer(filtered_attractions)
        await self.broadcast_to_budget_analyzer(filtered_attractions)
        
        return ToolResponse(
            content=[TextBlock(type="text", text=self.format_poi_results(filtered_attractions))],
            metadata={"attractions": filtered_attractions, "count": len(filtered_attractions)}
        )
```

**LocalExpertAgent核心功能**:
```python
# agents/local_expert_agent.py
class LocalExpertAgent(TravelAgentBase):
    def __init__(self, **kwargs):
        super().__init__(name="LocalExpertAgent", agent_type="local_expert", **kwargs)
        self.knowledge_base = LocalKnowledgeBase()
    
    async def provide_local_insights(self, destination: str) -> ToolResponse:
        """提供当地专家见解"""
        # 1. 文化和历史背景
        cultural_info = await self.get_cultural_background(destination)
        
        # 2. 实用生活信息
        practical_info = await self.get_practical_info(destination)
        
        # 3. 安全和法律信息
        safety_info = await self.get_safety_info(destination)
        
        # 4. 向所有Agent广播本地信息
        await self.broadcast_local_info_to_all_agents({
            "cultural": cultural_info,
            "practical": practical_info,
            "safety": safety_info
        })
        
        return ToolResponse(
            content=[TextBlock(type="text", text=self.format_local_guide(cultural_info, practical_info, safety_info))],
            metadata={"local_insights": True}
        )
```

#### Week 6-7: RouteOptimizationAgent 和 AccommodationAgent
**目标**: 实现路线优化和住宿规划Agent

**RouteOptimizationAgent核心算法**:
```python
# agents/route_optimization_agent.py
class RouteOptimizationAgent(TravelAgentBase):
    def __init__(self, **kwargs):
        super().__init__(name="RouteOptimizationAgent", agent_type="route_optimization", **kwargs)
        self.tsp_solver = TSPSolver()
        self.maps_client = GoogleMapsClient()
    
    async def optimize_daily_routes(self, pois: list, accommodation: dict, constraints: dict) -> ToolResponse:
        """优化每日路线"""
        optimized_routes = []
        
        for day, day_pois in enumerate(self.group_pois_by_day(pois), 1):
            # 1. TSP算法优化路径
            optimal_sequence = await self.tsp_solver.solve(day_pois, accommodation)
            
            # 2. 考虑时间窗口约束
            timed_sequence = self.apply_time_constraints(optimal_sequence, constraints)
            
            # 3. 计算交通方式和时间
            route_with_transport = await self.calculate_transportation(timed_sequence)
            
            optimized_routes.append({
                "day": day,
                "route": route_with_transport,
                "total_time": sum(poi['travel_time'] for poi in route_with_transport),
                "total_distance": sum(poi['distance'] for poi in route_with_transport)
            })
        
        # 广播给住宿和预算Agent
        await self.broadcast_route_info(optimized_routes)
        
        return ToolResponse(
            content=[TextBlock(type="text", text=self.format_route_plan(optimized_routes))],
            metadata={"routes": optimized_routes}
        )
```

#### Week 8: BudgetAnalysisAgent
**目标**: 实现预算分析和优化Agent

**BudgetAnalysisAgent核心功能**:
```python
# agents/budget_analysis_agent.py
class BudgetAnalysisAgent(TravelAgentBase):
    def __init__(self, **kwargs):
        super().__init__(name="BudgetAnalysisAgent", agent_type="budget_analysis", **kwargs)
        self.cost_calculator = CostCalculator()
        self.currency_converter = CurrencyConverter()
    
    async def analyze_comprehensive_budget(self, all_agent_data: dict) -> ToolResponse:
        """综合预算分析"""
        # 1. 收集所有Agent的成本信息
        poi_costs = all_agent_data.get('poi_costs', [])
        route_costs = all_agent_data.get('route_costs', {})
        accommodation_costs = all_agent_data.get('accommodation_costs', [])
        
        # 2. 成本分类和计算
        budget_breakdown = {
            "transportation": self.calculate_transport_costs(route_costs),
            "accommodation": self.calculate_accommodation_costs(accommodation_costs),
            "attractions": self.calculate_attraction_costs(poi_costs),
            "meals": self.estimate_meal_costs(all_agent_data),
            "shopping": self.estimate_shopping_budget(all_agent_data),
            "emergency": self.calculate_emergency_fund(all_agent_data)
        }
        
        # 3. 生成多档次方案
        budget_options = self.generate_budget_tiers(budget_breakdown)
        
        # 4. 省钱建议
        saving_tips = self.generate_saving_suggestions(budget_breakdown)
        
        return ToolResponse(
            content=[TextBlock(type="text", text=self.format_budget_analysis(budget_breakdown, budget_options, saving_tips))],
            metadata={"budget_analysis": budget_breakdown, "options": budget_options}
        )
```

### Phase 3: 工具和服务集成 (3周)

#### Week 9: 外部API集成
**目标**: 集成主要的外部服务API

**集成服务列表**:
1. **地图服务**: Google Maps API, 高德地图API
2. **旅游数据**: 携程API, 去哪儿API, TripAdvisor API
3. **住宿预订**: Booking.com API, Airbnb API
4. **交通查询**: 12306 API, 航班查询API

**API客户端实现**:
```python
# tools/external_apis/maps_client.py
class GoogleMapsClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = googlemaps.Client(key=api_key)
    
    async def calculate_route(self, origin: tuple, destination: tuple, mode: str = "driving") -> dict:
        """计算路线"""
        try:
            result = self.client.directions(origin, destination, mode=mode)
            return {
                "distance": result[0]['legs'][0]['distance']['value'],
                "duration": result[0]['legs'][0]['duration']['value'],
                "polyline": result[0]['overview_polyline']['points']
            }
        except Exception as e:
            logger.error(f"Route calculation failed: {e}")
            return None
    
    async def search_nearby_places(self, location: tuple, place_type: str, radius: int = 5000) -> list:
        """搜索附近地点"""
        try:
            result = self.client.places_nearby(
                location=location,
                radius=radius,
                type=place_type
            )
            return result.get('results', [])
        except Exception as e:
            logger.error(f"Nearby places search failed: {e}")
            return []
```

#### Week 10: MCP客户端和工具开发
**目标**: 实现MCP客户端和专用工具

**MCP工具实现**:
```python
# tools/mcp_tools/travel_tools.py
from agentscope.mcp import StatefulClientBase

class TravelMCPClient(StatefulClientBase):
    def __init__(self):
        super().__init__(
            name="travel_mcp",
            command="python",
            args=["-m", "travel_mcp_server"]
        )
    
    async def search_pois(self, destination: str, preferences: dict) -> dict:
        """通过MCP搜索POI"""
        return await self.call_tool("search_pois", {
            "destination": destination,
            "preferences": preferences
        })
    
    async def analyze_reviews(self, poi_id: str) -> dict:
        """分析POI评价"""
        return await self.call_tool("analyze_reviews", {
            "poi_id": poi_id
        })
```

#### Week 11: 缓存和性能优化
**目标**: 实现缓存策略和性能优化

**缓存策略**:
```python
# core/cache/cache_manager.py
class CacheManager:
    def __init__(self, redis_client):
        self.redis = redis_client
        self.default_ttl = 3600  # 1 hour
    
    async def cache_poi_data(self, key: str, data: dict, ttl: int = None):
        """缓存POI数据"""
        ttl = ttl or self.default_ttl
        await self.redis.setex(key, ttl, json.dumps(data))
    
    async def get_cached_poi_data(self, key: str) -> dict:
        """获取缓存的POI数据"""
        cached = await self.redis.get(key)
        return json.loads(cached) if cached else None
    
    async def cache_route_calculation(self, origin: tuple, destination: tuple, result: dict):
        """缓存路线计算结果"""
        cache_key = f"route:{hash((origin, destination))}"
        await self.cache_poi_data(cache_key, result, ttl=1800)  # 30 minutes
```

### Phase 4: 协作机制完善 (2周)

#### Week 12: 实时监控和动态重规划
**目标**: 实现实时监控和动态重规划功能

**实时监控系统**:
```python
# core/monitoring/real_time_monitor.py
class RealTimeMonitor:
    def __init__(self, travel_notebook):
        self.travel_notebook = travel_notebook
        self.event_handlers = {
            "location_change": self.handle_location_change,
            "time_delay": self.handle_time_delay,
            "external_event": self.handle_external_event
        }
        self.websocket_connections = {}
    
    async def start_monitoring(self, request_id: str):
        """开始监控旅行状态"""
        while True:
            # 检查各种变化
            changes = await self.detect_changes(request_id)
            
            if changes:
                # 评估重规划必要性
                replanning_plan = await self.evaluate_replanning_necessity(changes)
                
                if replanning_plan:
                    # 通知用户
                    await self.notify_user(request_id, replanning_plan)
                    
                    # 等待用户确认
                    user_response = await self.wait_for_user_response(request_id)
                    
                    if user_response.get('approved'):
                        # 执行重规划
                        await self.execute_replanning(request_id, replanning_plan)
            
            # 等待下次检查
            await asyncio.sleep(60)  # 每分钟检查一次
```

#### Week 13: 错误处理和恢复机制
**目标**: 完善错误处理和系统恢复机制

**错误处理框架**:
```python
# core/error_handling/error_handler.py
class ErrorHandler:
    def __init__(self):
        self.retry_strategies = {
            "api_timeout": self.retry_with_backoff,
            "rate_limit": self.retry_after_delay,
            "service_unavailable": self.fallback_to_cache
        }
    
    async def handle_agent_error(self, agent_name: str, error: Exception, context: dict):
        """处理Agent执行错误"""
        error_type = self.classify_error(error)
        
        # 记录错误
        await self.log_error(agent_name, error, context)
        
        # 尝试恢复
        recovery_strategy = self.retry_strategies.get(error_type)
        if recovery_strategy:
            return await recovery_strategy(agent_name, context)
        
        # 如果无法恢复，降级处理
        return await self.fallback_processing(agent_name, context)
```

### Phase 5: API和用户接口 (2周)

#### Week 14: RESTful API实现
**目标**: 实现完整的RESTful API

**API路由设计**:
```python
# api/v1/travel.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

router = APIRouter(prefix="/api/v1/travel", tags=["travel"])

@router.post("/plan", response_model=TravelPlanResponse)
async def create_travel_plan(
    request: TravelPlanRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建旅行规划"""
    try:
        # 1. 创建旅行请求记录
        travel_request = await create_travel_request(db, request, current_user.id)
        
        # 2. 启动Multi-Agent规划流程
        planner_agent = TravelPlannerAgent()
        planning_result = await planner_agent.plan_travel(travel_request)
        
        # 3. 返回规划结果
        return TravelPlanResponse(
            id=travel_request.id,
            status="planning",
            estimated_completion_time=planning_result.estimated_time
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/plan/{plan_id}", response_model=TravelPlanDetail)
async def get_travel_plan(
    plan_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取旅行规划详情"""
    plan = await get_travel_plan_by_id(db, plan_id, current_user.id)
    if not plan:
        raise HTTPException(status_code=404, detail="Travel plan not found")
    
    return TravelPlanDetail.from_orm(plan)

@router.websocket("/ws/{plan_id}")
async def websocket_endpoint(websocket: WebSocket, plan_id: str):
    """WebSocket连接，实时推送规划进度"""
    await websocket.accept()
    
    try:
        # 注册WebSocket连接
        await register_websocket_connection(plan_id, websocket)
        
        # 保持连接并处理消息
        while True:
            data = await websocket.receive_text()
            # 处理客户端消息
            await handle_websocket_message(plan_id, data)
    
    except WebSocketDisconnect:
        await unregister_websocket_connection(plan_id, websocket)
```

#### Week 15: WebSocket实时通信
**目标**: 实现实时状态推送和用户交互

**WebSocket管理器**:
```python
# api/websocket/connection_manager.py
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
    
    async def connect(self, plan_id: str, websocket: WebSocket):
        """建立WebSocket连接"""
        await websocket.accept()
        if plan_id not in self.active_connections:
            self.active_connections[plan_id] = []
        self.active_connections[plan_id].append(websocket)
    
    async def disconnect(self, plan_id: str, websocket: WebSocket):
        """断开WebSocket连接"""
        if plan_id in self.active_connections:
            self.active_connections[plan_id].remove(websocket)
    
    async def send_personal_message(self, plan_id: str, message: dict):
        """发送消息给特定计划的所有连接"""
        if plan_id in self.active_connections:
            for connection in self.active_connections[plan_id]:
                await connection.send_json(message)
    
    async def broadcast_agent_update(self, plan_id: str, agent_name: str, update: dict):
        """广播Agent状态更新"""
        message = {
            "type": "agent_update",
            "agent": agent_name,
            "data": update,
            "timestamp": datetime.now().isoformat()
        }
        await self.send_personal_message(plan_id, message)
```

### Phase 6: 测试和部署 (2周)

#### Week 16: 测试和质量保证
**目标**: 完整的测试覆盖和质量保证

**测试策略**:
1. **单元测试**: 每个Agent和工具的独立测试
2. **集成测试**: Agent间协作测试
3. **端到端测试**: 完整旅行规划流程测试
4. **性能测试**: 并发处理和响应时间测试
5. **压力测试**: 系统负载测试

**测试用例示例**:
```python
# tests/integration/test_agent_collaboration.py
class TestAgentCollaboration:
    async def test_complete_planning_workflow(self):
        """测试完整的规划工作流程"""
        # 1. 创建测试请求
        request = TravelPlanRequest(
            destination="Tokyo",
            duration=5,
            budget_range="moderate",
            travel_style="culture",
            group_size=2
        )
        
        # 2. 启动规划流程
        planner = TravelPlannerAgent()
        result = await planner.plan_travel(request)
        
        # 3. 验证结果
        assert result.status == "completed"
        assert len(result.daily_itineraries) == 5
        assert result.budget_breakdown is not None
        
        # 4. 验证Agent协作
        assert all(agent.status == "completed" for agent in result.agent_states)

# tests/performance/test_concurrent_planning.py
class TestConcurrentPlanning:
    async def test_multiple_concurrent_requests(self):
        """测试并发规划请求处理"""
        # 创建多个并发请求
        requests = [create_test_request() for _ in range(10)]
        
        # 并发执行
        results = await asyncio.gather(*[
            process_travel_request(req) for req in requests
        ])
        
        # 验证所有请求都成功处理
        assert all(result.status == "completed" for result in results)
```

#### Week 17: 部署和监控
**目标**: 生产环境部署和监控配置

**Docker部署配置**:
```yaml
# docker-compose.prod.yml
version: '3.8'
services:
  travel-planner-api:
    build: .
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/travel_planner
      - REDIS_URL=redis://redis:6379
      - ENVIRONMENT=production
    depends_on:
      - db
      - redis
    ports:
      - "8000:8000"
    
  db:
    image: postgres:14
    environment:
      POSTGRES_DB: travel_planner
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass
    volumes:
      - postgres_data:/var/lib/postgresql/data
    
  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
    
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
    
  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana_data:/var/lib/grafana

volumes:
  postgres_data:
  redis_data:
  grafana_data:
```

**Kubernetes部署配置**:
```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: travel-planner-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: travel-planner-api
  template:
    metadata:
      labels:
        app: travel-planner-api
    spec:
      containers:
      - name: api
        image: travel-planner:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: travel-planner-secrets
              key: database-url
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: travel-planner-secrets
              key: redis-url
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
```

## 5. 监控和运维策略

### 5.1 监控指标
- **业务指标**: 规划成功率、用户满意度、响应时间
- **技术指标**: API响应时间、数据库连接数、内存使用
- **Agent指标**: Agent执行时间、协作效率、错误率

### 5.2 日志策略
- **结构化日志**: 使用JSON格式，便于分析
- **分级记录**: ERROR、WARN、INFO、DEBUG
- **链路追踪**: 使用Jaeger进行分布式追踪

### 5.3 报警机制
- **实时报警**: 系统异常、性能瓶颈
- **趋势报警**: 用户增长、资源使用趋势
- **业务报警**: 规划失败率超标、用户投诉

## 6. 总结和后续规划

### 6.1 交付成果
- 完整的Multi-Agent旅行规划系统
- 5个专业化Agent的实现
- RESTful API和WebSocket接口
- 数据库和缓存系统
- 监控和运维体系

### 6.2 技术亮点
- 基于AgentScope的Multi-Agent协作
- 实时监控和动态重规划
- 高性能的并发处理能力
- 完善的错误处理和恢复机制

### 6.3 后续优化方向
1. **AI能力增强**: 集成大语言模型提升智能化水平
2. **个性化优化**: 基于用户行为的机器学习推荐
3. **国际化扩展**: 支持多语言和多地区
4. **移动端适配**: 开发移动端应用
5. **商业化功能**: 预订集成、收益分成等

这个开发计划为期17周，涵盖了从基础架构到生产部署的完整流程，确保交付一个高质量的旅行规划Multi-Agent系统。