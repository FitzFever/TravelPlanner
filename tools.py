#!/usr/bin/env python3
"""
旅行规划工具集 - 基于AgentScope标准工具定义
提供搜索、路线计算等基础功能，支持降级策略
"""

from typing import List, Dict, Any, Optional
from agentscope.tool import Toolkit, ToolResponse
import json
import random
from datetime import datetime, timedelta
import asyncio
import os

# 模拟数据 - 用于降级策略
MOCK_DATA = {
    "cities": {
        "上海": {
            "description": "中国最大的经济中心，融合东西方文化的国际大都市",
            "best_season": "春秋季（3-5月，9-11月）",
            "avg_budget": {"经济": 500, "舒适": 1000, "奢华": 2000}
        },
        "北京": {
            "description": "中国首都，拥有丰富的历史文化遗产",
            "best_season": "春秋季（4-5月，9-10月）",
            "avg_budget": {"经济": 600, "舒适": 1200, "奢华": 2500}
        },
        "东京": {
            "description": "日本首都，现代与传统完美融合的国际都市",
            "best_season": "春季樱花季（3-4月）和秋季红叶季（11月）",
            "avg_budget": {"经济": 800, "舒适": 1500, "奢华": 3000}
        },
        "巴黎": {
            "description": "浪漫之都，艺术、时尚和美食的天堂",
            "best_season": "春夏季（4-9月）",
            "avg_budget": {"经济": 1000, "舒适": 2000, "奢华": 4000}
        }
    },
    "pois": {
        "上海": [
            {"name": "外滩", "category": "景点", "duration": 2, "cost": 0, "rating": 4.8},
            {"name": "东方明珠", "category": "景点", "duration": 3, "cost": 220, "rating": 4.5},
            {"name": "豫园", "category": "文化", "duration": 3, "cost": 40, "rating": 4.6},
            {"name": "田子坊", "category": "购物", "duration": 2, "cost": 0, "rating": 4.4},
            {"name": "上海博物馆", "category": "文化", "duration": 3, "cost": 0, "rating": 4.7}
        ],
        "北京": [
            {"name": "故宫", "category": "历史", "duration": 5, "cost": 60, "rating": 4.9},
            {"name": "长城", "category": "历史", "duration": 6, "cost": 45, "rating": 4.8},
            {"name": "颐和园", "category": "文化", "duration": 4, "cost": 30, "rating": 4.7},
            {"name": "天坛", "category": "历史", "duration": 3, "cost": 35, "rating": 4.6},
            {"name": "798艺术区", "category": "艺术", "duration": 3, "cost": 0, "rating": 4.5}
        ],
        "东京": [
            {"name": "浅草寺", "category": "文化", "duration": 3, "cost": 0, "rating": 4.6},
            {"name": "东京塔", "category": "景点", "duration": 2, "cost": 1200, "rating": 4.5},
            {"name": "秋叶原", "category": "购物", "duration": 4, "cost": 0, "rating": 4.7},
            {"name": "新宿御苑", "category": "自然", "duration": 2, "cost": 500, "rating": 4.8},
            {"name": "涉谷", "category": "购物", "duration": 3, "cost": 0, "rating": 4.6}
        ]
    },
    "hotels": {
        "经济": ["青年旅社", "快捷酒店", "民宿"],
        "舒适": ["三星酒店", "精品酒店", "高级民宿"],
        "奢华": ["五星酒店", "度假村", "奢华精品酒店"]
    }
}


def search_destination(city: str) -> ToolResponse:
    """
    搜索城市基本信息
    
    Args:
        city: 目的地城市名称
        
    Returns:
        ToolResponse: 城市信息
    """
    try:
        # 尝试使用真实API（如果配置了）
        if os.getenv("TAVILY_API_KEY") and os.getenv("TAVILY_API_KEY") != "your-tavily-key-here":
            # 这里可以集成Tavily API
            pass
    except Exception as e:
        print(f"API调用失败，使用备用数据: {e}")
    
    # 使用模拟数据
    if city in MOCK_DATA["cities"]:
        city_info = MOCK_DATA["cities"][city]
        return ToolResponse(
            content=[{
                "type": "text",
                "text": f"城市：{city}\n"
                       f"简介：{city_info['description']}\n"
                       f"最佳季节：{city_info['best_season']}\n"
                       f"日均预算参考：\n"
                       f"  - 经济型：{city_info['avg_budget']['经济']}元\n"
                       f"  - 舒适型：{city_info['avg_budget']['舒适']}元\n"
                       f"  - 奢华型：{city_info['avg_budget']['奢华']}元"
            }]
        )
    
    return ToolResponse(
        content=[{
            "type": "text",
            "text": f"未找到城市 {city} 的详细信息，建议查询主要旅游城市"
        }]
    )


