import { Annotation, StateGraph, START, END } from "@langchain/langgraph";
import { ChatGoogleGenerativeAI } from "@langchain/google-genai";
import { config } from "../config.js";
import {
  fetchPlayerFullStats,
  savePlayerReport,
  type PlayerFullStats,
} from "../db/stats.js";

// エージェントのステート定義
export const AgentStateAnnotation = Annotation.Root({
  playerId: Annotation<number>(),
  year: Annotation<number>(),
  playerStats: Annotation<PlayerFullStats | null>({
    reducer: (_, next) => next,
    default: () => null,
  }),
  report: Annotation<string>({
    reducer: (_, next) => next,
    default: () => "",
  }),
  error: Annotation<string | null>({
    reducer: (_, next) => next,
    default: () => null,
  }),
  dryRun: Annotation<boolean>({
    reducer: (_, next) => next,
    default: () => false,
  }),
});

export type AgentState = typeof AgentStateAnnotation.State;

// 1. 成績データ取得ノード
export async function fetchStatsNode(
  state: AgentState
): Promise<Partial<AgentState>> {
  const stats = await fetchPlayerFullStats(state.playerId, state.year);
  if (!stats) {
    return {
      error: `選手ID ${state.playerId} の情報が見つかりませんでした。`,
    };
  }

  if (!stats.batterStats && !stats.pitcherStats) {
    return {
      playerStats: stats,
      error: `選手「${stats.player.nameEn}」の ${state.year} 年の成績データ（打撃・投球）が存在しません。`,
    };
  }

  return {
    playerStats: stats,
  };
}

// プロンプト生成ヘルパー
export function buildPrompt(stats: PlayerFullStats): string {
  const { player, year, batterStats, pitcherStats } = stats;
  const playerName = player.nameJa
    ? `${player.nameJa} (${player.nameEn})`
    : player.nameEn;
  const team = player.teamName ? `所属球団: ${player.teamName}` : "";

  let prompt = `あなたはプロ野球・メジャーリーグ（MLB）の高度なデータ分析を行う野球アナリストです。\n`;
  prompt += `以下の選手および${year}年シーズンのスタッツデータを分析し、日本語で詳細かつ魅力的なシーズン解説文を作成してください。\n\n`;
  prompt += `### 対象選手情報\n`;
  prompt += `- 選手名: ${playerName}\n`;
  if (team) {
    prompt += `- ${team}\n`;
  }
  prompt += `- 対象シーズン: ${year}年\n\n`;

  if (batterStats) {
    prompt += `### 打撃成績 (${year}年)\n`;
    prompt += `- 試合数: ${batterStats.games}試合, 打席数: ${batterStats.plateAppearances}, 打数: ${batterStats.atBats}\n`;
    prompt += `- 安打数: ${batterStats.hits}本 (二塁打: ${batterStats.doubles}, 三塁打: ${batterStats.triples}, 本塁打: ${batterStats.homeRuns}本)\n`;
    prompt += `- 打点: ${batterStats.rbi}, 得点: ${batterStats.runs}\n`;
    prompt += `- 打率: ${batterStats.battingAverage.toFixed(3)}, 出塁率: ${batterStats.onBasePercentage.toFixed(3)}, 長打率: ${batterStats.sluggingPercentage.toFixed(3)}, OPS: ${batterStats.ops.toFixed(3)}\n`;
    prompt += `- 盗塁: ${batterStats.stolenBases} (盗塁死: ${batterStats.caughtStealing})\n`;
    prompt += `- 四球: ${batterStats.walks} (敬遠: ${batterStats.intentionalWalks}), 死球: ${batterStats.hitByPitch}, 三振: ${batterStats.strikeouts}\n\n`;
  }

  if (pitcherStats) {
    prompt += `### 投球成績 (${year}年)\n`;
    prompt += `- 登板数: ${pitcherStats.gamesPitched}登板 (先発: ${pitcherStats.gamesStarted}, 完投: ${pitcherStats.completeGames}, 完封: ${pitcherStats.shutouts})\n`;
    prompt += `- 勝敗: ${pitcherStats.wins}勝 ${pitcherStats.losses}敗, 防御率 (ERA): ${pitcherStats.era.toFixed(2)}\n`;
    prompt += `- セーブ: ${pitcherStats.saves} (機会: ${pitcherStats.saveOpportunities}), ホールド: ${pitcherStats.holds}, ブロウンセーブ: ${pitcherStats.blownSaves}\n`;
    prompt += `- 投球回: ${pitcherStats.inningsPitched}回 (アウト数: ${pitcherStats.outs}), 投球数: ${pitcherStats.numberOfPitches}球\n`;
    prompt += `- 被安打: ${pitcherStats.hits}, 失点: ${pitcherStats.runs}, 自責点: ${pitcherStats.earnedRuns}, 被本塁打: ${pitcherStats.homeRuns}\n`;
    prompt += `- 奪三振: ${pitcherStats.strikeouts}, 与四球: ${pitcherStats.walks}, 対戦打者数: ${pitcherStats.battersFaced}\n`;
    prompt += `- WHIP: ${pitcherStats.whip.toFixed(2)}, 被打率: ${pitcherStats.battingAverageAgainst.toFixed(3)}\n\n`;
  }

  prompt += `### 出力形式の指示\n`;
  prompt += `1. **シーズンの総括・ハイライト**: このシーズンの選手の活躍や特徴をわかりやすくまとめた導入。\n`;
  prompt += `2. **詳細分析**: 打撃または投球（二刀流の場合は両面）における優れたスタッツや指標の特徴（OPS、本塁打、四球率、三振数、防御率、WHIP等）についての具体的な分析・考察。\n`;
  prompt += `3. **まとめ**: チームへの貢献度やシーズン全体の印象。\n`;
  prompt += `\n※ マークダウン形式で見出しや箇条書きを活用して読みやすく構成してください。`;

  return prompt;
}

