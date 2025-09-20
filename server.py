#!/usr/bin/env python3
"""
自驾游规划WebSocket服务器 - 基于AgentScope的对话问答服务
专注于自驾旅行的实时交互规划服务
"""
import asyncio
import json
import logging
import websockets
from typing import Dict, Set, Optional

# 从已安装的 agentscope 包导入
import agentscope
from agentscope.agent import UserAgent
from agentscope.message import Msg
from agentscope.pipeline import MsgHub

from config import get_settings
from agent_factory import create_coordinator, create_expert_agents, create_consultation_expert, list_agents
from tools_simple import create_travel_toolkit, cleanup_mcp
from tools_expert import cleanup_expert_mcp

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TravelPlannerServer:
    """自驾游规划WebSocket服务器"""

    def __init__(self, host='localhost', port=9001):
        self.host = host
        self.port = port
        self.connected_clients: Set = set()
        self.client_sessions: Dict[str, dict] = {}
        self.global_agents: Dict = {}
        self.current_websocket: Optional = None  # 当前活跃的WebSocket连接
        self.message_cache: Dict[str, dict] = {}  # 用于跟踪消息ID和内容

    async def initialize_agents(self):
        """初始化全局AI代理"""
        try:
            logger.info("🚗 初始化自驾游规划Multi-Agent系统...")

            # 初始化 MCP 工具集
            toolkit = None
            try:
                toolkit = await create_travel_toolkit()
                if toolkit:
                    logger.info("✅ Tavily MCP 工具已加载")
            except Exception as e:
                logger.warning(f"⚠️ MCP 工具加载失败: {e}")

            # 初始化设置
            settings = get_settings()

            # 初始化AgentScope（无Studio）
            agentscope.init(
                project="Self-Driving Travel Planner Multi-Agent",
                name="self_driving_planner_server",
                logging_level="INFO",
                studio_url=None  # WebSocket模式不连接Studio
            )

            logger.info("✅ AgentScope初始化完成（WebSocket模式）")

            # 创建Agent团队
            self.global_agents = {
                'consultation_expert': create_consultation_expert(settings),
                'coordinator': create_coordinator(settings, toolkit),
                'experts': await create_expert_agents(settings, toolkit),
                'settings': settings,
                'toolkit': toolkit
            }

            logger.info("🤖 自驾游专家团队已就绪")
            logger.info("👤 咨询专家：负责收集自驾游需求")
            logger.info(list_agents(self.global_agents['experts']))

            # 设置agent的WebSocket回调
            self.setup_agent_callbacks()
            logger.info("📡 WebSocket回调已设置完成")

            return True
        except Exception as e:
            logger.error(f"❌ 初始化失败: {e}")
            import traceback
            traceback.print_exc()
            return False

    def get_session_id(self, websocket) -> str:
        """获取客户端会话ID"""
        return f"{websocket.remote_address[0]}:{websocket.remote_address[1]}"

    def initialize_client_session(self, session_id: str):
        """初始化客户端会话"""
        if session_id not in self.client_sessions:
            self.client_sessions[session_id] = {
                'state': 'welcome',  # welcome, consultation, planning, chatting
                'consultation_complete': False,
                'user_requirements': '',
                'conversation_history': []
            }

    async def websocket_handler(self, websocket):
        """WebSocket连接处理器"""
        session_id = self.get_session_id(websocket)
        self.connected_clients.add(websocket)
        self.initialize_client_session(session_id)

        # 设置当前活跃的WebSocket连接
        self.current_websocket = websocket
        # 清理之前的消息缓存，确保新连接的干净状态
        self.message_cache.clear()

        logger.info(f"🔌 WebSocket客户端已连接: {websocket.remote_address}")

        try:
            # 发送欢迎消息
            await self.send_welcome_message(websocket, session_id)

            async for message in websocket:
                try:
                    data = json.loads(message)
                    await self.handle_message(websocket, session_id, data)
                except json.JSONDecodeError:
                    await self.send_error(websocket, "无效的JSON格式")
                except Exception as e:
                    logger.error(f"处理消息时出错: {e}")
                    await self.send_error(websocket, f"处理消息时出错: {str(e)}")

        except websockets.exceptions.ConnectionClosed:
            logger.info(f"🔌 WebSocket客户端已断开: {websocket.remote_address}")
        except Exception as e:
            logger.error(f"WebSocket处理错误: {e}")
        finally:
            self.connected_clients.discard(websocket)
            if session_id in self.client_sessions:
                del self.client_sessions[session_id]
            # 清除当前WebSocket连接
            if self.current_websocket == websocket:
                self.current_websocket = None
            # 清理消息缓存
            self.message_cache.clear()

    async def send_welcome_message(self, websocket, session_id: str):
        """发送欢迎消息"""
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

        await self.send_message(websocket, {
            'type': 'assistant_message',
            'content': welcome_msg,
            'state': 'welcome'
        })

        # 更新会话状态
        self.client_sessions[session_id]['state'] = 'consultation'

    async def handle_message(self, websocket, session_id: str, data: dict):
        """处理客户端消息"""
        message_type = data.get('type')
        content = data.get('content', '').strip()

        if not content:
            await self.send_error(websocket, "消息内容不能为空")
            return

        session = self.client_sessions[session_id]

        # 检查退出命令
        if content.lower() in ['exit', 'quit', '退出', '结束', 'bye']:
            await self.send_message(websocket, {
                'type': 'system',
                'content': '👋 感谢使用，祝您自驾旅途愉快！'
            })
            await websocket.close()
            return

        # 重置命令
        if content.lower() in ['reset', '重置', '重新开始']:
            await self.reset_session(websocket, session_id)
            return

        # 处理用户输入
        if message_type == 'user_input':
            await self.process_user_input(websocket, session_id, content)
        else:
            await self.send_error(websocket, f"不支持的消息类型: {message_type}")

    async def process_user_input(self, websocket, session_id: str, content: str):
        """处理用户输入"""
        session = self.client_sessions[session_id]

        # 记录对话历史
        session['conversation_history'].append({
            'role': 'user',
            'content': content,
            'timestamp': asyncio.get_event_loop().time()
        })

        # 发送用户消息确认
        await self.send_message(websocket, {
            'type': 'user_message',
            'content': content
        })

        try:
            if session['state'] == 'consultation' and not session['consultation_complete']:
                # 咨询阶段
                await self.send_progress_update(websocket, 'consultation', '💭 咨询专家正在分析您的需求...')
                response = await self.process_consultation_phase(content, session_id)

                # 检查咨询是否完成
                if "咨询完成" in response or "制定专属旅行方案" in response:
                    session['consultation_complete'] = True
                    session['user_requirements'] = response
                    session['state'] = 'planning'

                    await self.send_message(websocket, {
                        'type': 'assistant_message',
                        'content': response,
                        'state': 'consultation_complete'
                    })

                    # 自动开始规划阶段
                    await self.send_message(websocket, {
                        'type': 'system',
                        'content': '✅ 自驾游需求收集完成，开始制定专属方案...'
                    })

                    planning_response = await self.start_expert_collaboration(session_id, websocket)
                    await self.send_message(websocket, {
                        'type': 'assistant_message',
                        'content': planning_response,
                        'state': 'planning_complete'
                    })

                    session['state'] = 'chatting'
                else:
                    await self.send_message(websocket, {
                        'type': 'assistant_message',
                        'content': response,
                        'state': 'consultation'
                    })

            elif session['state'] == 'chatting':
                # 后续对话阶段
                await self.send_progress_update(websocket, 'followup', '🤔 分析您的补充问题...')
                response = await self.process_followup_question(content, session_id)
                await self.send_message(websocket, {
                    'type': 'assistant_message',
                    'content': response,
                    'state': 'chatting'
                })

            else:
                await self.send_error(websocket, "会话状态异常，请重置会话")

        except Exception as e:
            logger.error(f"处理用户输入时出错: {e}")
            import traceback
            traceback.print_exc()
            await self.send_message(websocket, {
                'type': 'assistant_message',
                'content': "抱歉，刚才出现了一些问题。请重新告诉我您的自驾游需求。",
                'state': 'error'
            })

    async def process_consultation_phase(self, content: str, session_id: str) -> str:
        """处理咨询阶段"""
        consultation_expert = self.global_agents['consultation_expert']
        msg = Msg(name="用户", content=content, role="user")
        response = await consultation_expert(msg)

        # 记录对话历史
        session = self.client_sessions[session_id]
        session['conversation_history'].append({
            'role': 'assistant',
            'content': response.content,
            'timestamp': asyncio.get_event_loop().time()
        })

        return response.content

    async def start_expert_collaboration(self, session_id: str, websocket) -> str:
        """启动专家团队协作"""
        try:
            session = self.client_sessions[session_id]
            user_requirements = session['user_requirements']

            coordinator = self.global_agents['coordinator']
            experts = self.global_agents['experts']

            # 发送协作开始通知
            await self.send_progress_update(websocket, 'collaboration_start', '🤖 专家团队开始协作...')

            # 使用MsgHub进行多Agent协作
            expert_list = list(experts.values())
            async with MsgHub(participants=expert_list + [coordinator]):

                # 1. 广播用户需求给所有专家
                await self.send_progress_update(websocket, 'broadcasting', '📢 向专家团队广播用户需求...')
                requirements_broadcast = Msg(
                    name="咨询专家",
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

                # 向每个专家广播需求
                broadcast_tasks = []
                for expert in expert_list:
                    task = expert(requirements_broadcast)
                    broadcast_tasks.append(task)

                await asyncio.gather(*broadcast_tasks, return_exceptions=True)
                await self.send_progress_update(websocket, 'broadcast_complete', '✅ 需求广播完成，专家开始分析...')

                # 2. 协调员分析和任务分配
                await self.send_progress_update(websocket, 'coordination', '🧠 协调员正在分析需求并分配任务...')
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

                analysis = await coordinator(
                    Msg(name="system", content=analysis_prompt, role="system")
                )

                # 3. 专家并行工作
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

                    task = expert(Msg(
                        name="coordinator",
                        content=expert_prompt,
                        role="assistant"
                    ))
                    expert_tasks.append(task)

                # 等待所有专家完成
                expert_results = await asyncio.gather(*expert_tasks, return_exceptions=True)

                # 4. 整合专家建议
                expert_advice_parts = []
                for i, result in enumerate(expert_results):
                    if isinstance(result, Exception):
                        logger.warning(f"专家{i+1}（{expert_list[i].name}）出错: {str(result)[:100]}")
                        continue
                    elif result is not None:
                        content = result.content if hasattr(result, 'content') else str(result)
                        expert_advice_parts.append(
                            f"专家{i+1}（{expert_list[i].name}）建议：\n{content}"
                        )

                expert_advice = "\n\n".join(expert_advice_parts) if expert_advice_parts else "专家暂无建议"

                # 5. 生成最终方案
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
                    Msg(name="system", content=integration_prompt, role="system")
                )

                await self.send_progress_update(websocket, 'collaboration_complete', '🎉 专家协作完成，方案已生成！')
                return final_plan.content

        except Exception as e:
            logger.error(f"专家协作过程出错: {e}")
            return f"专家协作过程出错: {str(e)}"

    async def process_followup_question(self, content: str, session_id: str) -> str:
        """处理后续问题"""
        try:
            coordinator = self.global_agents['coordinator']

            followup_prompt = f"""用户对自驾游方案有补充需求：{content}

请根据用户的问题，提供相应的自驾游解答或方案调整。
重点关注自驾游的特殊需求：路线优化、停车便利、驾驶安全等。
如果需要，可以重新询问专家团队。"""

            response = await coordinator(
                Msg(name="user", content=followup_prompt, role="user")
            )

            # 记录对话历史
            session = self.client_sessions[session_id]
            session['conversation_history'].append({
                'role': 'assistant',
                'content': response.content,
                'timestamp': asyncio.get_event_loop().time()
            })

            return response.content
        except Exception as e:
            logger.error(f"处理后续问题时出错: {e}")
            return f"处理后续问题时出错: {str(e)}"

    async def reset_session(self, websocket, session_id: str):
        """重置会话"""
        self.initialize_client_session(session_id)
        await self.send_message(websocket, {
            'type': 'system',
            'content': '🔄 会话已重置'
        })
        await self.send_welcome_message(websocket, session_id)

    async def send_message(self, websocket, message: dict):
        """发送消息到客户端"""
        try:
            await websocket.send(json.dumps(message, ensure_ascii=False))
        except Exception as e:
            logger.error(f"发送消息失败: {e}")

    async def send_error(self, websocket, error_message: str):
        """发送错误消息"""
        await self.send_message(websocket, {
            'type': 'error',
            'content': error_message
        })

    async def send_expert_stream(self, websocket, expert_name: str, message: dict, phase: str = 'working'):
        """发送专家流式输出，支持基于ID的消息更新"""
        if not message or 'id' not in message:
            return

        message_id = message['id']

        # 检查是否为消息更新
        if message_id in self.message_cache:
            # 更新现有消息的内容
            cached_message = self.message_cache[message_id]

            # 合并或更新content
            if 'content' in message:
                cached_message['content'] = message['content']

            # 更新时间戳
            cached_message['timestamp'] = message.get('timestamp', asyncio.get_event_loop().time())

            # 发送更新后的消息
            await self.send_message(websocket, cached_message)
        else:
            # 新消息，缓存并发送
            self.message_cache[message_id] = message.copy()
            await self.send_message(websocket, message)

    async def send_progress_update(self, websocket, phase: str, message: str, agent_name: str = None):
        """发送进度更新消息"""
        update_data = {
            'type': 'progress_update',
            'phase': phase,
            'content': message,
            'timestamp': asyncio.get_event_loop().time()
        }
        if agent_name:
            update_data['agent_name'] = agent_name

        await self.send_message(websocket, update_data)

    async def agent_output_callback(self, agent_name: str, message: dict):
        """Agent输出回调函数，将agent的输出发送到WebSocket"""
        if self.current_websocket:
            # message已经是正确的格式，直接发送
            await self.send_expert_stream(self.current_websocket, agent_name, message, 'output')

    def setup_agent_callbacks(self):
        """为所有agent设置WebSocket回调"""
        if not self.global_agents:
            return

        # 设置协调员的回调
        coordinator = self.global_agents.get('coordinator')
        if coordinator and hasattr(coordinator, 'set_websocket_callback'):
            coordinator.set_websocket_callback(self.agent_output_callback)

        # 设置咨询专家的回调
        consultation_expert = self.global_agents.get('consultation_expert')
        if consultation_expert and hasattr(consultation_expert, 'set_websocket_callback'):
            consultation_expert.set_websocket_callback(self.agent_output_callback)

        # 设置所有专家的回调
        experts = self.global_agents.get('experts', {})
        for expert_name, expert in experts.items():
            if hasattr(expert, 'set_websocket_callback'):
                expert.set_websocket_callback(self.agent_output_callback)

    async def start_server(self):
        """启动WebSocket服务器"""
        # 初始化Agent系统
        if not await self.initialize_agents():
            logger.error("❌ Agent系统初始化失败，无法启动服务器")
            return

        logger.info(f"🚀 启动WebSocket服务器在 {self.host}:{self.port}...")

        try:
            async with websockets.serve(self.websocket_handler, self.host, self.port):
                logger.info(f"✅ WebSocket服务器已启动: ws://{self.host}:{self.port}")
                logger.info("📱 等待客户端连接...")

                # 保持服务器运行
                await asyncio.Future()  # run forever

        except KeyboardInterrupt:
            logger.info("\n👋 WebSocket服务器已停止")
        except Exception as e:
            logger.error(f"❌ 服务器启动失败: {e}")
        finally:
            # 清理资源
            try:
                await cleanup_mcp()
                await cleanup_expert_mcp()
            except Exception as e:
                logger.error(f"清理资源时出错: {e}")

async def main():
    """主函数"""
    server = TravelPlannerServer(host='localhost', port=9001)
    await server.start_server()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("程序被用户中断")
    except Exception as e:
        logger.error(f"程序异常退出: {e}")