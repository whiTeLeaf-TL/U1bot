"""
@Author         : yanyongyu
@Date           : 2020-09-18 00:00:13
@LastEditors    : yanyongyu
@LastEditTime   : 2023-03-30 18:26:14
@Description    : Common text matcher for status plugin
@GitHub         : https://github.com/yanyongyu
"""

__author__ = "yanyongyu"
import json
from nonebot import logger, on_command
from nonebot.permission import SUPERUSER
from nonebot.adapters.onebot.v11 import GroupMessageEvent, Bot
from . import server_status, status_config, status_permission, switchFile


async def switch_status(event: GroupMessageEvent) -> bool:
    if isinstance(event, GroupMessageEvent):
        # 读取状态
        with open(switchFile, 'r', encoding='utf-8') as f:
            switch = json.load(f)
        if str(event.group_id) not in switch:
            return True
        # 判断是否开启
        return bool(switch[str(event.group_id)])
    return True


if status_config.server_status_enabled:
    on_command(
        "status",
        rule=switch_status,
        permission=status_permission,
        priority=10,
        handlers=[server_status],
    )
    """`status`/`状态` command matcher"""


