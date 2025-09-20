# -*- coding: utf-8 -*-
# pylint: disable=too-many-branches, too-many-statements, no-name-in-module
"""A werewolf game implemented by agentscope."""
import asyncio
import os

from agentscope.formatter._anthropic_formatter import AnthropicChatFormatter
from structured_output import (
    DiscussionModel,
    get_vote_model,
    get_poison_model,
    WitchResurrectModel,
    get_seer_model,
    get_hunter_model,
)
from prompt import Prompts
from utils import (
    check_winning,
    majority_vote,
    get_player_name,
    names_to_str,
    EchoAgent,
    MAX_GAME_ROUND,
    MAX_DISCUSSION_ROUND,
)
from agentscope.agent import ReActAgent
from agentscope.model import AnthropicChatModel
from agentscope.pipeline import MsgHub, sequential_pipeline, fanout_pipeline

NAME_TO_ROLE = {}
role_mapping = {
    '村民': 'villager',
    '狼人': 'werewolf', 
    '预言家': 'seer',
    '女巫': 'witch',
    '猎人': 'hunter'
}
moderator = EchoAgent()
healing, poison = True, True
villagers, werewolves, seer, witch, hunter = [], [], [], [], []
current_alive = []


async def hunter_stage(
    hunter_agent: ReActAgent,
) -> str | None:
    """Because the hunter's stage may happen in two places: killed at night
    or voted during the day, we define a function here to avoid duplication."""
    global current_alive, moderator
    msg_hunter = await hunter_agent(
        await moderator(Prompts.to_hunter.format(name=hunter_agent.name)),
        structured_model=get_hunter_model(current_alive),
    )
    if msg_hunter.metadata.get("shoot"):
        return msg_hunter.metadata.get("name", None)
    return None


def update_players(dead_players: list[str]) -> None:
    """Update the global alive players list by removing the dead players."""
    global werewolves, villagers, seer, hunter, witch, current_alive
    werewolves = [_ for _ in werewolves if _.name not in dead_players]
    villagers = [_ for _ in villagers if _.name not in dead_players]
    seer = [_ for _ in seer if _.name not in dead_players]
    hunter = [_ for _ in hunter if _.name not in dead_players]
    witch = [_ for _ in witch if _.name not in dead_players]
    current_alive = [_ for _ in current_alive if _.name not in dead_players]


async def create_player(role: str) -> ReActAgent:
    """Create a player with the given name and role."""
    name = get_player_name()
    global NAME_TO_ROLE
    NAME_TO_ROLE[name] = role
    agent = ReActAgent(
        name=name,
        sys_prompt=Prompts.system_prompt.format(
            player_name=name,
            guidance=getattr(Prompts, f"notes_{role_mapping.get(role, role)}"),
        ),
        model=AnthropicChatModel(
            model_name="claude-sonnet-4-20250514",
            api_key="sk-zd91Lk9LYpIm8RQL7e15Cd196d1b4986BfCdAb8633DdDd97",
            max_tokens=40960,
            stream=True,  # 可配置的流式输出
            # 支持自定义 base_url（用于代理或自定义端点）
            client_args={
                "base_url":"https://api.mjdjourney.cn"
            }
        ),    
        formatter=AnthropicChatFormatter(),
        
    )
    await agent.observe(
        await moderator(
            f"[仅限{name}] {name}，你的角色是{role}。",
        ),
    )
    return agent


