import { Command } from "commander";
import { createPlayerReportGraph } from "./agent/graph.js";
import { closePool } from "./db/client.js";

const program = new Command();

program
  .name("statcast-agent")
  .description("LangGraph and Google Gemini agent for MLB player report generation")
  .version("0.1.0")
  .requiredOption("-p, --player-id <id>", "Player MLB ID (e.g. 660271 for Shohei Ohtani)")
  .option("-y, --year <year>", "Season year", "2024")
  .option("--dry-run", "Generate report without saving to PostgreSQL", false);

async function main() {
  program.parse(process.argv);
  const options = program.opts();

  const playerId = Number.parseInt(options.playerId, 10);
  const year = Number.parseInt(options.year, 10);
  const dryRun = Boolean(options.dryRun);

  if (Number.isNaN(playerId)) {
    console.error("エラー: --player-id には有効な数値を指定してください。");
    process.exit(1);
  }

  if (Number.isNaN(year)) {
    console.error("エラー: --year には有効な数値を指定してください。");
    process.exit(1);
  }

  console.log(`=======================================================`);
  console.log(`選手解説生成エージェント起動`);
  console.log(`対象選手ID: ${playerId}, 対象シーズン: ${year}年, dry-run: ${dryRun}`);
  console.log(`=======================================================\n`);

  try {
    const app = createPlayerReportGraph();
    const finalState = await app.invoke({
      playerId,
      year,
      dryRun,
    });

    if (finalState.error) {
      console.error(`\n[エラー発生] ${finalState.error}`);
      process.exitCode = 1;
      return;
    }

    console.log(`\n=================== 生成された解説文 ===================\n`);
    console.log(finalState.report);
    console.log(`\n=======================================================`);

    if (dryRun) {
      console.log(`\n※ dry-run が指定されているため、DBへの保存はスキップされました。`);
    } else {
      console.log(`\n✔ PostgreSQL (player_reports) への保存が完了しました。`);
    }
  } catch (err) {
    console.error("\n予期しないエラーが発生しました:", err);
    process.exitCode = 1;
  } finally {
    await closePool();
  }
}

main();
