"use server";

import { auth } from "@/lib/auth";
import { headers } from "next/headers";
import { api } from "@/lib/api";
import { revalidatePath } from "next/cache";

interface GetTasksParams {
  search?: string;
  status?: string;
  priority?: string;
  tag?: string;
  sort_by?: string;
  sort_dir?: string;
}

export async function getTasks(params?: GetTasksParams) {
  const session = await auth.api.getSession({ headers: await headers() });
  if (!session) throw new Error("Unauthorized");

  const query = new URLSearchParams();
  if (params?.search) query.set("search", params.search);
  if (params?.status) query.set("status", params.status);
  if (params?.priority) query.set("priority", params.priority);
  if (params?.tag) query.set("tag", params.tag);
  if (params?.sort_by) query.set("sort_by", params.sort_by);
  if (params?.sort_dir) query.set("sort_dir", params.sort_dir);

  const qs = query.toString();
  const path = `/api/todos${qs ? `?${qs}` : ""}`;
  return api.get(path, session.session.token);
}

export async function getAvailableTags() {
  const session = await auth.api.getSession({ headers: await headers() });
  if (!session) throw new Error("Unauthorized");
  return api.get("/api/todos/tags", session.session.token);
}

export async function createTask(formData: FormData) {
  const session = await auth.api.getSession({ headers: await headers() });
  if (!session) throw new Error("Unauthorized");

  const tagsRaw = formData.get("tags") as string;
  const tags = tagsRaw ? JSON.parse(tagsRaw) : [];
  const recurrenceRaw = formData.get("recurrence_pattern") as string;
  const recurrence = recurrenceRaw ? JSON.parse(recurrenceRaw) : null;
  const reminderRaw = formData.get("reminder_minutes") as string;

  const result = await api.post(
    "/api/todos",
    {
      title: formData.get("title") as string,
      description: (formData.get("description") as string) || null,
      priority: (formData.get("priority") as string) || "medium",
      tags,
      due_date: (formData.get("due_date") as string) || null,
      recurrence_pattern: recurrence,
      reminder_minutes: reminderRaw ? parseInt(reminderRaw) : null,
    },
    session.session.token
  );
  revalidatePath("/dashboard");
  return result;
}

export async function toggleComplete(taskId: string) {
  const session = await auth.api.getSession({ headers: await headers() });
  if (!session) throw new Error("Unauthorized");
  const result = await api.patch(
    `/api/todos/${taskId}/complete`,
    session.session.token
  );
  revalidatePath("/dashboard");
  return result;
}

export async function updateTask(
  taskId: string,
  data: {
    title?: string;
    description?: string;
    priority?: string;
    tags?: string[];
    due_date?: string | null;
    recurrence_pattern?: { frequency: string; interval: number; next_due: string } | null;
    reminder_minutes?: number | null;
  }
) {
  const session = await auth.api.getSession({ headers: await headers() });
  if (!session) throw new Error("Unauthorized");
  const result = await api.put(
    `/api/todos/${taskId}`,
    data,
    session.session.token
  );
  revalidatePath("/dashboard");
  return result;
}

export async function deleteTask(taskId: string) {
  const session = await auth.api.getSession({ headers: await headers() });
  if (!session) throw new Error("Unauthorized");
  await api.del(`/api/todos/${taskId}`, session.session.token);
  revalidatePath("/dashboard");
}

export async function getReminders() {
  const session = await auth.api.getSession({ headers: await headers() });
  if (!session) throw new Error("Unauthorized");
  return api.get("/api/todos/reminders", session.session.token);
}

export async function snoozeTask(taskId: string) {
  const session = await auth.api.getSession({ headers: await headers() });
  if (!session) throw new Error("Unauthorized");
  const result = await api.post(`/api/todos/${taskId}/snooze`, {}, session.session.token);
  revalidatePath("/dashboard");
  return result;
}
