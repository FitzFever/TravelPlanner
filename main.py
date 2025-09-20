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
        name="咨询专家",
        content=welcome_msg,
        role="assistant"
    )

    # 消息驱动的自驾游规划流程
    print("\n🔄 启动基于消息驱动的自驾游专家协作...")
    
    # 先收集用户需求
    user_requirements = None
    
    while not user_requirements:
        try:
            # 获取用户输入
            msg = await user(msg)

            if msg.get_text_content().lower() in ['exit', 'quit', '退出', '结束']:
                print("👋 感谢使用，祝您自驾旅途愉快！")
                return

            print(f"🚗 用户输入: {msg.content}")

            # 咨询专家处理用户回复
            msg = await consultation_expert(msg)

            # 检查咨询是否完成
            if "咨询完成" in msg.content or "制定专属旅行方案" in msg.content:
                user_requirements = msg.content
                print("✅ 需求收集完成，开始专家团队协作...")

        except KeyboardInterrupt:
            print("\n👋 程序已退出")
            return
        except Exception as e:
            print(f"❌ 需求收集错误: {e}")
            msg = Msg(
                name="咨询专家",
                content="抱歉，请重新告诉我您的自驾游需求。",
                role="assistant"
            )

    # 基于预设信息广播矩阵的专家协作
    print("\n🎯 按照预设广播矩阵进行专家协作...")

    try:
        # 使用MsgHub进行结构化的专家协作
        expert_list = list(experts.values())
        async with MsgHub(participants=expert_list + [coordinator]) as hub:

            # 创建用户需求的初始消息
            initial_msg = Msg(
                name="用户",
                content=f"""🚗 **自驾游规划需求**

{user_requirements}

**自驾游特殊要求：**
- 路况和驾驶安全
- 停车便利性和费用
- 加油站、休息区分布
- 驾驶时间合理控制
- 车辆适应性考虑""",
                role="user"
            )

            print("📢 开始结构化专家协作流程...")
            
            # 消息收集字典
            expert_messages = {}
            
            # 第1步：当地专家首先提供基础信息（广播矩阵：当地专家 → POI专家、路线专家）
            print("🌍 当地专家提供基础信息...")
            local_expert = experts.get('local_expert')
            if local_expert:
                try:
                    local_msg = await local_expert(initial_msg)
                    expert_messages['local_expert'] = local_msg
                    print("✅ 当地专家信息准备完成")
                except Exception as e:
                    print(f"⚠️ 当地专家处理错误: {e}")
                    expert_messages['local_expert'] = Msg(
                        name="当地专家", 
                        content="当地信息收集遇到问题，将使用基本信息继续", 
                        role="assistant"
                    )
            
            # 第2步：POI专家基于当地信息进行景点研究
            print("🏞️ POI专家进行景点研究...")
            poi_expert = experts.get('poi_expert')
            if poi_expert:
                try:
                    poi_input = Msg(
                        name="system",
                        content=f"""基于用户需求和当地专家信息进行景点研究：

用户需求：{user_requirements}

当地专家信息：{expert_messages.get('local_expert', Msg(name='default', content='无', role='assistant')).content}

请提供符合自驾游特点的景点推荐，包括：
- 景点位置坐标
- 游览时长
- 停车便利性
- 门票费用

输出格式（用于后续专家）：
- selected_pois: [(name, lat, lng, duration_hours, parking_info)]
- total_ticket_cost: 总门票费用""",
                        role="system"
                    )
                    poi_msg = await poi_expert(poi_input)
                    expert_messages['poi_expert'] = poi_msg
                    print("✅ POI专家研究完成")
                except Exception as e:
                    print(f"⚠️ POI专家处理错误: {e}")
                    expert_messages['poi_expert'] = Msg(
                        name="POI专家", 
                        content="景点研究遇到问题，将使用默认推荐", 
                        role="assistant"
                    )

            # 第3步：路线专家基于POI信息进行路线规划（广播矩阵：POI专家 → 路线专家）
            print("🛣️ 路线专家进行路线规划...")
            route_expert = experts.get('route_expert')
            if route_expert:
                try:
                    route_input = Msg(
                        name="poi_expert",
                        content=f"""基于POI专家提供的景点信息进行路线规划：

用户需求：{user_requirements}

POI专家信息：{expert_messages.get('poi_expert', Msg(name='default', content='无', role='assistant')).content}

当地专家交通信息：{expert_messages.get('local_expert', Msg(name='default', content='无', role='assistant')).content}

请规划最优自驾路线，包括：
- 每日行程安排
- 驾驶时间和距离
- 路况分析
- 休息点安排

输出格式（用于后续专家）：
- daily_endpoints: [(day, final_location, area)]
- transport_cost: 交通费用估算
- total_distance: 总里程数""",
                        role="assistant"
                    )
                    route_msg = await route_expert(route_input)
                    expert_messages['route_expert'] = route_msg
                    print("✅ 路线专家规划完成")
                except Exception as e:
                    print(f"⚠️ 路线专家处理错误: {e}")
                    expert_messages['route_expert'] = Msg(
                        name="路线专家", 
                        content="路线规划遇到问题，将使用基本路线", 
                        role="assistant"
                    )
            
            # 第4步：住宿专家基于路线信息推荐住宿（广播矩阵：路线专家 → 住宿专家）
            print("🏨 住宿专家推荐住宿...")
            hotel_expert = experts.get('hotel_expert')
            if hotel_expert:
                try:
                    hotel_input = Msg(
                        name="route_expert",
                        content=f"""基于路线专家的终点位置推荐住宿：

用户需求：{user_requirements}

路线专家信息：{expert_messages.get('route_expert', Msg(name='default', content='无', role='assistant')).content}

请推荐符合自驾游特点的住宿，重点考虑：
- 停车场配备
- 位置便利性
- 价格合理性
- 车辆安全保障

输出格式（用于后续专家）：
- accommodation_cost: 住宿总费用
- parking_info: 停车信息""",
                        role="assistant"
                    )
                    hotel_msg = await hotel_expert(hotel_input)
                    expert_messages['hotel_expert'] = hotel_msg
                    print("✅ 住宿专家推荐完成")
                except Exception as e:
                    print(f"⚠️ 住宿专家处理错误: {e}")
                    expert_messages['hotel_expert'] = Msg(
                        name="住宿专家", 
                        content="住宿推荐遇到问题，将使用默认选择", 
                        role="assistant"
                    )

            # 第5步：预算专家汇总所有费用（广播矩阵：所有专家 → 预算专家）
            print("💰 预算专家进行费用分析...")
            budget_expert = experts.get('budget_expert')
            if budget_expert:
                try:
                    # 汇总所有专家的费用信息
                    all_expert_info = "\n\n".join([
                        f"{expert_name}信息：{msg.content}" 
                        for expert_name, msg in expert_messages.items()
                    ])
                    
                    budget_input = Msg(
                        name="system",
                        content=f"""基于所有专家信息进行自驾游预算分析：

用户需求：{user_requirements}

{all_expert_info}

请分析自驾游总体费用，包括：
- 油费和过路费
- 停车费用
- 门票费用
- 住宿费用
- 餐饮预算
- 应急备用金

如果超出用户预算，请提供削减建议：
- 给路线专家的建议（减少景点、选择经济路线）
- 给住宿专家的建议（降级住宿选择）

输出格式：
- total_cost: 总费用
- budget_status: "within" 或 "over"
- suggestions: 具体建议""",
                        role="system"
                    )
                    budget_msg = await budget_expert(budget_input)
                    expert_messages['budget_expert'] = budget_msg
                    print("✅ 预算专家分析完成")
                except Exception as e:
                    print(f"⚠️ 预算专家处理错误: {e}")
                    expert_messages['budget_expert'] = Msg(
                        name="预算专家", 
                        content="预算分析遇到问题，将使用基本估算", 
                        role="assistant"
                    )
                
                # 如果超预算，通知相关专家调整（广播矩阵：预算专家 → 路线、住宿专家）
                if "over" in budget_msg.content.lower():
                    print("⚠️ 预算超支，通知专家调整方案...")
                    
                    # 通知路线专家调整
                    if route_expert:
                        adjust_msg = Msg(
                            name="budget_expert",
                            content=f"预算超支，需要调整：\n{budget_msg.content}",
                            role="assistant"
                        )
                        route_adjust = await route_expert(adjust_msg)
                        expert_messages['route_expert_adjusted'] = route_adjust
                    
                    # 通知住宿专家调整
                    if hotel_expert:
                        adjust_msg = Msg(
                            name="budget_expert",
                            content=f"预算超支，需要调整：\n{budget_msg.content}",
                            role="assistant"
                        )
                        hotel_adjust = await hotel_expert(adjust_msg)
                        expert_messages['hotel_expert_adjusted'] = hotel_adjust

            # 第6步：协调员整合所有专家信息生成最终方案
            print("🎯 协调员整合专家信息生成最终方案...")
            
            # 汇总所有专家的建议
            expert_advice_parts = []
            for expert_name, msg in expert_messages.items():
                content = msg.content if hasattr(msg, 'content') else str(msg)
                expert_advice_parts.append(f"**{expert_name}建议：**\n{content}")
            
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

            try:
                final_plan = await coordinator(
                    Msg(
                        name="system",
                        content=integration_prompt,
                        role="system"
                    )
                )
            except Exception as e:
                print(f"⚠️ 协调员处理时出错: {e}")
                # 创建一个简化的最终方案
                final_plan = Msg(
                    name="协调员",
                    content=f"""🚗 **自驾游规划方案**

基于专家团队的建议，为您整理的自驾游方案：

{expert_advice}

**注意事项：**
- 请根据实际路况调整行程
- 注意驾驶安全，合理安排休息
- 提前预订住宿和查看停车条件""",
                    role="assistant"
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
                    name="旅行规划师",
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
        # 清理 MCP 连接，使用防御性错误处理
        try:
            asyncio.run(cleanup_mcp())
        except Exception as e:
            print(f"⚠️ MCP 清理警告: {e}")
        
        try:
            asyncio.run(cleanup_expert_mcp())
        except Exception as e:
            print(f"⚠️ 专家 MCP 清理警告: {e}")