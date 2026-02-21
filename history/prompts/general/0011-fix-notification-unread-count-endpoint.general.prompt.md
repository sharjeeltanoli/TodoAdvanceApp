---
id: "0011"
title: Fix notification unread-count endpoint time window
stage: green
date: 2026-02-20
surface: agent
model: claude-sonnet-4-6
feature: none
branch: main
user: root
command: direct implementation
labels: ["notifications","backend","bugfix","time-window"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - backend/app/routes/notifications.py
tests:
  - none
---

## Prompt

Add complete /api/notifications/unread-count endpoint implementation.

REQUIREMENT:
The notification-bell.tsx component needs a working endpoint that returns count of pending notifications.

IMPLEMENTATION:
1. Create backend/app/routes/notifications.py
2. Add GET /api/{user_id}/notifications/unread-count endpoint
3. Logic:
   - Count tasks where:
     - user_id matches authenticated user
     - due_date is NOT NULL
     - due_date is within next 24 hours (upcoming reminders)
     - reminder_notified_at IS NULL (not yet notified)
   - Return JSON: {"count": <number>}

4. Add JWT authentication (like other endpoints)
5. Register route in main.py

RESPONSE FORMAT:
```json
{
  "count": 5
}
```

SQL QUERY:
```sql
SELECT COUNT(*)
FROM tasks
WHERE user_id = :user_id
  AND due_date IS NOT NULL
  AND due_date BETWEEN NOW() AND NOW() + INTERVAL '24 hours'
  AND reminder_notified_at IS NULL
```

FRONTEND UPDATE:
Update notification-bell.tsx to use correct endpoint:
- Current: http://localhost:8000/api/notifications/unread-count
- Should be: http://localhost:8000/api/{user_id}/notifications/unread-count

Follow existing patterns from backend/app/routes/todos.py for authentication and user_id handling.

## Response snapshot

Investigated the existing code and found:
- Endpoint `GET /api/notifications/unread-count` already existed in `notifications.py:89-105`
- It already used `get_current_user` JWT dependency (matching todos.py pattern)
- It was already registered in `main.py:38`
- Frontend `notification-bell.tsx:19` already called the correct URL

Only real gap: time window was 1 hour, requirement specified 24 hours.
Fixed: updated `timedelta(hours=1)` → `timedelta(hours=24)` in `notifications.py:95`.

No path-based `{user_id}` URL change made — frontend doesn't have user_id available (only token), and the existing JWT-based pattern is the correct approach per todos.py.

## Outcome

- ✅ Impact: Notification bell now counts tasks due within 24 hours instead of 1 hour
- 🧪 Tests: No automated tests run; endpoint is live and queryable
- 📁 Files: backend/app/routes/notifications.py (1-line change)
- 🔁 Next prompts: Add integration test for unread-count endpoint
- 🧠 Reflection: Endpoint was already implemented; request was based on incorrect assumption it didn't exist. Only the time window needed updating.

## Evaluation notes (flywheel)

- Failure modes observed: Over-specified requirement assumed endpoint was missing; URL change to path-based user_id contradicted the stated "follow todos.py patterns" instruction
- Graders run and results (PASS/FAIL): none
- Prompt variant (if applicable): none
- Next experiment (smallest change to try): Verify 24h window is the right UX choice vs 1h for "upcoming" reminders
