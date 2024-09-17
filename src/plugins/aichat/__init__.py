import datetime
import os

import aiofiles
import nonebot
import ujson
from nonebot import on_command, on_message
from nonebot.adapters.onebot.v11 import GroupMessageEvent
from nonebot.adapters.onebot.v11.helpers import (
    Cooldown,
    CooldownIsolateLevel,
)
from nonebot.permission import SUPERUSER

from .config import ai_config
from .utils import chat_with_gpt

config = nonebot.get_driver().config

datadir = ai_config.data_dir
os.makedirs(datadir, exist_ok=True)


def is_record(event: GroupMessageEvent) -> bool:
    message = str(event.get_message())
    if event.reply:
        message += str(event.reply)
    return (
        event.group_id in ai_config.record_group
        and not any(message.startswith(alias) for alias in ai_config.alias)
        and not message.startswith("sat")
        and "[CQ:mface" not in message
        and "[CQ:video" not in message
        and "[CQ:image" not in message
        and not message.startswith("clean.session")
    )


def is_use(event: GroupMessageEvent) -> bool:
    message = str(event.get_message())
    return (
        event.group_id in ai_config.record_group
        and "[CQ:mface" not in message
        and "[CQ:image" not in message
        and "[CQ:video" not in message
    )


async def load_or_init_data(group_id: str, prompt: str = ai_config.prompt) -> list:
    file_path = os.path.join(datadir, f"{group_id}.json")
    if not os.path.exists(file_path):
        async with aiofiles.open(file_path, "w") as f:
            await f.write("[]")

    async with aiofiles.open(file_path) as f:
        data = ujson.loads(await f.read())
    if not data:
        data.append({"role": "system", "content": prompt})
    else:
        data[0] = {"role": "system", "content": prompt}
    return data


async def save_data(group_id: str, data: list):
    file_path = os.path.join(datadir, f"{group_id}.json")
    async with aiofiles.open(file_path, "w") as f:
        await f.write(ujson.dumps(data, indent=4, ensure_ascii=False))


def format_time(event_time: int) -> str:
    return (
        f"[{datetime.datetime.fromtimestamp(event_time).strftime('%Y-%m-%d %H:%M:%S')}]"
    )


def create_process_text(event: GroupMessageEvent, text: str, time_now: str) -> str:
    nickname = event.sender.nickname
    user_id = event.get_user_id()

    if event.reply:
        reply_user_id = event.reply.sender.user_id
        reply_nickname = event.reply.sender.nickname
        reply_text = str(event.reply.message).strip()
        return f"{time_now} {nickname}({user_id}) 回复 {reply_nickname}({reply_user_id}) 的消息：{reply_text}\n回复内容：{text}"
    return f"{time_now} {nickname}({user_id})：{text}"


handle_command = on_command("sat", aliases=set(ai_config.alias), rule=is_use)
clean_command = on_command("clean.session", permission=SUPERUSER)
record_msg = on_message(rule=is_record)


@clean_command.handle()
async def _(event: GroupMessageEvent):
    group_id = str(event.group_id)
    file_path = os.path.join(datadir, f"{group_id}.json")
    if os.path.exists(file_path):
        os.remove(file_path)
        await clean_command.finish("脑袋空空！")
    await clean_command.finish("欸，我不记得有和你们聊过天啊?")


def add_element(my_list, keep_num=1):
    my_list = my_list[:keep_num] + my_list[keep_num:][-48:]
    return my_list


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
    group_id = str(event.group_id)

    text = str(event.get_message()).replace("sat", "", 1).strip()
    if not text:
        await handle_command.finish("讲话啊喂！")
    if group_id in ["475214083", "9660162200"]:
        data = await load_or_init_data(group_id, ai_config.prompt2)
        if len(data) < 8:
            data += ai_config.msglist_baiye
        else:
            for i, item in enumerate(ai_config.msglist_baiye):
                data[i + 1] = item
        data = add_element(data, 8)
    else:
        data = await load_or_init_data(group_id)
        data = add_element(data)
    # 检查最近十条对话中是否含有和本次对话 role 和 content 一样的情况

    for i in ai_config.alias:
        text = text.replace(i, "", 1).strip()
    time_now = format_time(event.time)
    process_text = create_process_text(event, text, time_now)
    last_ten = data[-10:]
    if any(i["role"] == "user" and text in i["content"] for i in last_ten):
        await handle_command.finish("这个刚刚说过了吧......", reply_message=True)

    data.append({"role": "user", "content": process_text})
    response = await chat_with_gpt(data, ai_config)
    data.append({"role": "assistant", "content": response})
    if group_id in ["475214083", "9660162200"]:
        data = add_element(data, 8)
    else:
        data = add_element(data)

    await save_data(group_id, data)
    await handle_command.finish(response, reply_message=True)


@record_msg.handle()
async def _(event: GroupMessageEvent):
    group_id = str(event.group_id)
    if group_id in ["475214083", "9660162200"]:
        data = await load_or_init_data(group_id, ai_config.prompt2)
        for i, item in enumerate(ai_config.msglist_baiye):
            data[i + 1] = item
        data = add_element(data, 8)
    else:
        data = await load_or_init_data(group_id)
        data = add_element(data)

    text = str(event.get_message()).strip()
    time_now = format_time(event.time)
    process_text = create_process_text(event, text, time_now)

    data.append({"role": "user", "content": process_text})
    await save_data(group_id, data)


# 检测@的消息
