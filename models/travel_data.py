#!/usr/bin/env python3
"""
旅行路书数据模型 - 与前端 mockData.js 兼容的 Pydantic 模型
"""

from typing import List, Optional
import random
from pydantic import BaseModel, Field


class TravelConfig(BaseModel):
    """旅行配置信息（对应前端 TravelConfig）"""
    location: str = Field(description="目的地城市")
    totalDays: int = Field(description="总天数", ge=1, le=30)
    startDate: str = Field(description="开始日期，格式 YYYY-MM-DD")
    title: str = Field(description="路书标题")


class RoutePoint(BaseModel):
    """路线点信息（对应前端 RoutePointsData）"""
    id: int = Field(description="路线点ID")
    x: int = Field(description="地图坐标X", ge=0, le=1000)
    y: int = Field(description="地图坐标Y", ge=0, le=800)
    name: str = Field(description="地点名称")
    type: str = Field(description="类型：start/attraction/hotel/restaurant/end")


class InfoCard(BaseModel):
    """信息卡片（对应前端 CardsData）"""
    id: str = Field(description="卡片唯一ID")
    type: str = Field(description="卡片类型：weather/attraction/hotel/restaurant")
    title: str = Field(description="卡片标题")
    content: str = Field(description="卡片内容描述")
    value: str = Field(description="价格或重要数值")
    status: str = Field(description="状态：available/busy/closed")
    statusText: str = Field(description="状态文本")
    icon: str = Field(description="图标emoji")
    pointTypes: List[str] = Field(description="适用的路线点类型")
    pointId: Optional[int] = Field(description="关联的路线点ID", default=None)


class ItineraryItem(BaseModel):
    """行程条目"""
    time: str = Field(description="时间，格式 HH:MM")
    type: str = Field(description="类型：start/attraction/restaurant/hotel/end")
    title: str = Field(description="活动标题")
    description: str = Field(description="详细描述")
    price: str = Field(description="价格信息")
    duration: str = Field(description="持续时间")
    icon: str = Field(description="图标emoji")


class DayItinerary(BaseModel):
    """单日行程（对应前端 ItineraryData）"""
    day: int = Field(description="第几天", ge=1)
    date: str = Field(description="具体日期，格式 YYYY-MM-DD")
    title: str = Field(description="当日标题")
    summary: str = Field(description="当日概览")
    items: List[ItineraryItem] = Field(description="当日详细行程")


class TravelPlanData(BaseModel):
    """完整的旅行方案数据（结构化输出模型）"""
    
    # 基础配置
    config: TravelConfig = Field(description="旅行基础配置")
    
    # 路线点（地图上的节点）
    route_points: List[RoutePoint] = Field(
        description="路线上的关键地点，用于地图显示",
        max_items=10
    )
    
    # 信息卡片
    cards: List[InfoCard] = Field(
        description="各种信息卡片：天气、景点、酒店、餐厅等",
        max_items=15
    )
    
    # 详细行程
    itinerary: List[DayItinerary] = Field(
        description="每日详细行程安排",
        max_items=15
    )


# 详细的前端数据结构
class RoutePoint(BaseModel):
    """路线点（对应 RoutePointsData）"""
    id: int = Field(description="路线点ID")
    x: int = Field(description="地图坐标X", ge=0, le=1000)
    y: int = Field(description="地图坐标Y", ge=0, le=800)
    name: str = Field(description="地点名称")
    type: str = Field(description="类型：start/attraction/hotel/restaurant/end")


class ExpandedContent(BaseModel):
    """卡片展开内容"""
    description: str = Field(description="详细描述")
    details: Optional[List[str]] = Field(description="详细信息列表", default=None)
    features: Optional[List[str]] = Field(description="特色功能", default=None)
    openHours: Optional[str] = Field(description="开放时间", default=None)
    transportation: Optional[str] = Field(description="交通信息", default=None)
    tips: Optional[str] = Field(description="游览建议", default=None)
    forecast: Optional[str] = Field(description="天气预报", default=None)
    suggestion: Optional[str] = Field(description="建议", default=None)
    reservation: Optional[str] = Field(description="预订信息", default=None)
    specialties: Optional[List[str]] = Field(description="特色菜品", default=None)


