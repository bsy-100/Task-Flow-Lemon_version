from fastapi import FastAPI, status

from .schemas import Task, TaskCreate
from .store import MemoryTaskStore

app = FastAPI(title="Task Flow API")
store = MemoryTaskStore()


@app.get("/api/health")
def health() -> dict[str, str]:
    """API 서버가 요청을 처리할 수 있는지 확인한다."""
    return {"status": "ok"}


@app.get("/api/tasks")
def list_tasks() -> list[Task]:
    """할 일 목록을 등록 순서로 반환한다."""
    return store.list()


@app.post("/api/tasks", status_code=status.HTTP_201_CREATED)
def create_task(data: TaskCreate) -> Task:
    """할 일을 등록한다. 상태는 항상 TODO로 시작한다."""
    return store.create(data)
