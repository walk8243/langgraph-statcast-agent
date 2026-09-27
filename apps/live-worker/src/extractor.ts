/**
 * MLB Stats API feed/live からのデータ抽出および差分検知エンジン
 */

import {
  DiffResult,
  GameInfo,
  LiveEvent,
  LiveLinescoreRecord,
  LivePitchRecord,
  LivePlayRecord,
  PlayerRecord,
} from "./types.js";

export class LiveGameTracker {
  game_pk: number;
  last_status: string | null = null;
  last_abstract_state: string | null = null;
  last_linescore_hash: string | null = null;
  last_plays_state: Map<number, string> = new Map();
  known_pitches: Set<string> = new Set();

  constructor(gamePk: number) {
    this.game_pk = gamePk;
  }
}

function parseDate(dtStr: string | null | undefined): Date | null {
  if (!dtStr) return null;
  const d = new Date(dtStr);
  return isNaN(d.getTime()) ? null : d;
}

function safeFloat(val: any): number | null {
  if (val === null || val === undefined) return null;
  const num = parseFloat(val);
  return isNaN(num) ? null : num;
}

function safeInt(val: any): number | null {
  if (val === null || val === undefined) return null;
  const num = parseInt(val, 10);
  return isNaN(num) ? null : num;
}

export function extractGameInfo(feedData: Record<string, any>): GameInfo {
  const gameData = feedData.gameData || {};
  const gameMeta = gameData.game || {};
  const gamePk = safeInt(gameMeta.pk) || safeInt(feedData.gamePk) || 0;
  const statusInfo = gameData.status || {};
  const teamsInfo = gameData.teams || {};
  const datetimeInfo = gameData.datetime || {};

  const homeTeam = teamsInfo.home || {};
  const awayTeam = teamsInfo.away || {};

  const liveLinescore = feedData.liveData?.linescore || {};
  const lsTeams = liveLinescore.teams || {};

  let gameDateTime = parseDate(datetimeInfo.dateTime || datetimeInfo.originalDate);
  if (!gameDateTime) {
    gameDateTime = new Date();
  }

  let seasonVal = safeInt(gameMeta.season);
  if (!seasonVal && gameDateTime) {
    seasonVal = gameDateTime.getUTCFullYear();
  }

  return {
    game_pk: gamePk,
    game_date_time: gameDateTime,
    season: seasonVal || 2024,
    game_type: gameMeta.type || "R",
    status: statusInfo.detailedState || "Unknown",
    status_code: statusInfo.statusCode || null,
    abstract_state: statusInfo.abstractGameState || "Live",
    home_team_id: safeInt(homeTeam.id),
    away_team_id: safeInt(awayTeam.id),
    home_score: safeInt(lsTeams.home?.runs),
    away_score: safeInt(lsTeams.away?.runs),
  };
}

export function extractPlayersFromFeed(feedData: Record<string, any>): PlayerRecord[] {
  const playersData = feedData.gameData?.players || {};
  const result: PlayerRecord[] = [];

  for (const key of Object.keys(playersData)) {
    const pinfo = playersData[key];
    const pid = safeInt(pinfo.id);
    if (!pid) continue;

    const fullName = pinfo.fullName || pinfo.boxscoreName || `Player ${pid}`;
    const currentTeam = pinfo.currentTeam || {};
    const teamId = safeInt(currentTeam.id);

    result.push({
      player_id: pid,
      name_en: fullName,
      team_id: teamId,
    });
  }
  return result;
}

export function extractLinescoreRecord(
  gamePk: number,
  feedData: Record<string, any>
): { record: LiveLinescoreRecord; hashKey: string } {
  const ls = feedData.liveData?.linescore || {};
  const teams = ls.teams || {};
  const home = teams.home || {};
  const away = teams.away || {};

  const currentInning = safeInt(ls.currentInning) ?? 1;
  const isTopInning = ls.isTopInning !== undefined ? Boolean(ls.isTopInning) : true;
  const scheduledInnings = safeInt(ls.scheduledInnings) ?? 9;
  const balls = safeInt(ls.balls) ?? 0;
  const strikes = safeInt(ls.strikes) ?? 0;
  const outs = safeInt(ls.outs) ?? 0;

  const homeScore = safeInt(home.runs) ?? 0;
  const awayScore = safeInt(away.runs) ?? 0;
  const homeHits = safeInt(home.hits) ?? 0;
  const awayHits = safeInt(away.hits) ?? 0;
  const homeErrors = safeInt(home.errors) ?? 0;
  const awayErrors = safeInt(away.errors) ?? 0;

  const inningsRaw = ls.innings || [];
  const inningsJson = JSON.stringify(inningsRaw);

  const hashKey = `${currentInning}:${isTopInning}:${balls}:${strikes}:${outs}:${homeScore}:${awayScore}:${homeHits}:${awayHits}:${homeErrors}:${awayErrors}:${inningsRaw.length}`;

  const record: LiveLinescoreRecord = {
    game_pk: gamePk,
    current_inning: currentInning,
    is_top_inning: isTopInning,
    scheduled_innings: scheduledInnings,
    balls,
    strikes,
    outs,
    home_score: homeScore,
    away_score: awayScore,
    home_hits: homeHits,
    away_hits: awayHits,
    home_errors: homeErrors,
    away_errors: awayErrors,
    innings_json: inningsJson,
  };

  return { record, hashKey };
}

