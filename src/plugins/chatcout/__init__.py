from datetime import datetime

from nonebot import get_plugin_config, logger, on_fullmatch, on_message
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
    """
    处理群消息事件以跟踪和提醒用户的聊天活动。

    参数:
        event (GroupMessageEvent): 包含群消息详细信息的事件对象。

    功能:
        - 检索或创建群组和用户的聊天时间记录。
        - 更新用户的时间戳和消息计数。
        - 如果上次记录的时间戳是前一天的，则重置每日数据。
        - 计算消息之间的时间差并更新用户的聊天时长。
        - 根据预定义的聊天时长里程碑向用户发送提醒。
        - 将更新的聊天时间记录保存到数据库。
    """
    group_id = event.group_id
    user_id = event.get_user_id()
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
        # 用户第一次发送消息
        timestamp_map[user_id] = now_timestamp
        user_time_map[user_id] = 0
        user_message_map[user_id] = 0
        today_time_map[user_id] = 0
        today_message_map[user_id] = 0
        today_remind_time[user_id] = [180, 240, 300, 360]  # 分钟
    else:
        # 用户已存在，检查是否为新的一天
        if (
            datetime.fromtimestamp(now_timestamp).date()
            != datetime.fromtimestamp(timestamp_map[user_id]).date()
        ):
            timestamp_map[user_id] = now_timestamp
            today_time_map[user_id] = 0
            today_message_map[user_id] = 0
            today_remind_time[user_id] = [180, 240, 300, 360]  # 分钟

    # 检查时间差
    if now_timestamp - timestamp_map[user_id] <= config.interval:
        today_message_map[user_id] += 1
        user_message_map[user_id] += 1
        time_diff = now_timestamp - timestamp_map[user_id]
        today_time_map[user_id] += time_diff
        user_time_map[user_id] += time_diff

    # 更新时间戳
    timestamp_map[user_id] = now_timestamp

    # 发送消息提醒
    today_time = today_time_map[user_id]
    if reminders_to_remove := {
        remind_time
        for remind_time in today_remind_time[user_id]
        if today_time >= remind_time * 60
    }:
        try:
            await coutmsg.send(
                f"你今天已经水群{today_time // 60}分{today_time % 60}秒了！",
                at_sender=True,
            )
            # 清空今天的提醒时间
            today_remind_time[user_id] = [
                t for t in today_remind_time[user_id] if t not in reminders_to_remove
            ]
        except Exception as e:
            logger.error(f"发送消息时出错: {e}")

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
