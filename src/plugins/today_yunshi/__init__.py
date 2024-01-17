"""这是一个今日运势插件，可以查看今日运势。"""

import time
import random
from os import path
from pathlib import Path
from datetime import datetime
from nonebot import on_command
from nonebot.matcher import Matcher
from nonebot.adapters.onebot.v11 import MessageEvent, PrivateMessageEvent
from nonebot.plugin import PluginMetadata
from .models import MemberData


try:
    import ujson as json
except ImportError:
    import json

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
    member_model = await MemberData.get_or_none(user_id=str(event.user_id))

    if member_model is None:
        # 如果没有数据则创建数据
        result_text, luckid = randomluck(str(event.user_id), {})
        await MemberData.create(
            user_id=str(event.user_id), luckid=luckid, time=datetime.now()
        )

        if isinstance(event, PrivateMessageEvent):
            await matcher.finish(result_text)
        else:
            await matcher.finish("\n" + result_text, at_sender=True)
    else:
        # 如果有数据则判断是否是今天的数据
        if member_model.time.strftime("%Y-%m-%d") != time.strftime(
            "%Y-%m-%d", time.localtime(time.time())
        ):
            # 如果不是今天的数据则随机运势
            result, luckid = randomluck(str(event.user_id), {})
            member_model = await MemberData.get(user_id=str(event.user_id))
            member_model.luckid = luckid
            member_model.time = datetime.now()
            await member_model.save()
        else:
            # 如果是今天的数据则返回今天的数据
            r = str(member_model.luckid)
            result = (
                f"----\n{luckdata[r]['运势']}\n{luckdata[r]['星级']}\n"
                f"{luckdata[r]['签文']}\n{luckdata[r]['解签']}\n----"
            )
        if isinstance(event, PrivateMessageEvent):
            await matcher.finish(result)
        else:
            await matcher.finish("\n" + result, at_sender=True)


def randomluck(arg, memberdata):
    """
    随机获取运势信息。

    Args:
        arg (str): 参数。
        memberdata (dict): 成员数据。

    Returns:
        tuple: 运势信息和选择的运势编号。
    """
    # 判断是否有在json文件中和是否有time键值
    if arg in memberdata and "time" in memberdata[arg]:
        if memberdata[arg]["time"] != time.strftime(
            "%Y-%m-%d", time.localtime(time.time())
        ):
            r = random.choice(list(luckdata.keys()))
        else:
            r = memberdata[arg]["id"]
    else:
        r = random.choice(list(luckdata.keys()))
    result_text = (
        f"----\n{luckdata[r]['运势']}\n{luckdata[r]['星级']}\n"
        f"{luckdata[r]['签文']}\n{luckdata[r]['解签']}\n----"
    )
    return result_text, r
