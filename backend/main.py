import logging

from fastapi import Depends, FastAPI, HTTPException, Request, Response, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from .auth import (
    DUMMY_HASH,
    SESSION_COOKIE,
    SESSION_MAX_AGE,
    cookie_secure,
    hash_password,
    hash_token,
    new_session_token,
    session_expires_at,
    utc_now,
    verify_password,
)
from .schemas import LoginRequest, Priority, SignupRequest, Status, Task, TaskCreate, TaskUpdate, User
from .store import DbTaskStore
from .user_store import DbUserStore

app = FastAPI(title="Task Flow API")
store = DbTaskStore()
user_store = DbUserStore()
logger = logging.getLogger(__name__)

TASK_NOT_FOUND = "할 일을 찾을 수 없습니다."
LOGIN_REQUIRED = "로그인이 필요합니다."
LOGIN_FAILED = "사용자명 또는 비밀번호가 올바르지 않습니다."
USERNAME_TAKEN = "이미 사용 중인 사용자명입니다."
DATABASE_ERROR = "DB에 연결할 수 없거나 처리 중 오류가 발생했습니다."


@app.exception_handler(RequestValidationError)
def handle_validation_error(request: Request, error: RequestValidationError) -> JSONResponse:
    """422 응답. 인증 요청은 입력값(비밀번호)이 응답에 되돌아가지 않도록 input을 뺀다."""
    errors = error.errors()
    if request.url.path.startswith("/api/auth/"):
        errors = [{key: value for key, value in item.items() if key not in ("input", "ctx")} for item in errors]
    return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, content={"detail": jsonable_encoder(errors)})


@app.exception_handler(SQLAlchemyError)
def handle_database_error(request: Request, error: SQLAlchemyError) -> JSONResponse:
    """DB 오류는 내부 내용을 응답에 노출하지 않고 503으로 알린다. 자세한 내용은 서버 로그에 남긴다."""
    logger.error("DB 오류: %s %s: %s", request.method, request.url.path, error)
    return JSONResponse(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, content={"detail": DATABASE_ERROR})


@app.get("/api/health")
def health() -> dict[str, str]:
    """API 서버가 요청을 처리할 수 있는지 확인한다."""
    return {"status": "ok"}


@app.post("/api/auth/signup", status_code=status.HTTP_201_CREATED)
def signup(data: SignupRequest) -> User:
    """회원가입. 로그인은 하지 않으며 비밀번호는 argon2 해시로만 저장한다."""
    user = user_store.create(data.username, hash_password(data.password))
    if user is None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=USERNAME_TAKEN)
    return user


def current_user(request: Request) -> User:
    """쿠키의 세션으로 로그인한 사용자를 찾는다. 없거나 만료됐으면 401. T19에서 /api/tasks에 사용한다."""
    token = request.cookies.get(SESSION_COOKIE)
    user = user_store.find_user_by_session(hash_token(token), utc_now()) if token else None
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=LOGIN_REQUIRED)
    return user


@app.post("/api/auth/login")
def login(data: LoginRequest, request: Request, response: Response) -> User:
    """로그인. 세션을 DB에 만들고 HttpOnly 쿠키로 전달한다. 실패 사유는 구분하지 않는다."""
    found = user_store.find_credentials(data.username)
    # 없는 사용자명도 같은 해시 검증을 거쳐 응답 시간으로 존재 여부를 알 수 없게 한다.
    password_ok = verify_password(found[1] if found else DUMMY_HASH, data.password)
    if found is None or not password_ok:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=LOGIN_FAILED)
    old_token = request.cookies.get(SESSION_COOKIE)
    if old_token:
        user_store.delete_session(hash_token(old_token))
    token = new_session_token()
    now = utc_now()
    user_store.create_session(found[0].id, hash_token(token), now, session_expires_at(now))
    response.set_cookie(
        SESSION_COOKIE,
        token,
        max_age=SESSION_MAX_AGE,
        path="/",
        httponly=True,
        samesite="lax",
        secure=cookie_secure(),
    )
    return found[0]


@app.post("/api/auth/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(request: Request, response: Response) -> None:
    """로그아웃. 세션이 없어도 204이다."""
    token = request.cookies.get(SESSION_COOKIE)
    if token:
        user_store.delete_session(hash_token(token))
    response.delete_cookie(SESSION_COOKIE, path="/", httponly=True, samesite="lax", secure=cookie_secure())


@app.get("/api/auth/me")
def me(user: User = Depends(current_user)) -> User:
    """현재 로그인한 사용자."""
    return user


@app.get("/api/tasks")
def list_tasks(
    user: User = Depends(current_user),
    q: str | None = None,
    status: Status | None = None,
    priority: Priority | None = None,
) -> list[Task]:
    """로그인한 사용자의 할 일을 제목 검색(q)과 상태·우선순위 필터 AND 조건으로 등록 순서대로 반환한다."""
    return store.list(user.id, q=q, status=status, priority=priority)


@app.post("/api/tasks", status_code=status.HTTP_201_CREATED)
def create_task(data: TaskCreate, user: User = Depends(current_user)) -> Task:
    """할 일을 등록한다. 상태는 항상 TODO로 시작하고 소유자는 로그인한 사용자이다."""
    return store.create(user.id, data)


@app.patch("/api/tasks/{task_id}")
def update_task(task_id: int, data: TaskUpdate, user: User = Depends(current_user)) -> Task:
    """보낸 필드만 수정하고 나머지는 유지한다. 다른 사용자의 할 일은 없는 것처럼 404이다."""
    task = store.update(user.id, task_id, data.changes())
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=TASK_NOT_FOUND)
    return task


@app.delete("/api/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: int, user: User = Depends(current_user)) -> None:
    """할 일을 삭제한다. 다른 사용자의 할 일은 없는 것처럼 404이다."""
    if not store.delete(user.id, task_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=TASK_NOT_FOUND)