class InfoCard(BaseModel):
    """信息卡片（对应 CardsData）"""
    id: str = Field(description="卡片唯一ID")
    type: str = Field(description="卡片类型：weather/attraction/hotel/restaurant")
    title: str = Field(description="卡片标题")
    content: str = Field(description="卡片内容描述")
    value: str = Field(description="价格或重要数值")
    status: str = Field(description="状态：available/busy/closed")
    statusText: str = Field(description="状态文本")
    icon: str = Field(description="图标emoji")
    pointTypes: List[str] = Field(description="适用的路线点类型")
    pointId: Optional[int] = Field(description="关联的路线点ID", default=None)
    expandedContent: Optional[ExpandedContent] = Field(description="展开内容", default=None)


class ItineraryItem(BaseModel):
    """行程条目"""
    time: str = Field(description="时间，格式 HH:MM")
    type: str = Field(description="类型：start/attraction/restaurant/hotel/end")
    title: str = Field(description="活动标题")
    description: str = Field(description="详细描述")
    price: str = Field(description="价格信息")
    duration: str = Field(description="持续时间")
    icon: str = Field(description="图标emoji")


class DayItinerary(BaseModel):
    """单日行程（对应 ItineraryData）"""
    day: int = Field(description="第几天", ge=1)
    date: str = Field(description="具体日期，格式 YYYY-MM-DD")
    title: str = Field(description="当日标题")
    summary: str = Field(description="当日概览")
    items: List[ItineraryItem] = Field(description="当日详细行程")


class TravelConfig(BaseModel):
    """旅行配置（对应 TravelConfig）"""
    location: str = Field(description="目的地城市")
    totalDays: int = Field(description="总天数", ge=1, le=30)
    startDate: str = Field(description="开始日期，格式 YYYY-MM-DD")
    title: str = Field(description="路书标题")


# 前端兼容的完整数据模型
class FrontendTravelPlan(BaseModel):
    """完全匹配前端 mockData.js 的数据结构"""
    
    # 基础配置
    config: TravelConfig = Field(description="旅行基础配置")
    
    # 地图路线点
    route_points: List[RoutePoint] = Field(
        description="地图上的关键地点，包含坐标和类型",
        max_items=8
    )
    
    # 信息卡片
    cards: List[InfoCard] = Field(
        description="景点、酒店、餐厅等信息卡片",
        max_items=15
    )
    
    # 详细行程
    itinerary: List[DayItinerary] = Field(
        description="每日详细时间安排",
        max_items=15
    )

# 简化版本 - 如果完整版本太复杂
class SimpleTravelPlan(BaseModel):
    """简化的旅行方案数据 - 便于AI快速生成"""
    
    destination: str = Field(description="目的地")
    days: int = Field(description="旅行天数", ge=1, le=15)
    travel_type: str = Field(description="旅行类型：自驾游/亲子游/深度游等")
    budget_level: str = Field(description="预算级别：经济型/舒适型/豪华型")
    
    # 关键景点（最多5个）
    attractions: List[str] = Field(
        description="主要景点列表", 
        max_items=5
    )
    
    # 推荐酒店（最多3个）
    hotels: List[str] = Field(
        description="推荐酒店列表", 
        max_items=3
    )
    
    # 每日概要
    daily_summary: List[str] = Field(
        description="每日行程概要，按天数组织",
        max_items=15
    )


# 工具函数：坐标生成
def generate_route_coordinates(locations: List[str], days: int) -> List[RoutePoint]:
    """为景点生成合理的地图坐标"""
    points = []
    
    for i, location in enumerate(locations[:6]):  # 最多6个景点
        # 生成分布合理的坐标
        x = 150 + (i * 120) + random.randint(-30, 30)
        y = 100 + (i % 3) * 120 + random.randint(-40, 40)
        
        # 确保坐标在范围内
        x = max(50, min(950, x))
        y = max(50, min(750, y))
        
        point_type = 'start' if i == 0 else ('end' if i == len(locations) - 1 else 'attraction')
        
        points.append(RoutePoint(
            id=i,
            x=x,
            y=y,
            name=location,
            type=point_type
        ))
    
    return points


