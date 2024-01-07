import base64
import re
import requests


def url_to_base64(image_url):
    response = requests.get(image_url)
    image_data = response.content
    base64_data = base64.b64encode(image_data).decode("utf-8")
    return base64_data


def process_message(original_message):
    # 使用正则表达式提取图片URL
    url_match = re.search(
        r"\[CQ:image,file=\w+\.image,url=([^\]]+)\]", original_message
    )

    if url_match:
        image_url = url_match.group(1)

        # 将图片URL转换为Base64
        base64_image = url_to_base64(image_url)

        # 构建新的消息
        new_message = re.sub(
            r"\[CQ:image,file=\w+\.image,url=([^\]]+)\]",
            f"[CQ:image,file=base64://{base64_image}]",
            original_message,
        )

        return new_message
    else:
        return original_message


# 覆盖一个txt文件
with open("test.txt", "w", encoding="utf-8") as f:
    f.write(process_message(input()))
