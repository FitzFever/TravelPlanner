#!/usr/bin/env python3
"""
安全的 AnthropicChatFormatter - 修复空内容处理问题

这个格式化器继承自官方的 AnthropicChatFormatter，
但添加了对空消息内容的保护，避免 'NoneType' object is not iterable 错误。
"""

from agentscope.formatter import AnthropicChatFormatter


class SafeAnthropicChatFormatter(AnthropicChatFormatter):
    """
    安全的 Anthropic 格式化器
    
    修复了原版在处理 msg.get_content_blocks() 返回 None 时的 TypeError 问题
    """
    
    async def _format(self, msgs):
        """
        重写 _format 方法，添加空值保护
        
        修复核心问题：当 msg.get_content_blocks() 返回 None 时的迭代错误
        """
        self.assert_list_of_msgs(msgs)

        messages = []
        for index, msg in enumerate(msgs):
            content_blocks = []
            
            # 修复：添加空值检查，防止 NoneType 错误
            content_blocks_raw = msg.get_content_blocks()
            if content_blocks_raw is None:
                content_blocks_raw = []

            for block in content_blocks_raw:
                typ = block.get("type")
                if typ in ["thinking", "text", "image"]:
                    content_blocks.append({**block})

                elif typ == "tool_use":
                    content_blocks.append(
                        {
                            "id": block.get("id"),
                            "type": "tool_use",
                            "name": block.get("name"),
                            "input": block.get("input", {}),
                        },
                    )

                elif typ == "tool_result":
                    output = block.get("output")
                    if output is None:
                        content_value = [{"type": "text", "text": None}]
                    elif isinstance(output, list):
                        content_value = output
                    else:
                        content_value = [{"type": "text", "text": str(output)}]
                    messages.append(
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "tool_result",
                                    "tool_use_id": block.get("id"),
                                    "content": content_value,
                                },
                            ],
                        },
                    )
                else:
                    from agentscope._logging import logger
                    logger.warning(
                        "Unsupported block type %s in the message, skipped.",
                        typ,
                    )

            # Claude only allow the first message to be system message
            if msg.role == "system" and index != 0:
                role = "user"
            else:
                role = msg.role

            msg_anthropic = {
                "role": role,
                "content": content_blocks or None,
            }

            # When both content and tool_calls are None, skipped
            if msg_anthropic["content"] or msg_anthropic.get("tool_calls"):
                messages.append(msg_anthropic)

        return messages