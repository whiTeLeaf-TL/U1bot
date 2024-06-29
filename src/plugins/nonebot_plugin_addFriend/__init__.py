
import json
from asyncio import sleep
from datetime import datetime

from nonebot import on_command, on_request
from nonebot.adapters import Message
from nonebot.adapters.onebot.v11 import (
    Bot,
    FriendRequestEvent,
    GroupRequestEvent,
    MessageEvent,
    RequestEvent,
)
from nonebot.params import CommandArg
from nonebot.permission import SUPERUSER

from . import configUtil
from .configUtil import (
    blackLogPath,
    check_dict_key_bot_id,
    config,
    configPath,
    numDict,
    numDictPath,
    requestorDict,
    requestorDictPath,
    writeData,
)
from .utils import (
    filterFriend,
    getExist,
    getReferIdList,
    isNormalAdd,
    parseMsg,
    parseTime,
    sendMsg,
    writeLog,
    writeTime,
)

# 初始化完毕，num 文件单独初始化
parseRequest = on_request(priority=1, block=True)


@parseRequest.handle()
async def _(bot: Bot, event: RequestEvent):
    check_dict_key_bot_id(config, requestorDict, numDict, bot)
    now = datetime.now()
    time = str(now)
    if isinstance(event, FriendRequestEvent):
        notice_msg = config[bot.self_id]["friend_msg"]["notice_msg"]
        welcome_msg = config[bot.self_id]["friend_msg"]["welcome_msg"]
        id = str(event.user_id)
        autoType = 'friend'
        agreeAutoApprove = config[bot.self_id]['agreeAutoApprove'][autoType]
        addInfo = await bot.get_stranger_info(user_id=int(id), no_cache=True)
        msg = f"{id}{notice_msg+event.comment}\n时间:{time}"
    elif isinstance(event, GroupRequestEvent):
        if event.sub_type != 'invite':
            return
        notice_msg = config[bot.self_id]["group_msg"]["notice_msg"]
        welcome_msg = config[bot.self_id]["group_msg"]["welcome_msg"]
        id = str(event.group_id)
        autoType = 'group'
        agreeAutoApprove = config[bot.self_id]['agreeAutoApprove'][autoType]
        await sleep(0.5)
        addInfo = await bot.get_group_info(group_id=int(id), no_cache=True)
        msg = f'群号{id}，{event.get_user_id()+notice_msg+event.comment}\n时间:{time}'
        if addInfo["member_count"] != 0 or agreeAutoApprove != 0:
            status = '\n或因群人数少，已经添加成功'
            await sendMsg(bot, config[bot.self_id]['recipientList'], msg+status, 0)
            await bot.send_private_msg(user_id=event.user_id, message=welcome_msg)
            return
    else:
        return
    agreeAutoApprove, status = isNormalAdd(
        config[bot.self_id], autoType, addInfo, agreeAutoApprove)  # 正常添加判断，过滤无意义添加，类似 xx 通知群
    if agreeAutoApprove == -1:  # 黑名单结果
        await event.reject(bot)
        # 黑名单警告，转发给设定的人
        await sendMsg(bot, config[bot.self_id]['recipientList'], msg+status, 0)
        forwardId = config[bot.self_id]["blackDict"]["forward"].get(id)
        if forwardId is not None and autoType == "group":
            friendList = await getReferIdList(bot, 'user_id')
            if forwardId in friendList:
                await bot.send_private_msg(user_id=forwardId, message=msg+status)
            else:
                del config[bot.self_id]["blackDict"]["forward"][id]
            writeLog(blackLogPath, msg+status+'\n')
        return
    # 验证信息
    if not filterFriend(event.comment, autoType, config[bot.self_id]['allowAddFriednText']):
        status = '\n未通过验证消息，已拒绝'
        # 不记录
        await sendMsg(bot, config[bot.self_id]['recipientList'], msg+status, 0)
        await event.reject(bot)
        return
    num = parseTime(config[bot.self_id]['numControl'],
                    numDict[bot.self_id][autoType], now)
    if agreeAutoApprove == 0 or num == -1:
        if num == -1:
            status = f"\n此时增满{config[bot.self_id]['numControl']['maxNum']}人，未能再自动添加"
        else:
            status = '\n未允许自动添加'
        requestorDict[bot.self_id][autoType][id] = {'flag': event.flag, 'comment': event.comment,
                                                    "notice_msg": notice_msg, 'staus': status, 'requestorId': event.user_id, 'time': time}
        writeData(requestorDictPath, requestorDict)
        await sendMsg(bot, config[bot.self_id]['recipientList'], msg+status, 0)
    else:
        # 既自动添加又条件合适
        writeTime(numDictPath, numDict)
        await event.approve(bot)
        await sendMsg(bot, config[bot.self_id]['recipientList'], msg+status, 0)
        # 等待腾讯服务器更新
        await sleep(1.5)
        await bot.send_private_msg(user_id=event.user_id, message=welcome_msg)


