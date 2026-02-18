"use client";

import { useState, useEffect, useCallback } from "react";

interface TaskHistoryEvent {
  id: string;
  event_type: string;
  timestamp: string;
  changed_fields: Record<string, { old: unknown; new: unknown }> | null;
  data: Record<string, unknown>;
  event_source: string;
}

interface TaskHistoryProps {
  taskId: string;
  token?: string;
  isOpen: boolean;
}

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "";

function formatRelativeTime(dateStr: string): string {
  const date = new Date(dateStr);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMin = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMin / 60);
  const diffDays = Math.floor(diffHours / 24);

  if (diffMin < 1) return "just now";
  if (diffMin < 60) return `${diffMin}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  return `${diffDays}d ago`;
}

function eventLabel(type: string): string {
  switch (type) {
    case "created":
      return "Created";
    case "updated":
      return "Updated";
    case "completed":
      return "Completed";
    case "deleted":
      return "Deleted";
    default:
      return type;
  }
}

function eventColor(type: string): string {
  switch (type) {
    case "created":
      return "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400";
    case "updated":
      return "bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400";
    case "completed":
      return "bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400";
    case "deleted":
      return "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400";
    default:
      return "bg-zinc-100 text-zinc-700 dark:bg-zinc-800 dark:text-zinc-400";
  }
}

function formatFieldValue(value: unknown): string {
  if (value === null || value === undefined) return "none";
  if (typeof value === "boolean") return value ? "yes" : "no";
  if (Array.isArray(value)) return value.join(", ") || "none";
  return String(value);
}

export function TaskHistory({ taskId, token, isOpen }: TaskHistoryProps) {
  const [events, setEvents] = useState<TaskHistoryEvent[]>([]);
  const [loading, setLoading] = useState(false);

  const fetchHistory = useCallback(async () => {
    if (!token) return;
    setLoading(true);
    try {
      const resp = await fetch(
        `${BACKEND_URL}/api/todos/${taskId}/history?limit=20`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      if (resp.ok) {
        const data = await resp.json();
        setEvents(data.events ?? []);
      }
    } catch {
      // Silently ignore
    } finally {
      setLoading(false);
    }
  }, [taskId, token]);

  useEffect(() => {
    if (isOpen) fetchHistory();
  }, [isOpen, fetchHistory]);

  if (!isOpen) return null;

  return (
    <div className="mt-2 rounded-md border border-zinc-200 bg-zinc-50 p-3 dark:border-zinc-700 dark:bg-zinc-800/50">
      <h4 className="mb-2 text-xs font-semibold uppercase tracking-wide text-zinc-500 dark:text-zinc-400">
        History
      </h4>

      {loading ? (
        <p className="text-sm text-zinc-400">Loading...</p>
      ) : events.length === 0 ? (
        <p className="text-sm text-zinc-400">No history available</p>
      ) : (
        <div className="space-y-2">
          {events.map((evt) => (
            <div key={evt.id} className="flex items-start gap-2">
              <span
                className={`mt-0.5 shrink-0 rounded px-1.5 py-0.5 text-[10px] font-semibold ${eventColor(evt.event_type)}`}
              >
                {eventLabel(evt.event_type)}
              </span>
              <div className="min-w-0 flex-1">
                {evt.changed_fields &&
                  Object.keys(evt.changed_fields).length > 0 && (
                    <div className="text-xs text-zinc-600 dark:text-zinc-300">
                      {Object.entries(evt.changed_fields).map(
                        ([field, change]) => (
                          <span key={field} className="mr-2">
                            <span className="font-medium">{field}</span>:{" "}
                            <span className="text-zinc-400 line-through">
                              {formatFieldValue(change.old)}
                            </span>{" "}
                            &rarr; {formatFieldValue(change.new)}
                          </span>
                        )
                      )}
                    </div>
                  )}
              </div>
              <span className="shrink-0 text-[10px] text-zinc-400">
                {formatRelativeTime(evt.timestamp)}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
