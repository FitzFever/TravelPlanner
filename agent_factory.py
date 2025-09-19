#!/usr/bin/env python3
"""
Agent工厂模块 - 根据配置创建不同数量和类型的Agent
支持基础版、标准版、完整版三种模式
"""

from typing import Dict, List
from agentscope.agent import ReActAgent
from agentscope.model import OpenAIChatModel

# 使用本地的 KimiMultiAgentFormatter
from formatter import KimiMultiAgentFormatter

from config import Settings
from tools import create_travel_toolkit, create_minimal_toolkit


def create_model(settings: Settings):
    """创建统一的模型实例"""
    return OpenAIChatModel(
        model_name="kimi-k2-turbo-preview",
        api_key=settings.api_key,
        client_args={"base_url": settings.base_url}
    )


def create_coordinator(settings: Settings) -> ReActAgent:
    """
    创建协调Agent（所有模式通用）
    """
    return ReActAgent(
        name="旅行规划师",
        model=create_model(settings),
        formatter=KimiMultiAgentFormatter(),
        sys_prompt="""你是主协调规划师，负责：
        1. 理解用户的旅行需求（目的地、时间、预算、偏好）
        2. 协调专家团队的工作，分配任务
        3. 整合各专家的建议，生成完整的旅行方案
        4. 确保方案满足用户的需求和预期
        5. 与用户友好交流，提供专业建议
        
        请用中文与用户交流，提供详细、实用、个性化的旅行规划服务。"""
    )


def create_basic_experts(settings: Settings) -> Dict[str, ReActAgent]:
    """
    创建基础版专家Agent（3个）
    快速Demo和开发测试
    """
    model = create_model(settings)
    
    experts = {
        "search_expert": ReActAgent(
            name="搜索专家",
            model=model,
            formatter=KimiMultiAgentFormatter(),
            toolkit=create_travel_toolkit(),  # 每个Agent独立的toolkit
            sys_prompt="""你是旅行搜索专家，负责：
            1. 搜索目的地的基本信息和特色
            2. 查找热门景点、文化活动、美食推荐
            3. 收集当地的实用信息（天气、交通、风俗）
            4. 提供景点的开放时间、门票价格等详细信息
            
            使用工具搜索信息，提供准确、实用的搜索结果。"""
        ),
        
        "plan_expert": ReActAgent(
            name="规划专家",
            model=model,
            formatter=KimiMultiAgentFormatter(),
            toolkit=create_travel_toolkit(),  # 每个Agent独立的toolkit
            sys_prompt="""你是行程规划专家，负责：
            1. 根据景点位置优化游览路线
            2. 安排每日的行程时间表
            3. 计算路线的交通时间和方式
            4. 确保行程紧凑但不疲劳
            
            使用路线计算工具，设计高效、合理的行程安排。"""
        ),
        
        "budget_expert": ReActAgent(
            name="预算专家",
            model=model,
            formatter=KimiMultiAgentFormatter(),
            toolkit=create_travel_toolkit(),  # 每个Agent独立的toolkit
            sys_prompt="""你是预算分析专家，负责：
            1. 计算旅行的总体预算（含住宿、交通、餐饮、门票）
            2. 根据不同预算级别提供方案
            3. 推荐性价比高的选择
            4. 提供省钱技巧和优惠信息
            
            使用预算估算工具，提供详细的费用明细。"""
        )
    }
    
    return experts


