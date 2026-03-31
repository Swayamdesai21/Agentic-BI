import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Agentic BI — Natural Language Business Intelligence",
  description:
    "Ask questions in plain English, get live business dashboards powered by AI agents. Built with LangGraph, Groq, and Next.js.",
  keywords: ["business intelligence", "AI dashboard", "natural language", "data analytics", "LangGraph"],
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <head>
        <link
          href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="antialiased bg-grid-pattern">
        {children}
      </body>
    </html>
  );
}
