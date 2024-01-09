import copy
from datetime import datetime
from os.path import dirname, exists
from nonebot import get_driver
import json
from nonebot.adapters.onebot.v11 import Bot
from .utils import writeTime

basedir = dirname(__file__)
configPath = f"{basedir}/config.json"
requestorDictPath = f"{basedir}/requestor.json"
numDictPath = f"{basedir}/num.json"
max = 6
blackLogPath = f"{basedir}/blackLog.txt"


def check_dict_key_bot_id(config: dict, requestorDict: dict, numDict: dict, bot: Bot):
    print(1)
    if config.get(bot.self_id) is None:
        config[bot.self_id] = copy.deepcopy(configModel)
        writeData(configPath, config)
    if requestorDict.get(bot.self_id) is None:
        requestorDict[bot.self_id] = copy.deepcopy(requestorDictModel)
        writeData(requestorDictPath, requestorDict)
    if numDict.get(bot.self_id) is None:
        numDict[bot.self_id] = copy.deepcopy(numDictModel)
        for type in numDict[bot.self_id].keys():
            numDict[bot.self_id][type]["time"] = datetime.strptime(
                numDict[bot.self_id][type]["time"], "%Y-%m-%d %H:%M:%S.%f"
            )
        writeTime(numDictPath, numDict)
    # return True


def readData(path, content={}, update=0) -> dict:
    if not exists(path):
        with open(path, "w", encoding="utf-8") as fp:
            json.dump(content, fp, ensure_ascii=False)
    with open(path, "r", encoding="utf-8") as fp:
        data = json.loads(fp.read())
    return data


def writeData(path, content):
    with open(path, "w", encoding="utf-8") as fp:
        json.dump(content, fp, ensure_ascii=False)


recipientList = list(get_driver().config.superusers)
# recipients=str(recipients)[1:-1].replace(' ','').replace("'",'')
# 可以在这里修改默认模板哦
configModel = {
    "agreeAutoApprove": {"friend": 1, "group": 1},
    "recipientList": [],
    "forwardSet": 0,
    "numControl": {
        "useAlgorithm": 0,
        "maxNum": 6,
        "time": 2,
        "unit": "h",
        "friend": {"maxNum": 6, "time": 2, "unit": "h"},
        "group": {"maxNum": 5, "time": 2, "unit": "h"},
    },
    "maxViewNum": 20,
    "blackDict": {
        "friend": {"text": [], "id": []},
        "group": {"text": [], "id": []},
        "forward": {},
    },
    "warnDict": {
        "friend": {"text": [], "id": []},
        "group": {"text": [], "id": []},
        "forward": {},
    },
    "allowAddFriednText": [],
    "botName": "姚奕",
    "friend_msg": {
        "notice_msg": "请求添加好友,验证消息为",
        "welcome_msg": "你吼，我是姚奕！我的信息都会在我的说说更新，绝对不会骚扰到你滴！\n同时，如果有疑问，可以发送help哦",
    },
    "group_msg": {"notice_msg": "发送群邀请,验证消息为", "welcome_msg": "很高兴有你的邀请，但要等我一下！"},
    "statusDict": {
        "blackDict": {
            "friend": {"status": "拉黑QQ,已拒绝,仅作提示"},
            "group": {"status": "拉黑群聊,已拒绝,仅作提示"},
        },
        "warnDict": {
            "friend": {"status": "警告QQ,手动同意,是否同意"},
            "group": {"status": "警告群聊,手动同意,是否同意"},
        },
    },
}

requestorDictModel = {"friend": {}, "group": {}}
numDictModel = {
    "friend": {"count": 0, "time": str(datetime.now())},
    "group": {"count": 0, "time": str(datetime.now())},
}
config = readData(configPath)
requestorDict = readData(requestorDictPath)
numDict = readData(numDictPath)
for bot_id in numDict.keys():
    for type in numDict[bot_id].keys():
        numDict[bot_id][type]["time"] = datetime.strptime(
            numDict[bot_id][type]["time"], "%Y-%m-%d %H:%M:%S.%f"
        )
