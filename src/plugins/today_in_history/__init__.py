from .config import Config
from nonebot_plugin_htmlrender import text_to_pic
from nonebot_plugin_apscheduler import scheduler
import json
from datetime import date

import httpx
import nonebot
from nonebot import require, get_driver, on_fullmatch
from nonebot.adapters.onebot.v11 import MessageSegment
from nonebot.plugin import PluginMetadata

require("nonebot_plugin_apscheduler")

__plugin_meta__ = PluginMetadata(name="历史上的今天",
                                 description="让我们看看今天在过去都发生了什么吧!",
                                 usage="指令:历史上的今天",
                                 config=Config)

plugin_config = Config.parse_obj(get_driver().config.dict())
if plugin_config.history_inform_time is None:
    hour: int = 7
    minute: int = 35
elif isinstance(plugin_config.history_inform_time, str):
    strhour, strminute = plugin_config.history_inform_time.split(" ")
    hour, minute = int(strhour), int(strminute)
elif isinstance(plugin_config.history_inform_time, list):
    hour = plugin_config.history_inform_time[0]["HOUR"]
    minute = plugin_config.history_inform_time[0]["MINUTE"]

config_test = on_fullmatch("test")


@config_test.handle()
async def _():
    await config_test.send(f"time={hour}:{minute}")
    await config_test.send(
        f"is_list={isinstance(plugin_config.history_inform_time, list)}")
    await config_test.send(
        f"is_str={isinstance(plugin_config.history_inform_time, str)}")
    await config_test.send(f"is_None={plugin_config.history_inform_time is None}")


history_matcher = on_fullmatch("历史上的今天")


@history_matcher.handle()
async def _():
    await history_matcher.finish(await get_history_info())


# api处理->json
def text_handle(text: str) -> dict:
    text = text.replace(r"<\/a>", "")
    text = text.replace("\n", "")

    # 去除html标签
    while True:
        address_head = text.find("<a target=")
        address_end = text.find(">", address_head)
        if address_head == -1 or address_end == -1:
            break
        text_middle = text[address_head:address_end + 1]
        text = text.replace(text_middle, "")

    # 去除api返回内容中不符合json格式的部分
    # 去除key:desc值
    address_head: int = 0
    while True:
        address_head = text.find('"desc":', address_head)
        address_end = text.find('"cover":', address_head)
        if address_head == -1 or address_end == -1:
            break
        text_middle = text[address_head + 8:address_end - 2]
        address_head = address_end
        text = text.replace(text_middle, "")

    # 去除key:title中多引号
    address_head: int = 0
    while True:
        address_head = text.find('"title":', address_head)
        address_end = text.find('"festival"', address_head)
        if address_head == -1 or address_end == -1:
            break
        text_middle = text[address_head + 9:address_end - 2]
        if '"' in text_middle:
            text_middle = text_middle.replace('"', " ")
            text = text[:address_head + 9] + text_middle + text[address_end -
                                                                2:]
        address_head = address_end

    return json.loads(text)


# 信息获取
async def get_history_info() -> MessageSegment:
    async with httpx.AsyncClient() as client:
        month = date.today().strftime("%m")
        day = date.today().strftime("%d")
        url = f"https://baike.baidu.com/cms/home/eventsOnHistory/{month}.json"
        r = await client.get(url)
        if r.status_code != 200:
            return MessageSegment.text("获取失败，请重试")
        r.encoding = "unicode_escape"
        data = text_handle(r.text)
        today = f"{month}{day}"
        s = f"历史上的今天 {today}\n"
        len_max = len(data[month][month + day])
        for i in range(len_max):
            str_year = data[month][today][i]["year"]
            str_title = data[month][today][i]["title"]
            s = (
                f"{s}{str_year} {str_title}"
                if i == len_max - 1
                else f"{s}{str_year} {str_title}\n"
            )
        return MessageSegment.image(await text_to_pic(s))


# 消息发送
# async def send_msg_today_in_histoty():
#     msg = await get_history_info()
#     for qq in plugin_config.history_qq_friends:
#         await nonebot.get_bot().send_private_msg(user_id=qq, message=Message(msg))

#     for qq_group in plugin_config.history_qq_groups:
#         await nonebot.get_bot().send_group_msg(group_id=qq_group, message=Message(msg))

# 定时任务
# for index, time in enumerate(plugin_config.history_inform_time):
#     nonebot.logger.info("id:{},time:{}".format(index, time))
#     scheduler.add_job(send_msg_today_in_histoty, 'cron', hour=time.hour, minute=time.minute)


# 定时任务
@scheduler.scheduled_job("cron", hour=hour, minute=minute)
async def _():
    msg = await get_history_info()
    for qq in plugin_config.history_qq_friends:
        await nonebot.get_bot().send_private_msg(user_id=qq, message=msg)
    for qq_group in plugin_config.history_qq_groups:
        await nonebot.get_bot().send_group_msg(group_id=qq_group, message=msg)
