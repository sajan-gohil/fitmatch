"use client";

import { useEffect, useState } from "react";

import { listMatches } from "@/lib/api";
import { getToken } from "@/lib/auth";
import type { Match } from "@/lib/types";

export default function MatchesPage() {
  const [token, setToken] = useState<string | null>(null);
  const [matches, setMatches] = useState<Match[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      const sessionToken = getToken();
      setToken(sessionToken);
      if (!sessionToken) {
        setLoading(false);
        return;
      }

      listMatches(sessionToken)
        .then((payload) => setMatches(payload.matches))
        .catch((fetchError) => {
          const message = fetchError instanceof Error ? fetchError.message : "Unable to load matches";
          setError(message);
        })
        .finally(() => setLoading(false));
    }, 0);

    return () => window.clearTimeout(timer);
  }, []);

  if (!token) {
    return (
      <div className="mx-auto w-full max-w-4xl px-6 py-10">
        <h1 className="text-2xl font-semibold text-zinc-900 dark:text-zinc-100">Top Matches</h1>
        <p className="mt-4 text-sm text-zinc-600 dark:text-zinc-300">Please sign in to view matches.</p>
      </div>
    );
  }

  return (
    <div className="mx-auto w-full max-w-4xl px-6 py-10">
      <h1 className="text-2xl font-semibold text-zinc-900 dark:text-zinc-100">Top Matches</h1>
      {loading ? <p className="mt-4 text-sm text-zinc-600 dark:text-zinc-300">Loading matches...</p> : null}
      {error ? <p className="mt-4 text-sm text-red-600">{error}</p> : null}

      {!loading && !error ? (
        <ul className="mt-6 space-y-3">
          {matches.map((match) => (
            <li key={String(match.job.external_job_id ?? match.job.title)} className="rounded-xl border border-zinc-200 p-4 dark:border-zinc-800">
              <p className="font-medium text-zinc-900 dark:text-zinc-100">{String(match.job.title ?? "Untitled role")}</p>
              <p className="text-sm text-zinc-600 dark:text-zinc-300">{String(match.job.company_name ?? "Unknown company")} • {String(match.job.location ?? "Unknown location")}</p>
              <p className="mt-2 text-sm text-zinc-700 dark:text-zinc-200">Match score: {match.score}%</p>
            </li>
          ))}
          {matches.length === 0 ? <li className="text-sm text-zinc-600 dark:text-zinc-300">No matches yet.</li> : null}
        </ul>
      ) : null}
    </div>
  );
}
