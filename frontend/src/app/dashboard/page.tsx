"use client";

import Link from "next/link";

import { getToken, isOnboardingCompleted } from "@/lib/auth";

export default function DashboardPage() {
  const signedIn = getToken() !== null;
  const onboarded = isOnboardingCompleted();

  return (
    <div className="mx-auto flex min-h-screen w-full max-w-3xl items-center px-6 py-10">
      <main className="w-full rounded-2xl border border-zinc-200 bg-white p-8 shadow-sm dark:border-zinc-800 dark:bg-zinc-950">
        <h1 className="text-2xl font-semibold text-zinc-900 dark:text-zinc-100">Dashboard</h1>

        {!signedIn ? (
          <p className="mt-3 text-sm text-zinc-600 dark:text-zinc-300">You are not signed in yet. Start with authentication.</p>
        ) : !onboarded ? (
          <p className="mt-3 text-sm text-zinc-600 dark:text-zinc-300">You are signed in. Complete onboarding to unlock personalized matches.</p>
        ) : (
          <>
            <p className="mt-3 text-sm text-zinc-600 dark:text-zinc-300">Onboarding complete. Matches loading...</p>
            <p className="mt-1 text-xs text-zinc-500 dark:text-zinc-400">This placeholder prepares the first-run handoff for Phase 3 matching results.</p>
          </>
        )}

        <div className="mt-6 flex flex-wrap gap-3">
          {!signedIn ? (
            <Link className="rounded-lg bg-zinc-900 px-4 py-2 text-sm font-medium text-white hover:bg-zinc-700 dark:bg-zinc-100 dark:text-zinc-900" href="/login">
              Sign in
            </Link>
          ) : null}
          {signedIn && !onboarded ? (
            <Link className="rounded-lg bg-zinc-900 px-4 py-2 text-sm font-medium text-white hover:bg-zinc-700 dark:bg-zinc-100 dark:text-zinc-900" href="/onboarding">
              Continue onboarding
            </Link>
          ) : null}
          {signedIn && onboarded ? (
            <>
              <Link className="rounded-lg bg-zinc-900 px-4 py-2 text-sm font-medium text-white hover:bg-zinc-700 dark:bg-zinc-100 dark:text-zinc-900" href="/matches">
                View top matches
              </Link>
              <Link className="rounded-lg border border-zinc-300 px-4 py-2 text-sm font-medium text-zinc-700 hover:bg-zinc-100 dark:border-zinc-700 dark:text-zinc-200 dark:hover:bg-zinc-900" href="/upload-resume">
                Upload another resume
              </Link>
            </>
          ) : null}
        </div>
      </main>
    </div>
  );
}
