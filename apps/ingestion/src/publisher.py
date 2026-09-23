"""Cloud Pub/Sub メッセージ発行クライアントモジュール"""

from __future__ import annotations

import json
import logging
import os
from typing import Optional
from google.cloud import pubsub_v1

logger = logging.getLogger(__name__)


def publish_statcast_raw_message(
    player_id: int,
    year: Optional[int] = None,
    player_type: str = "both",
    project_id: Optional[str] = None,
    topic_id: Optional[str] = None,
    timeout: float = 10.0,
) -> Optional[str]:
    """Baseball Savant 生データ登録完了後に、集計トリガーメッセージを Cloud Pub/Sub へ発行する

    送信するデータは現在 Aggregation サービスが実行に使用しているパラメータのみに限定します。

    Args:
        player_id: MLB 選手ID
        year: 対象年度 (None の場合は全年度)
        player_type: 選手種別 ('batter', 'pitcher', 'both')
        project_id: GCP プロジェクトID (未指定時は環境変数またはデフォルト)
        topic_id: Pub/Sub トピックID (未指定時は環境変数またはデフォルト)
        timeout: メッセージ発行待機タイムアウト秒数

    Returns:
        発行された message_id (失敗時やエミュレータ未接続時は None)
    """
    if player_type not in ("batter", "pitcher", "both"):
        logger.warning(
            f"無効な player_type ('{player_type}') が指定されたため、Pub/Sub メッセージ発行をスキップします。"
        )
        return None

    project_id = project_id or os.getenv("GCP_PROJECT_ID", "local-statcast-project")
    topic_id = topic_id or os.getenv("PUBSUB_TOPIC_STATCAST_RAW", "statcast-raw-ingested")

    payload = {
        "player_id": player_id,
        "year": year,
        "player_type": player_type,
    }

    try:
        data_bytes = json.dumps(payload).encode("utf-8")
        publisher = pubsub_v1.PublisherClient()
        topic_path = publisher.topic_path(project_id, topic_id)

        logger.info(
            f"Pub/Sub トピックへメッセージを発行中: topic={topic_path}, payload={payload}"
        )
        future = publisher.publish(topic_path, data=data_bytes)
        message_id = future.result(timeout=timeout)
        logger.info(f"Pub/Sub メッセージの発行が完了しました (message_id={message_id})")
        return str(message_id)

    except Exception as e:
        # Ingestion 本体のデータ登録処理が中断・失敗しないようフォールバック
        logger.warning(
            f"Cloud Pub/Sub へのメッセージ発行に失敗しました (Ingestion処理は継続します): {e}",
            exc_info=True,
        )
        return None
