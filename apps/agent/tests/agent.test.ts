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

  it("打者成績および複数年推移が含まれるプロンプトが正しく生成されること", () => {
    const batter2023 = {
      year: 2023,
      games: 135,
      plateAppearances: 599,
      atBats: 497,
      runs: 102,
      hits: 151,
      doubles: 26,
      triples: 8,
      homeRuns: 44,
      rbi: 95,
      totalBases: 325,
      strikeouts: 143,
      walks: 91,
      intentionalWalks: 21,
      hitByPitch: 3,
      stolenBases: 20,
      caughtStealing: 6,
      battingAverage: 0.304,
      onBasePercentage: 0.412,
      sluggingPercentage: 0.654,
      ops: 1.066,
    };

    const batter2024 = {
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
    };

    const stats: PlayerFullStats = {
      player: dummyPlayer,
      targetYear: 2024,
      batterStatsList: [batter2023, batter2024],
      pitcherStatsList: [],
      targetBatterStats: batter2024,
      targetPitcherStats: null,
    };

    const prompt = buildPrompt(stats);
    expect(prompt).toContain("大谷 翔平 (Shohei Ohtani)");
    expect(prompt).toContain("Los Angeles Dodgers");
    expect(prompt).toContain("【2024年シーズン】を中心とした");
    expect(prompt).toContain("【中心分析対象】2024年 打撃成績");
    expect(prompt).toContain("本塁打: 54本");
    expect(prompt).toContain("打点: 130");
    expect(prompt).toContain("盗塁: 59");
    expect(prompt).toContain("OPS: 1.036");
    expect(prompt).toContain("参考：打撃成績の推移（直近2年間）");
    expect(prompt).toContain("2023年:");
    expect(prompt).toContain("2024年:");
    expect(prompt).not.toContain("【中心分析対象】2024年 投球成績");
  });

  it("投手成績が含まれるプロンプトが正しく生成されること", () => {
    const pitcher2024 = {
      year: 2024,
      wins: 18,
      losses: 3,
      era: 2.38,
      gamesPitched: 29,
      gamesStarted: 29,
      completeGames: 0,
      shutouts: 0,
      saves: 0,
      saveOpportunities: 0,
      holds: 0,
      blownSaves: 0,
      inningsPitched: "177.2",
      outs: 533,
      hits: 141,
      runs: 52,
      earnedRuns: 47,
      homeRuns: 9,
      walks: 39,
      strikeouts: 225,
      whip: 1.01,
      battingAverageAgainst: 0.216,
      battersFaced: 702,
      numberOfPitches: 2800,
    };

    const stats: PlayerFullStats = {
      player: {
        playerId: 519242,
        nameEn: "Chris Sale",
        nameJa: "クリス・セール",
        teamId: 144,
        teamName: "Atlanta Braves",
      },
      targetYear: 2024,
      batterStatsList: [],
      pitcherStatsList: [pitcher2024],
      targetBatterStats: null,
      targetPitcherStats: pitcher2024,
    };

    const prompt = buildPrompt(stats);
    expect(prompt).toContain("クリス・セール (Chris Sale)");
    expect(prompt).toContain("【中心分析対象】2024年 投球成績");
    expect(prompt).toContain("18勝 3敗");
    expect(prompt).toContain("防御率 (ERA): 2.38");
    expect(prompt).toContain("奪三振: 225");
    expect(prompt).toContain("WHIP: 1.01");
    expect(prompt).not.toContain("【中心分析対象】2024年 打撃成績");
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

  it("対象年の成績データが存在しない場合はエラーを返すこと", async () => {
    vi.spyOn(statsDb, "fetchPlayerFullStats").mockResolvedValue({
      player: {
        playerId: 12345,
        nameEn: "Test Player",
        nameJa: null,
        teamId: null,
        teamName: null,
      },
      targetYear: 2024,
      batterStatsList: [],
      pitcherStatsList: [],
      targetBatterStats: null,
      targetPitcherStats: null,
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
    const mockBatter = {
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
    };

    const mockStats: PlayerFullStats = {
      player: {
        playerId: 12345,
        nameEn: "Test Player",
        nameJa: "テスト選手",
        teamId: 1,
        teamName: "Team",
      },
      targetYear: 2024,
      batterStatsList: [mockBatter],
      pitcherStatsList: [],
      targetBatterStats: mockBatter,
      targetPitcherStats: null,
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
