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
from agent_factory import create_coordinator, create_expert_agents, list_agents

async def main():
    """主函数 - Multi-Agent旅行规划系统"""
    
    print("🎨 启动Multi-Agent旅行规划系统...")
    print("📚 基于AgentScope官方最佳实践设计")
    
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
    print(f"🎯 Agent模式: {settings.agent_mode.upper()}")
    
    # 根据配置创建Agent团队
    coordinator = create_coordinator(settings)
    experts = create_expert_agents(settings)
    
    # 创建用户代理
    user = UserAgent("旅行者")
    
    # 显示团队信息
    print("\n🤖 Multi-Agent团队已就绪")
    print(list_agents(experts))
    print("\n👤 请在Studio中输入您的旅行需求...")
    
    # 初始欢迎消息
    welcome_msg = f"""您好！我是您的AI旅行规划师。

我的专业团队包括{len(experts)}位专家，可以为您提供：
- 🏛️ 景点推荐和深度介绍
- 🗺️ 路线优化和交通规划
- 💰 预算分析和省钱建议
{'- 🏨 住宿推荐' if len(experts) >= 5 else ''}
{'- 🍜 美食探索' if len(experts) >= 6 else ''}

请告诉我您的旅行需求，比如：
- 目的地（如：上海、北京、东京）
- 旅行天数（如：3天、一周）
- 预算级别（经济、舒适、奢华）
- 旅行风格（文化、美食、购物、自然）
- 出行人数

示例："我想去上海旅行3天，预算舒适型，喜欢文化和美食，2个人"
"""
    
    msg = Msg(
        name="旅行规划师",
        content=welcome_msg,
        role="assistant"
    )
    
    while True:
        try:
            # 获取用户输入
            msg = await user(msg)
            
            if msg.get_text_content().lower() in ['exit', 'quit', '退出', '结束']:
                print("👋 感谢使用，祝您旅途愉快！")
                break
            
            print(f"\n👤 用户需求: {msg.content}")
            print("🔄 专家团队开始协作...")
            
            # 使用MsgHub进行多Agent协作
            expert_list = list(experts.values())
            async with MsgHub(participants=expert_list + [coordinator]):
                # 1. 协调员分析用户需求
                analysis = await coordinator(
                    Msg(
                        "system",
                        f"用户的旅行需求是：{msg.content}\n"
                        f"请分析需求的关键信息（目的地、天数、预算、偏好等），"
                        f"然后分配任务给{len(experts)}位专家。",
                        "system"
                    )
                )
                
                # 2. 专家并行工作（根据配置的专家数量）
                expert_tasks = []
                for expert in expert_list:
                    expert_prompt = f"""基于用户需求：{msg.content}
                    
请根据你的专业领域提供建议：
- 如果你是搜索/POI专家：搜索并推荐景点
- 如果你是规划/路线专家：优化游览路线
- 如果你是预算专家：分析费用明细
- 如果你是当地专家：提供文化和美食建议
- 如果你是住宿专家：推荐合适的酒店

请使用工具获取准确信息，给出专业建议。"""
                    
                    # 创建任务但不等待
                    task = expert(Msg("coordinator", expert_prompt, "assistant"))
                    expert_tasks.append(task)
                
                # 等待所有专家完成
                expert_results = await asyncio.gather(*expert_tasks)
                
                # 3. 协调员整合方案
                integration_prompt = f"""请基于{len(experts)}位专家的建议，生成完整的旅行方案。

用户需求：{msg.content}

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
                    Msg("system", integration_prompt, "system")
                )
            
            # 返回给用户
            msg = final_plan
            print(f"\n🎯 旅行方案已生成")
            
        except KeyboardInterrupt:
            print("\n👋 程序已退出")
            break
        except Exception as e:
            print(f"❌ 错误: {e}")
            import traceback
            traceback.print_exc()
            # 继续对话
            msg = Msg(
                name="旅行规划师",
                content="抱歉，刚才出现了一些问题。请重新告诉我您的需求。",
                role="assistant"
            )

if __name__ == "__main__":
    asyncio.run(main())