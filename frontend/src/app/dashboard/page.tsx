"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { listMatches, listNotifications, markNotificationRead } from "@/lib/api";
import { getToken, isOnboardingCompleted } from "@/lib/auth";
import type { NotificationItem } from "@/lib/types";

const FIRST_BATCH_LIMIT = 3;

export default function DashboardPage() {
  const [hydrated, setHydrated] = useState(false);
  const [signedIn, setSignedIn] = useState(false);
  const [onboarded, setOnboarded] = useState(false);
  const [firstBatchCount, setFirstBatchCount] = useState<number | null>(null);
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const [notificationError, setNotificationError] = useState<string | null>(null);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      setSignedIn(getToken() !== null);
      setOnboarded(isOnboardingCompleted());
      setHydrated(true);
    }, 0);
    return () => window.clearTimeout(timer);
  }, []);

  useEffect(() => {
    if (!hydrated) {
      return;
    }
    const token = getToken();
    if (!token || !onboarded) {
      return;
    }
    listMatches(token, FIRST_BATCH_LIMIT)
      .then((payload) => setFirstBatchCount(payload.total))
      .catch(() => setFirstBatchCount(0));

    listNotifications(token)
      .then((payload) => setNotifications(payload.items))
      .catch((error) => {
        const message = error instanceof Error ? error.message : "Unable to load notifications";
        setNotificationError(message);
      });
  }, [hydrated, onboarded]);

  function onToggleRead(id: string, read: boolean) {
    const token = getToken();
    if (!token) {
      return;
    }
    markNotificationRead(token, id, read)
      .then(() => {
        setNotifications((current) => current.map((item) => (item.id === id ? { ...item, read } : item)));
      })
      .catch((error) => {
        const message = error instanceof Error ? error.message : "Unable to update notification";
        setNotificationError(message);
      });
  }

  return (
    <div className="mx-auto flex min-h-screen w-full max-w-3xl items-center px-6 py-10">
      <main className="w-full rounded-2xl border border-zinc-200 bg-white p-8 shadow-sm dark:border-zinc-800 dark:bg-zinc-950">
        <h1 className="text-2xl font-semibold text-zinc-900 dark:text-zinc-100">Dashboard</h1>

        {!hydrated ? (
          <p className="mt-3 text-sm text-zinc-600 dark:text-zinc-300">Loading dashboard...</p>
        ) : !signedIn ? (
          <p className="mt-3 text-sm text-zinc-600 dark:text-zinc-300">You are not signed in yet. Start with authentication.</p>
        ) : !onboarded ? (
          <p className="mt-3 text-sm text-zinc-600 dark:text-zinc-300">You are signed in. Complete onboarding to unlock personalized matches.</p>
        ) : (
          <>
            <p className="mt-3 text-sm text-zinc-600 dark:text-zinc-300">
              Onboarding complete. Your first match batch is ready.
            </p>
            <p className="mt-1 text-xs text-zinc-500 dark:text-zinc-400">
              {firstBatchCount === null
                ? "Fetching top matches..."
                : `Loaded ${firstBatchCount} quick-start matches for your first-run experience.`}
            </p>
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

        {signedIn && onboarded ? (
          <section className="mt-8 rounded-xl border border-zinc-200 p-4 dark:border-zinc-800">
            <h2 className="text-base font-semibold text-zinc-900 dark:text-zinc-100">In-app notifications</h2>
            {notificationError ? (
              <p className="mt-2 text-sm text-red-600">{notificationError}</p>
            ) : null}
            {notifications.length === 0 ? (
              <p className="mt-2 text-sm text-zinc-600 dark:text-zinc-300">No alerts yet.</p>
            ) : (
              <ul className="mt-3 space-y-2">
                {notifications.slice(0, 5).map((item) => (
                  <li key={item.id} className="rounded-md border border-zinc-200 px-3 py-2 text-sm dark:border-zinc-700">
                    <p className="font-medium text-zinc-900 dark:text-zinc-100">
                      {item.title} {item.read ? "(read)" : "(unread)"}
                    </p>
                    <p className="mt-1 text-zinc-600 dark:text-zinc-300">{item.body}</p>
                    <button
                      className="mt-2 rounded border border-zinc-300 px-2 py-1 text-xs text-zinc-700 hover:bg-zinc-100 dark:border-zinc-700 dark:text-zinc-200 dark:hover:bg-zinc-900"
                      onClick={() => onToggleRead(item.id, !item.read)}
                      type="button"
                    >
                      Mark as {item.read ? "unread" : "read"}
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </section>
        ) : null}
      </main>
    </div>
  );
}
