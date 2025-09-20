#!/usr/bin/env python3
"""
路书存储工具 - KISS 原则 + 模型驱动版本
让AI模型直接提供结构化数据，而不是复杂的文本解析
"""

import json
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List
from agentscope.tool import ToolResponse

# 导入数据模型
try:
    from models.travel_data import SimpleTravelPlan, FrontendTravelPlan, transform_simple_to_frontend
except ImportError:
    from pydantic import BaseModel, Field
    
    class SimpleTravelPlan(BaseModel):
        destination: str = Field(description="目的地")
        days: int = Field(description="旅行天数") 
        travel_type: str = Field(description="旅行类型")
        budget_level: str = Field(description="预算级别")
        attractions: List[str] = Field(description="主要景点", max_items=5)
        hotels: List[str] = Field(description="推荐酒店", max_items=3)
        daily_summary: List[str] = Field(description="每日概要", max_items=15)
    
    # 如果无法导入，提供基本的空实现
    FrontendTravelPlan = SimpleTravelPlan
    def transform_simple_to_frontend(plan, start_date=None):
        return plan


def extract_destination_simple(content: str) -> str:
    """极简目的地提取 - 只要5行代码"""
    # 1. 优先标准格式
    match = re.search(r'目的地[:：]\s*([一-龥]{2,8})', content[:200])
    if match:
        return match.group(1)
    
    # 2. 备用方案
    match = re.search(r'([一-龥]{2,6})(?:\d+天|旅游|自驾)', content[:100])
    return match.group(1) if match else "未知"


def generate_simple_filename(destination: str) -> str:
    """极简文件名 - 目的地_时间戳"""
    timestamp = datetime.now().strftime("%m%d_%H%M")
    return f"{destination}_{timestamp}.json"


def save_travel_plan(content: str, title: str = "") -> ToolResponse:
    """保存路书 - 传统文本版本"""
    try:
        base_dir = Path("travel_plans")
        base_dir.mkdir(exist_ok=True)
        
        destination = extract_destination_simple(content)
        filename = generate_simple_filename(destination)
        
        data = {
            "title": title or f"{destination}旅行方案",
            "content": content,
            "created_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "destination": destination
        }
        
        # 保存文件
        file_path = base_dir / filename
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        return ToolResponse(content=[{
            "type": "text",
            "text": f"✅ 路书已保存: {filename}\n📍 目的地: {destination}"
        }])
        
    except Exception as e:
        return ToolResponse(content=[{
            "type": "text",
            "text": f"❌ 保存失败: {e}"
        }])


def save_structured_travel_plan(structured_data: Dict[str, Any], title: str = "") -> ToolResponse:
    """保存结构化路书 - 模型驱动版本
    
    Args:
        structured_data: 模型直接输出的结构化数据
        title: 可选标题
    """
    try:
        base_dir = Path("travel_plans")
        base_dir.mkdir(exist_ok=True)
        
        # 直接使用模型提供的数据，无需复杂解析
        destination = structured_data.get("destination", "未知")
        days = structured_data.get("days", 0)
        travel_type = structured_data.get("travel_type", "")
        budget_level = structured_data.get("budget_level", "")
        
        # 生成有意义的文件名
        filename = f"{destination}{days}天_{budget_level}_{datetime.now().strftime('%m%d_%H%M')}.json"
        
        # 完整数据结构
        full_data = {
            "title": title or f"{destination}{days}天{travel_type}",
            "created_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "structured_data": structured_data,  # 模型原始数据
            "metadata": {
                "destination": destination,
                "days": days,
                "travel_type": travel_type, 
                "budget_level": budget_level
            }
        }
        
        # 保存
        file_path = base_dir / filename
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(full_data, f, ensure_ascii=False, indent=2)
        
        return ToolResponse(content=[{
            "type": "text",
            "text": f"""✅ 结构化路书已保存！

📁 文件: {filename}
📍 目的地: {destination}
📅 天数: {days}天
🎯 类型: {travel_type}
💰 预算: {budget_level}

🎉 数据已完全结构化，便于前端使用！"""
        }])
        
    except Exception as e:
        return ToolResponse(content=[{
            "type": "text",
            "text": f"❌ 保存结构化数据失败: {e}"
        }])


