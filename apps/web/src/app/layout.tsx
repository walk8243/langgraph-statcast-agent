import type { Metadata } from "next";
import { Providers } from "./providers";
import "./globals.css";

export const metadata: Metadata = {
  title: "MLB Statcast Agent Dashboard",
  description:
    "MLB Statcast analytics and LangGraph AI agent dashboard built with Next.js and Microsoft Fluent UI",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ja">
      <body>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
