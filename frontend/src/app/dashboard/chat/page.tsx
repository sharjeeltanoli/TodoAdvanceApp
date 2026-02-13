"use client";

import Script from "next/script";
import { ChatPanel } from "@/components/chat/chat-panel";

export default function ChatPage() {
  return (
    <div className="flex h-[calc(100vh-57px)] flex-col">
      <Script
        src="https://cdn.platform.openai.com/deployments/chatkit/chatkit.js"
        strategy="afterInteractive"
        onLoad={() => console.log("[ChatKit] CDN script loaded")}
        onError={(e) => console.error("[ChatKit] CDN script failed to load:", e)}
      />
      <ChatPanel />
    </div>
  );
}
