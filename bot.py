import nonebot
from nonebot.adapters.onebot.v11 import Adapter as ONEBOT_V11Adapter
import cProfile

nonebot.init()
app = nonebot.get_asgi()
driver = nonebot.get_driver()
driver.register_adapter(ONEBOT_V11Adapter)


nonebot.load_from_toml("pyproject.toml")

if __name__ == "__main__":

    cProfile.run('nonebot.run()', filename="result.out")
