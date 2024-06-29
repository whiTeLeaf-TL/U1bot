import random
from pathlib import Path

from nonebot import on_endswith, on_startswith
from nonebot.adapters.onebot.v11 import GroupMessageEvent
from nonebot.matcher import Matcher
from nonebot.plugin import PluginMetadata

__plugin_meta__ = PluginMetadata(
    name="答案之书",
    description="愿一切无解都有解！解除你的迷惑，终结你的纠结！",
    usage=(
        "翻看答案 + 问题\n"
        "问题 + 翻看答案\n"
        "数据来源于吉林美术出版社2018年9月第1版的《神奇的答案之书》，数据著作权为原作者张权所有。"
    ),
)
import ujson as json

answers_path = Path(__file__).parent / "answersbook.json"
answers = json.loads(answers_path.read_text("utf-8"))


def get_answers():
    key = random.choice(list(answers))
    return answers[key]["answer"]


answers_starts = on_startswith("翻看答案")
answers_ends = on_endswith("翻看答案")


@answers_starts.handle()
@answers_ends.handle()
async def answersbook(event: GroupMessageEvent, matcher: Matcher):
    msg = event.message.extract_plain_text().replace("翻看答案", "")
    if not msg:
        await matcher.finish("你想问什么问题呢？")
    answer = get_answers()
    await matcher.send(answer, at_sender=True)
