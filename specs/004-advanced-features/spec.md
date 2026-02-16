# Feature Specification: Enhanced Task Management

**Feature Branch**: `004-advanced-features`
**Created**: 2026-02-16
**Status**: Draft
**Input**: User description: "Phase 5A — Advanced & Intermediate Todo Features: Priorities, Tags, Search, Recurring Tasks, and Reminders"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Set Task Priority (Priority: P1)

As a user, I can assign a priority level (High, Medium, Low) to any task so I can focus on what matters most.

**Why this priority**: Priority is the simplest enhancement that immediately improves task organization. Every task management tool needs this — it's the foundation for filtering and sorting.

**Independent Test**: Can be fully tested by creating a task with a priority, verifying it displays correctly, and confirming it persists across page reloads.

**Acceptance Scenarios**:

1. **Given** I am creating a new task, **When** I select a priority level (High, Medium, or Low), **Then** the task is saved with that priority and displays a visual indicator (color or icon).
2. **Given** I have an existing task with no priority, **When** I edit the task and set it to High priority, **Then** the priority updates immediately and the visual indicator reflects the change.
3. **Given** I am creating a task, **When** I do not select a priority, **Then** the task defaults to Medium priority.

---

### User Story 2 - Tag and Categorize Tasks (Priority: P1)

As a user, I can label tasks with tags (e.g., "work", "personal", "shopping") so I can organize and group related tasks.

**Why this priority**: Tags enable categorization — a core organizational feature that unlocks filtering and grouping capabilities.

**Independent Test**: Can be fully tested by adding tags to a task, verifying they display as chips/badges, and confirming they persist.

**Acceptance Scenarios**:

1. **Given** I am creating or editing a task, **When** I type a tag name and press Enter or comma, **Then** the tag is added as a removable chip/badge on the task.
2. **Given** a task has multiple tags, **When** I click the remove icon on a tag, **Then** that tag is removed from the task.
3. **Given** I am adding a tag, **When** I type a tag name that already exists on other tasks, **Then** the system suggests existing tags for auto-completion.
4. **Given** I add a tag with mixed case (e.g., "Work"), **When** I view it, **Then** it is stored and displayed in lowercase ("work") for consistency.

---

### User Story 3 - Set Due Dates (Priority: P1)

As a user, I can set a due date on tasks so I know when they need to be completed.

**Why this priority**: Due dates are essential for time-sensitive task management and enable sorting by urgency.

**Independent Test**: Can be fully tested by setting a due date on a task via date picker and verifying it displays correctly with overdue visual indicators.

**Acceptance Scenarios**:

1. **Given** I am creating or editing a task, **When** I click the due date field, **Then** a date picker appears allowing me to select a future date.
2. **Given** a task has a due date that has passed, **When** I view my task list, **Then** the overdue task displays a warning indicator (e.g., red text or icon).
3. **Given** a task has a due date set for today, **When** I view my task list, **Then** the task displays a "due today" indicator.
4. **Given** I want to remove a due date, **When** I clear the date field, **Then** the due date is removed from the task.

---

### User Story 4 - Search Tasks (Priority: P1)

As a user, I can search my tasks by keyword so I can quickly find specific tasks.

**Why this priority**: Search is critical for usability once a user has more than a handful of tasks.

**Independent Test**: Can be fully tested by creating several tasks, entering a keyword in the search bar, and verifying only matching tasks appear.

**Acceptance Scenarios**:

1. **Given** I have multiple tasks, **When** I type a keyword in the search bar, **Then** only tasks whose title or description contains that keyword are displayed.
2. **Given** I search for "grocery", **When** tasks exist with "grocery" in the title or description, **Then** those tasks appear in the results regardless of case.
3. **Given** I clear the search bar, **When** the search field is empty, **Then** all tasks are displayed again (respecting any active filters).
4. **Given** I search for a term with no matches, **When** no tasks match, **Then** an empty state message is shown (e.g., "No tasks found").

---

### User Story 5 - Filter Tasks (Priority: P2)

As a user, I can filter my task list by status, priority, or tag so I can focus on a relevant subset of tasks.

**Why this priority**: Filtering builds on priorities and tags (P1 stories) to provide meaningful organization.

**Independent Test**: Can be fully tested by applying filters and verifying the task list updates to show only matching tasks.

**Acceptance Scenarios**:

