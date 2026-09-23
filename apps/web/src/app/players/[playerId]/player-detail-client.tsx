"use client";

import React from "react";
import Link from "next/link";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import {
  Title1,
  Title2,
  Title3,
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
  Bot24Regular,
  Sport24Regular,
  Shield24Regular,
  Calendar20Regular,
  Info20Regular,
  Sparkle20Regular,
  Target20Regular,
  DataTrending24Regular,
} from "@fluentui/react-icons";
import {
  PlayerDetail,
  BatterSeasonStat,
  PitcherSeasonStat,
  PlayerReport,
  BatterStatcastStat,
  PitcherStatcastStat,
  PitcherPitchTypeStat,
} from "@/types/player";
import { formatBatsThrows } from "@/lib/player-utils";

const useStyles = makeStyles({
  container: {
    maxWidth: "1280px",
    marginLeft: "auto",
    marginRight: "auto",
    ...shorthands.padding("32px", "24px"),
    display: "flex",
    flexDirection: "column",
    rowGap: "28px",
  },
  headerNav: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    ...shorthands.borderBottom("1px", "solid", tokens.colorNeutralStroke2),
    ...shorthands.padding("0", "0", "16px", "0"),
  },
  backLink: {
    textDecoration: "none",
  },
  heroBanner: {
    ...shorthands.padding("32px"),
    backgroundColor: tokens.colorNeutralBackground1,
    ...shorthands.borderRadius(tokens.borderRadiusLarge),
    boxShadow: tokens.shadow4,
    display: "flex",
    flexDirection: "column",
    rowGap: "16px",
    background: "linear-gradient(135deg, #f7f9fc 0%, #eef2f7 100%)",
    ...shorthands.border("1px", "solid", tokens.colorNeutralStroke2),
  },
  playerTopRow: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "flex-start",
    flexWrap: "wrap",
    gap: "16px",
  },
  playerTitleArea: {
    display: "flex",
    flexDirection: "column",
    rowGap: "6px",
  },
  jerseyBadge: {
    fontSize: "20px",
    fontWeight: "bold",
    ...shorthands.padding("8px", "16px"),
  },
  metaTagsRow: {
    display: "flex",
    alignItems: "center",
    flexWrap: "wrap",
    gap: "10px",
  },
  teamLink: {
    display: "inline-flex",
    alignItems: "center",
    textDecoration: "none",
    ":hover": {
      opacity: 0.85,
    },
  },
  contentSection: {
    display: "flex",
    flexDirection: "column",
    rowGap: "20px",
  },
  reportCard: {
    ...shorthands.padding("28px"),
    backgroundColor: tokens.colorNeutralBackground1,
    ...shorthands.borderRadius(tokens.borderRadiusLarge),
    boxShadow: tokens.shadow4,
    ...shorthands.border("1px", "solid", tokens.colorNeutralStroke2),
  },
  reportHeader: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    flexWrap: "wrap",
    gap: "12px",
    ...shorthands.borderBottom("1px", "solid", tokens.colorNeutralStroke2),
    ...shorthands.padding("0", "0", "16px", "0"),
  },
  reportMetaRow: {
    display: "flex",
    alignItems: "center",
    flexWrap: "wrap",
    gap: "16px",
  },
  markdownContainer: {
    marginTop: "20px",
    lineHeight: "1.75",
    color: tokens.colorNeutralForeground1,
    "& h1": {
      fontSize: "24px",
      fontWeight: "700",
      marginTop: "24px",
      marginBottom: "12px",
      color: tokens.colorNeutralForeground1,
      ...shorthands.borderBottom("1px", "solid", tokens.colorNeutralStroke3),
      ...shorthands.padding("0", "0", "8px", "0"),
    },
    "& h2": {
      fontSize: "20px",
      fontWeight: "700",
      marginTop: "24px",
      marginBottom: "12px",
      color: tokens.colorNeutralForeground1,
      ...shorthands.borderBottom("1px", "solid", tokens.colorNeutralStroke3),
      ...shorthands.padding("0", "0", "6px", "0"),
    },
    "& h3": {
      fontSize: "17px",
      fontWeight: "600",
      marginTop: "20px",
      marginBottom: "8px",
      color: tokens.colorBrandForeground1,
    },
    "& p": {
      marginTop: "10px",
      marginBottom: "10px",
      fontSize: "15px",
    },
    "& ul, & ol": {
      marginTop: "8px",
      marginBottom: "12px",
      paddingLeft: "24px",
    },
    "& li": {
      marginTop: "4px",
      marginBottom: "4px",
      fontSize: "14px",
    },
    "& hr": {
      ...shorthands.border("none"),
      borderTop: `1px solid ${tokens.colorNeutralStroke3}`,
      margin: "24px 0",
    },
    "& blockquote": {
      ...shorthands.borderLeft("4px", "solid", tokens.colorBrandStroke1),
      margin: "12px 0",
      ...shorthands.padding("8px", "16px"),
      backgroundColor: tokens.colorNeutralBackground2,
      color: tokens.colorNeutralForeground2,
      ...shorthands.borderRadius("0", tokens.borderRadiusMedium, tokens.borderRadiusMedium, "0"),
    },
    "& strong": {
      fontWeight: "700",
      color: tokens.colorNeutralForeground1,
    },
    "& table": {
      width: "100%",
      borderCollapse: "collapse",
      marginTop: "16px",
      marginBottom: "16px",
      display: "block",
      overflowX: "auto",
    },
    "& th, & td": {
      ...shorthands.border("1px", "solid", tokens.colorNeutralStroke2),
      ...shorthands.padding("8px", "12px"),
      textAlign: "left",
      fontSize: "14px",
    },
    "& th": {
      backgroundColor: tokens.colorNeutralBackground3,
      fontWeight: "600",
    },
  },
  statsCard: {
    ...shorthands.padding("24px"),
    backgroundColor: tokens.colorNeutralBackground1,
    ...shorthands.borderRadius(tokens.borderRadiusLarge),
    boxShadow: tokens.shadow2,
    ...shorthands.border("1px", "solid", tokens.colorNeutralStroke2),
  },
  tableWrapper: {
    overflowX: "auto",
    marginTop: "16px",
  },
  highlightCell: {
    fontWeight: "bold",
    color: tokens.colorBrandForeground1,
  },
  emptyReportCard: {
    ...shorthands.padding("40px", "24px"),
    backgroundColor: tokens.colorNeutralBackground1,
    ...shorthands.borderRadius(tokens.borderRadiusLarge),
    boxShadow: tokens.shadow2,
    ...shorthands.border("1px", "dashed", tokens.colorNeutralStroke1),
    textAlign: "center",
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    rowGap: "12px",
  },
  codeBlock: {
    backgroundColor: tokens.colorNeutralBackground3,
    ...shorthands.padding("10px", "16px"),
    ...shorthands.borderRadius(tokens.borderRadiusMedium),
    fontFamily: "monospace",
    fontSize: "13px",
    marginTop: "8px",
    display: "inline-block",
  },
  metricsGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
    gap: "16px",
    marginTop: "16px",
  },
  metricCard: {
    ...shorthands.padding("16px"),
    backgroundColor: tokens.colorNeutralBackground2,
    ...shorthands.borderRadius(tokens.borderRadiusMedium),
    ...shorthands.border("1px", "solid", tokens.colorNeutralStroke3),
    display: "flex",
    flexDirection: "column",
    rowGap: "6px",
  },
  metricLabel: {
    fontSize: "12px",
    color: tokens.colorNeutralForeground3,
    fontWeight: "600",
    textTransform: "uppercase",
  },
  metricValue: {
    fontSize: "24px",
    fontWeight: "700",
    color: tokens.colorNeutralForeground1,
  },
  metricSubtext: {
    fontSize: "12px",
    color: tokens.colorNeutralForeground2,
  },
});

