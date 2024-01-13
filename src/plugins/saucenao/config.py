

from pydantic import Extra, BaseModel


class Config(BaseModel, extra=Extra.ignore):
    saucenao_apikey: str = ""
