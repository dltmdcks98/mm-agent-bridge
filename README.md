# mm-agent-bridge

Mattermost 요청을 받아 Agent 작업으로 연결하는 브리지 서비스입니다.

## 개요

이 프로젝트는 아래 계층을 연결합니다.
- Mattermost (입력)
- Bridge Server (요청 수신/검증/큐잉)
- Agent 실행 계층 (Codex/Claude 등)
- 데이터베이스 (상태 저장)

## 핵심 원칙

- 저장소는 Stateless 유지
- 런타임 데이터는 DB에만 저장
- 개인 데이터/원본 대화 로그/시크릿은 저장소에 저장 금지

## 현재 구현 범위

- `POST /webhooks/mattermost`: 요청 수신 후 DB에 저장
- `POST /webhooks/mattermost`: Mattermost 토큰 검증 후 DB에 저장
- `incoming_messages`, `agent_tasks` 테이블 기반 큐잉
- 동일 `request_id` 중복 요청 방지(409)
- 중복 처리 시 DB 유니크 제약 기반으로 원자적 롤백 보장
- `GET /healthz` 헬스체크
- `GET /readyz` DB 연결 준비 상태 체크
- `GET /tasks/{task_id}` 작업 상태/요약 조회
- 백그라운드 워커(`python -m mm_agent_bridge.worker`)로 큐 작업 소비
- `response_url`이 있으면 워커가 실행 결과를 Mattermost로 콜백 전송
- 실행기 어댑터: `mock` 또는 `codex_cli` 선택 가능

## 로컬 실행

1. 의존성 설치

```bash
make setup
```

2. 환경 변수 설정

```bash
cp .env.example .env
```

- `MM_BRIDGE_MATTERMOST_WEBHOOK_TOKEN`에 Mattermost에서 발급한 토큰을 설정하세요.
- 실제 실행을 원하면 `.env`에서 `MM_BRIDGE_EXECUTOR_BACKEND=codex_cli`로 설정하세요.

3. PostgreSQL 시작

```bash
make up
```

4. 마이그레이션 적용

```bash
make migrate
```

5. 애플리케이션 실행

```bash
make run
```

6. 워커 실행

```bash
make worker
```

한 건만 처리할 때:

```bash
make worker-once
```

## 테스트 / 린트

```bash
make test
make lint
```

## 실행기 설정

- `MM_BRIDGE_EXECUTOR_BACKEND`: `mock`(기본) 또는 `codex_cli`
- `MM_BRIDGE_CODEX_CLI_COMMAND`: Codex CLI 실행 파일명 (기본 `codex`)
- `MM_BRIDGE_CODEX_CLI_ARGS`: Codex CLI 추가 인자(공백 구분)
- `MM_BRIDGE_EXECUTOR_TIMEOUT_SECONDS`: 실행 타임아웃 초

## 마이그레이션 파일

- `sql/001_init.sql`
- `sql/002_add_response_url.sql`

## CI

- GitHub Actions: `.github/workflows/ci.yml`
- 실행 항목: `ruff check .`, `pytest`

## 프로젝트 구조

- `app/src` → 애플리케이션 코드
- `app/tests` → 테스트 코드
- `docs` → 아키텍처 문서
- `sql` → 스키마 및 마이그레이션
- `infra` → docker/deployment 설정
- `.codex/agents` → 프로젝트 로컬 서브에이전트 설정
