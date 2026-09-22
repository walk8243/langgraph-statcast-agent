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

  if (!stats.targetBatterStats && !stats.targetPitcherStats) {
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
  const {
    player,
    targetYear,
    batterStatsList,
    pitcherStatsList,
    targetBatterStats,
    targetPitcherStats,
  } = stats;
  const playerName = player.nameJa
    ? `${player.nameJa} (${player.nameEn})`
    : player.nameEn;
  const team = player.teamName ? `所属球団: ${player.teamName}` : "";

  let prompt = `あなたはプロ野球・メジャーリーグ（MLB）の高度なデータ分析を行う野球アナリストです。\n`;
  prompt += `以下の選手および直近最大3年間のスタッツデータを分析し、【${targetYear}年シーズン】を中心とした日本語の詳細かつ魅力的なシーズン解説文を作成してください。\n\n`;
  prompt += `### 対象選手情報\n`;
  prompt += `- 選手名: ${playerName}\n`;
  if (team) {
    prompt += `- ${team}\n`;
  }
  prompt += `- 分析対象シーズン（中心）: ${targetYear}年\n\n`;

  // 1. 打者成績
  if (targetBatterStats) {
    prompt += `### 【中心分析対象】${targetYear}年 打撃成績\n`;
    prompt += `- 試合数: ${targetBatterStats.games}試合, 打席数: ${targetBatterStats.plateAppearances}, 打数: ${targetBatterStats.atBats}\n`;
    prompt += `- 安打数: ${targetBatterStats.hits}本 (二塁打: ${targetBatterStats.doubles}, 三塁打: ${targetBatterStats.triples}, 本塁打: ${targetBatterStats.homeRuns}本)\n`;
    prompt += `- 打点: ${targetBatterStats.rbi}, 得点: ${targetBatterStats.runs}\n`;
    prompt += `- 打率: ${targetBatterStats.battingAverage.toFixed(3)}, 出塁率: ${targetBatterStats.onBasePercentage.toFixed(3)}, 長打率: ${targetBatterStats.sluggingPercentage.toFixed(3)}, OPS: ${targetBatterStats.ops.toFixed(3)}\n`;
    prompt += `- 盗塁: ${targetBatterStats.stolenBases} (盗塁死: ${targetBatterStats.caughtStealing})\n`;
    prompt += `- 四球: ${targetBatterStats.walks} (敬遠: ${targetBatterStats.intentionalWalks}), 死球: ${targetBatterStats.hitByPitch}, 三振: ${targetBatterStats.strikeouts}\n\n`;
  }

  if (batterStatsList.length > 1) {
    prompt += `### 参考：打撃成績の推移（直近${batterStatsList.length}年間）\n`;
    for (const b of batterStatsList) {
      prompt += `- ${b.year}年: ${b.games}試合 打率.${(b.battingAverage * 1000).toFixed(0).padStart(3, "0")} 本塁打${b.homeRuns}本 打点${b.rbi} 盗塁${b.stolenBases} OPS${b.ops.toFixed(3)} 四球${b.walks} 三振${b.strikeouts}\n`;
    }
    prompt += `\n`;
  }

  // 2. 投手成績
  if (targetPitcherStats) {
    prompt += `### 【中心分析対象】${targetYear}年 投球成績\n`;
    prompt += `- 登板数: ${targetPitcherStats.gamesPitched}登板 (先発: ${targetPitcherStats.gamesStarted}, 完投: ${targetPitcherStats.completeGames}, 完封: ${targetPitcherStats.shutouts})\n`;
    prompt += `- 勝敗: ${targetPitcherStats.wins}勝 ${targetPitcherStats.losses}敗, 防御率 (ERA): ${targetPitcherStats.era.toFixed(2)}\n`;
    prompt += `- セーブ: ${targetPitcherStats.saves} (機会: ${targetPitcherStats.saveOpportunities}), ホールド: ${targetPitcherStats.holds}, ブロウンセーブ: ${targetPitcherStats.blownSaves}\n`;
    prompt += `- 投球回: ${targetPitcherStats.inningsPitched}回 (アウト数: ${targetPitcherStats.outs}), 投球数: ${targetPitcherStats.numberOfPitches}球\n`;
    prompt += `- 被安打: ${targetPitcherStats.hits}, 失点: ${targetPitcherStats.runs}, 自責点: ${targetPitcherStats.earnedRuns}, 被本塁打: ${targetPitcherStats.homeRuns}\n`;
    prompt += `- 奪三振: ${targetPitcherStats.strikeouts}, 与四球: ${targetPitcherStats.walks}, 対戦打者数: ${targetPitcherStats.battersFaced}\n`;
    prompt += `- WHIP: ${targetPitcherStats.whip.toFixed(2)}, 被打率: ${targetPitcherStats.battingAverageAgainst.toFixed(3)}\n\n`;
  }

  if (pitcherStatsList.length > 1) {
    prompt += `### 参考：投球成績の推移（直近${pitcherStatsList.length}年間）\n`;
    for (const pt of pitcherStatsList) {
      prompt += `- ${pt.year}年: ${pt.gamesPitched}登板 ${pt.wins}勝${pt.losses}敗 防御率${pt.era.toFixed(2)} 投球回${pt.inningsPitched} 奪三振${pt.strikeouts} 四球${pt.walks} WHIP${pt.whip.toFixed(2)}\n`;
    }
    prompt += `\n`;
  }

  prompt += `### 出力形式の指示\n`;
  prompt += `1. **${targetYear}年シーズンの総括・ハイライト**: このシーズンを中心とし、選手の主要な活躍や特徴をわかりやすくまとめた導入。\n`;
  prompt += `2. **詳細分析**: 打撃または投球（二刀流の場合は両面）における優れたスタッツや指標の特徴（OPS、長打力、選球眼、走塁効率、防御率、奪三振率、制球力等）についての詳細な考察。\n`;
  prompt += `3. **過去シーズンからの推移と進化**: 提供された直近複数年の推移データを踏まえ、前年からの変化や向上点、キャリアの成熟度や傾向について言及。\n`;
  prompt += `4. **まとめ**: チームへの貢献度やシーズン全体の位置づけ。\n`;
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

  try {
    const prompt = buildPrompt(state.playerStats);
    const response = await model.invoke(prompt);
    const reportText =
      typeof response.content === "string"
        ? response.content
        : JSON.stringify(response.content);

    return {
      report: reportText,
    };
  } catch (err: any) {
    return {
      error: `Gemini API 呼び出し中にエラーが発生しました: ${err.message || String(err)}`,
    };
  }
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
