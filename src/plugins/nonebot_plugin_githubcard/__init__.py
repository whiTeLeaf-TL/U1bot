from nonebot.rule import T_State
from nonebot import get_driver
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent, MessageSegment
from .config import Config
from .data_source import get_github_reposity_information
from nonebot.plugin import on_regex
from nonebot.plugin import PluginMetadata

import re

__plugin_meta__ = PluginMetadata(
    name="github card",
    description="展示github仓库卡片",
    usage="github仓库卡片\n发出 github.com/用户名/仓库名 的格式即可自动检测")
global_config = get_driver().config
config = Config(**global_config.dict())
github = on_regex(r"https?://github\.com/([^/]+/[^/]+)",
                  priority=10,
                  block=False)


def match_link_parts(link):
    pattern = r'https?://github\.com/([^/]+/[^/]+)'
    return match.group(0) if (match := re.search(pattern, link)) else None


@github.handle()
async def github_handle(bot: Bot, event: GroupMessageEvent, state: T_State):
    url = match_link_parts(event.get_plaintext())
    imageUrl = await get_github_reposity_information(url)
    if imageUrl == "获取信息失败":
        raise AssertionError
    await github.send(MessageSegment.image(imageUrl))