export function extractPlayRecord(gamePk: number, play: Record<string, any>): LivePlayRecord {
  const about = play.about || {};
  const result = play.result || {};
  const matchup = play.matchup || {};

  const atBatIndex = safeInt(about.atBatIndex) ?? 0;
  const inning = safeInt(about.inning) ?? 1;
  const halfInning = String(about.halfInning || "top");
  const isTopInning = about.isTopInning !== undefined ? Boolean(about.isTopInning) : true;

  const batterId = safeInt(matchup.batter?.id) ?? 0;
  const pitcherId = safeInt(matchup.pitcher?.id) ?? 0;

  const firstRunner = matchup.postOnFirst || {};
  const secondRunner = matchup.postOnSecond || {};
  const thirdRunner = matchup.postOnThird || {};

  return {
    game_pk: gamePk,
    at_bat_index: atBatIndex,
    inning,
    half_inning: halfInning,
    is_top_inning: isTopInning,
    batter_id: batterId,
    pitcher_id: pitcherId,
    first_base_runner_id: safeInt(firstRunner.id),
    second_base_runner_id: safeInt(secondRunner.id),
    third_base_runner_id: safeInt(thirdRunner.id),
    event: result.event || null,
    event_type: result.eventType || null,
    description: result.description || null,
    rbi: safeInt(result.rbi) ?? 0,
    away_score: safeInt(result.awayScore) ?? 0,
    home_score: safeInt(result.homeScore) ?? 0,
    is_scoring_play: Boolean(about.isScoringPlay),
    is_out: Boolean(result.isOut) || Boolean(about.hasOut),
    is_complete: Boolean(about.isComplete),
    start_time: parseDate(about.startTime),
    end_time: parseDate(about.endTime),
  };
}

export function extractPitchRecord(
  gamePk: number,
  atBatIndex: number,
  pe: Record<string, any>
): LivePitchRecord | null {
  const isPitch = pe.isPitch;
  const pitchNumber = safeInt(pe.pitchNumber);

  if (!isPitch && pitchNumber === null) {
    return null;
  }

  const pitchNum = pitchNumber ?? (safeInt(pe.index) ?? 0) + 1;
  const playId = pe.playId || null;

  const details = pe.details || {};
  const typeInfo = details.type || {};
  const callInfo = details.call || {};

  const pitchType = typeInfo.code || null;
  const pitchName = typeInfo.description || null;

  const pitchData = pe.pitchData || {};
  const coords = pitchData.coordinates || {};
  const breaks = pitchData.breaks || {};
  const hitData = pe.hitData || {};
  const hitCoords = hitData.coordinates || {};
  const count = pe.count || {};

  const px = safeFloat(coords.p_x !== undefined ? coords.p_x : coords.pX);
  const pz = safeFloat(coords.p_z !== undefined ? coords.p_z : coords.pZ);
  const coordX = safeFloat(hitCoords.coordX !== undefined ? hitCoords.coordX : coords.x);
  const coordY = safeFloat(hitCoords.coordY !== undefined ? hitCoords.coordY : coords.y);

  return {
    game_pk: gamePk,
    at_bat_index: atBatIndex,
    pitch_number: pitchNum,
    play_id: playId,
    pitch_type: pitchType,
    pitch_name: pitchName,
    start_speed: safeFloat(pitchData.startSpeed),
    end_speed: safeFloat(pitchData.endSpeed),
    zone: safeInt(pitchData.zone),
    p_x: px,
    p_z: pz,
    spin_rate: safeFloat(breaks.spinRate),
    spin_direction: safeInt(breaks.spinDirection),
    break_angle: safeFloat(breaks.breakAngle),
    break_vertical: safeFloat(breaks.breakVertical !== undefined ? breaks.breakVertical : breaks.breakLength),
    break_vertical_induced: safeFloat(breaks.breakVerticalInduced),
    break_horizontal: safeFloat(breaks.breakHorizontal),
    call_code: callInfo.code || null,
    call_description: callInfo.description || null,
    description: details.description || null,
    balls: safeInt(count.balls) ?? 0,
    strikes: safeInt(count.strikes) ?? 0,
    outs: safeInt(count.outs) ?? 0,
    is_strike: Boolean(details.isStrike),
    is_ball: Boolean(details.isBall),
    is_in_play: Boolean(details.isInPlay),
    is_pitch: true,
    launch_speed: safeFloat(hitData.launchSpeed),
    launch_angle: safeFloat(hitData.launchAngle),
    total_distance: safeInt(hitData.totalDistance),
    trajectory: hitData.trajectory || null,
    hardness: hitData.hardness || null,
    hit_location: hitData.location !== undefined ? String(hitData.location) : null,
    coord_x: coordX,
    coord_y: coordY,
    start_time: parseDate(pe.startTime),
    end_time: parseDate(pe.endTime),
  };
}

