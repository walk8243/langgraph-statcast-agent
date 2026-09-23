"use client";

import React, { useState, useMemo } from "react";
import Link from "next/link";
import {
  Title1,
  Title3,
  Body1,
  Caption1,
  Button,
  Card,
  CardHeader,
  CardFooter,
  Badge,
  TabList,
  Tab,
  Input,
  makeStyles,
  shorthands,
  tokens,
  Text,
} from "@fluentui/react-components";
import {
  ArrowLeft16Regular,
  ArrowRight16Regular,
  Search20Regular,
  Filter20Regular,
  Sport24Regular,
  Shield24Regular,
} from "@fluentui/react-icons";
import { Team } from "@/types/team";
import { Player, PositionGroup } from "@/types/player";
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
    rowGap: "12px",
    background: "linear-gradient(135deg, #f7f9fc 0%, #eef2f7 100%)",
    ...shorthands.border("1px", "solid", tokens.colorNeutralStroke2),
  },
  teamMetaRow: {
    display: "flex",
    alignItems: "center",
    flexWrap: "wrap",
    gap: "10px",
  },
  controlsRow: {
    display: "flex",
    flexWrap: "wrap",
    justifyContent: "space-between",
    alignItems: "center",
    gap: "16px",
    ...shorthands.padding("12px", "16px"),
    backgroundColor: tokens.colorNeutralBackground1,
    ...shorthands.borderRadius(tokens.borderRadiusMedium),
    ...shorthands.border("1px", "solid", tokens.colorNeutralStroke2),
  },
  searchInput: {
    minWidth: "260px",
  },
  positionSection: {
    display: "flex",
    flexDirection: "column",
    rowGap: "16px",
  },
  positionHeader: {
    display: "flex",
    alignItems: "center",
    columnGap: "12px",
    ...shorthands.padding("8px", "0"),
    ...shorthands.borderBottom("2px", "solid", tokens.colorBrandStroke1),
  },
  playerGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))",
    gap: "16px",
  },
  playerCard: {
    backgroundColor: tokens.colorNeutralBackground1,
    ...shorthands.border("1px", "solid", tokens.colorNeutralStroke2),
    boxShadow: tokens.shadow2,
    transitionProperty: "all",
    transitionDuration: "0.2s",
    transitionTimingFunction: "ease-in-out",
    ":hover": {
      boxShadow: tokens.shadow8,
      ...shorthands.borderColor(tokens.colorBrandStroke1),
      transform: "translateY(-2px)",
    },
  },
  jerseyBadge: {
    fontSize: "14px",
    fontWeight: "bold",
    minWidth: "36px",
    height: "28px",
    display: "inline-flex",
    justifyContent: "center",
    alignItems: "center",
  },
  playerDetails: {
    display: "flex",
    flexDirection: "column",
    rowGap: "6px",
    ...shorthands.padding("8px", "0"),
  },
  detailRow: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    fontSize: "12px",
    color: tokens.colorNeutralForeground2,
  },
  detailLabel: {
    color: tokens.colorNeutralForeground3,
  },
  emptyState: {
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    justifyContent: "center",
    ...shorthands.padding("64px", "24px"),
    backgroundColor: tokens.colorNeutralBackground1,
    ...shorthands.borderRadius(tokens.borderRadiusMedium),
    ...shorthands.border("1px", "dashed", tokens.colorNeutralStroke2),
    textAlign: "center",
  },
  footer: {
    ...shorthands.padding("24px", "0"),
    ...shorthands.borderTop("1px", "solid", tokens.colorNeutralStroke2),
    textAlign: "center",
    color: tokens.colorNeutralForeground3,
  },
});

interface TeamRosterClientProps {
  team: Team;
  players: Player[];
  positionGroups: PositionGroup[];
}

