from tortoise import fields
from tortoise.models import Model

# 导入插件方法
from nonebot_plugin_tortoise_orm import add_model


add_model("src.plugins.cave.models")


class cave_models(Model):
    """
    Model representing the cave_models table in the database.

    Attributes:
        id (int): The primary key of the cave model.
        details (str): The details of the cave model.
        user_id (int): The user ID associated with the cave model.
        time (datetime): The timestamp when the cave model was created.
    """

    id = fields.IntField(pk=True, generated=True)
    details = fields.TextField()
    user_id = fields.BigIntField()
    time = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "cave_models"
