import { NextRequest, NextResponse } from "next/server";
import { sendDeskChat } from "@/lib/article-generator-client";
import { DeskChatRequest } from "@/types/desk";

export async function POST(req: NextRequest) {
  try {
    const body = (await req.json()) as DeskChatRequest;
    if (!body || !Array.isArray(body.messages) || body.messages.length === 0) {
      return NextResponse.json(
        { error: "messages array is required" },
        { status: 400 }
      );
    }

    const response = await sendDeskChat(body.messages);
    return NextResponse.json(response);
  } catch (error) {
    console.error("API error in desk chat:", error);
    return NextResponse.json(
      { error: error instanceof Error ? error.message : "Internal Server Error" },
      { status: 500 }
    );
  }
}
