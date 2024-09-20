import asyncio
import datetime
import os
import random
import re
import time

import aiofiles
import nonebot
import ujson
from nonebot import logger, on_command, on_message
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent
from nonebot.adapters.onebot.v11.helpers import (
    Cooldown,
    CooldownIsolateLevel,
)
from nonebot.permission import SUPERUSER
from nonebot.rule import Rule, to_me

from .config import ai_config
from .ofa_image_process import ImageCaptioningPipeline
from .utils import chat_with_gpt, is_image_message, is_reply_image_message

config = nonebot.get_driver().config

datadir = ai_config.data_dir
os.makedirs(datadir, exist_ok=True)
truncate_probs = [0.1, 0.1]
MAX_LEN = 12
bracket_probs = [0.45, 0.4]


def is_record(event: GroupMessageEvent) -> bool:
    message = str(event.get_message())
    if event.reply:
        message += str(event.reply)
    return (
        event.group_id in ai_config.record_group
        and "[CQ:video" not in message
        and not event.to_me
        and not message.startswith("clean.session")
    )


def is_use(event: GroupMessageEvent) -> bool:
    message = str(event.get_message())
    return event.group_id in ai_config.record_group and "[CQ:video" not in message


async def load_or_init_data(group_id: str) -> dict:
    file_path = os.path.join(datadir, f"{group_id}.json")
    if not os.path.exists(file_path):
        async with aiofiles.open(file_path, "w") as f:
            await f.write(
                ujson.dumps(
                    {
                        "keep_prompt": [],
                        "record": [],
                    },
                    ensure_ascii=False,
                )
            )

    async with aiofiles.open(file_path) as f:
        data = ujson.loads(await f.read())
    if group_id in {"475214083", "966016220"}:
        data["keep_prompt"] = [
            {"role": "system", "content": ai_config.prompt2},
            {"role": "assistant", "content": "好的！我会记住的~"},
            *ai_config.msglist_baiye,
        ]
    else:
        data["keep_prompt"] = [
            {"role": "system", "content": ai_config.prompt},
            {"role": "assistant", "content": "好的！我会记住的~"},
        ]
    return data


async def save_data(group_id: str, data: dict) -> None:
    file_path = os.path.join(datadir, f"{group_id}.json")
    async with aiofiles.open(file_path, "w") as f:
        await f.write(ujson.dumps(data, indent=4, ensure_ascii=False))


def format_time(event_time: int) -> str:
    return (
        f"[{datetime.datetime.fromtimestamp(event_time).strftime('%Y-%m-%d %H:%M:%S')}]"
    )


async def create_process_text(
    event: GroupMessageEvent, text: str, time_now: str
) -> str:
    nickname = event.sender.nickname
    user_id = event.get_user_id()
    is_image, image_url = is_image_message(True, event)
    if is_image and ai_config.enable_ofa_image:
        caption: str = await image_captioning_pipeline.generate_caption(image_url)
        # 去除cq码，一个个解析文字[开始]结束的内容全部去掉替换为图片：[图片{caption}]
        for cq in re.findall(r"\[CQ:.*?\]", text):
            text = text.replace(cq, f"[图片,描述:{caption}]")
    if event.reply:
        is_image_reply, image_url_reply = is_reply_image_message(True, event.reply)
        reply_user_id = event.reply.sender.user_id
        reply_nickname = event.reply.sender.nickname
        reply_text = str(event.reply.message).strip()
        if is_image_reply:
            if ai_config.enable_ofa_image:
                caption = await image_captioning_pipeline.generate_caption(
                    image_url_reply
                )
            else:
                caption = "无描述"
            for cq in re.findall(r"\[CQ:.*?\]", reply_text):
                reply_text = reply_text.replace(cq, f"[图片,描述:{caption}]")
        return f"{time_now}，{nickname}({user_id}) 引用并回复了 {reply_nickname}({reply_user_id}) 的消息：\n引用内容：“{reply_text}”\n回复内容：“{text}”"
    return f"{time_now} {nickname}({user_id}): {text}"


record_msg = on_message(rule=is_record)
handle_command = on_message(rule=is_use & to_me())
clean_command = on_command("clean.session", permission=SUPERUSER)


