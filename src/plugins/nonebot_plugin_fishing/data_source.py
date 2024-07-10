import random
import time
from typing import List

import ujson as json
from nonebot.adapters.onebot.v11 import GroupMessageEvent, PrivateMessageEvent
from nonebot_plugin_orm import get_session
from sqlalchemy import select, update, bindparam

from .config import config
from .model import FishingRecord, FishingSwitch

fishing_coin_name = config.fishing_coin_name
fish_rotten = config.fish_rotten
fish_moldy = config.fish_moldy
fish_common = config.fish_common
fish_golden = config.fish_golden
fish_void = config.fish_void
fish_fire = config.fish_hidden_fire

fish = {
    "普通": {"weight": 100, "price_mpr": 0.1, "long": (1, 30), "fish": fish_common},
    "腐烂": {"weight": 20, "price_mpr": 0.05, "long": (15, 45), "fish": fish_rotten},
    "发霉": {"weight": 15, "price_mpr": 0.08, "long": (20, 150), "fish": fish_moldy},
    "金": {"weight": 5, "price_mpr": 0.15, "long": (125, 800), "fish": fish_golden},
    "虚空": {"weight": 3, "price_mpr": 0.2, "long": (800, 4000), "fish": fish_void},
    "隐火": {"weight": 1, "price_mpr": 0.2, "long": (1000, 4000), "fish": fish_fire},
}


async def update_sql():
    delete_fish = [
        "贴图错误鱼发霉的鲤鱼",
        "多宝鱼龙利鱼墨鱼",
        "腐烂的孙笑川鱼",
        "虚空乌贼虚空鳗鱼",
        "黄花鱼墨鱼",
    ]
    session = get_session()
    async with session.begin():
        fishes_records = await session.execute(select(FishingRecord))
        update_data = []

        for fishes_record in fishes_records.scalars():
            load_fishes = json.loads(fishes_record.fishes)
            fish_removed = False

            for fish_name in delete_fish:
                if fish_name in load_fishes:
                    del load_fishes[fish_name]
                    fish_removed = True

            if fish_removed or fishes_record.coin != fishes_record.count_coin:
                dump_fishes = json.dumps(load_fishes)
                update_data.append(
                    {
                        "user_id": fishes_record.user_id,
                        "fishes": dump_fishes,
                        "count_coin": fishes_record.coin,
                    }
                )

        if update_data:
            await session.execute(
                update(FishingRecord)
                .where(FishingRecord.user_id == bindparam("user_id"))
                .values(fishes=bindparam("fishes"), count_coin=bindparam("count_coin")),
                update_data,
            )
    await session.commit()


def choice() -> tuple[str, int]:
    # 挑品质
    # 将字典所有键转换为列表
    fish_quality = list(fish.keys())
    fish_quality_weight = [fish[key]["weight"] for key in fish_quality]
    quality = random.choices(fish_quality, weights=fish_quality_weight)[0]
    # 挑鱼
    return random.choice(fish[quality]["fish"]), random.randint(
        fish[quality]["long"][0], fish[quality]["long"][1]
    )


def get_quality(fish_name: str) -> str:
    """获取鱼的品质"""
    for quality in fish:
        if fish_name in fish[quality]["fish"]:
            return quality
    raise ValueError(f"未知的鱼：{fish_name}")


def get_price(fish_name: str, fish_long: int) -> float:
    """获取鱼的价格"""
    for quality in fish:
        if fish_name in fish[quality]["fish"]:
            return fish[quality]["price_mpr"] * fish_long
    raise ValueError(f"未知的鱼：{fish_name}")


