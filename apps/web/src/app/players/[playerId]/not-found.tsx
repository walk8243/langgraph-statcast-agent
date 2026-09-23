"use client";

import React from "react";
import Link from "next/link";
import { Title1, Body1, Button } from "@fluentui/react-components";
import { ArrowLeft16Regular, ErrorCircle24Regular } from "@fluentui/react-icons";

export default function PlayerNotFound() {
  return (
    <div
      style={{
        maxWidth: "600px",
        margin: "80px auto",
        padding: "32px",
        textAlign: "center",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        rowGap: "16px",
      }}
    >
      <ErrorCircle24Regular style={{ fontSize: "48px", color: "#d13438" }} />
      <Title1>選手が見つかりませんでした</Title1>
      <Body1 style={{ color: "#605e5c" }}>
        指定された選手IDの選手は存在しないか、登録されていません。チームロスターまたは選手一覧から再度お選びください。
      </Body1>
      <Link href="/teams" style={{ textDecoration: "none", marginTop: "16px" }}>
        <Button appearance="primary" icon={<ArrowLeft16Regular />}>
          チーム一覧へ戻る
        </Button>
      </Link>
    </div>
  );
}
