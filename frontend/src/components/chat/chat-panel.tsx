"use client";

import { useEffect, useRef, useState } from "react";
import { authClient } from "@/lib/auth-client";

// NEXT_PUBLIC_BACKEND_URL must be set on Vercel to the Render backend URL.
// Falls back to localhost for local dev.
const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

interface Message {
  role: "user" | "assistant";
  content: string;
}

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
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [conversationId, setConversationId] = useState<string | undefined>();
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  async function sendMessage() {
    const text = input.trim();
    if (!text || loading) return;

    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: text }]);
    setLoading(true);

    try {
      // Send last 10 messages as history so the AI has multi-turn context
      const history = messages.slice(-10).map((m) => ({
        role: m.role,
        content: m.content,
      }));

      const res = await fetch(`${BACKEND_URL}/api/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ message: text, conversation_id: conversationId, history }),
      });

      if (!res.ok) {
        const detail = await res.text();
        throw new Error(`${res.status}: ${detail}`);
      }

      const data = await res.json();
      setConversationId(data.conversation_id);
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: data.response },
      ]);
    } catch (err) {
      console.error("[ChatPanel] send error:", err);
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: "Sorry, I ran into an error. Please try again.",
        },
      ]);
    } finally {
      setLoading(false);
    }
  }

  const STARTER_PROMPTS = [
    "Show all my tasks",
    "Add a new task: ",
    "Give me a summary of my tasks",
  ];

  return (
    <div className="flex h-full flex-col">
      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full gap-5 text-center">
            <div>
              <p className="text-xl font-bold bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent">
                How can I help with your tasks?
              </p>
              <p className="mt-1 text-sm text-slate-400">
                Ask me to create, list, complete, or delete tasks
              </p>
            </div>
            <div className="flex flex-wrap gap-2 justify-center">
              {STARTER_PROMPTS.map((p) => (
                <button
                  key={p}
                  onClick={() => setInput(p)}
                  className="rounded-full border border-indigo-200 bg-indigo-50 px-4 py-1.5 text-sm font-medium text-indigo-700 transition-all hover:bg-indigo-100 hover:shadow-sm"
                >
                  {p}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg, i) => (
          <div
            key={i}
            className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
          >
            <div
              className={`max-w-[80%] rounded-2xl px-4 py-2 text-sm whitespace-pre-wrap ${
                msg.role === "user"
                  ? "bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-br-sm shadow-sm"
                  : "bg-white border border-slate-100 text-slate-800 rounded-bl-sm shadow-sm"
              }`}
            >
              {msg.content}
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex justify-start">
            <div className="bg-white border border-slate-100 text-slate-400 rounded-2xl rounded-bl-sm px-4 py-2 text-sm shadow-sm">
              <span className="animate-pulse">Thinking…</span>
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="border-t border-indigo-100 bg-white/60 p-4 backdrop-blur-sm">
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
              }
            }}
            placeholder="Ask me to manage your tasks…"
            disabled={loading}
            className="flex-1 rounded-xl border border-indigo-200 px-4 py-2 text-sm focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-300/50 disabled:opacity-50 bg-white"
          />
          <button
            onClick={sendMessage}
            disabled={loading || !input.trim()}
            className="rounded-xl bg-gradient-to-r from-indigo-600 to-purple-600 px-5 py-2 text-sm font-semibold text-white transition-all hover:from-indigo-500 hover:to-purple-500 hover:shadow-md disabled:opacity-40 disabled:cursor-not-allowed"
          >
            Send
          </button>
        </div>
      </div>
    </div>
  );
}
