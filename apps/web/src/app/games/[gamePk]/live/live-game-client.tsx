"use client";

import React, { useState } from "react";
import Link from "next/link";
import {
  Title3,
  Subtitle2,
  Body1,
  Body1Strong,
  Caption1,
  Button,
  Card,
  CardHeader,
  Badge,
  Table,
  TableHeader,
  TableRow,
  TableHeaderCell,
  TableBody,
  TableCell,
  makeStyles,
  shorthands,
  tokens,
  Text,
} from "@fluentui/react-components";
import {
  ArrowLeft16Regular,
  ArrowSync24Regular,
  CheckmarkCircle20Filled,
  Warning20Filled,
  ErrorCircle20Filled,
  Sport24Regular,
  Target24Regular,
  ChevronDown20Regular,
  ChevronUp20Regular,
} from "@fluentui/react-icons";

import {
  LiveGameInitialData,
  LivePitch,
} from "@/types/game";
import { useLiveEvents } from "@/hooks/use-live-events";

const useStyles = makeStyles({
  container: {
    maxWidth: "1280px",
    marginLeft: "auto",
    marginRight: "auto",
    ...shorthands.padding("32px", "24px"),
    display: "flex",
    flexDirection: "column",
    rowGap: "24px",
  },
  topNav: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
  },
  headerCard: {
    backgroundColor: tokens.colorNeutralBackground1,
    ...shorthands.border("1px", "solid", tokens.colorNeutralStroke2),
    ...shorthands.borderRadius(tokens.borderRadiusLarge),
    ...shorthands.padding("24px"),
    boxShadow: tokens.shadow4,
    display: "flex",
    flexDirection: "column",
    rowGap: "16px",
    background: "linear-gradient(135deg, #ffffff 0%, #f4f7fb 100%)",
  },
  matchupRow: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    flexWrap: "wrap",
    gap: "16px",
  },
  teamBlock: {
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    minWidth: "160px",
  },
  scoreDisplay: {
    display: "flex",
    alignItems: "center",
    columnGap: "20px",
  },
  scoreNumber: {
    fontSize: "48px",
    fontWeight: "bold",
    lineHeight: "1",
    color: tokens.colorBrandForeground1,
  },
  gameMetaRow: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    flexWrap: "wrap",
    gap: "12px",
    ...shorthands.borderTop("1px", "solid", tokens.colorNeutralStroke2),
    ...shorthands.padding("12px", "0", "0", "0"),
  },
  statusBadgeGroup: {
    display: "flex",
    alignItems: "center",
    columnGap: "10px",
  },
  grid: {
    display: "grid",
    gridTemplateColumns: "1fr",
    gap: "24px",
    "@media (min-width: 992px)": {
      gridTemplateColumns: "3fr 2fr",
    },
  },
  leftColumn: {
    display: "flex",
    flexDirection: "column",
    rowGap: "24px",
  },
  rightColumn: {
    display: "flex",
    flexDirection: "column",
    rowGap: "24px",
  },
  card: {
    backgroundColor: tokens.colorNeutralBackground1,
    ...shorthands.border("1px", "solid", tokens.colorNeutralStroke2),
    ...shorthands.borderRadius(tokens.borderRadiusMedium),
    ...shorthands.padding("20px"),
    boxShadow: tokens.shadow2,
    display: "flex",
    flexDirection: "column",
    rowGap: "16px",
  },
  bsoRow: {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-around",
    flexWrap: "wrap",
    gap: "16px",
    ...shorthands.padding("12px"),
    backgroundColor: tokens.colorNeutralBackground2,
    ...shorthands.borderRadius(tokens.borderRadiusSmall),
  },
  bsoItem: {
    display: "flex",
    alignItems: "center",
    columnGap: "8px",
  },
  countDots: {
    display: "flex",
    columnGap: "6px",
  },
  dot: {
    width: "12px",
    height: "12px",
    borderRadius: "50%",
    backgroundColor: tokens.colorNeutralStroke1,
  },
  ballDotActive: {
    backgroundColor: "#107c41", // Green
  },
  strikeDotActive: {
    backgroundColor: "#c19c00", // Yellow / Gold
  },
  outDotActive: {
    backgroundColor: "#d13438", // Red
  },
  diamondContainer: {
    width: "60px",
    height: "60px",
    position: "relative",
  },
  baseSquare: {
    width: "14px",
    height: "14px",
    position: "absolute",
    transform: "rotate(45deg)",
    ...shorthands.border("2px", "solid", "#666666"),
    backgroundColor: "#ffffff",
  },
  baseActive: {
    backgroundColor: "#d13438",
    ...shorthands.borderColor("#a80000"),
  },
  tableContainer: {
    overflowX: "auto",
  },
  currentInningCol: {
    backgroundColor: tokens.colorBrandBackground2,
    fontWeight: "bold",
  },
  strikeZoneContainer: {
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    rowGap: "16px",
  },
  statcastCardGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fit, minmax(110px, 1fr))",
    gap: "10px",
    width: "100%",
  },
  metricCard: {
    ...shorthands.padding("10px"),
    ...shorthands.borderRadius(tokens.borderRadiusSmall),
    backgroundColor: tokens.colorNeutralBackground2,
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    textAlign: "center",
  },
  playItem: {
    ...shorthands.padding("12px"),
    ...shorthands.borderRadius(tokens.borderRadiusSmall),
    ...shorthands.border("1px", "solid", tokens.colorNeutralStroke2),
    display: "flex",
    flexDirection: "column",
    rowGap: "8px",
  },
  playHeader: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    cursor: "pointer",
  },
  playDetails: {
    ...shorthands.padding("8px", "0", "0", "0"),
    ...shorthands.borderTop("1px", "dashed", tokens.colorNeutralStroke2),
    display: "flex",
    flexDirection: "column",
    rowGap: "6px",
  },
});

