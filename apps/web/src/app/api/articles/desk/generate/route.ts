import { NextRequest, NextResponse } from "next/server";
import { sendDeskGenerate } from "@/lib/article-generator-client";
import { DeskGenerateRequest } from "@/types/desk";

export async function POST(req: NextRequest) {
  try {
    const body = (await req.json()) as DeskGenerateRequest;
    if (!body || !body.proposal) {
      return NextResponse.json(
        { error: "proposal object is required" },
        { status: 400 }
      );
    }

    const response = await sendDeskGenerate(body.proposal);
    return NextResponse.json(response);
  } catch (error) {
    console.error("API error in multi article generate:", error);
    return NextResponse.json(
      { error: error instanceof Error ? error.message : "Internal Server Error" },
      { status: 500 }
    );
  }
}
