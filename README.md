# Backend (FastAPI + uv)

이 프로젝트는 **uv**(파이썬 패키지/가상환경/실행 관리) + **FastAPI** 기반 백엔드 템플릿이야.

---

## 1) uv 사용법 (필수 커맨드)

### 설치 (처음 1회)
- uv: https://astral.sh/uv

### 의존성 설치/동기화
```bash
uv sync
```
- `pyproject.toml` 기준으로 venv(`.venv`) 만들고, `uv.lock`에 잠긴 버전대로 설치해.

### "uv 활성화"(가상환경 들어가기) — macOS / Windows

uv는 보통 `uv run ...`으로 실행하면 **자동으로 .venv를 사용**해서, 굳이 activate 안 해도 돼.
그래도 터미널에서 `python`, `pip`을 직접 치고 싶으면 아래처럼 활성화하면 됨.

#### macOS / Linux (zsh, bash)
```bash
# 프로젝트 루트에서
source .venv/bin/activate

# 해제
deactivate
```

#### Windows (PowerShell)
```powershell
# 프로젝트 루트에서
.\.venv\Scripts\Activate.ps1

# 해제
deactivate
```

#### Windows (cmd)
```bat
:: 프로젝트 루트에서
.venv\Scripts\activate.bat
```

> 참고: Windows PowerShell에서 스크립트 실행이 막히면(ExecutionPolicy) 아래 중 하나가 필요할 수 있음.
> - PowerShell을 관리자 권한으로 열고: `Set-ExecutionPolicy RemoteSigned`
> - 또는 현재 세션만: `Set-ExecutionPolicy -Scope Process Bypass`

### 서버 실행 (개발)
```bash
uv run uvicorn app.main:app --reload
```

### 코드 품질
```bash
uv run ruff check .
uv run mypy .
uv run pytest -q
```

---

## 2) 추천 폴더 구조(컨트롤러/서비스/스키마/레포지토리)

너가 말한 컨벤션으로 확정:
- **Router 폴더는 안 둠**
- **Controller = HTTP 레이어(엔드포인트 정의)**
- **Service = 비즈니스 로직**
- **Controller는 최대한 얇게(thin)**

권장 트리(현재 적용된 형태랑 동일한 방향):

```text
Backend/
  app/
    main.py                  # FastAPI 앱 생성, API 라우터 등록

    core/
      errors.py              # 공통 에러/예외
      config.py              # (나중에) 환경변수/설정

    api/
      api.py                 # 전체 API router 묶는 곳(include_router)

      controllers/           # "라우터" 대신 여기서 endpoint 정의
        health_controller.py # GET /health
        users_controller.py  # (예시) /users ...

      schemas/               # Pydantic request/response 모델
        health.py
        user.py

    services/                # 비즈니스 로직(유즈케이스)
      health_service.py
      user_service.py

    repositories/            # (DB 붙일 때) 데이터 접근 계층
      user_repo.py

  tests/
    test_health.py

  pyproject.toml
  uv.lock
```

---

## 3) 역할 분리: 어디에 “로직”을 두는 게 좋은가?

이번 프로젝트 컨벤션(추천):
- **Controller(컨트롤러)**: HTTP endpoint 정의. 최대한 얇게.
- **Service(서비스)**: 비즈니스 로직(유즈케이스). 대부분의 로직은 여기.
- **Schema(스키마)**: request/response 계약(Pydantic).
- **Repository(레포지토리)**: (DB 붙일 때) 데이터 접근.

### (1) Controller (컨트롤러) = Router 역할
- 책임: **HTTP 레이어**
  - path/method 정의 (`GET /users/{id}`)
  - request parsing/validation(스키마로)
  - dependency 주입(auth, db session 등)
  - response status code/headers
- 규칙: **얇게(thin)**
  - 컨트롤러는 “흐름을 연결”만 하고, 판단/연산은 서비스로 넘김.

### (2) Service (서비스)
- 책임: **유즈케이스(업무 로직)**
  - 예: “회원가입”, “로그인”, “프로필 수정”
  - 여러 repo 호출 조합, 권한 체크, 정책 적용
- 장점: HTTP/DB 변경에도 중심 로직이 덜 흔들림

### (3) Schema (스키마)
- 책임: **입출력 계약(Contract)**
  - Request/Response 모델(Pydantic)
  - validation 규칙(필드 타입/범위/regex 등)
- 예: `UserCreateRequest`, `UserResponse`

### (4) Repository (레포지토리)
- 책임: **데이터 접근(영속성)**
  - DB 붙었을 때: SQLAlchemy/SQLModel/Raw SQL 등으로 CRUD

중요한 포인트(추천):
- **Repository 안에 Pydantic Schema를 “영구적으로” 묶어두는 건 보통 비추**
  - 스키마는 API 계약, repo는 데이터 접근이라 경계가 달라.
  - repo는 보통 ORM 모델/도메인 엔티티를 다루고,
  - 서비스에서 schema ↔ entity 변환을 담당하는 편이 유지보수에 좋아.

해커톤 단순화(허용):
- repo에서 dict/row를 바로 schema로 만들어 반환하는 것도 가능
- 대신 나중에 규모 커지면 리팩터링 포인트가 될 수 있음

---

## 4) 요청 → 처리 흐름 예시

예: `POST /users` (회원 생성)

1. `routers/users.py`
   - `UserCreateRequest`로 body 검증
   - `user_controller.create_user(req)` 호출

2. `controllers/user_controller.py`
   - 정책/중복체크/비즈니스 로직
   - (DB 붙으면) `user_repo.create(...)` 호출

3. `repositories/user_repo.py`
   - DB insert/select
   - 결과 반환

4. `controllers`에서 `UserResponse` 형태로 가공

5. `routers`가 response 반환

---

## 5) 지금 당장 실행
```bash
uv sync
uv run uvicorn app.main:app --reload
```
- Health: http://127.0.0.1:8000/health
- Docs: http://127.0.0.1:8000/docs

---

## 확인하고 싶은 것(모호한 부분 질문)
DB는 나중에 붙인다고 했으니, 구조 컨벤션만 먼저 확정하면 돼.

1) 너희 팀은 `controllers`로 갈까 `services`로 갈까? (둘 다 가능)
2) “라우터에 로직”을 얼마나 허용할지: 
   - A) 라우터는 최대한 얇게(권장)
   - B) 해커톤이라 라우터에 로직 꽤 넣고, repo는 나중에만
3) response 형태는 공통 포맷으로 감쌀까?
   - 예: `{ "success": true, "data": ... }` 같은 래핑

이 3개만 답 주면, 그 컨벤션에 맞춰서 **실제 파일/폴더까지 자동으로 생성**해줄게.
