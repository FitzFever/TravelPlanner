#!/usr/bin/env python3
"""
Agent工厂模块 - 根据配置创建不同数量和类型的Agent
支持基础版、标准版、完整版三种模式
"""

from typing import Dict, List

import json
from agentscope.agent import ReActAgent
from agentscope.model import OpenAIChatModel, AnthropicChatModel
from agentscope.memory import InMemoryMemory
from agentscope.tool import Toolkit
from agentscope.message import Msg
import asyncio

# 使用本地的 Formatter
from formatter import KimiMultiAgentFormatter

from config import Settings
from tools_expert import create_expert_toolkits
from tools_storage import save_travel_plan, load_travel_plan, list_travel_plans, save_structured_travel_plan, request_structured_output


class TravelReActAgent(ReActAgent):
    """
    自定义的旅行规划ReActAgent，支持流式输出到WebSocket
    """

    def __init__(self, *args, websocket_callback=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.websocket_callback = websocket_callback
        self.agent_name = kwargs.get('name', 'Agent')

    def set_websocket_callback(self, callback):
        """设置WebSocket回调函数"""
        self.websocket_callback = callback

    async def print(self, msg: Msg, last: bool = True):
        """重写print方法，捕获Agent的输出并发送到WebSocket"""
        # 调用原始的print方法
        await super().print(msg, last)

        #如果有WebSocket回调，发送消息
        if self.websocket_callback:
            # 转换为json
            message = msg.to_dict()
            # 使用asyncio创建任务来发送WebSocket消息
            try:
                loop = asyncio.get_event_loop()
                loop.create_task(self.websocket_callback(self.agent_name, message))
            except RuntimeError:
                # 如果没有运行的事件循环，暂时忽略
                pass


def get_formatter(settings: Settings):
    """根据模型类型返回合适的 formatter"""
    if settings.model_type == "claude":
        # 使用修复的 SafeAnthropicChatFormatter，解决空内容问题
        from formatter.safe_anthropic_formatter import SafeAnthropicChatFormatter
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


def create_coordinator(settings: Settings, toolkit=None) -> TravelReActAgent:
    """
    创建协调Agent（所有模式通用）
    
    Args:
        settings: 配置
        toolkit: 可选的工具集（如 Tavily MCP）
    """
    # 创建或扩展工具集，添加存储工具
    if toolkit is None:
        toolkit = Toolkit()
    
    # 注册简化的路书存储工具
    toolkit.register_tool_function(save_travel_plan)
    toolkit.register_tool_function(save_structured_travel_plan)
    toolkit.register_tool_function(load_travel_plan)
    toolkit.register_tool_function(list_travel_plans)
    toolkit.register_tool_function(request_structured_output)

    return TravelReActAgent(
        name="旅行规划师",
        model=create_model(settings),
        formatter=get_formatter(settings),
        memory=InMemoryMemory(),  # 显式设置 memory
        toolkit=toolkit,  # 协调员使用工具集进行搜索和存储
        sys_prompt="""你是主协调规划师，负责为用户提供基于真实数据的旅行规划服务。

工作流程：
1. 理解用户的旅行需求（目的地、时间、预算、偏好）
2. 【重要】使用 tavily_search 工具搜索相关信息：
   - 搜索目的地的景点、门票价格、开放时间
   - 搜索当地的美食、住宿、交通信息
   - 搜索最新的旅游攻略和实用信息
3. 基于搜索到的真实信息，协调专家团队分析
4. 整合各方建议，生成完整的旅行方案
5. 【重要】路书生成后自动保存，或根据用户要求保存

可用的存储工具：
- save_travel_plan: 保存文本格式路书
- save_structured_travel_plan: 保存结构化数据（推荐，直接传入模型生成的结构化数据）
- request_structured_output: 请求用户提供结构化格式的旅行方案
- load_travel_plan: 加载保存的路书
- list_travel_plans: 查看所有路书

路书保存规则：
- 【推荐】生成完整方案后，优先使用 save_structured_travel_plan 保存结构化数据
- 传统文本格式需要时，使用 save_travel_plan 保存
- 用户要求"保存"、"存储"路书时，询问用户偏好或直接使用结构化保存
- 用户询问"历史记录"、"之前的计划"时，使用 list_travel_plans
- 用户要求"加载"特定路书时，使用 load_travel_plan

结构化输出要求：
- 【最佳实践】直接生成结构化数据，调用 save_structured_travel_plan
- 如需要用户确认，可先用 request_structured_output 引导用户
- 结构化数据格式包括：destination, days, travel_type, budget_level, attractions, hotels, daily_summary
- 避免复杂的文本解析，让模型直接提供清晰的数据结构

文件管理特性：
- 系统自动生成便于检索的文件名：目的地+天数+预算+时间戳
- 支持同一目的地的多版本保存，用户可以比较不同方案
- list_travel_plans 按目的地分组显示，便于管理和查找

注意事项：
- 必须使用 tavily_search 工具获取真实信息
- 不要编造或猜测信息
- 所有建议都应基于搜索到的真实数据
- 生成完整方案后要主动保存路书
        
请用中文与用户交流，提供准确、实用的旅行规划服务。"""
    )


def create_basic_experts(settings: Settings, expert_toolkits: Dict = None) -> Dict[str, TravelReActAgent]:
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
        "search_expert": TravelReActAgent(
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

        "plan_expert": TravelReActAgent(
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

        "budget_expert": TravelReActAgent(
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


def create_standard_experts(settings: Settings, expert_toolkits: Dict = None) -> Dict[str, TravelReActAgent]:
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
        "poi_expert": TravelReActAgent(
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

        "route_expert": TravelReActAgent(
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

        "local_expert": TravelReActAgent(
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

        "budget_expert": TravelReActAgent(
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


def create_full_experts(settings: Settings, expert_toolkits: Dict = None) -> Dict[str, TravelReActAgent]:
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
    experts["hotel_expert"] = TravelReActAgent(
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
        experts["food_expert"] = TravelReActAgent(
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


def create_consultation_expert(settings: Settings) -> TravelReActAgent:
    """
    创建咨询专家Agent - 负责系统性收集用户旅行需求

    Args:
        settings: 应用配置

    Returns:
        TravelReActAgent: 咨询专家Agent
    """
    return TravelReActAgent(
        name="咨询专家",
        model=create_model(settings),
        formatter=get_formatter(settings),
        memory=InMemoryMemory(),
        toolkit=None,  # 咨询专家不需要外部工具，专注于对话
        sys_prompt="""你是专业的旅行咨询专家，负责系统性收集用户的完整旅行需求。

**核心职责：**
你必须按顺序收集以下6项必要信息：
1. 🎯 **目的地** - 用户想去的城市或地区
2. 📅 **旅行天数** - 计划旅行多少天
3. 👥 **出行人数** - 几个人一起旅行
4. 💰 **预算级别** - 经济型 或 舒适型
5. ⏰ **旅行节奏** - 休闲型 或 紧凑型
6. 📝 **其他要求** - 特殊偏好、忌讳、活动类型等

**工作流程：**
1. 友好地欢迎用户，简要介绍自己的作用
2. 逐项询问上述6项信息，确保每项都得到明确回答
3. 如果用户一次性提供了多项信息，要确认遗漏的部分
4. 收集完毕后，整理并确认所有信息的准确性
5. 只有在用户确认信息无误后，才表示咨询完成

**沟通风格：**
- 使用友好、专业的语调
- 一次只询问一个问题，避免用户感到压力
- 对用户的回答给予积极反馈
- 如果信息不够明确，要礼貌地要求澄清
- 使用中文进行交流

**重要原则：**
- 绝不跳过任何一项必要信息
- 不要开始旅行规划，那是其他专家的工作
- 专注于信息收集和确认
- 保持耐心和专业态度

**完成标准：**
只有当6项信息全部收集完整且用户确认无误时，才能结束咨询。
最后要明确告知用户："咨询完成，现在将为您制定专属旅行方案。"""
    )


async def create_expert_agents(settings: Settings, toolkit=None) -> Dict[str, TravelReActAgent]:
    """
    创建标准的5个专家Agent（基于文档定义）

    Args:
        settings: 应用配置
        toolkit: 协调员使用的工具集（保持向后兼容）

    Returns:
        Dict[str, TravelReActAgent]: 专家Agent字典
    """
    print("🔧 正在为专家分配工具...")
    expert_toolkits = await create_expert_toolkits()

    print("📋 创建标准专家团队：5个专家Agent")

    model = create_model(settings)
    formatter = get_formatter(settings)

    experts = {
        "poi_expert": TravelReActAgent(
            name="景点研究专家",
            model=model,
            formatter=formatter,
            memory=InMemoryMemory(),
            toolkit=expert_toolkits.get("poi_expert"),
            sys_prompt="""你是景点研究专家，专注于：

**核心职责：**
1. 景点信息收集和分析
2. 用户评价分析
3. 热门程度评估
4. 季节性因素分析

**你拥有的工具：**
- tavily_search: 搜索景点详细信息、开放时间、门票价格
- 小红书搜索: 获取真实游客体验、评价和攻略

**工作流程：**
1. 使用tavily_search获取景点的基本信息、官方数据
2. 使用小红书搜索查看真实用户评价和体验分享
3. 分析景点的热门程度和最佳游览时间
4. 综合评估景点的价值和推荐度

**输出要求：**
- 提供详细的景点介绍和亮点
- 分析用户评价的真实性和代表性
- 给出明确的推荐指数和理由
- 注明最佳游览时间和注意事项"""
        ),

        "route_expert": TravelReActAgent(
            name="路线优化专家",
            model=model,
            formatter=formatter,
            memory=InMemoryMemory(),
            toolkit=expert_toolkits.get("route_expert"),
            sys_prompt="""你是路线优化专家，专注于：

**核心职责：**
1. 地理位置聚类分析
2. 最优路径规划算法
3. 时间安排优化
4. 交通连接分析

**你拥有的工具：**
- 高德地图API: 路线规划、距离计算、实时交通、交通方式查询

**工作流程：**
1. 使用高德地图API获取景点间的距离和交通时间
2. 分析不同交通方式的优劣（步行、公交、地铁、打车）
3. 考虑交通高峰期和景点开放时间
4. 设计最优的游览顺序和路线

**输出要求：**
- 提供详细的路线规划图
- 标注每段路程的时间和交通方式
- 考虑实际交通状况和等待时间
- 提供备选路线方案"""
        ),

        "local_expert": TravelReActAgent(
            name="当地专家",
            model=model,
            formatter=formatter,
            memory=InMemoryMemory(),
            toolkit=expert_toolkits.get("local_expert"),
            sys_prompt="""你是当地专家，专注于：

**核心职责：**
1. 当地文化和习俗介绍
2. 当地特色推荐（游玩/美食）
3. 隐藏景点推荐（进阶玩法）
4. 实用信息提供

**你拥有的工具：**
- 天气服务: 查询当地天气、气候特点、季节特色
- 小红书搜索: 获取当地人和深度游客的真实体验分享

**工作流程：**
1. 使用天气服务了解当地气候特点和季节性活动
2. 使用小红书搜索本地人推荐的小众景点和美食
3. 分析当地的文化特色和风俗习惯
4. 挖掘深度游玩体验和隐藏宝藏

**输出要求：**
- 介绍当地的文化背景和特色
- 推荐地道的美食和餐厅
- 分享本地人才知道的小众景点
- 提供实用的生活贴士和注意事项"""
        ),

        "hotel_expert": TravelReActAgent(
            name="住宿专家",
            model=model,
            formatter=formatter,
            memory=InMemoryMemory(),
            toolkit=expert_toolkits.get("hotel_expert"),
            sys_prompt="""你是住宿专家，专注于：

**核心职责：**
1. 酒店/民宿推荐
2. 价格对比分析
3. 位置便利性评估
4. 设施和服务分析

**你拥有的工具：**
- tavily_search: 搜索酒店信息、价格比较、预订攻略
- 小红书搜索: 获取住宿真实评价和入住体验

**工作流程：**
1. 使用tavily_search查找酒店基本信息、价格和预订渠道
2. 使用小红书搜索查看真实入住体验和评价
3. 分析住宿位置与景点、交通的便利性
4. 评估性价比和服务质量

**输出要求：**
- 推荐不同价位的住宿选择
- 分析位置优势和交通便利性
- 对比设施、服务和性价比
- 提供预订建议和注意事项"""
        ),

        "budget_expert": TravelReActAgent(
            name="预算分析专家",
            model=model,
            formatter=formatter,
            memory=InMemoryMemory(),
            toolkit=expert_toolkits.get("budget_expert"),
            sys_prompt="""你是预算分析专家，专注于：

**核心职责：**
1. 详细预算表制作
2. 成本分析报告
3. 省钱建议提供
4. 不同预算档次方案设计

**你拥有的工具：**
- tavily_search: 搜索最新价格信息、优惠活动、省钱攻略

**工作流程：**
1. 使用tavily_search获取各项费用的最新价格信息
2. 分析不同季节和时期的价格差异
3. 研究各种优惠政策和省钱技巧
4. 制定不同预算级别的完整方案

**输出要求：**
- 制作详细的预算分解表
- 提供经济型、舒适型、豪华型三种方案
- 分享实用的省钱技巧和优惠信息
- 标注费用的合理区间和注意事项"""
        )
    }

    return experts


def list_agents(experts: Dict[str, TravelReActAgent]) -> str:
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