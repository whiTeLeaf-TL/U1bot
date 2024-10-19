import base64
import random
import re

import requests
from nonebot import get_driver, logger, on_command, on_fullmatch
from nonebot.adapters.onebot.v11 import (
    Bot,
    GroupMessageEvent,
    Message,
    MessageEvent,
    PrivateMessageEvent,
)
from nonebot.adapters.onebot.v11.helpers import extract_image_urls
from nonebot.params import CommandArg
from nonebot.permission import SUPERUSER
from nonebot.plugin import PluginMetadata
from .models import cave_models

Bot_NICKNAME = list(get_driver().config.nickname)
Bot_NICKNAME = Bot_NICKNAME[0] if Bot_NICKNAME else "bot"
__plugin_meta__ = PluginMetadata(
    name="回声洞",
    description="看看别人的投稿，也可以自己投稿~",
    usage="""投稿\n
查看回声洞记录\n
删除 [序号]\n
如：\n
投稿""",
)


cave_main = on_fullmatch("回声洞", block=True)
cave_add = on_command("投稿", aliases={"回声洞投稿"}, block=True)
cave_am_add = on_command("匿名投稿", aliases={"回声洞匿名投稿"}, block=True)
cave_history = on_command("查看回声洞记录", aliases={"回声洞记录"}, block=True)
cave_view = on_command("查看", block=True)
cave_del = on_command("删除", block=True)

cave_update = on_command("更新回声洞", permission=SUPERUSER, block=True)
SUPERUSER_list = list(get_driver().config.superusers)


@cave_update.handle()
async def _():
    "操作数据库，将id重新排列，并且自动id更新到最新"
    all_caves = await cave_models.all()

    # 遍历所有对象，逐个删除并重新创建
    for index, cave in enumerate(all_caves, start=1):
        details = cave.details
        user_id = cave.user_id
        time = cave.time
        anonymous = cave.anonymous
        await cave.delete()  # 删除原对象
        await cave.save()
        await cave_models.create(
            id=index, details=details, user_id=user_id, time=time, anonymous=anonymous
        )

    await cave_update.finish("更新成功！")


def url_to_base64(image_url):
    response = requests.get(image_url, timeout=5)
    image_data = response.content
    return base64.b64encode(image_data).decode("utf-8")


def process_message(original_message):
    if url_match := re.search(
        r"\[CQ:image,file=\w+\.image,url=([^\]]+)\]", original_message
    ):
        image_url = url_match[1]

        # 将图片 URL 转换为 Base64
        base64_image = url_to_base64(image_url)

        return re.sub(
            r"\[CQ:image,file=\w+\.image,url=([^\]]+)\]",
            f"[CQ:image,file=base64://{base64_image}]",
            original_message,
        )
    return original_message


@cave_add.handle()
async def _(event: MessageEvent, args: Message = CommandArg()):
    key = str(args).strip()
    # 仅私聊
    urllist = extract_image_urls(event.get_message())
    if len(urllist) > 1:
        await cave_add.finish("只能投一张图哦")
    if not isinstance(event, PrivateMessageEvent):
        await cave_add.finish("别搞啊，只能私聊我才能投稿啊！")
    if not key:
        await cave_add.finish("不输入内容，小子你是想让我投稿什么？空气咩？")

    caves = await cave_models.create(
        details=process_message(key), user_id=event.user_id
    )
    await cave_add.send("投稿成功！")
    await cave_add.finish(
        Message(
            f"预览：\n编号：{caves.id}\n----------------------\n内容：\n{caves.details}\n----------------------\n投稿时间：{caves.time.strftime('%Y-%m-%d %H:%M:%S')}\n----------------------"
        )
    )


@cave_am_add.handle()
async def _(event: MessageEvent, args: Message = CommandArg()):
    "匿名发布回声洞"
    key = str(args).strip()
    # 仅私聊
    urllist = extract_image_urls(event.get_message())
    if len(urllist) > 1:
        await cave_add.finish("只能投一张图哦")
    if not isinstance(event, PrivateMessageEvent):
        await cave_add.finish("别搞啊，只能私聊我才能投稿啊！")
    if not key:
        await cave_add.finish("不输入内容，小子你是想让我投稿什么？空气咩？")

    caves = await cave_models.create(
        details=process_message(key), user_id=event.user_id, anonymous=True
    )
    await cave_add.send("匿名投稿成功！")
    await cave_add.finish(
        Message(
            f"预览：\n编号：{caves.id}\n----------------------\n内容：\n{caves.details}\n----------------------\n投稿时间：{caves.time.strftime('%Y-%m-%d %H:%M:%S')}\n----------------------\n匿名投稿将会保存用户信息\n但其他用户无法看到作者"
        )
    )


