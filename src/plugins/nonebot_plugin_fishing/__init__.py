import random
from nonebot import on_command, require

require("nonebot_plugin_orm")  # noqa
from nonebot.plugin import PluginMetadata
from nonebot.adapters import Event, Message
from nonebot.params import CommandArg

import asyncio

from .config import Config, config
from .data_source import (choice, get_quality,
                          switch_fish,
                          get_stats,
                          save_fish,
                          get_backpack,
                          sell_fish,
                          get_balance, get_switch_fish)
from nonebot.adapters.onebot.v11 import (
    GroupMessageEvent, PrivateMessageEvent, MessageEvent, Message, Bot
)
from nonebot.adapters.onebot.v11.permission import GROUP_ADMIN,GROUP_OWNER
from nonebot.permission import SUPERUSER
from nonebot.adapters.onebot.v11.helpers import (
    Cooldown,
    CooldownIsolateLevel,
)
from nonebot import get_driver
__plugin_meta__ = PluginMetadata(
    name="赛博钓鱼",
    description="你甚至可以电子钓鱼",
    usage="发送“钓鱼”，放下鱼竿。",
    type="application",
    homepage="https://github.com/C14H22O/nonebot-plugin-fishing",
    config=Config,
    supported_adapters=None
)

Bot_NICKNAME = list(get_driver().config.nickname)
Bot_NICKNAME = Bot_NICKNAME[0] if Bot_NICKNAME else "bot"
fishing = on_command("fishing", aliases={
                     "钓鱼"}, priority=5, rule=get_switch_fish)
stats = on_command("stats", aliases={"统计信息"}, priority=5)
backpack = on_command("backpack", aliases={"背包"}, priority=5)
sell = on_command("sell", aliases={"卖鱼"}, priority=5)
balance = on_command("balance", aliases={"余额"}, priority=5)
switch = on_command("fish_switch", aliases={
                    "开关钓鱼"}, priority=5, permission=GROUP_OWNER|GROUP_ADMIN | SUPERUSER)


@fishing.handle(
    parameterless=[
        Cooldown(
            cooldown=config.fishing_limit,
            prompt="河累了，休息一下吧",
            isolate_level=CooldownIsolateLevel.USER,
        )
    ]
)
async def _fishing(event: Event):
    """钓鱼"""
    user_id = event.get_user_id()
    await fishing.send("正在钓鱼…")
    fish = choice()
    fish_name = fish[0]
    fish_long = fish[1]
    sleep_time = random.randint(1, 6)
    result = ""
    if fish == "河":
        result = "* 河累了，休息..等等...你钓到了一条河？！"
    else:
        result = f"* 你钓到了一条 {get_quality(fish_name)} {fish_name}，长度为 {fish_long}cm！"
    await save_fish(user_id, fish_name, fish_long)
    await asyncio.sleep(sleep_time)
    # result = "* 你钓了一整天，什么也没钓到，但是你的技术有所提升了！"
    await fishing.finish(result, reply_message=True)


@stats.handle()
async def _stats(event: Event):
    """统计信息"""
    user_id = event.get_user_id()
    await stats.finish(await get_stats(user_id), reply_message=True)


@backpack.handle()
async def _backpack(bot: Bot, event: MessageEvent):
    """背包"""
    user_id = event.get_user_id()
    fmt = await get_backpack(user_id)
    return fmt if isinstance(fmt, str) else await send_forward_msg(bot, event, Bot_NICKNAME, bot.self_id, fmt)


@sell.handle()
async def _sell(event: Event, arg: Message = CommandArg()):
    """卖鱼"""
    fish_name = arg.extract_plain_text()
    if fish_name == "":
        await sell.finish("请输入要卖出的鱼的名字，如：卖鱼 小鱼")
    user_id = event.get_user_id()
    await sell.finish(await sell_fish(user_id, fish_name), reply_message=True)


@balance.handle()
async def _balance(event: Event):
    """余额"""
    user_id = event.get_user_id()
    await balance.finish(await get_balance(user_id), reply_message=True)


@switch.handle()
async def _switch(event: GroupMessageEvent | PrivateMessageEvent):
    """钓鱼开关"""
    if await switch_fish(event):
        await switch.finish("钓鱼开关已打开")
    else:
        await switch.finish("钓鱼开关已关闭")


async def send_forward_msg(
    bot: Bot,
    event: MessageEvent,
    name: str,
    uin: str,
    msgs: list,
) -> dict:
    """
    发送转发消息的异步函数。

    参数:
        bot (Bot): 机器人实例
        event (MessageEvent): 消息事件
        name (str): 转发消息的名称
        uin (str): 转发消息的 UIN
        msgs (list): 转发的消息列表

    返回:
        dict: API 调用结果
    """

    def to_json(msg: Message):
        return {"type": "node", "data": {"name": name, "uin": uin, "content": msg}}

    messages = [to_json(msg) for msg in msgs]
    if isinstance(event, GroupMessageEvent):
        return await bot.call_api(
            "send_group_forward_msg", group_id=event.group_id, messages=messages
        )
    return await bot.call_api(
        "send_private_forward_msg", user_id=event.user_id, messages=messages
    )
