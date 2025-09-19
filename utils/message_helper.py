#!/usr/bin/env python3
"""
消息助手模块 - 确保消息格式正确
"""

from agentscope.message import Msg
from typing import Optional


def create_safe_msg(name: str, content: Optional[str], role: str = "assistant") -> Msg:
    """
    创建安全的消息对象，确保 content 不为 None
    
    Args:
        name: 发送者名称
        content: 消息内容（可能为 None）
        role: 消息角色
    
    Returns:
        Msg: 安全的消息对象
    """
    # 如果 content 为 None，使用空字符串
    safe_content = content if content is not None else ""
    
    return Msg(
        name=name,
        content=safe_content,
        role=role
    )


def validate_msg_content(msg: Msg) -> Msg:
    """
    验证并修复消息的 content 字段
    
    Args:
        msg: 消息对象
    
    Returns:
        Msg: 修复后的消息对象
    """
    if msg.content is None:
        msg.content = ""
    elif isinstance(msg.content, list) and len(msg.content) == 0:
        msg.content = ""
    
    return msg