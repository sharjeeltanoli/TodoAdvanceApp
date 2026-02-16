"use client";

interface FilterBarProps {
  status: string;
  priority: string;
  tag: string;
  availableTags: string[];
  onStatusChange: (v: string) => void;
  onPriorityChange: (v: string) => void;
  onTagChange: (v: string) => void;
  onClear: () => void;
}

export function FilterBar({
  status,
  priority,
  tag,
  availableTags,
  onStatusChange,
  onPriorityChange,
  onTagChange,
  onClear,
}: FilterBarProps) {
  const activeCount = [status, priority, tag].filter(Boolean).length;

  const selectClass =
    "rounded-md border border-zinc-300 bg-white px-2 py-1.5 text-sm text-zinc-700 focus:border-zinc-500 focus:outline-none dark:border-zinc-600 dark:bg-zinc-800 dark:text-zinc-300";

  return (
    <div className="flex flex-wrap items-center gap-2">
      <select value={status} onChange={(e) => onStatusChange(e.target.value)} className={selectClass}>
        <option value="">All Status</option>
        <option value="pending">Pending</option>
        <option value="completed">Completed</option>
      </select>

      <select value={priority} onChange={(e) => onPriorityChange(e.target.value)} className={selectClass}>
        <option value="">All Priority</option>
        <option value="high">High</option>
        <option value="medium">Medium</option>
        <option value="low">Low</option>
      </select>

      <select value={tag} onChange={(e) => onTagChange(e.target.value)} className={selectClass}>
        <option value="">All Tags</option>
        {availableTags.map((t) => (
          <option key={t} value={t}>
            {t}
          </option>
        ))}
      </select>

      {activeCount > 0 && (
        <button
          type="button"
          onClick={onClear}
          className="text-sm text-zinc-500 hover:text-zinc-700 dark:text-zinc-400 dark:hover:text-zinc-200"
        >
          Clear filters ({activeCount})
        </button>
      )}
    </div>
  );
}