def search_poi(city: str, category: Optional[str] = None) -> ToolResponse:
    """
    搜索城市景点信息
    
    Args:
        city: 城市名称
        category: 景点类别（可选）：景点、文化、购物、美食、自然、历史、艺术
        
    Returns:
        ToolResponse: 景点列表信息
    """
    if city not in MOCK_DATA["pois"]:
        return ToolResponse(
            content=[{
                "type": "text",
                "text": f"暂无 {city} 的景点数据"
            }]
        )
    
    pois = MOCK_DATA["pois"][city]
    
    # 按类别筛选
    if category:
        pois = [p for p in pois if p["category"] == category]
    
    if not pois:
        return ToolResponse(
            content=[{
                "type": "text",
                "text": f"未找到 {city} 的{category if category else ''}景点"
            }]
        )
    
    # 格式化输出
    poi_list = []
    for poi in pois:
        poi_list.append(
            f"- {poi['name']} ({poi['category']})\n"
            f"  建议游览时长：{poi['duration']}小时\n"
            f"  门票：{poi['cost']}元\n"
            f"  评分：{poi['rating']}/5.0"
        )
    
    return ToolResponse(
        content=[{
            "type": "text",
            "text": f"{city}的{''+category if category else '热门'}景点：\n\n" + "\n\n".join(poi_list)
        }]
    )


def calculate_route(points: List[str], mode: str = "public") -> ToolResponse:
    """
    计算多个地点之间的最优路线
    
    Args:
        points: 地点列表
        mode: 交通方式（public/taxi/walk）
        
    Returns:
        ToolResponse: 路线规划结果
    """
    if len(points) < 2:
        return ToolResponse(
            content=[{
                "type": "text",
                "text": "至少需要2个地点才能计算路线"
            }]
        )
    
    # 模拟路线计算（实际可以调用地图API）
    routes = []
    total_time = 0
    total_cost = 0
    
    transport_info = {
        "public": {"speed": 30, "cost_per_km": 2},
        "taxi": {"speed": 40, "cost_per_km": 10},
        "walk": {"speed": 5, "cost_per_km": 0}
    }
    
    info = transport_info.get(mode, transport_info["public"])
    
    for i in range(len(points) - 1):
        # 模拟距离（随机3-15公里）
        distance = random.uniform(3, 15)
        time = distance / info["speed"] * 60  # 分钟
        cost = distance * info["cost_per_km"]
        
        routes.append({
            "from": points[i],
            "to": points[i + 1],
            "distance": f"{distance:.1f}公里",
            "time": f"{time:.0f}分钟",
            "cost": f"{cost:.0f}元",
            "mode": mode
        })
        
        total_time += time
        total_cost += cost
    
    # 格式化输出
    route_text = []
    for i, route in enumerate(routes, 1):
        route_text.append(
            f"{i}. {route['from']} → {route['to']}\n"
            f"   距离：{route['distance']}\n"
            f"   时间：{route['time']}\n"
            f"   费用：{route['cost']}（{route['mode']}）"
        )
    
    return ToolResponse(
        content=[{
            "type": "text",
            "text": f"路线规划结果：\n\n" + "\n\n".join(route_text) + 
                   f"\n\n总计：\n- 总时间：{total_time:.0f}分钟\n- 总费用：{total_cost:.0f}元"
        }]
    )


def get_weather(city: str, date: Optional[str] = None) -> ToolResponse:
    """
    获取天气信息
    
    Args:
        city: 城市名称
        date: 日期（可选，格式：YYYY-MM-DD）
        
    Returns:
        ToolResponse: 天气信息
    """
    # 模拟天气数据
    weather_patterns = [
        {"condition": "晴", "temp_high": 28, "temp_low": 20, "rain_prob": 10},
        {"condition": "多云", "temp_high": 25, "temp_low": 18, "rain_prob": 20},
        {"condition": "小雨", "temp_high": 22, "temp_low": 16, "rain_prob": 80},
        {"condition": "阴", "temp_high": 24, "temp_low": 17, "rain_prob": 30}
    ]
    
    weather = random.choice(weather_patterns)
    
    if not date:
        date = datetime.now().strftime("%Y-%m-%d")
    
    return ToolResponse(
        content=[{
            "type": "text",
            "text": f"{city} {date} 天气预报：\n"
                   f"天气：{weather['condition']}\n"
                   f"气温：{weather['temp_low']}℃ - {weather['temp_high']}℃\n"
                   f"降雨概率：{weather['rain_prob']}%\n"
                   f"建议：{'适合户外活动' if weather['rain_prob'] < 30 else '建议携带雨具'}"
        }]
    )


