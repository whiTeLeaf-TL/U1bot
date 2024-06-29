from typing import Literal, overload

__all__ = ("model_validator",)

from pydantic import root_validator


@overload
def model_validator(*, mode: Literal["before"]): ...


@overload
def model_validator(*, mode: Literal["after"]): ...


def model_validator(*, mode: Literal["before", "after"]):
    return root_validator(pre=mode == "before", allow_reuse=True)