againReadConfig = on_command("重载配置", aliases={
                             "更改自动同意", "更改最大加数量", "更改加时间", "更改加时间单位", "更改查看加返回数量"}, priority=5, block=True, permission=SUPERUSER)


@againReadConfig.handle()
# 下个版本把其他俩 json 也重载一下，不知道为啥这次就不想改
async def _(bot: Bot, event: MessageEvent, args: Message = CommandArg()):
    with open(configPath, 'r', encoding='utf-8') as fp:
        configUtil.config = json.load(fp)
    check_dict_key_bot_id(configUtil.config, requestorDict, numDict, bot)
    text = event.get_plaintext().strip()
    argsText = args.extract_plain_text().strip()
    commandText = getExist('', text, argsText)
    if isinstance(commandText, bool):
        return
    if '群聊' in argsText:
        argsText = argsText.replace('群聊', '').strip()
        autoType = 'group'
    elif '好友' in argsText:
        argsText = argsText.replace('好友', '').strip()
        autoType = 'friend'
    else:
        autoType = 'all'
    if "更改自动同意" in commandText:
        resMsg = await handle_auto_approve_command(bot, argsText, autoType)

    elif "更改最大加数量" in commandText:
        resMsg = handle_max_num_command(bot, argsText, autoType)
    elif "更改最大加时间" in commandText:
        resMsg = handle_max_time_command(bot, argsText, autoType)
    elif "更改加时间单位" in commandText:
        resMsg = handle_time_unit_command(bot, argsText, autoType)
    elif "更改查看加返回数量" in commandText:
        resMsg = handle_view_num_command(bot, argsText)
    else:
        resMsg = f'重载成功:\n{configUtil.config[bot.self_id]}'
    if '重载配置' not in commandText:
        writeData(configPath, configUtil.config)
    resMsg = await parseMsg(resMsg)
    await againReadConfig.finish(resMsg)


def handle_view_num_command(bot, argsText):
    if argsText.isdigit() and 0 < int(argsText) < 120:
        configUtil.config[bot.self_id]['maxViewNum'] = int(argsText)
    return f"更改成功，为\n{configUtil.config[bot.self_id]['maxViewNum']}"


def handle_time_unit_command(bot, argsText, autoType):
    if '时' in argsText:
        configUtil.config[bot.self_id]['numControl'][autoType]['unit'] = 'h'
    elif '分' in argsText:
        configUtil.config[bot.self_id]['numControl'][autoType]['unit'] = 'm'
    else:
        configUtil.config[bot.self_id]['numControl'][autoType]['unit'] = 'd'
    return f'更改成功，为{configUtil.config[bot.self_id]["numControl"][autoType]["unit"]}'


def handle_max_time_command(bot, argsText, autoType):
    if argsText.isdigit():
        time = int(argsText)
        if time > 0:
            configUtil.config[bot.self_id]['numControl'][autoType]['time'] = time
    return f'更改成功，为{configUtil.config[bot.self_id]["numControl"][autoType]["time"]}'


def handle_max_num_command(bot, argsText, autoType):
    if argsText.isdigit():
        maxNum = int(argsText)
        if maxNum > 0:
            configUtil.config[bot.self_id]['numControl'][autoType]['maxNum'] = maxNum
        else:
            configUtil.config[bot.self_id]['numControl'][autoType]['maxNum'] = 0
    return f'更改成功，为{configUtil.config[bot.self_id]["numControl"][autoType]["maxNum"]}'


