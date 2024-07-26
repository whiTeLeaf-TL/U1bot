import asyncio
from pathlib import Path
from re import I, sub
from typing import Annotated, Any, Dict, Union

from nonebot import on_command, on_regex, require
from nonebot.adapters.onebot.v11 import (
    GROUP,
    PRIVATE_FRIEND,
    Bot,
    Event,
    GroupMessageEvent,
    Message,
    MessageEvent,
    MessageSegment,
    PrivateMessageEvent,
)
from nonebot.adapters.onebot.v11.helpers import (
    Cooldown,
    CooldownIsolateLevel,
)
from nonebot.adapters.onebot.v11.permission import GROUP_ADMIN, GROUP_OWNER
from nonebot.permission import SUPERUSER
from nonebot.exception import ActionFailed
from nonebot.log import logger
from nonebot.params import Depends, RegexGroup
from nonebot.plugin import PluginMetadata
from nonebot_plugin_tortoise_orm import add_model
from PIL import UnidentifiedImageError

from .config import CDTIME, EFFECT, MAX, SETU_PATH, WITHDRAW_TIME, Config
from .data_source import SetuHandler
from .database import (
    MessageInfo,
    SetuInfo,
    SetuSwitch,
    auto_upgrade_setuinfo,
    bind_message_data,
)
from .img_utils import EFFECT_FUNC_LIST, image_segment_convert
from .models import Setu, SetuNotFindError
from .perf_timer import PerfTimer
from .r18_whitelist import get_group_white_list_record
from .utils import SpeedLimiter

require("nonebot_plugin_localstore")
require("nonebot_plugin_tortoise_orm")


usage_msg = """指令: 色图|涩图|来点色色|色色|涩涩|来点色图"""

__plugin_meta__ = PluginMetadata(
    name="涩图",
    description="给群友涩涩",
    usage=usage_msg,
    type="application",
    homepage="https://github.com/kexue-z/nonebot-plugin-setu-now",
    config=Config,
    extra={},
)


add_model("src.plugins.nonebot_plugin_setu_now.database")


global_speedlimiter = SpeedLimiter()

setu_matcher = on_regex(
    r"^(色图|涩图|来点色色|色色|来点色图)\s?([x|✖️|×|X|*]?\d+[张|个|份]?)?\s?(r18)?\s?\s?(tag)?\s?(.*)?",
    flags=I,
    permission=PRIVATE_FRIEND | GROUP,
)

setuopenorclose_matcher = on_command(
    "setu开关",
    aliases={"色图开关", "涩图开关"},
    permission=SUPERUSER | GROUP_ADMIN | GROUP_OWNER,
)


@setuopenorclose_matcher.handle()
async def _(event: GroupMessageEvent):
    # 查询数据库中是否有该群的记录，如果有则修改，没有则创建
    if record := await SetuSwitch.get_or_none(group_id=event.group_id):
        logger.debug(f"修改涩图开关 {event.group_id}")
        record.switch = not record.switch
        await record.save()
    else:
        logger.debug(f"添加涩图开关 {event.group_id}")
        await SetuSwitch.create(group_id=event.group_id, switch=False)
        record = await SetuSwitch.get_or_none(group_id=event.group_id)
    if record.switch:
        await setuopenorclose_matcher.finish("已开启本群涩图")
    else:
        await setuopenorclose_matcher.finish("已关闭本群涩图")


