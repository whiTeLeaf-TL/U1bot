import base64
import re
import ssl

import aiohttp
from nonebot.adapters.onebot.v11 import MessageEvent
from nonebot.adapters.onebot.v11.utils import unescape


async def url_to_base64(image_url) -> str:
    ssl_context = ssl.create_default_context()
    ssl_context.set_ciphers("DEFAULT:@SECLEVEL=1")  # 降低 SSL/TLS 安全等级

    async with aiohttp.ClientSession() as session:
        async with session.get(image_url, ssl=ssl_context) as response:
            image_data = await response.read()
            print(image_data)
            return base64.b64encode(image_data).decode("utf-8")


def extract_image_url(message: str) -> str:
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
        return image_match[1]

    url_pattern = r"url=(file[^,]+)"
    if image_match := re.search(url_pattern, message):
        return image_match[1]

    return ""


def replace_cq_with_caption(text: str, base64_image: str) -> str:
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
    return re.sub(pattern, f"[CQ:image,file=base64://{base64_image}]", text)


async def is_image_message(
    data: MessageEvent, is_cq_code: bool = False
) -> tuple[bool, str]:
    if is_cq_code:
        image_url = extract_image_url(str(data.message))
        return (
            (
                True,
                replace_cq_with_caption(
                    str(data.message), await url_to_base64(image_url)
                ),
            )
            if image_url
            else (False, "")
        )

    for msg in data.message:
        if msg.type == "image" and (image_url := msg.data.get("url", "")):
            return True, replace_cq_with_caption(
                str(data.message), await url_to_base64(image_url)
            )

    return False, ""
