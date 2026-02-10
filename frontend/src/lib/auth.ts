import { betterAuth } from "better-auth";
import { Pool, neonConfig } from "@neondatabase/serverless";
import { bearer } from "better-auth/plugins/bearer";
import { jwt } from "better-auth/plugins/jwt";
import ws from "ws";

neonConfig.webSocketConstructor = ws;

export const auth = betterAuth({
  database: new Pool({
    connectionString: process.env.DATABASE_URL!,
  }),
  emailAndPassword: {
    enabled: true,
  },
  plugins: [bearer(), jwt()],
});
