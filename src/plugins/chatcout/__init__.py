from nonebot import get_plugin_config, on_fullmatch, on_message
from nonebot.adapters.onebot.v11 import GroupMessageEvent
from nonebot.plugin import PluginMetadata

from .config import Config
from .models import ChatTime, ChatTimeDB

__plugin_meta__ = PluginMetadata(
    name="chatcout",
    description="",
    usage="",
    config=Config,
)

config: Config = get_plugin_config(Config)

coutmsg = on_message()


@coutmsg.handle()
async def _(event: GroupMessageEvent):
    group_id = event.group_id
    user_id = str(event.user_id)
    # 获取数据库
    chat_time, is_create = await ChatTimeDB.get_or_create(group_id=group_id)
    chat_time_total, is_create = await ChatTime.get_or_create(group_id=group_id)

    # 获取时间戳
    timestamp_map = chat_time.timestamp_map
    today_time_map = chat_time.today_time_map
    today_message_map = chat_time.today_message_map
    today_remind_time = chat_time.today_remind_time
    # 获取用户的聊天时长和消息数
    user_time_map = chat_time_total.user_time_map
    user_message_map = chat_time_total.user_message_map

    # 获取现在的时间戳
    now_timestamp = event.time

    # 如果用户不在时间戳中，添加用户，或者数据是昨天的，重置数据
    if user_id not in timestamp_map:
        user_time_map[user_id] = 0
        user_message_map[user_id] = 0
        timestamp_map[user_id] = now_timestamp
        today_time_map[user_id] = 0
        today_message_map[user_id] = 0
        today_remind_time[user_id] = [60, 120, 180, 240, 300]  # 分钟
    elif now_timestamp - timestamp_map[user_id] >= 86400:
        today_time_map[user_id] = 0
        today_message_map[user_id] = 0
        timestamp_map[user_id] = now_timestamp
        today_remind_time[user_id] = [60, 120, 180, 240, 300]
    # 如果与现在的时间戳相差不大于5分钟，消息数+1，记录数据库与现在的时间戳的差值加在在数据库中
    if now_timestamp - timestamp_map[user_id] <= config.interval:
        today_message_map[user_id] += 1
        user_message_map[user_id] += 1

        # 计算时间差，加在数据库中为秒
        time_diff = now_timestamp - timestamp_map[user_id]

        today_time_map[user_id] += time_diff
        user_time_map[user_id] += time_diff
    timestamp_map[user_id] = now_timestamp

    # 如果在时间段内，发送消息提醒，并移除时间段
    for remind_time in today_remind_time[user_id]:
        if today_time_map[user_id] >= remind_time * 60:
            await coutmsg.send(f"你今天已经水群{remind_time}分钟了！", at_sender=True)
            today_remind_time[user_id].remove(remind_time)

    # 保存数据库
    await chat_time.save()
    await chat_time_total.save()


search_cout = on_fullmatch("查询水群")


@search_cout.handle()
async def _(event: GroupMessageEvent):
    # %s今天水了%d分%d秒，发了%d条消息；总计水了%d分%d秒，发了%d条消息
    group_id = event.group_id
    user_id = str(event.user_id)
    # 获取数据库
    chat_time = await ChatTimeDB.get_or_none(group_id=group_id)
    chat_time_total = await ChatTime.get_or_none(group_id=group_id)

    if (
        chat_time is None
        or chat_time_total is None
        or user_id not in chat_time_total.user_message_map
    ):
        await search_cout.finish("找不到今天的数据？看起来你喜欢沉淀？", at_sender=True)

    today_time_map = chat_time.today_time_map
    today_message_map = chat_time.today_message_map
    user_time_map = chat_time_total.user_time_map
    user_message_map = chat_time_total.user_message_map

    today_time = today_time_map[user_id]
    today_message = today_message_map[user_id]
    user_time = user_time_map[user_id]
    user_message = user_message_map[user_id]

    await search_cout.finish(
        f"你今天水了{today_time//60}分{today_time%60}秒，发了{today_message}条消息；总计水了{user_time//60}分{user_time%60}秒，发了{user_message}条消息呢",
        at_sender=True,
    )
