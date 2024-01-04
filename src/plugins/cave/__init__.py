from nonebot import on_command, get_driver, on_regex, logger
from pathlib import Path
from nonebot.plugin import PluginMetadata
from nonebot.matcher import Matcher
import re

SUPERUSER = list(get_driver().config.superusers)

import random
import time
from nonebot.adapters.onebot.v11 import (
    MessageEvent,
    Bot,
    Message,
    GroupMessageEvent,
    PrivateMessageEvent,
)
from typing import Tuple
from nonebot.params import RegexGroup, CommandArg

__plugin_meta__ = PluginMetadata(
    name="回声洞",
    description="看看别人的投稿，也可以自己投稿~",
    usage="""投稿\n
查看回声洞记录\n
删除[序号]\n
如：\n
投稿""",
    extra={
        "menu_data": [
            {
                "func": "投稿",
                "trigger_method": "投稿/回声洞投稿",
                "trigger_condition": "仅私聊",
                "brief_des": "投稿到回声洞",
                "detail_des": "投稿\n" "将内容投稿到回声洞\n" "仅限私聊\n" "例如：\n" "投稿 内容",
            },
            {
                "func": "查看回声洞记录",
                "trigger_method": "查看回声洞记录/回声洞记录",
                "trigger_condition": "群聊/私聊",
                "brief_des": "查看回声洞的投稿记录（合并信息）",
                "detail_des": "例如\n" "查看回声洞记录\n" "回声洞记录\n" "他是合并信息，不怕刷屏咯",
            },
            {
                "func": "删除投稿",
                "trigger_method": "删除[序号]",
                "trigger_condition": "群聊/私聊",
                "brief_des": "删除指定序号的投稿（仅限自己的投稿）",
                "detail_des": "删除[序号]\n" "删除回声洞中指定序号的投稿\n" "群聊或私聊\n" "例如：\n" "删除1",
            },
        ],
        "menu_template": "default",
    },
)

try:
    import ujson as json
except Exception:
    import json

Bot_NICKNAME = list(get_driver().config.nickname)
Bot_NICKNAME = Bot_NICKNAME[0] if Bot_NICKNAME else "bot"

cavemain = on_command("回声洞")
cavehistory = on_command("查看回声洞记录", aliases={"回声洞记录"})
# 仅私聊,关于投稿+内容的,内容只能在投稿后面,可能有空格
caveadd = on_command("投稿", aliases={"回声洞投稿"})
cavedel = on_command("删除", priority=1)
# 查看特定序号的投稿
caveview = on_command(r"查看", priority=1)

datapath = Path.cwd().joinpath("data/cave/data.json")
if not datapath.exists():
    datapath.parent.mkdir(parents=True, exist_ok=True)
    with open(datapath, "w", encoding="utf-8") as f:
        json.dump({}, f, indent=4, ensure_ascii=False)


@caveview.handle()
async def _(matcher: Matcher, args: Message = CommandArg()):
    key = str(args).strip()
    with open(datapath, "r", encoding="utf-8") as f:
        data = json.load(f)
    if str(key) not in data:
        await matcher.finish("没有这个序号的投稿")
    result = f"编号:{key}\n"
    result += "----------------------\n"
    result += f"内容：\n{data[key]['内容']}\n"
    result += "----------------------\n"
    result += f"投稿人：{data[key]['投稿人']}\n"
    result += f"投稿时间：{data[key]['投稿时间']}\n"
    result += "----------------------\n"
    result += "可以私聊我投稿内容啊！\n投稿[内容]（支持图片，文字）"
    await matcher.finish(Message(result))


