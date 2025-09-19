#!/usr/bin/env python3
"""
Agent工厂模块 - 根据配置创建不同数量和类型的Agent
支持基础版、标准版、完整版三种模式
"""

from typing import Dict, List
from agentscope.agent import ReActAgent
from agentscope.model import OpenAIChatModel, AnthropicChatModel
from agentscope.memory import InMemoryMemory

# 使用本地的 Formatter
from formatter import KimiMultiAgentFormatter, SafeAnthropicChatFormatter

from config import Settings
from tools_expert import create_expert_toolkits


def get_formatter(settings: Settings):
    """根据模型类型返回合适的 formatter"""
    if settings.model_type == "claude":
        # 使用安全的 AnthropicChatFormatter，能处理 content 为 None 的情况
        return SafeAnthropicChatFormatter()
    else:
        # 使用本地的 KimiMultiAgentFormatter
        return KimiMultiAgentFormatter()


def create_model(settings: Settings):
    """创建统一的模型实例，支持 Claude 和 OpenAI 格式"""
    
    if settings.model_type == "claude":
        # 使用 AgentScope 原生的 AnthropicChatModel
        return AnthropicChatModel(
            model_name=settings.claude_model,
            api_key=settings.anthropic_api_key,
            # Claude 模型的额外配置
            max_tokens=40960,
            stream=settings.stream_output,  # 可配置的流式输出
            # 支持自定义 base_url（用于代理或自定义端点）
            client_args={
                "base_url": settings.anthropic_base_url
            }
        )
    else:
        # 原有的 OpenAI 格式 API（Moonshot 等）
        return OpenAIChatModel(
            model_name="kimi-k2-turbo-preview",
            api_key=settings.api_key,
            stream=settings.stream_output,  # 可配置的流式输出
            client_args={"base_url": settings.base_url}
        )


def create_coordinator(settings: Settings, toolkit=None) -> ReActAgent:
    """
    创建协调Agent（所有模式通用）
    
    Args:
        settings: 配置
        toolkit: 可选的工具集（如 Tavily MCP）
    """
    return ReActAgent(
        name="旅行规划师",
        model=create_model(settings),
        formatter=get_formatter(settings),
        memory=InMemoryMemory(),  # 显式设置 memory
        toolkit=toolkit,  # 协调员使用工具集进行搜索
        sys_prompt="""你是主协调规划师，负责为用户提供基于真实数据的旅行规划服务。

工作流程：
1. 理解用户的旅行需求（目的地、时间、预算、偏好）
2. 【重要】使用 tavily_search 工具搜索相关信息：
   - 搜索目的地的景点、门票价格、开放时间
   - 搜索当地的美食、住宿、交通信息
   - 搜索最新的旅游攻略和实用信息
3. 基于搜索到的真实信息，协调专家团队分析
4. 整合各方建议，生成完整的旅行方案

注意事项：
- 必须使用 tavily_search 工具获取真实信息
- 不要编造或猜测信息
- 所有建议都应基于搜索到的真实数据
        
请用中文与用户交流，提供准确、实用的旅行规划服务。"""
    )


def create_basic_experts(settings: Settings, expert_toolkits: Dict = None) -> Dict[str, ReActAgent]:
    """
    创建基础版专家Agent（3个）
    快速Demo和开发测试

    Args:
        settings: 配置
        expert_toolkits: 专家工具集字典
    """
    if expert_toolkits is None:
        expert_toolkits = {}

    model = create_model(settings)

    experts = {
        "search_expert": ReActAgent(
            name="搜索专家",
            model=model,
            formatter=get_formatter(settings),
            memory=InMemoryMemory(),
            toolkit=expert_toolkits.get("search_expert"),  # 使用分配的工具
            sys_prompt="""你是旅行搜索专家，负责：
            1. 搜索目的地的基本信息和特色
            2. 查找热门景点、文化活动、美食推荐
            3. 收集当地的实用信息（天气、交通、风俗）
            4. 提供景点的开放时间、门票价格等详细信息

            你拥有以下工具：
            - tavily_search: 网络搜索最新信息
            - 小红书搜索: 获取真实用户评价和攻略

            请优先使用工具获取真实、准确的信息，不要编造数据。"""
        ),

        "plan_expert": ReActAgent(
            name="规划专家",
            model=model,
            formatter=get_formatter(settings),
            memory=InMemoryMemory(),
            toolkit=expert_toolkits.get("plan_expert"),  # 使用分配的工具
            sys_prompt="""你是行程规划专家，负责：
            1. 根据景点位置优化游览路线
            2. 安排每日的行程时间表
            3. 计算路线的交通时间和方式
            4. 确保行程紧凑但不疲劳

            你拥有以下工具：
            - 高德地图API: 路线规划、距离计算、交通方式查询

            设计高效、合理的行程安排。"""
        ),

        "budget_expert": ReActAgent(
            name="预算专家",
            model=model,
            formatter=get_formatter(settings),
            memory=InMemoryMemory(),
            toolkit=expert_toolkits.get("budget_expert"),  # 使用分配的工具
            sys_prompt="""你是预算分析专家，负责：
            1. 计算旅行的总体预算（含住宿、交通、餐饮、门票）
            2. 根据不同预算级别提供方案
            3. 推荐性价比高的选择
            4. 提供省钱技巧和优惠信息

            你拥有以下工具：
            - tavily_search: 搜索最新价格和优惠信息

            提供详细的费用明细。"""
        )
    }

    return experts


