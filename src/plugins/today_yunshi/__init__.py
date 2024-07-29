"""这是一个今日运势插件，可以查看今日运势。"""

import random
import time
from datetime import datetime
from os import path
from pathlib import Path

import ujson as json
from nonebot import logger, on_command
from nonebot.adapters.onebot.v11 import MessageEvent
from nonebot.matcher import Matcher
from nonebot.plugin import PluginMetadata

from .models import MemberData

__plugin_meta__ = PluginMetadata(
    name="今日运势",
    description="看看今天的运势吧",
    usage='发送"今日运势"或"运势"',
)

Luck = on_command("今日运势", aliases={"运势"})
luckpath = Path(path.join(path.dirname(__file__), "Fortune.json"))
with open(luckpath, "r", encoding="utf-8") as f:
    luckdata = json.load(f)


@Luck.handle()
async def _(matcher: Matcher, event: MessageEvent):
    # 读取数据库
    member_model = await MemberData.get_or_none(user_id=event.user_id)

    if member_model is None:
        # 如果没有数据则创建数据
        result, luckid = randomluck()
        await MemberData.create(
            user_id=event.user_id, luckid=luckid, time=datetime.now()
        )
    elif member_model.time.strftime("%Y-%m-%d") == time.strftime("%Y-%m-%d"):
        # 如果是今天的数据则返回今天的数据
        logger.info(f"member_model.luckid1: {member_model.luckid}")
        r = str(member_model.luckid)
        result = (
            f"----\n{luckdata[r]['运势']}\n{luckdata[r]['星级']}\n"
            f"{luckdata[r]['签文']}\n{luckdata[r]['解签']}\n----"
        )
    else:
        # 如果不是今天的数据则随机运势
        result, luckid = randomluck()
        logger.info(f"member_model.luckid2: {member_model.luckid}")
        member_model.luckid = luckid
        member_model.time = datetime.now()
        await member_model.save()
    await matcher.finish(result, reply_message=True)


def randomluck():
    """
    随机获取运势信息。

    Args:
        arg (str): 参数。
        memberdata (dict): 成员数据。

    Returns:
        tuple: 运势信息和选择的运势编号。
    """
    # 判断是否有在 json 文件中和是否有 time 键值
    r = random.choice(list(luckdata.keys()))
    result_text = (
        f"----\n{luckdata[r]['运势']}\n{luckdata[r]['星级']}\n"
        f"{luckdata[r]['签文']}\n{luckdata[r]['解签']}\n----"
    )
    return result_text, r
