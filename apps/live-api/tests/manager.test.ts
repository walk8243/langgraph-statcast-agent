import { describe, it, expect, vi, beforeEach } from "vitest";
import { ConnectionManager } from "../src/manager.js";
import type { LiveEvent } from "../src/types.js";
import { EventEmitter } from "node:events";

function createMockResponse() {
  const emitter = new EventEmitter() as any;
  emitter.writeHead = vi.fn();
  emitter.write = vi.fn();
  emitter.end = vi.fn();
  emitter.flushHeaders = vi.fn();
  return emitter;
}

describe("ConnectionManager", () => {
  let manager: ConnectionManager;

  beforeEach(() => {
    manager = new ConnectionManager();
  });

  it("should add client, write SSE headers, and send initial comment", () => {
    const res = createMockResponse();
    const client = manager.addClient(748534, res);

    expect(res.writeHead).toHaveBeenCalledWith(
      200,
      expect.objectContaining({
        "Content-Type": "text/event-stream",
        "Cache-Control": "no-cache, no-transform",
        "Connection": "keep-alive",
      }),
    );
    expect(res.write).toHaveBeenCalledWith(": connected\n\n");
    expect(manager.getClientCount(748534)).toBe(1);
    expect(manager.getClientCount()).toBe(1);
    expect(client.gamePk).toBe(748534);
  });

  it("should remove client on response close event", () => {
    const res = createMockResponse();
    manager.addClient(748534, res);
    expect(manager.getClientCount(748534)).toBe(1);

    // クライアント切断イベントをエミュレート
    res.emit("close");

    expect(manager.getClientCount(748534)).toBe(0);
    expect(manager.getClientCount()).toBe(0);
  });

  it("should broadcast event only to clients of the matching game_pk", () => {
    const res1 = createMockResponse();
    const res2 = createMockResponse();
    const resOther = createMockResponse();

    manager.addClient(1001, res1);
    manager.addClient(1001, res2);
    manager.addClient(2002, resOther);

    const event: LiveEvent = {
      game_pk: 1001,
      event_type: "pitch",
      timestamp: new Date().toISOString(),
      data: { pitch_number: 1, call_description: "Called Strike" },
    };

    const sentCount = manager.broadcast(event);
    expect(sentCount).toBe(2);

    expect(res1.write).toHaveBeenCalledWith(
      expect.stringContaining("event: pitch\ndata: "),
    );
    expect(res2.write).toHaveBeenCalledWith(
      expect.stringContaining("event: pitch\ndata: "),
    );
    // 異なる gamePk のクライアントには送られないこと
    expect(resOther.write).not.toHaveBeenCalledWith(
      expect.stringContaining("event: pitch"),
    );
  });

  it("should send keepalive to all connected clients", () => {
    const res1 = createMockResponse();
    const res2 = createMockResponse();

    manager.addClient(1001, res1);
    manager.addClient(2002, res2);

    manager.sendKeepalive();

    expect(res1.write).toHaveBeenCalledWith(": keepalive\n\n");
    expect(res2.write).toHaveBeenCalledWith(": keepalive\n\n");
  });

  it("should return correct stats", () => {
    const res1 = createMockResponse();
    const res2 = createMockResponse();

    manager.addClient(1001, res1);
    manager.addClient(2002, res2);

    const stats = manager.getStats();
    expect(stats.totalConnections).toBe(2);
    expect(stats.activeGames).toBe(2);
    expect(stats.gamePks).toEqual(expect.arrayContaining([1001, 2002]));
  });

  it("should close all connections on closeAll", () => {
    const res1 = createMockResponse();
    const res2 = createMockResponse();

    manager.addClient(1001, res1);
    manager.addClient(2002, res2);

    manager.closeAll();

    expect(res1.end).toHaveBeenCalled();
    expect(res2.end).toHaveBeenCalled();
    expect(manager.getClientCount()).toBe(0);
  });
});
