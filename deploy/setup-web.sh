#!/usr/bin/env bash
# T14 Web 서버(Nginx) 구성 스크립트. 여러 번 실행해도 안전하다.
# 사용법: 프로젝트 루트에서 sudo bash deploy/setup-web.sh
# 하는 일: 설정 복사 → 기본 사이트(default) 연결 해제 → nginx -t 검사 → 통과하면 reload, 실패하면 원래대로 되돌림.
# 화면 파일은 /opt/task-flow/frontend(T13 setup-app.sh가 복사)를 사용하므로 T13이 먼저 되어 있어야 한다.
set -euo pipefail

if [ "$(id -u)" -ne 0 ]; then
  echo "[오류] sudo로 실행하세요: sudo bash deploy/setup-web.sh" >&2
  exit 1
fi

SRC="$(cd "$(dirname "$0")/.." && pwd)"
AVAIL=/etc/nginx/sites-available/task-flow
ENABLED=/etc/nginx/sites-enabled/task-flow
DEFAULT=/etc/nginx/sites-enabled/default

command -v nginx >/dev/null || { echo "[오류] nginx가 설치되어 있지 않습니다." >&2; exit 1; }
[ -f /opt/task-flow/frontend/index.html ] || { echo "[오류] /opt/task-flow/frontend가 없습니다. 먼저 sudo bash deploy/setup-app.sh를 실행하세요." >&2; exit 1; }

# 화면 파일을 최신으로 맞춘다(App 서버 코드 복사본과 동일하게).
rsync -a --delete "$SRC/frontend/" /opt/task-flow/frontend/
chown -R taskflow:taskflow /opt/task-flow/frontend

echo "[1/3] 설정 복사"
[ -f "$AVAIL" ] && cp -a "$AVAIL" "$AVAIL.bak"
cp "$SRC/deploy/nginx-task-flow.conf" "$AVAIL"
ln -sfn "$AVAIL" "$ENABLED"

echo "[2/3] 기본 사이트 연결 해제(80번 default_server 충돌 방지)"
DEFAULT_TARGET=""
if [ -L "$DEFAULT" ]; then
  DEFAULT_TARGET="$(readlink "$DEFAULT")"
  rm -f "$DEFAULT"
fi

echo "[3/3] 문법 검사 후 reload"
if nginx -t; then
  systemctl enable nginx >/dev/null 2>&1
  systemctl reload nginx || systemctl restart nginx
else
  echo "[오류] 설정 검사 실패. 원래 상태로 되돌립니다." >&2
  [ -n "$DEFAULT_TARGET" ] && ln -sfn "$DEFAULT_TARGET" "$DEFAULT"
  rm -f "$ENABLED"
  [ -f "$AVAIL.bak" ] && mv "$AVAIL.bak" "$AVAIL"
  exit 1
fi

echo "---- 확인 ----"
echo -n "화면 /            -> HTTP "; curl -s -m 3 -o /dev/null -w "%{http_code}\n" http://127.0.0.1/
echo -n "API  /api/health  -> "; curl -s -m 3 http://127.0.0.1/api/health; echo
echo -n "API  /api/tasks   -> HTTP "; curl -s -m 3 -o /dev/null -w "%{http_code}\n" http://127.0.0.1/api/tasks
echo "문제가 있으면: sudo tail -n 30 /var/log/nginx/error.log"
