from datetime import datetime, timezone
from threading import Lock

from .schemas import Status, Task, TaskCreate


class MemoryTaskStore:
    """서버 메모리에 할 일을 보관한다. API를 재시작하면 데이터가 사라진다."""

    def __init__(self) -> None:
        self._tasks: dict[int, Task] = {}
        self._next_id = 1
        # 동기 엔드포인트는 스레드에서 실행되므로 id 발급과 저장을 함께 잠근다.
        self._lock = Lock()

    def list(self) -> list[Task]:
        with self._lock:
            return sorted(self._tasks.values(), key=lambda task: task.id)

    def create(self, data: TaskCreate) -> Task:
        with self._lock:
            task = Task(
                id=self._next_id,
                title=data.title,
                description=data.description,
                status=Status.TODO,
                priority=data.priority,
                due_date=data.due_date,
                created_at=datetime.now(timezone.utc).replace(microsecond=0),
            )
            self._tasks[task.id] = task
            self._next_id += 1
            return task
