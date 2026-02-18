"use client";

import { useState, useEffect, useCallback } from "react";

interface Notification {
  id: string;
  type: string;
  title: string;
  body: string | null;
  task_id: string | null;
  read: boolean;
  created_at: string;
}

interface NotificationListProps {
  token?: string;
  isOpen: boolean;
  onClose: () => void;
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

function typeIcon(type: string): string {
  if (type === "reminder_overdue") return "!";
  if (type === "reminder_upcoming") return "~";
  return "i";
}

function typeColor(type: string): string {
  if (type === "reminder_overdue") return "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400";
  if (type === "reminder_upcoming") return "bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400";
  return "bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400";
}

export function NotificationList({ token, isOpen, onClose }: NotificationListProps) {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [loading, setLoading] = useState(false);

  const fetchNotifications = useCallback(async () => {
    if (!token) return;
    setLoading(true);
    try {
      const resp = await fetch(`${BACKEND_URL}/api/notifications?limit=20`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (resp.ok) {
        const data = await resp.json();
        setNotifications(data.notifications ?? []);
      }
    } catch {
      // Silently ignore
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => {
    if (isOpen) fetchNotifications();
  }, [isOpen, fetchNotifications]);

  async function markAsRead(id: string) {
    if (!token) return;
    try {
      await fetch(`${BACKEND_URL}/api/notifications/${id}/read`, {
        method: "PATCH",
        headers: { Authorization: `Bearer ${token}` },
      });
      setNotifications((prev) =>
        prev.map((n) => (n.id === id ? { ...n, read: true } : n))
      );
    } catch {
      // Silently ignore
    }
  }

  async function markAllRead() {
    if (!token) return;
    try {
      await fetch(`${BACKEND_URL}/api/notifications/read-all`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
      });
      setNotifications((prev) => prev.map((n) => ({ ...n, read: true })));
    } catch {
      // Silently ignore
    }
  }

  if (!isOpen) return null;

  return (
    <>
      {/* Backdrop */}
      <div className="fixed inset-0 z-40" onClick={onClose} />

      {/* Dropdown */}
      <div className="absolute right-0 top-full z-50 mt-2 w-80 rounded-lg border border-zinc-200 bg-white shadow-lg dark:border-zinc-700 dark:bg-zinc-800">
        <div className="flex items-center justify-between border-b border-zinc-200 px-4 py-3 dark:border-zinc-700">
          <h3 className="text-sm font-semibold text-zinc-900 dark:text-zinc-100">
            Notifications
          </h3>
          {notifications.some((n) => !n.read) && (
            <button
              onClick={markAllRead}
              className="text-xs text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300"
            >
              Mark all read
            </button>
          )}
        </div>

        <div className="max-h-80 overflow-y-auto">
          {loading ? (
            <div className="p-4 text-center text-sm text-zinc-400">
              Loading...
            </div>
          ) : notifications.length === 0 ? (
            <div className="p-4 text-center text-sm text-zinc-400">
              No notifications
            </div>
          ) : (
            notifications.map((notif) => (
              <button
                key={notif.id}
                onClick={() => {
                  if (!notif.read) markAsRead(notif.id);
                }}
                className={`flex w-full gap-3 border-b border-zinc-100 px-4 py-3 text-left transition-colors last:border-0 hover:bg-zinc-50 dark:border-zinc-700/50 dark:hover:bg-zinc-700/50 ${
                  !notif.read ? "bg-blue-50/50 dark:bg-blue-900/10" : ""
                }`}
              >
                <span
                  className={`mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-xs font-bold ${typeColor(notif.type)}`}
                >
                  {typeIcon(notif.type)}
                </span>
                <div className="min-w-0 flex-1">
                  <div className="flex items-center justify-between gap-2">
                    <p
                      className={`truncate text-sm ${
                        !notif.read
                          ? "font-semibold text-zinc-900 dark:text-zinc-100"
                          : "text-zinc-600 dark:text-zinc-300"
                      }`}
                    >
                      {notif.title}
                    </p>
                    <span className="shrink-0 text-[10px] text-zinc-400">
                      {formatRelativeTime(notif.created_at)}
                    </span>
                  </div>
                  {notif.body && (
                    <p className="mt-0.5 truncate text-xs text-zinc-500 dark:text-zinc-400">
                      {notif.body}
                    </p>
                  )}
                </div>
                {!notif.read && (
                  <span className="mt-2 h-2 w-2 shrink-0 rounded-full bg-blue-500" />
                )}
              </button>
            ))
          )}
        </div>
      </div>
    </>
  );
}