def save_frontend_travel_plan(structured_data: Dict[str, Any], start_date: str = "", title: str = "") -> ToolResponse:
    """保存前端兼容的完整旅行方案
    
    Args:
        structured_data: SimpleTravelPlan格式的结构化数据
        start_date: 旅行开始日期 YYYY-MM-DD
        title: 可选标题
    """
    try:
        # 将SimpleTravelPlan转换为FrontendTravelPlan
        simple_plan = SimpleTravelPlan(**structured_data)
        
        # 使用当前日期作为默认开始日期
        if not start_date:
            start_date = datetime.now().strftime("%Y-%m-%d")
        
        # 转换为前端格式
        frontend_plan = transform_simple_to_frontend(simple_plan, start_date)
        
        # 保存文件
        base_dir = Path("travel_plans")
        base_dir.mkdir(exist_ok=True)
        
        destination = simple_plan.destination
        days = simple_plan.days
        budget_level = simple_plan.budget_level
        
        filename = f"{destination}{days}天_前端版_{budget_level}_{datetime.now().strftime('%m%d_%H%M')}.json"
        
        # 完整数据结构（前端兼容格式）
        full_data = {
            "title": title or f"{destination}{days}天{simple_plan.travel_type}",
            "created_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "frontend_data": frontend_plan.dict(),  # 前端完整格式
            "simple_data": structured_data,  # 简化格式备份
            "metadata": {
                "destination": destination,
                "days": days,
                "travel_type": simple_plan.travel_type,
                "budget_level": budget_level,
                "start_date": start_date,
                "format_version": "frontend_v1"
            }
        }
        
        # 保存
        file_path = base_dir / filename
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(full_data, f, ensure_ascii=False, indent=2)
        
        return ToolResponse(content=[{
            "type": "text",
            "text": f"""✅ 前端兼容路书已保存！

📁 文件: {filename}
📍 目的地: {destination}
📅 天数: {days}天 (开始日期: {start_date})
🎯 类型: {simple_plan.travel_type}
💰 预算: {budget_level}

🎯 包含数据:
- 地图路线点: {len(frontend_plan.route_points)}个
- 信息卡片: {len(frontend_plan.cards)}个  
- 详细行程: {len(frontend_plan.itinerary)}天

🚀 此文件可直接被前端使用，包含完整的坐标、卡片和行程数据！"""
        }])
        
    except Exception as e:
        return ToolResponse(content=[{
            "type": "text",
            "text": f"❌ 保存前端兼容数据失败: {e}"
        }])


def request_structured_output() -> ToolResponse:
    """请求AI使用结构化输出的工具"""
    return ToolResponse(content=[{
        "type": "text", 
        "text": """🤖 **结构化输出请求**

请使用以下格式重新生成您的旅行方案：

**基础版本**: structured_model=SimpleTravelPlan
**前端完整版**: 使用 save_frontend_travel_plan 保存

**SimpleTravelPlan格式**:
```json
{
  "destination": "具体城市名",
  "days": 天数(数字),
  "travel_type": "自驾游/亲子游/深度游等",
  "budget_level": "经济型/舒适型/豪华型", 
  "attractions": ["景点1", "景点2", "景点3"],
  "hotels": ["酒店1", "酒店2"],
  "daily_summary": ["第1天概要", "第2天概要", ...]
}
```

💡 推荐使用 save_frontend_travel_plan，它会自动转换为前端所需的完整格式（包含坐标、卡片、详细行程）！"""
    }])


