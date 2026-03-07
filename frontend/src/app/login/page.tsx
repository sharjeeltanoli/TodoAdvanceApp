import Link from "next/link";
import { LoginForm } from "@/components/auth/login-form";

const FEATURES = [
  {
    icon: "✨",
    label: "AI Chat Assistant",
    detail: "Manage tasks in plain English",
    iconBg: "bg-blue-500/20",
    labelColor: "text-blue-300",
  },
  {
    icon: "🎯",
    label: "Smart Priorities",
    detail: "High, medium, and low task tiers",
    iconBg: "bg-orange-500/20",
    labelColor: "text-orange-300",
  },
  {
    icon: "🏷️",
    label: "Tags & Filters",
    detail: "Organise tasks exactly your way",
    iconBg: "bg-green-500/20",
    labelColor: "text-green-300",
  },
  {
    icon: "📅",
    label: "Due Dates & Reminders",
    detail: "Never miss a deadline",
    iconBg: "bg-purple-500/20",
    labelColor: "text-purple-300",
  },
  {
    icon: "🔄",
    label: "Real-time Sync",
    detail: "Updates across all devices instantly",
    iconBg: "bg-cyan-500/20",
    labelColor: "text-cyan-300",
  },
  {
    icon: "🔍",
    label: "Advanced Search",
    detail: "Find any task in seconds",
    iconBg: "bg-indigo-500/20",
    labelColor: "text-indigo-300",
  },
];

export default function LoginPage() {
  return (
    <div className="flex min-h-screen bg-gradient-to-br from-slate-900 via-indigo-950 to-slate-900">
      {/* Left — marketing panel */}
      <div className="hidden md:flex md:w-1/2 flex-col justify-center px-12 lg:px-20">
        <div className="max-w-md">
          {/* Wordmark */}
          <div className="mb-8 inline-flex items-center gap-2 rounded-full border border-indigo-500/30 bg-indigo-500/10 px-4 py-1.5">
            <span className="text-sm font-semibold text-indigo-300 tracking-wide">Todo App</span>
          </div>

          {/* Heading with gradient */}
          <h1 className="text-4xl font-bold leading-tight mb-4">
            <span className="bg-gradient-to-r from-blue-400 via-indigo-400 to-purple-400 bg-clip-text text-transparent">
              Manage Tasks Smarter,
            </span>
            <br />
            <span className="text-white">Not Harder</span>
          </h1>

          <p className="text-slate-400 text-base mb-10 leading-relaxed">
            AI-powered chat, smart priorities, tags, reminders, and real-time sync — all in one place.
          </p>

          {/* Feature list */}
          <ul className="space-y-3">
            {FEATURES.map(({ icon, label, detail, iconBg, labelColor }) => (
              <li key={label} className="flex items-center gap-3 rounded-xl p-2 transition-colors hover:bg-white/5">
                <div className={`flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-lg text-lg ${iconBg}`}>
                  {icon}
                </div>
                <div>
                  <span className={`text-sm font-semibold ${labelColor}`}>{label}</span>
                  <span className="text-slate-500 text-sm"> — {detail}</span>
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
          <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-400 via-indigo-400 to-purple-400 bg-clip-text text-transparent">
            Manage Tasks Smarter
          </h1>
          <p className="mt-1 text-sm text-slate-400">
            AI-powered task management at your fingertips
          </p>
        </div>

        <div className="w-full max-w-sm space-y-6 rounded-xl border border-white/10 bg-white/[0.06] p-8 shadow-2xl backdrop-blur-sm">
          <div className="space-y-1 text-center">
            <h2 className="text-2xl font-bold text-white">
              Welcome back
            </h2>
            <p className="text-sm text-slate-400">
              Sign in to your account
            </p>
          </div>
          <LoginForm />
          <p className="text-center text-sm text-slate-400">
            Don&apos;t have an account?{" "}
            <Link
              href="/signup"
              className="font-semibold text-indigo-400 underline-offset-4 hover:underline hover:text-indigo-300"
            >
              Sign up
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