// 2. Gemini による解説生成ノード
export async function generateReportNode(
  state: AgentState
): Promise<Partial<AgentState>> {
  if (state.error || !state.playerStats) {
    return {};
  }

  const apiKey = config.gemini.apiKey;
  if (!apiKey) {
    return {
      error:
        "GEMINI_API_KEY が設定されていません。.env ファイルまたは環境変数を確認してください。",
    };
  }

  const model = new ChatGoogleGenerativeAI({
    model: config.gemini.model,
    apiKey: apiKey,
    temperature: 0.7,
  });

  const prompt = buildPrompt(state.playerStats);
  const response = await model.invoke(prompt);
  const reportText =
    typeof response.content === "string"
      ? response.content
      : JSON.stringify(response.content);

  return {
    report: reportText,
  };
}

// 3. レポート保存ノード
export async function saveReportNode(
  state: AgentState
): Promise<Partial<AgentState>> {
  if (state.error || !state.report) {
    return {};
  }

  if (state.dryRun) {
    return {};
  }

  await savePlayerReport(
    state.playerId,
    state.year,
    state.report,
    config.gemini.model
  );

  return {};
}

// エラー判定用の条件分岐
function shouldContinueAfterFetch(state: AgentState): string {
  if (state.error) {
    return END;
  }
  return "generateReport";
}

function shouldContinueAfterGenerate(state: AgentState): string {
  if (state.error) {
    return END;
  }
  return "saveReport";
}

// ワークフローグラフの構築
export function createPlayerReportGraph() {
  const workflow = new StateGraph(AgentStateAnnotation)
    .addNode("fetchStats", fetchStatsNode)
    .addNode("generateReport", generateReportNode)
    .addNode("saveReport", saveReportNode)
    .addEdge(START, "fetchStats")
    .addConditionalEdges("fetchStats", shouldContinueAfterFetch, {
      [END]: END,
      generateReport: "generateReport",
    })
    .addConditionalEdges("generateReport", shouldContinueAfterGenerate, {
      [END]: END,
      saveReport: "saveReport",
    })
    .addEdge("saveReport", END);

  return workflow.compile();
}
