import sys
from typing import TYPE_CHECKING

import nonebot
from nonebot import logger
from nonebot.adapters.onebot.v11 import Adapter as ONEBOT_V11Adapter
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent
from nonebot.exception import IgnoredException
from nonebot.log import default_format, logger_id

if TYPE_CHECKING:
    # avoid sphinx autodoc resolve annotation failed
    # because loguru module do not have `Logger` class actually
    from loguru import Record
nonebot.init()


app = nonebot.get_asgi()
driver = nonebot.get_driver()
driver.register_adapter(ONEBOT_V11Adapter)


nonebot.load_from_toml("pyproject.toml")
from nonebot.message import event_preprocessor

from U1.database import Channel


@event_preprocessor
async def _(bot: Bot, event: GroupMessageEvent):
    "防止双发"
    bot_qqid = bot.self_id
    channel = await Channel.get_or_none(id=str(event.group_id))
    if channel is None:
        await bot.send(
            event, "我们正在尝试注册此群频道，此条信息发送完毕后将会自动注册"
        )
        raise IgnoredException("未找到频道，忽略")
    if channel.assignee != bot_qqid:
        raise IgnoredException("机器人不是频道指定的机器人，忽略")


@event_preprocessor
async def _(bot: Bot, event: GroupMessageEvent):
    "防止机器人自言自语"
    # 检测是否是机器人自己发的消息
    event_qqid = str(event.user_id)
    bot_qqid = bot.self_id
    if event_qqid == bot_qqid:
        raise IgnoredException("机器人自言自语，忽略")


def default_filter(record: "Record"):
    """默认的日志过滤器，根据 `config.log_level` 配置改变日志等级。"""
    log_level = record["extra"].get("nonebot_log_level", "INFO")
    levelno = logger.level(log_level).no if isinstance(log_level, str) else log_level

    # 过滤掉 module 为 src.plugins.chatcout 的日志
    if "src.plugins.chatcout" in record["message"]:
        return False

    return record["level"].no >= levelno


# 移除 NoneBot 默认的日志处理器
logger.remove(logger_id)
# 添加新的日志处理器
logger.add(
    sys.stdout,
    level=0,
    diagnose=True,
    format=default_format,
    filter=default_filter,
)

if __name__ == "__main__":
    nonebot.run()
