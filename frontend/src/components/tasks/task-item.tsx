"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { formatDistanceToNow, isPast, isToday } from "date-fns";
import { Button } from "@/components/ui/button";
import { PriorityBadge } from "@/components/ui/priority-badge";
import { TaskForm } from "@/components/tasks/task-form";
import { DeleteDialog } from "@/components/tasks/delete-dialog";
import { TaskHistory } from "@/components/tasks/task-history";
import { toggleComplete } from "@/app/dashboard/actions";

export interface TaskData {
  id: string;
  title: string;
  description: string | null;
  completed: boolean;
  created_at: string;
  updated_at: string;
  priority: "high" | "medium" | "low";
  tags: string[];
  due_date: string | null;
  recurrence_pattern: { frequency: string; interval: number; next_due: string } | null;
  reminder_minutes: number | null;
  snoozed_until: string | null;
  reminder_notified_at: string | null;
  parent_task_id: string | null;
}

interface TaskItemProps {
  task: TaskData;
  authToken?: string;
}

export function TaskItem({ task, authToken }: TaskItemProps) {
  const router = useRouter();
  const [editing, setEditing] = useState(false);
  const [showDelete, setShowDelete] = useState(false);
  const [toggling, setToggling] = useState(false);
  const [expanded, setExpanded] = useState(false);
  const [showHistory, setShowHistory] = useState(false);

  async function handleToggle() {
    setToggling(true);
    try {
      await toggleComplete(task.id);
      router.refresh();
    } finally {
      setToggling(false);
    }
  }

  function renderDueDate() {
    if (!task.due_date) return null;
    const due = new Date(task.due_date);
    const overdue = !task.completed && isPast(due) && !isToday(due);
    const dueToday = !task.completed && isToday(due);

    let text: string;
    if (overdue) {
      text = `Overdue ${formatDistanceToNow(due, { addSuffix: false })}`;
    } else {
      text = `Due ${formatDistanceToNow(due, { addSuffix: true })}`;
    }

    return (
      <span
        className={`text-xs ${
          overdue
            ? "font-medium text-red-600 dark:text-red-400"
            : dueToday
              ? "font-medium text-amber-600 dark:text-amber-400"
              : "text-zinc-500 dark:text-zinc-400"
        }`}
      >
        {text}
      </span>
    );
  }

  const descriptionLong =
    task.description && task.description.length > 100;

  if (editing) {
    return (
      <div className="rounded-lg border border-zinc-200 bg-white p-4 dark:border-zinc-800 dark:bg-zinc-900">
        <TaskForm
          mode="edit"
          taskId={task.id}
          initialTitle={task.title}
          initialDescription={task.description || ""}
          initialPriority={task.priority}
          initialTags={task.tags}
          initialDueDate={task.due_date}
          initialRecurrence={task.recurrence_pattern}
          initialReminderMinutes={task.reminder_minutes}
          onSuccess={() => {
            setEditing(false);
            router.refresh();
          }}
          onCancel={() => setEditing(false)}
        />
      </div>
    );
  }

  return (
    <>
      <div className="flex items-start gap-3 rounded-lg border border-zinc-200 bg-white p-4 dark:border-zinc-800 dark:bg-zinc-900">
        <input
          type="checkbox"
          checked={task.completed}
          onChange={handleToggle}
          disabled={toggling}
          className="mt-1 h-4 w-4 rounded border-zinc-300 text-zinc-900 focus:ring-zinc-500 dark:border-zinc-600"
        />
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <p
              className={`font-medium ${
                task.completed
                  ? "text-zinc-400 line-through dark:text-zinc-500"
                  : "text-zinc-900 dark:text-zinc-100"
              }`}
            >
              {task.title}
            </p>
            <PriorityBadge priority={task.priority} />
            {task.recurrence_pattern && (
              <span className="inline-flex items-center text-xs text-zinc-500 dark:text-zinc-400">
                Repeats {task.recurrence_pattern.frequency}
              </span>
            )}
          </div>

          {/* Tags */}
          {task.tags.length > 0 && (
            <div className="mt-1 flex flex-wrap gap-1">
              {task.tags.map((tag) => (
                <span
                  key={tag}
                  className="rounded bg-zinc-100 px-1.5 py-0.5 text-xs text-zinc-600 dark:bg-zinc-800 dark:text-zinc-400"
                >
                  {tag}
                </span>
              ))}
            </div>
          )}

          {/* Description with show more/less */}
          {task.description && (
            <div className="mt-1">
              <p
                className={`text-sm whitespace-pre-wrap ${
                  task.completed
                    ? "text-zinc-400 line-through dark:text-zinc-600"
                    : "text-zinc-500 dark:text-zinc-400"
                }`}
              >
                {descriptionLong && !expanded
                  ? task.description.slice(0, 100) + "..."
                  : task.description}
              </p>
              {descriptionLong && (
                <button
                  type="button"
                  onClick={() => setExpanded(!expanded)}
                  className="text-xs text-zinc-500 hover:text-zinc-700 dark:text-zinc-400 dark:hover:text-zinc-200"
                >
                  {expanded ? "Show less" : "Show more"}
                </button>
              )}
            </div>
          )}

          {/* Due date */}
          <div className="mt-1 flex items-center gap-2">
            {renderDueDate()}
          </div>
        </div>
        <div className="flex gap-1">
          <Button variant="ghost" onClick={() => setShowHistory(!showHistory)}>
            History
          </Button>
          <Button variant="ghost" onClick={() => setEditing(true)}>
            Edit
          </Button>
          <Button variant="ghost" onClick={() => setShowDelete(true)}>
            Delete
          </Button>
        </div>
      </div>
      {showHistory && (
        <TaskHistory taskId={task.id} token={authToken} isOpen={showHistory} />
      )}
      {showDelete && (
        <DeleteDialog
          taskId={task.id}
          taskTitle={task.title}
          onClose={() => setShowDelete(false)}
          onDeleted={() => {
            setShowDelete(false);
            router.refresh();
          }}
        />
      )}
    </>
  );
}
