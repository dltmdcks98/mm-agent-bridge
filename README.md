# mm-agent-bridge

Mattermost 요청을 받아 Agent 작업으로 연결하는 브리지 서비스입니다.

---

## 개요 (Overview)

이 프로젝트는 아래 계층을 연결하는 브리지 역할을 합니다.
- Mattermost (입력)
- Agent 실행 계층 (Codex / Claude Code / 향후 도구)
- 데이터베이스 (상태 저장 계층)

---

## 핵심 원칙 (Key Principles)

- 저장소(Repository)는 Stateless로 유지한다
- 모든 런타임 데이터는 데이터베이스에 저장한다
- 개인 정보/대화 데이터는 파일에 저장하지 않는다
- 저장소에는 코드/설정/문서만 포함한다

---

## 아키텍처 (단순화)

Mattermost → Bridge Server → Agent Execution → Database

---

## 로컬 설정 (Local Setup)

1. 환경 변수 파일 복사

```bash
cp .env.example .env
```

2. 의존 서비스 시작

```bash
docker-compose up -d
```

3. 마이그레이션 실행

```bash
# TODO: 마이그레이션 명령 추가
```

4. 애플리케이션 실행

```bash
# TODO: 실행 명령 추가
```

---

## 프로젝트 구조 (Project Structure)

- `app/` → 애플리케이션 코드
- `docs/` → 문서
- `sql/` → 스키마 및 마이그레이션
- `infra/` → Docker/인프라 설정

---

## 범위 (Scope)

### 포함 (Included)

- Agent 브리지 로직
- Mattermost 연동
- 데이터베이스 스키마
- 실행 오케스트레이션

### 제외 (Not Included)

- 저장소 내 개인 사용자 데이터
- 파일 기반 대화 로그
- 시크릿 또는 API 키

---

## 향후 작업 (Future Work)

- Agent 실행기 통합 (Codex / Claude Code)
- Stateful 메모리 계층 (PostgreSQL + Vector)
- 작업 오케스트레이션
- 관측성(로깅/트레이싱)
