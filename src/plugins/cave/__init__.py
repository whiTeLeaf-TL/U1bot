import random
import re
import base64
import requests
from nonebot import get_driver, logger, on_command
from nonebot.adapters.onebot.v11 import Message, Bot, GroupMessageEvent, PrivateMessageEvent, MessageEvent
from nonebot.plugin import PluginMetadata
from nonebot.matcher import Matcher
from nonebot.params import CommandArg
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
    response = requests.get(image_url, timeout=5)
    image_data = response.content
    return base64.b64encode(image_data).decode("utf-8")


def process_message(original_message):
    if url_match := re.search(
        r"\[CQ:image,file=\w+\.image,url=([^\]]+)\]", original_message
    ):
        image_url = url_match[1]

        # 将图片URL转换为Base64
        base64_image = url_to_base64(image_url)

        return re.sub(
            r"\[CQ:image,file=\w+\.image,url=([^\]]+)\]",
            f"[CQ:image,file=base64://{base64_image}]",
            original_message,
        )
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
    else:
        await matcher.finish("你不是投稿人，也不是作者的，你想干咩？")
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
    msg_list = [
        "回声洞记录如下：",
        *[
            f"----------------------\n编号：{i.id}\n----------------------\n内容：\n{i.details}\n----------------------\n投稿时间：{i.time}\n----------------------"
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

    参数:
        bot (Bot): 机器人实例
        event (MessageEvent): 消息事件
        name (str): 转发消息的名称
        uin (str): 转发消息的 UIN
        msgs (list): 转发的消息列表

    返回:
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
    从文本中提取删除原因。

    Args:
        text (str): 包含删除原因的文本。

    Returns:
        list: 包含删除原因的字典列表，每个字典包含序号和原因。

    Example:
        >>> text = "删除1原因1\n删除2原因2\n删除3"
        >>> extract_deletion_reason(text)
        [{'序号': 1, '原因': '原因1'}, {'序号': 2, '原因': '原因2'}, {'序号': 3, '原因': '作者删除'}]
    """
    pattern = r"删除(\d+)(.*?)$"
    matches = re.findall(pattern, text, re.MULTILINE)
    results = []
    for match in matches:
        if match[1].strip():
            results.append({"序号": int(match[0]), "原因": match[1].strip()})
        else:
            results.append({"序号": int(match[0]), "原因": "作者删除"})

    return results
