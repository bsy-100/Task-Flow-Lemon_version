# Task Flow PLAN
## 작업 원칙
한 번에 아래 작업 하나만 구현한다. 실제 확인 전에는 완료로 표시하지 않는다.
상태는 [ ] 미완료, [x] 확인 완료로 관리하고 확인 결과를 각 항목 아래 기록한다.
## 2장: 브라우저 앱
- [x] T01: frontend/index.html, styles.css, app.js 생성. 제목 입력·등록·목록만 구현한다.
  확인: 두 항목 등록, 빈 제목 거절. 이 단계에서 새로고침하면 사라져도 정상이다.
  기록(2026-10-13): frontend/index.html, styles.css, app.js 생성.
  Node DOM 스텁 테스트 통과(두 항목 등록, 빈·공백 제목 거절, 101자 거절, 100자 등록, HTML 글자 표시).
  http.server 5500에서 세 파일 200 응답.
  Windows 브라우저(http://localhost:5500, WSL localhostForwarding)에서 사용자 확인 정상. 남은 오류 없음.
- [x] T02: localStorage(task-flow-v1) 저장·복원.
  확인: 새로고침 후 유지. 손상된 저장값을 자동 덮어쓰지 않는다.
  기록(2026-10-13): frontend/app.js 저장·복원 추가, index.html에 저장 오류 영역·버튼 id 추가, styles.css 비활성 스타일.
  Node 스텁 테스트 통과(저장, 재실행 후 복원, 손상값 4종에서 등록 중지·원래 값 유지, 저장 실패 시 되돌림, T01 회귀).
  http.server 세 파일 200 응답.
  Windows 브라우저에서 사용자 확인 정상(새로고침 후 유지, 손상값 입력 시 등록 중지). 남은 오류 없음.
- [x] T03: 상태 변경, 수정, 삭제 확인.
  확인: 삭제 취소 시 유지. 다른 항목이 수정되지 않는다.
  기록(2026-10-13): frontend/app.js 상태 선택·제목 수정·삭제 확인 추가(id 기준), styles.css 항목 버튼·완료 스타일.
  설명 수정은 T04에서 다룬다. 저장 실패 시 변경을 되돌린다. status 없는 기존 저장값은 TODO로 읽는다.
  Node 스텁 테스트 12개 통과(상태 변경, 빈 제목 수정 거절, 수정·취소·Esc, 삭제 취소 유지, 삭제 시 해당 항목만, 재실행 후 유지, 저장 실패 되돌림, 회귀).
  Windows 브라우저에서 사용자 확인 정상(상태 변경·수정·삭제 취소·삭제, 새로고침 후 유지). 남은 오류 없음.
- [x] T04: 설명·우선순위·마감일·검색·필터·지연 표시.
  확인: 필터 중 수정·삭제, 어제 마감 TODO의 지연 표시.
  기록(2026-10-13): index.html 등록 폼(우선순위·마감일·설명)과 검색·필터 영역 추가, app.js 필드·검증·수정 폼·필터·지연 표시, styles.css 배지·필터 스타일.
  수정 폼에서 제목·설명·우선순위·마감일을 함께 수정한다. 이전 단계 저장값은 빠진 필드를 기본값으로 읽는다.
  Node 스텁 테스트 통과: T04 12개(기본값, 검증, 지연 표시, 검색·필터 AND, 필터 중 수정·삭제, 호환·손상값, 새로고침 유지), T03 회귀 12개.
  Windows 브라우저에서 사용자 확인 정상(어제 마감 TODO 지연 표시, 필터 AND, 필터 중 수정·삭제, 새로고침 유지). 남은 오류 없음.
## 3장: API
- [x] T05: API-SPEC.md 작성, FastAPI /api/health 구현.
  확인: curl로 200과 status=ok.
  기록(2026-10-13): API-SPEC.md(T05~T08 계약), backend/__init__.py, backend/main.py, requirements.txt(fastapi 0.143.0, uvicorn 0.54.0), .gitignore 생성.
  실행: .venv/bin/python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 (Python 3.10.12)
  결과: curl -i /api/health → 200, {"status":"ok"}. /docs 200, 없는 경로 404. 남은 오류 없음.
- [x] T06: 메모리 기반 /api/tasks GET과 POST.
  확인: /docs에서 등록 후 조회. 입력 위반은 422.
  기록(2026-10-13): backend/schemas.py(TaskCreate·Task 검증), backend/store.py(메모리 저장소), backend/main.py에 GET·POST /api/tasks 추가.
  수정: due_date strict 검증이 "2026-10-20"까지 거절해 YYYY-MM-DD 형식 검사 후 날짜 변환하도록 변경.
  실행: 포트 8001에서 uvicorn 실행 후 urllib 스크립트로 확인. 26개 통과(기본값 201, 경계값 201, 위반 18종 422, GET id 순서, 재시작 후 빈 목록).
  /docs 화면에서 사용자 확인 정상(등록 201, 빈 제목 422, 등록 후 조회). 남은 오류 없음.
- [x] T07: PATCH·DELETE와 필터 구현.
  확인: 미전달 필드 유지, 없는 ID 404, 삭제 204.
  기록(2026-10-13): backend/schemas.py TaskUpdate(보낸 필드만 수정, due_date만 null 허용), backend/store.py update·delete·필터, backend/main.py PATCH·DELETE와 q·status·priority 쿼리.
  실행: 포트 8001에서 uvicorn 실행 후 urllib 스크립트로 확인. T07 41개 통과(부분 수정 시 나머지·다른 항목 유지, due_date null 삭제, PATCH 위반 14종 422, 없는 id 404, 삭제 204·재삭제 404, q·status·priority AND, 잘못된 필터 422). T06 회귀 25개 통과.
  남은 오류 없음.
- [x] T08: 프런트엔드 저장 처리를 API 호출로 교체.
  확인: 화면과 curl 목록이 같음. API 중지 시 오류 표시.
  기록(2026-10-13): frontend/app.js localStorage 제거, 목록·등록·상태 변경·수정·삭제를 /api 호출로 교체, 검색·필터는 API 쿼리(q·status·priority)로 조회, 지연 표시는 화면에서 계산.
  backend/main.py에 frontend 정적 파일 제공 추가(같은 주소, CORS 불필요), index.html 오류 영역 id를 api-error로 변경, API-SPEC.md에 화면 제공 방식 추가.
  실행: 포트 8001 uvicorn + Node 스텁(실제 HTTP 요청) 테스트 12개 통과(등록 후 화면·curl 목록 동일, 필터 중 수정·삭제, 404 안내, API 중지 시 오류 표시). T07 API 회귀 41개 통과.
  Windows 브라우저(http://localhost:8000)에서 사용자 확인 정상(화면·curl 목록 동일, API 중지 시 오류 표시). 남은 오류 없음.
## 4장: DB
- [x] T09: MariaDB 전용 사용자·DB와 .env 준비. 접속 확인.
  기록(2026-10-13): MariaDB 10.6.23(127.0.0.1:3306). 사용자가 task_flow DB와 task_flow_app@localhost 생성, .env 작성. .env.example(가짜 값) 추가, .env 권한 600, .gitignore 대상 확인.
  결과: .env 정보로 mariadb 접속 성공(CURRENT_USER task_flow_app@localhost, DATABASE task_flow, utf8mb4_general_ci, 테이블 없음).
  참고: 권한이 ALL PRIVILEGES(DROP 포함)로 부여됨. 비밀번호가 짧아 서버 분리(T12) 전 변경 권장.
- [x] T10: backend/database.py, models.py, init_db.py 생성.
  확인: python -m backend.init_db 실행 후 tasks 테이블 확인.
  기록(2026-10-13): requirements.txt에 SQLAlchemy 2.0.54, PyMySQL 1.2.3 추가. database.py(.env·환경변수 읽기, 엔진·세션), models.py(TaskRow), init_db.py(없는 테이블만 생성) 작성.
  실행: python -m backend.init_db 2회 → 1회차 생성, 2회차 "이미 있어 변경하지 않음".
  결과: DESCRIBE tasks로 id(AUTO_INCREMENT PK)·title varchar(100)·description varchar(2000)·status·priority ENUM·due_date date NULL·created_at datetime 확인. InnoDB, utf8mb4, 0행. 접속 정보 누락 시 안내 오류 확인. 남은 오류 없음.
- [x] T11: API 메모리 저장을 DB로 교체.
  확인: 등록한 행을 SQL로 조회. API 재시작 후 데이터 유지.
  기록(2026-10-13): backend/store.py를 DbTaskStore(MariaDB, 메서드 동일)로 교체, backend/main.py가 DbTaskStore 사용·DB 오류 시 503 응답. API-SPEC.md에 503 추가.
  실행: 포트 8001 uvicorn + urllib 스크립트. 31개 통과(등록·부분 수정·422·404·204, q·status·priority AND, q의 %·_ 글자 검색, 2000자 설명·이모지 저장).
  결과: 등록 행을 mariadb SELECT로 확인. API 재시작 후 같은 id·수정 내용 유지. 틀린 DB 비밀번호로 실행 시 /api/tasks 503, 로그에 비밀번호 미노출.
  테스트 항목([T11검증] 제목)은 확인 후 삭제해 tasks는 0행. AUTO_INCREMENT는 6부터 시작. 남은 오류 없음.
## 5장: 서버 분리
- [x] T12: DB 서버 구성 후 App 서버에서 SELECT 1 확인.
  기록: 사용자가 별도로 확인했다고 보고함(세부 출력·구성 내용은 기록되지 않음).
- [x] T13: App 서버 코드·가상환경·환경변수·systemd 구성.
  확인: App에서 /api/health 응답.
  기록: 변경 파일 deploy/task-flow-api.service, deploy/setup-app.sh(추가). 같은 WSL 안에서 App 서버를 흉내 내어 구성함(별도 서버 아님).
  실행 명령: sudo bash deploy/setup-app.sh (taskflow 사용자, /opt/task-flow 코드 복사, 가상환경·패키지, .env 복사 600, systemd 등록·기동). 사용자가 직접 실행.
  서비스 이름: task-flow-api.service(예전 task-flow.service는 제거). 시작: sudo systemctl start task-flow-api.service
  확인: systemctl is-active=active, is-enabled=enabled, 프로세스 사용자 taskflow, /opt/task-flow/.env 권한 600(taskflow), /api/health {"status":"ok"}, /api/tasks 200.
  서비스가 0.0.0.0:8000이므로 실제 서버에서는 8000번을 Web 서버만 허용. 서버 재부팅 후 자동 기동은 미확인.
- [x] T14: Web 서버 Nginx와 정적 파일·/api 프록시 구성.
  확인: Web 주소로 등록, DB 저장, App 재시작 후 유지.
  기록: 변경 파일 deploy/nginx-task-flow.conf, deploy/setup-web.sh(추가). 80번 포트, 화면은 /opt/task-flow/frontend 정적 제공, /api/는 127.0.0.1:8000 프록시, 기본 사이트 연결 해제. 같은 WSL 안 시뮬레이션.
  실행 명령: sudo bash deploy/setup-web.sh (사용자가 직접 실행), sudo systemctl restart task-flow-api.service (사용자가 직접 실행).
  확인: nginx active, / 200, /api/health ok, /api/tasks 200. Nginx 경유 POST로 등록(id=3) → App 재시작(프로세스 가동 44초로 확인) 후 같은 행이 조회됨 → 테스트 행 삭제.
  기록(2026-10-14): http://127.0.0.1 브라우저 화면 렌더링·동작을 사용자가 확인, 정상.
  미확인: 서버 재부팅 후 자동 기동. 남은 문제: main.py가 /에 frontend를 항상 mount(Nginx 뒤에서는 동작에 영향 없음, 미수정).
## 6장: 다중 사용자(회원가입·로그인)
- [x] T15: API-SPEC.md에 인증 계약 작성(POST /api/auth/signup·login·logout, GET /api/auth/me, 401·409·422, 쿠키 속성, 세션 7일). argon2-cffi를 requirements.txt에 기록.
  확인: 문서 검토. PRD F10~F14와 계약이 일치한다.
  기록(2026-10-14): API-SPEC.md에 인증 장(사용자·세션·쿠키 규칙, signup·login·logout·me, 401·409 코드, /api/tasks 로그인 필수·타인 id 404) 추가. requirements.txt에 argon2-cffi==25.1.0 기록(PyPI 최신 25.1.0 확인, 아직 설치하지 않음 — T17에서 설치).
  확인: PRD F10~F14 항목(사용자명·비밀번호 규칙, 7일 세션, HttpOnly 쿠키, 로그인 실패 동일 응답, 타인 id 404, 미로그인 401)을 계약과 대조해 일치함. 코드 변경·실행 없음(문서 단계).
  결정: 로그인 시 기존 세션은 교체, 로그아웃은 멱등 204, 만료는 7일 고정, 가입은 쿠키를 발급하지 않음(가입 후 별도 로그인).
- [x] T16: users·sessions 테이블 모델 추가, tasks.user_id(FK) 추가, init_db 갱신.
  확인: 테이블 구조 조회. 기존 tasks 행은 사용자 승인에 따라 정리 가능하나 삭제 전 대상 행을 먼저 보여 준다.
  기록(2026-10-14): backend/models.py에 UserRow(username, username_key 소문자 유일값, password_hash)·SessionRow(token_hash 해시만, expires_at)·TaskRow.user_id(FK, ON DELETE CASCADE) 추가. backend/init_db.py가 없는 테이블만 만들고 tasks.user_id를 추가(기존 행이 있으면 --delete-existing-tasks 없이는 중단).
  실행: .venv/bin/python -m backend.init_db (옵션 없이: 기존 4행 때문에 중단·행 유지 확인) → --delete-existing-tasks → 다시 실행(모두 변경 없음).
  삭제: 사용자 승인에 따라 T14 테스트 행 4개(id 6~9: NICE, TO, MEET, YOU)만 삭제. 삭제 전 목록을 확인함.
  결과: SHOW CREATE TABLE로 users·sessions·tasks(user_id NOT NULL, 인덱스, FK) 확인. 롤백 트랜잭션에서 없는 user_id로 task 등록 거절, 대소문자만 다른 사용자명 거절, 사용자 삭제 시 task·session 연쇄 삭제 확인(롤백 후 0행).
  남은 문제: tasks.user_id가 NOT NULL이라 아직 user_id를 넣지 않는 현재 /api/tasks 등록(POST)은 실패한다(T19에서 해결). /opt/task-flow의 배포본과 http://127.0.0.1 화면도 T21 전까지 등록이 안 된다. 같은 DB를 쓰므로 지금 이미 영향이 있다.
- [x] T17: POST /api/auth/signup 구현(argon2 해시, 사용자명 검증, 중복 409).
  확인: DB에 해시만 저장, 중복·형식 위반·비밀번호 길이 위반 거절, 응답·로그에 비밀번호 미노출.
  기록(2026-10-14): backend/auth.py(argon2 해시), backend/user_store.py(DbUserStore), backend/schemas.py(SignupRequest·User), backend/main.py에 POST /api/auth/signup과 인증 경로 422 응답에서 입력값(input)을 빼는 핸들러 추가. .venv에 requirements.txt 설치(Python 3.14.4, argon2-cffi 25.1.0).
  실행: 포트 8001 uvicorn + urllib 스크립트. 48개 중 47개 통과(가입 201·응답은 id·username만·쿠키 미발급, 대소문자만 다른 이름·같은 이름 409, 사용자명 3·21자·공백·개행·한글·하이픈 422와 4·20자 허용, 비밀번호 7·73자·한글 25자(75바이트) 422와 8·72자·한글 24자·앞뒤 공백 허용, 추가 필드·누락·타입 오류·깨진 JSON 422). 실패 1건은 스크립트 오탐(응답의 "Extra inputs" 문구가 "input" 검사에 걸림, 입력값 자체는 응답에 없음). /api/health·GET /api/tasks·tasks 검증 422 형식 회귀 정상.
  결과: DB에는 $argon2id$ 해시(97자)만 저장, 평문 포함 행 0, 서버 로그에 비밀번호 0건. 422 응답에 비밀번호 미포함.
  정리: 테스트 사용자(t17 접두사)만 삭제해 users 0행. AUTO_INCREMENT는 계속 증가.
  남은 문제: 같은 이름 동시 가입은 유일 제약+409 처리로 대비했으나 동시 요청 테스트는 하지 않음. POST /api/tasks는 T19 전까지 계속 실패.
- [x] T18: POST /api/auth/login·logout, GET /api/auth/me 구현(DB 세션, HttpOnly 쿠키).
  확인: 로그인 후 /me 200, 로그아웃 후 같은 쿠키 401, 틀린 비밀번호와 없는 사용자명이 같은 응답, API 재시작 후 세션 유지, DB에 토큰 원문 없음.
  기록(2026-10-14): backend/auth.py(비밀번호 검증·토큰 생성·SHA-256 해시·Secure 설정 읽기), backend/user_store.py(로그인 조회·세션 생성·삭제·조회), backend/schemas.py(LoginRequest), backend/main.py에 POST /api/auth/login·logout, GET /api/auth/me와 current_user 의존성(T19에서 사용) 추가. .env.example에 COOKIE_SECURE(가짜 값 false) 추가.
  동작: 쿠키 session(HttpOnly, SameSite=Lax, Path=/, Max-Age=604800, COOKIE_SECURE=true일 때 Secure). 재로그인 시 이전 세션 삭제, 로그인 시 해당 사용자의 만료 세션 정리. 없는 사용자명도 가짜 해시를 검증해 응답 시간 차이를 줄임.
  실행: 포트 8001 uvicorn 2회(COOKIE_SECURE=false, 재시작 후 true) + urllib 스크립트. 33개 전부 통과: 쿠키 없이 me 401, 틀린 비밀번호·없는 사용자·형식 틀린 사용자명이 동일한 401 본문(쿠키 미발급), 로그인 422(추가 필드·누락·201자·숫자)에 입력값 미포함, 대소문자 무시 로그인 200과 쿠키 속성, DB에 해시만 저장(토큰 원문 없음·만료 168시간), 사용자 A·B 세션 분리, 재로그인 시 이전 토큰 401, 가짜·5000자 쿠키 401, 만료 세션 401, API 재시작 후 세션 유지, 로그아웃 204·쿠키 삭제(Max-Age=0)·같은 쿠키 401·DB 행 삭제, 반복·쿠키 없는 로그아웃 204, Secure 설정 시 Secure 속성, health·GET /api/tasks 회귀. 서버 로그에 비밀번호·토큰 원문 0건.
  정리: 테스트 사용자(chk_ 접두사 2명, 세션은 연쇄 삭제)만 삭제해 users·sessions 0행.
  남은 문제: 로그인 시도 횟수 제한은 없음(PRD 범위 밖). 만료 세션은 로그인 때만 정리하므로 로그인하지 않는 사용자의 만료 행은 남음. POST /api/tasks는 T19 전까지 계속 실패.
- [x] T19: /api/tasks 전체를 로그인 필수로 바꾸고 모든 조회·수정·삭제에 user_id 조건 적용.
  확인: 미로그인 401, 사용자 A·B 목록 분리, B가 A의 id를 PATCH·DELETE하면 404. 기존 T06~T11 동작(검증·필터)은 회귀 확인.
  기록(2026-10-14): backend/store.py의 list·create·update·delete가 user_id를 받아 모든 쿼리에 소유자 조건 적용(_get_own), backend/main.py의 /api/tasks 4개 엔드포인트에 current_user 의존성 추가. 응답 Task에 user_id는 노출하지 않음. API 계약(필드·검증·필터)은 그대로.
  실행: 포트 8001 uvicorn 2회(재시작 포함) + urllib 스크립트. 44개 전부 통과: 미로그인 GET·POST·PATCH·DELETE 401(본문이 잘못돼도 401), 가짜 쿠키 401, health는 로그인 없이 200, A·B 목록 분리, B가 A의 id를 PATCH·DELETE하면 404이며 없는 id와 동일한 본문, A 항목 변경 없음, 응답 키에서 user_id 제외, 등록 기본값·경계값(100자·2000자·이모지), 부분 수정·due_date null, 수정·등록 위반 422(user_id·id 추가 필드 포함), status·priority·q 필터 AND·%·_ 글자 검색·공백 q·잘못된 필터 422, 삭제 204·재삭제 404, 재시작 후 사용자별 데이터 유지, 로그아웃 후 tasks 401(다른 사용자는 정상). 서버 로그에 비밀번호·토큰 0건. DB에서 사용자별 행(A 3, B 1) 확인.
  정리: 테스트 사용자(chk_ 접두사, tasks·sessions 연쇄 삭제)만 삭제해 users·sessions·tasks 0행.
  남은 문제: 배포본(/opt/task-flow)과 프런트엔드는 아직 옛 버전이라 http://127.0.0.1 화면에서는 등록이 안 됨(T20·T21에서 해결). 타인의 id에 잘못된 본문을 보내면 소유 확인 전에 422가 나옴(정보 노출 없음).
- [ ] T20: 프런트엔드 회원가입·로그인 폼, 사용자명 표시, 로그아웃 버튼. 401이면 로그인 화면으로 이동.
  확인: 가입→로그인→등록→로그아웃→다른 계정 로그인 시 목록이 다름. 사용자명·입력은 글자로 표시.
- [ ] T21: App·Web 서버에 반영(/opt/task-flow 복사, 의존성 설치, init_db, systemd 재시작, Nginx 쿠키·헤더 전달 확인).
  확인: http://127.0.0.1 에서 두 사용자 시나리오 전체, App 재시작 후 로그인 유지.
## 실행 기준
T01~T04: python3 -m http.server 5500 --bind 127.0.0.1 --directory frontend
T05~T11: 가상환경에서 python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
실제 존재하는 파일을 확인한 뒤 명령을 실행한다.
## 기록
각 작업에 변경 파일, 실행 명령, 실제 확인 결과, 남은 오류를 기록한다.
정상 동작을 확인한 작업 단위로 Git 커밋한다.