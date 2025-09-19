#!/usr/bin/env python3
"""
旅行规划Multi-Agent系统 - 基于AgentScope官方最佳实践
支持工具调用和灵活的Agent配置
"""
import asyncio

# 从已安装的 agentscope 包导入
import agentscope
from agentscope.agent import UserAgent
from agentscope.message import Msg
from agentscope.pipeline import MsgHub

from config import get_settings
from agent_factory import create_coordinator, create_expert_agents, create_consultation_expert, list_agents
from tools_simple import create_travel_toolkit, cleanup_mcp
from tools_expert import cleanup_expert_mcp

async def main():
    """主函数 - Multi-Agent旅行规划系统"""

    print("🎨 启动Multi-Agent旅行规划系统...")
    print("📚 基于AgentScope官方最佳实践设计")

    # 初始化 MCP 工具集（如果配置了 Tavily）
    toolkit = None
    try:
        toolkit = await create_travel_toolkit()
        if toolkit:
            print("✅ Tavily MCP 工具已加载")
    except Exception as e:
        print(f"⚠️ MCP 工具加载失败: {e}")

    # 初始化设置
    settings = get_settings()

    # 初始化AgentScope和Studio
    agentscope.init(
        project="Travel Planner Multi-Agent",
        name="travel_planner",
        logging_level="INFO",
        studio_url=settings.studio_url if settings.enable_studio else None
    )

    print("✅ AgentScope初始化完成")
    print(f"📊 Studio地址: {settings.studio_url}")

    # 创建Agent团队
    consultation_expert = create_consultation_expert(settings)
    coordinator = create_coordinator(settings, toolkit)
    experts = await create_expert_agents(settings, toolkit)

    # 创建用户代理
    user = UserAgent("旅行者")

    # 显示团队信息
    print("\n🤖 Multi-Agent团队已就绪")
    print("👤 咨询专家：负责收集用户需求")
    print(list_agents(experts))
    print("\n👤 请在Studio中输入您的旅行需求...")

    # 初始欢迎消息
    welcome_msg = """您好！我是您的AI旅行咨询专家。

在为您制定专属旅行方案之前，我需要了解您的具体需求。
我会逐步询问您的旅行偏好，包括目的地、时间、预算等信息。

请告诉我，您想开始规划旅行了吗？"""

    msg = Msg(
        name="咨询专家",
        content=welcome_msg,
        role="assistant"
    )

    # 阶段1：咨询专家收集需求
    print("\n📋 阶段1：咨询专家收集用户需求...")
    consultation_complete = False

    while not consultation_complete:
        try:
            # 获取用户输入
            msg = await user(msg)

            if msg.get_text_content().lower() in ['exit', 'quit', '退出', '结束']:
                print("👋 感谢使用，祝您旅途愉快！")
                return

            print(f"👤 用户回复: {msg.content}")

            # 咨询专家处理用户回复
            msg = await consultation_expert(msg)

            # 检查咨询是否完成（通过检查回复内容中的关键词）
            if "咨询完成" in msg.content or "制定专属旅行方案" in msg.content:
                consultation_complete = True
                print("✅ 需求收集完成，开始制定旅行方案...")

                # 提取用户的完整需求
                user_requirements = msg.content

        except KeyboardInterrupt:
            print("\n👋 程序已退出")
            return
        except Exception as e:
            print(f"❌ 咨询阶段错误: {e}")
            import traceback
            traceback.print_exc()
            # 继续咨询
            msg = Msg(
                name="咨询专家",
                content="抱歉，刚才出现了一些问题。请重新告诉我您的需求。",
                role="assistant"
            )

    # 阶段2：规划专家团队协作
    print("\n🔄 阶段2：专家团队开始协作...")

    try:
        # 使用MsgHub进行多Agent协作
        expert_list = list(experts.values())
        async with MsgHub(participants=expert_list + [coordinator]):
            # 1. 协调员分析用户需求
            analysis_prompt = f"""用户通过咨询专家收集的完整需求如下：

{user_requirements}

请分析需求的关键信息（目的地、天数、预算、偏好等），然后分配任务给5位专家。"""

            analysis = await coordinator(
                Msg(
                    name="system",
                    content=analysis_prompt,
                    role="system"
                )
            )

            # 2. 专家并行工作
            expert_tasks = []
            for expert in expert_list:
                expert_prompt = f"""基于用户的完整需求：

{user_requirements}

请根据你的专业领域提供建议：
- 如果你是景点研究专家：深入研究并推荐景点
- 如果你是路线优化专家：设计最优游览路线
- 如果你是当地专家：提供文化和美食建议
- 如果你是住宿专家：推荐合适的住宿选择
- 如果你是预算分析专家：制定详细的费用分析

请使用工具获取准确信息，给出专业建议。"""

                # 创建任务但不等待
                task = expert(Msg(
                    name="coordinator",
                    content=expert_prompt,
                    role="assistant"
                ))
                expert_tasks.append(task)

            # 等待所有专家完成（即使有错误也继续）
            expert_results = await asyncio.gather(*expert_tasks, return_exceptions=True)

            # 3. 协调员整合方案
            expert_advice_parts = []
            for i, result in enumerate(expert_results):
                if isinstance(result, Exception):
                    # 如果是异常，记录但继续
                    print(f"⚠️ 专家{i+1}（{expert_list[i].name}）出错: {str(result)[:100]}")
                    continue
                elif result is not None:
                    content = result.content if hasattr(result, 'content') else str(result)
                    expert_advice_parts.append(
                        f"专家{i+1}（{expert_list[i].name}）建议：\n{content}"
                    )

            expert_advice = "\n\n".join(expert_advice_parts) if expert_advice_parts else "专家暂无建议"

            integration_prompt = f"""请基于5位专家的建议，生成完整的旅行方案。

用户需求：
{user_requirements}

专家建议：
{expert_advice}

请整合成一份结构化的旅行规划，包括：
1. 行程安排（每日计划）
2. 景点推荐（含时间和门票）
3. 交通方案（路线和方式）
4. 预算明细（各项费用）
5. 实用贴士（注意事项）

确保方案：
- 符合用户的需求和预算
- 行程安排合理不赶时间
- 信息准确实用"""

            final_plan = await coordinator(
                Msg(
                    name="system",
                    content=integration_prompt,
                    role="system"
                )
            )

        # 返回给用户
        msg = final_plan
        print(f"\n🎯 旅行方案已生成")

        # 继续对话循环，允许用户提问或修改
        while True:
            try:
                msg = await user(msg)

                if msg.get_text_content().lower() in ['exit', 'quit', '退出', '结束']:
                    print("👋 感谢使用，祝您旅途愉快！")
                    break

                print(f"\n👤 用户补充需求: {msg.content}")

                # 协调员处理后续问题
                followup_prompt = f"""用户对旅行方案有补充需求：{msg.content}

请根据用户的问题，提供相应的解答或方案调整。如果需要，可以重新询问专家团队。"""

                msg = await coordinator(
                    Msg(
                        name="user",
                        content=followup_prompt,
                        role="user"
                    )
                )

            except KeyboardInterrupt:
                print("\n👋 程序已退出")
                break
            except Exception as e:
                print(f"❌ 后续对话错误: {e}")
                import traceback
                traceback.print_exc()
                msg = Msg(
                    name="旅行规划师",
                    content="抱歉，刚才出现了一些问题。请重新告诉我您的需求。",
                    role="assistant"
                )

    except Exception as e:
        print(f"❌ 规划阶段错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    finally:
        # 清理 MCP 连接
        asyncio.run(cleanup_mcp())
        asyncio.run(cleanup_expert_mcp())