import random
import nonebot
from nonebot.plugin.on import on_command, on_message
from nonebot.permission import SUPERUSER
from nonebot.typing import T_State
from nonebot.adapters.onebot.v11 import (
    GROUP_ADMIN,
    GROUP_OWNER,
    Bot,
    GroupMessageEvent,
    Message,
    MessageSegment,
)
from nonebot.plugin import PluginMetadata
from numpy import record
from .models import *
from .utils import *
from .config import Config
from datetime import datetime, timedelta

__plugin_meta__ = PluginMetadata(name="waifu", description="", usage="", config=Config)


global_config = nonebot.get_driver().config
waifu_config = Config.parse_obj(global_config.dict())
last_sent_time_filter = waifu_config.waifu_last_sent_time_filter
HE = waifu_config.waifu_he
BE = HE + waifu_config.waifu_be
NTR = waifu_config.waifu_ntr
no_waifu = [
    "你没有娶到群友，强者注定孤独，加油！",
    "找不到对象.jpg",
    "雪花飘飘北风萧萧～天地一片苍茫。",
    "要不等着分配一个对象？",
    "恭喜伱没有娶到老婆~",
    "さんが群友で結婚するであろうヒロインは、\n『自分の左手』です！",
    "醒醒，伱没有老婆。",
    "哈哈哈哈哈哈哈哈哈",
    "智者不入爱河，建设美丽中国。",
    "智者不入爱河，我们终成富婆",
    "智者不入爱河，寡王一路硕博",
]

happy_end = [
    "好耶~",
    "婚礼？启动！",
    "需要咱主持婚礼吗qwq",
    "不许秀恩爱！",
    "(响起婚礼进行曲♪)",
    "比翼从此添双翅，连理于今有合枝。\n琴瑟和鸣鸳鸯栖，同心结结永相系。",
    "金玉良缘，天作之合，郎才女貌，喜结同心。",
    "繁花簇锦迎新人，车水马龙贺新婚。",
    "乾坤和乐，燕尔新婚。",
    "愿天下有情人终成眷属。",
    "花团锦绣色彩艳，嘉宾满堂话语喧。",
    "火树银花不夜天，春归画栋双栖燕。",
    "红妆带绾同心结，碧树花开并蒂莲。",
    "一生一世两情相悦，三世尘缘四世同喜",
    "玉楼光辉花并蒂，金屋春暖月初圆。",
    "笙韵谱成同生梦，烛光笑对含羞人。",
    "祝你们百年好合,白头到老。",
    "祝你们生八个。",
]


