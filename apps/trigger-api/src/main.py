import argparse
import logging
from typing import Any, Dict, Literal, Optional

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field
import uvicorn

from .publisher import TriggerPublisher

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("trigger-api")

app = FastAPI(
    title="Statcast Trigger API",
    description="REST API to trigger asynchronous workflows via Cloud Pub/Sub",
    version="0.1.0",
)

publisher = TriggerPublisher()


class AggregateRequest(BaseModel):
    player_id: int = Field(
        ...,
        description="MLB Player ID (MLBAM ID)",
        gt=0,
        examples=[660271],
    )
    year: Optional[int] = Field(
        None,
        description="Target season year (None for all available years)",
        ge=1900,
        le=2100,
        examples=[2024],
    )
    player_type: Literal["batter", "pitcher", "both"] = Field(
        "both",
        description="Target player type for aggregation",
        examples=["batter"],
    )


class AggregateResponse(BaseModel):
    status: str = "accepted"
    message_id: str
    data: Dict[str, Any]


@app.get("/health", tags=["Health"])
def health_check() -> Dict[str, str]:
    """Health check endpoint."""
    return {
        "status": "healthy",
        "topic": publisher.topic_path,
    }


@app.post(
    "/aggregate",
    response_model=AggregateResponse,
    status_code=status.HTTP_202_ACCEPTED,
    tags=["Aggregation Trigger"],
    summary="Trigger Statcast aggregation asynchronously",
)
@app.post(
    "/api/aggregate",
    response_model=AggregateResponse,
    status_code=status.HTTP_202_ACCEPTED,
    include_in_schema=False,
)
def trigger_aggregate(request: AggregateRequest) -> AggregateResponse:
    """Publishes an aggregation trigger message to Cloud Pub/Sub.

    Returns HTTP 202 Accepted immediately upon message publishing.
    """
    try:
        message_id = publisher.publish_aggregate_request(
            player_id=request.player_id,
            year=request.year,
            player_type=request.player_type,
        )
        return AggregateResponse(
            status="accepted",
            message_id=message_id,
            data=request.model_dump(),
        )
    except Exception as e:
        logger.error("Failed to publish aggregate message: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to publish trigger message: {e}",
        ) from e


def main() -> None:
    parser = argparse.ArgumentParser(description="Statcast Trigger API Server")
    parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="Host to bind the API server (default: 0.0.0.0)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to bind the API server (default: 8000)",
    )
    args = parser.parse_args()

    logger.info("Starting Trigger API server on %s:%d", args.host, args.port)
    uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
