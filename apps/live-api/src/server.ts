import express, { type Express, type Request, type Response } from "express";
import cors from "cors";
import type { ConnectionManager } from "./manager.js";
import type { AppConfig } from "./config.js";

export function createApp(manager: ConnectionManager, config?: Partial<AppConfig>): Express {
  const app = express();

  app.use(cors({
    origin: config?.corsOrigin || "*",
    methods: ["GET", "HEAD", "OPTIONS"],
  }));

  app.use(express.json());

  // ルート情報エンドポイント
  app.get("/", (_req: Request, res: Response) => {
    res.json({
      service: "live-api",
      description: "MLB Real-time Live Events SSE Delivery Server",
      endpoints: {
        health: "/health",
        events: "/api/games/:gamePk/events",
      },
    });
  });

  // ヘルスチェックエンドポイント
  app.get("/health", (_req: Request, res: Response) => {
    res.json({
      status: "healthy",
      uptime: process.uptime(),
      timestamp: new Date().toISOString(),
      connections: manager.getStats(),
    });
  });

  // SSE イベント配信ハンドラー
  const sseHandler = (req: Request, res: Response) => {
    const rawGamePk = Array.isArray(req.params.gamePk) ? req.params.gamePk[0] : req.params.gamePk;
    const gamePk = parseInt(rawGamePk ?? "", 10);

    if (isNaN(gamePk) || gamePk <= 0) {
      res.status(400).json({
        error: "Invalid gamePk. Must be a positive integer.",
      });
      return;
    }

    manager.addClient(gamePk, res);
  };

  app.get("/api/games/:gamePk/events", sseHandler);
  app.get("/games/:gamePk/events", sseHandler);

  return app;
}