1. **Given** I have tasks with different statuses, **When** I filter by "Pending", **Then** only incomplete tasks are shown.
2. **Given** I have tasks with different priorities, **When** I filter by "High" priority, **Then** only high-priority tasks are shown.
3. **Given** I have tasks with different tags, **When** I filter by the tag "work", **Then** only tasks tagged "work" are shown.
4. **Given** I have multiple filters active (e.g., priority=High AND tag="work"), **When** I view the results, **Then** only tasks matching ALL active filters are shown (AND logic).
5. **Given** I have active filters, **When** I click "Clear filters", **Then** all filters are removed and the full task list is displayed.

---

### User Story 6 - Sort Tasks (Priority: P2)

As a user, I can sort my task list by due date, priority, or creation time so I can view tasks in the order most useful to me.

**Why this priority**: Sorting complements filtering and provides flexible viewing options.

**Independent Test**: Can be fully tested by selecting a sort option and verifying the task order changes accordingly.

**Acceptance Scenarios**:

1. **Given** I have tasks with different due dates, **When** I sort by "Due Date (soonest first)", **Then** tasks are ordered with the earliest due date first; tasks without due dates appear at the end.
2. **Given** I have tasks with different priorities, **When** I sort by "Priority (highest first)", **Then** tasks are ordered High > Medium > Low.
3. **Given** I am viewing tasks, **When** I sort by "Created (newest first)", **Then** tasks are ordered by creation date descending (default behavior).

---

### User Story 7 - Task Descriptions (Priority: P2)

As a user, I can add longer descriptions to tasks so I can capture additional context and details.

**Why this priority**: Descriptions already exist in the data model but need better UI support for longer content.

**Independent Test**: Can be fully tested by expanding a task, entering a multi-line description, and verifying it saves and displays correctly.

**Acceptance Scenarios**:

1. **Given** I am creating or editing a task, **When** I click on the description field, **Then** an expandable text area appears supporting multi-line input.
2. **Given** a task has a long description, **When** I view the task in the list, **Then** a truncated preview is shown with a "show more" option.
3. **Given** I expand a task's description, **When** I read the full description, **Then** it preserves line breaks and formatting.

---

### User Story 8 - Recurring Tasks (Priority: P3)

As a user, I can create recurring tasks that automatically generate new instances on a schedule (daily, weekly, monthly) so I don't forget regular responsibilities.

**Why this priority**: Recurring tasks add significant value but have higher complexity. They depend on core task features being stable first.

**Independent Test**: Can be fully tested by creating a recurring task, advancing time (or triggering the recurrence manually), and verifying a new task instance is created.

**Acceptance Scenarios**:

1. **Given** I am creating a task, **When** I enable recurrence and select "Daily", **Then** the task is marked as recurring with a daily schedule.
2. **Given** a daily recurring task exists, **When** the scheduled time arrives, **Then** a new task instance is automatically created with the same title, description, priority, and tags.
3. **Given** I complete a recurring task instance, **When** I mark it done, **Then** only that instance is marked complete; the recurrence schedule continues generating future instances.
4. **Given** I want to stop a recurrence, **When** I edit the task and disable recurrence, **Then** no further instances are created but existing instances remain.
5. **Given** I set a weekly recurrence, **When** I view the task, **Then** it shows the recurrence pattern (e.g., "Repeats every Monday").

---

### User Story 9 - Reminders (Priority: P3)

As a user, I receive browser notifications before a task's due date so I don't miss deadlines.

**Why this priority**: Reminders are valuable but depend on due dates (P1) and require browser notification permissions, adding complexity.

**Independent Test**: Can be fully tested by setting a reminder, waiting for the trigger time, and verifying a browser notification appears.

**Acceptance Scenarios**:

1. **Given** I set a due date on a task, **When** I enable reminders, **Then** I can choose a reminder time (e.g., 15 minutes before, 1 hour before, 1 day before).
2. **Given** a reminder is set and the reminder time arrives, **When** I have the app open in my browser, **Then** a browser notification appears with the task title and due time.
3. **Given** a browser notification appears, **When** I click "Snooze", **Then** the reminder is postponed by 15 minutes.
4. **Given** the browser has not granted notification permission, **When** I try to enable reminders, **Then** the system prompts me to allow notifications and explains why.

---

### Edge Cases

