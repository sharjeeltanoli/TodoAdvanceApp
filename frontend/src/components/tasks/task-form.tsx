"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { TagInput } from "@/components/ui/tag-input";
import { DatePicker } from "@/components/ui/date-picker";
import { createTask, updateTask, getAvailableTags } from "@/app/dashboard/actions";

interface TaskFormProps {
  mode?: "create" | "edit";
  taskId?: string;
  initialTitle?: string;
  initialDescription?: string;
  initialPriority?: string;
  initialTags?: string[];
  initialDueDate?: string | null;
  initialRecurrence?: { frequency: string; interval: number; next_due: string } | null;
  initialReminderMinutes?: number | null;
  onSuccess?: () => void;
  onCancel?: () => void;
}

export function TaskForm({
  mode = "create",
  taskId,
  initialTitle = "",
  initialDescription = "",
  initialPriority = "medium",
  initialTags = [],
  initialDueDate = null,
  initialRecurrence = null,
  initialReminderMinutes = null,
  onSuccess,
  onCancel,
}: TaskFormProps) {
  const [title, setTitle] = useState(initialTitle);
  const [description, setDescription] = useState(initialDescription);
  const [priority, setPriority] = useState(initialPriority);
  const [tags, setTags] = useState<string[]>(initialTags);
  const [dueDate, setDueDate] = useState(
    initialDueDate ? initialDueDate.slice(0, 10) : ""
  );
  const [recurrenceEnabled, setRecurrenceEnabled] = useState(!!initialRecurrence);
  const [recurrenceFrequency, setRecurrenceFrequency] = useState(
    initialRecurrence?.frequency || "daily"
  );
  const [reminderMinutes, setReminderMinutes] = useState<string>(
    initialReminderMinutes ? String(initialReminderMinutes) : ""
  );
  const [tagSuggestions, setTagSuggestions] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    getAvailableTags()
      .then(setTagSuggestions)
      .catch(() => {});
  }, []);

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
      const dueDateValue = dueDate
        ? new Date(dueDate + "T00:00:00Z").toISOString()
        : null;
      const recurrencePattern = recurrenceEnabled && dueDate
        ? { frequency: recurrenceFrequency, interval: 1, next_due: dueDateValue! }
        : null;
      const reminderValue = reminderMinutes ? parseInt(reminderMinutes) : null;

      if (mode === "edit" && taskId) {
        await updateTask(taskId, {
          title: trimmedTitle,
          description: description.trim() || undefined,
          priority,
          tags,
          due_date: dueDateValue,
          recurrence_pattern: recurrencePattern,
          reminder_minutes: reminderValue,
        });
      } else {
        const formData = new FormData();
        formData.set("title", trimmedTitle);
        if (description.trim()) formData.set("description", description.trim());
        formData.set("priority", priority);
        formData.set("tags", JSON.stringify(tags));
        if (dueDateValue) formData.set("due_date", dueDateValue);
        if (recurrencePattern)
          formData.set("recurrence_pattern", JSON.stringify(recurrencePattern));
        if (reminderValue) formData.set("reminder_minutes", String(reminderValue));
        await createTask(formData);
        setTitle("");
        setDescription("");
        setPriority("medium");
        setTags([]);
        setDueDate("");
        setRecurrenceEnabled(false);
        setReminderMinutes("");
      }
      onSuccess?.();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save task");
    } finally {
      setLoading(false);
    }
  }

  const priorityOptions = [
    { value: "high", label: "High", color: "bg-red-500" },
    { value: "medium", label: "Med", color: "bg-yellow-500" },
    { value: "low", label: "Low", color: "bg-green-500" },
  ];

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
          style={{ resize: "vertical" }}
        />
      </div>

      {/* Priority selector */}
      <div className="flex flex-col gap-1.5">
        <label className="text-sm font-medium text-zinc-700 dark:text-zinc-300">
          Priority
        </label>
        <div className="flex gap-1">
          {priorityOptions.map((opt) => (
            <button
              key={opt.value}
              type="button"
              onClick={() => setPriority(opt.value)}
              className={`flex items-center gap-1.5 rounded-md px-3 py-1.5 text-sm font-medium transition-colors ${
                priority === opt.value
                  ? "bg-zinc-900 text-white dark:bg-zinc-100 dark:text-zinc-900"
                  : "bg-zinc-100 text-zinc-600 hover:bg-zinc-200 dark:bg-zinc-800 dark:text-zinc-400 dark:hover:bg-zinc-700"
              }`}
            >
              <span className={`h-2 w-2 rounded-full ${opt.color}`} />
              {opt.label}
            </button>
          ))}
        </div>
      </div>

      {/* Tags */}
      <TagInput value={tags} onChange={setTags} suggestions={tagSuggestions} />

      {/* Due date */}
      <DatePicker value={dueDate} onChange={setDueDate} />

      {/* Reminder (only when due date is set) */}
      {dueDate && (
        <div className="flex flex-col gap-1.5">
          <label className="text-sm font-medium text-zinc-700 dark:text-zinc-300">
            Reminder
          </label>
          <select
            value={reminderMinutes}
            onChange={(e) => setReminderMinutes(e.target.value)}
            className="rounded-md border border-zinc-300 bg-white px-3 py-2 text-sm text-zinc-900 focus:border-zinc-500 focus:outline-none dark:border-zinc-600 dark:bg-zinc-800 dark:text-zinc-100"
          >
            <option value="">No reminder</option>
            <option value="15">15 min before</option>
            <option value="60">1 hour before</option>
            <option value="1440">1 day before</option>
          </select>
        </div>
      )}

      {/* Recurrence (only when due date is set) */}
      {dueDate && (
        <div className="flex flex-col gap-1.5">
          <label className="flex items-center gap-2 text-sm font-medium text-zinc-700 dark:text-zinc-300">
            <input
              type="checkbox"
              checked={recurrenceEnabled}
              onChange={(e) => setRecurrenceEnabled(e.target.checked)}
              className="h-4 w-4 rounded border-zinc-300"
            />
            Recurring task
          </label>
          {recurrenceEnabled && (
            <select
              value={recurrenceFrequency}
              onChange={(e) => setRecurrenceFrequency(e.target.value)}
              className="rounded-md border border-zinc-300 bg-white px-3 py-2 text-sm text-zinc-900 focus:border-zinc-500 focus:outline-none dark:border-zinc-600 dark:bg-zinc-800 dark:text-zinc-100"
            >
              <option value="daily">Daily</option>
              <option value="weekly">Weekly</option>
              <option value="monthly">Monthly</option>
            </select>
          )}
        </div>
      )}

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
