from faker import Faker
from nonebot import on_command
from nonebot.plugin import PluginMetadata
from nonebot.matcher import Matcher
__plugin_meta__ = PluginMetadata(
    name="伪造信息",
    description="伪造身份信息",
    usage='指令：伪造信息',
)

faker = Faker(locale='zh_CN')
fakeinfo = on_command('伪造信息')


@fakeinfo.handle()
async def handle_function(matcher: Matcher):
    await matcher.finish(
        f'伪造信息：\n姓名：{faker.name()}\n网名：{faker.user_name()}\n身份证：{faker.ssn(min_age=18, max_age=90)}\n住址：{faker.address()}\n电话：{faker.phone_number()}\n邮箱：{faker.email()}\n公司：{faker.company()}\n职位：{faker.job()}'
    )
