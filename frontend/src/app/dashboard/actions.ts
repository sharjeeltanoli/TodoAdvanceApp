"use server";

import { auth } from "@/lib/auth";
import { headers } from "next/headers";
import { api } from "@/lib/api";
import { revalidatePath } from "next/cache";

export async function getTasks() {
  const session = await auth.api.getSession({ headers: await headers() });
  if (!session) throw new Error("Unauthorized");
  return api.get("/api/todos", session.session.token);
}

export async function createTask(formData: FormData) {
  const session = await auth.api.getSession({ headers: await headers() });
  if (!session) throw new Error("Unauthorized");
  const result = await api.post(
    "/api/todos",
    {
      title: formData.get("title") as string,
      description: (formData.get("description") as string) || null,
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
  data: { title?: string; description?: string }
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
