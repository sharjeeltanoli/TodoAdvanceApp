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
  const [pendingTag, setPendingTag] = useState("");
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

    // Commit any tag still in the input field (user typed but didn't press Enter)
    let finalTags = [...tags];
    if (pendingTag.trim()) {
      const normalized = pendingTag.toLowerCase().trim();
      if (!finalTags.includes(normalized) && finalTags.length < 10) {
        finalTags.push(normalized);
      }
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
          tags: finalTags,
          due_date: dueDateValue,
          recurrence_pattern: recurrencePattern,
          reminder_minutes: reminderValue,
        });
      } else {
        const formData = new FormData();
        formData.set("title", trimmedTitle);
        if (description.trim()) formData.set("description", description.trim());
        formData.set("priority", priority);
        formData.set("tags", JSON.stringify(finalTags));
        if (dueDateValue) formData.set("due_date", dueDateValue);
        if (recurrencePattern)
          formData.set("recurrence_pattern", JSON.stringify(recurrencePattern));
        if (reminderValue) formData.set("reminder_minutes", String(reminderValue));
        await createTask(formData);
        setTitle("");
        setDescription("");
        setPriority("medium");
        setTags([]);
        setPendingTag("");
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
    { value: "high", label: "High", dot: "bg-red-500", active: "bg-red-500 text-white shadow-sm", inactive: "bg-slate-100 text-slate-600 hover:bg-red-50 hover:text-red-700" },
    { value: "medium", label: "Med", dot: "bg-amber-500", active: "bg-amber-500 text-white shadow-sm", inactive: "bg-slate-100 text-slate-600 hover:bg-amber-50 hover:text-amber-700" },
    { value: "low", label: "Low", dot: "bg-emerald-500", active: "bg-emerald-500 text-white shadow-sm", inactive: "bg-slate-100 text-slate-600 hover:bg-emerald-50 hover:text-emerald-700" },
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
          className="text-sm font-medium text-slate-700"
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
          className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 placeholder:text-slate-400 focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-300/50"
          style={{ resize: "vertical" }}
        />
      </div>

      {/* Priority selector */}
      <div className="flex flex-col gap-1.5">
        <label className="text-sm font-medium text-slate-700">
          Priority
        </label>
        <div className="flex gap-1.5">
          {priorityOptions.map((opt) => (
            <button
              key={opt.value}
              type="button"
              onClick={() => setPriority(opt.value)}
              className={`flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-sm font-medium transition-all ${
                priority === opt.value ? opt.active : opt.inactive
              }`}
            >
              <span className={`h-2 w-2 rounded-full ${priority === opt.value ? "bg-white/80" : opt.dot}`} />
              {opt.label}
            </button>
          ))}
        </div>
      </div>

      {/* Tags */}
      <TagInput value={tags} onChange={setTags} suggestions={tagSuggestions} onInputChange={setPendingTag} inputValue={pendingTag} />

      {/* Due date */}
      <DatePicker value={dueDate} onChange={setDueDate} />

      {/* Reminder (only when due date is set) */}
      {dueDate && (
        <div className="flex flex-col gap-1.5">
          <label className="text-sm font-medium text-slate-700">
            Reminder
          </label>
          <select
            value={reminderMinutes}
            onChange={(e) => setReminderMinutes(e.target.value)}
            className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-300/50"
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
          <label className="flex items-center gap-2 text-sm font-medium text-slate-700">
            <input
              type="checkbox"
              checked={recurrenceEnabled}
              onChange={(e) => setRecurrenceEnabled(e.target.checked)}
              className="h-4 w-4 rounded border-slate-300 accent-indigo-600"
            />
            Recurring task
          </label>
          {recurrenceEnabled && (
            <select
              value={recurrenceFrequency}
              onChange={(e) => setRecurrenceFrequency(e.target.value)}
              className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-300/50"
            >
              <option value="daily">Daily</option>
              <option value="weekly">Weekly</option>
              <option value="monthly">Monthly</option>
            </select>
          )}
        </div>
      )}

      <div className="flex gap-2 pt-1">
        <button
          type="submit"
          disabled={loading}
          className="rounded-lg bg-gradient-to-r from-indigo-600 to-purple-600 px-5 py-2 text-sm font-semibold text-white transition-all hover:from-indigo-500 hover:to-purple-500 hover:shadow-md disabled:cursor-not-allowed disabled:opacity-50"
        >
          {loading
            ? mode === "edit" ? "Saving…" : "Adding…"
            : mode === "edit" ? "Save Changes" : "Add Task"}
        </button>
        {mode === "edit" && onCancel && (
          <Button type="button" variant="ghost" onClick={onCancel}>
            Cancel
          </Button>
        )}
      </div>
    </form>
  );
}