async def main() -> None:
    """The main entry of the werewolf game"""
    # Enable studio if you want
    # import agentscope
    # agentscope.init(
    #     studio_url="http://localhost:3000",
    #     project="Werewolf Game",
    # )
    global healing, poison, villagers, werewolves, seer, witch, hunter
    global current_alive
    # 创建玩家
    villagers = [await create_player("村民") for _ in range(3)]
    werewolves = [await create_player("狼人") for _ in range(3)]
    seer = [await create_player("预言家")]
    witch = [await create_player("女巫")]
    hunter = [await create_player("猎人")]
    # 按姓名顺序发言
    current_alive = sorted(
        werewolves + villagers + seer + witch + hunter,
        key=lambda _: _.name,
    )

    # 游戏开始！
    for _ in range(MAX_GAME_ROUND):
        # 为所有玩家创建一个 MsgHub 来广播消息
        async with MsgHub(
            participants=current_alive,
            enable_auto_broadcast=False,  # 仅手动广播
            name="all_players",
        ) as all_players_hub:
            # 夜晚阶段
            await all_players_hub.broadcast(
                await moderator(Prompts.to_all_night),
            )
            killed_player, poisoned_player, shot_player = None, None, None

            # 狼人讨论
            async with MsgHub(
                werewolves,
                enable_auto_broadcast=True,
                announcement=await moderator(
                    Prompts.to_wolves_discussion.format(
                        names_to_str(werewolves),
                        names_to_str(current_alive),
                    ),
                ),
            ) as werewolves_hub:
                # 讨论
                res = None
                for _ in range(1, MAX_DISCUSSION_ROUND * len(werewolves) + 1):
                    res = await werewolves[_ % len(werewolves)](
                        structured_model=DiscussionModel,
                    )
                    if _ % len(werewolves) == 0 and res.metadata.get(
                        "reach_agreement",
                    ):
                        break

                # 狼人投票
                # 禁用自动广播以避免跟随他人投票
                werewolves_hub.set_auto_broadcast(False)
                msgs_vote = await fanout_pipeline(
                    werewolves,
                    msg=await moderator(content=Prompts.to_wolves_vote),
                    structured_model=get_vote_model(current_alive),
                    enable_gather=False,
                )
                killed_player, votes = majority_vote(
                    [_.metadata.get("vote") for _ in msgs_vote],
                )
                # 延迟投票结果的广播
                await werewolves_hub.broadcast(
                    [
                        *msgs_vote,
                        await moderator(
                            Prompts.to_wolves_res.format(votes, killed_player),
                        ),
                    ],
                )

            # 女巫回合
            await all_players_hub.broadcast(
                await moderator(Prompts.to_all_witch_turn),
            )
            msg_witch_poison = None
            for agent in witch:
                # 女巫不能治疗自己
                msg_witch_resurrect = None
                if healing and killed_player != agent.name:
                    msg_witch_resurrect = await agent(
                        await moderator(
                            Prompts.to_witch_resurrect.format(
                                witch_name=agent.name,
                                dead_name=killed_player,
                            ),
                        ),
                        structured_model=WitchResurrectModel,
                    )
                    if msg_witch_resurrect.metadata.get("resurrect"):
                        killed_player = None
                        healing = False

                if poison and not (
                    msg_witch_resurrect
                    and msg_witch_resurrect.metadata["resurrect"]
                ):
                    msg_witch_poison = await agent(
                        await moderator(
                            Prompts.to_witch_poison.format(
                                witch_name=agent.name,
                            ),
                        ),
                        structured_model=get_poison_model(current_alive),
                    )
                    if msg_witch_poison.metadata.get("poison"):
                        poisoned_player = msg_witch_poison.metadata.get("name")
                        poison = False

            # 预言家回合
            await all_players_hub.broadcast(
                await moderator(Prompts.to_all_seer_turn),
            )
            for agent in seer:
                msg_seer = await agent(
                    await moderator(
                        Prompts.to_seer.format(
                            agent.name,
                            names_to_str(current_alive),
                        ),
                    ),
                    structured_model=get_seer_model(current_alive),
                )
                if msg_seer.metadata.get("name"):
                    player = msg_seer.metadata["name"]
                    await agent.observe(
                        await moderator(
                            Prompts.to_seer_result.format(
                                agent_name=player,
                                role=NAME_TO_ROLE[player],
                            ),
                        ),
                    )

            # 猎人回合
            for agent in hunter:
                # 如果被杀且不是被女巫毒死
                if (
                    killed_player == agent.name
                    and poisoned_player != agent.name
                ):
                    shot_player = await hunter_stage(agent)

            # 更新存活玩家
            dead_tonight = [killed_player, poisoned_player, shot_player]
            update_players(dead_tonight)

            # 白天阶段
            if len([_ for _ in dead_tonight if _]) > 0:
                await all_players_hub.broadcast(
                    await moderator(
                        Prompts.to_all_day.format(
                            names_to_str([_ for _ in dead_tonight if _]),
                        ),
                    ),
                )
            else:
                await all_players_hub.broadcast(
                    await moderator(Prompts.to_all_peace),
                )

            # 检查获胜条件
            res = check_winning(current_alive, werewolves)
            if res:
                await moderator(res)
                return

            # 讨论
            await all_players_hub.broadcast(
                await moderator(
                    Prompts.to_all_discuss.format(
                        names=names_to_str(current_alive),
                    ),
                ),
            )
            # 开启自动广播以启用讨论
            all_players_hub.set_auto_broadcast(True)
            await sequential_pipeline(current_alive)
            # 禁用自动广播以避免信息泄露
            all_players_hub.set_auto_broadcast(False)

            # 投票
            msgs_vote = await fanout_pipeline(
                current_alive,
                await moderator(
                    Prompts.to_all_vote.format(names_to_str(current_alive)),
                ),
                structured_model=get_vote_model(current_alive),
                enable_gather=False,
            )
            voted_player, votes = majority_vote(
                [_.metadata.get("vote") for _ in msgs_vote],
            )
            await all_players_hub.broadcast(
                [
                    *msgs_vote,
                    await moderator(
                        Prompts.to_all_res.format(votes, voted_player),
                    ),
                ],
            )

            shot_player = None
            for agent in hunter:
                if voted_player == agent.name:
                    shot_player = await hunter_stage(agent)
                    if shot_player:
                        await all_players_hub.broadcast(
                            await moderator(
                                Prompts.to_all_hunter_shoot.format(
                                    shot_player,
                                ),
                            ),
                        )

            # 更新存活玩家
            dead_today = [voted_player, shot_player]
            update_players(dead_today)

            # 检查获胜条件
            res = check_winning(current_alive, werewolves)
            if res:
                await moderator(res)
                return


if __name__ == "__main__":
    import agentscope
    agentscope.init(studio_url="http://localhost:3000")
    asyncio.run(main())
