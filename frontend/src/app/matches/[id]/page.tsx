"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";

import { BillingActions } from "@/components/billing-actions";
import { getMatchDetail, getResumeIntelligence } from "@/lib/api";
import { getToken } from "@/lib/auth";
import type { MatchDetailResponse, ResumeIntelligenceResponse } from "@/lib/types";

export default function MatchDetailPage() {
  const params = useParams<{ id: string }>();
  const externalJobId = params?.id ?? "";
  const token = getToken();
  const [detail, setDetail] = useState<MatchDetailResponse | null>(null);
  const [intelligence, setIntelligence] = useState<ResumeIntelligenceResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [upgradeRequired, setUpgradeRequired] = useState(false);
  const [loading, setLoading] = useState(Boolean(token && externalJobId));

  useEffect(() => {
    if (!token || !externalJobId) {
      return;
    }

    getMatchDetail(token, externalJobId)
      .then((payload) => {
        setDetail(payload);
        setUpgradeRequired(false);
      })
      .catch((fetchError) => {
        const message = fetchError instanceof Error ? fetchError.message : "Unable to load detail";
        setUpgradeRequired(message === "Upgrade required");
        setError(message);
      })
      .finally(() => setLoading(false));

    getResumeIntelligence(token, externalJobId)
      .then((payload) => setIntelligence(payload))
      .catch((intelligenceError) => {
        console.warn("Unable to load resume intelligence", intelligenceError);
      });
  }, [externalJobId, token]);

  return (
    <div className="mx-auto w-full max-w-4xl px-6 py-10">
      <Link className="text-sm text-zinc-600 hover:underline dark:text-zinc-300" href="/matches">
        ← Back to matches
      </Link>
      {!token || !externalJobId ? <p className="mt-4 text-sm text-red-600">Sign in and select a match to view details.</p> : null}
      {loading ? <p className="mt-4 text-sm text-zinc-600 dark:text-zinc-300">Loading match detail...</p> : null}
      {error ? <p className="mt-4 text-sm text-red-600">{error}</p> : null}
      {upgradeRequired ? (
        <div className="mt-4 rounded-md border border-amber-300 bg-amber-50 px-3 py-2 text-xs text-amber-800">
          This detailed match explanation is a paid feature.
          <BillingActions />
        </div>
      ) : null}
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
          {intelligence ? (
            <section className="mt-6 rounded-lg border border-zinc-200 p-4 dark:border-zinc-800">
              <h2 className="text-base font-semibold text-zinc-900 dark:text-zinc-100">Phase 7 Resume Intelligence</h2>
              {intelligence.is_preview ? (
                <div className="mt-2 rounded-md border border-amber-300 bg-amber-50 px-3 py-2 text-xs text-amber-800">
                  You are seeing a free preview of skill gap analysis and rewrite suggestions.
                  <BillingActions />
                </div>
              ) : null}
              <p className="mt-3 text-sm text-zinc-700 dark:text-zinc-200">{intelligence.fit_report.summary}</p>
              <div className="mt-3 text-sm text-zinc-700 dark:text-zinc-200">
                <p className="font-medium">Missing skills</p>
                <p>{intelligence.skill_gap.missing_skills.join(", ") || "None detected"}</p>
              </div>
              <ul className="mt-3 list-disc space-y-1 pl-5 text-sm text-zinc-700 dark:text-zinc-200">
                {intelligence.fit_report.suggestions.map((suggestion) => (
                  <li key={suggestion}>{suggestion}</li>
                ))}
              </ul>
              <div className="mt-3 grid gap-2 text-xs text-zinc-600 dark:text-zinc-300 md:grid-cols-3">
                <p>Clarity: {intelligence.resume_scoring.clarity_formatting}%</p>
                <p>Quantification: {intelligence.resume_scoring.quantification}%</p>
                <p>Keyword density: {intelligence.resume_scoring.keyword_density}%</p>
                <p>Experience narrative: {intelligence.resume_scoring.experience_narrative}%</p>
                <p>Skills coverage: {intelligence.resume_scoring.skills_coverage}%</p>
                <p className="font-semibold">Overall resume score: {intelligence.resume_scoring.overall}%</p>
              </div>
              <div className="mt-3 text-sm text-zinc-700 dark:text-zinc-200">
                <p className="font-medium">AI rewrite suggestions</p>
                <ul className="mt-1 list-disc space-y-1 pl-5">
                  {intelligence.rewrite_suggestions.map((item) => (
                    <li key={item.id}>
                      <span className="font-medium">{item.state.toUpperCase()}:</span> {item.suggested}
                    </li>
                  ))}
                </ul>
              </div>
            </section>
          ) : null}
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
