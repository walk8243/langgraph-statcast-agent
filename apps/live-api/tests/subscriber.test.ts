import { describe, it, expect, vi, beforeEach } from "vitest";
import { LiveEventSubscriber } from "../src/subscriber.js";
import { ConnectionManager } from "../src/manager.js";
import type { LiveEvent } from "../src/types.js";
import { EventEmitter } from "node:events";

// Google Cloud PubSub のモック
const mockSubscription = new EventEmitter() as any;
mockSubscription.close = vi.fn().mockResolvedValue(undefined);

const mockPubSub = {
  subscription: vi.fn(() => mockSubscription),
  close: vi.fn().mockResolvedValue(undefined),
};

vi.mock("@google-cloud/pubsub", () => {
  return {
    PubSub: vi.fn().mockImplementation(() => mockPubSub),
  };
});

describe("LiveEventSubscriber", () => {
  let manager: ConnectionManager;
  let subscriber: LiveEventSubscriber;

  beforeEach(() => {
    vi.clearAllMocks();
    mockSubscription.removeAllListeners();
    manager = new ConnectionManager();
    subscriber = new LiveEventSubscriber("test-project", "test-sub", manager);
  });

  it("should process valid message, broadcast to manager, and ack message", () => {
    const broadcastSpy = vi.spyOn(manager, "broadcast").mockReturnValue(1);

    subscriber.start();

    const testEvent: LiveEvent = {
      game_pk: 748534,
      event_type: "linescore",
      timestamp: new Date().toISOString(),
      data: { current_inning: 9 },
    };

    const mockMessage = {
      data: Buffer.from(JSON.stringify(testEvent)),
      ack: vi.fn(),
      nack: vi.fn(),
    };

    mockSubscription.emit("message", mockMessage);

    expect(broadcastSpy).toHaveBeenCalledWith(testEvent);
    expect(mockMessage.ack).toHaveBeenCalled();
  });

  it("should handle invalid JSON message gracefully and ack to prevent loop", () => {
    const broadcastSpy = vi.spyOn(manager, "broadcast");

    subscriber.start();

    const mockMessage = {
      data: Buffer.from("invalid-json-content"),
      ack: vi.fn(),
      nack: vi.fn(),
    };

    mockSubscription.emit("message", mockMessage);

    expect(broadcastSpy).not.toHaveBeenCalled();
    expect(mockMessage.ack).toHaveBeenCalled();
  });

  it("should stop cleanly and remove listeners", async () => {
    subscriber.start();
    expect(subscriber.getRunning()).toBe(true);

    await subscriber.stop();
    expect(subscriber.getRunning()).toBe(false);
    expect(mockSubscription.close).toHaveBeenCalled();
    expect(mockPubSub.close).toHaveBeenCalled();
  });
});
