import re

import aiohttp
from nonebot.adapters.onebot.v11.event import MessageEvent, Reply

from .config import Config


async def chat_with_gpt(data: list, config: Config) -> str:
    payload = {
        "messages": data,
        "model": config.appoint_model,
        "temperature": config.temperature,
        "max_tokens": config.max_tokens,
        "top_p": 0.3,
        "frequency_penalty": 1.4,
        "presence_penalty": 1,
        "stream": False,
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{config.base_url}/chat/completions",
            json=payload,
            headers={
                "Authorization": f"Bearer {config.api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
        ) as resp:
            result = await resp.json()
            return result["choices"][0]["message"]["content"]


def extract_image_url(message: str) -> tuple[bool, str]:
    """
    从消息文本中提取图片 URL。
    Args:
    - message (str): 消息文本。

    Returns:
    - tuple: 包含两个元素：
        - is_image (bool): 是否找到图片 URL。
        - image_url (str): 图片 URL。
    """
    url_pattern = r"url=(https?[^,]+)"
    if image_match := re.search(url_pattern, message):
        return True, image_match[1]

    url_pattern = r"url=(file[^,]+)"
    if image_match := re.search(url_pattern, message):
        return True, image_match[1]

    return False, ""


def is_image_message(data: MessageEvent | Reply, is_cq_code: bool) -> tuple[bool, str]:
    """
    判断是否是图片消息。
    Args:
    - data (MessageEvent): 消息数据。
    - is_cq_code (bool): 是否是 CQ 码。

    Returns:
    - tuple: 包含两个元素：
        - is_image (bool): 是否是图片消息。
        - image_url (str): 图片 URL。
    """
    if is_cq_code:
        return extract_image_url(str(data.message))

    for msg in data.message:
        if msg.type == "image" and (image_url := msg.data.get("url", "")):
            return True, image_url

    return False, ""


from nonebot.adapters.onebot.v11.utils import unescape


def replace_cq_with_caption(text: str, caption: str) -> str:
    """
    将文本中的 [CQ:...] 标签替换为指定的描述。

    参数:
    - text: 包含 [CQ:...] 标签的原始文本
    - caption: 用于替换 [CQ:...] 的描述文本

    返回值:
    - 替换后的文本
    """
    # 反转义
    text = unescape(text)

    # 匹配包含 URL 或 file 的 [CQ:image] 标签，处理 subType=1 结尾
    pattern = r"\[CQ:image(?:,.*?url=(https?://[^,]+|file=[^,]+).*?subType=\d+)?\]"

    # 替换匹配到的 [CQ:image] 标签
    return re.sub(pattern, f"[图片,描述:{caption}]", text)


def replace_at_message(text: str) -> str:
    """
    检测并替换指定的 CQ:at 消息。
    Args:
    - text (str): 原始消息文本。
    - target_qq (str): 目标 QQ 号。

    Returns:
    - str: 替换后的文本。
    """
    # 匹配 CQ:at 类型的消息，提取 qq 和 name
    cq_at_pattern = r"\[CQ:at,qq=(\d+),name=(.*?)\]"

    def replace_at(match):
        name = match.group(2)
        # 检查是否是指定的 qq 号
        return f"@{name}"

    # 使用正则表达式进行替换
    return re.sub(cq_at_pattern, replace_at, text)


def extract_mface_summary(text: str) -> str:
    """
    检测并提取 CQ:mface 消息的 summary 字段，返回 '表情包,描述:summary内容' 格式。
    Args:
    - text (str): 原始消息文本。

    Returns:
    - str: 提取后的描述信息，如果没有匹配，则返回空字符串。
    """
    # 匹配 CQ:mface 的消息，并提取 summary 字段
    cq_mface_pattern = r"\[CQ:mface,[^\]]*summary=\[([^\]]+)\][^\]]*\]"

    if match := re.search(cq_mface_pattern, text):
        summary = match[1]
        return f"[表情包,描述:{summary}]"

    return ""  # 如果没有匹配到，则返回空字符串