async def save_fish(user_id: str, fish_name: str, fish_long: int) -> None:
    """向数据库写入鱼以持久化保存"""
    time_now = int(time.time())
    fishing_limit = config.fishing_limit
    session = get_session()
    async with session.begin():
        records = await session.execute(select(FishingRecord))
        for record in records.scalars():
            if record.user_id == user_id:
                loads_fishes: dict[str, List[int]] = json.loads(record.fishes)
                try:
                    loads_fishes[fish_name].append(fish_long)
                except KeyError:
                    loads_fishes[fish_name] = [fish_long]
                dump_fishes = json.dumps(loads_fishes)
                user_update = (
                    update(FishingRecord)
                    .where(FishingRecord.user_id == user_id)
                    .values(
                        time=time_now + fishing_limit,
                        frequency=record.frequency + 1,
                        fishes=dump_fishes,
                    )
                )
                await session.execute(user_update)
                await session.commit()
                return
        data = {fish_name: [fish_long]}
        dump_fishes = json.dumps(data)
        new_record = FishingRecord(
            user_id=user_id,
            time=time_now + fishing_limit,
            frequency=1,
            fishes=dump_fishes,
            coin=0,
        )
        session.add(new_record)
        await session.commit()


async def get_stats(user_id: str) -> str:
    """获取钓鱼统计信息（总长度，次数，次元币总数）"""
    session = get_session()
    async with session.begin():
        fishing_records = await session.execute(select(FishingRecord))
        return next(
            (
                f"共钓到鱼次数 {fishing_record.frequency} 次\n"
                f"背包内鱼总长度 {sum(sum(fish_long) for fish_long in json.loads(fishing_record.fishes).values())}cm\n"
                f"总共获得过 {fishing_record.count_coin} 次元币"
                for fishing_record in fishing_records.scalars()
                if fishing_record.user_id == user_id
            ),
            "你还没有钓过鱼，快去钓鱼吧",
        )


def print_backpack(backpack: dict[str, List[int]]) -> list:
    """输出背包内容"""
    backpack_list = list(backpack.items())

    return [
        "\n".join(
            [
                f"{fish_name}:\n  个数:{len(fish_info)}\n  总长度:{sum(fish_info)}"
                for fish_name, fish_info in backpack_list[i : i + 20]
            ]
        )
        for i in range(0, len(backpack_list), 20)
    ]


async def get_backpack(user_id: str) -> str | list:
    """从数据库查询背包内容"""
    session = get_session()
    async with session.begin():
        fishes_records = await session.execute(select(FishingRecord))
        for fishes_record in fishes_records.scalars():
            if fishes_record.user_id == user_id:
                load_fishes = json.loads(fishes_record.fishes)
                return (
                    print_backpack(load_fishes) if load_fishes else "你的背包里空无一物"
                )
        return "你的背包里空无一物"


async def sell_quality_fish(user_id: str, quality: str) -> str:
    """卖出指定品质的鱼"""
    session = get_session()
    async with session.begin():
        fishes_records = await session.execute(select(FishingRecord))
        for fishes_record in fishes_records.scalars():
            if fishes_record.user_id == user_id:  # 对应的用户
                load_fishes = json.loads(fishes_record.fishes)
                if not load_fishes:
                    break
                if quality not in [get_quality(fish_name) for fish_name in load_fishes]:
                    return f"你的背包里没有 {quality} 鱼了"
                price = sum(
                    round(get_price(fish_name, sum(fish_long)), 2)
                    for fish_name, fish_long in load_fishes.items()
                    if get_quality(fish_name) == quality
                )
                coin = fishes_record.coin + price
                count_coin = fishes_record.count_coin + price
                load_fishes: dict = {
                    fish_name: fish_long
                    for fish_name, fish_long in load_fishes.items()
                    if get_quality(fish_name) != quality
                }
                dump_fishes = json.dumps(load_fishes)
                user_update = (
                    update(FishingRecord)
                    .where(FishingRecord.user_id == user_id)
                    .values(fishes=dump_fishes, coin=coin, count_coin=count_coin)
                )
                await session.execute(user_update)
                await session.commit()
                return f"你卖出了所有 {quality} 鱼，获得了 {price} {fishing_coin_name}"
        return "你的背包里空无一物"


