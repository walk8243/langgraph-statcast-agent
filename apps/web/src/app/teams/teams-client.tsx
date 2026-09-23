"use client";

import React, { useState, useMemo } from "react";
import Link from "next/link";
import {
  Title1,
  Title3,
  Subtitle2,
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
  PeopleTeam24Regular,
  ArrowRight16Regular,
  ArrowLeft16Regular,
  Search20Regular,
  Filter20Regular,
  Shield24Regular,
} from "@fluentui/react-icons";
import { Team, LeagueGroup } from "@/types/team";

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
  divisionSection: {
    display: "flex",
    flexDirection: "column",
    rowGap: "16px",
  },
  divisionHeader: {
    display: "flex",
    alignItems: "center",
    columnGap: "12px",
    ...shorthands.padding("8px", "0"),
    ...shorthands.borderBottom("2px", "solid", tokens.colorBrandStroke1),
  },
  teamGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fill, minmax(260px, 1fr))",
    gap: "16px",
  },
  teamCard: {
    backgroundColor: tokens.colorNeutralBackground1,
    ...shorthands.border("1px", "solid", tokens.colorNeutralStroke2),
    boxShadow: tokens.shadow2,
    transitionProperty: "all",
    transitionDuration: "200ms",
    ":hover": {
      boxShadow: tokens.shadow8,
      transform: "translateY(-2px)",
      ...shorthands.borderColor(tokens.colorBrandStroke1),
    },
  },
  cardHeader: {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
  },
  abbreviationBadge: {
    fontWeight: tokens.fontWeightBold,
    letterSpacing: "0.5px",
    fontSize: "14px",
  },
  emptyState: {
    ...shorthands.padding("48px", "24px"),
    textAlign: "center",
    backgroundColor: tokens.colorNeutralBackground1,
    ...shorthands.borderRadius(tokens.borderRadiusMedium),
    ...shorthands.border("1px", "dashed", tokens.colorNeutralStroke2),
  },
  footer: {
    ...shorthands.padding("24px", "0"),
    ...shorthands.borderTop("1px", "solid", tokens.colorNeutralStroke2),
    textAlign: "center",
    color: tokens.colorNeutralForeground3,
  },
});

interface TeamsClientProps {
  initialLeagueGroups: LeagueGroup[];
  allTeams: Team[];
}

