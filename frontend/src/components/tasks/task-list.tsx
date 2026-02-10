"use client";

import { useRouter } from "next/navigation";
import { TaskItem, TaskData } from "@/components/tasks/task-item";
import { EmptyState } from "@/components/tasks/empty-state";
import { TaskForm } from "@/components/tasks/task-form";

interface TaskListProps {
  tasks: TaskData[];
}

export function TaskList({ tasks }: TaskListProps) {
  const router = useRouter();

  function handleTaskCreated() {
    router.refresh();
  }

  return (
    <div className="space-y-6">
      <TaskForm onSuccess={handleTaskCreated} />
      {tasks.length === 0 ? (
        <EmptyState />
      ) : (
        <div className="space-y-2">
          {tasks.map((task) => (
            <TaskItem key={task.id} task={task} />
          ))}
        </div>
      )}
    </div>
  );
}
