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
      targetBatterStatcastStats: null,
      targetPitcherStatcastStats: null,
      targetPitcherPitchTypes: [],
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
    expect(prompt).not.toContain("【Statcast高度指標】");
  });

  it("打者Statcast指標が含まれるプロンプトが正しく生成されること", () => {
    const stats: PlayerFullStats = {
      player: {
        playerId: 673548,
        nameEn: "Seiya Suzuki",
        nameJa: "鈴木 誠也",
        teamId: 112,
        teamName: "Chicago Cubs",
      },
      targetYear: 2024,
      batterStatsList: [],
      pitcherStatsList: [],
      targetBatterStats: {
        year: 2024,
        games: 132,
        plateAppearances: 586,
        atBats: 512,
        runs: 74,
        hits: 145,
        doubles: 27,
        triples: 6,
        homeRuns: 21,
        rbi: 73,
        totalBases: 247,
        strikeouts: 139,
        walks: 63,
        intentionalWalks: 1,
        hitByPitch: 8,
        stolenBases: 16,
        caughtStealing: 5,
        battingAverage: 0.283,
        onBasePercentage: 0.366,
        sluggingPercentage: 0.482,
        ops: 0.848,
      },
      targetPitcherStats: null,
      targetBatterStatcastStats: {
        playerId: 673548,
        year: 2024,
        pitchesSeen: 2350,
        battedBalls: 350,
        barrels: 42,
        barrelPct: 12.0,
        hardHitCount: 165,
        hardHitPct: 47.1,
        avgExitVelocity: 91.5,
        maxExitVelocity: 114.2,
        avgLaunchAngle: 13.8,
        sweetSpotPct: 37.5,
      },
      targetPitcherStatcastStats: null,
      targetPitcherPitchTypes: [],
    };

    const prompt = buildPrompt(stats);
    expect(prompt).toContain("鈴木 誠也 (Seiya Suzuki)");
    expect(prompt).toContain("【Statcast高度指標】2024年 打球品質・トラッキングデータ");
    expect(prompt).toContain("打球数: 350球");
    expect(prompt).toContain("バレル (Barrels): 42本 (12.0%)");
    expect(prompt).toContain("ハードヒット率 (HardHit%): 47.1%");
    expect(prompt).toContain("平均打球初速 (Avg Exit Velocity): 91.5 mph");
    expect(prompt).toContain("最高打球初速 (Max Exit Velocity): 114.2 mph");
    expect(prompt).toContain("平均打球角度 (Avg Launch Angle): 13.8°");
    expect(prompt).toContain("スイートスポット率 (SweetSpot%): 37.5%");
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
      targetBatterStatcastStats: null,
      targetPitcherStatcastStats: null,
      targetPitcherPitchTypes: [],
    };

    const prompt = buildPrompt(stats);
    expect(prompt).toContain("クリス・セール (Chris Sale)");
    expect(prompt).toContain("【中心分析対象】2024年 投球成績");
    expect(prompt).toContain("18勝 3敗");
    expect(prompt).toContain("防御率 (ERA): 2.38");
    expect(prompt).toContain("奪三振: 225");
    expect(prompt).toContain("WHIP: 1.01");
    expect(prompt).not.toContain("【中心分析対象】2024年 打撃成績");
    expect(prompt).not.toContain("【Statcast高度指標】");
    expect(prompt).not.toContain("【球種別分析 (Pitch Arsenal)】");
  });

  it("投手Statcast指標および球種別データが含まれるプロンプトが正しく生成されること", () => {
    const stats: PlayerFullStats = {
      player: {
        playerId: 808967,
        nameEn: "Yoshinobu Yamamoto",
        nameJa: "山本 由伸",
        teamId: 119,
        teamName: "Los Angeles Dodgers",
      },
      targetYear: 2024,
      batterStatsList: [],
      pitcherStatsList: [],
      targetBatterStats: null,
      targetPitcherStats: {
        year: 2024,
        wins: 7,
        losses: 2,
        era: 3.0,
        gamesPitched: 18,
        gamesStarted: 18,
        completeGames: 0,
        shutouts: 0,
        saves: 0,
        saveOpportunities: 0,
        holds: 0,
        blownSaves: 0,
        inningsPitched: "90.0",
        outs: 270,
        hits: 78,
        runs: 32,
        earnedRuns: 30,
        homeRuns: 7,
        walks: 22,
        strikeouts: 105,
        whip: 1.11,
        battingAverageAgainst: 0.228,
        battersFaced: 367,
        numberOfPitches: 1470,
      },
      targetBatterStatcastStats: null,
      targetPitcherStatcastStats: {
        playerId: 808967,
        year: 2024,
        totalPitches: 1470,
        battedBalls: 230,
        barrelsAllowed: 14,
        barrelPct: 6.1,
        hardHitCount: 75,
        hardHitPct: 32.6,
        avgExitVelocity: 88.2,
        swings: 710,
        whiffs: 205,
        whiffPct: 28.9,
        calledStrikes: 240,
        cswPct: 30.3,
      },
      targetPitcherPitchTypes: [
        {
          playerId: 808967,
          year: 2024,
          pitchType: "FF",
          pitchName: "Four-Seam Fastball",
          pitches: 720,
          usagePct: 49.0,
          avgSpeed: 95.5,
          avgSpinRate: 2420,
          avgPfxX: -7.2,
          avgPfxZ: 16.5,
          swings: 350,
          whiffs: 75,
          whiffPct: 21.4,
        },
        {
          playerId: 808967,
          year: 2024,
          pitchType: "FS",
          pitchName: "Splitter",
          pitches: 410,
          usagePct: 27.9,
          avgSpeed: 90.2,
          avgSpinRate: 1510,
          avgPfxX: -9.8,
          avgPfxZ: 4.1,
          swings: 210,
          whiffs: 85,
          whiffPct: 40.5,
        },
      ],
    };

    const prompt = buildPrompt(stats);
    expect(prompt).toContain("山本 由伸 (Yoshinobu Yamamoto)");
    expect(prompt).toContain("【Statcast高度指標】2024年 投球トラッキングデータ");
    expect(prompt).toContain("総投球数: 1470球, 被打球数: 230球");
    expect(prompt).toContain("被バレル率 (Barrel%): 6.1% (被バレル数: 14本)");
    expect(prompt).toContain("空振り率 (Whiff%): 28.9%");
    expect(prompt).toContain("CSW% (Called Strikes + Whiffs): 30.3%");
    expect(prompt).toContain("【球種別分析 (Pitch Arsenal)】2024年");
    expect(prompt).toContain("Four-Seam Fastball (FF): 投球割合 49.0% (720球), 平均球速 95.5 mph");
    expect(prompt).toContain("Splitter (FS): 投球割合 27.9% (410球), 平均球速 90.2 mph");
    expect(prompt).toContain("空振り率 40.5%");
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
      targetBatterStatcastStats: null,
      targetPitcherStatcastStats: null,
      targetPitcherPitchTypes: [],
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
      targetBatterStatcastStats: null,
      targetPitcherStatcastStats: null,
      targetPitcherPitchTypes: [],
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
