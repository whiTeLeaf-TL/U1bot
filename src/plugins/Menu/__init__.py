import base64
import re
import traceback
from pathlib import Path
from typing import Union

import aiofiles
import jinja2
import ujson as json
from nonebot import on_command
from nonebot.adapters.onebot.v11 import Bot as V11Bot
from nonebot.adapters.onebot.v11 import Message as V11Msg
from nonebot.adapters.onebot.v11 import MessageSegment as V11MsgSeg
from nonebot.adapters.onebot.v12 import Bot as V12Bot
from nonebot.adapters.onebot.v12 import MessageSegment as V12MsgSeg
from nonebot.log import logger
from nonebot.matcher import Matcher
from nonebot.params import CommandArg
from nonebot_plugin_htmlrender import html_to_pic

dir_path = Path(__file__).parent
template_path = dir_path / "template"
env = jinja2.Environment(
    loader=jinja2.FileSystemLoader(template_path), enable_async=True, autoescape=False
)


async def get_reply(data: dict):
    template = env.get_template("index.html")
    content = await template.render_async(data=data, url=template_path / "cover.webp")
    return await html_to_pic(
        content,
        wait=0,
    )


menu = on_command("菜单", aliases={"cd", "功能", "帮助", "help"})

with open(dir_path / "main.png", mode="rb") as file:
    img_bytes = file.read()
base64_str = f"base64://{base64.b64encode(img_bytes).decode()}"

# 将 json 所有功能缓存 base64
cache_plugin_img: dict = {}

with open(dir_path / "plugin.json", mode="r", encoding="utf-8") as file:
    content = file.read()
    plugin_list: dict = json.loads(content)


@menu.handle()
async def _(bot: Union[V11Bot, V12Bot], matcher: Matcher, arg: V11Msg = CommandArg()):
    msg = arg.extract_plain_text().strip()

    if not msg:  # 参数为空，主菜单
        await matcher.finish(V11MsgSeg.image(base64_str))

    match_result = re.match(r"^(?P<name>.*?)$", msg)
    if not match_result:
        return

    plugin_name: str = match_result["name"]

    if plugin_name.isdigit():
        plugin_dict = plugin_list.get(plugin_name)
        if not plugin_dict:
            await matcher.finish("插件序号不存在")
    else:
        for _, value in plugin_list.items():
            if plugin_name in value["name"]:
                plugin_dict = value
        if not plugin_dict:
            await matcher.finish("插件名过于模糊或不存在")

    plugin_name = plugin_dict["name"]

    if plugin_name not in cache_plugin_img:
        try:
            result = await get_reply(plugin_dict)
            if plugin_name not in cache_plugin_img and isinstance(result, bytes):
                cache_plugin_img[plugin_name] = (
                    f"base64://{base64.b64encode(result).decode()}"
                )
        except Exception:
            logger.warning(traceback.format_exc())
            await matcher.finish("出错了，请稍后再试")
    result = cache_plugin_img[plugin_name]

    if isinstance(result, str) and not result.startswith("base64://"):
        await matcher.finish(result)

    if isinstance(bot, V11Bot):
        await matcher.finish(V11MsgSeg.image(result))
    elif isinstance(bot, V12Bot):
        resp = await bot.upload_file(type="data", name="ddcheck", data=result)
        file_id = resp["file_id"]
        await matcher.finish(V12MsgSeg.image(file_id))
