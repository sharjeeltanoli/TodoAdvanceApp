import { betterAuth } from "better-auth";
import { Pool, neonConfig } from "@neondatabase/serverless";
import { bearer } from "better-auth/plugins/bearer";
import { jwt } from "better-auth/plugins/jwt";
import ws from "ws";

neonConfig.webSocketConstructor = ws;

// Build trusted origins. Explicit BETTER_AUTH_TRUSTED_ORIGINS env var takes precedence,
// then Vercel system env vars are auto-included so preview + production deployments
// work without any extra dashboard config.
function getTrustedOrigins(): string[] {
  const origins = new Set<string>();

  if (process.env.BETTER_AUTH_TRUSTED_ORIGINS) {
    for (const o of process.env.BETTER_AUTH_TRUSTED_ORIGINS.split(",")) {
      origins.add(o.trim());
    }
  }

  // Vercel injects these automatically — include both so any deployment URL is trusted
  if (process.env.VERCEL_URL) {
    origins.add(`https://${process.env.VERCEL_URL}`);
  }
  if (process.env.VERCEL_PROJECT_PRODUCTION_URL) {
    origins.add(`https://${process.env.VERCEL_PROJECT_PRODUCTION_URL}`);
  }

  return [...origins];
}

export const auth = betterAuth({
  database: new Pool({
    connectionString: process.env.DATABASE_URL!,
  }),
  emailAndPassword: {
    enabled: true,
  },
  plugins: [bearer(), jwt()],
  trustedOrigins: getTrustedOrigins(),
});
