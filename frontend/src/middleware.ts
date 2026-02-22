import { NextRequest, NextResponse } from "next/server";

export default function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const sessionCookie = request.cookies.get("better-auth.session_token");

  // Public routes - allow access
  const publicRoutes = ["/login", "/signup"];
  if (publicRoutes.some((route) => pathname.startsWith(route))) {
    // If already authenticated, redirect to dashboard
    if (sessionCookie) {
      return NextResponse.redirect(new URL("/dashboard", request.url));
    }
    return NextResponse.next();
  }

  // Auth API routes - always allow (Better Auth handles them)
  if (pathname.startsWith("/api/auth")) {
    return NextResponse.next();
  }

  // Protected routes - require session cookie
  if (!sessionCookie) {
    return NextResponse.redirect(new URL("/login", request.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"],
};
