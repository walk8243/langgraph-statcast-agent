import json
import logging
import os
from typing import Any, Dict, Optional

from google.cloud import pubsub_v1

logger = logging.getLogger(__name__)


class TriggerPublisher:
    """Publisher for triggering asynchronous workflows via Cloud Pub/Sub."""

    def __init__(
        self,
        project_id: Optional[str] = None,
        topic_id: Optional[str] = None,
    ) -> None:
        self.project_id = project_id or os.getenv("GCP_PROJECT_ID", "local-statcast-project")
        self.topic_id = topic_id or os.getenv("PUBSUB_TOPIC_STATCAST_RAW", "statcast-raw-ingested")
        self._publisher: Optional[pubsub_v1.PublisherClient] = None

    @property
    def publisher(self) -> pubsub_v1.PublisherClient:
        if self._publisher is None:
            self._publisher = pubsub_v1.PublisherClient()
        return self._publisher

    @property
    def topic_path(self) -> str:
        return f"projects/{self.project_id}/topics/{self.topic_id}"

    def publish_aggregate_request(
        self,
        player_id: int,
        year: Optional[int] = None,
        player_type: str = "both",
    ) -> str:
        """Publishes an aggregate trigger message to Cloud Pub/Sub.

        Returns:
            The published message ID.
        """
        payload: Dict[str, Any] = {
            "player_id": player_id,
            "year": year,
            "player_type": player_type,
        }
        data = json.dumps(payload).encode("utf-8")

        logger.info(
            "Publishing trigger message to %s: %s",
            self.topic_path,
            payload,
        )

        future = self.publisher.publish(self.topic_path, data=data)
        message_id = future.result()
        logger.info("Successfully published message with ID: %s", message_id)
        return message_id
