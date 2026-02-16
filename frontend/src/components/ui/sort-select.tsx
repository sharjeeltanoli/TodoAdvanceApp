interface SortSelectProps {
  sortBy: string;
  sortDir: string;
  onSortByChange: (v: string) => void;
  onSortDirChange: (v: string) => void;
}

export function SortSelect({
  sortBy,
  sortDir,
  onSortByChange,
  onSortDirChange,
}: SortSelectProps) {
  return (
    <div className="flex items-center gap-2">
      <select
        value={sortBy}
        onChange={(e) => onSortByChange(e.target.value)}
        className="rounded-md border border-zinc-300 bg-white px-2 py-1.5 text-sm text-zinc-700 focus:border-zinc-500 focus:outline-none dark:border-zinc-600 dark:bg-zinc-800 dark:text-zinc-300"
      >
        <option value="created_at">Created</option>
        <option value="due_date">Due Date</option>
        <option value="priority">Priority</option>
      </select>
      <button
        type="button"
        onClick={() => onSortDirChange(sortDir === "asc" ? "desc" : "asc")}
        className="rounded-md border border-zinc-300 px-2 py-1.5 text-sm text-zinc-500 hover:text-zinc-700 dark:border-zinc-600 dark:text-zinc-400 dark:hover:text-zinc-200"
        title={sortDir === "asc" ? "Ascending" : "Descending"}
      >
        {sortDir === "asc" ? "\u2191" : "\u2193"}
      </button>
    </div>
  );
}
