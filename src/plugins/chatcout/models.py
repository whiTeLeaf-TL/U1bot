# 导入插件方法
from nonebot_plugin_tortoise_orm import add_model
from tortoise import fields
from tortoise.models import Model

add_model("src.plugins.chatcout.models")


class ChatTime(Model):
    group_id: int = fields.BigIntField(pk=True)
    user_time_map: dict[str, int] = fields.JSONField(default={})  # 总聊天时长
    user_message_map: dict[str, int] = fields.JSONField(default={})  # 总聊天消息数

    class Meta:
        table = "chat_time_total"


class ChatTimeDB(Model):
    group_id: int = fields.BigIntField(pk=True)
    timestamp_map: dict[str, int] = fields.JSONField(default={})  # 最近说话的时间戳
    today_time_map: dict[str, int] = fields.JSONField(default={})  # 今日聊天时长
    today_message_map: dict[str, int] = fields.JSONField(default={})  # 今日聊天消息数
    today_remind_time: dict[str, list[int]] = fields.JSONField(default={})  # 提醒时间段

    class Meta:
        table = "chat_time"
