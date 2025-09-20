# -*- coding: utf-8 -*-
"""The structured output models for werewolf game."""
from typing import Literal

from pydantic import BaseModel, Field

from agentscope.agent import AgentBase


class DiscussionModel(BaseModel):
    """The output format for discussion."""

    reach_agreement: bool = Field(
        description="你们是否已经达成一致",
    )


def get_vote_model(agents: list[AgentBase]) -> type[BaseModel]:
    """Get the vote model by player names."""
    from enum import Enum
    
    # Create dynamic enum for player names
    PlayerNames = Enum('PlayerNames', {agent.name: agent.name for agent in agents})
    
    class VoteModel(BaseModel):
        """The vote output format."""

        vote: PlayerNames = Field(  # type: ignore
            description="你想投票的玩家姓名",
        )

    return VoteModel


class WitchResurrectModel(BaseModel):
    """The output format for witch resurrect action."""

    resurrect: bool = Field(
        description="你是否想复活这个玩家",
    )


def get_poison_model(agents: list[AgentBase]) -> type[BaseModel]:
    """Get the poison model by player names."""
    from enum import Enum
    
    # Create dynamic enum for player names
    PlayerNames = Enum('PlayerNames', {agent.name: agent.name for agent in agents})

    class WitchPoisonModel(BaseModel):
        """The output format for witch poison action."""

        poison: bool = Field(
            description="你想使用毒药吗",
        )
        name: PlayerNames | None = Field(  # type: ignore
            description="你想毒死的玩家姓名，如果你不想毒死任何人，请留空",
            default=None,
        )

    return WitchPoisonModel


def get_seer_model(agents: list[AgentBase]) -> type[BaseModel]:
    """Get the seer model by player names."""
    from enum import Enum
    
    # Create dynamic enum for player names
    PlayerNames = Enum('PlayerNames', {agent.name: agent.name for agent in agents})

    class SeerModel(BaseModel):
        """The output format for seer action."""

        name: PlayerNames = Field(  # type: ignore
            description="你想查验的玩家姓名",
        )

    return SeerModel


def get_hunter_model(agents: list[AgentBase]) -> type[BaseModel]:
    """Get the hunter model by player agents."""
    from enum import Enum
    
    # Create dynamic enum for player names
    PlayerNames = Enum('PlayerNames', {agent.name: agent.name for agent in agents})

    class HunterModel(BaseModel):
        """The output format for hunter action."""

        shoot: bool = Field(
            description="你是否想使用射击能力",
        )
        name: PlayerNames | None = Field(  # type: ignore
            description="你想射击的玩家姓名，如果你不想使用这个能力，请留空",
            default=None,
        )

    return HunterModel
