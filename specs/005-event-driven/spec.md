# Feature Specification: Event-Driven Todo System

**Feature Branch**: `005-event-driven`
**Created**: 2026-02-17
**Status**: Draft
**Input**: User description: "Event-Driven Todo System with Kafka messaging and Dapr runtime — Phase 5B"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Real-Time Task Sync Across Devices (Priority: P1)

A user creates, updates, or deletes a todo task on one device. All other connected clients (browser tabs, mobile sessions) immediately reflect the change without requiring a manual refresh. The system publishes task change events that connected clients consume to stay synchronized.

**Why this priority**: Real-time synchronization is the primary user-facing benefit of event-driven architecture. Without it, users see stale data and lose trust in multi-device workflows.

**Independent Test**: Can be fully tested by opening two browser tabs, performing a CRUD operation in one, and verifying the other tab updates within 2 seconds.

**Acceptance Scenarios**:

1. **Given** a user has the todo list open in two browser tabs, **When** they create a new task in Tab A, **Then** Tab B displays the new task within 2 seconds without manual refresh.
2. **Given** a user updates a task title on their phone, **When** they switch to their laptop browser, **Then** the updated title is already visible.
3. **Given** a user deletes a task in one session, **When** another session is open, **Then** the deleted task disappears from the list within 2 seconds.
4. **Given** a user marks a task as complete, **When** the event is published, **Then** all subscribers receive the completion event with the correct task ID and timestamp.

---

### User Story 2 - Due Date Reminder Notifications (Priority: P1)

A user sets a due date on a task. When the due date approaches (configurable threshold, default 1 hour before), the system sends a reminder notification. Overdue tasks are detected every 5 minutes and trigger escalated notifications.

**Why this priority**: Reminders are the core value of due dates — without notifications, due dates are just decorative labels. This is the most impactful new capability for end users.

**Independent Test**: Can be tested by creating a task with a due date 5 minutes in the future and verifying a reminder is received.

**Acceptance Scenarios**:

1. **Given** a task has a due date set to 1 hour from now, **When** the reminder threshold is reached, **Then** a reminder notification is generated for the task owner.
2. **Given** a task's due date has passed, **When** the overdue check runs (every 5 minutes), **Then** the system generates an overdue notification.
3. **Given** a user receives a reminder notification, **When** they view it, **Then** it contains the task title, due date, and a direct link to the task.
4. **Given** a task is completed before its due date, **When** the reminder check runs, **Then** no reminder is generated for that task.

---

### User Story 3 - Automatic Recurring Task Generation (Priority: P2)

A user marks a recurring task as complete. The system automatically creates the next occurrence based on the recurrence pattern (daily, weekly, monthly). The new task inherits the original's properties (title, tags, priority) with an updated due date.

**Why this priority**: Recurring tasks build on the existing advanced features (Phase 4) and represent a natural extension of the event-driven pattern — task completion events trigger new task creation.

**Independent Test**: Can be tested by completing a recurring task and verifying a new task instance appears with the correct next due date.

**Acceptance Scenarios**:

1. **Given** a weekly recurring task is marked complete, **When** the task-events subscriber processes the completion, **Then** a new task is created with the due date set to 7 days after the original.
2. **Given** a daily recurring task is completed, **When** the next occurrence is generated, **Then** it inherits the title, tags, and priority of the original.
3. **Given** a recurring task is deleted (not completed), **When** the delete event is published, **Then** no new occurrence is created.

---

### User Story 4 - Event Audit Trail (Priority: P3)

An administrator or power user can view the history of changes made to any task. Every create, update, delete, and status change is recorded as an event, providing a complete audit trail.

**Why this priority**: Audit trails are a secondary benefit of event sourcing. While valuable for debugging and compliance, they are not the primary user need.

**Independent Test**: Can be tested by performing several operations on a task and then viewing its event history to verify all changes are recorded in order.

**Acceptance Scenarios**:

1. **Given** a task has been created and updated 3 times, **When** the user views the task history, **Then** all 4 events (1 create + 3 updates) are displayed in chronological order.
2. **Given** an event is recorded, **When** displayed in the audit trail, **Then** it shows the event type, timestamp, user who made the change, and the changed fields.

---

### Edge Cases

- What happens when the message broker is temporarily unavailable? The system must queue events locally and retry delivery when the broker recovers (at-least-once delivery guarantee).
- What happens when a duplicate event is delivered? All event consumers must be idempotent — processing the same event twice produces the same result as processing it once.
- What happens when a task is updated simultaneously from two devices? The last-write-wins strategy applies at the database level; both events are recorded in the audit trail.
- What happens when the recurring task service receives a completion event for a non-recurring task? The service ignores events for tasks without a recurrence pattern.
- What happens when the overdue check runs and the notification service is down? Overdue reminders are published to the message queue and will be delivered when the notification service recovers.
- What happens when a user deletes their account? All pending reminders and recurring task subscriptions for that user are cancelled.

