import pg from "pg";

const { Pool } = pg;

// Next.js hot-reloading safe singleton pool pattern
const globalForPg = globalThis as unknown as {
  pgPool?: pg.Pool;
};

export const pool =
  globalForPg.pgPool ??
  new Pool({
    host: process.env.POSTGRES_HOST || "localhost",
    port: Number.parseInt(process.env.POSTGRES_PORT || "5432", 10),
    database: process.env.POSTGRES_DB || "statcast",
    user: process.env.POSTGRES_USER || "statcast",
    password: process.env.POSTGRES_PASSWORD || "statcast_pass",
  });

if (process.env.NODE_ENV !== "production") {
  globalForPg.pgPool = pool;
}

export async function query<T extends pg.QueryResultRow = pg.QueryResultRow>(
  text: string,
  params?: unknown[]
): Promise<pg.QueryResult<T>> {
  return pool.query<T>(text, params);
}