export function extractDiff(
  feedData: Record<string, any>,
  tracker: LiveGameTracker
): DiffResult {
  const gameInfo = extractGameInfo(feedData);
  const gamePk = tracker.game_pk;
  const players = extractPlayersFromFeed(feedData);

  const events: LiveEvent[] = [];
  const nowIso = new Date().toISOString();

  // 1. 試合ステータス差分
  const currentStatus = gameInfo.status;
  const currentAbstract = gameInfo.abstract_state;
  if (
    tracker.last_status !== null &&
    (tracker.last_status !== currentStatus || tracker.last_abstract_state !== currentAbstract)
  ) {
    events.push({
      game_pk: gamePk,
      event_type: "game_status",
      timestamp: nowIso,
      data: {
        game_pk: gamePk,
        status: currentStatus,
        abstract_state: currentAbstract,
        home_score: gameInfo.home_score,
        away_score: gameInfo.away_score,
      },
    });
  }
  tracker.last_status = currentStatus;
  tracker.last_abstract_state = currentAbstract;

  // 2. ラインスコア差分
  const { record: linescoreRecord, hashKey: linescoreHash } = extractLinescoreRecord(gamePk, feedData);
  let changedLinescore: LiveLinescoreRecord | null = null;
  if (tracker.last_linescore_hash !== linescoreHash) {
    tracker.last_linescore_hash = linescoreHash;
    changedLinescore = linescoreRecord;
    events.push({
      game_pk: gamePk,
      event_type: "linescore",
      timestamp: nowIso,
      data: linescoreRecord,
    });
  }

  // 3. 打席 & 投球差分
  const allPlays = feedData.liveData?.plays?.allPlays || [];
  const changedPlays: LivePlayRecord[] = [];
  const newPitches: LivePitchRecord[] = [];

  for (const play of allPlays) {
    const atBatIndex = safeInt(play.about?.atBatIndex);
    if (atBatIndex === null) continue;

    const playRecord = extractPlayRecord(gamePk, play);
    const playSignature = `${playRecord.is_complete}:${playRecord.event}:${playRecord.description}`;

    const prevSignature = tracker.last_plays_state.get(atBatIndex);
    if (!prevSignature || prevSignature !== playSignature) {
      tracker.last_plays_state.set(atBatIndex, playSignature);
      changedPlays.push(playRecord);
      events.push({
        game_pk: gamePk,
        event_type: "play",
        timestamp: nowIso,
        data: playRecord,
      });
    }

    // 投球差分
    const playEvents = play.playEvents || [];
    for (const pe of playEvents) {
      const pitchRecord = extractPitchRecord(gamePk, atBatIndex, pe);
      if (!pitchRecord) continue;

      const pitchKey = `${atBatIndex}:${pitchRecord.pitch_number}`;
      if (!tracker.known_pitches.has(pitchKey)) {
        tracker.known_pitches.add(pitchKey);
        newPitches.push(pitchRecord);
        events.push({
          game_pk: gamePk,
          event_type: "pitch",
          timestamp: nowIso,
          data: pitchRecord,
        });
      }
    }
  }

  return {
    game_pk: gamePk,
    game_info: gameInfo,
    players,
    linescore: changedLinescore,
    plays: changedPlays,
    pitches: newPitches,
    events,
  };
}
