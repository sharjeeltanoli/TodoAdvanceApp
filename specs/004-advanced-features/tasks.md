# Tasks: Enhanced Task Management

**Input**: Design documents from `/specs/004-advanced-features/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/api.yaml

**Tests**: Not explicitly requested — test tasks omitted. Manual verification via acceptance criteria.

**Organization**: Tasks grouped by user story to enable independent implementation. Foundational tasks (migration, models) come first since all stories depend on them.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2)
- Include exact file paths in descriptions

---

## Phase 1: Setup

**Purpose**: Install new dependencies required for this feature

- [x] T001 Install `date-fns` in frontend for date formatting — `frontend/package.json`
- [x] T002 Install `apscheduler` in backend for recurring task scheduler — `backend/pyproject.toml`

---

## Phase 2: Foundational (Database & Models)

**Purpose**: Alembic migration and SQLModel updates that ALL user stories depend on

**CRITICAL**: No user story work can begin until this phase is complete

- [x] T003 Create Alembic migration adding `priority`, `tags`, `due_date`, `recurrence_pattern`, `reminder_minutes`, `snoozed_until`, `reminder_notified_at`, `parent_task_id` columns to `task` table with defaults and indexes — `backend/alembic/versions/004_add_advanced_fields.py`
  - **Acceptance**: Migration runs without error on existing data. Existing tasks get `priority='medium'`, `tags='[]'`. New indexes created: `ix_task_user_priority`, `ix_task_user_due`, `ix_task_tags_gin`. All 8 new columns present. Downgrade drops all new columns and indexes.

- [x] T004 Add `Priority` Python enum and `RecurrencePattern` Pydantic model to models — `backend/app/models.py`
  - **Acceptance**: `Priority` enum has values `high`, `medium`, `low`. `RecurrencePattern` has `frequency` (daily/weekly/monthly), `interval` (int), `next_due` (datetime).

- [x] T005 Extend `Task` SQLModel with new fields (`priority`, `tags`, `due_date`, `recurrence_pattern`, `reminder_minutes`, `snoozed_until`, `reminder_notified_at`, `parent_task_id`) — `backend/app/models.py`
  - **Acceptance**: `Task` table model includes all 8 new fields with correct types and defaults. `priority` defaults to `"medium"`, `tags` defaults to `[]`. `snoozed_until` and `reminder_notified_at` are nullable TIMESTAMPTZ.

- [x] T006 Update `TaskCreate`, `TaskUpdate`, `TaskResponse` schemas with new fields — `backend/app/models.py`
  - **Acceptance**: `TaskCreate` accepts optional `priority`, `tags`, `due_date`, `recurrence_pattern`, `reminder_minutes`. `TaskUpdate` accepts same as optional. `TaskResponse` includes all new fields including `snoozed_until`, `reminder_notified_at`, `parent_task_id`. Tags validated to max 10 items, each lowercase.

- [x] T007 Run migration against database and verify backward compatibility — `backend/alembic/`
  - **Acceptance**: `alembic upgrade head` succeeds. Existing tasks queryable with new fields at defaults. No data loss.

**Checkpoint**: Database schema updated, models ready. User story implementation can begin.

---

## Phase 3: User Story 1 — Set Task Priority (Priority: P1)

**Goal**: Users can assign High/Medium/Low priority to tasks with visual indicators

**Independent Test**: Create a task with priority, verify it displays with color-coded badge, confirm it persists on reload

### Implementation

- [x] T008 [US1] Extend `POST /todos` and `PUT /todos/{id}` to accept and persist `priority` field — `backend/app/routes/todos.py`
  - **Acceptance**: Creating a task with `{"title": "Test", "priority": "high"}` returns the task with `priority: "high"`. Omitting priority defaults to `"medium"`. Invalid priority values return 422.

- [x] T009 [P] [US1] Create `PriorityBadge` component displaying color-coded priority indicator (red=high, yellow=medium, green=low) — `frontend/src/components/ui/priority-badge.tsx`
  - **Acceptance**: Renders a small colored badge with priority text. Accepts `priority` prop of type `"high" | "medium" | "low"`.

- [x] T010 [US1] Add priority selector (3-button toggle or dropdown) to `TaskForm` for create and edit modes — `frontend/src/components/tasks/task-form.tsx`
  - **Acceptance**: Priority selector visible on task form. Defaults to "medium" on create. Shows current priority on edit. Selected priority submitted with form data.

- [x] T011 [US1] Display `PriorityBadge` on each task in `TaskItem` — `frontend/src/components/tasks/task-item.tsx`
  - **Acceptance**: Each task card shows its priority badge. Badge updates when task is edited.

- [x] T012 [US1] Update `createTask` and `updateTask` server actions to pass `priority` — `frontend/src/app/dashboard/actions.ts`
  - **Acceptance**: `createTask` sends `priority` in POST body. `updateTask` sends `priority` in PUT body. Default priority sent if not specified.

**Checkpoint**: Priority feature fully functional end-to-end

---

## Phase 4: User Story 2 — Tag and Categorize Tasks (Priority: P1)

**Goal**: Users can add/remove tags on tasks, with autocomplete from existing tags

**Independent Test**: Add tags to a task, verify chips display, verify autocomplete suggests existing tags

### Implementation

- [x] T013 [US2] Extend `POST /todos` and `PUT /todos/{id}` to accept and persist `tags` array with validation (max 10, lowercase normalization) — `backend/app/routes/todos.py`
  - **Acceptance**: Creating a task with `{"title": "Test", "tags": ["Work", "Personal"]}` stores `["work", "personal"]`. More than 10 tags returns 422.

- [x] T014 [US2] Add `GET /todos/tags` endpoint returning distinct tags for current user — `backend/app/routes/todos.py`
  - **Acceptance**: Returns `["personal", "shopping", "work"]` (sorted, deduplicated) from all user's tasks. Empty array if no tags exist.

- [x] T015 [P] [US2] Create `TagInput` component with chip display, add/remove, and autocomplete dropdown — `frontend/src/components/ui/tag-input.tsx`
  - **Acceptance**: Typing a tag and pressing Enter/comma adds a chip. Clicking X on chip removes it. Typing shows dropdown of matching existing tags. Mixed-case input normalized to lowercase on display.

- [x] T016 [US2] Integrate `TagInput` into `TaskForm` for create and edit — `frontend/src/components/tasks/task-form.tsx`
  - **Acceptance**: Tag input visible on task form. Existing tags populated on edit. Tags submitted with form data.

- [x] T017 [US2] Display tag chips on `TaskItem` — `frontend/src/components/tasks/task-item.tsx`
  - **Acceptance**: Each task card shows its tags as small chips/badges below the title. Tasks with no tags show nothing.

- [x] T018 [US2] Update `createTask` and `updateTask` server actions to pass `tags` array — `frontend/src/app/dashboard/actions.ts`
  - **Acceptance**: Tags array sent in request body. Fetches `/todos/tags` for autocomplete data.

**Checkpoint**: Tags feature fully functional end-to-end

---

## Phase 5: User Story 3 — Set Due Dates (Priority: P1)

**Goal**: Users can set due dates on tasks with date picker, overdue/today visual indicators

**Independent Test**: Set a due date on a task, verify date picker works, verify overdue styling on past-due tasks

### Implementation

- [x] T019 [US3] Extend `POST /todos` and `PUT /todos/{id}` to accept and persist `due_date` field — `backend/app/routes/todos.py`
  - **Acceptance**: Creating a task with `{"title": "Test", "due_date": "2026-02-20T00:00:00Z"}` stores the date. Null clears it. Invalid date format returns 422.

- [x] T020 [P] [US3] Create `DatePicker` component wrapping native `<input type="date">` with clear button — `frontend/src/components/ui/date-picker.tsx`
  - **Acceptance**: Renders a date input. Clear button sets value to null. Accepts `value` and `onChange` props.

- [x] T021 [US3] Integrate `DatePicker` into `TaskForm` for create and edit — `frontend/src/components/tasks/task-form.tsx`
  - **Acceptance**: Date picker visible on task form. Shows current due date on edit. Clearing removes due date.

- [x] T022 [US3] Display due date on `TaskItem` with overdue (red) and due-today (amber) indicators using `date-fns` — `frontend/src/components/tasks/task-item.tsx`
  - **Acceptance**: Shows relative date text (e.g., "Due tomorrow", "Overdue by 2 days"). Overdue tasks have red text/icon. Due-today tasks have amber indicator. No-date tasks show nothing. Completed tasks never show overdue.

- [x] T023 [US3] Update `createTask` and `updateTask` server actions to pass `due_date` — `frontend/src/app/dashboard/actions.ts`
  - **Acceptance**: `due_date` sent as ISO 8601 string or null.

**Checkpoint**: Due dates feature fully functional end-to-end

---

## Phase 6: User Story 4 — Search Tasks (Priority: P1)

**Goal**: Users can search tasks by keyword across title and description

**Independent Test**: Create several tasks, type keyword in search bar, verify only matching tasks shown

### Implementation

- [x] T024 [US4] Add `search` query parameter to `GET /todos` with case-insensitive ILIKE on title and description — `backend/app/routes/todos.py`
  - **Acceptance**: `GET /todos?search=grocery` returns only tasks with "grocery" in title or description (case-insensitive). Empty search returns all tasks. Special characters are escaped.

- [x] T025 [P] [US4] Create `SearchInput` component with debounced input (300ms) and search icon — `frontend/src/components/ui/search-input.tsx`
  - **Acceptance**: Renders a text input with search icon. Fires `onChange` after 300ms debounce. Clear button resets search.

- [x] T026 [US4] Integrate `SearchInput` into `TaskList` above the task list — `frontend/src/components/tasks/task-list.tsx`
  - **Acceptance**: Search bar visible at top of task list. Typing filters tasks in real-time (after debounce). Clearing search shows all tasks.

- [x] T027 [US4] Update `getTasks` server action to accept and pass `search` query parameter — `frontend/src/app/dashboard/actions.ts`
  - **Acceptance**: `getTasks({search: "keyword"})` calls `GET /todos?search=keyword`. No search param fetches all.

**Checkpoint**: Search feature fully functional end-to-end

---

## Phase 7: User Story 5 — Filter Tasks (Priority: P2)

**Goal**: Users can filter tasks by status, priority, and tag with AND logic

**Independent Test**: Apply filters and verify task list updates to show only matching tasks

**Depends on**: US1 (priorities), US2 (tags) — for meaningful filter options

### Implementation

- [x] T028 [US5] Add `status`, `priority`, and `tag` query parameters to `GET /todos` with AND-combined filtering — `backend/app/routes/todos.py`
  - **Acceptance**: `GET /todos?status=pending&priority=high&tag=work` returns only pending, high-priority tasks tagged "work". Each filter is optional. Combined with search if both present.

- [x] T029 [P] [US5] Create `FilterBar` component with dropdowns for status (pending/completed/all), priority (high/medium/low/all), and tag (from user's tags/all), plus "Clear filters" button — `frontend/src/components/ui/filter-bar.tsx`
  - **Acceptance**: Three dropdown/select controls. Selecting a filter triggers re-fetch. "Clear filters" resets all. Active filter count shown.

- [x] T030 [US5] Integrate `FilterBar` into `TaskList` between search and task list — `frontend/src/components/tasks/task-list.tsx`
  - **Acceptance**: Filter bar visible. Changing any filter updates the task list. Filters work with search (AND logic).

- [x] T031 [US5] Update `getTasks` server action to accept and pass filter query parameters — `frontend/src/app/dashboard/actions.ts`
  - **Acceptance**: `getTasks({status: "pending", priority: "high", tag: "work"})` passes all params to API.

**Checkpoint**: Filtering fully functional end-to-end

---

## Phase 8: User Story 6 — Sort Tasks (Priority: P2)

**Goal**: Users can sort tasks by due date, priority, or creation date

**Independent Test**: Select sort option and verify task order changes

### Implementation

- [x] T032 [US6] Add `sort_by` and `sort_dir` query parameters to `GET /todos` with support for `created_at`, `due_date`, `priority` sorting — `backend/app/routes/todos.py`
  - **Acceptance**: `GET /todos?sort_by=due_date&sort_dir=asc` returns tasks ordered by due date ascending. Tasks without due dates appear at end when sorting by due_date. Priority sorting: high > medium > low. Default: `created_at desc`.

- [x] T033 [P] [US6] Create `SortSelect` component with dropdown for sort field and toggle for direction — `frontend/src/components/ui/sort-select.tsx`
  - **Acceptance**: Dropdown with options: "Created (newest)", "Due Date (soonest)", "Priority (highest)". Selecting changes sort. Optional asc/desc toggle.

- [x] T034 [US6] Integrate `SortSelect` into `TaskList` alongside filter bar — `frontend/src/components/tasks/task-list.tsx`
  - **Acceptance**: Sort control visible. Changing sort re-fetches and re-orders task list. Works alongside search and filters.

- [x] T035 [US6] Update `getTasks` server action to accept and pass `sort_by`, `sort_dir` — `frontend/src/app/dashboard/actions.ts`
  - **Acceptance**: Sort params passed to API. Default sort is `created_at desc`.

**Checkpoint**: Sorting fully functional end-to-end

---

## Phase 9: User Story 7 — Task Descriptions (Priority: P2)

**Goal**: Better UI support for multi-line descriptions with expand/collapse

**Independent Test**: Add a long description, verify truncated preview in list, verify "show more" expands

### Implementation

- [x] T036 [US7] Update `TaskForm` description field to expandable `<textarea>` with auto-resize — `frontend/src/components/tasks/task-form.tsx`
  - **Acceptance**: Description field is a textarea (not single-line input). Auto-grows as user types. Supports multi-line input.

- [x] T037 [US7] Update `TaskItem` to show truncated description preview with "show more/less" toggle — `frontend/src/components/tasks/task-item.tsx`
  - **Acceptance**: Descriptions longer than 100 characters show truncated with "show more" link. Clicking expands to full text. "Show less" collapses back. Preserves line breaks.

**Checkpoint**: Enhanced descriptions functional

---

## Phase 10: User Story 8 — Recurring Tasks (Priority: P3)

**Goal**: Users can create recurring tasks that auto-generate new instances on schedule

**Independent Test**: Create a recurring daily task, trigger scheduler, verify new instance created

**Depends on**: US1 (priority), US2 (tags), US3 (due dates) — for copying fields to generated instances

### Implementation

- [x] T038 [US8] Extend `POST /todos` and `PUT /todos/{id}` to accept `recurrence_pattern` JSON and `parent_task_id` — `backend/app/routes/todos.py`
  - **Acceptance**: Creating task with `{"title": "Standup", "recurrence_pattern": {"frequency": "daily", "interval": 1, "next_due": "..."}}` stores the pattern. Setting `recurrence_pattern` to null disables recurrence.

- [x] T039 [US8] Create recurring task scheduler that runs every 5 minutes and generates new task instances — `backend/app/scheduler.py`
  - **Acceptance**: Scheduler queries tasks with `recurrence_pattern.next_due <= NOW()`. Creates child task (copies title, description, priority, tags, sets `parent_task_id`). Advances `next_due` based on frequency. Does not backfill missed intervals.

- [x] T040 [US8] Integrate scheduler startup into FastAPI lifespan — `backend/app/main.py`
  - **Acceptance**: Scheduler starts when backend starts. Runs every 5 minutes. Stops cleanly on shutdown.

- [x] T041 [P] [US8] Add recurrence toggle UI to `TaskForm` — frequency selector (daily/weekly/monthly) shown when recurrence enabled — `frontend/src/components/tasks/task-form.tsx`
  - **Acceptance**: Toggle to enable/disable recurrence. When enabled, shows frequency dropdown. Submits `recurrence_pattern` JSON with form data.

- [x] T042 [US8] Display recurrence indicator on `TaskItem` (e.g., "Repeats daily" icon/text) — `frontend/src/components/tasks/task-item.tsx`
  - **Acceptance**: Recurring tasks show a repeat icon with frequency text. Non-recurring tasks show nothing.

- [x] T043 [US8] Update `createTask`/`updateTask` server actions to pass `recurrence_pattern` — `frontend/src/app/dashboard/actions.ts`
  - **Acceptance**: Recurrence pattern sent as JSON object or null.

**Checkpoint**: Recurring tasks functional end-to-end

---

## Phase 11: User Story 9 — Reminders (Priority: P3)

**Goal**: Browser notifications before task due date with snooze capability

**Independent Test**: Set reminder on a task, wait for trigger time, verify browser notification appears

**Depends on**: US3 (due dates) — reminders require a due date

### Implementation

- [x] T044 [US9] Add `GET /todos/reminders` endpoint returning tasks with due reminders (where `due_date - reminder_minutes <= NOW()`, not completed, and `reminder_notified_at IS NULL` or `snoozed_until <= NOW()`) — `backend/app/routes/todos.py`
  - **Acceptance**: Returns only tasks with active reminders whose trigger time has passed. Completed tasks excluded. Tasks with `reminder_notified_at` set (already notified) excluded unless `snoozed_until` has passed. Empty array if none.

- [x] T045 [US9] Add `POST /todos/{id}/snooze` endpoint that sets `snoozed_until = NOW() + 15 min` and clears `reminder_notified_at` — `backend/app/routes/todos.py`
  - **Acceptance**: Calling snooze sets `snoozed_until` to 15 minutes from now and clears `reminder_notified_at` (so the reminder re-fires after snooze). Returns 400 if task has no reminder. Returns updated task.

- [x] T046 [P] [US9] Create `notifications.ts` utility with `requestPermission()`, `showNotification()`, and `checkReminders()` polling function — `frontend/src/lib/notifications.ts`
  - **Acceptance**: `requestPermission()` prompts user for notification permission. `showNotification()` creates a browser notification with title/body. `checkReminders()` fetches `/todos/reminders` and shows notification for each.

- [x] T047 [US9] Add reminder selector to `TaskForm` (only visible when due date is set) — dropdown with "15 min before", "1 hour before", "1 day before" — `frontend/src/components/tasks/task-form.tsx`
  - **Acceptance**: Reminder dropdown hidden when no due date. Shows 3 options when due date set. Selected value sent as `reminder_minutes` (15/60/1440).

- [x] T048 [US9] Start reminder polling on dashboard mount — check every 60 seconds, show browser notifications, PATCH `reminder_notified_at`, handle snooze — `frontend/src/app/dashboard/layout.tsx`
  - **Acceptance**: Polling starts when dashboard loads. Notifications shown for due reminders. After showing notification, PATCH task to set `reminder_notified_at = NOW()` to prevent duplicates. "Snooze" in notification calls snooze endpoint. Polling stops when navigating away. Permission requested on first reminder enable.

- [x] T049 [US9] Update `createTask`/`updateTask` server actions to pass `reminder_minutes` — `frontend/src/app/dashboard/actions.ts`
  - **Acceptance**: `reminder_minutes` sent as integer or null.

**Checkpoint**: Reminders functional end-to-end

---

## Phase 12: MCP Tools Update

**Purpose**: Extend MCP tools to support new task fields for AI agent consumption

- [x] T050 [P] Update inline `Task` model in MCP server with new columns (priority, tags, due_date, recurrence_pattern, reminder_minutes, parent_task_id) — `backend/mcp_server/server.py`
  - **Acceptance**: MCP `Task` model mirrors `backend/app/models.py` Task model with all new fields.

- [x] T051 Update `_task_dict()` serialization to include new fields — `backend/mcp_server/server.py`
  - **Acceptance**: `_task_dict()` returns priority, tags, due_date, recurrence_pattern, reminder_minutes, parent_task_id.

- [x] T052 Extend `add_task` MCP tool with `priority`, `tags`, `due_date` parameters — `backend/mcp_server/server.py`
  - **Acceptance**: `add_task(title="Test", auth_token="...", priority="high", tags=["work"], due_date="2026-02-20T00:00:00Z")` creates task with all fields. Missing optional fields use defaults.

- [x] T053 Extend `list_tasks` MCP tool with `search`, `priority`, `tag` filter parameters — `backend/mcp_server/server.py`
  - **Acceptance**: `list_tasks(auth_token="...", priority="high", tag="work", search="meeting")` returns filtered results.

- [x] T054 Extend `update_task` MCP tool with `priority`, `tags`, `due_date` parameters — `backend/mcp_server/server.py`
  - **Acceptance**: `update_task(task_id="...", auth_token="...", priority="low", tags=["personal"])` updates fields. Omitted fields unchanged.

**Checkpoint**: MCP tools support all new task fields

---

## Phase 13: Polish & Cross-Cutting Concerns

**Purpose**: Final integration, UX polish, and backward compatibility verification

- [x] T055 Verify backward compatibility — existing tasks without new fields display correctly with defaults — full-stack test
  - **Acceptance**: Tasks created before migration show `priority=medium`, empty tags, no due date. All existing CRUD operations still work.

- [x] T056 Verify search + filter + sort work together — combined query parameters produce correct results — `backend/app/routes/todos.py`
  - **Acceptance**: `GET /todos?search=test&status=pending&priority=high&sort_by=due_date&sort_dir=asc` returns correct, sorted, filtered results.

- [x] T057 Run quickstart.md validation — follow setup steps on clean checkout and verify all features work — `specs/004-advanced-features/quickstart.md`
  - **Acceptance**: Following quickstart steps, all 9 user stories are functional.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies — start immediately
- **Phase 2 (Foundational)**: Depends on Phase 1 — BLOCKS all user stories
- **Phases 3-6 (P1 Stories)**: Depend on Phase 2. Can run in parallel:
  - US1 (Priority): Independent
  - US2 (Tags): Independent
  - US3 (Due Dates): Independent
  - US4 (Search): Independent
- **Phases 7-9 (P2 Stories)**: Depend on Phase 2. Can mostly run in parallel:
  - US5 (Filter): Benefits from US1+US2 being done (for meaningful filter options)
  - US6 (Sort): Independent after Phase 2
  - US7 (Descriptions): Independent after Phase 2
- **Phases 10-11 (P3 Stories)**:
  - US8 (Recurring): Benefits from US1+US2+US3 (copies fields to instances)
  - US9 (Reminders): Depends on US3 (due dates required)
- **Phase 12 (MCP)**: Can run after Phase 2, parallel with UI work
- **Phase 13 (Polish)**: After all user stories complete

### User Story Dependencies

```text
Phase 2 (Foundation)
  ├── US1 (Priority)  ──┐
  ├── US2 (Tags)     ──┤── US5 (Filter) needs meaningful filter data
  ├── US3 (Due Dates) ──┤── US9 (Reminders) requires due dates
  │                      └── US8 (Recurring) copies priority/tags/due
  ├── US4 (Search)
  ├── US6 (Sort)
  ├── US7 (Descriptions)
  └── MCP (Phase 12)
