import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // output: "standalone" is for Docker/self-hosted only — remove for Vercel.
  // Keeping it on Vercel causes server action manifest mismatches after redeploys.
  serverExternalPackages: ["better-auth"],
  devIndicators: false,
};

export default nextConfig;
