import random

from faker import Faker
from nonebot import on_command
from nonebot.matcher import Matcher
from nonebot.plugin import PluginMetadata

__plugin_meta__ = PluginMetadata(
    name="伪造信息",
    description="伪造身份信息",
    usage="指令：伪造信息",
)

faker = Faker(locale="zh_CN")
fakeinfo = on_command("伪造信息", block=True)


def generate_family():
    # 随机生成家族前缀
    prefix = random.choice(
        [
            "火箭",
            "狂魔",
            "搵铁",
            "扥填",
            "飞天",
            "逆天",
            "谊读",
            "大话",
            "懒得",
            "扞雨",
            "盛世",
            "梦幻",
            "兰心",
            "嘻哈",
            "王者",
        ]
    )
    # 随机逆天字符
    character = random.choice(["※", "★", "♪", "的", "╰", "♣", "♡", "の", "之", ""])
    # 随机生成家族后缀
    suffix = random.choice(
        [
            "家族",
            "和家",
            "战队",
            "基",
            "世家",
            "天下",
            "皇朝",
            "热情",
            "尊王",
            "寂寞",
            "星球",
            "担当",
            "兴趣",
        ]
    )
    return prefix + character + suffix


@fakeinfo.handle()
async def handle_function(matcher: Matcher):
    await matcher.finish(
        f"姓名：{faker.name()}\n网名：{faker.user_name()}\n头像：{faker.image_url()}\n身份证：{faker.ssn(min_age=18, max_age=90)}\n家族：{generate_family()}\n住址：{faker.address()}\n电话：{faker.phone_number()}\n邮箱：{faker.free_email()}\n网站：{faker.hostname(2)}\n公司：{faker.company()}\n职位：{faker.job()}\n工作邮箱：{faker.company_email()}\n信用卡：{faker.credit_card_number()},{faker.credit_card_security_code()},{faker.credit_card_expire()}"
    )
