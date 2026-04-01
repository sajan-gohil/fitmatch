"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import { listMatches } from "@/lib/api";
import { getMatchFilters, getToken, saveMatchFilters } from "@/lib/auth";
import type { Match } from "@/lib/types";

export default function MatchesPage() {
  const [token, setToken] = useState<string | null>(null);
  const [matches, setMatches] = useState<Match[]>([]);
  const [roleFilter, setRoleFilter] = useState("");
  const [locationFilter, setLocationFilter] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [tier, setTier] = useState<"free" | "pro">("free");
  const [enforcedLimit, setEnforcedLimit] = useState<number | null>(null);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      const sessionToken = getToken();
      const savedFilters = getMatchFilters();
      setRoleFilter(savedFilters.role);
      setLocationFilter(savedFilters.location);
      setToken(sessionToken);
      if (!sessionToken) {
        setLoading(false);
        return;
      }

      listMatches(sessionToken)
        .then((payload) => {
          setMatches(payload.matches);
          setTier(payload.tier);
          setEnforcedLimit(payload.enforced_limit);
        })
        .catch((fetchError) => {
          const message = fetchError instanceof Error ? fetchError.message : "Unable to load matches";
          setError(message);
        })
        .finally(() => setLoading(false));
    }, 0);

    return () => window.clearTimeout(timer);
  }, []);

  const filteredMatches = useMemo(() => {
    const normalizedRole = roleFilter.trim().toLowerCase();
    const normalizedLocation = locationFilter.trim().toLowerCase();
    return matches.filter((match) => {
      const role = String(match.job.title ?? "").toLowerCase();
      const location = String(match.job.location ?? "").toLowerCase();
      const roleAllowed = normalizedRole ? role.includes(normalizedRole) : true;
      const locationAllowed = normalizedLocation ? location.includes(normalizedLocation) : true;
      return roleAllowed && locationAllowed;
    });
  }, [matches, roleFilter, locationFilter]);

  function onSaveSearch() {
    saveMatchFilters(roleFilter, locationFilter);
  }

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
      {tier === "free" && enforcedLimit ? (
        <p className="mt-4 rounded-md border border-amber-300 bg-amber-50 px-3 py-2 text-xs text-amber-800">
          Free tier currently shows up to {enforcedLimit} matches per refresh.
        </p>
      ) : null}

      {!loading && !error ? (
        <>
          <div className="mt-6 grid gap-3 rounded-xl border border-zinc-200 p-4 dark:border-zinc-800 md:grid-cols-3">
            <label className="text-sm text-zinc-700 dark:text-zinc-200">
              Role filter
              <input
                className="mt-1 w-full rounded-lg border border-zinc-300 px-3 py-2 text-zinc-900 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-100"
                onChange={(event) => setRoleFilter(event.target.value)}
                value={roleFilter}
              />
            </label>
            <label className="text-sm text-zinc-700 dark:text-zinc-200">
              Location filter
              <input
                className="mt-1 w-full rounded-lg border border-zinc-300 px-3 py-2 text-zinc-900 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-100"
                onChange={(event) => setLocationFilter(event.target.value)}
                value={locationFilter}
              />
            </label>
            <div className="flex items-end">
              <button
                className="w-full rounded-lg border border-zinc-300 px-3 py-2 text-sm font-medium text-zinc-700 hover:bg-zinc-100 dark:border-zinc-700 dark:text-zinc-200 dark:hover:bg-zinc-900"
                onClick={onSaveSearch}
                type="button"
              >
                Save search
              </button>
            </div>
          </div>
          <ul className="mt-6 space-y-3">
          {filteredMatches.map((match) => (
            <li key={String(match.job.external_job_id ?? match.job.title)} className="rounded-xl border border-zinc-200 p-4 dark:border-zinc-800">
              <p className="font-medium text-zinc-900 dark:text-zinc-100">
                <Link className="hover:underline" href={`/matches/${encodeURIComponent(String(match.job.external_job_id ?? ""))}`}>
                  {String(match.job.title ?? "Untitled role")}
                </Link>
              </p>
              <p className="text-sm text-zinc-600 dark:text-zinc-300">{String(match.job.company_name ?? "Unknown company")} • {String(match.job.location ?? "Unknown location")}</p>
              <p className="mt-2 text-sm text-zinc-700 dark:text-zinc-200">Match score: {match.score}%</p>
              <p className="mt-2 text-xs text-zinc-500 dark:text-zinc-400">
                Title {match.breakdown.title}% • Skills {match.breakdown.skills}% • Experience {match.breakdown.experience}% • Education {match.breakdown.education}%
              </p>
            </li>
          ))}
          {filteredMatches.length === 0 ? (
            <li className="text-sm text-zinc-600 dark:text-zinc-300">
              {matches.length === 0 ? "No matches yet." : "No matches for current filters."}
            </li>
          ) : null}
          </ul>
        </>
      ) : null}
    </div>
  );
}
