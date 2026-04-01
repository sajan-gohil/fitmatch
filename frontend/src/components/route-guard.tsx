"use client";

import { usePathname, useRouter } from "next/navigation";
import { useEffect } from "react";

import { getToken, isOnboardingCompleted } from "@/lib/auth";

const PROTECTED_ROUTES = new Set(["/onboarding", "/upload-resume", "/dashboard", "/matches", "/growth"]);

export function RouteGuard({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();

  useEffect(() => {
    if (!pathname || !PROTECTED_ROUTES.has(pathname)) {
      return;
    }

    const token = getToken();
    if (!token) {
      router.replace("/login");
      return;
    }

    if (pathname === "/dashboard" && !isOnboardingCompleted()) {
      router.replace("/onboarding");
    }
  }, [pathname, router]);

  return <>{children}</>;
}
