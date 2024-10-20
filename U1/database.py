from tortoise import fields
from tortoise.models import Model

from nonebot_plugin_tortoise_orm import add_model
add_model("U1.database")


class Channel(Model):
    id = fields.CharField(max_length=255, description="主键", pk=True)
    platform = fields.CharField(max_length=255, description="主键")
    flag = fields.BigIntField(unsigned=True, default=0, null=True, description="标志")
    assignee = fields.CharField(max_length=255, null=True, description="受让人")
    guildId = fields.CharField(max_length=255, null=True, description="公会ID")
    locales = fields.TextField(null=True, description="语言环境")
    permissions = fields.TextField(null=True, description="权限")
    createdAt = fields.DatetimeField(null=True, description="创建时间")

    class Meta:
        table = "channel"  # 表名
        unique_together = (("id", "platform"),)  # 确保 (id, platform) 组合唯一
