#!/usr/bin/env python3
"""
简单的 MCP 工具集成 - 使用 Tavily 搜索真实数据
"""

import os
from agentscope.tool import Toolkit
from agentscope.mcp import StdIOStatefulClient

# 全局 MCP 客户端
tavily_client = None


async def create_travel_toolkit() -> Toolkit:
    """
    创建旅行工具集（使用 Tavily MCP）
    """
    global tavily_client
    toolkit = Toolkit()
    
    # 检查 API Key - 优先从环境变量，其次从配置
    tavily_key = os.getenv("TAVILY_API_KEY")
    if not tavily_key:
        # 尝试从配置获取
        try:
            from config import get_settings
            settings = get_settings()
            tavily_key = settings.tavily_api_key
            if tavily_key and tavily_key != "your-tavily-key-here":
                # 设置环境变量供 MCP 使用
                os.environ["TAVILY_API_KEY"] = tavily_key
        except:
            pass
    
    if not tavily_key or tavily_key == "your-tavily-key-here":
        print("⚠️ TAVILY_API_KEY 未设置，将无法使用搜索功能")
        print("   访问 https://tavily.com 获取免费 API Key")
        return toolkit
    
    # 创建并连接 Tavily MCP
    tavily_client = StdIOStatefulClient(
        name="tavily_mcp",
        command="npx",
        args=["-y", "tavily-mcp@latest"],
        env={"TAVILY_API_KEY": tavily_key}
    )
    
    try:
        await tavily_client.connect()
        await toolkit.register_mcp_client(tavily_client)
        print("✅ Tavily MCP 已连接")
    except Exception as e:
        print(f"❌ Tavily MCP 连接失败: {e}")
    
    return toolkit


async def cleanup_mcp():
    """清理 MCP 连接"""
    global tavily_client
    if tavily_client:
        await tavily_client.close()
        tavily_client = None