"use client";

import { ChatKit, useChatKit } from "@openai/chatkit-react";
import { useEffect, useState } from "react";
import { authClient } from "@/lib/auth-client";

const BACKEND_URL =
  process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

export function ChatPanel() {
  const [token, setToken] = useState<string | null>(null);
  const [authError, setAuthError] = useState<string | null>(null);

  useEffect(() => {
    authClient
      .getSession()
      .then((res) => {
        const t = res.data?.session?.token;
        if (t) {
          setToken(t);
        } else {
          console.error("[ChatPanel] No session token found:", res);
          setAuthError("Not authenticated — please log in again.");
        }
      })
      .catch((err) => {
        console.error("[ChatPanel] getSession failed:", err);
        setAuthError("Failed to load session.");
      });
  }, []);

  if (authError) {
    return (
      <div className="flex h-full items-center justify-center text-red-500">
        {authError}
      </div>
    );
  }

  if (!token) {
    return (
      <div className="flex h-full items-center justify-center text-zinc-500">
        Loading chat...
      </div>
    );
  }

  return <ChatPanelInner token={token} />;
}

function ChatPanelInner({ token }: { token: string }) {
  const [ready, setReady] = useState(false);

  const chatkit = useChatKit({
    api: {
      url: `${BACKEND_URL}/chatkit`,
      domainKey: "todo-app",
      fetch: (input, init) => {
        const headers = new Headers(init?.headers);
        headers.set("Authorization", `Bearer ${token}`);
        return fetch(input, { ...init, headers });
      },
    },
    theme: "light",
    history: {
      enabled: true,
      showDelete: true,
    },
    startScreen: {
      greeting: "How can I help with your tasks?",
      prompts: [
        {
          label: "Show my tasks",
          prompt: "Show all my tasks",
          icon: "check-circle",
        },
        {
          label: "Add a task",
          prompt: "Add a new task: ",
          icon: "plus",
        },
        {
          label: "Task summary",
          prompt: "Give me a summary of my tasks",
          icon: "chart",
        },
      ],
    },
    composer: {
      placeholder: "Ask me to manage your tasks...",
    },
    onReady: () => {
      console.log("[ChatKit] ready");
      setReady(true);
    },
    onError: ({ error }) => {
      console.error("[ChatKit] error:", error);
    },
  });

  return (
    <div className="relative h-full w-full">
      {!ready && (
        <div className="absolute inset-0 z-10 flex items-center justify-center bg-white text-zinc-500">
          Initializing chat...
        </div>
      )}
      <ChatKit control={chatkit.control} className="block h-full w-full" />
    </div>
  );
}
