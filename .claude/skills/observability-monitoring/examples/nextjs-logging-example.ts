/**
 * Next.js Structured Logging Example for hackathon-todo Frontend
 *
 * Demonstrates pino-based structured JSON logging for:
 * - Server components
 * - API routes
 * - Client-side error reporting
 *
 * Install:
 *   npm install pino pino-pretty
 */

// ============================================================
// File: lib/logger.ts — Server-side logger
// ============================================================

import pino from "pino";

const isProduction = process.env.NODE_ENV === "production";

/**
 * Server-side logger. JSON in production, pretty in development.
 * Import in server components, API routes, and middleware only.
 */
export const logger = pino({
  name: "hackathon-todo-frontend",
  level: process.env.LOG_LEVEL || "info",
  base: {
    app: "hackathon-todo-frontend",
    env: process.env.NODE_ENV || "development",
  },
  timestamp: pino.stdTimeFunctions.isoTime,
  transport: isProduction
    ? undefined
    : {
        target: "pino-pretty",
        options: {
          colorize: true,
          translateTime: "HH:MM:ss",
          ignore: "pid,hostname",
        },
      },
  // Redact sensitive fields automatically
  redact: {
    paths: [
      "req.headers.authorization",
      "req.headers.cookie",
      "password",
      "token",
      "*.password",
      "*.token",
    ],
    censor: "[REDACTED]",
  },
});

/**
 * Create a child logger with request context for API routes.
 */
export function createRequestLogger(context: {
  requestId?: string;
  userId?: string;
  path?: string;
  method?: string;
}) {
  return logger.child({
    requestId: context.requestId || crypto.randomUUID(),
    userId: context.userId || "anonymous",
    path: context.path,
    method: context.method,
  });
}

// ============================================================
// File: app/api/tasks/route.ts — API Route with logging
// ============================================================

import { NextRequest, NextResponse } from "next/server";
// import { createRequestLogger } from "@/lib/logger";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function GET(request: NextRequest) {
  const log = createRequestLogger({
    path: "/api/tasks",
    method: "GET",
    requestId: request.headers.get("x-request-id") || undefined,
  });

  log.info("Fetching tasks from backend");
  const start = performance.now();

  try {
    const response = await fetch(`${API_URL}/api/tasks`, {
      headers: {
        Authorization: request.headers.get("authorization") || "",
      },
    });

    const duration = Math.round(performance.now() - start);

    if (!response.ok) {
      log.warn(
        { status: response.status, duration_ms: duration },
        "Backend returned error",
      );
      return NextResponse.json(
        { error: "Failed to fetch tasks" },
        { status: response.status },
      );
    }

    const data = await response.json();
    log.info(
      { count: data.tasks?.length || 0, duration_ms: duration },
      "Tasks fetched successfully",
    );

    return NextResponse.json(data);
  } catch (error) {
    const duration = Math.round(performance.now() - start);
    log.error(
      { err: error, duration_ms: duration },
      "Failed to fetch tasks from backend",
    );
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 },
    );
  }
}

export async function POST(request: NextRequest) {
  const log = createRequestLogger({
    path: "/api/tasks",
    method: "POST",
    requestId: request.headers.get("x-request-id") || undefined,
  });

  try {
    const body = await request.json();
    log.info({ title: body.title }, "Creating task");

    const response = await fetch(`${API_URL}/api/tasks`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: request.headers.get("authorization") || "",
      },
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      log.warn({ status: response.status }, "Task creation failed at backend");
      return NextResponse.json(
        { error: "Failed to create task" },
        { status: response.status },
      );
    }

    const data = await response.json();
    log.info({ taskId: data.id }, "Task created successfully");
    return NextResponse.json(data, { status: 201 });
  } catch (error) {
    log.error({ err: error }, "Task creation failed");
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 },
    );
  }
}

// ============================================================
// File: app/api/logs/route.ts — Client log receiver
// ============================================================

// import { NextRequest, NextResponse } from "next/server";
// import { logger } from "@/lib/logger";

const clientLog = logger.child({ source: "client" });

export async function POST_logs(request: NextRequest) {
  try {
    const { logs } = await request.json();

    if (!Array.isArray(logs) || logs.length > 50) {
      return NextResponse.json({ error: "Invalid payload" }, { status: 400 });
    }

    for (const entry of logs) {
      const level = entry.level === "error" ? "error" : "warn";
      clientLog[level](
        {
          url: entry.url,
          error: entry.error,
          clientTimestamp: entry.timestamp,
          ...entry.context,
        },
        `[CLIENT] ${entry.message}`,
      );
    }

    return NextResponse.json({ received: logs.length });
  } catch {
    return NextResponse.json({ error: "Invalid payload" }, { status: 400 });
  }
}

// ============================================================
// File: lib/logger-client.ts — Client-side error logger
// ============================================================

type LogLevel = "error" | "warn";

interface ClientLogEntry {
  level: LogLevel;
  message: string;
  error?: string;
  context?: Record<string, unknown>;
  timestamp: string;
  url: string;
}

class ClientLogger {
  private queue: ClientLogEntry[] = [];
  private timer: ReturnType<typeof setTimeout> | null = null;

  error(message: string, error?: Error, context?: Record<string, unknown>) {
    this.enqueue("error", message, error, context);
  }

  warn(message: string, error?: Error, context?: Record<string, unknown>) {
    this.enqueue("warn", message, error, context);
  }

  private enqueue(
    level: LogLevel,
    message: string,
    error?: Error,
    context?: Record<string, unknown>,
  ) {
    if (process.env.NODE_ENV !== "production") {
      console[level](message, error, context);
    }

    this.queue.push({
      level,
      message,
      error: error?.stack || error?.message,
      context,
      timestamp: new Date().toISOString(),
      url: typeof window !== "undefined" ? window.location.href : "",
    });

    if (!this.timer) {
      this.timer = setTimeout(() => this.flush(), 5000);
    }
  }

  private async flush() {
    this.timer = null;
    if (this.queue.length === 0) return;

    const batch = this.queue.splice(0, 50);
    try {
      await fetch("/api/logs", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ logs: batch }),
      });
    } catch {
      // Re-queue failed entries (with cap)
      if (this.queue.length < 100) {
        this.queue.unshift(...batch);
      }
    }
  }
}

export const clientLogger = new ClientLogger();

// ============================================================
// Usage in React components:
//
// "use client";
// import { clientLogger } from "@/lib/logger-client";
//
// function TaskForm() {
//   const handleSubmit = async (formData: FormData) => {
//     try {
//       const res = await fetch("/api/tasks", {
//         method: "POST",
//         body: JSON.stringify({ title: formData.get("title") }),
//       });
//       if (!res.ok) throw new Error(`HTTP ${res.status}`);
//     } catch (error) {
//       clientLogger.error("Failed to create task", error as Error, {
//         title: formData.get("title"),
//       });
//     }
//   };
// }
// ============================================================

// Example server-side log output (JSON):
// {"level":30,"time":"2026-02-17T10:30:00.000Z","name":"hackathon-todo-frontend",
//  "app":"hackathon-todo-frontend","env":"production",
//  "requestId":"a1b2c3","path":"/api/tasks","method":"GET",
//  "count":5,"duration_ms":42,"msg":"Tasks fetched successfully"}
