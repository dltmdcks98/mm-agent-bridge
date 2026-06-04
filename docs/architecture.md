# Architecture

## Overview

Mattermost 입력을 Agent 작업 큐로 변환하고, 상태를 데이터베이스에 저장하는 브리지 서비스입니다.
저장소에는 코드/설정/문서/SQL만 유지하며 런타임 데이터는 DB에만 저장합니다.

## Components

### 1) Mattermost Webhook Ingress

- 엔드포인트: `POST /webhooks/mattermost`
- 입력 검증: `request_id`, `user_id`, `channel_id`, `text`
- 중복 요청 방지: DB 유니크 제약(`request_id`) 기반으로 처리

### 2) Bridge Service

- 요청을 `incoming_messages`로 저장
- 후속 실행 단위를 `agent_tasks(status=queued)`로 생성
- 워커가 `queued` 작업을 소비해 `completed/failed` 상태로 갱신
- `response_url`이 있는 메시지는 워커 완료 시 Mattermost로 콜백 전송

### 3) Health / Readiness

- `GET /healthz`: 프로세스 생존 확인
- `GET /readyz`: DB 연결 준비 상태 확인

### 4) Task Status API

- `GET /tasks/{task_id}`: 작업 실행 상태/요약 조회

### 5) Worker

- 실행 명령: `python -m mm_agent_bridge.worker`
- 실행기 어댑터를 통해 `mock`, `codex_cli`, `claude_cli` 백엔드 사용
- `codex_cli`/`claude_cli` 사용 시 워커가 각 CLI를 호출해 결과를 task summary로 저장

### 6) Agent Execution Layer (Planned)

- Codex/Claude 등 엔진 추상화
- 워커 프로세스가 `agent_tasks`를 polling/consuming
- 실행 결과/요약/실패 원인을 DB에 업데이트

### 7) Runtime Abstraction Boundary (Incremental)

- `task_worker`는 직접 실행기 함수를 호출하지 않고 `AgentRuntime` 인터페이스를 통해 실행
- `AgentRequest` / `AgentResult`를 공통 계약으로 사용
- 기본 구현은 `ExecutorAgentRuntime`이며 기존 `mock`/`codex_cli`/`claude_cli` 동작을 그대로 재사용
- `ConversationSessionResolver`, `ResponsePublisher` 프로토콜을 먼저 도입해 향후 Happy adapter 연결 지점을 고정
- 주의: `root_id` 및 thread reply policy 결정은 Mattermost publishing 레이어 전용 책임으로 유지

### 8) Database (Stateful Layer)

- `incoming_messages`: 원 요청 메타데이터 + 텍스트 + `response_url`
- `agent_tasks`: 실행 상태 큐
- 마이그레이션: `sql/001_init.sql`, `sql/002_add_response_url.sql`

## Data Policy

### Allowed in Repository
- code
- documentation
- configuration templates
- SQL schema/migrations

### Forbidden in Repository
- personal user data
- raw conversation logs
- API keys/secrets
- runtime memory files

## Request Flow

1. Mattermost가 webhook 요청 전송
2. Bridge 서버가 payload 검증
3. DB에 `incoming_messages` 저장
4. DB에 `agent_tasks`를 `queued` 상태로 생성
5. `202 Accepted` 응답 반환
6. (향후) 실행 워커가 큐 소비 후 결과 갱신

## Extensibility

- Agent 엔진 추가 시 `engine` 필드와 실행 어댑터만 확장
- 웹훅 입력 소스 추가 시 ingress 라우터만 분리 확장
- 상태 모델은 DB 중심 유지로 저장소 무상태 원칙 보존
