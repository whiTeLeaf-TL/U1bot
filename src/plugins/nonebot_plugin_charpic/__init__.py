from nonebot import on_command
from nonebot.adapters.onebot.v11 import Bot, Event, MessageSegment, Message
from nonebot.typing import T_State
from nonebot.params import CommandArg
from nonebot.plugin import PluginMetadata

from .data_source import *


__plugin_meta__ = PluginMetadata(
    name='字符画',
    description='画一幅好看的字符画吧！',
    usage='字符画 <图片>（可GIF）',
    extra={
        'menu_data': [
            {
                'func': '字符画',
                'trigger_method': '字符画 <图片>',
                'trigger_condition': '群聊/私聊',
                'brief_des': '合成字符画，但输出的是图片（哭），可以用GIF啊！',
                'detail_des': '字符画 <图片>\n' '根据提供的图片生成相应的字符画\n' '群聊或私聊\n' '例如：\n' '字符画 图片',
            }
        ],
        'menu_template': 'default',
    },
)

pic2text = on_command("字符画", priority=26, block=True)


@pic2text.handle()
async def _(state: T_State, args: Message = CommandArg()):
    for seg in args:
        if seg.type == "image":
            state["image"] = Message(seg)


@pic2text.got("image", prompt="啊？图呢？你再发个图出来我看看试试？")
async def generate_(bot: Bot, event: Event, state: T_State):
    msg = state["image"]
    if msg[0].type == "image":
        url = msg[0].data["url"]  # 图片链接
        await pic2text.send("让姚奕思考一下...")

        pic = await get_img(url)  # 取图
        if not pic:
            await pic2text.finish(event, message="图片因为靠近”错误“黑洞而消失了")

        if pic.format == "GIF":
            res = await char_gif(pic)
            await pic2text.finish(MessageSegment.image(res))
        text = await get_pic_text(pic)
        if text:
            res = await text2img(text)
            await pic2text.finish(MessageSegment.image(res))
    else:
        await pic2text.finish("气死我力！要的是图！")
