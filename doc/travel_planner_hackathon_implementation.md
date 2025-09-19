# 黑客松旅行规划Multi-Agent系统 - 快速实现方案

基于AgentScope框架的KISS原则实现 - 专为黑客松优化的轻量级方案

## 🎯 项目目标

构建一个**可演示、可运行**的旅行规划Multi-Agent系统，展示Agent协作能力，**无需复杂数据库**，重点突出**智能协作**和**用户体验**。

## 🏗️ 简化架构设计

```
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Web界面                          │
│               (简单HTML + WebSocket)                        │
├─────────────────────────────────────────────────────────────┤
│                TravelPlannerAgent                           │
│                   (主协调器)                                │
├─────────────────────────────────────────────────────────────┤
│    POIAgent  │  RouteAgent  │  LocalAgent  │  BudgetAgent   │
│   (景点搜索) │  (路线优化)  │  (当地信息)  │  (预算分析)    │
├─────────────────────────────────────────────────────────────┤
│              共享内存字典 (TravelNotebook)                  │
│                   (替代数据库)                              │
├─────────────────────────────────────────────────────────────┤
│         搜索工具(MCP)  │  地图工具  │  模拟数据源           │
└─────────────────────────────────────────────────────────────┘
```

## 📁 项目结构 (极简版)

```
travel_planner_hackathon/
├── app.py                    # FastAPI主应用 
├── agents/
│   ├── __init__.py
│   ├── travel_planner.py     # 主协调Agent
│   ├── poi_agent.py          # 景点研究Agent
│   ├── route_agent.py        # 路线优化Agent
│   ├── local_agent.py        # 当地专家Agent
│   └── budget_agent.py       # 预算分析Agent
├── tools/
│   ├── __init__.py
│   ├── search_mcp.py         # 搜索MCP工具
│   ├── maps_tool.py          # 地图工具
│   └── data_sources.py       # 模拟数据源
├── models/
│   ├── __init__.py
│   └── data_models.py        # 数据模型
├── static/
│   ├── index.html           # 前端界面
│   ├── style.css
│   └── app.js
├── travel_notebook.py       # 共享数据存储
├── config.py               # 配置文件
├── requirements.txt
└── README.md
```

## 🚀 核心实现代码

### 1. 主应用 (app.py)

```python
# app.py
import asyncio
import json
from datetime import datetime
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Dict, List

from agents.travel_planner import TravelPlannerAgent
from travel_notebook import TravelNotebook
from config import get_settings

app = FastAPI(title="Travel Planner Hackathon")
app.mount("/static", StaticFiles(directory="static"), name="static")

# 全局状态管理
active_sessions: Dict[str, dict] = {}
settings = get_settings()

class TravelRequest(BaseModel):
    destination: str
    duration: int
    budget: str
    travel_style: str
    group_size: int = 1

@app.get("/")
async def get_index():
    with open("static/index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

@app.post("/api/plan")
async def create_travel_plan(request: TravelRequest):
    """创建旅行规划"""
    session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # 创建会话
    travel_notebook = TravelNotebook()
    planner_agent = TravelPlannerAgent(
        name="TravelPlanner",
        travel_notebook=travel_notebook,
        settings=settings
    )
    
    active_sessions[session_id] = {
        "planner": planner_agent,
        "notebook": travel_notebook,
        "request": request.dict(),
        "status": "planning"
    }
    
    return {"session_id": session_id, "status": "created"}

@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket实时通信"""
    await websocket.accept()
    
    if session_id not in active_sessions:
        await websocket.send_json({"error": "Session not found"})
        return
    
    try:
        session = active_sessions[session_id]
        planner = session["planner"]
        request_data = session["request"]
        
        # 启动规划流程
        async def send_updates():
            async for update in planner.plan_travel_with_updates(request_data):
                await websocket.send_json(update)
        
        await send_updates()
        
    except WebSocketDisconnect:
        print(f"WebSocket disconnected: {session_id}")
    except Exception as e:
        await websocket.send_json({"error": str(e)})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### 2. 共享数据存储 (travel_notebook.py)

```python
# travel_notebook.py
from typing import Dict, List, Any
from datetime import datetime
import json

