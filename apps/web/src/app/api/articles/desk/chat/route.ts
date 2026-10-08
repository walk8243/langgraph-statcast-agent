import { NextRequest, NextResponse } from "next/server";
import { runArticleGenerator } from "@/lib/python-runner";
import { DeskChatRequest, DeskChatResponse } from "@/types/desk";

export async function POST(req: NextRequest) {
  try {
    const body = (await req.json()) as DeskChatRequest;
    if (!body || !Array.isArray(body.messages) || body.messages.length === 0) {
      return NextResponse.json(
        { error: "messages array is required" },
        { status: 400 }
      );
    }

    const payloadStr = JSON.stringify({ messages: body.messages });
    const result = await runArticleGenerator(["--desk-chat-json", payloadStr]);

    if (result.exitCode !== 0 && !result.stdout) {
      console.error("Desk chat Python error:", result.stderr);
      return NextResponse.json(
        { error: result.stderr || "Desk agent execution failed" },
        { status: 500 }
      );
    }

    // Parse the JSON output from stdout
    // Sometimes there might be logs before the JSON line
    const lines = result.stdout.split("\n");
    let jsonLine = "";
    for (let i = lines.length - 1; i >= 0; i--) {
      const line = lines[i].trim();
      if (line.startsWith("{") && line.endsWith("}")) {
        jsonLine = line;
        break;
      }
    }

    if (!jsonLine) {
      console.error("No JSON output found in stdout:", result.stdout);
      return NextResponse.json(
        { error: "Failed to parse agent response" },
        { status: 500 }
      );
    }

    const parsed: DeskChatResponse = JSON.parse(jsonLine);
    return NextResponse.json(parsed);
  } catch (error) {
    console.error("API error in desk chat:", error);
    return NextResponse.json(
      { error: error instanceof Error ? error.message : "Internal Server Error" },
      { status: 500 }
    );
  }
}
