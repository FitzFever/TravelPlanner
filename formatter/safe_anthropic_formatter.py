#!/usr/bin/env python3
"""
安全的 Anthropic Formatter - 处理可能为 None 的消息内容
"""

from typing import Any, List
from agentscope.formatter import AnthropicChatFormatter
from agentscope.message import Msg, TextBlock


class SafeAnthropicChatFormatter(AnthropicChatFormatter):
    """
    安全的 Anthropic Formatter，能处理 content 为 None 的消息
    """
    
    async def _format(self, msgs: list[Msg]) -> list[dict[str, Any]]:
        """
        格式化消息，确保所有消息都有有效的 content
        
        Args:
            msgs: 消息列表
            
        Returns:
            格式化后的消息
        """
        # 过滤并修复消息
        safe_msgs = []
        for msg in msgs:
            if msg is None:
                continue
            
            # 确保消息有有效的 content
            if msg.content is None:
                # 创建一个新的消息副本，设置空字符串作为 content
                safe_msg = Msg(
                    name=msg.name,
                    content="",  # 使用空字符串代替 None
                    role=msg.role,
                    metadata=msg.metadata
                )
                safe_msgs.append(safe_msg)
            else:
                safe_msgs.append(msg)
        
        # 调用父类的 _format 方法
        return await super()._format(safe_msgs)