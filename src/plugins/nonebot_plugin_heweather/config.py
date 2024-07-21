from typing import Optional

from nonebot import get_driver
from pydantic import BaseModel, Extra

from .model import HourlyType


class Config(BaseModel, extra=Extra.ignore):
    qweather_apikey: Optional[str] = None
    qweather_apitype: Optional[int] = None
    qweather_hourlytype: Optional[HourlyType] = HourlyType.current_12h
    debug: bool = False


plugin_config = Config.model_validate(get_driver().config.model_dump())
QWEATHER_APIKEY = plugin_config.qweather_apikey
QWEATHER_APITYPE = plugin_config.qweather_apitype
QWEATHER_HOURLYTYPE = plugin_config.qweather_hourlytype
DEBUG = plugin_config.debug
