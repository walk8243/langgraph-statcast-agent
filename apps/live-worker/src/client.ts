/**
 * MLB Stats API クライアントモジュール (feed/live 取得および日程取得)
 */

import axios, { AxiosInstance } from "axios";

export const MLB_STATS_API_BASE_URL = "https://statsapi.mlb.com";

export class MlbLiveClient {
  private client: AxiosInstance;
  private baseUrl: string;

  constructor(baseUrl: string = MLB_STATS_API_BASE_URL, timeoutMs: number = 15000) {
    this.baseUrl = baseUrl.replace(/\/+$/, "");
    this.client = axios.create({
      baseURL: this.baseUrl,
      timeout: timeoutMs,
      headers: {
        "Accept-Encoding": "gzip",
        "User-Agent": "statcast-live-worker/0.1.0",
      },
    });
  }

  /**
   * 指定した gamePk の feed/live データを取得する
   */
  async fetchLiveFeed(gamePk: number, timecode?: string): Promise<Record<string, any>> {
    const params: Record<string, any> = {};
    if (timecode) {
      params.timecode = timecode;
    }

    const response = await this.client.get(`/api/v1.1/game/${gamePk}/feed/live`, {
      params,
    });
    return response.data;
  }

  /**
   * 指定日 (未指定時は本日) の MLB 試合一覧を取得する
   */
  async fetchTodaySchedule(targetDate?: string, sportId: number = 1): Promise<Record<string, any>[]> {
    const params: Record<string, any> = { sportId };
    if (targetDate) {
      params.date = targetDate;
    }

    const response = await this.client.get("/api/v1/schedule", { params });
    const dates = response.data?.dates || [];
    const games: Record<string, any>[] = [];

    for (const d of dates) {
      for (const g of d.games || []) {
        games.push(g);
      }
    }
    return games;
  }
}