interface PlayerDetailClientProps {
  player: PlayerDetail;
  batterStats: BatterSeasonStat[];
  pitcherStats: PitcherSeasonStat[];
  reports: PlayerReport[];
  latestBatterStatcast?: BatterStatcastStat | null;
  latestPitcherStatcast?: PitcherStatcastStat | null;
  latestPitchTypeStats?: PitcherPitchTypeStat[];
}

export default function PlayerDetailClient({
  player,
  batterStats,
  pitcherStats,
  reports,
  latestBatterStatcast,
  latestPitcherStatcast,
  latestPitchTypeStats = [],
}: PlayerDetailClientProps) {
  const styles = useStyles();

  // 最新の1件のみ使用（ORDER BY year DESC でソート済み）
  const latestReport = reports.length > 0 ? reports[0] : null;

  const batsThrows = formatBatsThrows(player.bat_side, player.pitch_hand);
  const mainName = player.name_ja || player.name_en;
  const subName = player.name_ja ? player.name_en : null;
  const jerseyDisplay = player.primary_number ? `#${player.primary_number}` : "-";

  return (
    <div className={styles.container}>
      {/* Navigation */}
      <nav className={styles.headerNav}>
        {player.team_id ? (
          <Link href={`/teams/${player.team_id}`} className={styles.backLink}>
            <Button appearance="subtle" icon={<ArrowLeft16Regular />}>
              {player.team_name || "所属チーム"} の選手一覧へ戻る
            </Button>
          </Link>
        ) : (
          <Link href="/teams" className={styles.backLink}>
            <Button appearance="subtle" icon={<ArrowLeft16Regular />}>
              チーム一覧へ戻る
            </Button>
          </Link>
        )}
      </nav>

      {/* Hero Banner: Player Profile */}
      <div className={styles.heroBanner}>
        <div className={styles.playerTopRow}>
          <div className={styles.playerTitleArea}>
            <Title1>{mainName}</Title1>
            {subName && (
              <Caption1 style={{ fontSize: "16px", color: tokens.colorNeutralForeground2 }}>
                {subName}
              </Caption1>
            )}
          </div>
          <Badge
            className={styles.jerseyBadge}
            appearance="filled"
            color={player.primary_number ? "brand" : "subtle"}
          >
            {jerseyDisplay}
          </Badge>
        </div>

        <div className={styles.metaTagsRow}>
          {player.team_id && player.team_name && (
            <Link href={`/teams/${player.team_id}`} className={styles.teamLink}>
              <Badge appearance="tint" color="brand" icon={<Shield24Regular />}>
                {player.team_name} ({player.team_abbreviation})
              </Badge>
            </Link>
          )}

          {player.league_name && (
            <Badge appearance="outline">
              {player.league_name} {player.division_name ? `• ${player.division_name}` : ""}
            </Badge>
          )}

          <Badge appearance="outline" icon={<Sport24Regular />}>
            ポジション: {player.primary_position_name || player.primary_position_type || "-"}
          </Badge>

          <Badge appearance="outline">投打: {batsThrows}</Badge>
        </div>
      </div>

      {/* AI Agent Report Section */}
      <section className={styles.contentSection}>
        <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
          <Sparkle20Regular style={{ color: tokens.colorBrandForeground1 }} />
          <Title2>AI解説レポート (Statcast Agent)</Title2>
        </div>

        {!latestReport ? (
          <div className={styles.emptyReportCard}>
            <Bot24Regular style={{ fontSize: "40px", color: tokens.colorNeutralForeground3 }} />
            <Title3>AI解説レポートはまだ生成されていません</Title3>
            <Body1 style={{ color: tokens.colorNeutralForeground3, maxWidth: "600px" }}>
              この選手に対する LangGraph AI Agent によるシーズン解説レポートはまだ登録されていません。
              エージェントを実行して最新レポートを生成できます。
            </Body1>
            <div className={styles.codeBlock}>
              npm run generate -- --player {player.player_id} --year 2024
            </div>
          </div>
        ) : (
          <div className={styles.reportCard}>
            {/* Report Header: Year Badge & Meta */}
            <div className={styles.reportHeader}>
              <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                <Badge appearance="filled" color="brand" icon={<Calendar20Regular />}>
                  {latestReport.year}年シーズン
                </Badge>
                <Text weight="semibold">最新解説レポート</Text>
              </div>

              <div className={styles.reportMetaRow}>
                <Badge appearance="tint" color="informative" icon={<Bot24Regular />}>
                  Model: {latestReport.model_name}
                </Badge>
                <Caption1 style={{ color: tokens.colorNeutralForeground3 }}>
                  作成日: {new Date(latestReport.created_at).toLocaleDateString("ja-JP")}
                </Caption1>
              </div>
            </div>

            {/* Report Markdown Content */}
            <div className={styles.markdownContainer}>
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {latestReport.report_text}
              </ReactMarkdown>
            </div>
          </div>
        )}
      </section>

      {/* Statcast Batter Metrics Section */}
      {latestBatterStatcast && (
        <section className={styles.contentSection}>
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <DataTrending24Regular style={{ color: tokens.colorBrandForeground1 }} />
            <Title2>最新 Statcast 打球指標</Title2>
            <Badge appearance="filled" color="brand">
              {latestBatterStatcast.year}年
            </Badge>
          </div>

          <div className={styles.statsCard}>
            <div className={styles.metricsGrid}>
              <div className={styles.metricCard}>
                <Caption1 className={styles.metricLabel}>Barrel% (バレル率)</Caption1>
                <Text className={styles.metricValue}>
                  {Number(latestBatterStatcast.barrel_pct).toFixed(1)}%
                </Text>
                <Caption1 className={styles.metricSubtext}>
                  {latestBatterStatcast.barrels} / {latestBatterStatcast.batted_balls} 打球
                </Caption1>
              </div>

              <div className={styles.metricCard}>
                <Caption1 className={styles.metricLabel}>HardHit% (ハードヒット率)</Caption1>
                <Text className={styles.metricValue}>
                  {Number(latestBatterStatcast.hard_hit_pct).toFixed(1)}%
                </Text>
                <Caption1 className={styles.metricSubtext}>
                  {latestBatterStatcast.hard_hit_count} / {latestBatterStatcast.batted_balls} 打球 (95+ mph)
                </Caption1>
              </div>

              <div className={styles.metricCard}>
                <Caption1 className={styles.metricLabel}>平均打球初速 (Avg EV)</Caption1>
                <Text className={styles.metricValue}>
                  {Number(latestBatterStatcast.avg_exit_velocity).toFixed(1)}{" "}
                  <span style={{ fontSize: "14px", fontWeight: "normal" }}>mph</span>
                </Text>
                <Caption1 className={styles.metricSubtext}>MLB平均 約88-89 mph</Caption1>
              </div>

              <div className={styles.metricCard}>
                <Caption1 className={styles.metricLabel}>最高打球初速 (Max EV)</Caption1>
                <Text className={styles.metricValue}>
                  {Number(latestBatterStatcast.max_exit_velocity).toFixed(1)}{" "}
                  <span style={{ fontSize: "14px", fontWeight: "normal" }}>mph</span>
                </Text>
                <Caption1 className={styles.metricSubtext}>シーズン最速打球</Caption1>
              </div>

              <div className={styles.metricCard}>
                <Caption1 className={styles.metricLabel}>平均打球角度 (Launch Angle)</Caption1>
                <Text className={styles.metricValue}>
                  {Number(latestBatterStatcast.avg_launch_angle).toFixed(1)}°
                </Text>
                <Caption1 className={styles.metricSubtext}>適正範囲: 10°〜25°</Caption1>
              </div>

              <div className={styles.metricCard}>
                <Caption1 className={styles.metricLabel}>SweetSpot% (適正角度率)</Caption1>
                <Text className={styles.metricValue}>
                  {Number(latestBatterStatcast.sweet_spot_pct).toFixed(1)}%
                </Text>
                <Caption1 className={styles.metricSubtext}>8°〜32°の打球割合</Caption1>
              </div>
            </div>

            <div style={{ marginTop: "16px", display: "flex", gap: "16px", flexWrap: "wrap" }}>
              <Caption1 style={{ color: tokens.colorNeutralForeground3 }}>
                総打球数 (Batted Balls): <strong>{latestBatterStatcast.batted_balls}</strong>
              </Caption1>
              <Caption1 style={{ color: tokens.colorNeutralForeground3 }}>
                見た投球数 (Pitches Seen): <strong>{latestBatterStatcast.pitches_seen}</strong>
              </Caption1>
            </div>
          </div>
        </section>
      )}

      {/* Season Stats Section: Batter */}
      {batterStats.length > 0 && (
        <section className={styles.contentSection}>
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <Sport24Regular style={{ color: tokens.colorBrandForeground1 }} />
            <Title2>打者シーズン成績</Title2>
          </div>

          <div className={styles.statsCard}>
            <div className={styles.tableWrapper}>
              <Table aria-label="Batter season stats table">
                <TableHeader>
                  <TableRow>
                    <TableHeaderCell>年度</TableHeaderCell>
                    <TableHeaderCell>打率 (AVG)</TableHeaderCell>
                    <TableHeaderCell>本塁打 (HR)</TableHeaderCell>
                    <TableHeaderCell>打点 (RBI)</TableHeaderCell>
                    <TableHeaderCell>OPS</TableHeaderCell>
                    <TableHeaderCell>試合 (G)</TableHeaderCell>
                    <TableHeaderCell>打数 (AB)</TableHeaderCell>
                    <TableHeaderCell>得点 (R)</TableHeaderCell>
                    <TableHeaderCell>安打 (H)</TableHeaderCell>
                    <TableHeaderCell>二塁打 (2B)</TableHeaderCell>
                    <TableHeaderCell>三塁打 (3B)</TableHeaderCell>
                    <TableHeaderCell>四球 (BB)</TableHeaderCell>
                    <TableHeaderCell>三振 (SO)</TableHeaderCell>
                    <TableHeaderCell>盗塁 (SB)</TableHeaderCell>
                    <TableHeaderCell>出塁率 (OBP)</TableHeaderCell>
                    <TableHeaderCell>長打率 (SLG)</TableHeaderCell>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {batterStats.map((stat) => (
                    <TableRow key={stat.year}>
                      <TableCell>
                        <Body1Strong>{stat.year}</Body1Strong>
                      </TableCell>
                      <TableCell className={styles.highlightCell}>
                        {Number(stat.batting_average).toFixed(3)}
                      </TableCell>
                      <TableCell className={styles.highlightCell}>
                        {stat.home_runs}
                      </TableCell>
                      <TableCell className={styles.highlightCell}>
                        {stat.rbi}
                      </TableCell>
                      <TableCell className={styles.highlightCell}>
                        {Number(stat.ops).toFixed(3)}
                      </TableCell>
                      <TableCell>{stat.games}</TableCell>
                      <TableCell>{stat.at_bats}</TableCell>
                      <TableCell>{stat.runs}</TableCell>
                      <TableCell>{stat.hits}</TableCell>
                      <TableCell>{stat.doubles}</TableCell>
                      <TableCell>{stat.triples}</TableCell>
                      <TableCell>{stat.walks}</TableCell>
                      <TableCell>{stat.strikeouts}</TableCell>
                      <TableCell>{stat.stolen_bases}</TableCell>
                      <TableCell>{Number(stat.on_base_percentage).toFixed(3)}</TableCell>
                      <TableCell>{Number(stat.slugging_percentage).toFixed(3)}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </div>
        </section>
      )}

      {/* Statcast Pitcher & Pitch Type Metrics Section */}
      {(latestPitcherStatcast || latestPitchTypeStats.length > 0) && (
        <section className={styles.contentSection}>
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <Target20Regular style={{ color: tokens.colorBrandForeground1 }} />
            <Title2>最新 Statcast 投球・球種別指標</Title2>
            <Badge appearance="filled" color="brand">
              {latestPitcherStatcast?.year || latestPitchTypeStats[0]?.year}年
            </Badge>
          </div>

          {latestPitcherStatcast && (
            <div className={styles.statsCard}>
              <Title3>投球品質サマリー</Title3>
              <div className={styles.metricsGrid}>
                <div className={styles.metricCard}>
                  <Caption1 className={styles.metricLabel}>Whiff% (空振り率)</Caption1>
                  <Text className={styles.metricValue}>
                    {Number(latestPitcherStatcast.whiff_pct).toFixed(1)}%
                  </Text>
                  <Caption1 className={styles.metricSubtext}>
                    {latestPitcherStatcast.whiffs} 空振り / {latestPitcherStatcast.swings} スイング
                  </Caption1>
                </div>

                <div className={styles.metricCard}>
                  <Caption1 className={styles.metricLabel}>CSW% (見逃し+空振り率)</Caption1>
                  <Text className={styles.metricValue}>
                    {Number(latestPitcherStatcast.csw_pct).toFixed(1)}%
                  </Text>
                  <Caption1 className={styles.metricSubtext}>
                    Called + Swinging Strikes / 投球数
                  </Caption1>
                </div>

                <div className={styles.metricCard}>
                  <Caption1 className={styles.metricLabel}>被Barrel% (被バレル率)</Caption1>
                  <Text className={styles.metricValue}>
                    {Number(latestPitcherStatcast.barrel_pct).toFixed(1)}%
                  </Text>
                  <Caption1 className={styles.metricSubtext}>
                    {latestPitcherStatcast.barrels_allowed} / {latestPitcherStatcast.batted_balls} 被打球
                  </Caption1>
                </div>

                <div className={styles.metricCard}>
                  <Caption1 className={styles.metricLabel}>被HardHit% (被ハードヒット率)</Caption1>
                  <Text className={styles.metricValue}>
                    {Number(latestPitcherStatcast.hard_hit_pct).toFixed(1)}%
                  </Text>
                  <Caption1 className={styles.metricSubtext}>
                    {latestPitcherStatcast.hard_hit_count} / {latestPitcherStatcast.batted_balls} 被打球
                  </Caption1>
                </div>

                <div className={styles.metricCard}>
                  <Caption1 className={styles.metricLabel}>被平均打球初速 (Avg EV against)</Caption1>
                  <Text className={styles.metricValue}>
                    {Number(latestPitcherStatcast.avg_exit_velocity).toFixed(1)}{" "}
                    <span style={{ fontSize: "14px", fontWeight: "normal" }}>mph</span>
                  </Text>
                  <Caption1 className={styles.metricSubtext}>許容打球の平均初速</Caption1>
                </div>
              </div>

              <div style={{ marginTop: "16px", display: "flex", gap: "16px", flexWrap: "wrap" }}>
                <Caption1 style={{ color: tokens.colorNeutralForeground3 }}>
                  総投球数 (Total Pitches): <strong>{latestPitcherStatcast.total_pitches}</strong>
                </Caption1>
                <Caption1 style={{ color: tokens.colorNeutralForeground3 }}>
                  スイング数 (Swings): <strong>{latestPitcherStatcast.swings}</strong>
                </Caption1>
                <Caption1 style={{ color: tokens.colorNeutralForeground3 }}>
                  空振り数 (Whiffs): <strong>{latestPitcherStatcast.whiffs}</strong>
                </Caption1>
                <Caption1 style={{ color: tokens.colorNeutralForeground3 }}>
                  見逃しストライク (Called Strikes): <strong>{latestPitcherStatcast.called_strikes}</strong>
                </Caption1>
              </div>
            </div>
          )}

          {latestPitchTypeStats.length > 0 && (
            <div className={styles.statsCard}>
              <Title3>球種別スタッツ (Pitch Arsenal)</Title3>
              <div className={styles.tableWrapper}>
                <Table aria-label="Pitcher pitch types stats table">
                  <TableHeader>
                    <TableRow>
                      <TableHeaderCell>球種</TableHeaderCell>
                      <TableHeaderCell>投球数</TableHeaderCell>
                      <TableHeaderCell>投球割合</TableHeaderCell>
                      <TableHeaderCell>平均球速</TableHeaderCell>
                      <TableHeaderCell>平均回転数</TableHeaderCell>
                      <TableHeaderCell>水平変化量</TableHeaderCell>
                      <TableHeaderCell>垂直変化量</TableHeaderCell>
                      <TableHeaderCell>Whiff% (空振り率)</TableHeaderCell>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {latestPitchTypeStats.map((stat) => (
                      <TableRow key={stat.pitch_type}>
                        <TableCell>
                          <Body1Strong>{stat.pitch_name || stat.pitch_type}</Body1Strong>{" "}
                          <Caption1 style={{ color: tokens.colorNeutralForeground3 }}>
                            ({stat.pitch_type})
                          </Caption1>
                        </TableCell>
                        <TableCell>{stat.pitches}</TableCell>
                        <TableCell className={styles.highlightCell}>
                          {Number(stat.usage_pct).toFixed(1)}%
                        </TableCell>
                        <TableCell className={styles.highlightCell}>
                          {Number(stat.avg_speed).toFixed(1)} mph
                        </TableCell>
                        <TableCell>{Math.round(Number(stat.avg_spin_rate))} rpm</TableCell>
                        <TableCell>
                          {Number(stat.avg_pfx_x) > 0 ? "+" : ""}
                          {Number(stat.avg_pfx_x).toFixed(1)}&quot;
                        </TableCell>
                        <TableCell>
                          {Number(stat.avg_pfx_z) > 0 ? "+" : ""}
                          {Number(stat.avg_pfx_z).toFixed(1)}&quot;
                        </TableCell>
                        <TableCell className={styles.highlightCell}>
                          {Number(stat.whiff_pct).toFixed(1)}%
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            </div>
          )}
        </section>
      )}

      {/* Season Stats Section: Pitcher */}
      {pitcherStats.length > 0 && (
        <section className={styles.contentSection}>
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <Sport24Regular style={{ color: tokens.colorBrandForeground1 }} />
            <Title2>投手シーズン成績</Title2>
          </div>

          <div className={styles.statsCard}>
            <div className={styles.tableWrapper}>
              <Table aria-label="Pitcher season stats table">
                <TableHeader>
                  <TableRow>
                    <TableHeaderCell>年度</TableHeaderCell>
                    <TableHeaderCell>防御率 (ERA)</TableHeaderCell>
                    <TableHeaderCell>勝 (W)</TableHeaderCell>
                    <TableHeaderCell>負 (L)</TableHeaderCell>
                    <TableHeaderCell>奪三振 (SO)</TableHeaderCell>
                    <TableHeaderCell>WHIP</TableHeaderCell>
                    <TableHeaderCell>登板 (G)</TableHeaderCell>
                    <TableHeaderCell>先発 (GS)</TableHeaderCell>
                    <TableHeaderCell>セーブ (SV)</TableHeaderCell>
                    <TableHeaderCell>投球回 (IP)</TableHeaderCell>
                    <TableHeaderCell>被安打 (H)</TableHeaderCell>
                    <TableHeaderCell>失点 (R)</TableHeaderCell>
                    <TableHeaderCell>自責点 (ER)</TableHeaderCell>
                    <TableHeaderCell>被本塁打 (HR)</TableHeaderCell>
                    <TableHeaderCell>与四球 (BB)</TableHeaderCell>
                    <TableHeaderCell>被打率 (BAA)</TableHeaderCell>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {pitcherStats.map((stat) => (
                    <TableRow key={stat.year}>
                      <TableCell>
                        <Body1Strong>{stat.year}</Body1Strong>
                      </TableCell>
                      <TableCell className={styles.highlightCell}>
                        {Number(stat.era).toFixed(2)}
                      </TableCell>
                      <TableCell className={styles.highlightCell}>
                        {stat.wins}
                      </TableCell>
                      <TableCell className={styles.highlightCell}>
                        {stat.losses}
                      </TableCell>
                      <TableCell className={styles.highlightCell}>
                        {stat.strikeouts}
                      </TableCell>
                      <TableCell className={styles.highlightCell}>
                        {Number(stat.whip).toFixed(2)}
                      </TableCell>
                      <TableCell>{stat.games_pitched}</TableCell>
                      <TableCell>{stat.games_started}</TableCell>
                      <TableCell>{stat.saves}</TableCell>
                      <TableCell>{stat.innings_pitched}</TableCell>
                      <TableCell>{stat.hits}</TableCell>
                      <TableCell>{stat.runs}</TableCell>
                      <TableCell>{stat.earned_runs}</TableCell>
                      <TableCell>{stat.home_runs}</TableCell>
                      <TableCell>{stat.walks}</TableCell>
                      <TableCell>
                        {Number(stat.batting_average_against).toFixed(3)}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>

            </div>
          </div>
        </section>
      )}

      {/* No Stats Fallback */}
      {batterStats.length === 0 &&
        pitcherStats.length === 0 &&
        !latestBatterStatcast &&
        !latestPitcherStatcast &&
        latestPitchTypeStats.length === 0 && (
          <Card className={styles.statsCard}>
            <CardHeader
              image={<Info20Regular />}
              header={<Text weight="semibold">シーズン成績データ</Text>}
              description={
                <Caption1>
                  現在登録されている打撃・投球のシーズン成績データはありません。
                </Caption1>
              }
            />
          </Card>
        )}

    </div>
  );
}
