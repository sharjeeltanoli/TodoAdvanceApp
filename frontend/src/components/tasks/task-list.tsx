"use client";

import { useState, useEffect, useCallback } from "react";
import { TaskItem, TaskData } from "@/components/tasks/task-item";
import { EmptyState } from "@/components/tasks/empty-state";
import { TaskForm } from "@/components/tasks/task-form";
import { SearchInput } from "@/components/ui/search-input";
import { FilterBar } from "@/components/ui/filter-bar";
import { SortSelect } from "@/components/ui/sort-select";
import { getTasks, getAvailableTags } from "@/app/dashboard/actions";

interface TaskListProps {
  tasks: TaskData[];
}

export function TaskList({ tasks: initialTasks }: TaskListProps) {
  const [tasks, setTasks] = useState<TaskData[]>(initialTasks);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [priorityFilter, setPriorityFilter] = useState("");
  const [tagFilter, setTagFilter] = useState("");
  const [sortBy, setSortBy] = useState("created_at");
  const [sortDir, setSortDir] = useState("desc");
  const [availableTags, setAvailableTags] = useState<string[]>([]);

  useEffect(() => {
    getAvailableTags().then(setAvailableTags).catch(() => {});
  }, []);

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
    getAvailableTags().then(setAvailableTags).catch(() => {});
  }

  return (
    <div className="space-y-4">
      <TaskForm onSuccess={handleTaskCreated} />

      {/* Search + Filter + Sort toolbar */}
      <div className="space-y-2">
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
            <TaskItem key={task.id} task={task} />
          ))}
        </div>
      )}
    </div>
  );
}
