from re import L

from nonebot import logger

# 导入插件方法
from nonebot_plugin_tortoise_orm import add_model
from tortoise import fields
from tortoise.models import Model

add_model("src.plugins.waifu.models")


class WaifuProtect(Model):
    group_id = fields.BigIntField(pk=True)
    # 列表
    user_id: list[int] = fields.JSONField(default=[])
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "waifu_protect"


class WaifuCP(Model):
    group_id = fields.BigIntField(pk=True)
    # 字典
    affect: dict[str, int] = fields.JSONField(default={})
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "waifu_cp"


class PWaifu(Model):
    group_id = fields.BigIntField(pk=True)
    # 列表
    waifu: list[int] = fields.JSONField(default=[])
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "waifu"


class WaifuLock(Model):
    group_id = fields.BigIntField(pk=True)
    # 字典
    lock: dict[str, int] = fields.JSONField(default={})
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "waifu_lock"


class Waifuyinppa1(Model):
    user_id = fields.BigIntField(pk=True)
    count = fields.IntField(default=0)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "waifu_yinppa1"


class Waifuyinppa2(Model):
    user_id = fields.BigIntField(pk=True)
    count = fields.IntField(default=0)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "waifu_yinppa2"
