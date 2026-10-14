"""테이블을 만들고 tasks에 user_id가 없으면 추가한다.

실행: python -m backend.init_db
      python -m backend.init_db --delete-existing-tasks   (기존 tasks 행을 지우고 user_id 추가)

없는 테이블만 만들며 이미 있는 테이블의 데이터는 바꾸지 않는다.
기존 tasks에 행이 있으면 소유자를 알 수 없으므로 옵션 없이는 user_id를 추가하지 않고 중단한다.
"""

import sys

from sqlalchemy import inspect, text

from .database import Base, engine
from .models import SessionRow, TaskRow, UserRow


def migrate_tasks_user_id(delete_existing: bool) -> bool:
    """tasks.user_id(NOT NULL, users FK)를 추가한다. 이미 있으면 아무것도 하지 않고 False를 반환한다."""
    columns = {column["name"] for column in inspect(engine).get_columns(TaskRow.__tablename__)}
    if "user_id" in columns:
        return False
    with engine.begin() as connection:
        count = connection.execute(text("SELECT COUNT(*) FROM tasks")).scalar_one()
        if count:
            if not delete_existing:
                raise SystemExit(
                    f"tasks에 소유자 없는 행이 {count}개 있어 user_id를 추가하지 않았습니다. "
                    "지워도 되면 --delete-existing-tasks 옵션으로 다시 실행하세요."
                )
            connection.execute(text("DELETE FROM tasks"))
            print(f"기존 tasks {count}행을 삭제했습니다.")
        connection.execute(text("ALTER TABLE tasks ADD COLUMN user_id INT NOT NULL AFTER id"))
        connection.execute(text("ALTER TABLE tasks ADD INDEX ix_tasks_user_id (user_id)"))
        connection.execute(
            text(
                "ALTER TABLE tasks ADD CONSTRAINT fk_tasks_user_id "
                "FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE"
            )
        )
    return True


def main() -> None:
    delete_existing = "--delete-existing-tasks" in sys.argv[1:]
    existing = set(inspect(engine).get_table_names())
    # create_all은 없는 테이블만 만든다. users는 tasks·sessions보다 먼저 만들어진다.
    Base.metadata.create_all(engine)
    for model in (UserRow, SessionRow, TaskRow):
        name = model.__tablename__
        print(f"{name} 테이블이 이미 있어 변경하지 않았습니다." if name in existing else f"{name} 테이블을 만들었습니다.")
    if TaskRow.__tablename__ in existing:
        if migrate_tasks_user_id(delete_existing):
            print("tasks에 user_id 컬럼을 추가했습니다.")
        else:
            print("tasks.user_id가 이미 있어 변경하지 않았습니다.")


if __name__ == "__main__":
    main()
