import dotenv from "dotenv";

dotenv.config();

export interface AppConfig {
  port: number;
  host: string;
  projectId: string;
  subscriptionId: string;
  keepaliveIntervalMs: number;
  corsOrigin: string;
}

export function loadConfig(): AppConfig {
  return {
    port: parseInt(process.env.PORT || process.env.LIVE_API_PORT || "8001", 10),
    host: process.env.HOST || "0.0.0.0",
    projectId: process.env.GCP_PROJECT_ID || "local-statcast-project",
    subscriptionId: process.env.PUBSUB_SUBSCRIPTION_LIVE_EVENTS || "mlb-live-events-sub",
    keepaliveIntervalMs: parseInt(process.env.KEEPALIVE_INTERVAL_MS || "15000", 10),
    corsOrigin: process.env.CORS_ORIGIN || "*",
  };
}
