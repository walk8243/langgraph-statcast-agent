import { describe, expect, it, vi } from "vitest";
import * as dbModule from "../src/db.js";
import { LiveGameWorker } from "../src/worker.js";

describe("worker", () => {
  it("processGame and runOnce correctly process feeds and track state", async () => {
    const mockFeed = {
      gamePk: 824703,
      gameData: {
        game: { pk: 824703, type: "R", season: "2024" },
        datetime: { dateTime: "2024-04-26T23:10:00Z" },
        status: { abstractGameState: "Live", detailedState: "In Progress" },
        teams: {
          away: { id: 111, name: "Boston Red Sox" },
          home: { id: 112, name: "Chicago Cubs" },
        },
        players: {},
      },
      liveData: {
        linescore: { currentInning: 1, balls: 0, strikes: 0, outs: 0, teams: {} },
        plays: { allPlays: [] },
      },
    };

    const mockClient = {
      fetchLiveFeed: vi.fn().mockResolvedValue(mockFeed),
      fetchTodaySchedule: vi.fn(),
    } as any;

    const mockPublisher = {
      publishEvents: vi.fn().mockResolvedValue(1),
      publishEvent: vi.fn(),
    } as any;

    const mockPool = {
      query: vi.fn().mockResolvedValue({ rows: [] }),
      connect: vi.fn().mockResolvedValue({
        query: vi.fn().mockResolvedValue({ rows: [] }),
        release: vi.fn(),
      }),
      end: vi.fn(),
    } as any;

    const saveSpy = vi.spyOn(dbModule, "saveDiffResult").mockResolvedValue();

    const worker = new LiveGameWorker({
      pollIntervalSeconds: 1.0,
      targetGamePks: [824703],
      autoDiscover: false,
      client: mockClient,
      publisher: mockPublisher,
      dbPool: mockPool,
    });

    const results1 = await worker.runOnce();
    expect(results1.get(824703)).toBe(1);
    expect(mockClient.fetchLiveFeed).toHaveBeenCalledWith(824703);
    expect(saveSpy).toHaveBeenCalledTimes(1);
    expect(mockPublisher.publishEvents).toHaveBeenCalledTimes(1);

    // 2回目は差分なしのため 0
    const results2 = await worker.runOnce();
    expect(results2.get(824703)).toBe(0);
  });
});
