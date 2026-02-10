"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { TaskForm } from "@/components/tasks/task-form";
import { DeleteDialog } from "@/components/tasks/delete-dialog";
import { toggleComplete } from "@/app/dashboard/actions";

export interface TaskData {
  id: string;
  title: string;
  description: string | null;
  completed: boolean;
  created_at: string;
  updated_at: string;
}

interface TaskItemProps {
  task: TaskData;
}

export function TaskItem({ task }: TaskItemProps) {
  const router = useRouter();
  const [editing, setEditing] = useState(false);
  const [showDelete, setShowDelete] = useState(false);
  const [toggling, setToggling] = useState(false);

  async function handleToggle() {
    setToggling(true);
    try {
      await toggleComplete(task.id);
      router.refresh();
    } finally {
      setToggling(false);
    }
  }

  if (editing) {
    return (
      <div className="rounded-lg border border-zinc-200 bg-white p-4 dark:border-zinc-800 dark:bg-zinc-900">
        <TaskForm
          mode="edit"
          taskId={task.id}
          initialTitle={task.title}
          initialDescription={task.description || ""}
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
          <p
            className={`font-medium ${
              task.completed
                ? "text-zinc-400 line-through dark:text-zinc-500"
                : "text-zinc-900 dark:text-zinc-100"
            }`}
          >
            {task.title}
          </p>
          {task.description && (
            <p
              className={`mt-1 text-sm ${
                task.completed
                  ? "text-zinc-400 line-through dark:text-zinc-600"
                  : "text-zinc-500 dark:text-zinc-400"
              }`}
            >
              {task.description}
            </p>
          )}
        </div>
        <div className="flex gap-1">
          <Button variant="ghost" onClick={() => setEditing(true)}>
            Edit
          </Button>
          <Button variant="ghost" onClick={() => setShowDelete(true)}>
            Delete
          </Button>
        </div>
      </div>
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