export function TeamsClient({ initialLeagueGroups, allTeams }: TeamsClientProps) {
  const styles = useStyles();
  const [selectedLeague, setSelectedLeague] = useState<string>("all");
  const [searchQuery, setSearchQuery] = useState<string>("");

  // フィルタリング処理（リーグ & 検索キーワード）
  const filteredLeagueGroups = useMemo(() => {
    const query = searchQuery.trim().toLowerCase();

    return initialLeagueGroups
      .filter((lg) => selectedLeague === "all" || lg.league_name === selectedLeague)
      .map((lg) => {
        const filteredDivisions = lg.divisions
          .map((div) => {
            const filteredTeams = div.teams.filter((team) => {
              if (!query) return true;
              return (
                team.name.toLowerCase().includes(query) ||
                team.abbreviation.toLowerCase().includes(query)
              );
            });
            return {
              ...div,
              teams: filteredTeams,
            };
          })
          .filter((div) => div.teams.length > 0);

        return {
          ...lg,
          divisions: filteredDivisions,
        };
      })
      .filter((lg) => lg.divisions.length > 0);
  }, [initialLeagueGroups, selectedLeague, searchQuery]);

  const totalVisibleTeams = useMemo(() => {
    return filteredLeagueGroups.reduce(
      (sum, lg) => sum + lg.divisions.reduce((divSum, d) => divSum + d.teams.length, 0),
      0
    );
  }, [filteredLeagueGroups]);

  return (
    <div className={styles.container}>
      {/* Header Navigation */}
      <header className={styles.headerNav}>
        <Link href="/" className={styles.backLink}>
          <Button appearance="subtle" icon={<ArrowLeft16Regular />}>
            ホームへ戻る
          </Button>
        </Link>
        <div style={{ display: "flex", alignItems: "center", columnGap: "8px" }}>
          <Badge appearance="filled" color="brand">
            全 {allTeams.length} 球団
          </Badge>
          <Badge appearance="tint" color="informative">
            PostgreSQL teams
          </Badge>
        </div>
      </header>

      {/* Hero Banner */}
      <section className={styles.heroBanner}>
        <div style={{ display: "flex", alignItems: "center", columnGap: "8px" }}>
          <PeopleTeam24Regular style={{ color: tokens.colorBrandForeground1 }} />
          <Title1>MLB チーム一覧</Title1>
        </div>
        <Subtitle2 style={{ color: tokens.colorNeutralForeground2 }}>
          アメリカン・リーグ（AL）およびナショナル・リーグ（NL）の全30球団一覧
        </Subtitle2>
        <Body1 style={{ color: tokens.colorNeutralForeground3 }}>
          各球団を選択すると、所属選手一覧（ロスター）および選手詳細・AI解説レポートへアクセスできます。
        </Body1>
      </section>

      {/* Filter and Search Controls */}
      <div className={styles.controlsRow}>
        <TabList
          selectedValue={selectedLeague}
          onTabSelect={(_, data) => setSelectedLeague(String(data.value))}
        >
          <Tab value="all" icon={<Shield24Regular />}>
            すべての球団 ({allTeams.length})
          </Tab>
          <Tab value="American League">
            アメリカン・リーグ (AL)
          </Tab>
          <Tab value="National League">
            ナショナル・リーグ (NL)
          </Tab>
        </TabList>

        <Input
          className={styles.searchInput}
          placeholder="球団名や略称で絞り込み (例: NYY, Dodgers)"
          value={searchQuery}
          onChange={(_, data) => setSearchQuery(data.value)}
          contentBefore={<Search20Regular />}
        />
      </div>

      {/* Team Divisions and Cards */}
      {filteredLeagueGroups.length === 0 ? (
        <div className={styles.emptyState}>
          <Filter20Regular style={{ fontSize: "36px", color: tokens.colorNeutralForeground3 }} />
          <Title3 style={{ marginTop: "12px" }}>該当する球団が見つかりませんでした</Title3>
          <Body1 style={{ color: tokens.colorNeutralForeground3, marginTop: "8px" }}>
            検索条件「{searchQuery}」に一致するチームがありません。検索キーワードを変更してください。
          </Body1>
          <Button
            style={{ marginTop: "16px" }}
            appearance="secondary"
            onClick={() => setSearchQuery("")}
          >
            検索条件をクリア
          </Button>
        </div>
      ) : (
        filteredLeagueGroups.map((league) => (
          <div key={league.league_name} style={{ display: "flex", flexDirection: "column", rowGap: "24px" }}>
            {league.divisions.map((division) => (
              <section key={division.division_name} className={styles.divisionSection}>
                <div className={styles.divisionHeader}>
                  <Title3>{division.division_label_ja}</Title3>
                  <Caption1 style={{ color: tokens.colorNeutralForeground3 }}>
                    ({division.division_name})
                  </Caption1>
                  <Badge size="small" appearance="tint" color="brand">
                    {division.teams.length} チーム
                  </Badge>
                </div>

                <div className={styles.teamGrid}>
                  {division.teams.map((team) => (
                    <Card key={team.team_id} className={styles.teamCard}>
                      <CardHeader
                        header={
                          <Text weight="semibold" size={400}>
                            {team.name}
                          </Text>
                        }
                        description={<Caption1>{division.division_name}</Caption1>}
                        action={
                          <Badge
                            className={styles.abbreviationBadge}
                            appearance="filled"
                            color={team.league_name === "American League" ? "brand" : "danger"}
                          >
                            {team.abbreviation}
                          </Badge>
                        }
                      />
                      <CardFooter style={{ marginTop: "auto", paddingTop: "12px" }}>
                        <Link
                          href={`/teams/${team.team_id}`}
                          style={{ textDecoration: "none", width: "100%" }}
                        >
                          <Button
                            style={{ width: "100%" }}
                            appearance="primary"
                            size="medium"
                            icon={<ArrowRight16Regular />}
                            iconPosition="after"
                          >
                            選手一覧を見る
                          </Button>
                        </Link>
                      </CardFooter>
                    </Card>
                  ))}
                </div>
              </section>
            ))}
          </div>
        ))
      )}

      {/* Summary Footer */}
      <footer className={styles.footer}>
        <Caption1>
          現在表示中: {totalVisibleTeams} / 30 球団 &bull; PostgreSQL 連携
        </Caption1>
      </footer>
    </div>
  );
}
