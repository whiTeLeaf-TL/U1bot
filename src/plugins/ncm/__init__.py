#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from pathlib import Path
from typing import Tuple, Any, Union

import nonebot
from nonebot import on_regex, on_command, on_message
from nonebot.adapters.onebot.v11 import (Message, Bot,
                                         MessageSegment,
                                         GroupMessageEvent,
                                         PrivateMessageEvent)
from nonebot.log import logger
from nonebot.matcher import Matcher
from nonebot.params import CommandArg, RegexGroup, Arg
from nonebot.rule import Rule

from .data_source import nncm, ncm_config, setting, Q, cmd

# =======nonebot-plugin-help=======
__plugin_meta__ = nonebot.plugin.PluginMetadata(
    name='网易云点歌',
    description='网易云无损音乐下载/点歌',
    usage=(
        '将网易云歌曲/歌单分享到群聊即可自动解析\n'
        '回复分享消息 + 文字`下载` 即可开始下载歌曲并上传到群文件(需要稍等一会)\n'
        '指令：\n'
        f'开启下载：{cmd}ncm t\n'
        f'关闭下载：{cmd}ncm f\n'
        f'点歌：{cmd}点歌 歌名'
    ),
    extra={'version': '1.5.0'}
)

# ========nonebot-plugin-ncm======
# ===========Constant=============
TRUE = ["True", "T", "true", "t"]
FALSE = ["False", "F", "false", "f"]
ADMIN = ["owner", "admin", "member"]


# ===============Rule=============
async def song_is_open(event: Union[GroupMessageEvent, PrivateMessageEvent]) -> bool:
    if isinstance(event, GroupMessageEvent):
        info = setting.search(Q["group_id"] == event.group_id)
        if info:
            return info[0]["song"]
        else:
            setting.insert({"group_id": event.group_id, "song": False, "list": False})
            return False
    elif isinstance(event, PrivateMessageEvent):
        info = setting.search(Q["user_id"] == event.user_id)
        if info:
            return info[0]["song"]
        else:
            setting.insert({"user_id": event.user_id, "song": True, "list": True})
            return True


async def playlist_is_open(event: Union[GroupMessageEvent, PrivateMessageEvent]) -> bool:
    if isinstance(event, GroupMessageEvent):
        info = setting.search(Q["group_id"] == event.group_id)
        if info:
            return info[0]["list"]
        else:
            setting.insert({"group_id": event.group_id, "song": False, "list": False})
            return False
    elif isinstance(event, PrivateMessageEvent):
        info = setting.search(Q["user_id"] == event.user_id)
        if info:
            return info[0]["list"]
        else:
            setting.insert({"user_id": event.user_id, "song": True, "list": True})
            return True


async def check_search() -> bool:
    info = setting.search(Q["global"] == "search")
    if info:
        return info[0]["value"]
    else:
        setting.insert({"global": "search", "value": True})
        return True


async def music_set_rule(event: Union[GroupMessageEvent, PrivateMessageEvent]) -> bool:
    # 权限设置
    return event.sender.role in ADMIN[:ncm_config.ncm_admin_level] or event.get_user_id() in ncm_config.superusers


async def music_reply_rule(event: Union[GroupMessageEvent, PrivateMessageEvent]):
    # logger.info(event.get_plaintext())
    return event.reply and event.get_plaintext().strip() == "下载"


# ============Matcher=============
ncm_set = on_command("ncm",
                     rule=Rule(music_set_rule),
                     priority=1, block=False)
'''功能设置'''
music_regex = on_regex("(song|url)\?id=([0-9]+)(|&)",
                       priority=2, block=False)
'''歌曲id识别'''
playlist_regex = on_regex("playlist\?id=([0-9]+)&",
                          priority=2, block=False)
'''歌单识别'''
music_reply = on_message(priority=2,
                         rule=Rule(music_reply_rule),
                         block=False)
'''回复下载'''
search = on_command("点歌",
                    rule=Rule(check_search),
                    priority=2, block=False)
'''点歌'''


