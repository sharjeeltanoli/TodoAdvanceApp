interface PriorityBadgeProps {
  priority: "high" | "medium" | "low";
}

const styles: Record<string, string> = {
  high: "bg-red-500 text-white",
  medium: "bg-amber-500 text-white",
  low: "bg-emerald-500 text-white",
};

export function PriorityBadge({ priority }: PriorityBadgeProps) {
  return (
    <span
      className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${styles[priority]}`}
    >
      {priority}
    </span>
  );
}
