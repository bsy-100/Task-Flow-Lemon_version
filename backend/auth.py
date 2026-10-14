import hashlib
import os
import secrets
from datetime import datetime, timedelta, timezone

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

from .database import ENV_FILE, read_env_file

# 기본 매개변수(argon2id)를 사용한다. 해시에는 솔트와 매개변수가 함께 들어 있다.
_hasher = PasswordHasher()

SESSION_COOKIE = "session"
SESSION_DAYS = 7
SESSION_MAX_AGE = SESSION_DAYS * 24 * 60 * 60


def hash_password(password: str) -> str:
    """비밀번호를 argon2 해시 문자열로 바꾼다. 평문은 저장하거나 기록하지 않는다."""
    return _hasher.hash(password)


def verify_password(password_hash: str, password: str) -> bool:
    """비밀번호가 해시와 맞는지 확인한다. 해시 형식 오류도 불일치로 처리한다."""
    try:
        return _hasher.verify(password_hash, password)
    except (VerificationError, InvalidHashError):
        return False


# 없는 사용자명으로 로그인할 때도 같은 해시 검증 시간이 들도록 쓰는 가짜 해시.
DUMMY_HASH = hash_password("dummy-password-for-timing")


def new_session_token() -> str:
    """세션 토큰 원문을 만든다. 쿠키로만 보내고 DB·로그에는 남기지 않는다."""
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    """DB에 저장·조회할 토큰 해시(SHA-256 16진수 64자). 토큰이 무작위 값이라 솔트 없이 쓴다."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def utc_now() -> datetime:
    """DB에 저장하는 UTC 현재 시각(시간대 정보 없음, 초 단위)."""
    return datetime.now(timezone.utc).replace(microsecond=0, tzinfo=None)


def session_expires_at(now: datetime) -> datetime:
    return now + timedelta(days=SESSION_DAYS)


def cookie_secure() -> bool:
    """HTTPS 배포에서는 COOKIE_SECURE=true로 Secure 속성을 켠다. 환경변수가 .env보다 우선한다."""
    value = os.environ.get("COOKIE_SECURE", read_env_file(ENV_FILE).get("COOKIE_SECURE", ""))
    return value.strip().lower() in ("1", "true", "yes")
