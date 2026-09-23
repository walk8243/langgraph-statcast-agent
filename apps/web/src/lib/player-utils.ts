import { Player, PositionGroup } from "@/types/player";

/**
 * ポジション種別ごとの表示順および日本語ラベル
 */
const POSITION_GROUP_CONFIG: Record<
  string,
  { nameJa: string; nameEn: string; order: number }
> = {
  Pitcher: { nameJa: "投手", nameEn: "Pitchers", order: 1 },
  Catcher: { nameJa: "捕手", nameEn: "Catchers", order: 2 },
  Infielder: { nameJa: "内野手", nameEn: "Infielders", order: 3 },
  Outfielder: { nameJa: "外野手", nameEn: "Outfielders", order: 4 },
  "Two-Way Player": { nameJa: "二刀流", nameEn: "Two-Way Players", order: 5 },
  "Designated Hitter": { nameJa: "指名打者", nameEn: "Designated Hitters", order: 6 },
  Other: { nameJa: "その他", nameEn: "Other", order: 99 },
};

/**
 * 選手一覧をポジション種別ごとにグルーピングする
 */
export function groupPlayersByPosition(players: Player[]): PositionGroup[] {
  const groups: Record<string, Player[]> = {};

  for (const player of players) {
    const rawType = player.primary_position_type || "Other";
    const groupKey = POSITION_GROUP_CONFIG[rawType] ? rawType : "Other";

    if (!groups[groupKey]) {
      groups[groupKey] = [];
    }
    groups[groupKey].push(player);
  }

  const result: PositionGroup[] = [];

  for (const [key, groupPlayers] of Object.entries(groups)) {
    const config = POSITION_GROUP_CONFIG[key] || {
      nameJa: key,
      nameEn: key,
      order: 99,
    };

    result.push({
      group_key: key,
      group_name_ja: config.nameJa,
      group_name_en: config.nameEn,
      order: config.order,
      players: groupPlayers,
    });
  }

  // 表示順序でソート
  return result.sort((a, b) => a.order - b.order);
}

/**
 * 投打表記の日本語フォーマットヘルパー
 */
export function formatBatsThrows(
  batSide: string | null | undefined,
  pitchHand: string | null | undefined
): string {
  const batsMap: Record<string, string> = {
    R: "右打",
    L: "左打",
    S: "両打",
  };
  const throwsMap: Record<string, string> = {
    R: "右投",
    L: "左投",
  };

  const bats = batSide ? (batsMap[batSide] ?? batSide) : "";
  const throws_ = pitchHand ? (throwsMap[pitchHand] ?? pitchHand) : "";

  if (throws_ && bats) {
    return `${throws_} / ${bats}`;
  }
  return throws_ || bats || "-";
}
