# -*- coding: utf-8 -*-
# pylint: disable=too-many-branches
"""The Kimi formatter module for Moonshot AI."""
import json
from typing import Any

from ._openai_formatter import OpenAIChatFormatter, OpenAIMultiAgentFormatter
from .._logging import logger


class KimiChatFormatter(OpenAIChatFormatter):
    """Formatter for Kimi (Moonshot AI) messages.
    
    Kimi API supports OpenAI format but returns tool calls in Anthropic format.
    This formatter handles the conversion between AgentScope messages and Kimi API.
    """

    support_tools_api: bool = True
    """Whether support tools API"""

    support_multiagent: bool = True
    """Whether support multi-agent conversations"""

    support_vision: bool = True
    """Whether support vision data (Kimi K2 supports vision)"""

    def __init__(
        self,
        max_tokens: int = 200000,  # Kimi supports 256K context
        **kwargs,
    ) -> None:
        """Initialize the Kimi chat formatter.

        Args:
            max_tokens (`int`, default `200000`):
                Max tokens allowed for conversation. Kimi supports 256K context.
            **kwargs:
                Additional keyword arguments passed to OpenAIChatFormatter.
        """
        super().__init__(
            max_tokens=max_tokens,
            **kwargs,
        )

    async def _format(
        self,
        msgs: list,
    ) -> list[dict[str, Any]]:
        """Format message objects into Kimi API format.
        
        Kimi returns tool_use blocks in Anthropic format, but we need to handle
        tool_result blocks in OpenAI format for compatibility.
        
        Args:
            msgs: The list of message objects to format.
            
        Returns:
            list[dict[str, Any]]: The formatted messages.
        """
        self.assert_list_of_msgs(msgs)

        messages: list[dict] = []
        for msg in msgs:
            content_blocks = []
            tool_calls = []

            for block in msg.get_content_blocks():
                typ = block.get("type")
                if typ == "text":
                    content_blocks.append({**block})

                elif typ == "tool_use":
                    # Kimi uses Anthropic-style tool_use, convert to OpenAI format
                    tool_calls.append(
                        {
                            "id": block.get("id"),
                            "type": "function",
                            "function": {
                                "name": block.get("name"),
                                "arguments": json.dumps(
                                    block.get("input", {}),
                                    ensure_ascii=False,
                                ),
                            },
                        },
                    )

                elif typ == "tool_result":
                    # Handle tool results in OpenAI format for API compatibility
                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": block.get("id"),
                            "content": self.convert_tool_result_to_string(
                                block.get("output"),
                            ),
                            "name": block.get("name"),
                        },
                    )

                elif typ == "image":
                    # Handle image blocks (Kimi supports vision)
                    source_type = block.get("source", {}).get("type")
                    if source_type == "url":
                        content_blocks.append({
                            "type": "image_url",
                            "image_url": {
                                "url": block["source"]["url"],
                                "detail": "auto"
                            }
                        })
                    elif source_type == "base64":
                        media_type = block["source"].get("media_type", "image/jpeg")
                        data = block["source"]["data"]
                        content_blocks.append({
                            "type": "image_url", 
                            "image_url": {
                                "url": f"data:{media_type};base64,{data}",
                                "detail": "auto"
                            }
                        })

                else:
                    if typ is not None:
                        logger.warning(
                            "Unsupported block type %s in the message, skipped.",
                            typ,
                        )

            # Build content for text and images
            content_msg = []
            for content in content_blocks:
                if content.get("type") == "text":
                    content_msg.append(content.get("text", ""))
                elif content.get("type") == "image_url":
                    # For mixed content, we need to use the content array format
                    if not content_msg:
                        content_msg = []
                    content_msg.append(content)

            # Create message
            if isinstance(content_msg, list) and any(isinstance(c, dict) for c in content_msg):
                # Mixed content with images
                formatted_content = []
                for item in content_msg:
                    if isinstance(item, str):
                        formatted_content.append({"type": "text", "text": item})
                    else:
                        formatted_content.append(item)
                msg_formatted = {
                    "role": msg.role,
                    "content": formatted_content,
                }
            else:
                # Text-only content
                content_text = "\n".join(content_msg) if isinstance(content_msg, list) else ""
                msg_formatted = {
                    "role": msg.role,
                    "content": content_text if content_text else " ",
                }

            if tool_calls:
                msg_formatted["tool_calls"] = tool_calls

            messages.append(msg_formatted)

        return messages


class KimiMultiAgentFormatter(KimiChatFormatter):
    """Multi-agent formatter for Kimi messages."""
    
    def __init__(
        self,
        max_tokens: int = 200000,
        **kwargs,
    ) -> None:
        """Initialize the Kimi multi-agent formatter."""
        super().__init__(
            max_tokens=max_tokens,
            **kwargs,
        )