async def waifu_rule(bot: Bot, event: GroupMessageEvent, state: T_State) -> bool:
    """
    规则：娶群友
    """
    today = datetime.now()
    yesterday = today - timedelta(days=1)
    await WaifuCP.filter(created_at__lt=yesterday).delete()
    msg = event.message.extract_plain_text()
    if not msg.startswith("娶群友"):
        return False
    group_id = event.group_id
    user_id = event.user_id
    protect_list = await WaifuProtect.get_or_none(group_id=group_id)
    if protect_list is not None:
        if user_id in protect_list.user_id:
            return False
    at = get_message_at(event.message)
    at = at[0] if at else None
    if protect_list is not None:
        if at in protect_list.user_id:
            return False
    tips = "伱的群友結婚对象是、"
    rec, _ = await WaifuCP.get_or_create(group_id=group_id)
    rec = rec.affect
    if (waifu_id := rec.get(str(user_id))) and waifu_id != user_id:
        try:
            member = await bot.get_group_member_info(
                group_id=group_id, user_id=waifu_id
            )
        except:
            member = None
            waifu_id = user_id
        if member:
            if at and at != user_id:
                if waifu_id == at:
                    msg = (
                        "这是你的CP！"
                        + random.choice(happy_end)
                        + MessageSegment.image(file=await user_img(waifu_id))
                    )
                    if waifu := await Waifu.get_or_none(group_id=group_id):
                        waifu = waifu.waifu
                    else:
                        waifu = []

                    if user_id in waifu:
                        waifulock, _ = await WaifuLock.get_or_create(
                            message_id=group_id
                        )
                        waifulock.lock[waifu_id] = user_id
                        waifulock.lock[user_id] = waifu_id
                        await waifulock.save()
                        msg += "\ncp已锁！"
                else:
                    msg = (
                        "你已经有CP了，不许花心哦~"
                        + MessageSegment.image(file=await user_img(waifu_id))
                        + f"你的CP：{member['card'] or member['nickname']}"
                    )
            else:
                msg = (
                    tips
                    + MessageSegment.image(file=await user_img(waifu_id))
                    + f"『{member['card'] or member['nickname']}』！"
                )
            await bot.send(event, msg, at_sender=True)
            return False

    if at:
        if at == rec.get(str(at)):
            X = HE
            del rec[waifu_id]
        else:
            X = random.randint(1, 100)

        if 0 < X <= HE:
            waifu_id = at
            tips = "恭喜你娶到了群友!\n" + tips
        elif HE < X <= BE:
            waifu_id = user_id
        else:
            pass

    if not waifu_id:
        group_id = event.group_id
        member_list = await bot.get_group_member_list(group_id=group_id)
        lastmonth = event.time - last_sent_time_filter
        rule_out = protect_list or set(rec.keys())
        waifu_ids = [
            user_id
            for member in member_list
            if (user_id := member["user_id"]) not in rule_out
            and member["last_sent_time"] > lastmonth
        ]
        if waifu_ids:
            waifu_id = random.choice(list(waifu_ids))
        else:
            msg = "群友已经被娶光了、\n" + random.choice(no_waifu)
            await bot.send(event, msg, at_sender=True)
            return False
    state["waifu"] = waifu_id, tips
    return True


waifu = on_message(rule=waifu_rule, priority=90, block=True)


@waifu.handle()
async def _(bot: Bot, event: GroupMessageEvent, state: T_State):
    group_id = event.group_id
    user_id = event.user_id
    waifu_id, tips = state["waifu"]
    if waifu_id == user_id:
        record_cp, _ = await WaifuCP.get_or_create(group_id=group_id)
        record_cp.affect[user_id] = user_id
        await record_cp.save()
        await waifu.finish(random.choice(no_waifu), at_sender=True)
    rec, _ = await WaifuCP.get_or_create(group_id=group_id)
    rec = rec.affect
    record_waifu, _ = await Waifu.get_or_create(group_id=group_id)
    if waifu_id in rec:
        waifu_cp = rec[str(waifu_id)]
        member = await bot.get_group_member_info(group_id=group_id, user_id=waifu_cp)
        msg = (
            "人家已经名花有主了~"
            + MessageSegment.image(file=await user_img(waifu_cp))
            + "ta的cp："
            + (member["card"] or member["nickname"])
        )
        record_lock, _ = await WaifuLock.get_or_create(group_id=group_id)
        if waifu_id in record_lock.lock.keys():
            await waifu.finish(msg + "\n本对cp已锁！", at_sender=True)
        X = random.randint(1, 100)
        if X > NTR:
            record_CP, _ = await WaifuCP.get_or_create(group_id=group_id)
            record_CP.affect[user_id] = user_id
        else:
            rec.pop(waifu_cp)
            record_waifu.waifu.discard(waifu_cp)
            await waifu.send(msg + "\n但是...", at_sender=True)
            await asyncio.sleep(1)
    record_CP, _ = await WaifuCP.get_or_create(group_id=group_id)
    record_CP.affect[user_id] = waifu_id
    record_CP.affect[waifu_id] = user_id
    record_waifu.waifu.append(waifu_id)
    member = await bot.get_group_member_info(group_id=group_id, user_id=waifu_id)
    msg = (
        tips
        + MessageSegment.image(file=await user_img(waifu_id))
        + f"『{(member['card'] or member['nickname'])}』！"
    )
    await record_CP.save()
    await record_waifu.save()
    await waifu.finish(msg, at_sender=True)
