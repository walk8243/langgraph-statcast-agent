/**
 * 常駐型ポーラーワーカーモジュール (LiveGameWorker)
 */

import { Pool } from "pg";
import { MlbLiveClient } from "./client.js";
import { createDbPool, findInProgressGames, initializeTables, saveDiffResult } from "./db.js";
import { extractDiff, LiveGameTracker } from "./extractor.js";
import { LiveEventPublisher } from "./publisher.js";

export interface LiveGameWorkerOptions {
  pollIntervalSeconds?: number;
  targetGamePks?: number[];
  autoDiscover?: boolean;
  client?: MlbLiveClient;
  publisher?: LiveEventPublisher;
  dbPool?: Pool;
}

export class LiveGameWorker {
  public pollIntervalSeconds: number;
  public targetGamePks: Set<number>;
  public autoDiscover: boolean;

  private client: MlbLiveClient;
  private publisher: LiveEventPublisher;
  private pool: Pool;
  private running = false;
  private trackers: Map<number, LiveGameTracker> = new Map();
  private tablesInitialized = false;

  constructor(options?: LiveGameWorkerOptions) {
    this.pollIntervalSeconds = options?.pollIntervalSeconds ?? 10.0;
    this.targetGamePks = new Set(options?.targetGamePks || []);
    this.autoDiscover = options?.autoDiscover ?? true;

    this.client = options?.client || new MlbLiveClient();
    this.publisher = options?.publisher || new LiveEventPublisher();
    this.pool = options?.dbPool || createDbPool();
  }

  private async ensureTables(): Promise<void> {
    if (!this.tablesInitialized) {
      try {
        await initializeTables(this.pool);
        this.tablesInitialized = true;
      } catch (err) {
        console.warn("Failed to initialize tables:", err);
      }
    }
  }

  public stop(): void {
    console.log("Worker stop requested.");
    this.running = false;
  }

  /**
   * 単一試合の feed/live を取得・差分抽出し、DB永続化およびPub/Sub発行を行う
   */
  async processGame(gamePk: number): Promise<number> {
    let tracker = this.trackers.get(gamePk);
    if (!tracker) {
      tracker = new LiveGameTracker(gamePk);
      this.trackers.set(gamePk, tracker);
    }

    let feedData: Record<string, any>;
    try {
      feedData = await this.client.fetchLiveFeed(gamePk);
    } catch (error) {
      console.warn(`Failed to fetch live feed for game ${gamePk}:`, error);
      return 0;
    }

    const diff = extractDiff(feedData, tracker);

    const hasChanges =
      diff.linescore !== null ||
      diff.plays.length > 0 ||
      diff.pitches.length > 0 ||
      diff.events.length > 0;

    if (hasChanges) {
      await this.ensureTables();
      await saveDiffResult(this.pool, diff);

      if (diff.events.length > 0) {
        const published = await this.publisher.publishEvents(diff.events);
        console.log(
          `Game ${gamePk}: Extracted ${diff.events.length} events (${diff.linescore ? 1 : 0} linescore, ${diff.plays.length} plays, ${diff.pitches.length} pitches), published ${published}`
        );
        return published;
      }
    }

    return 0;
  }

  /**
   * 監視対象の試合一覧を収集する
   */
  async discoverGames(): Promise<Set<number>> {
    const active = new Set<number>(this.targetGamePks);

    if (this.autoDiscover) {
      try {
        await this.ensureTables();
        const inProgress = await findInProgressGames(this.pool);
        for (const pk of inProgress) {
          active.add(pk);
        }
      } catch (err) {
        console.error("Failed to discover in-progress games from DB:", err);
      }
    }

    return active;
  }

  /**
   * 全対象試合に対して 1 サイクルのみポーリングを実行する (テスト・シミュレーション用)
   */
  async runOnce(): Promise<Map<number, number>> {
    const active = await this.discoverGames();
    const results = new Map<number, number>();
    for (const gamePk of active) {
      const count = await this.processGame(gamePk);
      results.set(gamePk, count);
    }
    return results;
  }

  /**
   * 常駐ポーリングループを開始する
   */
  async run(): Promise<void> {
    this.running = true;
    console.log(
      `Starting LiveGameWorker (interval=${this.pollIntervalSeconds}s, targets=${Array.from(this.targetGamePks)}, autoDiscover=${this.autoDiscover})`
    );

    while (this.running) {
      const startTime = Date.now();
      const activeGames = await this.discoverGames();

      if (activeGames.size === 0) {
        // 対象試合がない場合
      } else {
        for (const gamePk of activeGames) {
          if (!this.running) break;
          await this.processGame(gamePk);
        }
      }

      const elapsedMs = Date.now() - startTime;
      const sleepMs = Math.max(0, this.pollIntervalSeconds * 1000 - elapsedMs);

      // 短い単位でスリープしてSIGINTへの応答性を担保
      const endSleep = Date.now() + sleepMs;
      while (this.running && Date.now() < endSleep) {
        const step = Math.min(500, endSleep - Date.now());
        await new Promise((resolve) => setTimeout(resolve, step));
      }
    }

    console.log("LiveGameWorker terminated cleanly.");
    await this.pool.end();
  }
}
