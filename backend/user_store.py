from datetime import datetime, timezone

from sqlalchemy.exc import IntegrityError

from .database import SessionLocal
from .models import SessionRow, UserRow
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

    def find_credentials(self, username: str) -> tuple[User, str] | None:
        """로그인용으로 사용자와 비밀번호 해시를 찾는다. 대소문자는 구분하지 않는다."""
        with SessionLocal() as session:
            row = session.query(UserRow).filter(UserRow.username_key == username.lower()).first()
            return (User(id=row.id, username=row.username), row.password_hash) if row else None

    def create_session(self, user_id: int, token_hash: str, now: datetime, expires_at: datetime) -> None:
        """세션을 저장한다. 같은 사용자의 만료된 세션은 함께 정리한다."""
        with SessionLocal() as session:
            session.query(SessionRow).filter(SessionRow.user_id == user_id, SessionRow.expires_at <= now).delete()
            session.add(SessionRow(token_hash=token_hash, user_id=user_id, created_at=now, expires_at=expires_at))
            session.commit()

    def delete_session(self, token_hash: str) -> None:
        """세션을 삭제한다. 없으면 아무것도 하지 않는다."""
        with SessionLocal() as session:
            session.query(SessionRow).filter(SessionRow.token_hash == token_hash).delete()
            session.commit()

    def find_user_by_session(self, token_hash: str, now: datetime) -> User | None:
        """만료되지 않은 세션의 사용자를 반환한다."""
        with SessionLocal() as session:
            row = (
                session.query(UserRow)
                .join(SessionRow, SessionRow.user_id == UserRow.id)
                .filter(SessionRow.token_hash == token_hash, SessionRow.expires_at > now)
                .first()
            )
            return User(id=row.id, username=row.username) if row else None
