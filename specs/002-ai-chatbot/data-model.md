# Data Model: AI-Powered Todo Chatbot

**Feature**: 002-ai-chatbot
**Date**: 2026-02-10

## Entity Relationship Diagram

```
┌──────────────┐        ┌────────────────────┐        ┌──────────────────┐
│    user       │       │   conversation      │       │     message       │
│ (Better Auth) │       │                     │       │                   │
├──────────────┤       ├────────────────────┤       ├──────────────────┤
│ id       PK  │◄──┐   │ id            PK   │◄──┐   │ id           PK  │
│ email        │   │   │ user_id       FK   │───┘   │ conversation_id FK│
│ ...          │   │   │ title              │       │ role             │
└──────────────┘   │   │ created_at         │       │ content          │
                   │   │ updated_at         │       │ created_at       │
                   │   └────────────────────┘       └──────────────────┘
                   │
                   │   ┌──────────────────┐
                   │   │      task         │
                   │   │   (Phase 2)       │
                   │   ├──────────────────┤
                   └───│ user_id      FK  │
                       │ id           PK  │
                       │ title            │
                       │ description      │
                       │ completed        │
                       │ created_at       │
                       │ updated_at       │
                       └──────────────────┘
```

## New Tables

### conversation

Stores chat threads. Maps to ChatKit `ThreadMetadata`.

| Column     | Type                     | Constraints                    | Notes                          |
|------------|--------------------------|--------------------------------|--------------------------------|
| id         | UUID                     | PK, DEFAULT uuid_generate_v4() | ChatKit thread ID              |
| user_id    | TEXT                     | FK → user.id, NOT NULL, INDEX  | Owner, enforces isolation      |
| title      | VARCHAR(255)             | NULL                           | Auto-generated or user-set     |
| created_at | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT now()        |                                |
| updated_at | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT now()        | Last activity in conversation  |

**Indexes**:
- `ix_conversation_user_id` on `(user_id)`
- `ix_conversation_user_updated` on `(user_id, updated_at DESC)` — for listing conversations by recency

### message

Stores individual messages within conversations. Maps to ChatKit `ThreadItem`.

| Column          | Type                     | Constraints                         | Notes                        |
|-----------------|--------------------------|-------------------------------------|------------------------------|
| id              | UUID                     | PK, DEFAULT uuid_generate_v4()      | ChatKit item ID              |
| conversation_id | UUID                     | FK → conversation.id, NOT NULL      | Parent thread                |
| role            | VARCHAR(20)              | NOT NULL, CHECK IN ('user','assistant') | Message author           |
| content         | TEXT                     | NOT NULL                            | Message text                 |
| created_at      | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT now()             | Ordering key                 |

**Indexes**:
- `ix_message_conversation_id` on `(conversation_id)`
- `ix_message_conversation_created` on `(conversation_id, created_at ASC)` — for loading thread history in order

**Foreign key cascades**:
- `conversation.user_id` → `user.id` ON DELETE CASCADE
- `message.conversation_id` → `conversation.id` ON DELETE CASCADE

## Existing Tables (Unchanged)

### task (Phase 2)

No schema changes. The chatbot reads and modifies tasks exclusively through MCP tools, which use the existing SQLModel `Task` model and async session.

### user (Better Auth managed)

No schema changes. Better Auth continues to manage the `user`, `session`, `account`, `verification`, and `jwks` tables.

## Validation Rules

### conversation
- `title`: Optional, max 255 characters. Auto-generated from first user message if not set.
- `user_id`: Required. Must match an existing Better Auth user.

### message
- `role`: Required. Must be one of `user` or `assistant`.
- `content`: Required. Cannot be empty or whitespace-only.
- `conversation_id`: Required. Must reference an existing conversation owned by the authenticated user.

## State Transitions

### Conversation Lifecycle
```
[New] ──create──► [Active] ──delete──► [Deleted]
                    │  ▲
                    │  │
                 message (updates updated_at)
```

- Conversations are created implicitly on first message (if no active thread exists) or explicitly via "New conversation" action.
- Each new message updates the conversation's `updated_at` timestamp.
- Deleting a conversation cascades to delete all its messages.

## Migration Plan

- Alembic migration `002_create_conversation_and_message_tables.py`
- Creates `conversation` table with indexes and FK to `user.id`
- Creates `message` table with indexes and FK to `conversation.id`
- Non-destructive: does not modify existing `task` or Better Auth tables
