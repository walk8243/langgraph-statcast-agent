import { spawn } from "child_process";
import path from "path";
import fs from "fs";

function resolveArticleGeneratorDir(): string {
  const candidates = [
    path.resolve(process.cwd(), "../article-generator"),
    path.resolve(process.cwd(), "apps/article-generator"),
    path.resolve(__dirname, "../../../../article-generator"),
  ];

  for (const dir of candidates) {
    if (fs.existsSync(/*turbopackIgnore: true*/ path.join(dir, "src/main.py"))) {
      return dir;
    }
  }

  return candidates[0];
}

export interface PythonRunResult {
  stdout: string;
  stderr: string;
  exitCode: number;
}

export async function runArticleGenerator(args: string[]): Promise<PythonRunResult> {
  const cwd = resolveArticleGeneratorDir();

  if (!fs.existsSync(/*turbopackIgnore: true*/ cwd)) {
    return {
      stdout: "",
      stderr: `Article generator directory not found: ${cwd}. Please ensure ARTICLE_GENERATOR_URL is configured.`,
      exitCode: 1,
    };
  }

  return new Promise((resolve, reject) => {
    // Try uv run python first, with fallback to python
    const isWindows = process.platform === "win32";
    const command = isWindows ? "cmd.exe" : "sh";
    const scriptArgs = isWindows
      ? ["/c", "uv", "run", "python", "-m", "src.main", ...args]
      : ["-c", `uv run python -m src.main ${args.map((a) => `"${a.replace(/"/g, '\\"')}"`).join(" ")}`];

    const proc = spawn(command, scriptArgs, {
      cwd,
      env: { ...process.env, PYTHONIOENCODING: "utf-8" },
    });

    let stdout = "";
    let stderr = "";

    proc.stdout.on("data", (data) => {
      stdout += data.toString("utf-8");
    });

    proc.stderr.on("data", (data) => {
      stderr += data.toString("utf-8");
    });

    proc.on("error", (err) => {
      reject(err);
    });

    proc.on("close", (exitCode) => {
      resolve({
        stdout: stdout.trim(),
        stderr: stderr.trim(),
        exitCode: exitCode ?? 0,
      });
    });
  });
}
