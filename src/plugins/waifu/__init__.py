import asyncio
import contextlib
import random
from datetime import datetime

from nonebot import get_driver, logger, on_command, require
from nonebot.adapters.onebot.v11 import (
    Bot,
    GroupMessageEvent,
    MessageSegment,
)
from nonebot.adapters.onebot.v11.helpers import (
    Cooldown,
    CooldownIsolateLevel,
)
from nonebot.permission import SUPERUSER
from nonebot.plugin import PluginMetadata

from .config import Config
from .models import PWaifu, WaifuCP, WaifuLock, WaifuProtect, Waifuyinppa1, Waifuyinppa2
from .utils import bbcode_to_png, get_message_at, text_to_png, user_img

__plugin_meta__ = PluginMetadata(name="waifu", description="", usage="", config=Config)


global_config = get_driver().config
waifu_config = Config.parse_obj(global_config.dict())
waifu_cd_bye = waifu_config.waifu_cd_bye
waifu_save = waifu_config.waifu_save
waifu_reset = waifu_config.waifu_reset
last_sent_time_filter = waifu_config.waifu_last_sent_time_filter
HE = waifu_config.waifu_he
BE = HE + waifu_config.waifu_be
NTR = waifu_config.waifu_ntr
yinpa_HE = waifu_config.yinpa_he
yinpa_BE = yinpa_HE + waifu_config.yinpa_be
yinpa_CP = waifu_config.yinpa_cp
yinpa_CP = yinpa_HE if yinpa_CP == 0 else yinpa_CP
Bot_NICKNAME = list(get_driver().config.nickname)
Bot_NICKNAME = Bot_NICKNAME[0] if Bot_NICKNAME else "bot"
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
    "娶不到就是娶不+-到，娶不到就多练！",
]

happy_end = [
    "好耶~",
    "婚礼？启动！",
    "需要咱主持婚礼吗 qwq",
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
    "祝你们百年好合，白头到老。",
    "祝你们生八个。",
]


# 重置记录


async def reset_record():
    logger.info("定时重置娶群友记录")
    today = datetime.now()
    yesterday = datetime(today.year, today.month, today.day, 0, 0, 0)
    logger.info(yesterday)
    await WaifuCP.filter(created_at__lt=yesterday).delete()
    await PWaifu.filter(created_at__lt=yesterday).delete()
    await WaifuLock.filter(created_at__lt=yesterday).delete()
    await Waifuyinppa1.filter(created_at__lt=yesterday).delete()
    await Waifuyinppa2.filter(created_at__lt=yesterday).delete()


async def mo_reset_record():
    logger.info("手动重置娶群友记录")
    await WaifuCP.all().delete()
    await PWaifu.all().delete()
    await WaifuLock.all().delete()
    await Waifuyinppa1.all().delete()
    await Waifuyinppa2.all().delete()


scheduler = require("nonebot_plugin_apscheduler").scheduler
on_command("重置记录", permission=SUPERUSER).append_handler(mo_reset_record)
# 第一个触发时间：每天凌晨 0:00
scheduler.add_job(reset_record, "cron", hour=0, minute=0, misfire_grace_time=120)


waifu = on_command("娶群友")


