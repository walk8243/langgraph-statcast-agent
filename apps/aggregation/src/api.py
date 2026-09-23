"""Cloud Pub/Sub へ集計要求を送信する Aggregation 実行用 REST API モジュール"""

from __future__ import annotations

import json
import logging
import os
from typing import Any, Optional
from fastapi import FastAPI, HTTPException, status
from google.cloud import pubsub_v1
from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger("aggregation.api")

app = FastAPI(
    title="Statcast Aggregation API",
    description="Statcast 指標集計要求を Cloud Pub/Sub に発行して非同期集計をトリガーする API サービス",
    version="0.1.0",
)


class AggregateRequest(BaseModel):
    """集計リクエストボディモデル"""

    player_id: int = Field(..., description="MLB 選手ID (例: 660271)")
    year: Optional[int] = Field(None, description="集計対象シーズン (例: 2024, None の場合は全年度)")
    player_type: str = Field(
        default="both",
        description="集計対象の選手タイプ ('batter', 'pitcher', 'both', デフォルト: both)",
    )

    @field_validator("player_type")
    @classmethod
    def validate_player_type(cls, v: str) -> str:
        valid_types = ("batter", "pitcher", "both")
        if v not in valid_types:
            raise ValueError(f"Invalid player_type: '{v}'. Must be one of {valid_types}.")
        return v


def publish_aggregation_request(
    player_id: int,
    year: Optional[int] = None,
    player_type: str = "both",
    project_id: Optional[str] = None,
    topic_id: Optional[str] = None,
    timeout: float = 10.0,
) -> str:
    """Pub/Sub トピックへ集計トリガーメッセージを発行する"""
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

        logger.info(f"Pub/Sub へ集計メッセージを発行中: topic={topic_path}, payload={payload}")
        future = publisher.publish(topic_path, data=data_bytes)
        message_id = future.result(timeout=timeout)
        logger.info(f"Pub/Sub メッセージを発行しました (message_id={message_id})")
        return str(message_id)
    except Exception as e:
        logger.error(f"Pub/Sub へのメッセージ発行に失敗しました: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Failed to publish aggregation message to Pub/Sub: {str(e)}",
        ) from e


@app.get("/health", status_code=status.HTTP_200_OK)
def health_check() -> dict[str, str]:
    """サービスのヘルスチェックエンドポイント"""
    return {"status": "healthy"}


@app.post("/aggregate", status_code=status.HTTP_202_ACCEPTED)
@app.post("/api/aggregate", status_code=status.HTTP_202_ACCEPTED)
def queue_aggregation(request: AggregateRequest) -> dict[str, Any]:
    """指定した選手の Statcast 集計要求を Pub/Sub トピックへ投入する (202 Accepted)"""
    message_id = publish_aggregation_request(
        player_id=request.player_id,
        year=request.year,
        player_type=request.player_type,
    )
    return {
        "status": "accepted",
        "message": "Aggregation request queued successfully",
        "message_id": message_id,
        "data": {
            "player_id": request.player_id,
            "year": request.year,
            "player_type": request.player_type,
        },
    }
