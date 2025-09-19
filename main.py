#!/usr/bin/env python3
"""
自驾游规划Multi-Agent系统 - 基于AgentScope官方最佳实践
专注于自驾旅行的路线规划、景点推荐和实用建议
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
    """主函数 - 自驾游规划Multi-Agent系统"""

    print("🚗 启动自驾游规划Multi-Agent系统...")
    print("📚 专注于自驾旅行的专业规划服务")

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
        project="Self-Driving Travel Planner Multi-Agent",
        name="self_driving_planner",
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
    user = UserAgent("自驾游客")

    # 显示团队信息
    print("\n🤖 自驾游专家团队已就绪")
    print("👤 咨询专家：负责收集自驾游需求")
    print(list_agents(experts))
    print("\n👤 请在Studio中输入您的自驾游需求...")

    # 初始欢迎消息 - 专门针对自驾游
    welcome_msg = """您好！我是您的专业自驾游规划师。🚗

我专注于为您制定完美的自驾旅行方案，包括：
🛣️ 自驾路线规划与优化
🏞️ 沿途景点和停靠点推荐
⛽ 加油站、休息区、住宿安排
🅿️ 停车场信息和交通状况
💰 自驾游专属预算分析

在开始制定您的自驾游方案前，我需要了解您的具体需求：
- 出发地和目的地
- 自驾天数和行程节奏
- 车辆类型和驾驶经验
- 同行人数和预算水平
- 偏好的景点类型和特殊要求

请告诉我，您想开始规划自驾游了吗？"""

    msg = Msg(
        name="自驾游咨询专家",
        content=welcome_msg,
        role="assistant"
    )

    # 阶段1：咨询专家收集自驾游需求
    print("\n📋 阶段1：收集自驾游专属需求...")
    consultation_complete = False

    while not consultation_complete:
        try:
            # 获取用户输入
            msg = await user(msg)

            if msg.get_text_content().lower() in ['exit', 'quit', '退出', '结束']:
                print("👋 感谢使用，祝您自驾旅途愉快！")
                return

            print(f"🚗 用户回复: {msg.content}")

            # 咨询专家处理用户回复
            msg = await consultation_expert(msg)

            # 检查咨询是否完成（通过检查回复内容中的关键词）
            if "咨询完成" in msg.content or "制定专属旅行方案" in msg.content:
                consultation_complete = True
                print("✅ 自驾游需求收集完成，开始制定专属方案...")

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
                name="自驾游咨询专家",
                content="抱歉，刚才出现了一些问题。请重新告诉我您的自驾游需求。",
                role="assistant"
            )

    # 阶段2：需求广播和自驾游专家团队协作
    print("\n📢 阶段2：向自驾游专家团队广播完整需求...")

    try:
        # 使用MsgHub进行多Agent协作
        expert_list = list(experts.values())
        async with MsgHub(participants=expert_list + [coordinator]):

            # 1. 广播自驾游用户需求给所有专家
            requirements_broadcast = Msg(
                name="自驾游咨询专家",
                content=f"""🚗 **自驾游需求广播**

{user_requirements}

各位自驾游专家请注意：以上是收集的完整自驾游用户需求。
请各自根据自驾游的特殊要求和专业领域准备相应的建议和方案。

**自驾游特殊考虑因素：**
- 路况和驾驶安全
- 停车便利性
- 加油站分布
- 沿途休息点
- 车辆适应性
- 驾驶时间控制""",
                role="assistant"
            )

            print("📢 正在向所有自驾游专家广播用户需求...")

            # 向每个专家广播需求（让他们都接收到完整信息）
            broadcast_tasks = []
            for expert in expert_list:
                task = expert(requirements_broadcast)
                broadcast_tasks.append(task)

            # 等待所有专家确认接收到需求
            await asyncio.gather(*broadcast_tasks, return_exceptions=True)
            print("✅ 自驾游需求广播完成，所有专家已接收")

            # 2. 协调员分析和任务分配 - 专门针对自驾游
            analysis_prompt = f"""用户的完整自驾游需求如下：

{user_requirements}

请分析自驾游的关键信息（出发地、目的地、天数、车辆、预算、偏好等），然后明确分配任务给5位自驾游专家。

