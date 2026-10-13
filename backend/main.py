from fastapi import FastAPI

app = FastAPI(title="Task Flow API")


@app.get("/api/health")
def health() -> dict[str, str]:
    """API 서버가 요청을 처리할 수 있는지 확인한다."""
    return {"status": "ok"}
