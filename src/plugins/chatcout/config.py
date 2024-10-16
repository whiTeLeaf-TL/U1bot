from pydantic import BaseModel


class Config(BaseModel):
    """Plugin Config Here"""
    interval: int = 300 # seconds