@waifu.handle()
async def _(bot: Bot, event: GroupMessageEvent):
    """规则：娶群友"""
    msg = event.message.extract_plain_text()
    # 不能娶机器人
    if event.to_me:
        await waifu.finish("不可以啦~", at_sender=True)
    user_id = event.user_id
    group_id = event.group_id
    protect_list = await WaifuProtect.get_or_none(group_id=group_id)
    if protect_list is not None and user_id in protect_list.user_id:
        return
    at = get_message_at(event.message)
    at = at[0] if at else None
    if protect_list is not None and at in protect_list.user_id:
        return
    rec, _ = await WaifuCP.get_or_create(group_id=group_id)
    rec = rec.affect
    tips = "伱的群友結婚对象是："
    if (waifu_id := rec.get(str(user_id))) and waifu_id != user_id:
        try:
            member = await bot.get_group_member_info(
                group_id=group_id, user_id=waifu_id
            )
        except Exception:
            member = None
            waifu_id = user_id
        if member:
            if at and at != user_id:
                if waifu_id == at:
                    msg = f"这是你的 CP！{random.choice(happy_end)}{MessageSegment.image(file=await user_img(waifu_id))}"
                    waifulist, _ = await PWaifu.get_or_create(group_id=group_id)
                    if str(user_id) in waifulist.waifu:
                        waifulock, _ = await WaifuLock.get_or_create(
                            message_id=group_id
                        )
                        waifulock.lock[str(waifu_id)] = user_id
                        waifulock.lock[str(user_id)] = waifu_id
                        await waifulock.save()
                        msg += "\ncp 已锁！"
                else:
                    msg = (
                        f"你已经有 CP 了，不许花心哦~{MessageSegment.image(file=await user_img(waifu_id))}"
                        + f"你的 CP：{member['card'] or member['nickname']}"
                    )
            else:
                msg = (
                    tips
                    + MessageSegment.image(file=await user_img(waifu_id))
                    + f"『{member['card'] or member['nickname']}』!"
                )
            await bot.send(event, msg, at_sender=True)
        return
    chooselist = rec.keys() or protect_list.user_id if protect_list else []
    if at and str(at) not in list(chooselist):
        if at == rec.get(str(at)):
            X = HE
            del rec[str(at)]
        else:
            X = random.randint(1, 100)

        if 0 < X <= HE:
            waifu_id = at
            tips = "恭喜你娶到了群友!\n" + tips
        elif HE < X <= BE:
            waifu_id = user_id

    if not waifu_id:
        group_id = event.group_id
        member_list = [
            member
            for member in await bot.get_group_member_list(group_id=group_id)
            if member["user_id"] not in [int(bot.self_id), 2854196310]
        ]
        # lastmonth = event.time - last_sent_time_filter
        rule_out = protect_list.user_id if protect_list else [] or rec.keys()
        waifu_ids = [
            user_id
            for member in member_list
            if str(user_id := member["user_id"]) not in rule_out
            # and member["last_sent_time"] > lastmonth
        ]
        if waifu_ids:
            waifu_id = random.choice(list(waifu_ids))
        else:
            msg = "群友已经被娶光了、\n" + random.choice(no_waifu)
            await bot.send(event, msg, at_sender=True)
            return False
    user_id = event.user_id
    group_id = event.group_id
    if waifu_id == user_id:
        record_cp, _ = await WaifuCP.get_or_create(group_id=group_id)
        record_cp.affect[str(user_id)] = user_id
        await record_cp.save()
        await waifu.finish(random.choice(no_waifu), at_sender=True)
    rec, _ = await WaifuCP.get_or_create(group_id=group_id)
    rec = rec.affect
    record_waifu, _ = await PWaifu.get_or_create(group_id=group_id)
    if str(waifu_id) in rec:
        waifu_cp = rec[str(waifu_id)]
        member = await bot.get_group_member_info(group_id=group_id, user_id=waifu_cp)
        msg = (
            f"人家已经名花有主了~{MessageSegment.image(file=await user_img(waifu_cp))}ta 的 cp："
            + (member["card"] or member["nickname"])
        )
        record_lock, _ = await WaifuLock.get_or_create(group_id=group_id)
        if str(waifu_id) in record_lock.lock.keys():
            await waifu.finish(msg + "\n本对 cp 已锁！", at_sender=True)
        X = random.randint(1, 100)
        if X > NTR:
            record_CP, _ = await WaifuCP.get_or_create(group_id=group_id)
            record_CP.affect[str(user_id)] = user_id
        else:
            rec.pop(str(waifu_cp))
            with contextlib.suppress(Exception):
                record_waifu.waifu.remove(waifu_cp)
            await waifu.send(msg + "\n但是...", at_sender=True)
            await asyncio.sleep(1)
    record_CP, _ = await WaifuCP.get_or_create(group_id=group_id)
    record_CP.affect[str(user_id)] = waifu_id
    record_CP.affect[str(waifu_id)] = user_id
    record_waifu.waifu.append(waifu_id)
    await record_CP.save()
    await record_waifu.save()
    member = await bot.get_group_member_info(group_id=group_id, user_id=waifu_id)
    msg = (
        tips
        + MessageSegment.image(file=await user_img(waifu_id))
        + f"『{(member['card'] or member['nickname'])}』!"
    )
    await waifu.finish(msg, at_sender=True)


