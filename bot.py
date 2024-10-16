import nonebot
from nonebot import get_bots
from nonebot.adapters.onebot.v11 import Adapter as ONEBOT_V11Adapter
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent
from nonebot.exception import IgnoredException

nonebot.init()
app = nonebot.get_asgi()
driver = nonebot.get_driver()
driver.register_adapter(ONEBOT_V11Adapter)


nonebot.load_from_toml("pyproject.toml")
from nonebot.message import run_preprocessor


@run_preprocessor
async def _(bot: Bot, event: GroupMessageEvent):
    "防止双发"
    # 检测群是否有两个机器人，如果是则第一个机器人
    bot_qqid = bot.self_id
    # 获取所有机器人,取出qq号
    bots = get_bots()
    bot_qqids: list[str] = [bot.self_id for bot in bots.values()]
    group_members = await bot.get_group_member_list(group_id=event.group_id)
    group_qqids: list[str] = [str(member["user_id"]) for member in group_members]
    # 检查bot_qqid是否在group_qqids中,列出同类项
    same_qqids = list(set(bot_qqids) & set(group_qqids))
    if bot_qqid != same_qqids[0]:
        raise IgnoredException("遇到双发，忽略")


@run_preprocessor
async def _(bot: Bot, event: GroupMessageEvent):
    "防止机器人自言自语"
    # 检测是否是机器人自己发的消息
    event_qqid = str(event.user_id)
    bot_qqid = bot.self_id
    if event_qqid == bot_qqid:
        raise IgnoredException("机器人自言自语，忽略")


if __name__ == "__main__":
    nonebot.run()
