#!/usr/bin/env python3
"""
测试工具调用功能
验证Agent能正确使用工具获取信息
"""

import asyncio

# 从已安装的 agentscope 包导入
from agentscope.agent import ReActAgent
from agentscope.message import Msg
from config import get_settings
from agent_factory import create_model
from tools import create_travel_toolkit


async def test_tool_usage():
    """测试单个Agent的工具调用"""
    
    print("🧪 开始测试工具调用功能...")
    
    # 获取设置
    settings = get_settings()
    
    # 创建工具集
    toolkit = create_travel_toolkit()
    print(f"✅ 创建工具集，包含 {len(toolkit.tools)} 个工具")
    
    # 创建测试Agent
    test_agent = ReActAgent(
        name="测试专家",
        model=create_model(settings),
        toolkit=toolkit,
        sys_prompt="""你是一个旅行规划测试专家。
        请使用提供的工具来完成任务，并详细说明使用了哪些工具。
        用中文回复。"""
    )
    
    print("\n📋 测试场景1：搜索城市信息")
    msg = Msg(
        "user",
        "请搜索上海的基本信息",
        "user"
    )
    response = await test_agent(msg)
    print(f"Agent回复：{response.content[:200]}...")
    
    print("\n📋 测试场景2：搜索景点")
    msg = Msg(
        "user",
        "请搜索上海的文化类景点",
        "user"
    )
    response = await test_agent(msg)
    print(f"Agent回复：{response.content[:200]}...")
    
    print("\n📋 测试场景3：计算路线")
    msg = Msg(
        "user",
        "请计算从外滩到豫园再到田子坊的路线",
        "user"
    )
    response = await test_agent(msg)
    print(f"Agent回复：{response.content[:200]}...")
    
    print("\n📋 测试场景4：估算预算")
    msg = Msg(
        "user",
        "请估算上海3天2人舒适型旅行的预算",
        "user"
    )
    response = await test_agent(msg)
    print(f"Agent回复：{response.content[:200]}...")
    
    print("\n✅ 工具调用测试完成！")


async def test_multi_agent_with_tools():
    """测试多个Agent协作使用工具"""
    
    print("\n🧪 测试Multi-Agent工具协作...")
    
    settings = get_settings()
    toolkit = create_travel_toolkit()
    
    # 创建两个专家Agent
    search_expert = ReActAgent(
        name="搜索专家",
        model=create_model(settings),
        toolkit=toolkit,
        sys_prompt="你是搜索专家，负责搜索景点和城市信息。使用工具获取准确信息。"
    )
    
    budget_expert = ReActAgent(
        name="预算专家",
        model=create_model(settings),
        toolkit=toolkit,
        sys_prompt="你是预算专家，负责计算旅行费用。使用工具进行预算估算。"
    )
    
    # 测试协作
    print("\n🔄 专家协作测试")
    
    # 搜索专家工作
    search_msg = Msg("user", "搜索北京的历史景点", "user")
    search_result = await search_expert(search_msg)
    print(f"搜索专家: {search_result.content[:150]}...")
    
    # 预算专家基于搜索结果工作
    budget_msg = Msg(
        "search_expert",
        f"基于这些景点：{search_result.content[:100]}，请估算北京3天的预算",
        "assistant"
    )
    budget_result = await budget_expert(budget_msg)
    print(f"预算专家: {budget_result.content[:150]}...")
    
    print("\n✅ Multi-Agent工具协作测试完成！")


if __name__ == "__main__":
    print("=" * 50)
    print("旅行规划系统 - 工具调用测试")
    print("=" * 50)
    
    # 运行测试
    asyncio.run(test_tool_usage())
    asyncio.run(test_multi_agent_with_tools())
    
    print("\n🎉 所有测试完成！")