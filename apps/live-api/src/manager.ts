import { randomUUID } from "node:crypto";
import type { Response } from "express";
import type { ClientConnection, ConnectionStats, LiveEvent } from "./types.js";

export class ConnectionManager {
  private clients: Map<number, Set<ClientConnection>> = new Map();
  private keepaliveTimer: NodeJS.Timeout | null = null;

  /**
   * SSE クライアントを接続プールへ追加し、必要な SSE ヘッダーを送信する
   */
  addClient(gamePk: number, res: Response): ClientConnection {
    res.writeHead(200, {
      "Content-Type": "text/event-stream",
      "Cache-Control": "no-cache, no-transform",
      "Connection": "keep-alive",
      "X-Accel-Buffering": "no",
    });

    if (typeof (res as any).flushHeaders === "function") {
      (res as any).flushHeaders();
    }

    const client: ClientConnection = {
      id: randomUUID(),
      gamePk,
      res,
      connectedAt: new Date(),
    };

    if (!this.clients.has(gamePk)) {
      this.clients.set(gamePk, new Set());
    }
    this.clients.get(gamePk)!.add(client);

    // 接続確立の初期コメントを送信
    res.write(`: connected\n\n`);

    res.on("close", () => {
      this.removeClient(gamePk, client);
    });

    return client;
  }

  /**
   * 切断されたクライアントをプールから除去する
   */
  removeClient(gamePk: number, client: ClientConnection): void {
    const gameClients = this.clients.get(gamePk);
    if (!gameClients) {
      return;
    }

    gameClients.delete(client);
    if (gameClients.size === 0) {
      this.clients.delete(gamePk);
    }
  }

  /**
   * 指定試合に紐付くクライアントへイベントをブロードキャストする
   */
  broadcast(event: LiveEvent): number {
    const gameClients = this.clients.get(event.game_pk);
    if (!gameClients || gameClients.size === 0) {
      return 0;
    }

    const sseMessage = this.formatSseMessage(event.event_type, event);
    let sentCount = 0;

    for (const client of gameClients) {
      try {
        client.res.write(sseMessage);
        sentCount++;
      } catch (err) {
        console.error(`Failed to send event to client ${client.id}:`, err);
        this.removeClient(event.game_pk, client);
      }
    }

    return sentCount;
  }

  /**
   * 全接続中のクライアントへキープアライブ（コメント行）を送信する
   */
  sendKeepalive(): void {
    const keepaliveMsg = `: keepalive\n\n`;
    for (const [gamePk, gameClients] of this.clients.entries()) {
      for (const client of gameClients) {
        try {
          client.res.write(keepaliveMsg);
        } catch {
          this.removeClient(gamePk, client);
        }
      }
    }
  }

  /**
   * 定期的なキープアライブタイマーを開始する
   */
  startKeepalive(intervalMs: number = 15000): void {
    if (this.keepaliveTimer) {
      clearInterval(this.keepaliveTimer);
    }
    this.keepaliveTimer = setInterval(() => {
      this.sendKeepalive();
    }, intervalMs);
    if (this.keepaliveTimer.unref) {
      this.keepaliveTimer.unref();
    }
  }

  /**
   * キープアライブタイマーを停止する
   */
  stopKeepalive(): void {
    if (this.keepaliveTimer) {
      clearInterval(this.keepaliveTimer);
      this.keepaliveTimer = null;
    }
  }

  /**
   * 接続中のクライアント数を取得する
   */
  getClientCount(gamePk?: number): number {
    if (gamePk !== undefined) {
      return this.clients.get(gamePk)?.size ?? 0;
    }
    let total = 0;
    for (const set of this.clients.values()) {
      total += set.size;
    }
    return total;
  }

  /**
   * 現在の接続統計を取得する
   */
  getStats(): ConnectionStats {
    const gamePks = Array.from(this.clients.keys());
    return {
      totalConnections: this.getClientCount(),
      activeGames: gamePks.length,
      gamePks,
    };
  }

  /**
   * 全クライアントの接続を終了する（シャットダウン用）
   */
  closeAll(): void {
    this.stopKeepalive();
    for (const [gamePk, gameClients] of this.clients.entries()) {
      for (const client of gameClients) {
        try {
          client.res.end();
        } catch {
          // ignore
        }
      }
    }
    this.clients.clear();
  }

  /**
   * SSE 規格フォーマットに整形する
   */
  private formatSseMessage(eventType: string, data: any): string {
    const payload = JSON.stringify(data);
    return `event: ${eventType}\ndata: ${payload}\n\n`;
  }
}
