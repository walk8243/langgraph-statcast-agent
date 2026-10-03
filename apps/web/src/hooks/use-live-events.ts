"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import {
  LiveLinescore,
  LivePlay,
  LivePitch,
  LiveEventPayload,
  InningDetail,
} from "@/types/game";

export type ConnectionStatus = "connecting" | "connected" | "disconnected" | "error";

interface UseLiveEventsOptions {
  gamePk: number;
  initialLinescore: LiveLinescore | null;
  initialPlays: LivePlay[];
  initialStatus: string;
  apiBaseUrl?: string;
  autoConnect?: boolean;
}

export function useLiveEvents({
  gamePk,
  initialLinescore,
  initialPlays,
  initialStatus,
  apiBaseUrl,
  autoConnect = true,
}: UseLiveEventsOptions) {
  const [linescore, setLinescore] = useState<LiveLinescore | null>(initialLinescore);
  const [plays, setPlays] = useState<LivePlay[]>(initialPlays);
  const [gameStatus, setGameStatus] = useState<string>(initialStatus);
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>("disconnected");
  const [lastEventTime, setLastEventTime] = useState<Date | null>(null);
  const [reconnectCount, setReconnectCount] = useState<number>(0);
  const [error, setError] = useState<string | null>(null);

  const eventSourceRef = useRef<EventSource | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const isMountedRef = useRef<boolean>(true);
  const connectRef = useRef<() => void>(() => {});

  const resolvedApiUrl =
    apiBaseUrl ||
    process.env.NEXT_PUBLIC_LIVE_API_URL ||
    "http://localhost:8001";

  const connect = useCallback(() => {
    if (typeof window === "undefined" || !gamePk) return;

    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }

    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    setConnectionStatus("connecting");
    setError(null);

    const sseUrl = `${resolvedApiUrl}/api/games/${gamePk}/events`;
    const es = new EventSource(sseUrl);
    eventSourceRef.current = es;

    es.onopen = () => {
      if (!isMountedRef.current) return;
      setConnectionStatus("connected");
      setError(null);
      setReconnectCount(0);
    };

    es.onerror = () => {
      if (!isMountedRef.current) return;
      setConnectionStatus("error");
      setError("SSE 接続が切断されました。再接続を試みています...");
      es.close();
      eventSourceRef.current = null;

      // Exponential backoff reconnect
      setReconnectCount((prev) => {
        const nextCount = prev + 1;
        const delay = Math.min(1000 * Math.pow(1.5, nextCount), 15000);
        reconnectTimeoutRef.current = setTimeout(() => {
          if (isMountedRef.current) {
            connectRef.current();
          }
        }, delay);
        return nextCount;
      });
    };

    // 1. linescore イベント
    es.addEventListener("linescore", (event: MessageEvent) => {
      if (!isMountedRef.current) return;
      try {
        const payload = JSON.parse(event.data) as LiveEventPayload<Record<string, unknown>>;
        const data = (payload.data || {}) as Record<string, unknown>;
        let parsedInnings: InningDetail[] = Array.isArray(data.innings)
          ? (data.innings as InningDetail[])
          : [];
        if (typeof data.innings_json === "string") {
          try {
            parsedInnings = JSON.parse(data.innings_json) as InningDetail[];
          } catch {
            // keep as-is
          }
        } else if (Array.isArray(data.innings_json)) {
          parsedInnings = data.innings_json as InningDetail[];
        }

        setLinescore({
          game_pk: Number(data.game_pk || gamePk),
          current_inning: Number(data.current_inning || 1),
          is_top_inning: Boolean(data.is_top_inning),
          scheduled_innings: Number(data.scheduled_innings || 9),
          balls: Number(data.balls || 0),
          strikes: Number(data.strikes || 0),
          outs: Number(data.outs || 0),
          home_score: Number(data.home_score || 0),
          away_score: Number(data.away_score || 0),
          home_hits: Number(data.home_hits || 0),
          away_hits: Number(data.away_hits || 0),
          home_errors: Number(data.home_errors || 0),
          away_errors: Number(data.away_errors || 0),
          innings: parsedInnings,
        });
        setLastEventTime(new Date());
      } catch (err) {
        console.error("Failed to parse linescore event:", err);
      }
    });

    // 2. play イベント
    es.addEventListener("play", (event: MessageEvent) => {
      if (!isMountedRef.current) return;
      try {
        const payload = JSON.parse(event.data) as LiveEventPayload<Record<string, unknown>>;
        const rawPlay = payload.data;
        if (!rawPlay) return;

        const atBatIndex = Number(rawPlay.at_bat_index);
        setPlays((prevPlays) => {
          const index = prevPlays.findIndex((p) => p.at_bat_index === atBatIndex);
          const updatedPlay: LivePlay = {
            game_pk: Number(rawPlay.game_pk || gamePk),
            at_bat_index: atBatIndex,
            inning: Number(rawPlay.inning || 1),
            half_inning: String(rawPlay.half_inning || "top"),
            is_top_inning: Boolean(rawPlay.is_top_inning),
            batter_id: Number(rawPlay.batter_id),
            batter_name: rawPlay.batter_name ? String(rawPlay.batter_name) : (index >= 0 ? prevPlays[index].batter_name : `打者 ${rawPlay.batter_id}`),
            pitcher_id: Number(rawPlay.pitcher_id),
            pitcher_name: rawPlay.pitcher_name ? String(rawPlay.pitcher_name) : (index >= 0 ? prevPlays[index].pitcher_name : `投手 ${rawPlay.pitcher_id}`),
            first_base_runner_id: rawPlay.first_base_runner_id ? Number(rawPlay.first_base_runner_id) : null,
            second_base_runner_id: rawPlay.second_base_runner_id ? Number(rawPlay.second_base_runner_id) : null,
            third_base_runner_id: rawPlay.third_base_runner_id ? Number(rawPlay.third_base_runner_id) : null,
            event: rawPlay.event ? String(rawPlay.event) : null,
            event_type: rawPlay.event_type ? String(rawPlay.event_type) : null,
            description: rawPlay.description ? String(rawPlay.description) : null,
            rbi: Number(rawPlay.rbi || 0),
            away_score: Number(rawPlay.away_score || 0),
            home_score: Number(rawPlay.home_score || 0),
            is_scoring_play: Boolean(rawPlay.is_scoring_play),
            is_out: Boolean(rawPlay.is_out),
            is_complete: Boolean(rawPlay.is_complete),
            start_time: rawPlay.start_time ? String(rawPlay.start_time) : null,
            end_time: rawPlay.end_time ? String(rawPlay.end_time) : null,
            pitches: index >= 0 ? prevPlays[index].pitches : [],
          };

          if (index >= 0) {
            const next = [...prevPlays];
            next[index] = updatedPlay;
            return next;
          } else {
            return [...prevPlays, updatedPlay];
          }
        });
        setLastEventTime(new Date());
      } catch (err) {
        console.error("Failed to parse play event:", err);
      }
    });

    // 3. pitch イベント
    es.addEventListener("pitch", (event: MessageEvent) => {
      if (!isMountedRef.current) return;
      try {
        const payload = JSON.parse(event.data) as LiveEventPayload<Record<string, unknown>>;
        const rawPitch = payload.data;
        if (!rawPitch) return;

        const atBatIndex = Number(rawPitch.at_bat_index);
        const pitchNumber = Number(rawPitch.pitch_number);

        const newPitch: LivePitch = {
          game_pk: Number(rawPitch.game_pk || gamePk),
          at_bat_index: atBatIndex,
          pitch_number: pitchNumber,
          play_id: rawPitch.play_id ? String(rawPitch.play_id) : null,
          pitch_type: rawPitch.pitch_type ? String(rawPitch.pitch_type) : null,
          pitch_name: rawPitch.pitch_name ? String(rawPitch.pitch_name) : null,
          start_speed: rawPitch.start_speed !== null && rawPitch.start_speed !== undefined ? Number(rawPitch.start_speed) : null,
          end_speed: rawPitch.end_speed !== null && rawPitch.end_speed !== undefined ? Number(rawPitch.end_speed) : null,
          zone: rawPitch.zone !== null && rawPitch.zone !== undefined ? Number(rawPitch.zone) : null,
          p_x: rawPitch.p_x !== null && rawPitch.p_x !== undefined ? Number(rawPitch.p_x) : null,
          p_z: rawPitch.p_z !== null && rawPitch.p_z !== undefined ? Number(rawPitch.p_z) : null,
          spin_rate: rawPitch.spin_rate !== null && rawPitch.spin_rate !== undefined ? Number(rawPitch.spin_rate) : null,
          spin_direction: rawPitch.spin_direction !== null && rawPitch.spin_direction !== undefined ? Number(rawPitch.spin_direction) : null,
          break_angle: rawPitch.break_angle !== null && rawPitch.break_angle !== undefined ? Number(rawPitch.break_angle) : null,
          break_vertical: rawPitch.break_vertical !== null && rawPitch.break_vertical !== undefined ? Number(rawPitch.break_vertical) : null,
          break_vertical_induced: rawPitch.break_vertical_induced !== null && rawPitch.break_vertical_induced !== undefined ? Number(rawPitch.break_vertical_induced) : null,
          break_horizontal: rawPitch.break_horizontal !== null && rawPitch.break_horizontal !== undefined ? Number(rawPitch.break_horizontal) : null,
          call_code: rawPitch.call_code ? String(rawPitch.call_code) : null,
          call_description: rawPitch.call_description ? String(rawPitch.call_description) : null,
          description: rawPitch.description ? String(rawPitch.description) : null,
          balls: Number(rawPitch.balls || 0),
          strikes: Number(rawPitch.strikes || 0),
          outs: Number(rawPitch.outs || 0),
          is_strike: Boolean(rawPitch.is_strike),
          is_ball: Boolean(rawPitch.is_ball),
          is_in_play: Boolean(rawPitch.is_in_play),
          is_pitch: Boolean(rawPitch.is_pitch),
          launch_speed: rawPitch.launch_speed !== null && rawPitch.launch_speed !== undefined ? Number(rawPitch.launch_speed) : null,
          launch_angle: rawPitch.launch_angle !== null && rawPitch.launch_angle !== undefined ? Number(rawPitch.launch_angle) : null,
          total_distance: rawPitch.total_distance !== null && rawPitch.total_distance !== undefined ? Number(rawPitch.total_distance) : null,
          trajectory: rawPitch.trajectory ? String(rawPitch.trajectory) : null,
          hardness: rawPitch.hardness ? String(rawPitch.hardness) : null,
          hit_location: rawPitch.hit_location ? String(rawPitch.hit_location) : null,
          coord_x: rawPitch.coord_x !== null && rawPitch.coord_x !== undefined ? Number(rawPitch.coord_x) : null,
          coord_y: rawPitch.coord_y !== null && rawPitch.coord_y !== undefined ? Number(rawPitch.coord_y) : null,
          start_time: rawPitch.start_time ? String(rawPitch.start_time) : null,
          end_time: rawPitch.end_time ? String(rawPitch.end_time) : null,
        };

        setPlays((prevPlays) => {
          const playIndex = prevPlays.findIndex((p) => p.at_bat_index === atBatIndex);
          if (playIndex >= 0) {
            const play = prevPlays[playIndex];
            const existingPitches = [...play.pitches];
            const pIdx = existingPitches.findIndex((p) => p.pitch_number === pitchNumber);
            if (pIdx >= 0) {
              existingPitches[pIdx] = newPitch;
            } else {
              existingPitches.push(newPitch);
            }
            existingPitches.sort((a, b) => a.pitch_number - b.pitch_number);

            const next = [...prevPlays];
            next[playIndex] = {
              ...play,
              pitches: existingPitches,
            };
            return next;
          } else {
            // 打席がまだ作成されていない場合のフォールバック作成
            return [
              ...prevPlays,
              {
                game_pk: Number(rawPitch.game_pk || gamePk),
                at_bat_index: atBatIndex,
                inning: 1,
                half_inning: "top",
                is_top_inning: true,
                batter_id: 0,
                batter_name: "現在打席中",
                pitcher_id: 0,
                pitcher_name: "登板中",
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
                pitches: [newPitch],
              },
            ];
          }
        });
        setLastEventTime(new Date());
      } catch (err) {
        console.error("Failed to parse pitch event:", err);
      }
    });

    // 4. game_status イベント
    es.addEventListener("game_status", (event: MessageEvent) => {
      if (!isMountedRef.current) return;
      try {
        const payload = JSON.parse(event.data) as LiveEventPayload<{ status?: string }>;
        if (payload.data?.status) {
          setGameStatus(payload.data.status);
        }
        setLastEventTime(new Date());
      } catch (err) {
        console.error("Failed to parse game_status event:", err);
      }
    });
  }, [gamePk, resolvedApiUrl]);

  useEffect(() => {
    connectRef.current = connect;
  }, [connect]);

  useEffect(() => {
    isMountedRef.current = true;
    let timer: NodeJS.Timeout | null = null;

    if (autoConnect) {
      timer = setTimeout(() => {
        if (isMountedRef.current) {
          connect();
        }
      }, 0);
    }

    return () => {
      isMountedRef.current = false;
      if (timer) {
        clearTimeout(timer);
      }
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
        eventSourceRef.current = null;
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
        reconnectTimeoutRef.current = null;
      }
    };
  }, [autoConnect, connect]);

  // 最新打席および最新投球の算出
  const currentPlay = plays.length > 0 ? plays[plays.length - 1] : null;
  const latestPitch =
    currentPlay && currentPlay.pitches.length > 0
      ? currentPlay.pitches[currentPlay.pitches.length - 1]
      : null;

  return {
    linescore,
    plays,
    gameStatus,
    connectionStatus,
    lastEventTime,
    reconnectCount,
    error,
    reconnect: connect,
    currentPlay,
    latestPitch,
  };
}
