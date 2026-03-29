BEGIN;

CREATE TABLE IF NOT EXISTS incoming_messages (
  id BIGSERIAL PRIMARY KEY,
  request_id VARCHAR(64) NOT NULL UNIQUE,
  source VARCHAR(32) NOT NULL DEFAULT 'mattermost',
  user_id VARCHAR(128) NOT NULL,
  channel_id VARCHAR(128) NOT NULL,
  text TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_incoming_messages_user_id ON incoming_messages(user_id);
CREATE INDEX IF NOT EXISTS idx_incoming_messages_channel_id ON incoming_messages(channel_id);

CREATE TABLE IF NOT EXISTS agent_tasks (
  id BIGSERIAL PRIMARY KEY,
  message_id BIGINT NOT NULL REFERENCES incoming_messages(id) ON DELETE CASCADE,
  status VARCHAR(32) NOT NULL DEFAULT 'queued',
  engine VARCHAR(64) NOT NULL DEFAULT 'codex',
  summary TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_agent_tasks_message_id ON agent_tasks(message_id);
CREATE INDEX IF NOT EXISTS idx_agent_tasks_status ON agent_tasks(status);

COMMIT;
