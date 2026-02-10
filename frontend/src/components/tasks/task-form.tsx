"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { createTask, updateTask } from "@/app/dashboard/actions";

interface TaskFormProps {
  mode?: "create" | "edit";
  taskId?: string;
  initialTitle?: string;
  initialDescription?: string;
  onSuccess?: () => void;
  onCancel?: () => void;
}

export function TaskForm({
  mode = "create",
  taskId,
  initialTitle = "",
  initialDescription = "",
  onSuccess,
  onCancel,
}: TaskFormProps) {
  const [title, setTitle] = useState(initialTitle);
  const [description, setDescription] = useState(initialDescription);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);

    const trimmedTitle = title.trim();
    if (!trimmedTitle) {
      setError("Title is required");
      return;
    }

    setLoading(true);
    try {
      if (mode === "edit" && taskId) {
        await updateTask(taskId, {
          title: trimmedTitle,
          description: description.trim() || undefined,
        });
      } else {
        const formData = new FormData();
        formData.set("title", trimmedTitle);
        if (description.trim()) {
          formData.set("description", description.trim());
        }
        await createTask(formData);
        setTitle("");
        setDescription("");
      }
      onSuccess?.();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save task");
    } finally {
      setLoading(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-3">
      <Input
        label="Title"
        placeholder="What needs to be done?"
        value={title}
        onChange={(e) => setTitle(e.target.value)}
        maxLength={255}
        required
        error={error ?? undefined}
      />
      <div className="flex flex-col gap-1.5">
        <label
          htmlFor={`description-${taskId || "new"}`}
          className="text-sm font-medium text-zinc-700 dark:text-zinc-300"
        >
          Description
        </label>
        <textarea
          id={`description-${taskId || "new"}`}
          placeholder="Add details (optional)"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          maxLength={2000}
          rows={2}
          className="rounded-md border border-zinc-300 bg-white px-3 py-2 text-sm text-zinc-900 placeholder:text-zinc-400 focus:border-zinc-500 focus:outline-none focus:ring-1 focus:ring-zinc-500 dark:border-zinc-600 dark:bg-zinc-800 dark:text-zinc-100 dark:placeholder:text-zinc-500"
        />
      </div>
      <div className="flex gap-2">
        <Button type="submit" disabled={loading}>
          {loading
            ? mode === "edit"
              ? "Saving..."
              : "Adding..."
            : mode === "edit"
              ? "Save"
              : "Add Task"}
        </Button>
        {mode === "edit" && onCancel && (
          <Button type="button" variant="ghost" onClick={onCancel}>
            Cancel
          </Button>
        )}
      </div>
    </form>
  );
}
