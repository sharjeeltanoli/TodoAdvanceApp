export function EmptyState() {
  return (
    <div className="flex flex-col items-center justify-center rounded-lg border border-dashed border-zinc-300 py-12 dark:border-zinc-700">
      <p className="text-lg font-medium text-zinc-600 dark:text-zinc-400">
        No tasks yet
      </p>
      <p className="mt-1 text-sm text-zinc-500 dark:text-zinc-500">
        Create your first task to get started!
      </p>
    </div>
  );
}
