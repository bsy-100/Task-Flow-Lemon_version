from datetime import datetime, timezone
from threading import Lock

from .schemas import Priority, Status, Task, TaskCreate


class MemoryTaskStore:
    """서버 메모리에 할 일을 보관한다. API를 재시작하면 데이터가 사라진다."""

    def __init__(self) -> None:
        self._tasks: dict[int, Task] = {}
        self._next_id = 1
        # 동기 엔드포인트는 스레드에서 실행되므로 id 발급과 저장을 함께 잠근다.
        self._lock = Lock()

    def list(
        self,
        q: str | None = None,
        status: Status | None = None,
        priority: Priority | None = None,
    ) -> list[Task]:
        """조건을 모두 만족하는 할 일을 id 순서로 반환한다. None 조건은 무시한다."""
        query = (q or "").strip().lower()
        with self._lock:
            tasks = sorted(self._tasks.values(), key=lambda task: task.id)
        return [
            task
            for task in tasks
            if (not query or query in task.title.lower())
            and (status is None or task.status == status)
            and (priority is None or task.priority == priority)
        ]

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

    def update(self, task_id: int, changes: dict[str, object]) -> Task | None:
        """전달된 필드만 바꾼다. 없는 id는 None을 반환한다."""
        with self._lock:
            task = self._tasks.get(task_id)
            if task is None:
                return None
            updated = task.model_copy(update=changes)
            self._tasks[task_id] = updated
            return updated

    def delete(self, task_id: int) -> bool:
        """삭제했으면 True, 없는 id면 False를 반환한다."""
        with self._lock:
            return self._tasks.pop(task_id, None) is not None
