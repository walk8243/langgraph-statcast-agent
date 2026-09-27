/**
 * Cloud Pub/Sub イベント発行クライアントモジュール (mlb-live-events)
 */

import { PubSub, Topic } from "@google-cloud/pubsub";
import { LiveEvent } from "./types.js";

export class LiveEventPublisher {
  private pubsub: PubSub;
  private topic: Topic;
  public projectId: string;
  public topicId: string;

  constructor(projectId?: string, topicId?: string) {
    this.projectId = projectId || process.env.GCP_PROJECT_ID || "local-statcast-project";
    this.topicId = topicId || process.env.PUBSUB_TOPIC_LIVE_EVENTS || "mlb-live-events";
    this.pubsub = new PubSub({ projectId: this.projectId });
    this.topic = this.pubsub.topic(this.topicId);
  }

  /**
   * 単一の速報イベントを発行する
   */
  async publishEvent(event: LiveEvent): Promise<string | null> {
    try {
      const dataBuffer = Buffer.from(JSON.stringify(event));
      const messageId = await this.topic.publishMessage({
        data: dataBuffer,
        attributes: {
          game_pk: String(event.game_pk),
          event_type: event.event_type,
        },
      });
      return messageId;
    } catch (error) {
      console.warn(`Failed to publish live event to Pub/Sub:`, error);
      return null;
    }
  }

  /**
   * 複数の速報イベントを順次発行する
   */
  async publishEvents(events: LiveEvent[]): Promise<number> {
    let count = 0;
    for (const ev of events) {
      const msgId = await this.publishEvent(ev);
      if (msgId) {
        count++;
      }
    }
    return count;
  }
}
