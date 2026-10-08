import { DeskChatRequest, DeskChatResponse, DeskGenerateRequest, DeskGenerateResponse } from "@/types/desk";
import { runArticleGenerator } from "./python-runner";

const ARTICLE_GENERATOR_URL =
  process.env.ARTICLE_GENERATOR_URL || "http://localhost:8002";

export async function sendDeskChat(
  messages: DeskChatRequest["messages"]
): Promise<DeskChatResponse> {
  // 1. Try HTTP API first
  if (ARTICLE_GENERATOR_URL) {
    try {
      const res = await fetch(`${ARTICLE_GENERATOR_URL}/api/desk/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ messages }),
        signal: AbortSignal.timeout(60000), // 60s timeout for LLM
      });

      if (res.ok) {
        return (await res.json()) as DeskChatResponse;
      }

      // If server returned a business error (4xx/5xx), try to read error detail
      const errText = await res.text();
      let errMsg = `Article generator returned HTTP ${res.status}`;
      try {
        const errJson = JSON.parse(errText);
        if (errJson.detail) errMsg = errJson.detail;
        if (errJson.error) errMsg = errJson.error;
      } catch {
        if (errText) errMsg = errText;
      }

      // If it's a 4xx client error, don't fallback to CLI
      if (res.status >= 400 && res.status < 500) {
        throw new Error(errMsg);
      }

      console.warn(
        `Article generator HTTP request failed (${res.status}), attempting CLI fallback...`,
        errMsg
      );
    } catch (httpError: unknown) {
      // If it's a 4xx error we explicitly threw, rethrow
      if (
        httpError instanceof Error &&
        !httpError.message.includes("fetch failed") &&
        !httpError.message.includes("ECONNREFUSED") &&
        !httpError.message.includes("TimeoutError")
      ) {
        throw httpError;
      }

      console.warn(
        `Failed to reach article-generator at ${ARTICLE_GENERATOR_URL}. Attempting local CLI fallback...`,
        httpError
      );
    }
  }

  // 2. Fallback to local Python runner (CLI)
  const payloadStr = JSON.stringify({ messages });
  const result = await runArticleGenerator(["--desk-chat-json", payloadStr]);

  if (result.exitCode !== 0 && !result.stdout) {
    throw new Error(result.stderr || "Desk agent execution failed via CLI");
  }

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
    throw new Error(
      `Failed to parse agent response from CLI: ${result.stdout.slice(0, 200)}`
    );
  }

  return JSON.parse(jsonLine) as DeskChatResponse;
}

export async function sendDeskGenerate(
  proposal: DeskGenerateRequest["proposal"]
): Promise<DeskGenerateResponse> {
  // 1. Try HTTP API first
  if (ARTICLE_GENERATOR_URL) {
    try {
      const res = await fetch(`${ARTICLE_GENERATOR_URL}/api/desk/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ proposal }),
        signal: AbortSignal.timeout(180000), // 3 min timeout for multi-material synthesis
      });

      if (res.ok) {
        return (await res.json()) as DeskGenerateResponse;
      }

      const errText = await res.text();
      let errMsg = `Article generator returned HTTP ${res.status}`;
      try {
        const errJson = JSON.parse(errText);
        if (errJson.detail) errMsg = errJson.detail;
        if (errJson.error) errMsg = errJson.error;
      } catch {
        if (errText) errMsg = errText;
      }

      if (res.status >= 400 && res.status < 500) {
        throw new Error(errMsg);
      }

      console.warn(
        `Article generator HTTP generate failed (${res.status}), attempting CLI fallback...`,
        errMsg
      );
    } catch (httpError: unknown) {
      if (
        httpError instanceof Error &&
        !httpError.message.includes("fetch failed") &&
        !httpError.message.includes("ECONNREFUSED") &&
        !httpError.message.includes("TimeoutError")
      ) {
        throw httpError;
      }

      console.warn(
        `Failed to reach article-generator at ${ARTICLE_GENERATOR_URL}. Attempting local CLI fallback...`,
        httpError
      );
    }
  }

  // 2. Fallback to local Python runner (CLI)
  const configStr = JSON.stringify(proposal);
  const result = await runArticleGenerator(["--generate-multi-article", configStr]);

  if (result.exitCode !== 0) {
    throw new Error(result.stderr || "Multi article generation failed via CLI");
  }

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
    throw new Error("Article ID not found in generator response via CLI");
  }

  return {
    success: true,
    article_id: articleId,
    title: title || proposal.title,
  };
}