class TravelNotebook:
    """内存中的旅行规划笔记本 - 替代数据库"""
    
    def __init__(self):
        self.data = {
            "request_info": {},
            "destination_analysis": "",
            "pois": [],
            "routes": [],
            "accommodations": [],
            "budget": {},
            "local_info": {},
            "agent_status": {},
            "timeline": [],
            "final_plan": {}
        }
        self.agents_data = {}  # Agent间共享数据
    
    def update_agent_status(self, agent_name: str, status: str, data: dict = None):
        """更新Agent状态"""
        self.data["agent_status"][agent_name] = {
            "status": status,
            "timestamp": datetime.now().isoformat(),
            "data": data or {}
        }
        self.log_timeline(f"{agent_name}: {status}")
    
    def share_data(self, from_agent: str, to_agent: str, data_type: str, data: Any):
        """Agent间数据共享"""
        if to_agent not in self.agents_data:
            self.agents_data[to_agent] = {}
        
        self.agents_data[to_agent][f"{from_agent}_{data_type}"] = {
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
        self.log_timeline(f"数据共享: {from_agent} -> {to_agent} ({data_type})")
    
    def get_shared_data(self, agent_name: str, data_type: str = None):
        """获取共享数据"""
        agent_data = self.agents_data.get(agent_name, {})
        if data_type:
            return {k: v for k, v in agent_data.items() if data_type in k}
        return agent_data
    
    def log_timeline(self, event: str):
        """记录时间线"""
        self.data["timeline"].append({
            "time": datetime.now().isoformat(),
            "event": event
        })
    
    def get_current_state(self):
        """获取当前状态"""
        return {
            "data": self.data,
            "agents_data": self.agents_data,
            "progress": len([s for s in self.data["agent_status"].values() 
                           if s["status"] == "completed"]) / 4  # 4个Agent
        }
```

### 3. 主协调Agent (agents/travel_planner.py)

```python
# agents/travel_planner.py
import asyncio
from typing import AsyncGenerator, Dict, Any
from agentscope.agent import ReActAgent
from agentscope.model import OpenAIChatModel
from agentscope.memory import InMemoryMemory
from agentscope.formatter import KimiMultiAgentFormatter

from .poi_agent import POIAgent
from .route_agent import RouteAgent
from .local_agent import LocalAgent
from .budget_agent import BudgetAgent

class TravelPlannerAgent(ReActAgent):
    """主协调Agent"""
    
    def __init__(self, name: str, travel_notebook, settings):
        # 使用你现有的模型配置
        model = OpenAIChatModel(
            model_name="kimi-k2-turbo-preview", 
            api_key=settings.api_key,
            client_args={"base_url": settings.base_url}
        )
        
        super().__init__(
            name=name,
            model=model,
            formatter=KimiMultiAgentFormatter(),
            memory=InMemoryMemory(),
            sys_prompt="""你是旅行规划系统的主协调器。负责：
1. 分析用户需求
2. 协调各专家Agent
3. 整合最终方案
4. 实时向用户报告进度"""
        )
        
        self.travel_notebook = travel_notebook
        self.settings = settings
        
        # 初始化专家Agents
        self.agents = {
            "poi": POIAgent("POIAgent", travel_notebook, settings),
            "route": RouteAgent("RouteAgent", travel_notebook, settings),
            "local": LocalAgent("LocalAgent", travel_notebook, settings),
            "budget": BudgetAgent("BudgetAgent", travel_notebook, settings)
        }
    
    async def plan_travel_with_updates(self, request: Dict[str, Any]) -> AsyncGenerator[Dict, None]:
        """带实时更新的旅行规划"""
        
        # 1. 分析用户需求
        yield {"type": "status", "message": "正在分析您的旅行需求...", "progress": 0.1}
        
        self.travel_notebook.data["request_info"] = request
        self.travel_notebook.log_timeline("开始旅行规划")
        
        # 2. 并行启动Agent任务
        yield {"type": "status", "message": "启动专家Agent分析...", "progress": 0.2}
        
        tasks = [
            self._run_agent_with_updates("poi", request),
            self._run_agent_with_updates("local", request)
        ]
        
        # 等待基础分析完成
        await asyncio.gather(*tasks)
        yield {"type": "status", "message": "基础分析完成，开始路线优化...", "progress": 0.6}
        
        # 3. 路线优化 (依赖POI数据)
        await self._run_agent_with_updates("route", request)
        yield {"type": "status", "message": "路线优化完成，进行预算分析...", "progress": 0.8}
        
        # 4. 预算分析 (依赖所有数据)
        await self._run_agent_with_updates("budget", request)
        
        # 5. 生成最终方案
        yield {"type": "status", "message": "生成最终旅行方案...", "progress": 0.9}
        final_plan = await self._generate_final_plan()
        
        yield {
            "type": "completed",
            "message": "旅行规划完成！",
            "progress": 1.0,
            "plan": final_plan,
            "notebook": self.travel_notebook.get_current_state()
        }
    
    async def _run_agent_with_updates(self, agent_type: str, request: Dict):
        """运行Agent并更新状态"""
        agent = self.agents[agent_type]
        self.travel_notebook.update_agent_status(agent_type, "running")
        
        try:
            result = await agent.process_request(request)
            self.travel_notebook.update_agent_status(agent_type, "completed", result)
        except Exception as e:
            self.travel_notebook.update_agent_status(agent_type, "error", {"error": str(e)})
            raise
    
    async def _generate_final_plan(self) -> Dict:
        """生成最终旅行方案"""
        notebook_data = self.travel_notebook.data
        
        return {
            "destination": notebook_data["request_info"]["destination"],
            "duration": notebook_data["request_info"]["duration"],
            "daily_itinerary": self._generate_daily_itinerary(),
            "accommodation_suggestions": notebook_data["accommodations"],
            "budget_summary": notebook_data["budget"],
            "local_tips": notebook_data["local_info"],
            "total_estimated_cost": notebook_data["budget"].get("total", 0)
        }
    
    def _generate_daily_itinerary(self) -> List[Dict]:
        """生成每日行程"""
        # 简化实现：基于POI和路线数据生成
        pois = self.travel_notebook.data["pois"]
        routes = self.travel_notebook.data["routes"]
        duration = self.travel_notebook.data["request_info"]["duration"]
        
        daily_plans = []
        pois_per_day = len(pois) // duration if pois else 0
        
        for day in range(1, duration + 1):
            start_idx = (day - 1) * pois_per_day
            end_idx = start_idx + pois_per_day
            day_pois = pois[start_idx:end_idx] if pois else []
            
            daily_plans.append({
                "day": day,
                "date": f"第{day}天",
                "attractions": day_pois,
                "estimated_cost": sum(poi.get("cost", 0) for poi in day_pois),
                "travel_time": sum(poi.get("duration", 60) for poi in day_pois),
                "highlights": [poi.get("name", "") for poi in day_pois[:2]]
            })
        
        return daily_plans
```

### 4. POI搜索Agent (agents/poi_agent.py)

```python
# agents/poi_agent.py
import asyncio
from agentscope.agent import ReActAgent
from agentscope.model import OpenAIChatModel
from agentscope.memory import InMemoryMemory
from agentscope.formatter import KimiMultiAgentFormatter
from agentscope.tool import Toolkit

from tools.search_mcp import create_search_tool
from tools.data_sources import get_mock_poi_data

class POIAgent(ReActAgent):
    """景点研究专家Agent"""
    
    def __init__(self, name: str, travel_notebook, settings):
        model = OpenAIChatModel(
            model_name="kimi-k2-turbo-preview",
            api_key=settings.api_key,
            client_args={"base_url": settings.base_url}
        )
        
        # 创建工具包
        toolkit = Toolkit()
        toolkit.register_tool_function(create_search_tool(settings))
        
        super().__init__(
            name=name,
            model=model,
            formatter=KimiMultiAgentFormatter(),
            memory=InMemoryMemory(),
            toolkit=toolkit,
            sys_prompt="""你是专业的景点研究专家。任务：
1. 根据目的地搜索热门景点
2. 分析景点特色和适合人群
3. 收集实用信息(开放时间、门票等)
4. 推荐个性化景点组合

输出格式：每个景点包含名称、评分、简介、开放时间、门票价格、推荐理由"""
        )
        
        self.travel_notebook = travel_notebook
    
    async def process_request(self, request: dict) -> dict:
        """处理POI搜索请求"""
        destination = request["destination"]
        travel_style = request["travel_style"]
        duration = request["duration"]
        
        # 1. 搜索景点
        search_query = f"{destination} 旅游景点 {travel_style}"
        pois = await self._search_pois(search_query, duration)
        
        # 2. 筛选和分析
        analyzed_pois = await self._analyze_pois(pois, request)
        
        # 3. 保存到notebook
        self.travel_notebook.data["pois"] = analyzed_pois
        
        # 4. 分享给其他Agent
        self.travel_notebook.share_data(
            "poi", "route", "poi_locations", 
            [{"name": p["name"], "location": p["location"], "duration": p["visit_duration"]} 
             for p in analyzed_pois]
        )
        
        self.travel_notebook.share_data(
            "poi", "budget", "poi_costs",
            [{"name": p["name"], "cost": p["ticket_price"]} for p in analyzed_pois]
        )
        
        return {"poi_count": len(analyzed_pois), "pois": analyzed_pois}
    
    async def _search_pois(self, query: str, duration: int) -> list:
        """搜索POI"""
        # 优先使用搜索工具，如果失败则使用模拟数据
        try:
            # 调用搜索工具
            from agentscope.message import Msg
            search_msg = Msg(name="user", content=f"搜索: {query}", role="user")
            result = await self(search_msg)
            
            # 解析搜索结果
            pois = self._parse_search_results(result.content, duration)
            if pois:
                return pois
        except Exception as e:
            print(f"搜索工具失败，使用模拟数据: {e}")
        
        # 使用模拟数据
        return get_mock_poi_data(query, duration)
    
    def _parse_search_results(self, content: str, duration: int) -> list:
        """解析搜索结果"""
        # 简化：从搜索结果中提取POI信息
        # 实际实现可以使用NLP或正则表达式
        lines = content.split('\n')
        pois = []
        
        for line in lines[:duration * 3]:  # 每天3个景点
            if any(keyword in line for keyword in ['景点', '公园', '博物馆', '寺庙', '广场']):
                pois.append({
                    "name": line.strip()[:20],  # 简化提取
                    "description": line.strip(),
                    "rating": 4.2,  # 默认评分
                    "location": {"lat": 0, "lng": 0},  # 待地图工具填充
                    "ticket_price": 50,  # 默认价格
                    "visit_duration": 120,  # 默认2小时
                    "opening_hours": "9:00-17:00"
                })
        
        return pois[:duration * 2]  # 控制数量
    
    async def _analyze_pois(self, pois: list, request: dict) -> list:
        """分析和筛选POI"""
        # 根据旅行风格调整推荐
        style_weights = {
            "文化": ["博物馆", "古迹", "寺庙"],
            "自然": ["公园", "山", "湖"],
            "美食": ["市场", "小吃街", "餐厅"],
            "休闲": ["公园", "咖啡", "购物"]
        }
        
        travel_style = request.get("travel_style", "休闲")
        preferred_keywords = style_weights.get(travel_style, [])
        
        # 简单评分和排序
        for poi in pois:
            score = poi["rating"]
            for keyword in preferred_keywords:
                if keyword in poi["description"]:
                    score += 1
            poi["recommendation_score"] = score
        
        # 按评分排序
        pois.sort(key=lambda x: x["recommendation_score"], reverse=True)
        
        return pois
```

### 5. 搜索MCP工具 (tools/search_mcp.py)

```python
# tools/search_mcp.py
from agentscope.mcp import StatefulClientBase, StdIOStatefulClient
from agentscope.tool import ToolResponse
from agentscope.message import TextBlock

def create_search_tool(settings):
    """创建搜索工具 - 参考meta_planner示例"""
    
    # 创建Tavily MCP客户端
    tavily_client = StdIOStatefulClient(
        name="tavily_search",
        command="npx",
        args=["-y", "tavily-mcp@latest"],
        env={"TAVILY_API_KEY": settings.tavily_api_key}
    )
    
    async def search_travel_info(query: str) -> ToolResponse:
        """搜索旅行相关信息"""
        try:
            # 连接MCP客户端
            await tavily_client.connect()
            
            # 调用搜索工具
            search_result = await tavily_client.call_tool("search", {
                "query": query + " 旅游攻略",
                "max_results": 10
            })
            
            # 处理搜索结果
            if search_result and "results" in search_result:
                content = []
                for result in search_result["results"][:5]:  # 限制结果数量
                    content.append(f"**{result.get('title', '')}**\n{result.get('content', '')}\n")
                
                return ToolResponse(
                    content=[TextBlock(type="text", text="\n".join(content))],
                    metadata={"search_results": search_result["results"]}
                )
            else:
                return ToolResponse(
                    content=[TextBlock(type="text", text="搜索暂时无结果，请稍后重试")],
                    metadata={"error": "no_results"}
                )
        
        except Exception as e:
            print(f"搜索错误: {e}")
            return ToolResponse(
                content=[TextBlock(type="text", text=f"搜索服务暂时不可用: {str(e)}")],
                metadata={"error": str(e)}
            )
        finally:
            try:
                await tavily_client.close()
            except:
                pass
    
    return search_travel_info
```

### 6. 模拟数据源 (tools/data_sources.py)

```python
# tools/data_sources.py
import random

def get_mock_poi_data(query: str, duration: int) -> list:
    """获取模拟POI数据"""
    
    # 基于查询关键词的模拟数据
    base_pois = {
        "tokyo": [
            {"name": "浅草寺", "type": "文化", "rating": 4.5, "cost": 0, "duration": 90},
            {"name": "东京塔", "type": "观光", "rating": 4.3, "cost": 120, "duration": 120},
            {"name": "新宿御苑", "type": "自然", "rating": 4.4, "cost": 50, "duration": 180},
            {"name": "银座", "type": "购物", "rating": 4.2, "cost": 0, "duration": 240},
            {"name": "上野公园", "type": "文化", "rating": 4.6, "cost": 0, "duration": 150},
            {"name": "明治神宫", "type": "文化", "rating": 4.5, "cost": 0, "duration": 100}
        ],
        "beijing": [
            {"name": "故宫", "type": "文化", "rating": 4.8, "cost": 80, "duration": 240},
            {"name": "长城", "type": "文化", "rating": 4.9, "cost": 45, "duration": 360},
            {"name": "天坛", "type": "文化", "rating": 4.6, "cost": 35, "duration": 120},
            {"name": "颐和园", "type": "自然", "rating": 4.7, "cost": 60, "duration": 180},
            {"name": "王府井", "type": "购物", "rating": 4.1, "cost": 0, "duration": 180},
            {"name": "南锣鼓巷", "type": "文化", "rating": 4.3, "cost": 0, "duration": 120}
        ]
    }
    
    # 检测查询关键词
    destination_key = None
    for key in base_pois.keys():
        if key in query.lower():
            destination_key = key
            break
    
    if not destination_key:
        destination_key = "beijing"  # 默认
    
    selected_pois = base_pois[destination_key]
    
    # 根据duration选择POI数量
    poi_count = min(duration * 2, len(selected_pois))
    result_pois = random.sample(selected_pois, poi_count)
    
    # 格式化数据
    formatted_pois = []
    for poi in result_pois:
        formatted_pois.append({
            "name": poi["name"],
            "description": f"{poi['name']}是著名的{poi['type']}景点",
            "rating": poi["rating"],
            "location": {"lat": 39.9 + random.uniform(-0.1, 0.1), 
                        "lng": 116.4 + random.uniform(-0.1, 0.1)},
            "ticket_price": poi["cost"],
            "visit_duration": poi["duration"],
            "opening_hours": "9:00-17:00",
            "category": poi["type"]
        })
    
    return formatted_pois

def get_mock_route_data(pois: list) -> dict:
    """获取模拟路线数据"""
    if not pois:
        return {}
    
    return {
        "total_distance": random.uniform(50, 200),  # km
        "total_time": sum(poi.get("visit_duration", 120) for poi in pois) + 60 * len(pois),  # 包含交通时间
        "transportation": "地铁+步行",
        "estimated_cost": len(pois) * 20,  # 交通费
        "route_points": [poi["location"] for poi in pois if "location" in poi]
    }

def get_mock_budget_data(pois: list, duration: int) -> dict:
    """获取模拟预算数据"""
    poi_costs = sum(poi.get("ticket_price", 0) for poi in pois)
    
    return {
        "accommodation": duration * 300,  # 每晚300元
        "meals": duration * 150,  # 每天150元
        "transportation": 200,  # 交通费
        "attractions": poi_costs,  # 景点门票
        "shopping": 500,  # 购物预算
        "total": duration * 450 + poi_costs + 700,
        "currency": "CNY"
    }

def get_mock_local_info(destination: str) -> dict:
    """获取模拟当地信息"""
    base_info = {
        "tokyo": {
            "culture": "日本文化注重礼仪，进入寺庙需脱帽",
            "transportation": "建议购买一日券，地铁系统发达",
            "safety": "治安良好，夜间出行相对安全",
            "tips": ["随身携带现金", "学会基本日语问候", "注意垃圾分类"]
        },
        "beijing": {
            "culture": "中华文化深厚，尊重历史古迹",
            "transportation": "地铁便利，注意高峰期拥挤",
            "safety": "整体安全，注意保管财物",
            "tips": ["备好身份证", "下载地图APP", "注意防雾霾"]
        }
    }
    
    return base_info.get(destination.lower(), base_info["beijing"])
```

### 7. 简单前端 (static/index.html)

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI旅行规划师</title>
    <link rel="stylesheet" href="/static/style.css">
</head>
<body>
    <div class="container">
        <header>
            <h1>🌏 AI旅行规划师</h1>
            <p>智能Multi-Agent协作，为您定制专属旅行方案</p>
        </header>

        <div class="planning-form" id="planningForm">
            <h2>开始规划您的旅行</h2>
            <form id="travelForm">
                <div class="form-group">
                    <label>目的地:</label>
                    <input type="text" id="destination" required placeholder="例: 东京">
                </div>
                
                <div class="form-group">
                    <label>旅行天数:</label>
                    <select id="duration" required>
                        <option value="3">3天</option>
                        <option value="5" selected>5天</option>
                        <option value="7">7天</option>
                    </select>
                </div>
                
                <div class="form-group">
                    <label>预算范围:</label>
                    <select id="budget" required>
                        <option value="经济">经济型 (1000-3000元)</option>
                        <option value="舒适" selected>舒适型 (3000-8000元)</option>
                        <option value="豪华">豪华型 (8000元以上)</option>
                    </select>
                </div>
                
                <div class="form-group">
                    <label>旅行风格:</label>
                    <select id="travelStyle" required>
                        <option value="文化">文化探索</option>
                        <option value="自然">自然风光</option>
                        <option value="美食">美食之旅</option>
                        <option value="休闲" selected>休闲度假</option>
                    </select>
                </div>
                
                <button type="submit">开始AI规划 🚀</button>
            </form>
        </div>

        <div class="planning-status" id="planningStatus" style="display: none;">
            <div class="agent-grid">
                <div class="agent-card" id="poi-agent">
                    <h3>🎯 景点专家</h3>
                    <div class="status">准备中...</div>
                    <div class="progress-bar"><div class="progress"></div></div>
                </div>
                
                <div class="agent-card" id="route-agent">
                    <h3>🗺️ 路线专家</h3>
                    <div class="status">准备中...</div>
                    <div class="progress-bar"><div class="progress"></div></div>
                </div>
                
                <div class="agent-card" id="local-agent">
                    <h3>🏠 当地专家</h3>
                    <div class="status">准备中...</div>
                    <div class="progress-bar"><div class="progress"></div></div>
                </div>
                
                <div class="agent-card" id="budget-agent">
                    <h3>💰 预算专家</h3>
                    <div class="status">准备中...</div>
                    <div class="progress-bar"><div class="progress"></div></div>
                </div>
            </div>
            
            <div class="main-progress">
                <h3>总体进度</h3>
                <div class="progress-bar main"><div class="progress"></div></div>
                <div class="status-text">正在初始化...</div>
            </div>
        </div>

        <div class="travel-plan" id="travelPlan" style="display: none;">
            <h2>🎉 您的专属旅行方案</h2>
            <div id="planContent"></div>
        </div>
    </div>

    <script src="/static/app.js"></script>
</body>
</html>
```

### 8. 配置文件 (config.py)

```python
# config.py
import os
from pydantic import BaseSettings

class Settings(BaseSettings):
    # API配置
    api_key: str = "sk-your-api-key"
    base_url: str = "https://api.moonshot.cn/v1"
    
    # 搜索配置
    tavily_api_key: str = "your-tavily-key"
    
    # 应用配置
    debug: bool = True
    
    class Config:
        env_file = ".env"

def get_settings():
    return Settings()
```

### 9. 启动脚本 (requirements.txt)

```txt
fastapi==0.104.1
uvicorn==0.24.0
websockets==12.0
agentscope>=0.1.0
pydantic==2.5.0
python-multipart==0.0.6
aiofiles==23.2.1
```

## 🎯 黑客松演示亮点

### 1. **实时Agent协作展示**
- WebSocket实时显示每个Agent的工作状态
- 可视化Agent间数据传递过程
- 展示并行处理和智能协作

### 2. **快速响应 (≤30秒)**
- 无数据库操作，全内存处理
- 并行Agent执行
- 优雅降级（搜索失败时使用模拟数据）

### 3. **完整的旅行方案**
- 个性化景点推荐
- 优化的路线规划
- 详细的预算分析
- 实用的当地信息

### 4. **技术展示价值**
- AgentScope Multi-Agent框架应用
- MCP工具集成示例
- 异步协作机制
- 实时Web界面

## 🚀 快速启动

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置环境变量
export API_KEY="your-api-key"
export TAVILY_API_KEY="your-tavily-key"

# 3. 启动应用
python app.py

# 4. 打开浏览器
# http://localhost:8000
```

## 💡 扩展思路

如果有时间，可以快速添加：
1. **地图可视化**: 集成简单的地图显示路线
2. **导出功能**: 生成PDF行程单
3. **语音交互**: 添加语音输入和播报
4. **社交分享**: 一键分享到社交媒体

这个方案专为黑客松优化：**快速开发、易于演示、技术亮点突出**！