import { describe, expect, it, vi } from "vitest";
import { LiveEventPublisher } from "../src/publisher.js";

describe("publisher", () => {
  it("publishEvent serializes and publishes message to topic", async () => {
    const publisher = new LiveEventPublisher("test-project", "mlb-live-events");
    const mockPublishMessage = vi.fn().mockResolvedValue("msg-12345");
    (publisher as any).topic = {
      publishMessage: mockPublishMessage,
    };

    const msgId = await publisher.publishEvent({
      game_pk: 824703,
      event_type: "pitch",
      timestamp: "2024-04-26T23:10:00Z",
      data: { pitch_number: 1, start_speed: 98.5 },
    });

    expect(msgId).toBe("msg-12345");
    expect(mockPublishMessage).toHaveBeenCalledTimes(1);

    const callArgs = mockPublishMessage.mock.calls[0][0];
    expect(callArgs.attributes.game_pk).toBe("824703");
    expect(callArgs.attributes.event_type).toBe("pitch");

    const payload = JSON.parse(callArgs.data.toString());
    expect(payload.game_pk).toBe(824703);
    expect(payload.event_type).toBe("pitch");
    expect(payload.data.start_speed).toBe(98.5);
  });

  it("publishEvents publishes multiple messages", async () => {
    const publisher = new LiveEventPublisher("test-project", "mlb-live-events");
    const mockPublishMessage = vi.fn().mockResolvedValue("msg-id");
    (publisher as any).topic = {
      publishMessage: mockPublishMessage,
    };

    const count = await publisher.publishEvents([
      {
        game_pk: 824703,
        event_type: "linescore",
        timestamp: "2024-04-26T23:10:00Z",
        data: {},
      },
      {
        game_pk: 824703,
        event_type: "pitch",
        timestamp: "2024-04-26T23:10:01Z",
        data: {},
      },
    ]);

    expect(count).toBe(2);
    expect(mockPublishMessage).toHaveBeenCalledTimes(2);
  });
});
