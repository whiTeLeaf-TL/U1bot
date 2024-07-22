"""这是一个今日运势插件，可以查看今日运势。"""

import random
import time
from datetime import datetime
from os import path
from pathlib import Path

import ujson as json
from nonebot import on_command
from nonebot.adapters.onebot.v11 import (
    MessageEvent,
    PrivateMessageEvent,
    GroupMessageEvent,
)
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
    member_model = await MemberData.get_or_none(user_id=str(event.user_id))

    if member_model is None:
        # 如果没有数据则创建数据
        result, luckid = randomluck(str(event.user_id), {})
        await MemberData.create(
            user_id=str(event.user_id), luckid=luckid, time=datetime.now()
        )
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
    if datetime.now().strftime("%m-%d") == "07-22" and event.user_id in [
        869379440,
        3347436696,
    ]:
        if isinstance(event, PrivateMessageEvent) or (
            isinstance(event, GroupMessageEvent) and event.group_id == 475214083
        ):
            result = (
                "----\n凶吗？其实是 大吉 + 官运 + 财运 + 才艺 + 人缘 + 健康 的 Plus Pro Super UItral Lucky ++版\n★★★★★★★★★★★★★★★★★★★★\n"
                "如龙得云，青云直上，智谋奋进，才略奏功\n你的期望高远，愿望强烈且容易实现。智谋出众，财力雄厚，但需注意克制猜疑和嫉妒之心。你像龙乘云一样迅速崛起，凭借智慧和勇气达成大志，获得无比的富贵。然而，需警惕牢骚和贪心过盛，避免过度的欲望和沉迷于投机行为，以免影响前程。祝你20岁生日快乐，风林！愿你的青春岁月充满激情与梦想，不错过任何美好的瞬间，前程似锦。\n呐，我不可能就那么提前敷衍一下生日快乐就睡觉的，毕竟你是我非常重要的朋友。就算凌晨再多人给你祝福，那我也得凑数！因为今天可是你的生日啊喂。\n晚安喔，你也不要忘记早点睡觉，好好休息才能保持健康和精力，迎接每一个美好的明天。\n----\n内幕：\n* ling 现在确实已经睡了，因为这明明是提前准备好的，但他刚刚起床上厕所才发现你居然会去主群发，所以在主群撤回了运势请不要介意，起床临时改了代码，在 TL 群发了运势就开了免打扰睡觉了。\n欸，因为面对给你的这个信息会让 ling 很尴尬（\n----"
            )
            if event.user_id == 3347436696:
                result += "\n啊哈我就知道，细心boy不会错过这个号的。"
        if isinstance(event, GroupMessageEvent) and event.group_id == 713478803:
            result = "显示错误，请在别的群再试试，如结果还如此请上报给作者。"
    await matcher.finish(result, reply_message=True)


def randomluck(arg, memberdata):
    """
    随机获取运势信息。

    Args:
        arg (str): 参数。
        memberdata (dict): 成员数据。

    Returns:
        tuple: 运势信息和选择的运势编号。
    """
    # 判断是否有在 json 文件中和是否有 time 键值
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
