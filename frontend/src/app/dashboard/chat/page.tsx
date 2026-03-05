"use client";

import { ChatPanel } from "@/components/chat/chat-panel";

export default function ChatPage() {
  return (
    <div className="flex h-[calc(100vh-57px)] flex-col">
      <ChatPanel />
    </div>
  );
}