## Requirements *(mandatory)*

### Functional Requirements

#### Event Publishing

- **FR-001**: System MUST publish an event to the `task-events` topic whenever a task is created, updated, or deleted.
- **FR-002**: Each event MUST contain the event type (created, updated, deleted, completed), task ID, user ID, timestamp, and the changed data.
- **FR-003**: Events MUST be published asynchronously — the user's request completes without waiting for event delivery confirmation.
- **FR-004**: System MUST guarantee at-least-once delivery of events to the message broker.

#### Reminder Notifications

- **FR-005**: System MUST check for tasks approaching their due date and publish reminder events to the `reminders` topic.
- **FR-006**: The overdue task check MUST run on a recurring schedule (every 5 minutes).
- **FR-007**: Reminder events MUST include the task title, due date, owner, and a link to the task.
- **FR-008**: System MUST NOT generate duplicate reminders for the same task within a 5-minute dedup window. Once a reminder (upcoming or overdue) is sent for a task, the system skips that task for the next 5 minutes. This prevents rapid-fire notifications when cron runs overlap with the reminder threshold.
- **FR-009**: Completed tasks MUST be excluded from reminder checks.

#### Real-Time Client Sync

- **FR-010**: System MUST publish task change summaries to the `task-updates` topic for consumption by connected clients.
- **FR-011**: Connected clients MUST receive updates within 2 seconds of the event being published.
- **FR-012**: The real-time update payload MUST be minimal — containing only the changed fields and task identifier, not the full task object.

#### Recurring Task Generation

- **FR-013**: When a recurring task is completed, the system MUST automatically create the next occurrence with an updated due date.
- **FR-014**: The new task instance MUST inherit title, description, tags, priority, and recurrence pattern from the completed task.
- **FR-015**: Deleting a recurring task MUST NOT trigger creation of a new occurrence.

#### Event Consumer Reliability

- **FR-016**: All event consumers MUST be idempotent — processing the same event multiple times produces the same outcome.
- **FR-017**: System MUST support graceful degradation — if a consumer is down, events remain queued and are processed upon recovery.
- **FR-018**: Each microservice MUST use its own consumer group to ensure independent consumption of events.

#### Service Communication

- **FR-019**: Services MUST communicate via the Dapr runtime sidecar pattern for both pub/sub and direct invocation.
- **FR-020**: All inter-service communication MUST be authenticated and encrypted via mutual TLS.

### Key Entities

- **TaskEvent**: A record of a change to a task. Contains event type, task ID, user ID, timestamp, changed fields, and the before/after state. Published to `task-events` topic.
- **ReminderEvent**: A notification trigger for an approaching or overdue task. Contains task ID, owner, task title, due date, and reminder type (upcoming/overdue). Published to `reminders` topic.
- **TaskUpdate**: A lightweight change notification for real-time client sync. Contains task ID, change type, and minimal changed fields. Published to `task-updates` topic.
- **ConsumerOffset**: Tracks the last successfully processed event position for each consumer group, enabling at-least-once delivery and replay.

## Assumptions

- The existing todo CRUD system (Phase 1) and advanced features (Phase 4 — priority, tags, due dates, recurring tasks) are fully operational.
- The Kubernetes local deployment (Phase 3) is available as the deployment target.
- Redpanda is used as the Kafka-compatible broker for local development; production may use Redpanda Cloud or managed Kafka.
- Dapr v1.14+ is installed on the Kubernetes cluster with sidecar injection enabled.
- Notification delivery channel is in-app (displayed in the UI). Email/SMS/push notifications are out of scope for this phase.
- The frontend will be extended with an SSE client for real-time task updates as part of FR-011 (User Story 1, tasks T033-T035).
- Event retention period in the broker is 7 days (industry standard for task management).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Task changes made on one client appear on all other connected clients within 2 seconds, 99% of the time.
- **SC-002**: Reminder notifications are delivered within 5 minutes of the configured threshold (e.g., within 5 minutes of the 1-hour-before-due-date mark).
- **SC-003**: Recurring task next occurrence is created within 5 seconds of the previous occurrence being marked complete.
- **SC-004**: The system processes at least 100 events per second without message loss or consumer lag exceeding 10 seconds.
- **SC-005**: Event consumers recover from downtime and process all queued events within 60 seconds of restart.
- **SC-006**: Zero duplicate side effects from duplicate event delivery (idempotency verification).
- **SC-007**: Complete audit trail is available for 100% of task operations, with no gaps in event history.
- **SC-008**: All services deploy with Dapr sidecars on the local Kubernetes cluster and communicate exclusively through Dapr building blocks.
