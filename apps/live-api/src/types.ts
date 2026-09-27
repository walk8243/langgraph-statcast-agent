import type { Response } from "express";

export type LiveEventType = "linescore" | "play" | "pitch" | "game_status";

export interface LiveEvent {
  game_pk: number;
  event_type: LiveEventType;
  timestamp: string;
  data: Record<string, any>;
}

export interface ClientConnection {
  id: string;
  gamePk: number;
  res: Response;
  connectedAt: Date;
}

export interface ConnectionStats {
  totalConnections: number;
  activeGames: number;
  gamePks: number[];
}
