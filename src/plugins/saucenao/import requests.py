import requests
import base64
import re
from nonebot.adapters.onebot.v11.helpers import extract_image_urls

def url_to_base64(image_url):
    response = requests.get(image_url)
    image_data = response.content
    base64_data = base64.b64encode(image_data).decode('utf-8')
    return base64_data

def process_message(original_message):
    # 提取所有图片URL列表
    image_urls = extract_image_urls(original_message)

    # 遍历每个URL，将其转换为Base64并替换原始信息
    for image_url in image_urls:
        base64_image = url_to_base64(image_url)
        original_message = original_message.replace(image_url, f'base64://{base64_image}')

    return original_message

# 原始信息
original_smessage = '给岁月以文明，而非给文明以岁月。[CQ:image,file=3830aee11c23f77197c742bb4d26f41b.image,url=https://c2cpicdw.qpic.cn/offpic_new/2580699277//2580699277-2369793329-3830AEE11C23F77197C742BB4D26F41B/0?term=2&amp;is_origin=0]'

# 处理信息并输出
new_message = process_message(original_smessage)
print("替换后的信息:")
print(new_message)