@search.handle()
async def search_receive(matcher: Matcher, args: Message = CommandArg()):
    if args:
        matcher.set_arg("song", args)  # 如果用户发送了参数则直接赋值


@search.got("song", prompt="要点什么歌捏?")
async def receive_song(bot: Bot,
                       event: Union[GroupMessageEvent, PrivateMessageEvent],
                       song: Message = Arg(),
                       ):
    nncm.get_session(bot, event)
    _id = await nncm.search_song(keyword=str(song), limit=1)
    message_id = await bot.send(event=event, message=Message(MessageSegment.music(type_="163", id_=_id)))
    nncm.get_song(message_id=message_id["message_id"], nid=_id)
    # try:

    # except ActionFailed as e:
    #    logger.error(e.info)
    #    await search.finish(event=event, message=f"[WARNING]: 网易云卡片消息发送失败: 账号可能被风控")


@music_regex.handle()
async def music_receive(bot: Bot, event: Union[GroupMessageEvent, PrivateMessageEvent],
                        regroup: Tuple[Any, ...] = RegexGroup()):
    nid = regroup[1]
    logger.info(f"已识别NID:{nid}的歌曲")
    nncm.get_session(bot, event)
    nncm.get_song(nid)


@playlist_regex.handle()
async def music_list_receive(bot: Bot, event: Union[GroupMessageEvent, PrivateMessageEvent],
                             regroup: Tuple[Any, ...] = RegexGroup()):
    lid = regroup[0]
    logger.info(f"已识别LID:{lid}的歌单")
    nncm.get_session(bot, event)
    nncm.get_playlist(lid=lid)


@music_reply.handle()
async def music_reply_receive(bot: Bot, event: Union[GroupMessageEvent, PrivateMessageEvent]):
    # logger.info(event.dict()["reply"]["message_id"])
    nncm.get_session(bot, event)
    info = nncm.check_message()
    if info is None:
        return
    if info["type"] == "song" and await song_is_open(event):
        await bot.send(event=event, message="好吧好吧，你等等我！")
        await nncm.download(ids=[int(info["nid"])])
        data = await nncm.music_check(info["nid"])
        if data:
            if isinstance(event, GroupMessageEvent):
                await nncm.upload_group_data_file(data)
            elif isinstance(event, PrivateMessageEvent):
                await nncm.upload_private_data_file(data)
        else:
            logger.error("数据库中未有该音乐地址数据")

    elif info["type"] == "playlist" and await playlist_is_open(event):
        await bot.send(event=event, message=info["lmsg"]+"\n下载中,上传时间较久,请勿重复发送命令")
        not_zips = await nncm.download(ids=info["ids"], lid=info["lid"], is_zip=ncm_config.ncm_playlist_zip)
        filename = f"{info['lid']}.zip"
        data = Path.cwd().joinpath("music").joinpath(filename)
        if ncm_config.ncm_playlist_zip:
            logger.debug(f"Upload:{filename}")
            if isinstance(event, GroupMessageEvent):
                await nncm.upload_group_file(file=str(data), name=filename)
            elif isinstance(event, PrivateMessageEvent):
                await nncm.upload_private_file(file=str(data), name=filename)
        else:
            for i in not_zips:
                file = i["file"]
                filename = i["filename"]
                logger.debug(f"Upload:{filename}")
                if isinstance(event, GroupMessageEvent):
                    await nncm.upload_group_file(file=file, name=filename)
                elif isinstance(event, PrivateMessageEvent):
                    await nncm.upload_private_file(file=file, name=filename)


