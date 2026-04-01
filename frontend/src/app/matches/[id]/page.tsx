"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";

import { getMatchDetail } from "@/lib/api";
import { getToken } from "@/lib/auth";
import type { MatchDetailResponse } from "@/lib/types";

export default function MatchDetailPage() {
  const params = useParams<{ id: string }>();
  const externalJobId = params?.id ?? "";
  const token = getToken();
  const [detail, setDetail] = useState<MatchDetailResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(Boolean(token && externalJobId));

  useEffect(() => {
    if (!token || !externalJobId) {
      return;
    }

    getMatchDetail(token, externalJobId)
      .then((payload) => setDetail(payload))
      .catch((fetchError) => {
        const message = fetchError instanceof Error ? fetchError.message : "Unable to load detail";
        setError(message);
      })
      .finally(() => setLoading(false));
  }, [externalJobId, token]);

  return (
    <div className="mx-auto w-full max-w-4xl px-6 py-10">
      <Link className="text-sm text-zinc-600 hover:underline dark:text-zinc-300" href="/matches">
        ← Back to matches
      </Link>
      {!token || !externalJobId ? <p className="mt-4 text-sm text-red-600">Sign in and select a match to view details.</p> : null}
      {loading ? <p className="mt-4 text-sm text-zinc-600 dark:text-zinc-300">Loading match detail...</p> : null}
      {error ? <p className="mt-4 text-sm text-red-600">{error}</p> : null}
      {detail ? (
        <article className="mt-6 rounded-xl border border-zinc-200 p-6 dark:border-zinc-800">
          <h1 className="text-2xl font-semibold text-zinc-900 dark:text-zinc-100">{String(detail.job.title ?? "Untitled role")}</h1>
          <p className="mt-1 text-sm text-zinc-600 dark:text-zinc-300">
            {String(detail.job.company_name ?? "Unknown company")} • {String(detail.job.location ?? "Unknown location")}
          </p>
          <p className="mt-4 text-lg font-medium text-zinc-900 dark:text-zinc-100">Overall match: {detail.score}%</p>
          <ul className="mt-3 space-y-1 text-sm text-zinc-700 dark:text-zinc-200">
            <li>Title alignment: {detail.breakdown.title}%</li>
            <li>Skills overlap: {detail.breakdown.skills}%</li>
            <li>Experience fit: {detail.breakdown.experience}%</li>
            <li>Education fit: {detail.breakdown.education}%</li>
          </ul>
          <p className="mt-4 whitespace-pre-wrap text-sm text-zinc-700 dark:text-zinc-200">
            {String(detail.job.description ?? "No description provided.")}
          </p>
          {typeof detail.job.url === "string" && detail.job.url ? (
            <a
              className="mt-6 inline-flex rounded-lg bg-zinc-900 px-4 py-2 text-sm font-medium text-white hover:bg-zinc-700 dark:bg-zinc-100 dark:text-zinc-900"
              href={detail.job.url}
              rel="noreferrer"
              target="_blank"
            >
              Apply now
            </a>
          ) : null}
        </article>
      ) : null}
    </div>
  );
}