export function TeamRosterClient({
  team,
  players,
  positionGroups,
}: TeamRosterClientProps) {
  const styles = useStyles();
  const [selectedGroup, setSelectedGroup] = useState<string>("all");
  const [searchQuery, setSearchQuery] = useState<string>("");

  // 検索・ポジションフィルター適用
  const filteredGroups = useMemo(() => {
    const query = searchQuery.trim().toLowerCase();

    return positionGroups
      .filter((group) => {
        if (selectedGroup === "all") return true;
        return group.group_key === selectedGroup;
      })
      .map((group) => {
        const filteredPlayers = group.players.filter((p) => {
          if (!query) return true;
          const matchNameEn = p.name_en.toLowerCase().includes(query);
          const matchNameJa = p.name_ja ? p.name_ja.toLowerCase().includes(query) : false;
          const matchNumber = p.primary_number ? p.primary_number.includes(query) : false;
          const matchPosName = p.primary_position_name
            ? p.primary_position_name.toLowerCase().includes(query)
            : false;

          return matchNameEn || matchNameJa || matchNumber || matchPosName;
        });

        return {
          ...group,
          players: filteredPlayers,
        };
      })
      .filter((group) => group.players.length > 0);
  }, [positionGroups, selectedGroup, searchQuery]);

  const totalVisiblePlayers = useMemo(() => {
    return filteredGroups.reduce((acc, g) => acc + g.players.length, 0);
  }, [filteredGroups]);

  return (
    <div className={styles.container}>
      {/* Header Navigation */}
      <nav className={styles.headerNav}>
        <Link href="/teams" className={styles.backLink}>
          <Button appearance="subtle" icon={<ArrowLeft16Regular />}>
            チーム一覧へ戻る
          </Button>
        </Link>
        <Caption1 style={{ color: tokens.colorNeutralForeground3 }}>
          {team.league_name || "MLB"} &bull; {team.division_name || ""}
        </Caption1>
      </nav>

      {/* Hero Banner */}
      <section className={styles.heroBanner}>
        <div style={{ display: "flex", alignItems: "center", columnGap: "12px" }}>
          <Sport24Regular style={{ color: tokens.colorBrandForeground1, fontSize: "28px" }} />
          <Title1>{team.name}</Title1>
          <Badge
            appearance="filled"
            color={team.league_name === "American League" ? "brand" : "danger"}
            size="large"
          >
            {team.abbreviation}
          </Badge>
        </div>

        <div className={styles.teamMetaRow}>
          {team.league_name && (
            <Badge appearance="tint" color="brand">
              {team.league_name}
            </Badge>
          )}
          {team.division_name && (
            <Badge appearance="outline">
              {team.division_name}
            </Badge>
          )}
          <Badge appearance="tint" color="informative">
            登録選手: {players.length} 名
          </Badge>
        </div>

        <Body1 style={{ color: tokens.colorNeutralForeground3, marginTop: "4px" }}>
          球団所属選手一覧（ロスター）。各選手を選択すると、選手成績および AI 生成による詳細解説レポートへアクセスできます。
        </Body1>
      </section>

      {/* Filter and Search Controls */}
      <div className={styles.controlsRow}>
        <TabList
          selectedValue={selectedGroup}
          onTabSelect={(_, data) => setSelectedGroup(String(data.value))}
        >
          <Tab value="all" icon={<Shield24Regular />}>
            すべて ({players.length})
          </Tab>
          {positionGroups.map((group) => (
            <Tab key={group.group_key} value={group.group_key}>
              {group.group_name_ja} ({group.players.length})
            </Tab>
          ))}
        </TabList>

        <Input
          className={styles.searchInput}
          placeholder="選手名、背番号、ポジションで検索"
          value={searchQuery}
          onChange={(_, data) => setSearchQuery(data.value)}
          contentBefore={<Search20Regular />}
        />
      </div>

      {/* Roster Sections */}
      {filteredGroups.length === 0 ? (
        <div className={styles.emptyState}>
          <Filter20Regular style={{ fontSize: "36px", color: tokens.colorNeutralForeground3 }} />
          <Title3 style={{ marginTop: "12px" }}>該当する選手が見つかりませんでした</Title3>
          <Body1 style={{ color: tokens.colorNeutralForeground3, marginTop: "8px" }}>
            検索条件「{searchQuery}」に一致する選手がいません。キーワードを変更してください。
          </Body1>
          <Button
            style={{ marginTop: "16px" }}
            appearance="secondary"
            onClick={() => {
              setSearchQuery("");
              setSelectedGroup("all");
            }}
          >
            フィルターをリセット
          </Button>
        </div>
      ) : (
        filteredGroups.map((group) => (
          <section key={group.group_key} className={styles.positionSection}>
            <div className={styles.positionHeader}>
              <Title3>{group.group_name_ja}</Title3>
              <Caption1 style={{ color: tokens.colorNeutralForeground3 }}>
                ({group.group_name_en})
              </Caption1>
              <Badge size="small" appearance="tint" color="brand">
                {group.players.length} 名
              </Badge>
            </div>

            <div className={styles.playerGrid}>
              {group.players.map((player) => {
                const batsThrows = formatBatsThrows(player.bat_side, player.pitch_hand);
                const jerseyNum = player.primary_number ? `#${player.primary_number}` : "-";

                return (
                  <Card key={player.player_id} className={styles.playerCard}>
                    <CardHeader
                      header={
                        <div style={{ display: "flex", alignItems: "center", columnGap: "8px" }}>
                          <Text weight="semibold" size={400}>
                            {player.name_en}
                          </Text>
                          {player.name_ja && (
                            <Caption1 style={{ color: tokens.colorNeutralForeground3 }}>
                              ({player.name_ja})
                            </Caption1>
                          )}
                        </div>
                      }
                      action={
                        <Badge
                          className={styles.jerseyBadge}
                          appearance="filled"
                          color={player.primary_number ? "brand" : "subtle"}
                        >
                          {jerseyNum}
                        </Badge>
                      }
                    />

                    <div className={styles.playerDetails}>
                      <div className={styles.detailRow}>
                        <span className={styles.detailLabel}>ポジション:</span>
                        <Text size={200}>{player.primary_position_name || "-"}</Text>
                      </div>
                      <div className={styles.detailRow}>
                        <span className={styles.detailLabel}>投打:</span>
                        <Text size={200}>{batsThrows}</Text>
                      </div>
                    </div>

                    <CardFooter style={{ marginTop: "auto", paddingTop: "12px" }}>
                      <Link
                        href={`/players/${player.player_id}`}
                        style={{ textDecoration: "none", width: "100%" }}
                      >
                        <Button
                          style={{ width: "100%" }}
                          appearance="primary"
                          size="medium"
                          icon={<ArrowRight16Regular />}
                          iconPosition="after"
                        >
                          選手詳細を見る
                        </Button>
                      </Link>
                    </CardFooter>
                  </Card>
                );
              })}
            </div>
          </section>
        ))
      )}

      {/* Summary Footer */}
      <footer className={styles.footer}>
        <Caption1>
          現在表示中: {totalVisiblePlayers} / {players.length} 名 &bull; {team.name} ロスター &bull; PostgreSQL 連携
        </Caption1>
      </footer>
    </div>
  );
}