def create_standard_experts(settings: Settings, expert_toolkits: Dict = None) -> Dict[str, ReActAgent]:
    """
    创建标准版专家Agent（4个）
    适合常规使用场景

    Args:
        settings: 配置
        expert_toolkits: 专家工具集字典
    """
    if expert_toolkits is None:
        expert_toolkits = {}

    model = create_model(settings)

    experts = {
        "poi_expert": ReActAgent(
            name="POI专家",
            model=model,
            formatter=get_formatter(settings),
            memory=InMemoryMemory(),
            toolkit=expert_toolkits.get("poi_expert"),  # 使用分配的工具
            sys_prompt="""你是景点研究专家，专注于：
            1. 深入研究目的地的必游景点
            2. 根据用户兴趣推荐合适的景点
            3. 提供景点的历史背景和文化价值
            4. 建议最佳游览时间和拍照地点

            你拥有以下工具：
            - tavily_search: 搜索景点详细信息
            - 小红书搜索: 获取真实游客体验和攻略

            提供专业的景点推荐。"""
        ),

        "route_expert": ReActAgent(
            name="路线专家",
            model=model,
            formatter=get_formatter(settings),
            memory=InMemoryMemory(),
            toolkit=expert_toolkits.get("route_expert"),  # 使用分配的工具
            sys_prompt="""你是路线优化专家，专注于：
            1. 设计最优的景点游览顺序
            2. 选择合适的交通方式
            3. 计算准确的路程时间
            4. 避免路线重复和时间浪费

            你拥有以下工具：
            - 高德地图API: 路线规划、距离计算、实时交通

            优化行程路线。"""
        ),

        "local_expert": ReActAgent(
            name="当地专家",
            model=model,
            formatter=get_formatter(settings),
            memory=InMemoryMemory(),
            toolkit=expert_toolkits.get("local_expert"),  # 使用分配的工具
            sys_prompt="""你是当地文化专家，专注于：
            1. 介绍当地的文化特色和风俗习惯
            2. 推荐地道的美食和餐厅
            3. 提供当地人的生活体验建议
            4. 分享避坑指南和注意事项

            你拥有以下工具：
            - 小红书搜索: 获取当地真实体验分享
            - 天气服务: 查询当地天气和气候

            提供深度的当地文化体验建议。"""
        ),

        "budget_expert": ReActAgent(
            name="预算专家",
            model=model,
            formatter=get_formatter(settings),
            memory=InMemoryMemory(),
            toolkit=expert_toolkits.get("budget_expert"),  # 使用分配的工具
            sys_prompt="""你是预算管理专家，专注于：
            1. 制定详细的预算分配方案
            2. 分析各项费用的合理性
            3. 提供不同预算级别的选择
            4. 推荐优惠和省钱策略

            你拥有以下工具：
            - tavily_search: 搜索最新价格和优惠信息

            提供精准的费用分析。"""
        )
    }

    return experts


def create_full_experts(settings: Settings, expert_toolkits: Dict = None) -> Dict[str, ReActAgent]:
    """
    创建完整版专家Agent（5-6个）
    适合高端定制需求

    Args:
        settings: 配置
        expert_toolkits: 专家工具集字典
    """
    if expert_toolkits is None:
        expert_toolkits = {}

    # 先获取标准版的4个专家
    experts = create_standard_experts(settings, expert_toolkits)

    model = create_model(settings)

    # 添加额外的专家
    experts["hotel_expert"] = ReActAgent(
        name="住宿专家",
        model=model,
        formatter=get_formatter(settings),
        memory=InMemoryMemory(),
        toolkit=expert_toolkits.get("hotel_expert"),  # 使用分配的工具
        sys_prompt="""你是住宿推荐专家，专注于：
        1. 根据预算和需求推荐合适的酒店
        2. 分析酒店的位置、设施和服务
        3. 提供民宿、青旅等多样化选择
        4. 建议最佳的预订时机和渠道

        你拥有以下工具：
        - tavily_search: 搜索酒店信息和价格
        - 小红书搜索: 获取住宿真实评价

        提供专业的住宿建议。"""
    )

    # 可选：添加美食专家
    if settings.debug:  # 在调试模式下添加第6个专家
        experts["food_expert"] = ReActAgent(
            name="美食专家",
            model=model,
            formatter=get_formatter(settings),
            memory=InMemoryMemory(),
            toolkit=expert_toolkits.get("food_expert"),  # 使用分配的工具
            sys_prompt="""你是美食推荐专家，专注于：
            1. 推荐当地特色美食和餐厅
            2. 根据口味偏好定制美食路线
            3. 提供米其林餐厅和街头小吃
            4. 建议用餐时间和预订方式

            你拥有以下工具：
            - 小红书搜索: 获取美食体验和评价
            - tavily_search: 搜索餐厅信息和菜单

            提供全方位的美食体验建议。"""
        )

    return experts


async def create_expert_agents(settings: Settings, toolkit=None) -> Dict[str, ReActAgent]:
    """
    根据配置创建相应的专家Agent组（集成工具分配）

    Args:
        settings: 应用配置
        toolkit: 协调员使用的工具集（保持向后兼容）

    Returns:
        Dict[str, ReActAgent]: 专家Agent字典
    """
    mode = settings.agent_mode.lower()

    # 创建专家工具集
    print(f"🔧 正在为 {mode} 模式分配专家工具...")
    expert_toolkits = await create_expert_toolkits(mode)

    if mode == "basic":
        print("📋 使用基础版配置：3个专家Agent")
        return create_basic_experts(settings, expert_toolkits)
    elif mode == "standard":
        print("📋 使用标准版配置：4个专家Agent")
        return create_standard_experts(settings, expert_toolkits)
    elif mode == "full":
        print("📋 使用完整版配置：5-6个专家Agent")
        return create_full_experts(settings, expert_toolkits)
    else:
        print(f"⚠️ 未知的agent_mode: {mode}，使用基础版")
        return create_basic_experts(settings, expert_toolkits)


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