- What happens when a user creates a task with more than 10 tags? System limits tags to 10 per task and shows a validation message.
- What happens when a recurring task's parent is deleted? All future recurrences stop; existing instances remain.
- What happens when a user searches with special characters? Special characters are escaped; the search treats them as literal text.
- What happens when filters and search are used simultaneously? Both are applied together (AND logic) — search results are further filtered.
- What happens when a task is overdue and completed? The overdue indicator is removed; the task shows as completed.
- What happens when a recurring task is set to recur daily but the user doesn't complete it for 3 days? Only one new instance is created per scheduled interval, not backfilled for missed days.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST allow users to assign a priority (High, Medium, Low) to any task, defaulting to Medium when not specified.
- **FR-002**: System MUST allow users to add up to 10 tags per task, stored as lowercase strings.
- **FR-003**: System MUST suggest existing tags when a user begins typing a tag name (auto-complete from user's existing tags).
- **FR-004**: System MUST allow users to set an optional due date on any task via a date picker.
- **FR-005**: System MUST visually indicate overdue tasks (past due date and not completed) and tasks due today.
- **FR-006**: System MUST provide keyword search across task titles and descriptions, case-insensitive.
- **FR-007**: System MUST allow filtering tasks by status (pending/completed), priority level, and tag.
- **FR-008**: System MUST support combining multiple filters with AND logic.
- **FR-009**: System MUST allow sorting tasks by due date, priority, or creation date in ascending or descending order.
- **FR-010**: System MUST support multi-line task descriptions with a text area input.
- **FR-011**: System MUST allow users to create recurring tasks with daily, weekly, or monthly schedules.
- **FR-012**: System MUST automatically generate new task instances based on recurrence schedules.
- **FR-013**: System MUST allow users to disable recurrence on a task, stopping future instance generation.
- **FR-014**: System MUST allow users to set reminders on tasks with due dates, with configurable lead times (15 min, 1 hour, 1 day before).
- **FR-015**: System MUST deliver reminders as browser notifications when the user has the app open.
- **FR-016**: System MUST allow users to snooze a reminder, postponing it by 15 minutes.
- **FR-017**: System MUST prompt users for browser notification permission when they first enable reminders.
- **FR-018**: Search and filter operations MUST work together — search results are further filtered by active filters.

### Key Entities

- **Task** (extended): Existing task entity enhanced with priority (enum: high/medium/low), tags (list of strings, max 10), due_date (optional datetime), description (expanded UI support), and reminder settings.
- **Recurrence Rule**: Defines the schedule pattern for a recurring task — includes frequency (daily/weekly/monthly), interval, and optional end date. Linked to a parent task.
- **Reminder**: Represents a scheduled notification for a task — includes the task reference, trigger time (computed from due date minus lead time), and snooze state.
- **Tag**: A lightweight label (lowercase string) associated with tasks. Tags are user-scoped and reusable across tasks.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can create a task with priority, tags, and due date in under 30 seconds.
- **SC-002**: Search returns matching results within 1 second for a user with up to 500 tasks.
- **SC-003**: Filtering by any combination of status, priority, and tag updates the task list within 1 second.
- **SC-004**: Sorting changes are reflected in the task list within 1 second.
- **SC-005**: Recurring tasks generate new instances within 5 minutes of their scheduled time.
- **SC-006**: Browser reminders are delivered within 1 minute of the configured trigger time.
- **SC-007**: 90% of users can successfully apply filters and find a specific task on their first attempt.
- **SC-008**: All new fields (priority, tags, due date) are backward-compatible — existing tasks without these fields continue to function normally.

## Assumptions

- Browser notification API (Notification API) is supported by target browsers (modern Chrome, Firefox, Edge, Safari).
- Recurring task generation will be handled by a background job or scheduled process (not event-driven/Kafka — that is deferred to Phase 5B).
- The existing task list UI will be extended rather than rebuilt from scratch.
- Tag auto-complete uses only the current user's existing tags, not a global tag dictionary.
- The snooze duration is fixed at 15 minutes (not configurable).
- Recurring tasks do not backfill missed instances — if the system was down during a scheduled generation, only the next scheduled instance is created.

## Constraints

- No Kafka or event-driven architecture in this phase (deferred to Phase 5B).
- Must be backward-compatible with existing task data — existing tasks without new fields must continue to work.
- Browser notifications require user permission and only work when the app is open in a browser tab.
- Maximum 10 tags per task to prevent abuse and maintain UI clarity.

## Dependencies

- Existing task CRUD (Feature 001-todo-crud) must be complete and stable.
- Better Auth session management for user-scoped operations.
- Browser Notification API availability.
