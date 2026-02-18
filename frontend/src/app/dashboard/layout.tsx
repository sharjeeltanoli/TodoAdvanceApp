"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { authClient } from "@/lib/auth-client";
import { Button } from "@/components/ui/button";
import { NotificationBell } from "@/components/notifications/notification-bell";
import { NotificationList } from "@/components/notifications/notification-list";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const pathname = usePathname();
  const [token, setToken] = useState<string | undefined>();
  const [notifOpen, setNotifOpen] = useState(false);

  useEffect(() => {
    authClient.getSession().then((res) => {
      const sessionToken = res.data?.session?.token;
      if (sessionToken) setToken(sessionToken);
    });
  }, []);

  async function handleLogout() {
    await authClient.signOut();
    router.push("/login");
    router.refresh();
  }

  const isChat = pathname === "/dashboard/chat";

  return (
    <div className="min-h-screen bg-zinc-50 dark:bg-zinc-950">
      <nav className="border-b border-zinc-200 bg-white dark:border-zinc-800 dark:bg-zinc-900">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-4 py-3">
          <div className="flex items-center gap-4">
            <h1 className="text-lg font-semibold text-zinc-900 dark:text-zinc-100">
              Todo App
            </h1>
            <div className="flex gap-1">
              <Link
                href="/dashboard"
                className={`rounded-md px-3 py-1.5 text-sm font-medium transition-colors ${
                  !isChat
                    ? "bg-zinc-100 text-zinc-900 dark:bg-zinc-800 dark:text-zinc-100"
                    : "text-zinc-500 hover:text-zinc-900 dark:text-zinc-400 dark:hover:text-zinc-100"
                }`}
              >
                Tasks
              </Link>
              <Link
                href="/dashboard/chat"
                className={`rounded-md px-3 py-1.5 text-sm font-medium transition-colors ${
                  isChat
                    ? "bg-zinc-100 text-zinc-900 dark:bg-zinc-800 dark:text-zinc-100"
                    : "text-zinc-500 hover:text-zinc-900 dark:text-zinc-400 dark:hover:text-zinc-100"
                }`}
              >
                Chat
              </Link>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <div className="relative">
              <NotificationBell
                token={token}
                onClick={() => setNotifOpen(!notifOpen)}
              />
              <NotificationList
                token={token}
                isOpen={notifOpen}
                onClose={() => setNotifOpen(false)}
              />
            </div>
            <Button variant="ghost" onClick={handleLogout}>
              Log Out
            </Button>
          </div>
        </div>
      </nav>
      <main className={isChat ? "" : "mx-auto max-w-3xl px-4 py-8"}>
        {children}
      </main>
    </div>
  );
}
