import type { Metadata } from "next";

import { PwaRegister } from "@/components/pwa-register";
import { RouteGuard } from "@/components/route-guard";
import "./globals.css";

export const metadata: Metadata = {
  title: "FitMatch",
  description: "FitMatch auth, onboarding, and resume ingestion",
  manifest: "/manifest.webmanifest",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="h-full antialiased">
      <body className="min-h-full flex flex-col">
        <PwaRegister />
        <RouteGuard>{children}</RouteGuard>
      </body>
    </html>
  );
}
