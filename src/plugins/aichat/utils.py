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


def is_image_message_normal(data: MessageEvent):
    message = str(data.get_message())
    url_pattern = r"url=(https?[^,]+)"
    if image_match := re.search(url_pattern, message):
        image_url = image_match[1]
        return True, image_url
    url_pattern = r"url=(file[^,]+)"
    if not (image_match := re.search(url_pattern, message)):
        return False, ""
    image_url = image_match[1]
    return True, image_url


def is_image_message(is_cq_code: bool, data: MessageEvent) -> tuple[bool, str]:
    """
    判断是否是图片消息。
    Args:
    - is_cq_code (bool): 是否是 CQ 码。
    - data (Any): 消息数据。
    Returns:
    - tuple: 包含两个元素：
        - is_image (bool): 是否是图片消息。
        - image_url (str): 图片 URL。
    """
    if is_cq_code:
        return is_image_message_normal(data)
    for msg in data.message:
        if msg.type == "image":
            if image_url := msg.data.get("url", ""):
                return True, image_url
            return False, ""
    return False, ""


def is_image_message_reply(data: Reply):
    message = str(data.message)
    url_pattern = r"url=(https?[^,]+)"
    if image_match := re.search(url_pattern, message):
        image_url = image_match[1]
        return True, image_url
    url_pattern = r"url=(file[^,]+)"
    if not (image_match := re.search(url_pattern, message)):
        return False, ""
    image_url = image_match[1]
    return True, image_url


def is_reply_image_message(is_cq_code: bool, data: Reply) -> tuple[bool, str]:
    """
    判断是否是回复的图片消息。
    Args:
    - is_cq_code (bool): 是否是 CQ 码。
    - data (Any): 消息数据。
    Returns:
    - tuple: 包含两个元素：
        - is_image (bool): 是否是图片消息。
        - image_url (str): 图片 URL。
    """
    if is_cq_code:
        return is_image_message_reply(data)
    for msg in data.message:
        if msg.type == "image":
            if image_url := msg.data.get("url", ""):
                return True, image_url
            return False, ""
    return False, ""