@setu_matcher.handle(
    parameterless=[
        Cooldown(
            cooldown=CDTIME,
            prompt="你太快啦，请稍后再试",
            isolate_level=CooldownIsolateLevel.USER,
        )
    ]
)
async def _(
    bot: Bot,
    event: Union[PrivateMessageEvent, GroupMessageEvent],
    regex_group: Annotated[tuple[Any, ...], RegexGroup()],
    white_list_record=Depends(get_group_white_list_record),
):
    if isinstance(event, GroupMessageEvent):
        record = await SetuSwitch.get_or_none(group_id=event.group_id)
        if record is not None and not record.switch:
            await setu_matcher.finish("不可以涩涩！本群未启用涩图功能")
    setu_total_timer = PerfTimer("Image request total")
    args = list(regex_group)
    logger.debug(f"args={args}")
    num = args[1]
    r18 = args[2]
    tags = args[3]
    key = args[4]

    num = int(sub(r"[张|个|份|x|✖️|×|X|*]", "", num)) if num else 1
    num = min(num, MAX)

    # 如果存在 tag 关键字, 则将 key 视为tag
    if tags:
        tags = list(map(lambda tplist: tplist.split("或"), key.split()))
        key = ""

    if r18:
        if isinstance(event, PrivateMessageEvent):
            r18 = True
        elif isinstance(event, GroupMessageEvent):
            if white_list_record is None:
                await setu_matcher.finish(
                    "不可以涩涩！\n本群未启用R18支持\n请移除R18标签或联系维护组"
                )
            r18 = True
    if r18:
        num = 1
    logger.debug(f"Setu: r18:{r18}, tag:{tags}, key:{key}, num:{num}")
    failure_msg = 0

    async def nb_send_handler(setu: Setu) -> None:
        nonlocal failure_msg
        if setu.img is None:
            logger.warning("Invalid image type, skipped")
            failure_msg += 1
            return
        for process_func in EFFECT_FUNC_LIST:
            if r18 and process_func == EFFECT_FUNC_LIST[0]:
                # R18禁止使用默认图像处理方法(do_nothing)
                continue
            logger.debug(f"Using effect {process_func}")
            effert_timer = PerfTimer.start("Effect process")
            try:
                image = process_func(setu.img)  # type: ignore
            except UnidentifiedImageError:
                logger.warning(f"Unidentified image: {type(setu.img)}")
                failure_msg += 1
                return
            effert_timer.stop()
            msg = Message(image_segment_convert(image))
            try:
                await global_speedlimiter.async_speedlimit()
                send_timer = PerfTimer("Image send")
                message_id = 0
                await auto_upgrade_setuinfo(setu)
                if not WITHDRAW_TIME:
                    # 未设置撤回时间 正常发送
                    message_id: int = (await setu_matcher.send(msg))["message_id"]

                    await bind_message_data(message_id, setu.pid)
                    logger.debug(f"Message ID: {message_id}")
                else:
                    logger.debug(f"Using auto revoke API, interval: {WITHDRAW_TIME}")
                    await autorevoke_send(
                        bot=bot,
                        event=event,
                        message=msg,
                        revoke_interval=WITHDRAW_TIME,
                        setu=setu,
                    )
                send_timer.stop()
                global_speedlimiter.send_success()
                if SETU_PATH is None:  # 未设置缓存路径，删除缓存
                    Path(setu.img).unlink()
                return
            except ActionFailed:
                if not EFFECT:  # 设置不允许添加特效
                    failure_msg += 1
                    return
                await asyncio.sleep(0)
                logger.warning("Image send failed, retrying another effect")
        failure_msg += 1
        logger.warning("Image send failed after tried all effects")
        if SETU_PATH is None:  # 未设置缓存路径，删除缓存
            Path(setu.img).unlink()

    setu_handler = SetuHandler(key, tags, r18, num, nb_send_handler)
    try:
        await setu_handler.process_request()
    except SetuNotFindError:
        await setu_matcher.finish(f"没有找到关于 {tags or key} 的色图喵")
    if failure_msg:
        await setu_matcher.send(
            message=Message(f"{failure_msg} 张图片消失了喵"),
        )
    setu_total_timer.stop()


setuinfo_matcher = on_command("信息")


@setuinfo_matcher.handle()
async def _(
    event: MessageEvent,
):
    logger.debug("Running setu info handler")
    event_message = event.original_message
    reply_segment = event_message["reply"]

    if reply_segment == []:
        logger.debug("Command invalid: Not specified setu info to get!")
        await setuinfo_matcher.finish("请直接回复需要作品信息的插画")

    reply_segment = reply_segment[0]
    reply_message_id = reply_segment.data["id"]

    logger.debug(f"Get setu info for message id: {reply_message_id}")

    if message_info := await MessageInfo.get_or_none(message_id=reply_message_id):
        message_pid = message_info.pid
    else:
        await setuinfo_matcher.finish("未找到该插画相关信息")

    if setu_info := await SetuInfo.get_or_none(pid=message_pid):
        info_message = MessageSegment.text(f"标题：{setu_info.title}\n")
        info_message += MessageSegment.text(f"画师：{setu_info.author}\n")
        info_message += MessageSegment.text(f"PID：{setu_info.pid}")

        await setu_matcher.finish(MessageSegment.reply(reply_message_id) + info_message)
    else:
        await setuinfo_matcher.finish("该插画相关信息已被移除")


async def autorevoke_send(
    bot: Bot,
    event: Event,
    message: Union[str, Message, MessageSegment],
    at_sender: bool = False,
    revoke_interval: int = 60,
    setu=None,
    **kwargs,
) -> asyncio.TimerHandle:
    """发出消息指定时间后自动撤回

    参数:
        bot: 实例化的Bot类
        event: 事件对象
        message: 消息对象或消息文本
        at_sender: 是否在消息中添加 @ 用户
        revoke_interval: 撤回消息的间隔时间, 单位为秒

    返回:
        [`TimerHandle`](https://docs.python.org/zh-cn/3/library/asyncio-eventloop.html#asyncio.TimerHandle) 对象, 可以用来取消定时撤回任务
    """  # noqa: E501
    message_data: Dict[str, Any] = await bot.send(
        event, message, at_sender=at_sender, **kwargs
    )
    message_id: int = message_data["message_id"]
    await bind_message_data(message_id, setu.pid)

    loop = asyncio.get_running_loop()
    return loop.call_later(
        revoke_interval,
        lambda: loop.create_task(bot.delete_msg(message_id=message_id)),
    )
