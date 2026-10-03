import { PubSub, type Subscription, type Message } from "@google-cloud/pubsub";
import type { ConnectionManager } from "./manager.js";
import type { LiveEvent } from "./types.js";

export class LiveEventSubscriber {
  private pubsub: PubSub;
  private subscription: Subscription;
  private isRunning: boolean = false;

  constructor(
    public readonly projectId: string,
    public readonly subscriptionId: string,
    private readonly manager: ConnectionManager,
  ) {
    this.pubsub = new PubSub({ projectId: this.projectId });
    this.subscription = this.pubsub.subscription(this.subscriptionId);
  }

  /**
   * Pub/Sub サブスクリプションからのイベント受信を開始する
   */
  start(): void {
    if (this.isRunning) {
      return;
    }
    this.isRunning = true;

    this.subscription.on("message", (message: Message) => {
      try {
        const raw = message.data.toString("utf-8");
        const event = JSON.parse(raw) as LiveEvent;

        if (event && typeof event.game_pk === "number" && typeof event.event_type === "string") {
          this.manager.broadcast(event);
        }

        message.ack();
      } catch (err) {
        console.error("Error processing live event message:", err);
        // パース不能な不正メッセージでも永久ループを防ぐため ack またはログ出力後に適切に処理
        message.ack();
      }
    });

    this.subscription.on("error", (err: unknown) => {
      console.error("LiveEventSubscriber subscription error:", err);
    });

    console.log(`LiveEventSubscriber started on subscription: ${this.subscriptionId}`);
  }

  /**
   * サブスクリプションを停止する
   */
  async stop(): Promise<void> {
    if (!this.isRunning) {
      return;
    }
    this.isRunning = false;

    try {
      this.subscription.removeAllListeners();
      await this.subscription.close();
      await this.pubsub.close();
      console.log(`LiveEventSubscriber stopped.`);
    } catch (err) {
      console.error("Error stopping LiveEventSubscriber:", err);
    }
  }

  getRunning(): boolean {
    return this.isRunning;
  }
}
