import { loadConfig } from "./config.js";
import { ConnectionManager } from "./manager.js";
import { LiveEventSubscriber } from "./subscriber.js";
import { createApp } from "./server.js";

async function main(): Promise<void> {
  const config = loadConfig();

  console.log(`Starting live-api server...`);
  console.log(`Configuration:`, {
    port: config.port,
    host: config.host,
    projectId: config.projectId,
    subscriptionId: config.subscriptionId,
    keepaliveIntervalMs: config.keepaliveIntervalMs,
    corsOrigin: config.corsOrigin,
    emulatorHost: process.env.PUBSUB_EMULATOR_HOST || "none",
  });

  const manager = new ConnectionManager();
  manager.startKeepalive(config.keepaliveIntervalMs);

  const subscriber = new LiveEventSubscriber(
    config.projectId,
    config.subscriptionId,
    manager,
  );
  subscriber.start();

  const app = createApp(manager, config);

  const server = app.listen(config.port, config.host, () => {
    console.log(`live-api server is listening on http://${config.host}:${config.port}`);
  });

  const shutdown = async (signal: string) => {
    console.log(`\nReceived ${signal}. Shutting down gracefully...`);
    manager.stopKeepalive();
    await subscriber.stop();
    manager.closeAll();

    server.close(() => {
      console.log("HTTP server closed.");
      process.exit(0);
    });

    // 強制終了フォールバック
    setTimeout(() => {
      console.error("Forceful shutdown after timeout.");
      process.exit(1);
    }, 5000).unref();
  };

  process.on("SIGINT", () => shutdown("SIGINT"));
  process.on("SIGTERM", () => shutdown("SIGTERM"));
}

main().catch((err) => {
  console.error("Fatal error starting live-api:", err);
  process.exit(1);
});