interface LiveGameClientProps {
  initialData: LiveGameInitialData;
}

export default function LiveGameClient({ initialData }: LiveGameClientProps) {
  const styles = useStyles();
  const { game } = initialData;

  const {
    linescore,
    plays,
    gameStatus,
    connectionStatus,
    lastEventTime,
    currentPlay,
    latestPitch,
  } = useLiveEvents({
    gamePk: game.game_pk,
    initialLinescore: initialData.linescore,
    initialPlays: initialData.plays,
    initialStatus: game.status,
  });

  const [expandedPlayIndex, setExpandedPlayIndex] = useState<number | null>(
    plays.length > 0 ? plays[plays.length - 1].at_bat_index : null
  );

  const [selectedPitch, setSelectedPitch] = useState<LivePitch | null>(null);

  // Active pitch for Statcast metrics view
  const activePitch = selectedPitch || latestPitch;

  // Inning string (e.g. "9回表", "試合終了", etc.)
  const currentInningLabel = linescore
    ? `${linescore.current_inning}回${linescore.is_top_inning ? "表" : "裏"}`
    : "試合前";

  // Scoreboard innings calculation
  const totalInningsCount = Math.max(
    linescore?.scheduled_innings || 9,
    linescore?.innings?.length || 9,
    linescore?.current_inning || 9
  );
  const inningsHeaderArray = Array.from({ length: totalInningsCount }, (_, i) => i + 1);

  // Runner state from current play
  const hasRunner1B = Boolean(currentPlay?.first_base_runner_id);
  const hasRunner2B = Boolean(currentPlay?.second_base_runner_id);
  const hasRunner3B = Boolean(currentPlay?.third_base_runner_id);

  // Pitch coordinate conversion for Strike Zone
  // Rulebook zone: approx x: [-0.83, 0.83], z: [1.5, 3.5]
  const convertPitchCoords = (pitch: LivePitch) => {
    let cx = 120;
    let cy = 135;

    if (pitch.p_x !== null && pitch.p_z !== null) {
      // SVG viewBox is 0 0 240 270. Zone center is (120, 135), width 100, height 120
      cx = 120 + (pitch.p_x / 0.83) * 50;
      cy = 135 - ((pitch.p_z - 2.5) / 1.0) * 60;
    } else if (pitch.zone !== null) {
      // Fallback for zone 1-9 & out of zone 11-14
      const z = pitch.zone;
      if (z >= 1 && z <= 9) {
        const col = (z - 1) % 3;
        const row = Math.floor((z - 1) / 3);
        cx = 87 + col * 33;
        cy = 95 + row * 40;
      } else if (z === 11) {
        cx = 50; cy = 60;
      } else if (z === 12) {
        cx = 190; cy = 60;
      } else if (z === 13) {
        cx = 50; cy = 210;
      } else if (z === 14) {
        cx = 190; cy = 210;
      }
    }

    return {
      cx: Math.max(15, Math.min(225, cx)),
      cy: Math.max(15, Math.min(255, cy)),
    };
  };

  const getPitchColor = (pitch: LivePitch) => {
    if (pitch.is_strike) return "#d13438"; // Red strike
    if (pitch.is_ball) return "#107c41"; // Green ball
    if (pitch.is_in_play) return "#0078d4"; // Blue in play
    return "#888888";
  };

  // Connection badge color & icon
  const renderConnectionBadge = () => {
    switch (connectionStatus) {
      case "connected":
        return (
          <Badge appearance="filled" color="success" icon={<CheckmarkCircle20Filled />}>
            リアルタイム接続中
          </Badge>
        );
      case "connecting":
        return (
          <Badge appearance="filled" color="warning" icon={<ArrowSync24Regular />}>
            接続中...
          </Badge>
        );
      case "error":
        return (
          <Badge appearance="filled" color="danger" icon={<Warning20Filled />}>
            切断 (再試行中)
          </Badge>
        );
      default:
        return (
          <Badge appearance="outline" color="informative" icon={<ErrorCircle20Filled />}>
            未接続
          </Badge>
        );
    }
  };

  return (
    <main className={styles.container}>
      {/* Navigation & Header */}
      <nav className={styles.topNav}>
        <Link href="/games" style={{ textDecoration: "none" }}>
          <Button appearance="subtle" icon={<ArrowLeft16Regular />}>
            試合一覧に戻る
          </Button>
        </Link>
        <div>
          {renderConnectionBadge()}
        </div>
      </nav>

      {/* Main Score & Matchup Header Card */}
      <section className={styles.headerCard}>
        <div className={styles.matchupRow}>
          {/* Away Team */}
          <div className={styles.teamBlock}>
            <Title3>{game.away_team_name}</Title3>
            <Caption1 style={{ color: tokens.colorNeutralForeground3 }}>
              {game.away_team_abbr} (ビジター)
            </Caption1>
          </div>

          {/* Scores & Inning */}
          <div className={styles.scoreDisplay}>
            <span className={styles.scoreNumber}>
              {linescore ? linescore.away_score : game.away_score ?? 0}
            </span>
            <div style={{ textAlign: "center" }}>
              <Badge appearance="filled" color="brand" size="large">
                {currentInningLabel}
              </Badge>
              <div style={{ marginTop: "4px" }}>
                <Caption1>{gameStatus || game.status}</Caption1>
              </div>
            </div>
            <span className={styles.scoreNumber}>
              {linescore ? linescore.home_score : game.home_score ?? 0}
            </span>
          </div>

          {/* Home Team */}
          <div className={styles.teamBlock}>
            <Title3>{game.home_team_name}</Title3>
            <Caption1 style={{ color: tokens.colorNeutralForeground3 }}>
              {game.home_team_abbr} (ホーム)
            </Caption1>
          </div>
        </div>

        {/* Count Bar & Runners */}
        <div className={styles.bsoRow}>
          {/* Balls */}
          <div className={styles.bsoItem}>
            <Text weight="bold">B</Text>
            <div className={styles.countDots}>
              {[1, 2, 3].map((b) => (
                <div
                  key={`b-${b}`}
                  className={`${styles.dot} ${
                    (linescore?.balls || 0) >= b ? styles.ballDotActive : ""
                  }`}
                />
              ))}
            </div>
          </div>

          {/* Strikes */}
          <div className={styles.bsoItem}>
            <Text weight="bold">S</Text>
            <div className={styles.countDots}>
              {[1, 2].map((s) => (
                <div
                  key={`s-${s}`}
                  className={`${styles.dot} ${
                    (linescore?.strikes || 0) >= s ? styles.strikeDotActive : ""
                  }`}
                />
              ))}
            </div>
          </div>

          {/* Outs */}
          <div className={styles.bsoItem}>
            <Text weight="bold">O</Text>
            <div className={styles.countDots}>
              {[1, 2].map((o) => (
                <div
                  key={`o-${o}`}
                  className={`${styles.dot} ${
                    (linescore?.outs || 0) >= o ? styles.outDotActive : ""
                  }`}
                />
              ))}
            </div>
          </div>

          {/* Diamond Base Runner Graphic */}
          <div className={styles.bsoItem}>
            <div className={styles.diamondContainer} title="出塁状況">
              {/* 2nd Base */}
              <div
                className={`${styles.baseSquare} ${
                  hasRunner2B ? styles.baseActive : ""
                }`}
                style={{ top: "4px", left: "23px" }}
              />
              {/* 3rd Base */}
              <div
                className={`${styles.baseSquare} ${
                  hasRunner3B ? styles.baseActive : ""
                }`}
                style={{ top: "23px", left: "4px" }}
              />
              {/* 1st Base */}
              <div
                className={`${styles.baseSquare} ${
                  hasRunner1B ? styles.baseActive : ""
                }`}
                style={{ top: "23px", left: "42px" }}
              />
            </div>
          </div>
        </div>

        <div className={styles.gameMetaRow}>
          <Caption1 style={{ color: tokens.colorNeutralForeground3 }}>
            Game ID: {game.game_pk} &bull; {new Date(game.game_date_time).toLocaleString("ja-JP")}
          </Caption1>
          {lastEventTime && (
            <Caption1 style={{ color: tokens.colorNeutralForeground2 }}>
              最終受信: {lastEventTime.toLocaleTimeString("ja-JP")}
            </Caption1>
          )}
        </div>
      </section>

      {/* Main Grid: Left = Scoreboard & Timeline, Right = Strike Zone & Statcast */}
      <div className={styles.grid}>
        <div className={styles.leftColumn}>
          {/* Scoreboard Table */}
          <Card className={styles.card}>
            <CardHeader
              image={<Sport24Regular />}
              header={<Text weight="semibold">ラインスコア (Line Score)</Text>}
            />
            <div className={styles.tableContainer}>
              <Table size="small">
                <TableHeader>
                  <TableRow>
                    <TableHeaderCell style={{ minWidth: "100px" }} />
                    {inningsHeaderArray.map((inningNum) => {
                      const isCurrent =
                        linescore &&
                        linescore.current_inning === inningNum &&
                        gameStatus !== "Final";
                      return (
                        <TableHeaderCell
                          key={`inning-${inningNum}`}
                          style={{ textAlign: "center", minWidth: "32px" }}
                          className={isCurrent ? styles.currentInningCol : undefined}
                        >
                          {inningNum}
                        </TableHeaderCell>
                      );
                    })}
                    <TableHeaderCell style={{ textAlign: "center", fontWeight: "bold" }}>
                      R
                    </TableHeaderCell>
                    <TableHeaderCell style={{ textAlign: "center" }}>H</TableHeaderCell>
                    <TableHeaderCell style={{ textAlign: "center" }}>E</TableHeaderCell>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {/* Away Row */}
                  <TableRow>
                    <TableCell>
                      <Body1Strong>{game.away_team_abbr}</Body1Strong>
                    </TableCell>
                    {inningsHeaderArray.map((inningNum) => {
                      const innData = linescore?.innings?.find((i) => i.inning === inningNum);
                      const isCurrent =
                        linescore &&
                        linescore.current_inning === inningNum &&
                        linescore.is_top_inning &&
                        gameStatus !== "Final";
                      return (
                        <TableCell
                          key={`away-inn-${inningNum}`}
                          style={{ textAlign: "center" }}
                          className={isCurrent ? styles.currentInningCol : undefined}
                        >
                          {innData?.away?.runs !== null && innData?.away?.runs !== undefined
                            ? innData.away.runs
                            : "-"}
                        </TableCell>
                      );
                    })}
                    <TableCell style={{ textAlign: "center", fontWeight: "bold" }}>
                      {linescore ? linescore.away_score : game.away_score ?? 0}
                    </TableCell>
                    <TableCell style={{ textAlign: "center" }}>
                      {linescore ? linescore.away_hits : 0}
                    </TableCell>
                    <TableCell style={{ textAlign: "center" }}>
                      {linescore ? linescore.away_errors : 0}
                    </TableCell>
                  </TableRow>

                  {/* Home Row */}
                  <TableRow>
                    <TableCell>
                      <Body1Strong>{game.home_team_abbr}</Body1Strong>
                    </TableCell>
                    {inningsHeaderArray.map((inningNum) => {
                      const innData = linescore?.innings?.find((i) => i.inning === inningNum);
                      const isCurrent =
                        linescore &&
                        linescore.current_inning === inningNum &&
                        !linescore.is_top_inning &&
                        gameStatus !== "Final";
                      return (
                        <TableCell
                          key={`home-inn-${inningNum}`}
                          style={{ textAlign: "center" }}
                          className={isCurrent ? styles.currentInningCol : undefined}
                        >
                          {innData?.home?.runs !== null && innData?.home?.runs !== undefined
                            ? innData.home.runs
                            : "-"}
                        </TableCell>
                      );
                    })}
                    <TableCell style={{ textAlign: "center", fontWeight: "bold" }}>
                      {linescore ? linescore.home_score : game.home_score ?? 0}
                    </TableCell>
                    <TableCell style={{ textAlign: "center" }}>
                      {linescore ? linescore.home_hits : 0}
                    </TableCell>
                    <TableCell style={{ textAlign: "center" }}>
                      {linescore ? linescore.home_errors : 0}
                    </TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </div>
          </Card>

          {/* Play-by-Play Timeline */}
          <Card className={styles.card}>
            <CardHeader
              header={<Text weight="semibold">打席・試合経過タイムライン ({plays.length} 打席)</Text>}
              description={<Caption1>最新の打席から順に表示</Caption1>}
            />
            <div style={{ display: "flex", flexDirection: "column", rowGap: "12px" }}>
              {plays.length === 0 ? (
                <Body1 style={{ color: tokens.colorNeutralForeground3 }}>
                  打席データがまだ記録されていません。
                </Body1>
              ) : (
                [...plays].reverse().map((play) => {
                  const isExpanded = expandedPlayIndex === play.at_bat_index;
                  return (
                    <div key={`play-${play.at_bat_index}`} className={styles.playItem}>
                      <div
                        className={styles.playHeader}
                        onClick={() =>
                          setExpandedPlayIndex(isExpanded ? null : play.at_bat_index)
                        }
                      >
                        <div style={{ display: "flex", alignItems: "center", columnGap: "8px" }}>
                          <Badge appearance="filled" color="brand">
                            {play.inning}回{play.is_top_inning ? "表" : "裏"}
                          </Badge>
                          <Body1Strong>{play.batter_name}</Body1Strong>
                          <Caption1 style={{ color: tokens.colorNeutralForeground3 }}>
                            vs {play.pitcher_name}
                          </Caption1>
                        </div>
                        <div style={{ display: "flex", alignItems: "center", columnGap: "8px" }}>
                          {play.event && (
                            <Badge
                              appearance="tint"
                              color={play.is_scoring_play ? "danger" : play.is_out ? "informative" : "success"}
                            >
                              {play.event}
                            </Badge>
                          )}
                          {isExpanded ? <ChevronUp20Regular /> : <ChevronDown20Regular />}
                        </div>
                      </div>

                      {play.description && (
                        <Body1 style={{ fontSize: "13px" }}>{play.description}</Body1>
                      )}

                      {/* Expandable Pitch Sequence */}
                      {isExpanded && (
                        <div className={styles.playDetails}>
                          <Caption1 style={{ fontWeight: "bold" }}>
                            配球履歴 ({play.pitches.length} 球)
                          </Caption1>
                          {play.pitches.length === 0 ? (
                            <Caption1 style={{ color: tokens.colorNeutralForeground3 }}>
                              投球データなし
                            </Caption1>
                          ) : (
                            <div style={{ display: "flex", flexDirection: "column", rowGap: "4px" }}>
                              {play.pitches.map((p) => {
                                const isSelected = selectedPitch?.pitch_number === p.pitch_number && selectedPitch?.at_bat_index === p.at_bat_index;
                                return (
                                  <div
                                    key={`play-${play.at_bat_index}-p-${p.pitch_number}`}
                                    onClick={() => setSelectedPitch(p)}
                                    style={{
                                      display: "flex",
                                      justifyContent: "space-between",
                                      alignItems: "center",
                                      padding: "4px 8px",
                                      borderRadius: "4px",
                                      cursor: "pointer",
                                      backgroundColor: isSelected
                                        ? tokens.colorBrandBackground2
                                        : "transparent",
                                    }}
                                  >
                                    <div style={{ display: "flex", alignItems: "center", columnGap: "6px" }}>
                                      <span
                                        style={{
                                          width: "18px",
                                          height: "18px",
                                          borderRadius: "50%",
                                          backgroundColor: getPitchColor(p),
                                          color: "#fff",
                                          fontSize: "11px",
                                          display: "inline-flex",
                                          alignItems: "center",
                                          justifyContent: "center",
                                          fontWeight: "bold",
                                        }}
                                      >
                                        {p.pitch_number}
                                      </span>
                                      <Caption1 style={{ fontWeight: "semibold" }}>
                                        {p.pitch_name || p.pitch_type || "投球"}
                                      </Caption1>
                                      {p.start_speed && (
                                        <Caption1 style={{ color: tokens.colorNeutralForeground3 }}>
                                          {p.start_speed.toFixed(1)} mph
                                        </Caption1>
                                      )}
                                    </div>
                                    <Caption1 style={{ color: tokens.colorNeutralForeground2 }}>
                                      {p.call_description || p.description || ""}
                                    </Caption1>
                                  </div>
                                );
                              })}
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  );
                })
              )}
            </div>
          </Card>
        </div>

        {/* Right Column: Strike Zone & Statcast Widget */}
        <div className={styles.rightColumn}>
          {/* Current Matchup & Strike Zone Card */}
          <Card className={styles.card}>
            <CardHeader
              image={<Target24Regular />}
              header={<Text weight="semibold">一球速報 & ストライクゾーン (Statcast)</Text>}
              description={
                currentPlay
                  ? `${currentPlay.batter_name} (打者) vs ${currentPlay.pitcher_name} (投手)`
                  : "待機中"
              }
            />

            <div className={styles.strikeZoneContainer}>
              {/* Strike Zone SVG */}
              <svg
                viewBox="0 0 240 270"
                style={{
                  width: "100%",
                  maxWidth: "260px",
                  height: "auto",
                  backgroundColor: "#fafbfc",
                  borderRadius: "8px",
                  border: "1px solid #d1d5db",
                }}
              >
                {/* Home Plate */}
                <polygon
                  points="95,245 145,245 155,255 120,265 85,255"
                  fill="#ffffff"
                  stroke="#9ca3af"
                  strokeWidth="1.5"
                />

                {/* Strike Zone Rectangle (Outer Box) */}
                <rect
                  x="70"
                  y="75"
                  width="100"
                  height="120"
                  fill="rgba(0, 120, 212, 0.04)"
                  stroke="#374151"
                  strokeWidth="2"
                />

                {/* Inner 3x3 Grid Lines */}
                <line x1="103.3" y1="75" x2="103.3" y2="195" stroke="#9ca3af" strokeWidth="1" strokeDasharray="2,2" />
                <line x1="136.6" y1="75" x2="136.6" y2="195" stroke="#9ca3af" strokeWidth="1" strokeDasharray="2,2" />
                <line x1="70" y1="115" x2="170" y2="115" stroke="#9ca3af" strokeWidth="1" strokeDasharray="2,2" />
                <line x1="70" y1="155" x2="170" y2="155" stroke="#9ca3af" strokeWidth="1" strokeDasharray="2,2" />

                {/* Plot Pitches for current or expanded play */}
                {(expandedPlayIndex !== null
                  ? plays.find((p) => p.at_bat_index === expandedPlayIndex)?.pitches || []
                  : currentPlay?.pitches || []
                ).map((pitch) => {
                  const { cx, cy } = convertPitchCoords(pitch);
                  const isSelected = activePitch?.pitch_number === pitch.pitch_number;
                  const color = getPitchColor(pitch);

                  return (
                    <g
                      key={`sz-pitch-${pitch.at_bat_index}-${pitch.pitch_number}`}
                      onClick={() => setSelectedPitch(pitch)}
                      style={{ cursor: "pointer" }}
                    >
                      {isSelected && (
                        <circle
                          cx={cx}
                          cy={cy}
                          r="15"
                          fill="none"
                          stroke={tokens.colorBrandStroke1}
                          strokeWidth="2.5"
                        />
                      )}
                      <circle
                        cx={cx}
                        cy={cy}
                        r="10"
                        fill={color}
                        stroke="#ffffff"
                        strokeWidth="1.5"
                      />
                      <text
                        x={cx}
                        y={cy + 3.5}
                        textAnchor="middle"
                        fontSize="9"
                        fontWeight="bold"
                        fill="#ffffff"
                      >
                        {pitch.pitch_number}
                      </text>
                    </g>
                  );
                })}
              </svg>

              {/* Pitch Color Legend */}
              <div style={{ display: "flex", columnGap: "14px", alignItems: "center" }}>
                <div style={{ display: "flex", alignItems: "center", columnGap: "4px" }}>
                  <div style={{ width: "10px", height: "10px", borderRadius: "50%", backgroundColor: "#d13438" }} />
                  <Caption1>ストライク</Caption1>
                </div>
                <div style={{ display: "flex", alignItems: "center", columnGap: "4px" }}>
                  <div style={{ width: "10px", height: "10px", borderRadius: "50%", backgroundColor: "#107c41" }} />
                  <Caption1>ボール</Caption1>
                </div>
                <div style={{ display: "flex", alignItems: "center", columnGap: "4px" }}>
                  <div style={{ width: "10px", height: "10px", borderRadius: "50%", backgroundColor: "#0078d4" }} />
                  <Caption1>打球 (In Play)</Caption1>
                </div>
              </div>
            </div>

            {/* Statcast Metrics Card */}
            {activePitch ? (
              <div style={{ display: "flex", flexDirection: "column", rowGap: "12px", marginTop: "8px" }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <Subtitle2>
                    第 {activePitch.pitch_number} 球: {activePitch.pitch_name || activePitch.pitch_type || "投球"}
                  </Subtitle2>
                  {activePitch.call_description && (
                    <Badge appearance="filled" color="brand">
                      {activePitch.call_description}
                    </Badge>
                  )}
                </div>

                <div className={styles.statcastCardGrid}>
                  <div className={styles.metricCard}>
                    <Caption1 style={{ color: tokens.colorNeutralForeground3 }}>初速 (Velocity)</Caption1>
                    <Text weight="bold" size={400}>
                      {activePitch.start_speed ? `${activePitch.start_speed.toFixed(1)} mph` : "-"}
                    </Text>
                  </div>

                  <div className={styles.metricCard}>
                    <Caption1 style={{ color: tokens.colorNeutralForeground3 }}>回転数 (Spin)</Caption1>
                    <Text weight="bold" size={400}>
                      {activePitch.spin_rate ? `${Math.round(activePitch.spin_rate)} rpm` : "-"}
                    </Text>
                  </div>

                  <div className={styles.metricCard}>
                    <Caption1 style={{ color: tokens.colorNeutralForeground3 }}>縦変化 (Induced)</Caption1>
                    <Text weight="bold" size={400}>
                      {activePitch.break_vertical_induced !== null
                        ? `${activePitch.break_vertical_induced.toFixed(1)}" `
                        : "-"}
                    </Text>
                  </div>

                  <div className={styles.metricCard}>
                    <Caption1 style={{ color: tokens.colorNeutralForeground3 }}>横変化 (Horizontal)</Caption1>
                    <Text weight="bold" size={400}>
                      {activePitch.break_horizontal !== null
                        ? `${activePitch.break_horizontal.toFixed(1)}" `
                        : "-"}
                    </Text>
                  </div>

                  {activePitch.launch_speed !== null && (
                    <div className={styles.metricCard}>
                      <Caption1 style={{ color: tokens.colorNeutralForeground3 }}>打球速度 (Exit)</Caption1>
                      <Text weight="bold" size={400} style={{ color: tokens.colorBrandForeground1 }}>
                        {activePitch.launch_speed.toFixed(1)} mph
                      </Text>
                    </div>
                  )}

                  {activePitch.launch_angle !== null && (
                    <div className={styles.metricCard}>
                      <Caption1 style={{ color: tokens.colorNeutralForeground3 }}>打球角度 (Angle)</Caption1>
                      <Text weight="bold" size={400}>
                        {activePitch.launch_angle.toFixed(1)}°
                      </Text>
                    </div>
                  )}

                  {activePitch.total_distance !== null && (
                    <div className={styles.metricCard}>
                      <Caption1 style={{ color: tokens.colorNeutralForeground3 }}>飛距離 (Distance)</Caption1>
                      <Text weight="bold" size={400} style={{ color: tokens.colorBrandForeground1 }}>
                        {activePitch.total_distance} ft
                      </Text>
                    </div>
                  )}
                </div>
              </div>
            ) : (
              <Body1 style={{ color: tokens.colorNeutralForeground3, textAlign: "center" }}>
                投球データを選択するか、新規投球の受信をお待ちください。
              </Body1>
            )}
          </Card>
        </div>
      </div>
    </main>
  );
}
