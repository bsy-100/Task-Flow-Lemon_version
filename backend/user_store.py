from datetime import datetime, timezone

from sqlalchemy.exc import IntegrityError

from .database import SessionLocal
from .models import UserRow
from .schemas import User


class DbUserStore:
    """MariaDB users 테이블에 사용자를 저장한다."""

    def create(self, username: str, password_hash: str) -> User | None:
        """사용자를 등록한다. 대소문자만 다른 사용자명까지 포함해 이미 있으면 None을 반환한다."""
        row = UserRow(
            username=username,
            username_key=username.lower(),
            password_hash=password_hash,
            created_at=datetime.now(timezone.utc).replace(microsecond=0, tzinfo=None),
        )
        with SessionLocal() as session:
            session.add(row)
            try:
                session.commit()
            except IntegrityError:
                # username_key의 유일 제약 위반. 다른 DB 오류는 그대로 올려 503으로 처리한다.
                session.rollback()
                if self._exists(username.lower()):
                    return None
                raise
            return User(id=row.id, username=row.username)

    def _exists(self, username_key: str) -> bool:
        with SessionLocal() as session:
            return session.query(UserRow.id).filter(UserRow.username_key == username_key).first() is not None
