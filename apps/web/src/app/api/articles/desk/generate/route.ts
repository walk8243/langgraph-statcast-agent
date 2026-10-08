import { NextRequest, NextResponse } from "next/server";
import { runArticleGenerator } from "@/lib/python-runner";
import { DeskGenerateRequest, DeskGenerateResponse } from "@/types/desk";

export async function POST(req: NextRequest) {
  try {
    const body = (await req.json()) as DeskGenerateRequest;
    if (!body || !body.proposal) {
      return NextResponse.json(
        { error: "proposal object is required" },
        { status: 400 }
      );
    }

    const configStr = JSON.stringify(body.proposal);
    const result = await runArticleGenerator(["--generate-multi-article", configStr]);

    if (result.exitCode !== 0) {
      console.error("Multi article generation error:", result.stderr);
      return NextResponse.json(
        { error: result.stderr || "Multi article generation failed" },
        { status: 500 }
      );
    }

    // Parse article ID from JSON_RESULT or regex
    let articleId: number | undefined;
    let title: string | undefined;

    const markerMatch = result.stdout.match(/JSON_RESULT:(.+)/);
    if (markerMatch) {
      try {
        const parsedMarker = JSON.parse(markerMatch[1]);
        articleId = parsedMarker.article_id;
        title = parsedMarker.title;
      } catch (e) {
        console.warn("Failed to parse JSON_RESULT:", e);
      }
    }

    if (!articleId) {
      const match = result.stdout.match(/Article Saved with ID:\s*(\d+)/i);
      if (match) {
        articleId = parseInt(match[1], 10);
      }
    }

    if (!articleId) {
      console.error("Failed to parse generated article ID from output:", result.stdout);
      return NextResponse.json(
        { error: "Article ID not found in generator response" },
        { status: 500 }
      );
    }

    const responseData: DeskGenerateResponse = {
      success: true,
      article_id: articleId,
      title: title || body.proposal.title,
    };

    return NextResponse.json(responseData);
  } catch (error) {
    console.error("API error in multi article generate:", error);
    return NextResponse.json(
      { error: error instanceof Error ? error.message : "Internal Server Error" },
      { status: 500 }
    );
  }
}
