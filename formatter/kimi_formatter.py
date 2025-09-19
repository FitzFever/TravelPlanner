# -*- coding: utf-8 -*-
"""Kimi formatter 模块，用于 Moonshot AI"""

import json
from typing import Any, Optional
import logging

logger = logging.getLogger(__name__)


class KimiMultiAgentFormatter:
    """
    Kimi Multi-Agent 格式化器
    处理 Moonshot AI 的消息格式，包括工具调用
    """
    
    def __init__(self, max_tokens: int = 200000, **kwargs):
        """
        初始化 Kimi 格式化器
        
        Args:
            max_tokens: 最大token数，Kimi 支持 256K 上下文
        """
        self.max_tokens = max_tokens
        self.kwargs = kwargs
    
    async def format(self, msgs: list, **kwargs: Any) -> list[dict[str, Any]]:
        """
        异步格式化消息列表，兼容 AgentScope 的接口
        
        Args:
            msgs: 消息列表（Msg 对象列表）
            **kwargs: 额外的关键字参数
            
        Returns:
            格式化后的消息列表
        """
        # 验证输入
        self.assert_list_of_msgs(msgs)
        # 内部调用 _format 方法
        return await self._format(msgs)
    
    async def _format(self, msgs: list) -> list[dict[str, Any]]:
        """
        内部格式化方法，处理各种消息类型和内容块
        
        Args:
            msgs: 消息列表
            
        Returns:
            格式化后的消息列表
        """
        messages = []
        
        for msg in msgs:
            # 如果消息有 get_content_blocks 方法，使用它
            if hasattr(msg, 'get_content_blocks'):
                formatted_msg = await self._format_msg_with_blocks(msg)
                if formatted_msg:
                    messages.extend(formatted_msg if isinstance(formatted_msg, list) else [formatted_msg])
            # 处理普通 Msg 对象
            elif hasattr(msg, 'role') and hasattr(msg, 'content'):
                messages.append({
                    'role': msg.role,
                    'content': msg.content if msg.content else " "
                })
            # 处理字典
            elif isinstance(msg, dict):
                messages.append(msg)
            # 其他类型
            else:
                try:
                    content = self._get_content_from_msg(msg)
                    messages.append({
                        'role': getattr(msg, 'role', 'assistant'),
                        'content': content
                    })
                except Exception as e:
                    logger.warning(f"Failed to format message: {e}")
        
        return messages
    
    async def _format_msg_with_blocks(self, msg) -> list[dict[str, Any]]:
        """
        处理包含内容块的消息
        
        Args:
            msg: 包含 get_content_blocks 方法的消息
            
        Returns:
            格式化后的消息或消息列表
        """
        messages = []
        content_blocks = []
        tool_calls = []
        
        # 处理各种内容块
        for block in msg.get_content_blocks():
            typ = block.get("type")
            
            if typ == "text":
                content_blocks.append(block.get("text", ""))
                
            elif typ == "tool_use":
                # Moonshot/Kimi 使用 tool_calls 格式
                tool_calls.append({
                    "id": block.get("id"),
                    "type": "function",
                    "function": {
                        "name": block.get("name"),
                        "arguments": json.dumps(
                            block.get("input", {}),
                            ensure_ascii=False
                        )
                    }
                })
                
            elif typ == "tool_result":
                # 工具结果作为单独的消息
                messages.append({
                    "role": "tool",
                    "tool_call_id": block.get("id"),
                    "content": self._convert_tool_result_to_string(
                        block.get("output")
                    ),
                    "name": block.get("name")
                })
                
            elif typ == "image":
                # 处理图像块
                source = block.get("source", {})
                if source.get("type") == "url":
                    content_blocks.append({
                        "type": "image_url",
                        "image_url": {
                            "url": source.get("url"),
                            "detail": "auto"
                        }
                    })
                elif source.get("type") == "base64":
                    media_type = source.get("media_type", "image/jpeg")
                    data = source.get("data")
                    content_blocks.append({
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{media_type};base64,{data}",
                            "detail": "auto"
                        }
                    })
            else:
                if typ is not None:
                    logger.warning(f"Unsupported block type: {typ}")
        
        # 构建主消息
        if content_blocks or tool_calls:
            # 处理内容
            if content_blocks:
                # 如果只有文本，合并为字符串
                if all(isinstance(b, str) for b in content_blocks):
                    content = "\n".join(content_blocks)
                else:
                    # 混合内容，保持列表格式
                    content = []
                    for block in content_blocks:
                        if isinstance(block, str):
                            content.append({"type": "text", "text": block})
                        else:
                            content.append(block)
            else:
                content = " "
            
            msg_formatted = {
                "role": msg.role,
                "content": content
            }
            
            # 添加工具调用
            if tool_calls:
                msg_formatted["tool_calls"] = tool_calls
            
            messages.append(msg_formatted)
        
        return messages if messages else None
    
    def _get_content_from_msg(self, msg) -> str:
        """
        从消息对象中提取内容
        
        Args:
            msg: 消息对象
            
        Returns:
            消息内容字符串
        """
        if hasattr(msg, 'get_text_content'):
            return msg.get_text_content()
        elif hasattr(msg, 'content'):
            return msg.content
        elif hasattr(msg, '__dict__'):
            return str(msg.__dict__)
        else:
            return str(msg)
    
    def _convert_tool_result_to_string(self, output: Any) -> str:
        """
        将工具结果转换为字符串
        
        Args:
            output: 工具输出
            
        Returns:
            字符串格式的输出
        """
        if isinstance(output, str):
            return output
        elif isinstance(output, list):
            # 处理结构化输出
            result_parts = []
            for item in output:
                if isinstance(item, dict):
                    if item.get("type") == "text":
                        result_parts.append(item.get("text", ""))
                    else:
                        result_parts.append(json.dumps(item, ensure_ascii=False))
                else:
                    result_parts.append(str(item))
            return "\n".join(result_parts)
        else:
            return json.dumps(output, ensure_ascii=False) if output else ""
    
    def assert_list_of_msgs(self, msgs: list) -> None:
        """
        验证消息列表格式
        
        Args:
            msgs: 消息列表
        """
        if not isinstance(msgs, list):
            raise TypeError(f"Expected list of messages, got {type(msgs)}")
    
    async def _count(self, formatted_msgs: list) -> int:
        """
        计算消息的 token 数量（简化实现）
        
        Args:
            formatted_msgs: 格式化后的消息
            
        Returns:
            估算的 token 数
        """
        total_chars = 0
        for msg in formatted_msgs:
            if isinstance(msg.get('content'), str):
                total_chars += len(msg['content'])
            elif isinstance(msg.get('content'), list):
                for item in msg['content']:
                    if isinstance(item, dict) and 'text' in item:
                        total_chars += len(item['text'])
                    elif isinstance(item, str):
                        total_chars += len(item)
            
            # 计算工具调用的字符数
            if 'tool_calls' in msg:
                total_chars += len(json.dumps(msg['tool_calls']))
        
        # 简单估算：每个字符约 0.5 个 token
        return int(total_chars * 0.5)