@cave_del.handle()
async def _(bot: Bot, event: MessageEvent):
    Message_text = str(event.message)
    deletion_reasons = extract_deletion_reason(Message_text)
    key = deletion_reasons["序号"]
    # 如果有原因获取，没有为 none
    reason = deletion_reasons["原因"]
    try:
        key = int(key)
    except ValueError:
        await cave_del.finish("请输入正确的序号")
    try:
        data = await cave_models.get(id=key)
    except Exception:
        await cave_del.finish("没有这个序号的投稿")
    # 判断是否是超级用户或者是投稿人
    if str(event.user_id) in SUPERUSER_list:
        try:
            await bot.send_private_msg(
                user_id=data.user_id,
                message=Message(
                    f"你的投稿{key}已经被{event.user_id}删除了！\n内容为：\n{data.details}\n原因：{reason}"
                ),
            )
        except Exception:
            logger.error(f"回声洞删除投稿私聊通知失败，投稿人 id：{data.user_id}")
    elif event.user_id == data.user_id:
        await data.delete()
        await data.save()
        await cave_del.finish(
            Message(f"删除成功！编号{key}的投稿已经被删除！\n内容为：\n{data.details}")
        )
    else:
        await cave_del.finish("你不是投稿人，也不是作者的，你想干咩？")
    result = data.details
    await data.delete()
    await data.save()
    await cave_del.finish(
        Message(
            f"删除成功！编号{key}的投稿已经被删除！\n内容为：\n{result}\n原因：{reason}"
        )
    )


@cave_main.handle()
async def _():
    all_caves = await cave_models.all()
    random_cave = random.choice(all_caves)
    displayname = "***（匿名投稿）" if random_cave.anonymous else random_cave.user_id
    result = f"编号:{random_cave.id}\n"
    result += "----------------------\n"
    result += f"内容：\n{random_cave.details}\n"
    result += "----------------------\n"
    result += f"投稿人：{displayname}\n"
    result += f"投稿时间：{random_cave.time.strftime('%Y-%m-%d %H:%M:%S')}\n"
    result += "----------------------\n"
    result += "可以私聊我投稿内容啊！\n投稿 [内容]（支持图片，文字）\n匿名投稿 [内容]（支持图片，文字）"
    await cave_main.finish(Message(result))


@cave_view.handle()
async def _(args: Message = CommandArg()):
    key = str(args).strip()
    if not key:
        await cave_view.finish("请输入编号")
    try:
        cave = await cave_models.get(id=int(key))
    except Exception as e:
        logger.error(e)
        await cave_view.finish("编号错误")
    # 判断是否是匿名
    displayname = "***（匿名投稿）" if cave.anonymous else cave.user_id
    result = f"编号:{cave.id}\n"
    result += "----------------------\n"
    result += f"内容：\n{cave.details}\n"
    result += "----------------------\n"
    result += f"投稿人：{displayname}\n"
    result += f"投稿时间：{cave.time.strftime('%Y-%m-%d %H:%M:%S')}\n"
    result += "----------------------\n"
    result += "可以私聊我投稿内容啊！\n投稿 [内容]（支持图片，文字）\n匿名投稿 [内容]（支持图片，文字）"
    await cave_view.finish(Message(result))


@cave_history.handle()
async def _(bot: Bot, event: MessageEvent):
    # 查询 userid 写所有数据
    all_caves = await cave_models.all()
    msg_list = [
        "回声洞记录如下：",
        *[
            Message(
                f"----------------------\n编号：{i.id}\n----------------------\n内容：\n{i.details}\n----------------------\n投稿时间：{i.time.strftime('%Y-%m-%d %H:%M:%S')}\n----------------------"
            )
            for i in all_caves
            if i.user_id == event.user_id
        ],
    ]
    await send_forward_msg(bot, event, Bot_NICKNAME, bot.self_id, msg_list)


async def send_forward_msg(
    bot: Bot,
    event: MessageEvent,
    name: str,
    uin: str,
    msgs: list,
) -> dict:
    """
    发送转发消息的异步函数。

    参数：
        bot (Bot): 机器人实例
        event (MessageEvent): 消息事件
        name (str): 转发消息的名称
        uin (str): 转发消息的 UIN
        msgs (list): 转发的消息列表

    返回：
        dict: API 调用结果
    """

    def to_json(msg: Message):
        return {"type": "node", "data": {"name": name, "uin": uin, "content": msg}}

    messages = [to_json(msg) for msg in msgs]
    if isinstance(event, GroupMessageEvent):
        return await bot.call_api(
            "send_group_forward_msg", group_id=event.group_id, messages=messages
        )
    return await bot.call_api(
        "send_private_forward_msg", user_id=event.user_id, messages=messages
    )


def extract_deletion_reason(text):
    """
    从文本中提取删除原因，处理“删除1”或“删除 1 原因1”等格式。

    Args:
        text (str): 包含删除原因的文本。

    Returns:
        dict: 包含删除原因的字典，包含序号和原因。

    Example:
        >>> text = "删除1 原因1"
        >>> extract_deletion_reason(text)
        {'序号': 1, '原因': '原因1'}
    """
    # 移除 "删除" 关键字以及多余的空格
    cleaned_text = text.replace("删除", "", 1).strip()

    # 分离序号和原因
    num = ""
    reason = ""

    # 通过第一个非数字字符来划分序号和原因
    for idx, char in enumerate(cleaned_text):
        if char.isdigit():
            num += char
        else:
            # 当遇到第一个非数字字符时，余下部分全是原因
            reason = cleaned_text[idx:].strip()
            break

    # 若没有原因，则设为默认值 "作者删除"
    if not reason:
        reason = "作者删除"

    return {"序号": int(num), "原因": reason}
