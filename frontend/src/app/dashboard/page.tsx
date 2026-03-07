import { auth } from "@/lib/auth";
import { headers } from "next/headers";
import { redirect } from "next/navigation";
import { getTasks } from "./actions";
import { TaskList } from "@/components/tasks/task-list";
import { DashboardClient } from "./dashboard-client";

export default async function DashboardPage() {
  const session = await auth.api.getSession({
    headers: await headers(),
  });

  if (!session) {
    redirect("/login");
  }

  let tasks = [];
  let fetchError = false;
  try {
    tasks = await getTasks();
  } catch {
    fetchError = true;
  }

  return (
    <div>
      <p className="text-sm text-slate-500">
        Signed in as{" "}
        <span className="font-medium text-slate-800">
          {session.user.email}
        </span>
      </p>
      <div className="mt-6">
        {fetchError && (
          <div className="mb-4 rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-800 shadow-sm">
            Could not load tasks. The backend may be unavailable. Your new tasks
            will still be saved when the connection is restored.
          </div>
        )}
        <DashboardClient tasks={tasks} />
      </div>
    </div>
  );
}