**自驾游专项分析要点：**
- 路线的驾驶难度和安全性
- 沿途景点的停车便利性
- 加油站和服务区分布
- 住宿的停车条件
- 自驾成本分析（油费、过路费、停车费）

为每位专家制定具体的自驾游工作重点和输出要求。"""

            print("🧠 协调员开始分析自驾游需求和任务分配...")
            analysis = await coordinator(
                Msg(
                    name="system",
                    content=analysis_prompt,
                    role="system"
                )
            )

            # 3. 自驾游专家并行工作
            print("🔄 自驾游专家团队开始并行工作...")
            expert_tasks = []
            for expert in expert_list:
                expert_prompt = f"""基于广播的完整自驾游用户需求，请根据你的专业领域提供建议：

{user_requirements}

**你的自驾游专业职责：**
- 如果你是景点研究专家：推荐适合自驾的景点，重点关注停车便利性、路况可达性
- 如果你是路线优化专家：设计最优自驾路线，考虑路况、驾驶时间、休息点分布
- 如果你是当地专家：提供自驾友好的美食和体验，关注停车方便的餐厅和景点
- 如果你是住宿专家：推荐有停车场的住宿，考虑车辆安全和便利性
- 如果你是预算分析专家：制定自驾游费用分析（油费、过路费、停车费、住宿餐饮）

**自驾游专项要求：**
1. 优先考虑驾驶安全和路况条件
2. 重点关注停车便利性和费用
3. 合理安排驾驶时间，避免疲劳驾驶
4. 考虑车辆类型的适应性
5. 提供沿途加油站和休息区信息
6. 给出明确的自驾游专业建议"""

                # 创建任务但不等待
                task = expert(Msg(
                    name="自驾游协调员",
                    content=expert_prompt,
                    role="assistant"
                ))
                expert_tasks.append(task)

            # 等待所有专家完成（即使有错误也继续）
            expert_results = await asyncio.gather(*expert_tasks, return_exceptions=True)

            # 4. 协调员整合自驾游方案
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

            integration_prompt = f"""请基于5位自驾游专家的建议，生成完整的自驾游方案。

自驾游用户需求：
{user_requirements}

专家建议：
{expert_advice}

请整合成一份结构化的自驾游规划，包括：

**🚗 自驾游专属方案结构：**
1. **路线规划**
   - 详细自驾路线（包含具体路段）
   - 驾驶时间和距离
   - 路况分析和注意事项

2. **景点安排**
   - 沿途景点推荐
   - 停车场信息和费用
   - 最佳游览时间安排

3. **住宿安排**
   - 有停车场的酒店推荐
   - 停车安全性评估
   - 位置便利性分析

4. **实用信息**
   - 加油站分布图
   - 服务区和休息点
   - 当地交通规则提醒

5. **费用预算**
   - 油费估算
   - 过路费明细
   - 停车费预算
   - 住宿餐饮费用

6. **安全贴士**
   - 驾驶安全提醒
   - 紧急联系方式
   - 车辆检查清单

确保方案：
- 完全针对自驾游的特殊需求
- 路线安全可行，适合自驾
- 时间安排合理，避免疲劳驾驶
- 信息准确实用，具有可操作性"""

            final_plan = await coordinator(
                Msg(
                    name="system",
                    content=integration_prompt,
                    role="system"
                )
            )

        # 返回给用户
        msg = final_plan
        print(f"\n🎯 自驾游方案已生成")

        # 继续对话循环，允许用户提问或修改
        while True:
            try:
                msg = await user(msg)

                if msg.get_text_content().lower() in ['exit', 'quit', '退出', '结束']:
                    print("👋 感谢使用，祝您自驾旅途愉快！")
                    break

                print(f"\n🚗 用户补充需求: {msg.content}")

                # 协调员处理后续自驾游问题
                followup_prompt = f"""用户对自驾游方案有补充需求：{msg.content}

请根据用户的问题，提供相应的自驾游解答或方案调整。
重点关注自驾游的特殊需求：路线优化、停车便利、驾驶安全等。
如果需要，可以重新询问专家团队。"""

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
                    name="自驾游规划师",
                    content="抱歉，刚才出现了一些问题。请重新告诉我您的自驾游需求。",
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