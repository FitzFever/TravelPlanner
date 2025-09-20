#!/usr/bin/env python3
"""
专家级MCP工具分配系统 - 根据专家类型分配特定工具
"""

import os
import asyncio
from typing import Dict, Optional
from agentscope.tool import Toolkit
from agentscope.mcp import StdIOStatefulClient, HttpStatefulClient

# 全局 MCP 客户端存储
mcp_clients = {}


async def create_combined_toolkit(tool_types: list, name_suffix: str = "") -> Optional[Toolkit]:
    """
    创建组合工具集，支持多种工具类型

    Args:
        tool_types: 工具类型列表 ["tavily", "xhs", "amap", "weather"]
        name_suffix: 名称后缀，用于区分不同实例
    """
    toolkit = Toolkit()
    has_tools = False

    for tool_type in tool_types:
        try:
            if tool_type == "tavily":
                client = await _create_tavily_client(f"tavily_{name_suffix}")
                if client:
                    await toolkit.register_mcp_client(client)
                    mcp_clients[f"tavily_{name_suffix}"] = client
                    has_tools = True

            elif tool_type == "xhs":
                client = await _create_xhs_client(f"xhs_{name_suffix}")
                if client:
                    await toolkit.register_mcp_client(client)
                    mcp_clients[f"xhs_{name_suffix}"] = client
                    has_tools = True

            elif tool_type == "amap":
                client = await _create_amap_client(f"amap_{name_suffix}")
                if client:
                    await toolkit.register_mcp_client(client)
                    mcp_clients[f"amap_{name_suffix}"] = client
                    has_tools = True

            elif tool_type == "weather":
                client = await _create_weather_client(f"weather_{name_suffix}")
                if client:
                    await toolkit.register_mcp_client(client)
                    mcp_clients[f"weather_{name_suffix}"] = client
                    has_tools = True

        except Exception as e:
            print(f"❌ {tool_type} 工具连接失败 ({name_suffix}): {e}")

    return toolkit if has_tools else None


async def _create_tavily_client(name: str):
    """创建Tavily客户端"""
    tavily_key = os.getenv("TAVILY_API_KEY")
    if not tavily_key:
        try:
            from config import get_settings
            settings = get_settings()
            tavily_key = settings.tavily_api_key
            if tavily_key and tavily_key != "your-tavily-key-here":
                os.environ["TAVILY_API_KEY"] = tavily_key
        except:
            pass

    if not tavily_key or tavily_key == "your-tavily-key-here":
        return None

    client = StdIOStatefulClient(
        name=name,
        command="npx",
        args=["-y", "tavily-mcp@latest"],
        env={"TAVILY_API_KEY": tavily_key}
    )
    await client.connect()
    return client


async def _create_xhs_client(name: str):
    """创建小红书客户端"""
    # 从配置获取小红书MCP路径
    try:
        from config import get_settings
        settings = get_settings()
        xhs_directory = settings.xhs_mcp_directory
    except:
        # 回退到默认路径
        xhs_directory = "/Users/geng/py/xhs-mcp"

    client = StdIOStatefulClient(
        name=name,
        command="uv",
        args=["--directory", xhs_directory, "run", "main.py"],
        env={
            "XHS_COOKIE": "abRequestId=6e12629e-86a3-59d3-9177-a908d77fdf1a; xsecappid=xhs-pc-web; a1=19744a844a5r6ncvxrpc6bzhhpeuam8a6068zw4eo30000782193; webId=af7afdd61d64eb3bce723fee54929418; gid=yjW08iidfiKWyjW440Y448E402FKIShCFUSKKdlDuxxUdYq8706Y0u888WYJyjq8KjySj8W8; webBuild=4.81.0; web_session=04006979827162156355bc2ff83a4bac04becb; acw_tc=0a4ae10f17583562845381940ef2d1982f904b71c4581f8e0cbb76ad6d5ee4; websectiga=10f9a40ba454a07755a08f27ef8194c53637eba4551cf9751c009d9afb564467; sec_poison_id=0bdc24b7-8009-4626-b792-ebda2cdd6281; unread={%22ub%22:%2268cd005c0000000013004b35%22%2C%22ue%22:%2268bedc45000000001b033c8c%22%2C%22uc%22:26}; loadts=1758357627361"
        }
    )
    await client.connect()
    return client


