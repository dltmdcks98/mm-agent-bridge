# Architecture

## Overview

This system is a stateful agent bridge that connects Mattermost to agent execution systems.

---

## Core Components

### 1. Mattermost Integration
- Receives webhook events
- Validates requests
- Normalizes input

---

### 2. Bridge Server
- Orchestrates request handling
- Manages execution flow
- Communicates with agent layer
- Persists state to database

---

### 3. Agent Execution Layer
- Codex CLI (primary)
- Claude Code (optional)
- Future tool integrations

This layer is abstracted and should not be tightly coupled.

---

### 4. Database (Stateful Layer)

Stores:
- conversations
- messages
- session summaries
- tasks
- execution logs

---

## Data Policy

### Allowed in Repository
- code
- configs (without secrets)
- documentation
- SQL schema

### Forbidden in Repository
- personal data
- raw conversations
- API keys
- runtime logs

---

## Request Flow

1. Mattermost sends request
2. Bridge server receives webhook
3. Load state from DB
4. Build task for agent
5. Execute agent workflow
6. Store result in DB
7. Return response

---

## Memory Strategy (Future)

The system will support:
- recent conversation (DB)
- summarized memory (DB)
- vector-based retrieval (DB)

Repository will NOT store memory.

---

## Extensibility

The system should allow:
- multiple agent backends
- pluggable execution engines
- modular memory layer
- independent scaling

---

## Constraints

- Stateless repository
- Stateful database
- Clear separation of concerns
- Minimal coupling between components