def create_standard_experts(settings: Settings) -> Dict[str, ReActAgent]:
    """
    创建标准版专家Agent（4个）
    适合常规使用场景
    """
    model = create_model(settings)
    
    experts = {
        "poi_expert": ReActAgent(
            name="POI专家",
            model=model,
            formatter=KimiMultiAgentFormatter(),
            toolkit=create_travel_toolkit(),  # 每个Agent独立的toolkit
            sys_prompt="""你是景点研究专家，专注于：
            1. 深入研究目的地的必游景点
            2. 根据用户兴趣推荐合适的景点
            3. 提供景点的历史背景和文化价值
            4. 建议最佳游览时间和拍照地点
            
            使用搜索工具获取景点信息，提供专业的景点推荐。"""
        ),
        
        "route_expert": ReActAgent(
            name="路线专家",
            model=model,
            formatter=KimiMultiAgentFormatter(),
            toolkit=create_travel_toolkit(),  # 每个Agent独立的toolkit
            sys_prompt="""你是路线优化专家，专注于：
            1. 设计最优的景点游览顺序
            2. 选择合适的交通方式
            3. 计算准确的路程时间
            4. 避免路线重复和时间浪费
            
            使用路线计算工具，优化行程路线。"""
        ),
        
        "local_expert": ReActAgent(
            name="当地专家",
            model=model,
            formatter=KimiMultiAgentFormatter(),
            toolkit=create_travel_toolkit(),  # 每个Agent独立的toolkit
            sys_prompt="""你是当地文化专家，专注于：
            1. 介绍当地的文化特色和风俗习惯
            2. 推荐地道的美食和餐厅
            3. 提供当地人的生活体验建议
            4. 分享避坑指南和注意事项
            
            提供深度的当地文化体验建议。"""
        ),
        
        "budget_expert": ReActAgent(
            name="预算专家",
            model=model,
            formatter=KimiMultiAgentFormatter(),
            toolkit=create_travel_toolkit(),  # 每个Agent独立的toolkit
            sys_prompt="""你是预算管理专家，专注于：
            1. 制定详细的预算分配方案
            2. 分析各项费用的合理性
            3. 提供不同预算级别的选择
            4. 推荐优惠和省钱策略
            
            使用预算工具，提供精准的费用分析。"""
        )
    }
    
    return experts


def create_full_experts(settings: Settings) -> Dict[str, ReActAgent]:
    """
    创建完整版专家Agent（5-6个）
    适合高端定制需求
    """
    # 先获取标准版的4个专家
    experts = create_standard_experts(settings)
    
    model = create_model(settings)
    
    # 添加额外的专家
    experts["hotel_expert"] = ReActAgent(
        name="住宿专家",
        model=model,
        formatter=KimiMultiAgentFormatter(),
        toolkit=create_travel_toolkit(),  # 每个Agent独立的toolkit
        sys_prompt="""你是住宿推荐专家，专注于：
        1. 根据预算和需求推荐合适的酒店
        2. 分析酒店的位置、设施和服务
        3. 提供民宿、青旅等多样化选择
        4. 建议最佳的预订时机和渠道
        
        使用酒店搜索工具，提供专业的住宿建议。"""
    )
    
    # 可选：添加美食专家
    if settings.debug:  # 在调试模式下添加第6个专家
        experts["food_expert"] = ReActAgent(
            name="美食专家",
            model=model,
            formatter=KimiMultiAgentFormatter(),
            sys_prompt="""你是美食推荐专家，专注于：
            1. 推荐当地特色美食和餐厅
            2. 根据口味偏好定制美食路线
            3. 提供米其林餐厅和街头小吃
            4. 建议用餐时间和预订方式
            
            提供全方位的美食体验建议。"""
        )
    
    return experts


def create_expert_agents(settings: Settings) -> Dict[str, ReActAgent]:
    """
    根据配置创建相应的专家Agent组
    
    Args:
        settings: 应用配置
        
    Returns:
        Dict[str, ReActAgent]: 专家Agent字典
    """
    mode = settings.agent_mode.lower()
    
    if mode == "basic":
        print("📋 使用基础版配置：3个专家Agent")
        return create_basic_experts(settings)
    elif mode == "standard":
        print("📋 使用标准版配置：4个专家Agent")
        return create_standard_experts(settings)
    elif mode == "full":
        print("📋 使用完整版配置：5-6个专家Agent")
        return create_full_experts(settings)
    else:
        print(f"⚠️ 未知的agent_mode: {mode}，使用基础版")
        return create_basic_experts(settings)


def list_agents(experts: Dict[str, ReActAgent]) -> str:
    """
    列出当前激活的Agent
    
    Args:
        experts: 专家Agent字典
        
    Returns:
        str: Agent列表描述
    """
    agent_list = ["协调Agent：旅行规划师"]
    agent_list.extend([f"专家Agent：{agent.name}" for agent in experts.values()])
    
    return "当前团队成员：\n" + "\n".join(f"  - {item}" for item in agent_list)


if __name__ == "__main__":
    # 测试Agent创建
    from config import get_settings
    
    settings = get_settings()
    
    # 测试不同模式
    for mode in ["basic", "standard", "full"]:
        settings.agent_mode = mode
        print(f"\n测试 {mode} 模式：")
        experts = create_expert_agents(settings)
        print(f"创建了 {len(experts)} 个专家Agent")
        print("专家列表：", list(experts.keys()))