import { describe, expect, it } from "vitest";
import {
  extractDiff,
  extractGameInfo,
  extractLinescoreRecord,
  extractPlayersFromFeed,
  LiveGameTracker,
} from "../src/extractor.js";

const mockFeedData = {
  gamePk: 824703,
  gameData: {
    game: { pk: 824703, type: "R", season: "2024" },
    datetime: { dateTime: "2024-04-26T23:10:00Z" },
    status: { abstractGameState: "Live", detailedState: "In Progress", statusCode: "I" },
    teams: {
      away: { id: 111, name: "Boston Red Sox" },
      home: { id: 112, name: "Chicago Cubs" },
    },
    players: {
      ID660271: { id: 660271, fullName: "Shohei Ohtani", currentTeam: { id: 111 } },
      ID543037: { id: 543037, fullName: "Gerrit Cole", currentTeam: { id: 112 } },
    },
  },
  liveData: {
    linescore: {
      currentInning: 1,
      isTopInning: true,
      scheduledInnings: 9,
      balls: 1,
      strikes: 2,
      outs: 0,
      teams: {
        away: { runs: 0, hits: 1, errors: 0 },
        home: { runs: 0, hits: 0, errors: 0 },
      },
      innings: [
        {
          num: 1,
          ordinalNum: "1st",
          away: { runs: 0, hits: 1, errors: 0 },
          home: { runs: 0, hits: 0, errors: 0 },
        },
      ],
    },
    plays: {
      allPlays: [
        {
          about: {
            atBatIndex: 0,
            inning: 1,
            halfInning: "top",
            isTopInning: true,
            startTime: "2024-04-26T23:10:15Z",
            endTime: null,
            isComplete: false,
            isScoringPlay: false,
            hasOut: false,
          },
          result: {
            type: "atBat",
            event: null,
            eventType: null,
            description: null,
            rbi: 0,
            awayScore: 0,
            homeScore: 0,
            isOut: false,
          },
          matchup: {
            batter: { id: 660271, fullName: "Shohei Ohtani" },
            pitcher: { id: 543037, fullName: "Gerrit Cole" },
            postOnFirst: null,
            postOnSecond: null,
            postOnThird: null,
          },
          playEvents: [
            {
              index: 0,
              pitchNumber: 1,
              playId: "uuid-pitch-1",
              isPitch: true,
              details: {
                call: { code: "B", description: "Ball" },
                description: "Ball",
                type: { code: "FF", description: "Four-Seam Fastball" },
                isStrike: false,
                isBall: true,
                isInPlay: false,
              },
              pitchData: {
                startSpeed: 98.5,
                endSpeed: 91.2,
                zone: 14,
                coordinates: { p_x: -0.85, p_z: 1.25, x: 80.0, y: 180.0 },
                breaks: {
                  spinRate: 2450.0,
                  spinDirection: 210,
                  breakAngle: 2.1,
                  breakVertical: 12.4,
                  breakVerticalInduced: 16.5,
                  breakHorizontal: 8.2,
                },
              },
              count: { balls: 1, strikes: 0, outs: 0 },
              startTime: "2024-04-26T23:10:20Z",
            },
          ],
        },
      ],
    },
  },
};

describe("extractor", () => {
  it("extractGameInfo parses basic game fields correctly", () => {
    const info = extractGameInfo(mockFeedData);
    expect(info.game_pk).toBe(824703);
    expect(info.season).toBe(2024);
    expect(info.status).toBe("In Progress");
    expect(info.abstract_state).toBe("Live");
    expect(info.home_team_id).toBe(112);
    expect(info.away_team_id).toBe(111);
    expect(info.home_score).toBe(0);
    expect(info.away_score).toBe(0);
  });

  it("extractPlayersFromFeed parses all player records", () => {
    const players = extractPlayersFromFeed(mockFeedData);
    expect(players.length).toBe(2);
    const pids = new Set(players.map((p) => p.player_id));
    expect(pids.has(660271)).toBe(true);
    expect(pids.has(543037)).toBe(true);
  });

  it("extractLinescoreRecord creates record and hash with normalized innings", () => {
    const { record, hashKey } = extractLinescoreRecord(824703, mockFeedData);
    expect(record.game_pk).toBe(824703);
    expect(record.current_inning).toBe(1);
    expect(record.balls).toBe(1);
    expect(record.strikes).toBe(2);
    expect(typeof hashKey).toBe("string");

    const parsedInnings = JSON.parse(record.innings_json);
    expect(parsedInnings.length).toBe(1);
    expect(parsedInnings[0].num).toBe(1);
    expect(parsedInnings[0].inning).toBe(1);
    expect(parsedInnings[0].away.runs).toBe(0);
    expect(parsedInnings[0].home.runs).toBe(0);
  });

  it("extractDiff correctly detects initial state and increments", () => {
    const tracker = new LiveGameTracker(824703);

    // 1回目 (初回取得): linescore, 1 play, 1 pitch
    const diff1 = extractDiff(mockFeedData, tracker);
    expect(diff1.linescore).not.toBeNull();
    expect(diff1.plays.length).toBe(1);
    expect(diff1.pitches.length).toBe(1);
    expect(diff1.events.length).toBe(3);

    // 2回目 (差分なし)
    const diff2 = extractDiff(mockFeedData, tracker);
    expect(diff2.linescore).toBeNull();
    expect(diff2.plays.length).toBe(0);
    expect(diff2.pitches.length).toBe(0);
    expect(diff2.events.length).toBe(0);

    // 3回目 (2球目追加)
    const feedData3 = JSON.parse(JSON.stringify(mockFeedData));
    feedData3.liveData.linescore.balls = 2;
    feedData3.liveData.plays.allPlays[0].playEvents.push({
      index: 1,
      pitchNumber: 2,
      playId: "uuid-pitch-2",
      isPitch: true,
      details: {
        call: { code: "C", description: "Called Strike" },
        description: "Called Strike",
        type: { code: "SL", description: "Slider" },
        isStrike: true,
        isBall: false,
        isInPlay: false,
      },
      pitchData: {
        startSpeed: 88.0,
        endSpeed: 82.0,
        zone: 3,
        coordinates: { p_x: 0.45, p_z: 2.85, x: 140.0, y: 130.0 },
        breaks: {
          spinRate: 2600.0,
          spinDirection: 90,
          breakAngle: -5.2,
          breakVertical: 35.0,
          breakHorizontal: -12.0,
        },
      },
      count: { balls: 2, strikes: 1, outs: 0 },
      startTime: "2024-04-26T23:10:45Z",
    });

    const diff3 = extractDiff(feedData3, tracker);
    expect(diff3.linescore).not.toBeNull();
    expect(diff3.linescore?.balls).toBe(2);
    expect(diff3.pitches.length).toBe(1);
    expect(diff3.pitches[0].pitch_number).toBe(2);
    expect(diff3.pitches[0].pitch_type).toBe("SL");
    expect(diff3.events.length).toBe(2); // linescore, pitch
  });
});
