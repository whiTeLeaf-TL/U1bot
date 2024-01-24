from tortoise import fields
from tortoise.models import Model

# 导入插件方法
from nonebot_plugin_tortoise_orm import add_model


add_model("src.plugins.morning.models")


class Morning(Model):
    group_id = fields.BigIntField(pk=True)
    # 字典
    morning = fields.JSONField(default=[])
    night = fields.JSONField(default=[])
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "morning"