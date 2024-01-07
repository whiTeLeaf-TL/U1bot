import random
import re
import json
import base64
from datetime import datetime
from nonebot import logger
import requests
from nonebot.adapters.onebot.v11 import (
    Message,
    Bot,
    GroupMessageEvent,
    PrivateMessageEvent,
    MessageEvent,
)
from nonebot import on_command, get_driver
from nonebot.plugin import PluginMetadata
from nonebot.matcher import Matcher
from nonebot.params import RegexGroup, CommandArg
from .models import cave_models

SUPERUSER = list(get_driver().config.superusers)

Bot_NICKNAME = list(get_driver().config.nickname)
Bot_NICKNAME = Bot_NICKNAME[0] if Bot_NICKNAME else "bot"
__plugin_meta__ = PluginMetadata(
    name="回声洞",
    description="看看别人的投稿，也可以自己投稿~",
    usage="""投稿\n
查看回声洞记录\n
删除[序号]\n
如：\n
投稿""",
)


cave_main = on_command("回声洞")
cave_add = on_command("投稿", aliases={"回声洞投稿"})
cave_history = on_command("查看回声洞记录", aliases={"回声洞记录"})
cave_view = on_command("查看")
cave_del = on_command("删除")


def url_to_base64(image_url):
    response = requests.get(image_url)
    image_data = response.content
    base64_data = base64.b64encode(image_data).decode("utf-8")
    return base64_data


def process_message(original_message):
    # 使用正则表达式提取图片URL
    url_match = re.search(
        r"\[CQ:image,file=\w+\.image,url=([^\]]+)\]", original_message
    )

    if url_match:
        image_url = url_match.group(1)

        # 将图片URL转换为Base64
        base64_image = url_to_base64(image_url)

        # 构建新的消息
        new_message = re.sub(
            r"\[CQ:image,file=\w+\.image,url=([^\]]+)\]",
            f"[CQ:image,file=base64://{base64_image}]",
            original_message,
        )

        return new_message
    else:
        return original_message


@cave_add.handle()
async def _(matcher: Matcher, event: MessageEvent, args: Message = CommandArg()):
    key = str(args).strip()
    # 仅私聊
    if not isinstance(event, PrivateMessageEvent):
        await matcher.finish("别搞啊，只能私聊我才能投稿啊！")
    if not key:
        await matcher.finish("不输入内容，小子你是想让我投稿什么？空气咩？")

    caves = await cave_models.create(
        details=process_message(key), user_id=event.user_id
    )
    await matcher.send("投稿成功！")
    await matcher.finish(
        Message(
            f"预览：\n编号：{caves.id}\n----------------------\n内容：\n{caves.details}\n----------------------\n投稿时间：{caves.time}\n----------------------"
        )
    )


@cave_del.handle()
async def _(bot: Bot, matcher: Matcher, event: MessageEvent):
    Message_text = str(event.message)
    deletion_reasons = extract_deletion_reason(Message_text)[0]
    key = deletion_reasons["序号"]
    # 如果有原因获取，没有为none
    reason = deletion_reasons["原因"]
    try:
        key = int(key)
    except ValueError:
        await matcher.finish("请输入正确的序号")
    try:
        data = await cave_models.get(id=key)
    except Exception:
        await matcher.finish("没有这个序号的投稿")
    # 判断是否是超级用户或者是投稿人
    if str(event.user_id) in SUPERUSER:
        try:
            await bot.send_private_msg(
                user_id=data.user_id,
                message=Message(
                    f"你的投稿{key}已经被{event.user_id}删除了！\n内容为：\n{data.details}\n原因：{reason}"
                ),
            )
        except Exception:
            logger.error(f"回声洞删除投稿私聊通知失败，投稿人id：{data.user_id}")
    elif event.user_id == data.user_id:
        await data.delete()
        await data.save()
        await matcher.finish(f"删除成功！编号{key}的投稿已经被删除！\n内容为：\n{data.details}")
    elif event.user_id != data.user_id:
        await matcher.finish("你不是投稿人，也不是作者的，你想干咩？")
    else:
        await matcher.finish("你是谁？")
    result = data.details
    await data.delete()
    await data.save()
    await matcher.finish(f"删除成功！编号{key}的投稿已经被删除！\n内容为：\n{result}\n原因：{reason}")


@cave_main.handle()
async def _(matcher: Matcher):
    all_caves = await cave_models.all()
    random_cave = random.choice(all_caves)
    result = f"编号:{random_cave.id}\n"
    result += "----------------------\n"
    result += f"内容：\n{random_cave.details}\n"
    result += "----------------------\n"
    result += f"投稿人：{random_cave.user_id}\n"
    result += f"投稿时间：{random_cave.time}\n"
    result += "----------------------\n"
    result += "可以私聊我投稿内容啊！\n投稿[内容]（支持图片，文字）"
    await matcher.finish(Message(result))


@cave_view.handle()
async def _(matcher: Matcher, args: Message = CommandArg()):
    key = str(args).strip()
    if not key:
        await matcher.finish("请输入编号")
    try:
        cave = await cave_models.get(id=int(key))
    except Exception as e:
        logger.error(e)
        await matcher.finish("编号错误")
    result = f"编号:{cave.id}\n"
    result += "----------------------\n"
    result += f"内容：\n{cave.details}\n"
    result += "----------------------\n"
    result += f"投稿人：{cave.user_id}\n"
    result += f"投稿时间：{cave.time}\n"
    result += "----------------------\n"
    result += "可以私聊我投稿内容啊！\n投稿[内容]（支持图片，文字）"
    await matcher.finish(Message(result))


@cave_history.handle()
async def _(bot: Bot, event: MessageEvent):
    # 查询userid写所有数据
    all_caves = await cave_models.all()
    msg_list = ["回声洞记录如下："]
    msg_list.extend(
        Message(
            f"----------------------\n编号：{i.id}\n内容：\n{i.details}\n投稿时间：{i.time}\n----------------------"
        )
        for i in all_caves
        if i.user_id == event.user_id
    )
    await send_forward_msg(bot, event, Bot_NICKNAME, bot.self_id, msg_list)


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
    results = []
    for match in matches:
        # 如果原因部分是空的或者只包含空格，可以忽略该原因
        if match[1].strip():
            results.append({"序号": int(match[0]), "原因": match[1].strip()})
        else:
            results.append({"序号": int(match[0]), "原因": "作者删除"})

    return results