# 工具函数：简单转复杂数据转换
def transform_simple_to_frontend(simple_plan: SimpleTravelPlan, start_date: str = "2024-03-01") -> FrontendTravelPlan:
    """将SimpleTravelPlan转换为完整的FrontendTravelPlan"""
    from datetime import datetime, timedelta
    
    # 基础配置
    config = TravelConfig(
        location=simple_plan.destination,
        totalDays=simple_plan.days,
        startDate=start_date,
        title=f"{simple_plan.destination}{simple_plan.days}天{simple_plan.travel_type}"
    )
    
    # 生成路线点（景点）
    all_locations = simple_plan.attractions[:6]  # 最多6个景点
    route_points = generate_route_coordinates(all_locations, simple_plan.days)
    
    # 生成信息卡片
    cards = []
    
    # 天气卡片
    cards.append(InfoCard(
        id="weather-general",
        type="weather",
        title="当前天气",
        content=f"{simple_plan.destination}天气晴朗，适合出行",
        value="24°C",
        status="available",
        statusText="晴朗",
        icon="☀️",
        pointTypes=["all"],
        pointId=None
    ))
    
    # 景点卡片
    for i, attraction in enumerate(simple_plan.attractions[:5]):
        cards.append(InfoCard(
            id=f"attraction-{i}",
            type="attraction",
            title=attraction,
            content=f"{attraction}详细介绍",
            value="免费" if i % 2 == 0 else f"¥{80 + i * 40}",
            status="available",
            statusText="开放中",
            icon="🏛️" if i % 2 == 0 else "🗼",
            pointTypes=["attraction"],
            pointId=i if i < len(route_points) else None
        ))
    
    # 酒店卡片
    for i, hotel in enumerate(simple_plan.hotels[:3]):
        cards.append(InfoCard(
            id=f"hotel-{i}",
            type="hotel",
            title=hotel,
            content=f"{hotel}高级住宿",
            value=f"¥{600 + i * 200}",
            status="available",
            statusText="有房",
            icon="🏨",
            pointTypes=["hotel"],
            pointId=None
        ))
    
    # 生成详细行程
    itinerary = []
    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    
    for day in range(simple_plan.days):
        current_date = start_dt + timedelta(days=day)
        date_str = current_date.strftime("%Y-%m-%d")
        
        # 获取当日概要，如果没有则生成默认
        summary = simple_plan.daily_summary[day] if day < len(simple_plan.daily_summary) else f"第{day+1}天行程"
        
        items = []
        # 简单的一日行程：上午景点 + 午餐 + 下午景点 + 晚餐 + 住宿
        if day < len(simple_plan.attractions):
            items.append(ItineraryItem(
                time="09:00",
                type="attraction",
                title=simple_plan.attractions[day],
                description=f"游览{simple_plan.attractions[day]}",
                price="¥120",
                duration="2小时",
                icon="🏛️"
            ))
        
        items.append(ItineraryItem(
            time="12:00",
            type="restaurant",
            title="当地特色餐厅",
            description="品尝当地美食",
            price="¥150",
            duration="1小时",
            icon="🍽️"
        ))
        
        if day < len(simple_plan.hotels):
            items.append(ItineraryItem(
                time="20:00",
                type="hotel",
                title=simple_plan.hotels[min(day, len(simple_plan.hotels)-1)],
                description="入住酒店休息",
                price="¥800",
                duration="过夜",
                icon="🏨"
            ))
        
        itinerary.append(DayItinerary(
            day=day + 1,
            date=date_str,
            title=f"第{day+1}天 - {summary[:20]}",
            summary=f"{len(items)}个安排",
            items=items
        ))
    
    return FrontendTravelPlan(
        config=config,
        route_points=route_points,
        cards=cards,
        itinerary=itinerary
    )