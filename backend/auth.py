from argon2 import PasswordHasher

# 기본 매개변수(argon2id)를 사용한다. 해시에는 솔트와 매개변수가 함께 들어 있다.
_hasher = PasswordHasher()


def hash_password(password: str) -> str:
    """비밀번호를 argon2 해시 문자열로 바꾼다. 평문은 저장하거나 기록하지 않는다."""
    return _hasher.hash(password)