# 分手
if waifu_cd_bye > -1:
    cd_bye = {}
    bye = on_command(
        "离婚",
        aliases={"分手"}
    )

    @bye.handle()
    async def _(event: GroupMessageEvent):
        waifu_cp_instance = await WaifuCP.get_or_none(group_id=event.group_id)
        if waifu_cp_instance is not None:
            user_affect = waifu_cp_instance.affect.get(
                str(event.user_id), event.user_id
            )
            if user_affect == event.user_id:
                return
        group_id = str(event.group_id)
        user_id = event.user_id
        cd_bye.setdefault(group_id, {})
        T, N, A = cd_bye[group_id].setdefault(user_id, [0, 0, 0])
        Now = event.time
        cd = T - Now
        if Now > T:
            cd_bye[group_id][user_id] = [Now + waifu_cd_bye, 0, 0]
            rec = await WaifuCP.get(group_id=group_id)
            waifu_set, _ = await PWaifu.get_or_create(group_id=group_id)
            waifu_id = rec.affect[str(user_id)]
            rec.affect.pop(str(user_id))
            rec.affect.pop(str(waifu_id))
            with contextlib.suppress(Exception):
                waifu_set.waifu.remove(waifu_id)
                waifu_set.waifu.remove(user_id)
            record_lock, _ = await WaifuLock.get_or_create(group_id=group_id)
            if group_id in record_lock.lock:
                if waifu_id in record_lock.lock:
                    del record_lock.lock[str(waifu_id)]
                if user_id in record_lock.lock:
                    del record_lock.lock[str(user_id)]
                await record_lock.save()
            await waifu_set.save()
            await rec.save()
            await bye.finish(random.choice(["嗯。", "...", "好。", "哦。", "行。"]))
        else:
            if A > Now:
                A = Now
                N = 0
            else:
                N += 1
            if N == 1:
                msg = f"你的 cd 还有{round(cd/60, 1)}分钟。"
            elif N == 2:
                msg = f"你已经问过了哦~ 你的 cd 还有{round(cd/60, 1)}分钟。"
            elif N < 6:
                T += 10
                msg = f"还问！罚时！你的 cd 还有{round(cd/60, 1)}+10 分钟。"
            elif random.randint(0, 2) == 0:
                await bye.finish("哼！")
            else:
                await bye.finish()
            cd_bye[group_id][user_id] = [T, N, A]
            await bye.finish(msg, at_sender=True)


# 查看娶群友卡池

waifu_list = on_command("查看群友卡池", aliases={"群友卡池"})


@waifu_list.handle()
async def _(bot: Bot, event: GroupMessageEvent):
    group_id = event.group_id
    member_list = await bot.get_group_member_list(group_id=group_id)
    lastmonth = event.time - last_sent_time_filter
    protect_list, _ = await WaifuProtect.get_or_create(group_id=group_id)
    rule_out = protect_list.user_id
    member_list = [
        member
        for member in member_list
        if member["user_id"] not in rule_out
        # and member["last_sent_time"] > lastmonth
        and member_list != 2854196310
    ]
    member_list.sort(key=lambda x: x["last_sent_time"], reverse=True)
    if member_list:
        msg = "卡池：\n——————————————\n"
        for member in member_list[:80]:
            msg += f"{member['card'] or member['nickname']}\n"
        await waifu_list.finish(MessageSegment.image(text_to_png(msg[:-1])))
    else:
        await waifu_list.finish("群友已经被娶光了。下次早点来吧。")


# 查看本群 CP

cp_list = on_command("本群CP", aliases={"本群cp"})


@cp_list.handle()
async def _(bot: Bot, event: GroupMessageEvent):
    group_id = event.group_id
    record_waifu = await PWaifu.get_or_none(group_id=group_id)
    if record_waifu is None or len(record_waifu.waifu) == 0:
        await cp_list.finish("本群暂无 cp 哦~")
    record_CP = await WaifuCP.get_or_none(group_id=group_id)
    if record_CP is None:
        raise ValueError("record_CP is None")
    rec = record_CP.affect
    msg = ""
    for waifu_id in record_waifu.waifu:
        logger.info(waifu_id)
        user_id = rec.get(str(waifu_id))
        if not user_id:
            continue
        try:
            member = await bot.get_group_member_info(group_id=group_id, user_id=user_id)
            niknameA = member["card"] or member["nickname"]
        except Exception:
            niknameA = ""
        try:
            member = await bot.get_group_member_info(
                group_id=group_id, user_id=waifu_id
            )
            niknameB = member["card"] or member["nickname"]
        except Exception:
            niknameB = ""

        msg += f"♥ {niknameA} | {niknameB}\n"
    await cp_list.finish(
        MessageSegment.image(text_to_png("本群 CP：\n——————————————\n" + msg[:-1]))
    )


yinpa = on_command("透群友")


