import re
from datetime import date, datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator

TITLE_MAX_LENGTH = 100
DESCRIPTION_MAX_LENGTH = 2000
DATE_PATTERN = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}")


class Status(str, Enum):
    TODO = "TODO"
    DOING = "DOING"
    DONE = "DONE"


class Priority(str, Enum):
    HIGH = "HIGH"
    NORMAL = "NORMAL"
    LOW = "LOW"


class TaskCreate(BaseModel):
    """POST /api/tasks 요청 본문. 정의되지 않은 필드는 거절한다."""

    model_config = ConfigDict(extra="forbid")

    title: str
    description: str = Field(default="", max_length=DESCRIPTION_MAX_LENGTH)
    priority: Priority = Priority.NORMAL
    due_date: date | None = None

    @field_validator("due_date", mode="before")
    @classmethod
    def validate_due_date(cls, value: object) -> object:
        # "YYYY-MM-DD" 문자열만 허용하고 숫자·일시 문자열은 날짜로 변환하지 않는다.
        # 실제 존재하는 날짜인지는 이후 date 변환에서 확인한다.
        if value is None:
            return None
        if not isinstance(value, str) or not DATE_PATTERN.fullmatch(value):
            raise ValueError("마감일은 YYYY-MM-DD 형식이어야 합니다.")
        return value

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: str) -> str:
        title = value.strip()
        if not 1 <= len(title) <= TITLE_MAX_LENGTH:
            raise ValueError(
                f"제목은 앞뒤 공백 제거 후 1~{TITLE_MAX_LENGTH}자여야 합니다."
            )
        return title


class Task(BaseModel):
    """API 응답의 할 일."""

    id: int
    title: str
    description: str
    status: Status
    priority: Priority
    due_date: date | None
    created_at: datetime