def list_travel_plans() -> ToolResponse:
    """列出路书 - 简化版"""
    try:
        base_dir = Path("travel_plans")
        json_files = sorted(base_dir.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True)
        
        if not json_files:
            return ToolResponse(content=[{
                "type": "text",
                "text": "📂 暂无保存的路书\n💡 生成路书后我会自动保存"
            }])
        
        # 按目的地分组 - 简化版
        groups = {}
        for file_path in json_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                destination = data.get("destination") or data.get("metadata", {}).get("destination", "未知")
                
                if destination not in groups:
                    groups[destination] = []
                
                # 简化的文件信息
                file_info = {
                    "filename": file_path.name,
                    "title": data.get("title", "无标题"),
                    "time": datetime.fromtimestamp(file_path.stat().st_mtime).strftime("%m/%d %H:%M")
                }
                
                # 如果有结构化数据，显示更多信息
                if "structured_data" in data:
                    sd = data["structured_data"]
                    file_info["extra"] = f"{sd.get('days', '?')}天·{sd.get('travel_type', '')}·{sd.get('budget_level', '')}"
                else:
                    file_info["extra"] = "文本版本"
                
                groups[destination].append(file_info)
                
            except:
                continue
        
        # 生成显示
        result = ["📂 您的路书库:\n"]
        
        for destination, files in groups.items():
            result.append(f"\n🌍 **{destination}** ({len(files)}个)")
            for i, info in enumerate(files, 1):
                result.append(f"  {i}. {info['extra']} 📅{info['time']}")
                result.append(f"     📁 {info['filename']}")
        
        total = sum(len(files) for files in groups.values())
        result.append(f"\n📊 总计: {len(groups)}个目的地, {total}个方案")
        
        return ToolResponse(content=[{
            "type": "text",
            "text": "\n".join(result)
        }])
        
    except Exception as e:
        return ToolResponse(content=[{
            "type": "text",
            "text": f"❌ 获取列表失败: {e}"
        }])


def load_travel_plan(filename: str) -> ToolResponse:
    """加载路书 - 简化版"""
    try:
        base_dir = Path("travel_plans")
        
        if not filename.endswith('.json'):
            filename = f"{filename}.json"
        
        file_path = base_dir / filename
        
        if not file_path.exists():
            # 简单的模糊匹配
            possible = list(base_dir.glob(f"*{filename.replace('.json', '')}*"))
            if possible:
                file_path = possible[0]
            else:
                return ToolResponse(content=[{
                    "type": "text",
                    "text": f"❌ 未找到文件: {filename}\n💡 使用 list_travel_plans 查看所有文件"
                }])
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 根据数据类型显示
        if "structured_data" in data:
            sd = data["structured_data"]
            content = f"""📖 **{data.get('title')}** (结构化版本)

📍 目的地: {sd.get('destination')}
📅 天数: {sd.get('days')}天  
🎯 类型: {sd.get('travel_type')}
💰 预算: {sd.get('budget_level')}

🏛️ 主要景点: {', '.join(sd.get('attractions', []))}
🏨 推荐酒店: {', '.join(sd.get('hotels', []))}

📋 每日概要:
{chr(10).join(f"  {i+1}. {summary}" for i, summary in enumerate(sd.get('daily_summary', [])))}"""
        else:
            content = f"""📖 **{data.get('title')}** (文本版本)

{data.get('content', '无内容')}"""
        
        return ToolResponse(content=[{
            "type": "text",
            "text": content
        }])
        
    except Exception as e:
        return ToolResponse(content=[{
            "type": "text",
            "text": f"❌ 加载失败: {e}"
        }])


# Agent调用的实际工具函数
def get_structured_travel_plan_from_agent(agent_result) -> Dict[str, Any]:
    """从Agent结果中提取结构化数据
    
    这是给Agent调用的辅助函数，用于处理structured_model的返回结果
    """
    if hasattr(agent_result, 'metadata') and agent_result.metadata:
        return agent_result.metadata
    else:
        # 如果没有结构化数据，返回空结构
        return {
            "destination": "未指定",
            "days": 0,
            "travel_type": "通用",
            "budget_level": "标准",
            "attractions": [],
            "hotels": [],
            "daily_summary": []
        }


if __name__ == "__main__":
    # 简单测试
    print("测试KISS版本存储工具...")
    
    # 测试结构化数据保存
    test_data = {
        "destination": "成都",
        "days": 3,
        "travel_type": "美食游",
        "budget_level": "舒适型",
        "attractions": ["宽窄巷子", "锦里", "大熊猫基地"],
        "hotels": ["茂业JW万豪酒店"],
        "daily_summary": ["第1天：抵达成都，游览宽窄巷子", "第2天：大熊猫基地，锦里古街", "第3天：返程"]
    }
    
    result = save_structured_travel_plan(test_data, "成都3天美食之旅")
    print(result.content[0]["text"])