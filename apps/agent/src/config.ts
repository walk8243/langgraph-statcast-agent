import dotenv from "dotenv";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// プロジェクトルートの .env も読み込むように設定
dotenv.config({ path: path.resolve(__dirname, "../../../.env") });
dotenv.config();

export interface Config {
  postgres: {
    host: string;
    port: number;
    database: string;
    user: string;
    password?: string;
  };
  gemini: {
    apiKey?: string;
    model: string;
  };
}

export const config: Config = {
  postgres: {
    host: process.env.POSTGRES_HOST || "localhost",
    port: Number.parseInt(process.env.POSTGRES_PORT || "5432", 10),
    database: process.env.POSTGRES_DB || "statcast",
    user: process.env.POSTGRES_USER || "statcast",
    password: process.env.POSTGRES_PASSWORD || "statcast_pass",
  },
  gemini: {
    apiKey: process.env.GEMINI_API_KEY,
    model: process.env.GEMINI_MODEL || "gemini-3.8-flash",
  },
};
