import base64
import traceback
from typing import Union
import jinja2
from nonebot.params import CommandArg
from nonebot import on_command
from nonebot.adapters.onebot.v11 import Bot as V11Bot
from nonebot.adapters.onebot.v11 import Message as V11Msg
from nonebot.adapters.onebot.v11 import MessageSegment as V11MsgSeg
from nonebot.adapters.onebot.v12 import Bot as V12Bot
from nonebot.adapters.onebot.v12 import MessageSegment as V12MsgSeg
from nonebot.log import logger
from nonebot.matcher import Matcher
from pathlib import Path
from nonebot_plugin_htmlrender import html_to_pic
import aiofiles

# import aiohttp
import re
import json

dir_path = Path(__file__).parent
template_path = dir_path / "template"
env = jinja2.Environment(
    loader=jinja2.FileSystemLoader(template_path), enable_async=True
)


async def get_reply(data: dict):
    template = env.get_template("index.html")
    content = await template.render_async(data=data, url=template_path / "cover.webp")
    return await html_to_pic(
        content,
        wait=0,
    )


async def async_open_file(file_path):
    async with aiofiles.open(file_path, mode="rb") as file:
        return await file.read()


async def async_read_json(file_path):
    async with aiofiles.open(file_path, mode="r", encoding="utf-8") as file:
        content = await file.read()
        return json.loads(content)


menu = on_command("菜单", aliases={"cd", "功能", "帮助", "help"}, priority=5)


@menu.handle()
async def _(bot: Union[V11Bot, V12Bot], matcher: Matcher, arg: V11Msg = CommandArg()):
    msg = arg.extract_plain_text().strip()

    if not msg:  # 参数为空，主菜单
        img_bytes = await async_open_file(dir_path / "main.png")
        base64_str = "base64://" + base64.b64encode(img_bytes).decode()
        await matcher.finish(V11MsgSeg.image(base64_str))

    match_result = re.match(r"^(?P<name>.*?)$", msg)
    if not match_result:
        return

    plugin_name: str = match_result["name"]

    # 查询plugin_name是否为数字，是则数字查找，否则模糊名查找，获取json，在dir_path/plugin.json
    # 加载json
    plugin_list = await async_read_json(dir_path / "plugin.json")

    if plugin_name.isdigit():
        plugin_dict = plugin_list.get(plugin_name)
        if not plugin_dict:
            await matcher.finish("插件序号不存在")
    else:
        plugin_dict = {}
        for key, value in plugin_list.items():
            # 模糊搜索
            if plugin_name in value["name"]:
                plugin_dict[key] = value
        if not plugin_dict:
            await matcher.finish("插件名过于模糊或不存在")

    try:
        if plugin_dict:
            result = await get_reply(plugin_dict)
        else:
            result = "插件名过于模糊或不存在"
    except Exception as e:
        logger.warning(traceback.format_exc())
        await matcher.finish("出错了，请稍后再试")

    if isinstance(result, str):
        await matcher.finish(result)

    if isinstance(bot, V11Bot):
        await matcher.finish(V11MsgSeg.image(result))
    elif isinstance(bot, V12Bot):
        resp = await bot.upload_file(type="data", name="ddcheck", data=result)
        file_id = resp["file_id"]
        await matcher.finish(V12MsgSeg.image(file_id))
