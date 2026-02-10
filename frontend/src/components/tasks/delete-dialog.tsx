"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { deleteTask } from "@/app/dashboard/actions";

interface DeleteDialogProps {
  taskId: string;
  taskTitle: string;
  onClose: () => void;
  onDeleted: () => void;
}

export function DeleteDialog({
  taskId,
  taskTitle,
  onClose,
  onDeleted,
}: DeleteDialogProps) {
  const [loading, setLoading] = useState(false);

  async function handleDelete() {
    setLoading(true);
    try {
      await deleteTask(taskId);
      onDeleted();
    } catch {
      setLoading(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="mx-4 w-full max-w-sm rounded-lg bg-white p-6 shadow-lg dark:bg-zinc-900">
        <h2 className="text-lg font-semibold text-zinc-900 dark:text-zinc-100">
          Delete task?
        </h2>
        <p className="mt-2 text-sm text-zinc-500 dark:text-zinc-400">
          Are you sure you want to delete &quot;{taskTitle}&quot;? This action
          cannot be undone.
        </p>
        <div className="mt-4 flex justify-end gap-2">
          <Button variant="ghost" onClick={onClose} disabled={loading}>
            Cancel
          </Button>
          <Button variant="danger" onClick={handleDelete} disabled={loading}>
            {loading ? "Deleting..." : "Delete"}
          </Button>
        </div>
      </div>
    </div>
  );
}
