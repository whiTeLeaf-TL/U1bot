from tortoise import fields
from tortoise.models import Model
from nonebot_plugin_tortoise_orm import add_model

add_model("src.plugins.nonebot_plugin_analysis_bilibili.models")
class Bili_Analysis_Switch(Model):
    group_id = fields.IntField(pk=True)
    switch = fields.BooleanField(default=True)

    class Meta:
        table = "bili_switch"
