# 获取所有群消息


from nonebot import on_command
from nonebot.adapters.onebot.v11 import Bot

# 事件响应函数
rlist = on_command("removegrouplist")


def condition(group_info):
    member_count = group_info["member_count"]
    group_name: str = group_info["group_name"]
    return (
        member_count < 15
        or (("机器人" in group_name or "ai" in group_name or "test" in group_name) and len(group_name) < 8)
        or group_name.count("、") >= 2
        or group_info['group_id'] == '966016220'
    )


@rlist.handle()
async def _(bot: Bot):
    # 获取群列表，获取每一个群的信息
    # 如果member_count小于7，就加入列表然后显示send出来

    # 获取群列表
    group_list = await bot.get_group_list()
    # 获取群信息
    for group_info in group_list:
        # 获取群成员数量
        member_count = group_info["member_count"]
        # print(member_count)
        # 如果群成员数量小于7
        if condition(group_info):
            await rlist.send(
                f"群号：{group_info['group_id']} 群名：{group_info['group_name']} 群成员数量：{member_count}"
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
    await rgroup.finish("已发送所有群信息")