async def sell_all_fish(user_id: str) -> str:
    """卖出所有鱼"""
    session = get_session()
    async with session.begin():
        fishes_records = await session.execute(select(FishingRecord))
        for fishes_record in fishes_records.scalars():
            if fishes_record.user_id == user_id:
                load_fishes = json.loads(fishes_record.fishes)
                if not load_fishes:
                    break
                price = sum(
                    round(get_price(fish_name, sum(fish_long)), 2)
                    for fish_name, fish_long in load_fishes.items()
                )
                coin = fishes_record.coin + price
                count_coin = fishes_record.count_coin + price
                user_update = (
                    update(FishingRecord)
                    .where(FishingRecord.user_id == user_id)
                    .values(fishes="{}", coin=coin, count_coin=count_coin)
                )
                await session.execute(user_update)
                await session.commit()
                return f"你卖出了所有鱼，获得了 {price} {fishing_coin_name}"
        return "你的背包里空无一物"


async def sell_fish(user_id: str, fish_name: str) -> str:
    """
    卖鱼 (一次性卖完)

    参数：
      - user_id: 将要卖鱼的用户唯一标识符，用于区分谁正在卖鱼
      - fish_name: 将要卖鱼的鱼名称

    返回：
      - (str): 待回复的文本
    """
    session = get_session()
    async with session.begin():
        fishes_records = await session.execute(select(FishingRecord))
        for fishes_record in fishes_records.scalars():
            if fishes_record.user_id == user_id:
                load_fishes = json.loads(fishes_record.fishes)
                if fish_name not in load_fishes:
                    return "你的背包里没有这种鱼"
                fish_long = load_fishes[fish_name]
                price = round(get_price(fish_name, sum(fish_long)), 2)
                coin = fishes_record.coin + price
                count_coin = fishes_record.count_coin + price
                del load_fishes[fish_name]
                dump_fishes = json.dumps(load_fishes)
                user_update = (
                    update(FishingRecord)
                    .where(FishingRecord.user_id == user_id)
                    .values(fishes=dump_fishes, coin=coin, count_coin=count_coin)
                )
                await session.execute(user_update)
                await session.commit()
                return f"你卖出了 {fish_name}×{len(fish_long)}，获得了 {price} {fishing_coin_name}"
        return "你的背包里空无一物"


async def get_balance(user_id: str) -> str:
    """获取余额"""
    session = get_session()
    async with session.begin():
        fishes_records = await session.execute(select(FishingRecord))
        return next(
            (
                f"你有 {fishes_record.coin} {fishing_coin_name}"
                for fishes_record in fishes_records.scalars()
                if fishes_record.user_id == user_id
            ),
            "你什么也没有 :)",
        )


async def switch_fish(event: GroupMessageEvent | PrivateMessageEvent) -> bool:
    """钓鱼开关切换，没有就创建"""
    if isinstance(event, PrivateMessageEvent):
        return True
    session = get_session()
    async with session.begin():
        switchs = await session.execute(
            select(FishingSwitch).where(FishingSwitch.group_id == event.group_id)
        )
        switch = switchs.scalars().first()
        if switch:
            result = switch.switch
            user_update = (
                update(FishingSwitch)
                .where(FishingSwitch.group_id == event.group_id)
                .values(switch=not result)
            )
            await session.execute(user_update)
            await session.commit()
            return not result
        new_switch = FishingSwitch(group_id=event.group_id, switch=False)
        session.add(new_switch)
        await session.commit()
        return False


async def get_switch_fish(event: GroupMessageEvent | PrivateMessageEvent) -> bool:
    """获取钓鱼开关"""
    if isinstance(event, PrivateMessageEvent):
        return True
    session = get_session()
    async with session.begin():
        switchs = await session.execute(
            select(FishingSwitch).where(FishingSwitch.group_id == event.group_id)
        )
        switch = switchs.scalars().first()
        return switch.switch if switch else True
