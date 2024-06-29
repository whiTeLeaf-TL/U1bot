from pydantic import BaseModel, Extra


class Config(BaseModel, extra=Extra.ignore):
    whateat_cd: int = 10
    whateat_max: int = 0
