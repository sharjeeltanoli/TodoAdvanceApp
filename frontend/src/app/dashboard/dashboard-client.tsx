"use client";

import { useEffect, useState } from "react";
import { authClient } from "@/lib/auth-client";
import { TaskList } from "@/components/tasks/task-list";
import { type TaskData } from "@/components/tasks/task-item";

interface DashboardClientProps {
  tasks: TaskData[];
}

export function DashboardClient({ tasks }: DashboardClientProps) {
  const [token, setToken] = useState<string | undefined>();

  useEffect(() => {
    authClient.getSession().then((res) => {
      const sessionToken = res.data?.session?.token;
      if (sessionToken) {
        setToken(sessionToken);
      }
    });
  }, []);

  return <TaskList tasks={tasks} authToken={token} />;
}
