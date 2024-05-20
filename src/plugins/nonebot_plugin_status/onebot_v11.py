"""
@Author         : yanyongyu
@Date           : 2022-09-02 11:35:48
@LastEditors    : yanyongyu
@LastEditTime   : 2023-03-30 18:25:12
@Description    : OneBot v11 matchers for status plugin
@GitHub         : https://github.com/yanyongyu
"""

__author__ = "yanyongyu"
import json
from nonebot import logger, on_type, on_message, on_command
from nonebot.adapters.onebot.v11 import PokeNotifyEvent, PrivateMessageEvent, GroupMessageEvent, Bot
from . import server_status, status_config, status_permission, switchFile
from nonebot.permission import SUPERUSER
from nonebot.adapters.onebot.v11.permission import GROUP_ADMIN, GROUP_OWNER


async def switch_status(bot: Bot, event: PokeNotifyEvent) -> bool:
    if event.is_tome():
        # 读取状态
        with open(switchFile, 'r', encoding='utf-8') as f:
            switch = json.load(f)
        # 判断是否开启
        # 找群，找不到就True
        if str(event.group_id) not in switch:
            return False
        if not switch[str(event.group_id)]:
            await bot.send(event, "本群状态已被关闭")
            return False
        return True
    return False

if status_config.server_status_enabled:
    group_poke = on_type(
        PokeNotifyEvent,
        rule=switch_status,
        permission=status_permission,
        priority=10,
        handlers=[server_status],
    )
    """Poke notify matcher.

    双击头像拍一拍
    """


async def _poke(event: PrivateMessageEvent) -> bool:
    return event.sub_type == "friend" and event.message[0].type == "poke"


if status_config.server_status_enabled:
    poke = on_message(
        _poke,
        permission=status_permission,
        priority=10,
        block=True,
        handlers=[server_status],
    )
    """Poke message matcher.

    私聊发送戳一戳
    """

switchst = on_command("状态开关", permission=SUPERUSER | GROUP_ADMIN | GROUP_OWNER)


@switchst.handle()
async def _(event: GroupMessageEvent):
    logger.info("status开关")
    # 找json文件是否有这个群，没有就创建并FALSE
    with open(switchFile, 'r', encoding='utf-8') as f:
        switch = json.load(f)
    if str(event.group_id) not in switch:
        switch[str(event.group_id)] = True
        with open(switchFile, 'w', encoding='utf-8') as f:
            json.dump(switch, f)
    else:
        switch[str(event.group_id)] = not switch[str(event.group_id)]
    with open(switchFile, 'w', encoding='utf-8') as f:
        json.dump(switch, f)
    if switch[str(event.group_id)]:
        await switchst.finish("状态已开启")
    await switchst.finish("状态已关闭")
