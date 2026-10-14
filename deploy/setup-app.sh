#!/usr/bin/env bash
# T13 App 서버 구성 스크립트(같은 WSL 안에서 App 서버를 흉내 낼 때 사용). 여러 번 실행해도 안전하다.
# 사용법: 프로젝트 루트에서 sudo bash deploy/setup-app.sh
# 하는 일: taskflow 사용자 → /opt/task-flow에 코드 복사 → 가상환경·패키지 → .env 복사(권한 600) → systemd 등록·기동 → 확인
# .env 값은 화면에 출력하지 않는다. 기존 DB·테이블은 건드리지 않는다.
set -euo pipefail

if [ "$(id -u)" -ne 0 ]; then
  echo "[오류] sudo로 실행하세요: sudo bash deploy/setup-app.sh" >&2
  exit 1
fi

SRC="$(cd "$(dirname "$0")/.." && pwd)"
DEST=/opt/task-flow
APP_USER=taskflow

[ -f "$SRC/.env" ] || { echo "[오류] $SRC/.env가 없습니다." >&2; exit 1; }

# 포트 8000을 다른 프로세스(개발용 uvicorn 등)가 쓰고 있으면 중단한다. 이미 task-flow-api(또는 예전 이름 task-flow)가 쓰는 경우는 통과한다.
if ss -ltn 2>/dev/null | grep -q ':8000 ' && ! systemctl is-active --quiet task-flow-api && ! systemctl is-active --quiet task-flow; then
  echo "[오류] 8000번 포트를 다른 프로그램이 사용 중입니다. 개발용 uvicorn을 Ctrl+C로 끈 뒤 다시 실행하세요." >&2
  exit 1
fi

echo "[1/5] 실행 사용자 확인"
id "$APP_USER" >/dev/null 2>&1 || useradd --system --home "$DEST" --shell /usr/sbin/nologin "$APP_USER"

echo "[2/5] 코드 복사 ($DEST)"
mkdir -p "$DEST"
rsync -a --delete --exclude '.git' --exclude '.venv' --exclude '.env' --exclude '__pycache__' "$SRC/" "$DEST/"

echo "[3/5] .env 복사(권한 600)"
install -o "$APP_USER" -g "$APP_USER" -m 600 "$SRC/.env" "$DEST/.env"
chown -R "$APP_USER:$APP_USER" "$DEST"

echo "[4/5] 가상환경과 패키지"
[ -x "$DEST/.venv/bin/python" ] || sudo -u "$APP_USER" python3 -m venv "$DEST/.venv"
sudo -u "$APP_USER" "$DEST/.venv/bin/pip" install -q -r "$DEST/requirements.txt"

echo "[5/5] systemd 등록·기동"
# 예전 이름(task-flow) 서비스가 있으면 같은 8000번을 쓰므로 중지·제거한다.
if [ -f /etc/systemd/system/task-flow.service ]; then
  systemctl disable --now task-flow >/dev/null 2>&1 || true
  rm -f /etc/systemd/system/task-flow.service
fi
cp "$DEST/deploy/task-flow-api.service" /etc/systemd/system/task-flow-api.service
systemctl daemon-reload
systemctl enable task-flow-api >/dev/null 2>&1
systemctl restart task-flow-api

for _ in $(seq 1 10); do
  curl -s -m 2 -o /dev/null http://127.0.0.1:8000/api/health && break
  sleep 1
done

echo "---- 확인 ----"
systemctl is-active task-flow-api
echo -n "/api/health -> "; curl -s -m 3 http://127.0.0.1:8000/api/health; echo
echo -n "/api/tasks  -> HTTP "; curl -s -m 3 -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8000/api/tasks
echo "문제가 있으면: journalctl -u task-flow-api -n 50 --no-pager"