def search_hotels(city: str, budget: str = "舒适", checkin: Optional[str] = None) -> ToolResponse:
    """
    搜索酒店信息
    
    Args:
        city: 城市名称
        budget: 预算级别（经济/舒适/奢华）
        checkin: 入住日期（可选）
        
    Returns:
        ToolResponse: 酒店推荐列表
    """
    if budget not in ["经济", "舒适", "奢华"]:
        budget = "舒适"
    
    hotel_types = MOCK_DATA["hotels"][budget]
    
    # 生成模拟酒店数据
    hotels = []
    for i, hotel_type in enumerate(hotel_types, 1):
        price = {
            "经济": random.randint(150, 300),
            "舒适": random.randint(400, 800),
            "奢华": random.randint(1000, 3000)
        }[budget]
        
        hotels.append(
            f"{i}. {city}{hotel_type}示例{i}\n"
            f"   类型：{hotel_type}\n"
            f"   价格：{price}元/晚\n"
            f"   评分：{random.uniform(4.2, 4.9):.1f}/5.0\n"
            f"   位置：市中心{random.randint(1, 5)}公里"
        )
    
    return ToolResponse(
        content=[{
            "type": "text",
            "text": f"{city} {budget}型住宿推荐：\n\n" + "\n\n".join(hotels)
        }]
    )


def estimate_budget(
    city: str, 
    days: int, 
    people: int = 1, 
    budget_level: str = "舒适"
) -> ToolResponse:
    """
    估算旅行预算
    
    Args:
        city: 城市名称
        days: 天数
        people: 人数
        budget_level: 预算级别（经济/舒适/奢华）
        
    Returns:
        ToolResponse: 预算明细
    """
    if city not in MOCK_DATA["cities"]:
        city_budget = {"经济": 500, "舒适": 1000, "奢华": 2000}
    else:
        city_budget = MOCK_DATA["cities"][city]["avg_budget"]
    
    daily_budget = city_budget.get(budget_level, city_budget["舒适"])
    
    # 计算各项费用
    accommodation = daily_budget * 0.4 * days * people
    meals = daily_budget * 0.3 * days * people
    transportation = daily_budget * 0.15 * days * people
    attractions = daily_budget * 0.1 * days * people
    shopping = daily_budget * 0.05 * days * people
    
    total = accommodation + meals + transportation + attractions + shopping
    
    return ToolResponse(
        content=[{
            "type": "text",
            "text": f"{city} {days}天{people}人 {budget_level}型预算明细：\n\n"
                   f"住宿费用：{accommodation:.0f}元\n"
                   f"餐饮费用：{meals:.0f}元\n"
                   f"交通费用：{transportation:.0f}元\n"
                   f"景点门票：{attractions:.0f}元\n"
                   f"购物预算：{shopping:.0f}元\n"
                   f"─────────────\n"
                   f"总计：{total:.0f}元\n"
                   f"人均：{total/people:.0f}元"
        }]
    )


def create_travel_toolkit() -> Toolkit:
    """
    创建旅行规划工具集
    
    Returns:
        Toolkit: 包含所有旅行规划工具的工具集
    """
    toolkit = Toolkit()
    
    # 注册必要工具
    toolkit.register_tool_function(search_destination)
    toolkit.register_tool_function(search_poi)
    toolkit.register_tool_function(calculate_route)
    
    # 注册可选工具
    toolkit.register_tool_function(get_weather)
    toolkit.register_tool_function(search_hotels)
    toolkit.register_tool_function(estimate_budget)
    
    return toolkit


def create_minimal_toolkit() -> Toolkit:
    """
    创建最小工具集（仅包含必要工具）
    
    Returns:
        Toolkit: 最小工具集
    """
    toolkit = Toolkit()
    
    # 仅注册必要工具
    toolkit.register_tool_function(search_destination)
    toolkit.register_tool_function(search_poi)
    toolkit.register_tool_function(calculate_route)
    
    return toolkit


if __name__ == "__main__":
    # 测试工具函数
    print("测试工具函数...")
    
    # 测试城市搜索
    result = search_destination("上海")
    print(f"\n搜索上海：\n{result.content[0]['text']}")
    
    # 测试景点搜索
    result = search_poi("上海", "文化")
    print(f"\n上海文化景点：\n{result.content[0]['text']}")
    
    # 测试路线计算
    result = calculate_route(["外滩", "豫园", "田子坊"], "public")
    print(f"\n路线规划：\n{result.content[0]['text']}")
    
    # 测试预算估算
    result = estimate_budget("上海", 3, 2, "舒适")
    print(f"\n预算估算：\n{result.content[0]['text']}")