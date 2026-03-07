import Link from "next/link";
import { LoginForm } from "@/components/auth/login-form";

const FEATURES = [
  { icon: "✨", label: "AI Chat Assistant", detail: "Manage tasks in plain English" },
  { icon: "🎯", label: "Smart Priorities", detail: "High, medium, and low task tiers" },
  { icon: "🏷️", label: "Tags & Filters", detail: "Organise tasks exactly your way" },
  { icon: "📅", label: "Due Dates & Reminders", detail: "Never miss a deadline" },
  { icon: "🔄", label: "Real-time Sync", detail: "Updates across all devices instantly" },
  { icon: "🔍", label: "Advanced Search", detail: "Find any task in seconds" },
];

export default function LoginPage() {
  return (
    <div className="flex min-h-screen bg-zinc-50 dark:bg-zinc-950">
      {/* Left — marketing panel */}
      <div className="hidden md:flex md:w-1/2 flex-col justify-center px-12 lg:px-20 bg-zinc-900 dark:bg-zinc-950">
        <div className="max-w-md">
          <div className="mb-6 text-sm font-semibold tracking-widest text-zinc-400 uppercase">
            Todo App
          </div>
          <h1 className="text-4xl font-bold text-white leading-tight mb-4">
            Manage Tasks Smarter, Not Harder
          </h1>
          <p className="text-zinc-400 text-lg mb-10 leading-relaxed">
            A powerful task manager with AI-powered chat, smart priorities, tags, reminders, and real-time sync.
          </p>
          <ul className="space-y-4">
            {FEATURES.map(({ icon, label, detail }) => (
              <li key={label} className="flex items-start gap-3">
                <span className="text-xl leading-none mt-0.5">{icon}</span>
                <div>
                  <span className="text-white font-medium text-sm">{label}</span>
                  <span className="text-zinc-500 text-sm"> — {detail}</span>
                </div>
              </li>
            ))}
          </ul>
        </div>
      </div>

      {/* Right — auth form */}
      <div className="flex w-full md:w-1/2 flex-col items-center justify-center px-6 py-12">
        {/* Mobile-only heading */}
        <div className="mb-8 text-center md:hidden">
          <h1 className="text-2xl font-bold text-zinc-900 dark:text-zinc-100">
            Manage Tasks Smarter
          </h1>
          <p className="mt-1 text-sm text-zinc-500 dark:text-zinc-400">
            AI-powered task management at your fingertips
          </p>
        </div>

        <div className="w-full max-w-sm space-y-6 rounded-lg border border-zinc-200 bg-white p-8 shadow-sm dark:border-zinc-800 dark:bg-zinc-900">
          <div className="space-y-2 text-center">
            <h2 className="text-2xl font-bold text-zinc-900 dark:text-zinc-100">
              Welcome back
            </h2>
            <p className="text-sm text-zinc-500 dark:text-zinc-400">
              Sign in to your account
            </p>
          </div>
          <LoginForm />
          <p className="text-center text-sm text-zinc-500 dark:text-zinc-400">
            Don&apos;t have an account?{" "}
            <Link
              href="/signup"
              className="font-medium text-zinc-900 underline-offset-4 hover:underline dark:text-zinc-100"
            >
              Sign up
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
