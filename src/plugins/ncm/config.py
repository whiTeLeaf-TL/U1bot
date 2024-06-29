import nonebot
from pydantic import BaseModel, Extra


# ============Config=============
class Config(BaseModel, extra=Extra.ignore):
    superusers: list = []

    ncm_admin_level: int = 1
    '''设置命令权限 (1:仅限 superusers 和群主，2:在 1 的基础上管理员，3:所有用户)'''

    ncm_phone: str = ""
    '''手机号'''

    ncm_ctcode: str = "86"
    '''手机号区域码，默认 86'''

    ncm_password: str = ""
    '''密码'''
    ncm_bitrate: int = 320
    '''下载码率 (单位 K) 96 及以下为 m4a,320 及以上为 flac，中间 mp3'''


global_config = nonebot.get_driver().config
ncm_config = Config(**global_config.dict())  # 载入配置
