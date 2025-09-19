#!/usr/bin/env python3
"""
简单测试脚本 - 验证Agent和工具调用功能
"""

import asyncio

# 从已安装的 agentscope 包导入
import agentscope
from agentscope.message import Msg
from config import get_settings
from agent_factory import create_basic_experts


async def test_basic():
    """测试基础功能"""
    
    print("🧪 简单功能测试...")
    
    # 初始化
    settings = get_settings()
    agentscope.init(
        project="Test",
        name="test_run",
        logging_level="WARNING"
    )
    
    # 创建基础专家
    experts = create_basic_experts(settings)
    print(f"✅ 创建了 {len(experts)} 个专家Agent")
    
    # 测试搜索专家
    search_expert = experts["search_expert"]
    msg = Msg("user", "请搜索上海的基本信息和景点", "user")
    
    print("\n📍 测试搜索专家...")
    response = await search_expert(msg)
    print(f"回复预览: {response.content[:200]}...")
    
    print("\n✅ 测试完成！Agent和工具调用正常工作。")


if __name__ == "__main__":
    asyncio.run(test_basic())