```

### Parallel Opportunities

- **Within Phase 2**: T003 (migration) must be first, then T004-T006 can run in parallel
- **P1 Stories (Phases 3-6)**: All 4 stories can run in parallel after Phase 2
- **UI Components**: PriorityBadge (T009), TagInput (T015), DatePicker (T020), SearchInput (T025) can all be built in parallel
- **MCP Update (Phase 12)**: Can run in parallel with all frontend phases

---

## Implementation Strategy

### MVP First (P1 Stories Only)

1. Complete Phase 1: Setup (T001-T002)
2. Complete Phase 2: Foundation (T003-T007)
3. Complete Phase 3: Priority (T008-T012)
4. **STOP and VALIDATE**: Priority feature works end-to-end
5. Continue with Phases 4-6: Tags, Due Dates, Search

### Incremental Delivery

1. Setup + Foundation → Schema ready
2. Add Priority (US1) → First visible improvement
3. Add Tags (US2) → Categorization working
4. Add Due Dates (US3) → Time management working
5. Add Search (US4) → Finding tasks easy
6. Add Filter + Sort (US5+US6) → Full organization toolkit
7. Add Descriptions (US7) → Better detail capture
8. Add Recurring (US8) → Automation working
9. Add Reminders (US9) → Proactive notifications
10. MCP + Polish → Complete feature

---

## Summary

| Metric | Value |
| ------ | ----- |
| Total tasks | 57 |
| Setup tasks | 2 |
| Foundational tasks | 5 |
| P1 story tasks | 20 (US1: 5, US2: 6, US3: 5, US4: 4) |
| P2 story tasks | 10 (US5: 4, US6: 4, US7: 2) |
| P3 story tasks | 12 (US8: 6, US9: 6) |
| MCP tasks | 5 |
| Polish tasks | 3 |
| Parallel opportunities | 12 tasks marked [P] |
| Suggested MVP scope | Phase 2 + US1 (Priority) = 10 tasks |

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks
- Backend route tasks (T008, T013, T019, T024, T028, T032) modify the same file (`todos.py`) — execute sequentially within their phases, but the file is extended incrementally
- Frontend `TaskForm` and `TaskItem` are modified by multiple stories — each story adds to them incrementally
- `actions.ts` is extended by each story — additions are additive and non-conflicting
- Commit after each task or logical group
- Stop at any checkpoint to validate the story independently