@cavedel.handle()
async def _(
    bot: Bot,
    matcher: Matcher,
    event: MessageEvent,
):
    Message_text = str(event.message)
    deletion_reasons = extract_deletion_reason(Message_text)[0]
    key = deletion_reasons["序号"]
    # 如果有原因获取，没有为none
    reason = deletion_reasons["原因"]
    try:
        key = int(key)
    except Exception:
        await matcher.finish("请输入正确的序号")
    with open(datapath, "r", encoding="utf-8") as f:
        data = json.load(f)
    if str(key) not in data:
        await matcher.finish("没有这个序号的投稿")
    result = data[str(key)]
    # 判断是否是超级用户或者是投稿人
    if str(event.user_id) in SUPERUSER:
        try:
            await bot.send_private_msg(
                user_id=int(data[str(key)]["投稿人"]),
                message=f"你的投稿{key}已经被{event.user_id}删除了！\n内容为：\n{data[str(key)]['内容']}\n原因：{reason}",
            )
        except Exception:
            logger.error(f"回声洞删除投稿私聊通知失败，投稿人id：{data[str(key)]['投稿人']}")
    elif event.user_id == int(data[str(key)]["投稿人"]):
        del data[str(key)]
    elif event.user_id != int(data[str(key)]["投稿人"]):
        await matcher.finish("你不是投稿人，也不是作者的，你想干咩？")
    else:
        await matcher.finish("你是谁？")
    result = (data[str(key)]["内容"],)
    del data[str(key)]
    with open(datapath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    await matcher.finish(f"删除成功！编号{key}的投稿已经被删除！\n内容为：\n{result}\n原因：{reason}")


@caveadd.handle()
async def _(matcher: Matcher, event: MessageEvent, args: Message = CommandArg()):
    key = str(args).strip()
    # 仅私聊
    if not isinstance(event, PrivateMessageEvent):
        await matcher.finish("别搞啊，只能私聊我才能投稿啊！")
    if not key:
        await matcher.finish("不输入内容，小子你是想让我投稿什么？空气咩？")
    with open(datapath, "r", encoding="utf-8") as f:
        data = json.load(f)
    # 读取json文件，获取用户的投稿记录
    """
    结构
    {
        "id":{
            "内容":"内容",
            "投稿人":"投稿人id",
            "投稿时间":"投稿时间"
        }
    }
    """
    # id为最后一个数字的+1
    id = str(int(list(data.keys())[-1]) + 1)
    data[id] = {"内容": key}
    data[id]["投稿人"] = str(event.user_id)
    data[id]["投稿时间"] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
    with open(datapath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    await matcher.send("投稿成功！")
    await matcher.finish(
        Message(
            f'预览：\n编号：{id}\n----------------------\n内容：\n{key}\n----------------------\n投稿时间：{data[id]["投稿时间"]}\n----------------------'
        )
    )


@cavehistory.handle()
async def _(bot: Bot, event: MessageEvent):
    with open(datapath, "r", encoding="utf-8") as f:
        data = json.load(f)

    msg_list = ["回声洞记录如下："]
    msg_list.extend(
        Message(
            f"----------------------\n编号：{i}\n内容：\n{data[i]['内容']}\n投稿时间：{data[i]['投稿时间']}\n----------------------"
        )
        for i in list(data.keys())
        if data[i]["投稿人"] == str(event.user_id)
    )
    await send_forward_msg(bot, event, Bot_NICKNAME, bot.self_id, msg_list)


@cavemain.handle()
async def _(matcher: Matcher):
    # 读取json文件
    # 随机获取回声洞
    with open(datapath, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not list(data.keys()):
        await matcher.finish("回声洞里面空空如也，快来投稿吧！\n投稿[内容]（支持图片，文字）")
    r = random.choice(list(data.keys()))
    result = f"编号:{r}\n"
    result += "----------------------\n"
    result += f"内容：\n{data[r]['内容']}\n"
    result += "----------------------\n"
    result += f"投稿人：{data[r]['投稿人']}\n"
    result += f"投稿时间：{data[r]['投稿时间']}\n"
    result += "----------------------\n"
    result += "可以私聊我投稿内容啊！\n投稿[内容]（支持图片，文字）"
    await matcher.finish(Message(result))


async def send_forward_msg(
    bot: Bot,
    event: MessageEvent,
    name: str,
    uin: str,
    msgs: list,
) -> dict:
    def to_json(msg: Message):
        return {"type": "node", "data": {"name": name, "uin": uin, "content": msg}}

    messages = [to_json(msg) for msg in msgs]
    if isinstance(event, GroupMessageEvent):
        return await bot.call_api(
            "send_group_forward_msg", group_id=event.group_id, messages=messages
        )
    else:
        return await bot.call_api(
            "send_private_forward_msg", user_id=event.user_id, messages=messages
        )


def extract_deletion_reason(text):
    # 正则表达式模式，匹配"删除"后面的内容
    pattern = r"删除(\d+)(.*?)$"
    matches = re.findall(pattern, text, re.MULTILINE)
    logger.debug(f"matches: {matches}")
    results = []
    for match in matches:
        # 如果原因部分是空的或者只包含空格，可以忽略该原因
        if match[1].strip():
            results.append({"序号": int(match[0]), "原因": match[1].strip()})
        else:
            results.append({"序号": int(match[0]), "原因": "作者删除"})

    return results
