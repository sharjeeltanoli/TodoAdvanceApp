# Data Model — Todo CRUD Application

**Feature**: 001-todo-crud
**Date**: 2026-02-08

## Entity Relationship

```
┌─────────────────────┐        ┌─────────────────────────┐
│       user           │        │          task            │
│ (Better Auth managed)│        │   (FastAPI managed)      │
├─────────────────────┤        ├─────────────────────────┤
│ id          TEXT PK  │───┐    │ id          UUID PK      │
│ name        TEXT     │   │    │ user_id     TEXT FK NN   │◄──┘
│ email       TEXT UQ  │   └───►│ title       VARCHAR(255) │
│ email_verified BOOL  │        │ description TEXT(2000)   │
│ image       TEXT     │        │ completed   BOOL DEFAULT │
│ created_at  TIMESTMP │        │ created_at  TIMESTAMP    │
│ updated_at  TIMESTMP │        │ updated_at  TIMESTAMP    │
└─────────────────────┘        └─────────────────────────┘

┌─────────────────────┐        ┌─────────────────────────┐
│      session         │        │      account             │
│ (Better Auth managed)│        │ (Better Auth managed)    │
├─────────────────────┤        ├─────────────────────────┤
│ id          TEXT PK  │        │ id          TEXT PK      │
│ user_id     TEXT FK  │        │ user_id     TEXT FK      │
│ token       TEXT UQ  │        │ account_id  TEXT         │
│ expires_at  TIMESTMP │        │ provider_id TEXT         │
│ ip_address  TEXT     │        │ access_token TEXT        │
│ user_agent  TEXT     │        │ refresh_token TEXT       │
│ created_at  TIMESTMP │        │ expires_at   TIMESTMP   │
│ updated_at  TIMESTMP │        │ password     TEXT        │
└─────────────────────┘        │ created_at   TIMESTMP   │
                                │ updated_at   TIMESTMP   │
                                └─────────────────────────┘

┌─────────────────────┐        ┌─────────────────────────┐
│    verification      │        │         jwks             │
│ (Better Auth managed)│        │ (Better Auth JWT plugin) │
├─────────────────────┤        ├─────────────────────────┤
│ id          TEXT PK  │        │ id          TEXT PK      │
│ identifier  TEXT     │        │ public_key  TEXT         │
│ value       TEXT     │        │ private_key TEXT         │
│ expires_at  TIMESTMP │        │ created_at  TIMESTMP    │
│ created_at  TIMESTMP │        └─────────────────────────┘
│ updated_at  TIMESTMP │
└─────────────────────┘
```

## Table: `task` (FastAPI-managed)

| Column       | Type          | Constraints                         | Notes                                    |
| ------------ | ------------- | ----------------------------------- | ---------------------------------------- |
| `id`         | UUID          | PRIMARY KEY, DEFAULT uuid_generate  | Auto-generated UUIDv4                    |
| `user_id`    | TEXT          | NOT NULL, FOREIGN KEY → user.id, INDEX | Links to Better Auth user table          |
| `title`      | VARCHAR(255)  | NOT NULL                            | Required, max 255 characters             |
| `description`| TEXT          | NULLABLE                            | Optional, max 2000 chars (app-enforced)  |
| `completed`  | BOOLEAN       | NOT NULL, DEFAULT FALSE             | Toggle between complete/incomplete       |
| `created_at` | TIMESTAMPTZ   | NOT NULL, DEFAULT NOW()             | Set on creation, never updated           |
| `updated_at` | TIMESTAMPTZ   | NOT NULL, DEFAULT NOW()             | Updated on every modification            |

### Indexes

| Index Name              | Columns              | Type     | Purpose                            |
| ----------------------- | -------------------- | -------- | ---------------------------------- |
| `pk_task`               | `id`                 | PRIMARY  | Primary key lookup                 |
| `ix_task_user_id`       | `user_id`            | B-TREE   | User isolation filter (every query)|
| `ix_task_user_created`  | `user_id, created_at`| B-TREE   | Ordered list for task dashboard    |

### Validation Rules

| Field         | Rule                                       | Enforced At       |
| ------------- | ------------------------------------------ | ----------------- |
| `title`       | Required, non-empty, max 255 chars         | Frontend + Backend|
| `title`       | Whitespace-only treated as empty           | Frontend + Backend|
| `description` | Optional, max 2000 chars                   | Frontend + Backend|
| `completed`   | Boolean only                               | Backend           |
| `user_id`     | Must match authenticated user from JWT     | Backend           |

### State Transitions

```
[Created] ──(toggle)──► [Completed]
    ▲                        │
    └────────(toggle)────────┘

[Any State] ──(delete)──► [Removed]
```

## Tables Managed by Better Auth

Better Auth automatically creates and manages the following tables via its database adapter. These are **not** defined in FastAPI SQLModel — they are managed by Better Auth's migration CLI (`npx @better-auth/cli migrate`).

- **`user`**: User accounts (id, name, email, emailVerified, image, timestamps)
- **`session`**: Active sessions (token, userId, expiresAt, ipAddress, userAgent)
- **`account`**: Auth provider credentials (password hash for email/password auth)
- **`verification`**: Email verification tokens
- **`jwks`**: JWT signing key pairs (added by JWT plugin)

The `task.user_id` column references `user.id` to enforce referential integrity.
