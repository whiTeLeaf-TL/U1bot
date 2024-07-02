from random import choice

from nonebot import get_driver, on_command
from nonebot import logger as log
from nonebot.adapters.onebot.v11 import Message, MessageEvent, MessageSegment
from nonebot.adapters.onebot.v11.helpers import Cooldown, extract_image_urls
from nonebot.plugin import PluginMetadata

from .config import Config
from .data_source import SauceNAO

conf = Config.parse_obj(get_driver().config.dict())

__plugin_meta__ = PluginMetadata(
    name="以图搜图", description="找不到图片啊~", usage="以图搜图", config=Config
)


_search_flmt_notice = choice(["太快了啊！", "冷静 1 下", "歇会歇会~~"])


search = on_command("以图搜图", aliases={"搜图", "以图搜图"})


@search.got("image", "图呢？", [Cooldown(5, prompt=_search_flmt_notice)])
async def _(event: MessageEvent):
    if not conf.saucenao_apikey:
        log.warning("你没配置 Key 啊 Bro~")

    user_id = event.get_user_id()
    img = extract_image_urls(event.get_message())
    if not img:
        await search.reject("请发送图片而不是其他东西！！")

    try:
        result = await SauceNAO(conf.saucenao_apikey).search(img[0])
    except Exception as err:
        await search.finish(f"搜索失败：{str(err)}")

    await search.finish(Message(f"> {MessageSegment.at(user_id)}\n{result}"))
