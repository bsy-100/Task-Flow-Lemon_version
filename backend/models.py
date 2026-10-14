from datetime import date, datetime

from sqlalchemy import CHAR, Date, DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


class UserRow(Base):
    """users 테이블. 비밀번호는 argon2 해시로만 저장한다."""

    __tablename__ = "users"
    __table_args__ = {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(20), nullable=False)
    # 대소문자 구분 없는 중복 방지용. username을 소문자로 바꾼 값이며 DB 정렬 규칙에 의존하지 않는다.
    username_key: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)


class SessionRow(Base):
    """sessions 테이블. 세션 토큰은 SHA-256 해시(16진수 64자)만 저장하고 원문은 저장하지 않는다."""

    __tablename__ = "sessions"
    __table_args__ = {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"}

    token_hash: Mapped[str] = mapped_column(CHAR(64), primary_key=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)


class TaskRow(Base):
    """tasks 테이블. 값 규칙은 API-SPEC.md의 Task 객체와 같다."""

    __tablename__ = "tasks"
    __table_args__ = {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(String(2000), nullable=False, default="", server_default="")
    status: Mapped[str] = mapped_column(
        Enum("TODO", "DOING", "DONE", name="task_status"),
        nullable=False,
        default="TODO",
        server_default="TODO",
    )
    priority: Mapped[str] = mapped_column(
        Enum("HIGH", "NORMAL", "LOW", name="task_priority"),
        nullable=False,
        default="NORMAL",
        server_default="NORMAL",
    )
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    # UTC 기준 등록 일시. 시간대 정보 없이 저장하고 API 응답에서 UTC로 표시한다.
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
