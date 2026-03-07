"use client";

import { useState, useEffect, useCallback, useRef, useMemo } from "react";
import { TaskItem, TaskData } from "@/components/tasks/task-item";
import { EmptyState } from "@/components/tasks/empty-state";
import { TaskForm } from "@/components/tasks/task-form";
import { SearchInput } from "@/components/ui/search-input";
import { FilterBar } from "@/components/ui/filter-bar";
import { SortSelect } from "@/components/ui/sort-select";
import { getTasks } from "@/app/dashboard/actions";
import { createTaskSSEConnection, SSEStatus, type SSEConnection } from "@/lib/sse";

interface TaskListProps {
  tasks: TaskData[];
  authToken?: string;
}

export function TaskList({ tasks: initialTasks, authToken }: TaskListProps) {
  const [tasks, setTasks] = useState<TaskData[]>(initialTasks);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [priorityFilter, setPriorityFilter] = useState("");
  const [tagFilter, setTagFilter] = useState("");
  const [sortBy, setSortBy] = useState("created_at");
  const [sortDir, setSortDir] = useState("desc");
  const [sseStatus, setSSEStatus] = useState<SSEStatus>("disconnected");
  const sseRef = useRef<SSEConnection | null>(null);

  // Derive available tags from the current task list — always in sync, no extra API call
  const availableTags = useMemo(
    () => Array.from(new Set(tasks.flatMap((t) => t.tags ?? []))).sort(),
    [tasks]
  );

  // SSE connection for real-time task updates
  useEffect(() => {
    if (!authToken) return;

    const connection = createTaskSSEConnection(authToken);
    sseRef.current = connection;

    connection.onStatusChange(setSSEStatus);
    connection.onEvent((event) => {
      // Refetch tasks when any change event arrives (availableTags derived from tasks)
      fetchTasks();
    });

    return () => {
      connection.close();
      sseRef.current = null;
    };
  }, [authToken]); // eslint-disable-line react-hooks/exhaustive-deps

  const hasFilters = search || statusFilter || priorityFilter || tagFilter || sortBy !== "created_at";

  const fetchTasks = useCallback(async () => {
    try {
      const result = await getTasks({
        search: search || undefined,
        status: statusFilter || undefined,
        priority: priorityFilter || undefined,
        tag: tagFilter || undefined,
        sort_by: sortBy,
        sort_dir: sortDir,
      });
      setTasks(result);
    } catch {
      // Keep current tasks on error
    }
  }, [search, statusFilter, priorityFilter, tagFilter, sortBy, sortDir]);

  useEffect(() => {
    if (hasFilters) {
      fetchTasks();
    } else {
      setTasks(initialTasks);
    }
  }, [fetchTasks, hasFilters, initialTasks]);

  function handleClearFilters() {
    setSearch("");
    setStatusFilter("");
    setPriorityFilter("");
    setTagFilter("");
    setSortBy("created_at");
    setSortDir("desc");
  }

  function handleTaskCreated() {
    fetchTasks();
  }

  return (
    <div className="space-y-5">
      {/* Add task card */}
      <div className="rounded-2xl border border-indigo-100 bg-white/70 p-5 shadow-sm backdrop-blur-sm">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-sm font-semibold uppercase tracking-wider text-indigo-600">
            Add New Task
          </h2>
          {authToken && sseStatus !== "disconnected" && (
            <div className="flex items-center gap-1.5 text-xs text-slate-400">
              <span
                className={`inline-block h-2 w-2 rounded-full ${
                  sseStatus === "connected"
                    ? "bg-emerald-500"
                    : "bg-amber-400 animate-pulse"
                }`}
              />
              {sseStatus === "connected" ? "Live" : sseStatus === "reconnecting" ? "Reconnecting…" : "Connecting…"}
            </div>
          )}
        </div>
        <TaskForm onSuccess={handleTaskCreated} />
      </div>

      {/* Search + Filter + Sort toolbar */}
      <div className="rounded-xl border border-indigo-100 bg-white/70 p-3 shadow-sm backdrop-blur-sm space-y-2">
        <SearchInput value={search} onChange={setSearch} />
        <div className="flex flex-wrap items-center justify-between gap-2">
          <FilterBar
            status={statusFilter}
            priority={priorityFilter}
            tag={tagFilter}
            availableTags={availableTags}
            onStatusChange={setStatusFilter}
            onPriorityChange={setPriorityFilter}
            onTagChange={setTagFilter}
            onClear={handleClearFilters}
          />
          <SortSelect
            sortBy={sortBy}
            sortDir={sortDir}
            onSortByChange={setSortBy}
            onSortDirChange={setSortDir}
          />
        </div>
      </div>

      {tasks.length === 0 ? (
        <EmptyState />
      ) : (
        <div className="space-y-2">
          {tasks.map((task) => (
            <TaskItem key={task.id} task={task} authToken={authToken} />
          ))}
        </div>
      )}
    </div>
  );
}
