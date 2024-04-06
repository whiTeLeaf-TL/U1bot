from pydantic import BaseModel

from typing import List, Dict
from nonebot import get_plugin_config


class Config(BaseModel):

    fishes: List[Dict] = [
        {
            "name": "空气",
            "frequency": 1,
            "weight": 100,
            "price": 0
        },
        {
            "name": "小鱼",
            "frequency": 2,
            "weight": 100,
            "price": 2
        },
        {
            "name": "尚方宝剑",
            "frequency": 2,
            "weight": 100,
            "price": 1
        },
        {
            "name": "臭袜子",
            "frequency": 2,
            "weight": 90,
            "price": 2
        },
        {
            "name": "小杂鱼~♡",
            "frequency": 3,
            "weight": 5,
            "price": 20
        },
        {
            "name": "烤激光鱼",
            "frequency": 10,
            "weight": 1,
            "price": 50
        },
        {
            "name": "破旧的钓鱼竿",
            "frequency": 2,
            "weight": 1,
            "price": 30
        }
    ]

    fishing_limit: int = 60


config = get_plugin_config(Config)
