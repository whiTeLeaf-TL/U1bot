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
    potential_matches = re.finditer(r"\[CQ:image", text)
    result = []
    last_pos = 0
    replacement_template = f"[CQ:image,file=base64://{base64_image}]"

    for match in potential_matches:
        start = match.start()
        result.append(text[last_pos:start])  # 添加上次匹配结束到这次匹配开始的部分
        # 从匹配位置开始逐字符解析，寻找完整的 [CQ:image,...]
        i = start
        depth = 0
        while i < len(text):
            if text[i] == "[":
                depth += 1
            elif text[i] == "]":
                depth -= 1
                if depth == 0:
                    # 匹配到完整的 [CQ:image,...]
                    result.append(replacement_template)
                    last_pos = i + 1  # 更新最后的结束位置
                    break
            i += 1
        else:
            # 如果没能闭合，直接保留原始文本
            last_pos = start

    # 添加剩余未处理的部分
    result.append(text[last_pos:])
    return "".join(result)


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
        print(msg)
        if msg.type == "image" and (image_url := msg.data.get("url", "")):
            return True, replace_cq_with_caption(
                str(data.message), await url_to_base64(image_url)
            )

    return False, ""
