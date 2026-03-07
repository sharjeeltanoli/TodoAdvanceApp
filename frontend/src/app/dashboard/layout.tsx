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
  const isChat = pathname === "/dashboard/chat";
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

  return (
    <div className="flex h-screen flex-col bg-gradient-to-br from-slate-900 via-indigo-950 to-slate-900">
      <nav className="sticky top-0 z-20 border-b border-white/10 bg-slate-900/80 shadow-sm backdrop-blur-md">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-4 py-3">
          <div className="flex items-center gap-4">
            <h1 className="bg-gradient-to-r from-indigo-400 to-purple-400 bg-clip-text text-lg font-bold text-transparent">
              Todo App
            </h1>
            <div className="flex gap-1">
              <Link
                href="/dashboard"
                className={`rounded-lg px-3 py-1.5 text-sm font-medium transition-all ${
                  !isChat
                    ? "bg-white/15 text-white shadow-sm"
                    : "text-slate-400 hover:bg-white/10 hover:text-white"
                }`}
              >
                Tasks
              </Link>
              <Link
                href="/dashboard/chat"
                className={`rounded-lg px-3 py-1.5 text-sm font-medium transition-all ${
                  isChat
                    ? "bg-white/15 text-white shadow-sm"
                    : "text-slate-400 hover:bg-white/10 hover:text-white"
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
            <Button variant="ghost" onClick={handleLogout} className="text-slate-300 hover:bg-white/10 hover:text-white">
              Log Out
            </Button>
          </div>
        </div>
      </nav>
      <main className={`scrollbar-hide mx-auto w-full max-w-3xl flex-1 overflow-hidden px-4${isChat ? "" : " overflow-y-auto py-8"}`}>
        {children}
      </main>
    </div>
  );
}
