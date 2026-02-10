# Tasks: Full-Stack Todo CRUD Application

**Input**: Design documents from `/specs/001-todo-crud/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/api.yaml

**Tests**: Not explicitly requested in the feature specification. Test tasks are omitted. Tests may be added later via `/sp.tasks --tdd`.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Backend**: `backend/app/` for source, `backend/tests/` for tests
- **Frontend**: `frontend/src/` for source, `frontend/tests/` for tests
- Based on monorepo structure defined in plan.md Section 1

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create monorepo directory structure, initialize both projects with dependencies, configure environment files

- [x] T001 Create monorepo directory structure with `frontend/` and `backend/` top-level directories per plan.md Section 1
- [x] T002 [P] Initialize backend Python project with `backend/pyproject.toml` including FastAPI, SQLModel, asyncpg, httpx, alembic, pydantic-settings, uvicorn dependencies
- [x] T003 [P] Initialize frontend Next.js 16 project with `frontend/package.json` including next, react, react-dom, better-auth, tailwindcss, @neondatabase/serverless dependencies
- [x] T004 [P] Create `backend/.env.example` with DATABASE_URL, BETTER_AUTH_URL, CORS_ORIGINS, DEBUG placeholders per plan.md Section 10
- [x] T005 [P] Create `frontend/.env.example` with BETTER_AUTH_SECRET, BETTER_AUTH_URL, DATABASE_URL, NEXT_PUBLIC_API_URL, BACKEND_URL placeholders per plan.md Section 10
- [x] T006 [P] Configure `frontend/tailwind.config.ts` and `frontend/postcss.config.mjs` for Tailwind CSS 4
- [x] T007 [P] Configure `frontend/tsconfig.json` with path alias `@/` mapping to `src/` and strict mode
- [x] T008 [P] Configure `frontend/next.config.ts` with server-side environment variable passthrough for BACKEND_URL
- [x] T009 Update root `.gitignore` to exclude `backend/.env`, `frontend/.env.local`, `backend/.venv/`, `node_modules/`, `__pycache__/`, `.next/`

**Checkpoint**: Both projects initialize without errors. `pip install -e ".[dev]"` succeeds in backend. `npm install` succeeds in frontend.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Database connection, SQLModel models, Alembic migrations, FastAPI app skeleton, Better Auth configuration, auth middleware — everything needed before any user story

**CRITICAL**: No user story work can begin until this phase is complete

### Backend Foundation

- [x] T010 Create `backend/app/__init__.py` as empty package init
- [x] T011 Create `backend/app/config.py` with Pydantic Settings class loading DATABASE_URL, BETTER_AUTH_URL, CORS_ORIGINS, DEBUG from `.env` per plan.md Section 6
- [x] T012 Create `backend/app/database.py` with async SQLAlchemy engine using `asyncpg`, async session factory, `create_db_and_tables()` function, and `get_session()` dependency per plan.md Section 6
- [x] T013 Create `backend/app/models.py` with TaskBase, TaskCreate, TaskUpdate, Task (table=True), and TaskResponse SQLModel classes per plan.md Section 2 and data-model.md
- [x] T014 Initialize Alembic with `backend/alembic.ini` and `backend/alembic/env.py` configured for async SQLModel migrations against Neon PostgreSQL
- [x] T015 Create Alembic migration `backend/alembic/versions/001_create_task_table.py` for the `task` table with UUID PK, user_id FK, title, description, completed, timestamps, and indexes per data-model.md
- [x] T016 Create `backend/app/dependencies.py` with `get_current_user()` FastAPI dependency that validates Bearer token via Better Auth's `/api/auth/get-session` endpoint and returns `user_id` per plan.md Section 4
- [x] T017 Create `backend/app/routes/__init__.py` as empty package init
- [x] T018 Create `backend/app/main.py` with FastAPI app factory, lifespan handler, CORS middleware (using settings.cors_origins_list), and router inclusion per plan.md Section 6

### Frontend Foundation

- [x] T019 Create `frontend/src/lib/auth.ts` with Better Auth server instance configured with Kysely/Neon database adapter, email/password plugin, Bearer plugin, and JWT plugin per plan.md Section 5
- [x] T020 Create `frontend/src/lib/auth-client.ts` with Better Auth client instance using `createAuthClient()` for browser-side auth operations per plan.md Section 5
- [x] T021 Create `frontend/src/lib/api.ts` with server-side fetch wrapper for FastAPI calls that attaches `Authorization: Bearer <token>` header, with get/post/put/patch/del methods per plan.md Section 5
- [x] T022 Create `frontend/src/app/api/auth/[...all]/route.ts` with Better Auth API route handler to expose `/api/auth/*` endpoints
- [x] T023 Create `frontend/src/proxy.ts` with cookie-existence check for session token, redirect unauthenticated users to `/login`, redirect authenticated users from `/login` and `/signup` to `/dashboard` per plan.md Section 5
- [x] T024 Create `frontend/src/app/layout.tsx` with root HTML layout, body, Tailwind CSS globals import, and metadata configuration
- [x] T025 Create `frontend/src/app/page.tsx` as landing page that redirects authenticated users to `/dashboard` and unauthenticated users to `/login`

### Shared UI Components

- [x] T026 [P] Create `frontend/src/components/ui/button.tsx` with styled button component supporting primary, danger, and ghost variants with responsive sizing
- [x] T027 [P] Create `frontend/src/components/ui/input.tsx` with styled input component supporting label, placeholder, error state display, and max-length indicators
- [x] T028 [P] Create `frontend/src/components/ui/error-message.tsx` with inline validation error display component for form fields

**Checkpoint**: Backend starts with `uvicorn app.main:app --reload --port 8000` and shows Swagger docs at `/docs`. Frontend starts with `npm run dev` and shows landing page. Better Auth endpoints respond at `/api/auth/*`. Database connection succeeds. Alembic migrations run successfully.

---

## Phase 3: User Story 1 — User Registration and Login (Priority: P1) MVP

**Goal**: Users can register with email/password, log in, see their dashboard, and log out. This is the gateway to the entire application.

**Independent Test**: Register a new account, verify redirect to empty dashboard, log out, log back in with same credentials, verify redirect to dashboard.

**Acceptance Criteria** (from spec.md US1):
1. Sign up with valid email/password creates account and redirects to empty dashboard
2. Login with valid credentials redirects to dashboard
3. Duplicate email shows clear error
4. Invalid credentials show clear error
5. Logout ends session and redirects to login

### Implementation for User Story 1

- [x] T029 [P] [US1] Create `frontend/src/components/auth/signup-form.tsx` client component with email input, password input, submit button, calls `authClient.signUp.email()`, handles duplicate email error, redirects to `/dashboard` on success
- [x] T030 [P] [US1] Create `frontend/src/components/auth/login-form.tsx` client component with email input, password input, submit button, calls `authClient.signIn.email()`, handles invalid credentials error, redirects to `/dashboard` on success
- [x] T031 [US1] Create `frontend/src/app/signup/page.tsx` server page that renders `<SignupForm />` with link to `/login` for existing users
- [x] T032 [US1] Create `frontend/src/app/login/page.tsx` server page that renders `<LoginForm />` with link to `/signup` for new users
- [x] T033 [US1] Create `frontend/src/app/dashboard/layout.tsx` authenticated layout with navigation bar showing app title and "Log Out" button that calls `authClient.signOut()` and redirects to `/login`
- [x] T034 [US1] Create `frontend/src/app/dashboard/page.tsx` server page that fetches session via `auth.api.getSession()`, shows user email in nav, renders empty state initially (task list comes in US2/US3)

**Checkpoint**: User Story 1 is fully functional. Register, login, logout all work. Unauthenticated users are redirected to `/login`. Authenticated users visiting `/login` are redirected to `/dashboard`.

---

## Phase 4: User Story 2 — Create a New Task (Priority: P1) MVP

**Goal**: Authenticated users can create tasks with a title (required) and optional description. New tasks appear immediately in the list.

**Independent Test**: Log in, click "Add Task", enter title and description, submit. Task appears in the list without page reload. Submit without title shows validation error.

**Acceptance Criteria** (from spec.md US2):
1. Clicking "Add Task" and submitting with title creates task with "incomplete" status
2. Both title and description are saved and visible
3. Submitting without title shows "Title is required" validation error
4. Task appears immediately without full page reload

### Implementation for User Story 2

- [x] T035 [US2] Create `backend/app/routes/todos.py` with `POST /api/todos` endpoint that accepts TaskCreate body, sets user_id from `get_current_user` dependency, creates Task in database, returns 201 with TaskResponse per contracts/api.yaml
- [x] T036 [US2] Register todos router in `backend/app/main.py` with `app.include_router(todos.router, prefix="/api")`
- [x] T037 [US2] Create `frontend/src/app/dashboard/actions.ts` with `createTask` server action that validates session, forwards request to `POST /api/todos` with Bearer token, and calls `revalidatePath("/dashboard")`
- [x] T038 [US2] Create `frontend/src/components/tasks/task-form.tsx` client component with title input (required, max 255 chars), description textarea (optional, max 2000 chars), client-side validation (non-empty title, whitespace-only rejection), submit calls `createTask` server action
- [x] T039 [US2] Add `getTasks` server action in `frontend/src/app/dashboard/actions.ts` that validates session, calls `GET /api/todos` with Bearer token, returns task list

**Checkpoint**: User Story 2 is functional. Backend `POST /api/todos` creates tasks. Frontend form submits tasks with validation. Tasks are persisted in database.

---

## Phase 5: User Story 3 — View Task List (Priority: P1) MVP

**Goal**: Authenticated users see all their tasks on the dashboard with title, description, and completion status in reverse chronological order. Empty state shown when no tasks exist.

**Independent Test**: Log in as user with existing tasks. All tasks display with correct details. New user sees empty state message. Two different users see only their own tasks.

**Acceptance Criteria** (from spec.md US3):
1. Dashboard shows all tasks with title, description, and completion status
2. Empty state message shown when no tasks exist
3. User isolation — each user sees only their own tasks
4. Tasks displayed newest first (reverse chronological)

### Implementation for User Story 3

- [x] T040 [US3] Add `GET /api/todos` endpoint in `backend/app/routes/todos.py` that returns all tasks for authenticated user ordered by `created_at DESC` per contracts/api.yaml
- [x] T041 [US3] Add `GET /api/todos/{task_id}` endpoint in `backend/app/routes/todos.py` that returns single task filtered by both `id` AND `user_id`, returns 404 for missing or cross-user access per contracts/api.yaml
- [x] T042 [P] [US3] Create `frontend/src/components/tasks/empty-state.tsx` component with friendly message encouraging user to create their first task
- [x] T043 [US3] Create `frontend/src/components/tasks/task-item.tsx` client component that renders single task row with title, description (if present), and completion status indicator (checkbox)
- [x] T044 [US3] Create `frontend/src/components/tasks/task-list.tsx` client component that receives tasks as props, maps to `<TaskItem />` components, shows `<EmptyState />` when array is empty, includes `<TaskForm />` for creation
- [x] T045 [US3] Update `frontend/src/app/dashboard/page.tsx` to call `getTasks` server action on load, pass tasks to `<TaskList />` component, handle loading and error states

**Checkpoint**: User Story 3 is functional. Dashboard shows task list or empty state. Tasks display in reverse chronological order. User isolation verified — different users see different tasks.

---

## Phase 6: User Story 4 — Mark Task Complete/Incomplete (Priority: P2)

**Goal**: Users can toggle task completion status. Completed tasks are visually distinguished with strikethrough/muted styling. Status persists on refresh.

**Independent Test**: Toggle a task from incomplete to complete. Verify visual change (strikethrough). Refresh page. Status persists. Toggle back to incomplete. Verify styling reverts.

**Acceptance Criteria** (from spec.md US4):
1. Clicking toggle marks incomplete task as complete with visual distinction
2. Clicking toggle on completed task marks it as incomplete with normal styling
3. Completion status persists after page refresh

### Implementation for User Story 4

- [x] T046 [US4] Add `PATCH /api/todos/{task_id}/complete` endpoint in `backend/app/routes/todos.py` that toggles `completed` boolean, updates `updated_at`, returns updated TaskResponse per contracts/api.yaml
- [x] T047 [US4] Add `toggleComplete` server action in `frontend/src/app/dashboard/actions.ts` that validates session, calls `PATCH /api/todos/{task_id}/complete` with Bearer token, revalidates `/dashboard`
- [x] T048 [US4] Update `frontend/src/components/tasks/task-item.tsx` to add checkbox/toggle control that calls `toggleComplete` server action, apply strikethrough and muted styling to completed tasks via Tailwind classes (`line-through text-gray-400`)

**Checkpoint**: User Story 4 is functional. Toggle works in both directions. Visual distinction clear. Persists across page refresh.

---

## Phase 7: User Story 5 — Edit Task Details (Priority: P2)

**Goal**: Users can edit task title and description via an edit form. Changes are saved and displayed. Validation prevents empty titles.

**Independent Test**: Click "Edit" on a task. Modify title and description. Save. Verify updated values display. Try clearing title and saving — validation error appears. Click "Cancel" — original values retained.

**Acceptance Criteria** (from spec.md US5):
1. Clicking "Edit" and modifying title saves updated title
2. Modifying description saves updated description
3. Clearing title and saving shows "Title is required" validation error
4. Clicking "Cancel" retains original values

### Implementation for User Story 5

- [x] T049 [US5] Add `PUT /api/todos/{task_id}` endpoint in `backend/app/routes/todos.py` that accepts TaskUpdate body, applies partial update (only provided fields), refreshes `updated_at`, returns updated TaskResponse per contracts/api.yaml
- [x] T050 [US5] Add `updateTask` server action in `frontend/src/app/dashboard/actions.ts` that validates session, calls `PUT /api/todos/{task_id}` with Bearer token and update data, revalidates `/dashboard`
- [x] T051 [US5] Update `frontend/src/components/tasks/task-form.tsx` to support edit mode — accept optional initial values (title, description, taskId), show "Save" instead of "Add", show "Cancel" button that discards changes
- [x] T052 [US5] Update `frontend/src/components/tasks/task-item.tsx` to add "Edit" button that toggles inline edit mode using `<TaskForm />` in edit mode, hide task display when editing

**Checkpoint**: User Story 5 is functional. Edit, save, cancel all work. Validation prevents empty titles on edit. Updated values persist.

---

## Phase 8: User Story 6 — Delete a Task (Priority: P3)

**Goal**: Users can delete tasks after confirming via a dialog. Deleted tasks are permanently removed from the list.

**Independent Test**: Click "Delete" on a task. Confirmation dialog appears. Click "Cancel" — task remains. Click "Delete" again, confirm — task is permanently removed from list.

**Acceptance Criteria** (from spec.md US6):
1. Clicking "Delete" shows confirmation dialog
2. Confirming deletion permanently removes task from list
3. Canceling deletion keeps task in list

### Implementation for User Story 6

- [x] T053 [US6] Add `DELETE /api/todos/{task_id}` endpoint in `backend/app/routes/todos.py` that deletes task filtered by `id` AND `user_id`, returns 204 No Content, returns 404 for missing/cross-user access per contracts/api.yaml
- [x] T054 [US6] Add `deleteTask` server action in `frontend/src/app/dashboard/actions.ts` that validates session, calls `DELETE /api/todos/{task_id}` with Bearer token, revalidates `/dashboard`
- [x] T055 [US6] Create `frontend/src/components/tasks/delete-dialog.tsx` client component with confirmation modal: "Are you sure?" message, "Cancel" button (closes dialog), "Delete" button (calls `deleteTask` server action, danger variant styling)
- [x] T056 [US6] Update `frontend/src/components/tasks/task-item.tsx` to add "Delete" button that opens `<DeleteDialog />`, pass task ID and title for display in confirmation message

**Checkpoint**: User Story 6 is functional. Delete with confirmation works. Canceled deletion preserves task. Deleted tasks are gone permanently.

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Responsive design, error handling edge cases, environment file validation

- [x] T057 [P] Add responsive Tailwind CSS styling to all pages ensuring functionality on viewports 375px (mobile) to 1920px (desktop) per FR-013 and SC-006
- [x] T058 [P] Add error handling for backend unavailability in frontend — display user-friendly error message and allow retry without data loss per edge case specification
- [x] T059 [P] Add `frontend/public/favicon.ico` and update metadata in `frontend/src/app/layout.tsx` with app title "Todo App"
- [x] T060 Verify full task lifecycle end-to-end: register, create task, view list, edit task, toggle complete, delete task, logout, login again, verify data persists

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
- **US1 (Phase 3)**: Depends on Foundational — auth must work before any task operations
- **US2 (Phase 4)**: Depends on US1 — must be logged in to create tasks
- **US3 (Phase 5)**: Depends on US2 — need tasks to display (also provides the list container for US4-US6)
- **US4 (Phase 6)**: Depends on US3 — needs task-item component and list display
- **US5 (Phase 7)**: Depends on US3 — needs task-item component and task-form component
- **US6 (Phase 8)**: Depends on US3 — needs task-item component and list display
- **Polish (Phase 9)**: Depends on all user stories being complete

### User Story Dependencies

- **US1 (Auth)**: Foundation only — no dependency on other stories
- **US2 (Create)**: Depends on US1 (must be authenticated)
- **US3 (View)**: Depends on US2 (need tasks to view; creates the task-list/task-item components)
- **US4 (Toggle)**: Depends on US3 (needs task-item component to add toggle)
- **US5 (Edit)**: Depends on US3 (needs task-item and task-form components)
- **US6 (Delete)**: Depends on US3 (needs task-item component to add delete button)
- **US4, US5, US6**: Independent of each other — can run in parallel after US3

### Within Each User Story

- Backend endpoints before frontend server actions
- Server actions before client components that call them
- Core components before updates to existing components

### Parallel Opportunities

**After Phase 2 (Foundational):**
- T029 and T030 (signup-form and login-form) can run in parallel

**After Phase 5 (US3 complete):**
- US4 (Phase 6), US5 (Phase 7), and US6 (Phase 8) can all start in parallel since they modify different aspects of `task-item.tsx`
- Within each: backend endpoint can be built independently of other stories' backend endpoints

**After all stories complete:**
- All Phase 9 polish tasks (T057, T058, T059) can run in parallel

---

## Parallel Example: After US3 Completion

```bash
# These three backend tasks can run in parallel (different endpoints, different HTTP methods):
Task T046: "PATCH /api/todos/{task_id}/complete in backend/app/routes/todos.py"
Task T049: "PUT /api/todos/{task_id} in backend/app/routes/todos.py"
Task T053: "DELETE /api/todos/{task_id} in backend/app/routes/todos.py"

# After backend endpoints exist, these server actions can run in parallel:
Task T047: "toggleComplete server action in frontend/src/app/dashboard/actions.ts"
Task T050: "updateTask server action in frontend/src/app/dashboard/actions.ts"
Task T054: "deleteTask server action in frontend/src/app/dashboard/actions.ts"
```

---

## Implementation Strategy

### MVP First (User Stories 1 + 2 + 3)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL — blocks all stories)
3. Complete Phase 3: US1 — Registration & Login
4. Complete Phase 4: US2 — Create Task
5. Complete Phase 5: US3 — View Task List
6. **STOP and VALIDATE**: Full create-and-view flow works end-to-end
7. Deploy/demo if ready — users can register, create tasks, and view them

### Incremental Delivery

1. Setup + Foundational: Infrastructure ready
2. US1 (Auth): Users can register and log in
3. US2 + US3 (Create + View): Core task management works (MVP!)
4. US4 (Toggle): Progress tracking added
5. US5 (Edit): Task refinement added
6. US6 (Delete): List cleanup added
7. Each story adds value without breaking previous stories

### Task Count Summary

| Phase | Tasks | Parallelizable |
|-------|-------|---------------|
| Phase 1: Setup | 9 | 7 |
| Phase 2: Foundational | 19 | 3 |
| Phase 3: US1 Auth | 6 | 2 |
| Phase 4: US2 Create | 5 | 0 |
| Phase 5: US3 View | 6 | 1 |
| Phase 6: US4 Toggle | 3 | 0 |
| Phase 7: US5 Edit | 4 | 0 |
| Phase 8: US6 Delete | 4 | 0 |
| Phase 9: Polish | 4 | 3 |
| **Total** | **60** | **16** |

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks
- [Story] label maps task to specific user story for traceability
- Backend endpoints are built per contracts/api.yaml OpenAPI spec
- All queries filter by `user_id` from JWT — Constitution Principle V
- Every task references exact file paths from plan.md Section 1
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
