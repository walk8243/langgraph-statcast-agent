/**
 * Live Worker CLI エントリポイント
 */

import "dotenv/config";
import { LiveGameWorker } from "./worker.js";

function parseArgs(args: string[]) {
  let gamePkArg: string | undefined = undefined;
  let interval = parseFloat(process.env.POLL_INTERVAL_SECONDS || "10.0");
  let once = false;
  let autoDiscover = true;

  for (let i = 0; i < args.length; i++) {
    const arg = args[i];
    if (arg === "--game-pk" && i + 1 < args.length) {
      gamePkArg = args[++i];
    } else if (arg === "--interval" && i + 1 < args.length) {
      interval = parseFloat(args[++i]);
    } else if (arg === "--once") {
      once = true;
    } else if (arg === "--no-auto-discover") {
      autoDiscover = false;
    } else if (arg === "--help" || arg === "-h") {
      console.log(`
Usage: node dist/index.js [options]

MLB Stats API Real-time Live Feed Poller Worker

Options:
  --game-pk <ids>       対象試合 ID (カンマ区切りまたは単一数値、例: 824703 または 824703,824704)
  --interval <seconds>  ポーリング間隔 (秒, デフォルト: 10.0)
  --once                1回のみポーリングを実行して終了する (テスト用)
  --no-auto-discover    PostgreSQL games テーブルからの進行中試合自動検知を無効化する
  --help, -h            ヘルプを表示する
      `);
      process.exit(0);
    }
  }

  return { gamePkArg, interval, once, autoDiscover };
}

async function main() {
  const { gamePkArg, interval, once, autoDiscover } = parseArgs(process.argv.slice(2));

  const targetGamePks: number[] = [];
  const rawPks = gamePkArg || process.env.TARGET_GAME_PKS || "";
  if (rawPks) {
    for (const p of rawPks.split(",")) {
      const trimmed = p.trim();
      if (/^\d+$/.test(trimmed)) {
        targetGamePks.push(parseInt(trimmed, 10));
      }
    }
  }

  const worker = new LiveGameWorker({
    pollIntervalSeconds: interval,
    targetGamePks,
    autoDiscover,
  });

  const sigHandler = (sig: string) => {
    console.log(`Received ${sig}, stopping worker...`);
    worker.stop();
  };

  process.on("SIGINT", () => sigHandler("SIGINT"));
  process.on("SIGTERM", () => sigHandler("SIGTERM"));

  if (once) {
    console.log("Running single iteration...");
    const results = await worker.runOnce();
    console.log("Single iteration finished. Results:", Object.fromEntries(results));
  } else {
    await worker.run();
  }
}

main().catch((err) => {
  console.error("Fatal worker error:", err);
  process.exit(1);
});