@yinpa.handle(
    parameterless=[
        Cooldown(
            cooldown=5,
            prompt="太快啦，慢点慢点",
            isolate_level=CooldownIsolateLevel.USER,
        )
    ]
)
async def _(bot: Bot, event: GroupMessageEvent):
    # 不能透机器人
    if event.to_me:
        await bot.send(event, "不行！", at_sender=True)
        return False
    user_id = event.user_id
    group_id = event.group_id
    protect_list, _ = await WaifuProtect.get_or_create(group_id=group_id)
    protect_set = protect_list.user_id
    if user_id in protect_set:
        return False
    at = get_message_at(event.message)
    yinpa_id = None
    tips = "伱的涩涩对象是、"
    if at:
        at = at[0]
        if at in protect_set:
            return False

        if at == user_id:
            member = await bot.get_group_member_info(group_id=group_id, user_id=user_id)
            msg = (
                f"恭喜你涩到了你自己！{MessageSegment.image(file=await user_img(user_id))}"
                + f"『{member['card'] or member['nickname']}』!"
            )
            await bot.send(event, msg, at_sender=True)
            return False
        X = random.randint(1, 100)
        record_CP, _ = await WaifuCP.get_or_create(group_id=group_id)
        if at == record_CP.affect.get(str(user_id), 0):
            if 0 < X <= yinpa_CP:
                yinpa_id = at
                tips = "恭喜你涩到了你的老婆！"
            else:
                await bot.send(event, "你的老婆拒绝和你涩涩！", at_sender=True)
                return False
        elif 0 < X <= yinpa_HE:
            yinpa_id = at
            tips = "恭喜你涩到了群友！"
        elif yinpa_HE < X <= yinpa_BE:
            yinpa_id = user_id
    if not yinpa_id:
        member_list = await bot.get_group_member_list(group_id=group_id)
        lastmonth = event.time - last_sent_time_filter
        yinpa_ids = [
            user_id
            for member in member_list
            if (user_id := member["user_id"]) not in protect_set
            # and member["last_sent_time"] > lastmonth
            and member["user_id"] != int(bot.self_id)
            and member["user_id"] != 2854196310
        ]
        if yinpa_ids:
            yinpa_id = random.choice(yinpa_ids)
        else:
            return False
    group_id = event.group_id
    user_id = event.user_id
    if yinpa_id == user_id:
        await yinpa.finish("不可以涩涩！", at_sender=True)
    else:
        record_yinpa1, _ = await Waifuyinppa1.get_or_create(user_id=user_id)
        record_yinpa1.count += 1
        await record_yinpa1.save()
        record_yinpa2, _ = await Waifuyinppa2.get_or_create(user_id=yinpa_id)
        record_yinpa2.count += 1
        await record_yinpa2.save()
        member = await bot.get_group_member_info(group_id=group_id, user_id=yinpa_id)
        msg = (
            tips
            + MessageSegment.image(file=await user_img(yinpa_id))
            + f"『{(member['card'] or member['nickname'])}』!"
        )
        await yinpa.finish(msg, at_sender=True)


# 查看涩涩记录

yinpa_list = on_command("涩涩记录", aliases={"色色记录"})


@yinpa_list.handle()
async def _(bot: Bot, event: GroupMessageEvent):
    group_id = event.group_id
    # 输出卡池
    member_list = await bot.get_group_member_list(group_id=event.group_id)
    lastmonth = event.time - last_sent_time_filter
    protect_set, _ = await WaifuProtect.get_or_create(group_id=group_id)
    member_list = [
        member
        for member in member_list
        if member["user_id"] not in protect_set.user_id
        # and member["last_sent_time"] > lastmonth
    ]
    member_list.sort(key=lambda x: x["last_sent_time"], reverse=True)
    msg = "卡池：\n——————————————\n" + "\n".join(
        [(member["card"] or member["nickname"]) for member in member_list[:80]]
    )
    msg_list = [MessageSegment.image(text_to_png(msg))]
    # 输出透群友记录

    record = [
        ((member["card"] or member["nickname"]), times.count)
        for member in member_list
        if (times := await Waifuyinppa1.get_or_none(user_id=member["user_id"]))
    ]
    for nickname, times in record:
        logger.info(f"{nickname} {times}")
    record.sort(key=lambda x: x[1], reverse=True)
    if msg := "\n".join(
        [
            f"[align=left]{nickname}[/align][align=right]今日透群友 {times} 次[/align]"
            for nickname, times in record
        ]
    ):
        msg_list.append(
            MessageSegment.image(bbcode_to_png("涩涩记录①：\n——————————————\n" + msg))
        )

    # 输出被透记录

    record = [
        ((member["card"] or member["nickname"]), times.count)
        for member in member_list
        if (times := await Waifuyinppa2.get_or_none(user_id=member["user_id"]))
    ]
    record.sort(key=lambda x: x[1], reverse=True)

    msg = "涩涩记录②：\n——————————————\n"
    if msg := "\n".join(
        [
            f"[align=left]{nickname}[/align][align=right]今日被透 {times} 次[/align]"
            for nickname, times in record
        ]
    ):
        msg_list.append(
            MessageSegment.image(bbcode_to_png("涩涩记录②：\n——————————————\n" + msg)),
        )

    def to_json(msg: MessageSegment):
        return {
            "type": "node",
            "data": {"name": Bot_NICKNAME, "uin": bot.self_id, "content": msg},
        }

    messages = [to_json(msg_temp) for msg_temp in msg_list]
    await bot.send_group_forward_msg(group_id=event.group_id, messages=messages)
