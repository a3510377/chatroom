
from typing import Literal, Optional, TypedDict

__all__ = (
    "AuthorizationType",
    "MessageEvent",
)


class AuthorizationType(TypedDict):
    username: str
    password: str


class MessageEvent(TypedDict):
    content: str
    user_name: Optional[str]
    type: Literal["sys", "user"]
    time_str: str