async def handle_auto_approve_command(bot, argsText, autoType):
    if argsText.isdigit() and autoType != 'all':
        if int(argsText) > 0:
            configUtil.config[bot.self_id]['agreeAutoApprove'][autoType] = 1
        else:
            configUtil.config[bot.self_id]['agreeAutoApprove'][autoType] = 0
    elif autoType == 'all':
        setList = argsText.split()
        i = 0
        setKeyList = list(
            configUtil.config[bot.self_id]['agreeAutoApprove'].keys())
        for setarg in setList[:2]:
            if setarg.isdigit():
                if int(setarg) > 0:
                    configUtil.config[bot.self_id]['agreeAutoApprove'][setKeyList[i]] = 1
                else:
                    configUtil.config[bot.self_id]['agreeAutoApprove'][setKeyList[i]] = 0
            i += 1
    else:
        await againReadConfig.finish('格式')
    return f'更改成功，为\n{configUtil.config[bot.self_id]["agreeAutoApprove"]}'


addFriend = on_command("同意加", aliases={'拒绝加', '查看加'}, priority=5, block=True)


@addFriend.handle()
async def _(bot: Bot, event: MessageEvent, args: Message = CommandArg()):
    check_dict_key_bot_id(config, requestorDict, numDict, bot)
    user_id = event.get_user_id()

    if user_id not in config[bot.self_id]['recipientList']:
        await addFriend.finish('无权限')

    text = event.get_plaintext().strip()
    args_text = args.extract_plain_text().strip()
    command_text = getExist("", text, args_text)
    if isinstance(command_text, bool):
        return
    auto_type = 'group' if '群' in args_text else 'friend'
    res_msg = ''
    status = '格式错误'
    if "同意加" in command_text:
        approve = True
        status = '添加成功'
    elif '拒绝' in command_text:
        approve = False
        status = '拒绝成功'
    else:
        num = int(args_text) if args_text.isdigit(
        ) else config[bot.self_id]['maxViewNum']
        requestor_infos = str(
            list(requestorDict[bot.self_id][auto_type].items())[:num])
        res_msg = await parseMsg(requestor_infos)
        await addFriend.finish(res_msg)

    if args_text == '':
        await addFriend.finish('格式')

    qq_or_group_id = args_text.split()[0]

    if qq_or_group_id not in requestorDict[bot.self_id][auto_type]:
        await addFriend.finish('没有此请求')

    flag = requestorDict[bot.self_id][auto_type][qq_or_group_id]['flag']
    notice_msg = requestorDict[bot.self_id][auto_type][qq_or_group_id]['notice_msg']
    comment = requestorDict[bot.self_id][auto_type][qq_or_group_id]['comment']
    requestor_id = requestorDict[bot.self_id][auto_type][qq_or_group_id]['requestorId']
    time = requestorDict[bot.self_id][auto_type][qq_or_group_id]['time']
    msg_type = ''
    try:
        if auto_type == "group":
            res_msg = f'群号{qq_or_group_id}，邀请者{requestor_id}{notice_msg}{comment}\n时间:{time}\n'
            msg_type = 'group_msg'
            group_list = await getReferIdList(bot)

            if int(qq_or_group_id) in group_list:
                status = '已经添加成功，勿复添加'
            else:
                await bot.set_group_add_request(flag=flag, sub_type="add", approve=approve)
        else:
            res_msg = f'{qq_or_group_id}{notice_msg}{comment}\n{time}\n'
            msg_type = 'friend_msg'
            friend_list = await getReferIdList(bot, 'user_id')

            if int(qq_or_group_id) in friend_list:
                status = '已经添加成功，勿复添加'
            else:
                if len(args_text) >= 2 and args_text[1] != '' and approve:
                    remark = args_text[1]
                    await bot.set_friend_add_request(flag=flag, approve=approve, remark=remark)
                else:
                    await bot.set_friend_add_request(flag=flag, approve=approve)
    except Exception:
        status = '为何手动添加而后又删好友或退群又来这里同意？'
    finally:
        del requestorDict[bot.self_id][auto_type][qq_or_group_id]
        writeData(requestorDictPath, requestorDict)

    res_msg += status
    await addFriend.send(res_msg)

    if status == '添加成功':
        await sleep(1.5)  # 等待腾讯数据更新
        welcome_msg = config[bot.self_id][msg_type]['welcome_msg']
        await bot.send_private_msg(user_id=requestor_id, message=welcome_msg)


