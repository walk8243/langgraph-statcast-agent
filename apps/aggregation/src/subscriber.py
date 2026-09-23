"""Cloud Pub/Sub サブスクリプション受信常駐ワーカーモジュール"""

from __future__ import annotations

import json
import logging
import os
import signal
import sys
from typing import Any, Callable, Optional
from google.cloud import pubsub_v1
from pydantic import BaseModel, Field, ValidationError

from src.main import aggregate_batter_statcast, aggregate_pitcher_statcast

logger = logging.getLogger("aggregation.subscriber")


class AggregationMessage(BaseModel):
    """Pub/Sub から受信する集計リクエストメッセージのスキーマ"""

    player_id: int = Field(..., description="MLB 選手 ID")
    year: Optional[int] = Field(None, description="対象年度 (None の場合は全年度)")
    player_type: str = Field(
        default="both",
        description="集計対象の選手タイプ ('batter', 'pitcher', 'both')",
    )

    def validate_player_type(self) -> None:
        if self.player_type not in ("batter", "pitcher", "both"):
            raise ValueError(
                f"Invalid player_type: {self.player_type}. Must be 'batter', 'pitcher', or 'both'."
            )


def process_aggregation_payload(payload_bytes: bytes) -> bool:
    """Pub/Sub メッセージのペイロードをパースして集計処理を実行する

    Args:
        payload_bytes: メッセージのバイナリデータ (JSON 文字列)

    Returns:
        bool: 処理成功時は True、致命的エラー時は False
    """
    try:
        raw_text = payload_bytes.decode("utf-8")
        data = json.loads(raw_text)
    except Exception as e:
        logger.error(f"メッセージの JSON パースに失敗しました (Poison Pill): {e}")
        # 不正な JSON は再送しても失敗するため、正常終了(True)扱いとして ACK させる
        return True

    try:
        req = AggregationMessage(**data)
        req.validate_player_type()
    except (ValidationError, ValueError) as e:
        logger.error(f"メッセージのバリデーションに失敗しました (Poison Pill): {e}, data: {data}")
        # スキーマ不一致も再試行不可のため ACK させる
        return True

    logger.info(
        f"集計リクエストを受信: player_id={req.player_id}, year={req.year}, player_type={req.player_type}"
    )

    try:
        if req.player_type in ("batter", "both"):
            logger.info(f"打者 Statcast 指標を集計中 (player_id={req.player_id}, year={req.year})...")
            aggregate_batter_statcast(player_id=req.player_id, year=req.year)

        if req.player_type in ("pitcher", "both"):
            logger.info(f"投手 Statcast 指標を集計中 (player_id={req.player_id}, year={req.year})...")
            aggregate_pitcher_statcast(player_id=req.player_id, year=req.year)

        logger.info(
            f"集計処理が正常に完了しました: player_id={req.player_id}, year={req.year}, player_type={req.player_type}"
        )
        return True
    except Exception as e:
        logger.error(
            f"集計処理中に一時的または予期しない例外が発生しました: {e}",
            exc_info=True,
        )
        # DB接続断などの一時的例外は再試行(NACK)させる
        return False


def create_message_callback() -> Callable[[pubsub_v1.subscriber.message.Message], None]:
    """Pub/Sub メッセージを処理するコールバック関数を生成する"""

    def callback(message: pubsub_v1.subscriber.message.Message) -> None:
        logger.info(f"Pub/Sub メッセージ受信 (message_id={message.message_id})")
        success = process_aggregation_payload(message.data)
        if success:
            message.ack()
            logger.debug(f"メッセージ ACK 完了 (message_id={message.message_id})")
        else:
            message.nack()
            logger.warning(f"メッセージ NACK 完了 (message_id={message.message_id})")

    return callback


def run_subscriber(
    project_id: Optional[str] = None,
    subscription_id: Optional[str] = None,
) -> None:
    """Cloud Pub/Sub サブスクリプションを購読する常駐ワーカーを起動する"""
    project_id = project_id or os.getenv("GCP_PROJECT_ID", "local-statcast-project")
    subscription_id = subscription_id or os.getenv(
        "PUBSUB_SUBSCRIPTION_STATCAST_RAW", "statcast-raw-ingested-sub"
    )

    emulator_host = os.getenv("PUBSUB_EMULATOR_HOST")
    if emulator_host:
        logger.info(f"Pub/Sub エミュレータに接続します: {emulator_host}")

    subscriber = pubsub_v1.SubscriberClient()
    subscription_path = subscriber.subscription_path(project_id, subscription_id)

    logger.info(f"サブスクリプションの購読を開始します: {subscription_path}")

    callback = create_message_callback()
    streaming_pull_future = subscriber.subscribe(
        subscription_path,
        callback=callback,
    )

    def shutdown(signum: int, frame: Any) -> None:
        logger.info(f"シャットダウンシグナル ({signum}) を受信しました。ワーカーを停止します...")
        streaming_pull_future.cancel()

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    logger.info("常駐ワーカーが起動しました。メッセージ待機中... (Ctrl+C で停止)")
    try:
        streaming_pull_future.result()
    except Exception as e:
        if not streaming_pull_future.cancelled():
            logger.error(f"ストリーミング購読中にエラーが発生しました: {e}", exc_info=True)
            streaming_pull_future.cancel()
            sys.exit(1)
    finally:
        subscriber.close()
        logger.info("常駐ワーカーを正常に終了しました。")
