import type { Metadata } from "next";

import { RouteGuard } from "@/components/route-guard";
import "./globals.css";

export const metadata: Metadata = {
  title: "FitMatch",
  description: "FitMatch auth, onboarding, and resume ingestion",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="h-full antialiased">
      <body className="min-h-full flex flex-col">
        <RouteGuard>{children}</RouteGuard>
      </body>
    </html>
  );
}
