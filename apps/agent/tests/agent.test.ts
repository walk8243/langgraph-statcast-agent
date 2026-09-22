import { describe, it, expect, vi, beforeEach } from "vitest";
import {
  buildPrompt,
  fetchStatsNode,
  saveReportNode,
  createPlayerReportGraph,
  type AgentState,
} from "../src/agent/graph.js";
import type { PlayerFullStats } from "../src/db/stats.js";
import * as statsDb from "../src/db/stats.js";

describe("buildPrompt", () => {
  const dummyPlayer = {
    playerId: 660271,
    nameEn: "Shohei Ohtani",
    nameJa: "大谷 翔平",
    teamId: 119,
    teamName: "Los Angeles Dodgers",
  };

  it("打者成績が含まれるプロンプトが正しく生成されること", () => {
    const stats: PlayerFullStats = {
      player: dummyPlayer,
      year: 2024,
      batterStats: {
        year: 2024,
        games: 159,
        plateAppearances: 731,
        atBats: 636,
        runs: 134,
        hits: 197,
        doubles: 38,
        triples: 7,
        homeRuns: 54,
        rbi: 130,
        totalBases: 411,
        strikeouts: 162,
        walks: 81,
        intentionalWalks: 10,
        hitByPitch: 6,
        stolenBases: 59,
        caughtStealing: 4,
        battingAverage: 0.31,
        onBasePercentage: 0.39,
        sluggingPercentage: 0.646,
        ops: 1.036,
      },
      pitcherStats: null,
    };

    const prompt = buildPrompt(stats);
    expect(prompt).toContain("大谷 翔平 (Shohei Ohtani)");
    expect(prompt).toContain("Los Angeles Dodgers");
    expect(prompt).toContain("2024年");
    expect(prompt).toContain("本塁打: 54本");
    expect(prompt).toContain("打点: 130");
    expect(prompt).toContain("盗塁: 59");
    expect(prompt).toContain("OPS: 1.036");
    expect(prompt).not.toContain("### 投球成績");
  });

  it("投手成績が含まれるプロンプトが正しく生成されること", () => {
    const stats: PlayerFullStats = {
      player: dummyPlayer,
      year: 2023,
      batterStats: null,
      pitcherStats: {
        year: 2023,
        wins: 10,
        losses: 5,
        era: 3.14,
        gamesPitched: 23,
        gamesStarted: 23,
        completeGames: 1,
        shutouts: 1,
        saves: 0,
        saveOpportunities: 0,
        holds: 0,
        blownSaves: 0,
        inningsPitched: "132.0",
        outs: 396,
        hits: 85,
        runs: 50,
        earnedRuns: 46,
        homeRuns: 18,
        walks: 55,
        strikeouts: 167,
        whip: 1.06,
        battingAverageAgainst: 0.184,
        battersFaced: 531,
        numberOfPitches: 2120,
      },
    };

    const prompt = buildPrompt(stats);
    expect(prompt).toContain("### 投球成績 (2023年)");
    expect(prompt).toContain("10勝 5敗");
    expect(prompt).toContain("防御率 (ERA): 3.14");
    expect(prompt).toContain("奪三振: 167");
    expect(prompt).toContain("WHIP: 1.06");
    expect(prompt).not.toContain("### 打撃成績");
  });
});

describe("fetchStatsNode", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("選手が存在しない場合はエラーを返すこと", async () => {
    vi.spyOn(statsDb, "fetchPlayerFullStats").mockResolvedValue(null);

    const state: AgentState = {
      playerId: 999999,
      year: 2024,
      playerStats: null,
      report: "",
      error: null,
      dryRun: false,
    };

    const result = await fetchStatsNode(state);
    expect(result.error).toContain("選手ID 999999 の情報が見つかりませんでした。");
  });

  it("成績データが存在しない場合はエラーを返すこと", async () => {
    vi.spyOn(statsDb, "fetchPlayerFullStats").mockResolvedValue({
      player: {
        playerId: 12345,
        nameEn: "Test Player",
        nameJa: null,
        teamId: null,
        teamName: null,
      },
      year: 2024,
      batterStats: null,
      pitcherStats: null,
    });

    const state: AgentState = {
      playerId: 12345,
      year: 2024,
      playerStats: null,
      report: "",
      error: null,
      dryRun: false,
    };

    const result = await fetchStatsNode(state);
    expect(result.error).toContain("成績データ（打撃・投球）が存在しません。");
  });

  it("正常に成績データが取得できること", async () => {
    const mockStats: PlayerFullStats = {
      player: {
        playerId: 12345,
        nameEn: "Test Player",
        nameJa: "テスト選手",
        teamId: 1,
        teamName: "Team",
      },
      year: 2024,
      batterStats: {
        year: 2024,
        games: 10,
        plateAppearances: 30,
        atBats: 25,
        runs: 5,
        hits: 8,
        doubles: 2,
        triples: 0,
        homeRuns: 1,
        rbi: 4,
        totalBases: 13,
        strikeouts: 5,
        walks: 5,
        intentionalWalks: 0,
        hitByPitch: 0,
        stolenBases: 1,
        caughtStealing: 0,
        battingAverage: 0.32,
        onBasePercentage: 0.433,
        sluggingPercentage: 0.52,
        ops: 0.953,
      },
      pitcherStats: null,
    };

    vi.spyOn(statsDb, "fetchPlayerFullStats").mockResolvedValue(mockStats);

    const state: AgentState = {
      playerId: 12345,
      year: 2024,
      playerStats: null,
      report: "",
      error: null,
      dryRun: false,
    };

    const result = await fetchStatsNode(state);
    expect(result.error).toBeUndefined();
    expect(result.playerStats).toEqual(mockStats);
  });
});

describe("saveReportNode", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("dryRun が true の場合は savePlayerReport を呼び出さないこと", async () => {
    const saveSpy = vi.spyOn(statsDb, "savePlayerReport").mockResolvedValue();

    const state: AgentState = {
      playerId: 12345,
      year: 2024,
      playerStats: null,
      report: "モックレポート",
      error: null,
      dryRun: true,
    };

    const result = await saveReportNode(state);
    expect(result).toEqual({});
    expect(saveSpy).not.toHaveBeenCalled();
  });

  it("dryRun が false の場合は savePlayerReport を呼び出して保存すること", async () => {
    const saveSpy = vi.spyOn(statsDb, "savePlayerReport").mockResolvedValue();

    const state: AgentState = {
      playerId: 12345,
      year: 2024,
      playerStats: null,
      report: "モックレポート",
      error: null,
      dryRun: false,
    };

    const result = await saveReportNode(state);
    expect(result).toEqual({});
    expect(saveSpy).toHaveBeenCalledWith(
      12345,
      2024,
      "モックレポート",
      expect.any(String)
    );
  });
});

describe("createPlayerReportGraph", () => {
  it("グラフが正常に生成されること", () => {
    const graph = createPlayerReportGraph();
    expect(graph).toBeDefined();
    expect(typeof graph.invoke).toBe("function");
  });

  it("選手が存在しない場合は fetchStats で停止しエラーを返すこと", async () => {
    vi.spyOn(statsDb, "fetchPlayerFullStats").mockResolvedValue(null);

    const graph = createPlayerReportGraph();
    const result = await graph.invoke({
      playerId: 999999,
      year: 2024,
      dryRun: true,
    });

    expect(result.error).toContain("選手ID 999999 の情報が見つかりませんでした。");
    expect(result.report).toBe("");
  });
});
