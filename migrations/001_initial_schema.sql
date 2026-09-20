-- EGEN Master Deck — D1 initial schema
-- DESIGN ONLY: do not apply to production until Phase 2 migration approval.

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  office TEXT NOT NULL CHECK (office IN ('JB','KL')),
  role TEXT NOT NULL CHECK (role IN ('Manager','Senior','Team')),
  active INTEGER NOT NULL DEFAULT 1 CHECK (active IN (0,1)),
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS user_statuses (
  user_id TEXT PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
  status TEXT NOT NULL CHECK (status IN ('free','busy','capacity')),
  version INTEGER NOT NULL DEFAULT 1,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS projects (
  id TEXT PRIMARY KEY,
  owner_id TEXT NOT NULL REFERENCES users(id),
  title TEXT NOT NULL,
  due_date TEXT,
  created_at TEXT,
  version INTEGER NOT NULL DEFAULT 1,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_projects_owner ON projects(owner_id);
CREATE INDEX IF NOT EXISTS idx_projects_due_date ON projects(due_date);

CREATE TABLE IF NOT EXISTS tasks (
  id TEXT PRIMARY KEY,
  project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  text TEXT NOT NULL,
  done INTEGER NOT NULL DEFAULT 0 CHECK (done IN (0,1)),
  waiting INTEGER NOT NULL DEFAULT 0 CHECK (waiting IN (0,1)),
  due_date TEXT,
  sort_order INTEGER NOT NULL DEFAULT 0,
  version INTEGER NOT NULL DEFAULT 1,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_tasks_project ON tasks(project_id);
CREATE INDEX IF NOT EXISTS idx_tasks_due_date ON tasks(due_date);
CREATE INDEX IF NOT EXISTS idx_tasks_waiting_done ON tasks(waiting, done);

CREATE TABLE IF NOT EXISTS briefs (
  id TEXT PRIMARY KEY,
  title TEXT NOT NULL,
  raw_brief TEXT,
  points_json TEXT NOT NULL DEFAULT '[]',
  client_asks_json TEXT NOT NULL DEFAULT '[]',
  concepts_json TEXT NOT NULL DEFAULT '[]',
  effort_level TEXT,
  effort_reason TEXT,
  assignee_id TEXT REFERENCES users(id),
  due_date TEXT,
  status TEXT NOT NULL,
  created_at TEXT,
  approved_at TEXT,
  source TEXT,
  version INTEGER NOT NULL DEFAULT 1,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_briefs_assignee ON briefs(assignee_id);
CREATE INDEX IF NOT EXISTS idx_briefs_status ON briefs(status);
CREATE INDEX IF NOT EXISTS idx_briefs_due_date ON briefs(due_date);
CREATE INDEX IF NOT EXISTS idx_briefs_source ON briefs(source);

CREATE TABLE IF NOT EXISTS schedules (
  id TEXT PRIMARY KEY,
  owner_id TEXT NOT NULL REFERENCES users(id),
  title TEXT NOT NULL,
  date TEXT NOT NULL,
  end_date TEXT,
  time TEXT,
  note TEXT,
  version INTEGER NOT NULL DEFAULT 1,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_schedules_owner ON schedules(owner_id);
CREATE INDEX IF NOT EXISTS idx_schedules_date ON schedules(date);

CREATE TABLE IF NOT EXISTS audit_logs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  actor_user_id TEXT,
  entity_type TEXT NOT NULL,
  entity_id TEXT NOT NULL,
  action TEXT NOT NULL,
  before_json TEXT,
  after_json TEXT,
  request_id TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_audit_entity ON audit_logs(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_audit_created_at ON audit_logs(created_at);

CREATE TABLE IF NOT EXISTS app_meta (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