delRequestorDict = on_command(
    "清理请求表", priority=5, block=True, permission=SUPERUSER)


@delRequestorDict.handle()
async def check_outdate(bot: Bot):
    check_dict_key_bot_id(config, requestorDict, numDict, bot)
    delList = []
    for requestorType in requestorDict:
        if requestorType != 'friend':
            ReferIdList = await getReferIdList(bot, 'group_id')
        else:
            ReferIdList = await getReferIdList(bot, 'user_id')
        requestorList = list(requestorDict[bot.self_id][requestorType])
        for requestor in requestorList:
            if int(requestor) in ReferIdList:
                delList.append(requestor)
                del requestorDict[bot.self_id][requestorType][requestor]
    writeData(requestorDictPath, requestorDict)
    msg = '已清理如下:\n'+str(delList)[1:-1].replace(', ', '  ')
    await delRequestorDict.send(msg)


reFriendReqNum = on_command(
    "重置请求次数", block=True, priority=5, permission=SUPERUSER)


@reFriendReqNum.handle()
async def _(bot: Bot, args: Message = CommandArg()):
    check_dict_key_bot_id(config, requestorDict, numDict, bot)
    argsText = args.extract_plain_text().strip()
    if '群聊' in argsText:
        argsText = argsText.replace('群聊', '').strip()
        autoType = 'group'
    elif '好友' in argsText:
        argsText = argsText.replace('好友', '').strip()
        autoType = 'friend'
    else:
        autoType = 'all'
    maxnum = config[bot.self_id]['numControl'][autoType]['maxNum']
    now = datetime.now()
    if parseTime(config[bot.self_id]['numControl'][autoType], numDict[bot.self_id][autoType], now) != -1:
        await reFriendReqNum.send(message=f'未增满{maxnum}人，人数为{numDict[bot.self_id][autoType]["count"]}上次添加时间{now}')
    argsText = argsText.replace('为', '').strip()
    if argsText.isdigit():
        numDict[bot.self_id][autoType]['count'] = int(argsText)
    else:
        numDict[bot.self_id][autoType]['count'] = 0
    numDict[bot.self_id][autoType]['time'] = now
    writeTime(numDictPath, numDict)
    await reFriendReqNum.finish(f'重置成功，为{numDict[bot.self_id][autoType]["count"]}')
addRecipient = on_command(
    "添加请求接收者", aliases={"删除请求接收者"}, block=True, priority=5, permission=SUPERUSER)


@addRecipient.handle()
async def _(bot: Bot, event: MessageEvent, args: Message = CommandArg()):
    check_dict_key_bot_id(config, requestorDict, numDict, bot)
    friend_list = await getReferIdList(bot, 'user_id')
    text = event.get_plaintext().strip()
    argsText = args.extract_plain_text()
    recipient = argsText
    if recipient == '':
        await addRecipient.send('格式')
    if int(recipient) in friend_list:
        choose = getExist('添加', text, argsText)
        if isinstance(choose, bool):
            if choose:
                op = '添加'
                if recipient not in config[bot.self_id]['recipientList']:
                    config[bot.self_id]['recipientList'].append(recipient)
            else:
                op = '删除'
                if recipient in config[bot.self_id]['recipientList']:
                    config[bot.self_id]['recipientList'].remove(recipient)
            writeData(configPath, config)
            await addRecipient.send(f'{op}{recipient}成功')
        else:
            return
    else:
        await addRecipient.finish(f'不是{config[bot.self_id]["botName"]}的好友或者格式错误')

friendHelp = on_command("加好友帮助", block=True, priority=5, permission=SUPERUSER)


@friendHelp.handle()
async def _():
    msg = '重载配置\n更改自动同意，更改最大加数量，更改查看加返回数量，更改加时间，更改加时间单位 (群聊、好友)\n同意加，拒绝加，查看加 (群聊、好友)\n清理请求表\n重置请求次数 (群聊、好友)\n添加请求接收者，删除请求接收者'
    await friendHelp.send(msg)
