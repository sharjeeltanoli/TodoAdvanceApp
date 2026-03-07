"use client";

import { ChatPanel } from "@/components/chat/chat-panel";

export default function ChatPage() {
  return (
    <div className="flex h-full py-4">
      <div className="flex flex-1 flex-col overflow-hidden rounded-2xl border border-white/10 bg-white/70 shadow-sm backdrop-blur-sm">
        <ChatPanel />
      </div>
    </div>
  );
}
