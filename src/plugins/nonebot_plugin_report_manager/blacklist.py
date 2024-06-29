import contextlib
from pathlib import Path
from typing import Literal

import ujson as json
from nonebot import get_driver
from nonebot.adapters.onebot.v11 import MessageEvent

superusers = get_driver().config.superusers
file_path = Path()/'data'/'blacklist'/'blacklist.json'

blacklist = (
    json.loads(file_path.read_text("utf-8"))
    if file_path.is_file()
    else {"blacklist": []}
)


def save_blacklist() -> None:
    file_path.write_text(json.dumps(blacklist), encoding="utf-8")


def is_number(s: str) -> bool:
    with contextlib.suppress(ValueError):
        float(s)
        return True
    with contextlib.suppress(TypeError, ValueError):
        import unicodedata
        unicodedata.numeric(s)
        return True
    return False


def handle_blacklist(
    event: MessageEvent,
    mode: Literal["add", "del"],
) -> str:
    msg = str(event.get_message()).strip().split(' ')
    uids = [i for i in msg if is_number(i)]
    if mode == "add":
        for i in uids:
            if i in superusers:
                uids.remove(i)
            if i in blacklist["blacklist"]:
                uids.remove(i)
        blacklist["blacklist"].extend(uids)
        _mode = "添加"
    elif mode == "del":
        for i in uids:
            if i not in blacklist["blacklist"]:
                uids.remove(i)
        blacklist["blacklist"] = [
            uid for uid in blacklist["blacklist"] if uid not in uids]
        _mode = "删除"
    save_blacklist()
    if not uids:
        return "没有可操作的用户，请检查输入格式或者用户是否已在黑名单中"
    return f"已{_mode} {len(uids)} 个黑名单用户: {', '.join(uids)}"
