#!/bin/sh
set -e

PUBSUB_HOST="${PUBSUB_HOST:-pubsub}"
PUBSUB_PORT="${PUBSUB_PORT:-8085}"
PROJECT_ID="${GCP_PROJECT_ID:-local-statcast-project}"
TOPIC_ID="${PUBSUB_TOPIC_STATCAST_RAW:-statcast-raw-ingested}"
SUB_ID="${PUBSUB_SUBSCRIPTION_STATCAST_RAW:-statcast-raw-ingested-sub}"
TOPIC_LIVE_EVENTS="${PUBSUB_TOPIC_LIVE_EVENTS:-mlb-live-events}"
SUB_LIVE_EVENTS="${PUBSUB_SUBSCRIPTION_LIVE_EVENTS:-mlb-live-events-sub}"

BASE_URL="http://${PUBSUB_HOST}:${PUBSUB_PORT}"

echo "Waiting for Pub/Sub emulator to be ready at ${BASE_URL}..."
until curl -s -f "${BASE_URL}" > /dev/null 2>&1; do
  sleep 1
done

echo "Pub/Sub emulator is ready."

echo "Creating topic: projects/${PROJECT_ID}/topics/${TOPIC_ID}"
curl -s -X PUT "${BASE_URL}/v1/projects/${PROJECT_ID}/topics/${TOPIC_ID}"
echo ""

echo "Creating subscription: projects/${PROJECT_ID}/subscriptions/${SUB_ID}"
curl -s -X PUT "${BASE_URL}/v1/projects/${PROJECT_ID}/subscriptions/${SUB_ID}" \
  -H "Content-Type: application/json" \
  -d "{\"topic\": \"projects/${PROJECT_ID}/topics/${TOPIC_ID}\"}"
echo ""

echo "Creating live events topic: projects/${PROJECT_ID}/topics/${TOPIC_LIVE_EVENTS}"
curl -s -X PUT "${BASE_URL}/v1/projects/${PROJECT_ID}/topics/${TOPIC_LIVE_EVENTS}"
echo ""

echo "Creating live events subscription: projects/${PROJECT_ID}/subscriptions/${SUB_LIVE_EVENTS}"
curl -s -X PUT "${BASE_URL}/v1/projects/${PROJECT_ID}/subscriptions/${SUB_LIVE_EVENTS}" \
  -H "Content-Type: application/json" \
  -d "{\"topic\": \"projects/${PROJECT_ID}/topics/${TOPIC_LIVE_EVENTS}\"}"
echo ""

echo "Pub/Sub initialization completed successfully."