async def _create_amap_client(name: str):
    """创建高德地图客户端"""
    client = HttpStatefulClient(
        name=name,
        transport="streamable_http",
        url="https://mcp.amap.com/mcp?key=9105a7f9617c226c0e5f49d059944354"
    )
    await client.connect()
    return client


async def _create_weather_client(name: str):
    """创建天气服务客户端"""
    client = HttpStatefulClient(
        name=name,
        transport="streamable_http",
        url="https://aigc-mcp-api-test.aijidou.com/mcp/weather/streamable",
        headers={"apikey": "690fd8653d0ee9c2f552459349e5faef"}
    )
    await client.connect()
    return client


async def create_expert_toolkits() -> Dict[str, Optional[Toolkit]]:
    """
    创建标准5个专家的工具集分配（基于文档定义）

    Returns:
        Dict[str, Optional[Toolkit]]: 专家名称到工具集的映射
    """
    print("🔧 正在为5个标准专家分配工具...")

    # 标准5个专家的工具分配（基于doc/agent/experts.md）
    allocation_strategy = {
        "poi_expert": ["tavily", "xhs"],        # 景点研究专家：搜索+社交
        "route_expert": ["amap"],               # 路线优化专家：地图
        "local_expert": ["weather", "xhs"],     # 当地专家：天气+社交
        "hotel_expert": ["tavily", "xhs"],      # 住宿专家：搜索+社交
        "budget_expert": ["tavily"]             # 预算分析专家：搜索
    }

    toolkits = {}

    # 并行创建所有工具集
    tasks = []
    expert_names = []

    for expert_name, tool_types in allocation_strategy.items():
        task = create_combined_toolkit(tool_types, expert_name)
        tasks.append(task)
        expert_names.append(expert_name)

    # 等待所有工具集创建完成
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # 分配结果
    for i, result in enumerate(results):
        expert_name = expert_names[i]
        if isinstance(result, Exception):
            print(f"❌ {expert_name} 工具集创建失败: {result}")
            toolkits[expert_name] = None
        else:
            toolkits[expert_name] = result

    # 显示分配结果
    print(f"🎯 工具分配完成:")
    for expert, toolkit in toolkits.items():
        if toolkit:
            print(f"   ✅ {expert}: 已分配工具")
        else:
            print(f"   ⚠️  {expert}: 无可用工具")

    return toolkits


async def cleanup_expert_mcp():
    """清理所有专家MCP连接"""
    print("🔄 正在清理MCP连接...")
    
    # 复制字典避免运行时修改
    clients_to_close = dict(mcp_clients)

    for name, client in clients_to_close.items():
        try:
            if client:
                await client.close()
                print(f"✅ {name} MCP 连接已关闭")
        except Exception as e:
            print(f"⚠️ 关闭 {name} MCP 连接时出错: {e}")

    mcp_clients.clear()
    print("🎯 所有MCP连接已清理")


# 便捷函数：获取单个工具集
async def get_search_toolkit() -> Optional[Toolkit]:
    """获取搜索工具集 (Tavily + 小红书)"""
    return await create_combined_toolkit(["tavily", "xhs"], "combined_search")


async def get_location_toolkit() -> Optional[Toolkit]:
    """获取位置工具集 (高德地图)"""
    return await create_combined_toolkit(["amap"], "location")


async def get_social_toolkit() -> Optional[Toolkit]:
    """获取社交媒体工具集 (小红书)"""
    return await create_combined_toolkit(["xhs"], "social")


async def get_weather_toolkit() -> Optional[Toolkit]:
    """获取天气工具集"""
    return await create_combined_toolkit(["weather"], "weather_only")


if __name__ == "__main__":
    # 测试工具分配
    async def test_toolkits():
        print("🧪 测试标准5专家工具分配系统...")

        toolkits = await create_expert_toolkits()

        print(f"   分配的专家数量: {len(toolkits)}")
        for expert, toolkit in toolkits.items():
            status = "✅ 有工具" if toolkit else "❌ 无工具"
            print(f"   {expert}: {status}")

        # 清理
        await cleanup_expert_mcp()

    asyncio.run(test_toolkits())