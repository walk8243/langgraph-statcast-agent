import { describe, it, expect, beforeEach } from "vitest";
import request from "supertest";
import type { Server } from "node:http";
import { ConnectionManager } from "../src/manager.js";
import { createApp } from "../src/server.js";

describe("Express Server & SSE Routes", () => {
  let manager: ConnectionManager;
  let app: ReturnType<typeof createApp>;

  beforeEach(() => {
    manager = new ConnectionManager();
    app = createApp(manager);
  });

  it("GET / returns service information", async () => {
    const res = await request(app).get("/");
    expect(res.status).toBe(200);
    expect(res.body.service).toBe("live-api");
    expect(res.body.endpoints).toBeDefined();
  });

  it("GET /health returns healthy status and connection stats", async () => {
    const res = await request(app).get("/health");
    expect(res.status).toBe(200);
    expect(res.body.status).toBe("healthy");
    expect(res.body.connections).toBeDefined();
    expect(res.body.connections.totalConnections).toBe(0);
  });

  it("GET /api/games/invalid/events returns 400 for non-numeric gamePk", async () => {
    const res = await request(app).get("/api/games/invalid/events");
    expect(res.status).toBe(400);
    expect(res.body.error).toContain("Invalid gamePk");
  });

  it("GET /api/games/-100/events returns 400 for negative gamePk", async () => {
    const res = await request(app).get("/api/games/-100/events");
    expect(res.status).toBe(400);
    expect(res.body.error).toContain("Invalid gamePk");
  });

  it("GET /api/games/748534/events registers client and returns SSE stream", async () => {
    const server: Server = await new Promise((resolve) => {
      const s = app.listen(0, "127.0.0.1", () => resolve(s));
    });

    try {
      const addr = server.address() as any;
      const port = addr.port;

      const controller = new AbortController();
      const res = await fetch(`http://127.0.0.1:${port}/api/games/748534/events`, {
        signal: controller.signal,
      });

      expect(res.status).toBe(200);
      expect(res.headers.get("content-type")).toContain("text/event-stream");
      expect(res.headers.get("cache-control")).toContain("no-cache");
      expect(manager.getClientCount(748534)).toBe(1);

      controller.abort();
    } finally {
      await new Promise<void>((resolve) => server.close(() => resolve()));
    }
  });
});