@ncm_set.handle()
async def set_receive(bot: Bot, event: Union[GroupMessageEvent, PrivateMessageEvent],
                      args: Message = CommandArg()):  # 功能设置接收
    logger.debug(f"权限为{event.sender.role}的用户<{event.sender.nickname}>尝试使用命令{cmd}ncm {args}")
    if args:
        args = str(args).split()
        if len(args) == 1:
            mold = args[0]
            if isinstance(event, GroupMessageEvent):
                info = setting.search(Q["group_id"] == event.group_id)
                # logger.info(info)
                if info:
                    if mold in TRUE:
                        info[0]["song"] = True
                        info[0]["list"] = True
                        setting.update(info[0], Q["group_id"] == event.group_id)
                        msg = "已开启自动下载功能"
                        await bot.send(event=event, message=Message(MessageSegment.text(msg)))
                    elif mold in FALSE:
                        info[0]["song"] = False
                        info[0]["list"] = False
                        setting.update(info[0], Q["group_id"] == event.group_id)
                        msg = "已关闭自动下载功能"
                        await bot.send(event=event, message=Message(MessageSegment.text(msg)))
                    logger.debug(f"用户<{event.sender.nickname}>执行操作成功")
                else:
                    if mold in TRUE:
                        setting.insert({"group_id": event.group_id, "song": True, "list": True})
                    elif mold in FALSE:
                        setting.insert({"group_id": event.group_id, "song": False, "list": False})
            elif isinstance(event, PrivateMessageEvent):
                info = setting.search(Q["user_id"] == event.user_id)
                # logger.info(info)
                if info:
                    if mold in TRUE:
                        info[0]["song"] = True
                        info[0]["list"] = True
                        setting.update(info[0], Q["user_id"] == event.user_id)
                        msg = "已开启下载功能"
                        await bot.send(event=event, message=Message(MessageSegment.text(msg)))
                    elif mold in FALSE:
                        info[0]["song"] = False
                        info[0]["list"] = False
                        setting.update(info[0], Q["user_id"] == event.user_id)
                        msg = "已关闭下载功能"
                        await bot.send(event=event, message=Message(MessageSegment.text(msg)))
                    logger.debug(f"用户<{event.sender.nickname}>执行操作成功")
                else:
                    if mold in TRUE:
                        setting.insert({"user_id": event.user_id, "song": True, "list": True})
                    elif mold in FALSE:
                        setting.insert({"user_id": event.user_id, "song": False, "list": False})
        elif len(args) == 2 and args[0] == "search":
            mold = args[1]
            info = setting.search(Q["global"] == "search")
            if info:
                if mold in TRUE:
                    info[0]["value"] = True
                    setting.update(info[0], Q["global"] == "search")
                    msg = "已开启点歌功能"
                    await bot.send(event=event, message=Message(MessageSegment.text(msg)))
                elif mold in FALSE:
                    info[0]["value"] = False
                    setting.update(info[0], Q["global"] == "search")
                    msg = "已关闭点歌功能"
                    await bot.send(event=event, message=Message(MessageSegment.text(msg)))
                logger.debug(f"用户<{event.sender.nickname}>执行操作成功")
            else:
                if mold in TRUE:
                    setting.insert({"global": "search", "value": True})
                elif mold in FALSE:
                    setting.insert({"global": "search", "value": False})
        elif len(args) == 3 and args[0] == "private":
            qq = args[1]
            mold = args[2]
            info = setting.search(Q["user_id"] == qq)
            # logger.info(info)
            if info:
                if mold in TRUE:
                    info[0]["song"] = True
                    info[0]["list"] = True
                    setting.update(info[0], Q["user_id"] == qq)
                    msg = f"已开启用户{qq}的下载功能"
                    await bot.send(event=event, message=Message(MessageSegment.text(msg)))
                elif mold in FALSE:
                    info[0]["song"] = False
                    info[0]["list"] = False
                    setting.update(info[0], Q["user_id"] == qq)
                    msg = f"已关闭用户{qq}的下载功能"
                    await bot.send(event=event, message=Message(MessageSegment.text(msg)))
                logger.debug(f"用户<{event.sender.nickname}>执行操作成功")
            else:
                if mold in TRUE:
                    setting.insert({"user_id": event.user_id, "song": True, "list": True})
                elif mold in FALSE:
                    setting.insert({"user_id": event.user_id, "song": False, "list": False})
    else:
        msg = f"{cmd}ncm:获取命令菜单\r\n说明:网易云歌曲分享到群内后回复机器人即可下载\r\n" \
              f"{cmd}ncm t:开启解析\r\n{cmd}ncm f:关闭解析\n{cmd}点歌 歌名:点歌"
        return await ncm_set.finish(message=MessageSegment.text(msg))
