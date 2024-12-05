# 获取所有群消息


from nonebot import logger, on_command
from nonebot.adapters.onebot.v11 import Bot
from sympy import loggamma

# 事件响应函数
rlist = on_command("removegrouplist")


def condition(group_info):
    member_count = group_info["member_count"]
    group_name: str = group_info["group_name"]
    return (
        member_count < 15
        or (
            ("机器人" in group_name or "ai" in group_name or "test" in group_name)
            and len(group_name) < 8
        )
        or group_name.count("、") >= 2
    ) and group_info["group_id"] != 966016220


@rlist.handle()
async def _(bot: Bot):
    # 获取群列表，获取每一个群的信息
    # 如果member_count小于7，就加入列表然后显示send出来

    # 获取群列表
    group_list = await bot.get_group_list()
    # 获取群信息
    await rlist.send("开始检查人数类")
    for group_info in group_list:
        # 获取群成员数量
        member_count = group_info["member_count"]
        # print(member_count)
        # 如果群成员数量小于7
        if condition(group_info):
            await rlist.send(
                f"群号：{group_info['group_id']} 群名：{group_info['group_name']} 群成员数量：{member_count}"
            )
    # 检查每个群的人有没有自己的好友
    await rlist.send("开始检查好友类")

    # 提前获取好友列表和群成员列表缓存
    friend_list = await bot.get_friend_list()
    friend_list_qq = [friend["user_id"] for friend in friend_list]

    group_member_lists = {}
    for group_info in group_list:
        group_member_list = await bot.get_group_member_list(
            group_id=group_info["group_id"]
        )
        group_member_lists[group_info["group_id"]] = [
            member["user_id"] for member in group_member_list
        ]
        # 输出进度，百分比和当前群号和数量
        logger.info(
            f"获取所有群的成员进度已完成{group_list.index(group_info)/len(group_list)*100:.2f}% 已完成：{group_list.index(group_info)}/{len(group_list)}"
        )

    for group_info in group_list:
        # 获取群成员数量
        member_count = group_info["member_count"]
        group_member_list_qq = group_member_lists[group_info["group_id"]]

        if not set(friend_list_qq) & set(group_member_list_qq):
            await rlist.send(
                f"群号：{group_info['group_id']} 群名：{group_info['group_name']} 群成员数量：{member_count}"
            )
        # 输出日志进度,百分比和当前群号和（数量/总数），输出两个set的交集在群里的占比
        logger.info(
            f"已完成{group_list.index(group_info)/len(group_list)*100:.2f}% 群号：{group_info['group_id']} 群名：{group_info['group_name']} 群成员数量：{member_count} 交集占比：{len(set(friend_list_qq) & set(group_member_list_qq))/len(set(friend_list_qq)):.2f} 交集数量：{len(set(friend_list_qq) & set(group_member_list_qq))}"
        )
    await rlist.finish("已发送所有群信息")


rgroup = on_command("removegroup")


@rgroup.handle()
async def _(bot: Bot):
    # 获取群列表，获取每一个群的信息
    # 如果member_count小于7，就加入列表然后显示send出来

    # 获取群列表
    group_list = await bot.get_group_list()
    # 获取群信息
    await rgroup.send("开始检查人数类")
    for group_info in group_list:
        # 获取群成员数量
        member_count = group_info["member_count"]
        # print(member_count)
        # 如果群成员数量小于7
        if condition(group_info):
            await bot.set_group_leave(group_id=group_info["group_id"])
            await rgroup.send(
                f"群号：{group_info['group_id']} 群名：{group_info['group_name']} 群成员数量：{member_count} 已移除"
            )
    # 检查每个群的人有没有自己的好友
    await rgroup.send("开始检查好友类")

    # 提前获取好友列表和群成员列表缓存
    friend_list = await bot.get_friend_list()
    friend_list_qq = [friend["user_id"] for friend in friend_list]

    group_member_lists = {}
    for group_info in group_list:
        group_member_list = await bot.get_group_member_list(
            group_id=group_info["group_id"]
        )
        group_member_lists[group_info["group_id"]] = [
            member["user_id"] for member in group_member_list
        ]
        # 输出进度，百分比和当前群号和数量
        logger.info(
            f"获取所有群的成员进度已完成{group_list.index(group_info)/len(group_list)*100:.2f}% 已完成：{group_list.index(group_info)}/{len(group_list)}"
        )

    for group_info in group_list:
        # 获取群成员数量
        member_count = group_info["member_count"]
        group_member_list_qq = group_member_lists[group_info["group_id"]]

        if not set(friend_list_qq) & set(group_member_list_qq):
            await bot.set_group_leave(group_id=group_info["group_id"])
            await rgroup.send(
                f"群号：{group_info['group_id']} 群名：{group_info['group_name']} 群成员数量：{member_count} 已移除"
            )
        # 输出日志进度,百分比和当前群号和（数量/总数），输出两个set的交集在群里的占比
        logger.info(
            f"已完成{group_list.index(group_info)/len(group_list)*100:.2f}% 群号：{group_info['group_id']} 群名：{group_info['group_name']} 群成员数量：{member_count} 交集占比：{len(set(friend_list_qq) & set(group_member_list_qq))/len(set(friend_list_qq)):.2f} 交集数量：{len(set(friend_list_qq) & set(group_member_list_qq))}"
        )

    await rgroup.finish("已发送所有群信息")
