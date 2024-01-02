from unittest import result
from nonebot import on_command, logger
from nonebot.adapters.onebot.v11 import MessageEvent, PrivateMessageEvent
from pathlib import Path
from nonebot.plugin import PluginMetadata
from os import path
import random
import time
from nonebot.matcher import Matcher
from .models import MemberData
from datetime import datetime


try:
    import ujson as json
except Exception:
    import json

__plugin_meta__ = PluginMetadata(
    name="今日运势",
    description="看看今天的运势吧",
    usage='发送"今日运势"或"运势"',
)

luck = on_command("今日运势", aliases={"运势"})
luckpath = Path(path.join(path.dirname(__file__), "Fortune.json"))
with open(luckpath, "r", encoding="utf-8") as f:
    luckdata = json.load(f)


@luck.handle()
async def _(matcher: Matcher, event: MessageEvent):
    # 读取数据库
    member_model = await MemberData.get_or_none(user_id=str(event.user_id))

    if member_model is None:
        # 如果没有数据则创建数据
        await MemberData.create(user_id=str(event.user_id))
        result, luckid = randomluck(str(event.user_id), {})
        member_model = await MemberData.get(user_id=str(event.user_id))
        member_model.luckid = luckid
        await member_model.save()
        if isinstance(event, PrivateMessageEvent):
            await matcher.finish(result)
        else:
            await matcher.finish("\n" + result, at_sender=True)
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
            if isinstance(event, PrivateMessageEvent):
                await matcher.finish(result)
            else:
                await matcher.finish("\n" + result, at_sender=True)
        else:
            # 如果是今天的数据则返回今天的数据
            r = str(member_model.luckid)
            result = f"----\n{luckdata[r]['运势']}\n{luckdata[r]['星级']}\n{luckdata[r]['签文']}\n{luckdata[r]['解签']}\n----"
            if isinstance(event, PrivateMessageEvent):
                await matcher.finish(result)
            else:
                await matcher.finish("\n" + result, at_sender=True)


def randomluck(arg, memberdata):
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
    result = f"----\n{luckdata[r]['运势']}\n{luckdata[r]['星级']}\n{luckdata[r]['签文']}\n{luckdata[r]['解签']}\n----"
    return result, r
