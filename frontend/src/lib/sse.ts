/**
 * SSE client library for real-time task updates.
 *
 * Connects to /api/stream/tasks with Bearer auth, parses SSE events,
 * and auto-reconnects with exponential backoff on disconnect.
 */

export interface TaskSSEEvent {
  change_type: "created" | "updated" | "deleted" | "completed";
  task_id: string;
  user_id: string;
  changed_fields: string[];
  timestamp: string;
}

export interface SSEConnection {
  onEvent: (callback: (event: TaskSSEEvent) => void) => void;
  onStatusChange: (callback: (status: SSEStatus) => void) => void;
  close: () => void;
}

export type SSEStatus = "connecting" | "connected" | "disconnected" | "reconnecting";

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "";
const MAX_RETRIES = 10;
const BASE_DELAY = 1000;
const MAX_DELAY = 30000;

export function createTaskSSEConnection(token: string): SSEConnection {
  let eventSource: EventSource | null = null;
  let eventCallback: ((event: TaskSSEEvent) => void) | null = null;
  let statusCallback: ((status: SSEStatus) => void) | null = null;
  let retryCount = 0;
  let retryTimer: ReturnType<typeof setTimeout> | null = null;
  let closed = false;

  function setStatus(status: SSEStatus) {
    statusCallback?.(status);
  }

  function connect() {
    if (closed) return;

    setStatus(retryCount === 0 ? "connecting" : "reconnecting");

    // EventSource doesn't support custom headers, so we pass token as query param
    // The SSE gateway will need to accept token from query param or we use a proxy
    const url = `${BACKEND_URL}/api/stream/tasks?token=${encodeURIComponent(token)}`;

    eventSource = new EventSource(url);

    eventSource.onopen = () => {
      retryCount = 0;
      setStatus("connected");
    };

    eventSource.addEventListener("sync.task-changed", (e: MessageEvent) => {
      try {
        const data: TaskSSEEvent = JSON.parse(e.data);
        eventCallback?.(data);
      } catch {
        // Ignore malformed events
      }
    });

    eventSource.onerror = () => {
      eventSource?.close();
      eventSource = null;

      if (closed) return;

      setStatus("disconnected");

      // Auto-reconnect with exponential backoff
      if (retryCount < MAX_RETRIES) {
        const delay = Math.min(BASE_DELAY * Math.pow(2, retryCount), MAX_DELAY);
        retryCount++;
        retryTimer = setTimeout(connect, delay);
      }
    };
  }

  connect();

  return {
    onEvent(callback) {
      eventCallback = callback;
    },
    onStatusChange(callback) {
      statusCallback = callback;
    },
    close() {
      closed = true;
      if (retryTimer) clearTimeout(retryTimer);
      eventSource?.close();
      eventSource = null;
    },
  };
}
