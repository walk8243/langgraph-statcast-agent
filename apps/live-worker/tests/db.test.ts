import { describe, expect, it, vi } from "vitest";
import { findInProgressGames, saveDiffResult } from "../src/db.js";
import { DiffResult } from "../src/types.js";

describe("db", () => {
  it("findInProgressGames returns array of game_pk", async () => {
    const mockPool = {
      query: vi.fn().mockResolvedValue({
        rows: [{ game_pk: "824703" }, { game_pk: "824704" }],
      }),
    } as any;

    const pks = await findInProgressGames(mockPool);
    expect(pks).toEqual([824703, 824704]);
    expect(mockPool.query).toHaveBeenCalledTimes(1);
    expect(mockPool.query.mock.calls[0][0]).toContain("status ILIKE '%Progress%'");
  });

  it("saveDiffResult executes in transaction and commits", async () => {
    const mockClient = {
      query: vi.fn().mockResolvedValue({ rows: [] }),
      release: vi.fn(),
    };
    const mockPool = {
      connect: vi.fn().mockResolvedValue(mockClient),
    } as any;

    const diff: DiffResult = {
      game_pk: 824703,
      game_info: {
        game_pk: 824703,
        game_date_time: new Date(),
        season: 2024,
        game_type: "R",
        status: "In Progress",
        status_code: "I",
        abstract_state: "Live",
        home_team_id: 112,
        away_team_id: 111,
        home_score: 0,
        away_score: 0,
      },
      players: [{ player_id: 660271, name_en: "Shohei Ohtani", team_id: 111 }],
      linescore: {
        game_pk: 824703,
        current_inning: 1,
        is_top_inning: true,
        scheduled_innings: 9,
        balls: 0,
        strikes: 0,
        outs: 0,
        home_score: 0,
        away_score: 0,
        home_hits: 0,
        away_hits: 0,
        home_errors: 0,
        away_errors: 0,
        innings_json: "[]",
      },
      plays: [
        {
          game_pk: 824703,
          at_bat_index: 0,
          inning: 1,
          half_inning: "top",
          is_top_inning: true,
          batter_id: 660271,
          pitcher_id: 543037,
          first_base_runner_id: null,
          second_base_runner_id: null,
          third_base_runner_id: null,
          event: null,
          event_type: null,
          description: null,
          rbi: 0,
          away_score: 0,
          home_score: 0,
          is_scoring_play: false,
          is_out: false,
          is_complete: false,
          start_time: null,
          end_time: null,
        },
      ],
      pitches: [
        {
          game_pk: 824703,
          at_bat_index: 0,
          pitch_number: 1,
          play_id: "uuid-1",
          pitch_type: "FF",
          pitch_name: "Four-Seam Fastball",
          start_speed: 98.0,
          end_speed: 91.0,
          zone: 5,
          p_x: 0.0,
          p_z: 2.5,
          spin_rate: 2400.0,
          spin_direction: 200,
          break_angle: 2.0,
          break_vertical: 12.0,
          break_vertical_induced: 15.0,
          break_horizontal: 5.0,
          call_code: "C",
          call_description: "Called Strike",
          description: "Strike",
          balls: 0,
          strikes: 1,
          outs: 0,
          is_strike: true,
          is_ball: false,
          is_in_play: false,
          is_pitch: true,
          launch_speed: null,
          launch_angle: null,
          total_distance: null,
          trajectory: null,
          hardness: null,
          hit_location: null,
          coord_x: null,
          coord_y: null,
          start_time: null,
          end_time: null,
        },
      ],
      events: [],
    };

    await saveDiffResult(mockPool, diff);

    expect(mockClient.query).toHaveBeenCalledWith("BEGIN");
    expect(mockClient.query).toHaveBeenCalledWith("COMMIT");
    expect(mockClient.release).toHaveBeenCalled();
  });

  it("saveDiffResult rolls back on error", async () => {
    const mockClient = {
      query: vi.fn().mockImplementation((sql: string) => {
        if (sql === "BEGIN") return Promise.resolve();
        throw new Error("DB failure");
      }),
      release: vi.fn(),
    };
    const mockPool = {
      connect: vi.fn().mockResolvedValue(mockClient),
    } as any;

    const diff = {
      game_pk: 824703,
      game_info: { game_pk: 824703 } as any,
      players: [],
      linescore: null,
      plays: [],
      pitches: [],
      events: [],
    };

    await expect(saveDiffResult(mockPool, diff)).rejects.toThrow("DB failure");
    expect(mockClient.query).toHaveBeenCalledWith("ROLLBACK");
    expect(mockClient.release).toHaveBeenCalled();
  });
});