@clean_command.handle()
async def _(event: GroupMessageEvent) -> None:
    group_id = str(event.group_id)
    file_path = os.path.join(datadir, f"{group_id}.json")
    if os.path.exists(file_path):
        os.remove(file_path)
        await clean_command.finish("脑袋空空！")
    await clean_command.finish("欸，我不记得有和你们聊过天啊?")


def add_element(my_list: list, keep_num=50) -> list:
    return my_list[-keep_num:]


def split_sentences(reply: str) -> list[str]:
    # 去掉头尾的标点符号并分割句子
    reply = reply.strip("”“’‘\"'!！。.?？~")
    sentences = re.split("[，。]", reply)

    # 根据概率删减句子，优化后移除循环中多余的异常处理
    for prob in truncate_probs:
        if len(sentences) > 1 and random.random() < prob:
            sentences.pop()

    # 根据概率添加括号
    if sentences:
        rand = random.random()
        if rand < bracket_probs[0]:
            sentences[-1] += "（）"
        elif rand < bracket_probs[0] + bracket_probs[1]:
            sentences[-1] += "（"

    # 限制输出的句子数量
    return sentences[:MAX_LEN]


def get_type_time(string) -> float:
    """
    打字时间模拟
    """
    tpc = 0.55  # 每个字符打字时间
    return tpc * len(string)


async def send_with_dynamic_wait(sentence: str, reply_message=True):
    # 动态计算等待时间，假设每个字符等待 0.05 秒
    tying_time = get_type_time(sentence)
    await asyncio.sleep(tying_time)
    await handle_command.send(sentence, reply_message=reply_message)


@handle_command.handle(
    parameterless=[
        Cooldown(
            cooldown=2,
            prompt="太快了...",
            isolate_level=CooldownIsolateLevel.USER,
        )
    ]
)
async def _(event: GroupMessageEvent):
    time_question = time.time()
    group_id = str(event.group_id)

    text = str(event.get_message()).strip()
    if not text:
        await handle_command.finish("讲话啊喂！")

    data = await load_or_init_data(group_id)
    keep_prompt: list = data.get("keep_prompt", [])

    # 通过api获取50条记录
    record: list = data.get("record", [])

    # 检查最近十条对话中是否含有和本次对话 role 和 content 一样的情况
    last_ten = record[-10:]
    if any(i["role"] == "user" and text in i["content"] for i in last_ten):
        await handle_command.finish("这个刚刚说过了吧......", reply_message=True)

    time_now = format_time(event.time)
    process_text = await create_process_text(event, text, time_now)
    record.append({"role": "user", "content": process_text})
    response = await chat_with_gpt(keep_prompt + record, ai_config)
    record.append({"role": "assistant", "content": response})

    # 保持记录在50条以内
    record = add_element(record, 50)

    # 保存记录
    data["record"] = record
    await save_data(group_id, data)
    if ai_config.sentences_divide:
        response = split_sentences(response)
        print(response)
        time_get_answer: float = time.time()
        if time_get_answer - time_question <= get_type_time(response[0]) + 1:
            # 否则按照打字时间延迟发送
            await asyncio.sleep(
                get_type_time(response[0]) + 1 - (time_get_answer - time_question)
            )
        await handle_command.send(response[0], reply_message=True)
        for sentence in response[1:]:
            await send_with_dynamic_wait(sentence)
    else:
        await send_with_dynamic_wait(response)


image_captioning_pipeline = ImageCaptioningPipeline()


@record_msg.handle()
async def _(event: GroupMessageEvent):
    group_id = str(event.group_id)

    data = await load_or_init_data(group_id)
    record: list = data.get("record", [])

    text = str(event.get_message()).strip()
    time_now = format_time(event.time)
    process_text = await create_process_text(event, text, time_now)
    record.append({"role": "user", "content": "聊天记录: \n" + process_text})

    # 保持记录在50条以内
    record = add_element(record, 50)

    data["record"] = record
    await save_data(group_id, data)


async def get_history(
    bot: Bot, group_id: str, cout: int = 50
) -> list[GroupMessageEvent]:
    data: list[GroupMessageEvent] = await bot.call_api(
        "get_group_msg_history", group_id=group_id, count=cout
    )
    return data
