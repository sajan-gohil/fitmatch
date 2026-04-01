"use client";

import { useEffect, useState } from "react";

import {
  addWatchlistCompany,
  deleteApplication,
  deleteWatchlistCompany,
  getSalaryBenchmark,
  listApplications,
  listWatchlist,
  upsertApplication,
} from "@/lib/api";
import { getToken } from "@/lib/auth";
import type { ApplicationStatus, ApplicationTrackerItem, SalaryBenchmarkResponse, WatchlistItem } from "@/lib/types";

const APPLICATION_STATUSES: ApplicationStatus[] = ["saved", "applied", "interviewing", "offer", "rejected"];

export default function GrowthPage() {
  const [token] = useState<string | null>(() => getToken());
  const [companyInput, setCompanyInput] = useState("");
  const [watchlist, setWatchlist] = useState<WatchlistItem[]>([]);
  const [applications, setApplications] = useState<ApplicationTrackerItem[]>([]);
  const [jobIdInput, setJobIdInput] = useState("");
  const [jobStatusInput, setJobStatusInput] = useState<ApplicationStatus>("saved");
  const [notesInput, setNotesInput] = useState("");
  const [benchmarkRole, setBenchmarkRole] = useState("");
  const [benchmarkLocation, setBenchmarkLocation] = useState("");
  const [benchmark, setBenchmark] = useState<SalaryBenchmarkResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(Boolean(token));

  useEffect(() => {
    if (!token) {
      return;
    }
    Promise.all([listWatchlist(token), listApplications(token), getSalaryBenchmark(token)])
      .then(([watchlistPayload, applicationsPayload, benchmarkPayload]) => {
        setWatchlist(watchlistPayload.items);
        setApplications(applicationsPayload.items);
        setBenchmark(benchmarkPayload);
      })
      .catch((fetchError) => {
        setError(fetchError instanceof Error ? fetchError.message : "Unable to load growth features");
      })
      .finally(() => setLoading(false));
  }, [token]);

  async function onAddWatchlist() {
    if (!token) return;
    try {
      await addWatchlistCompany(token, companyInput);
      const updated = await listWatchlist(token);
      setWatchlist(updated.items);
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : "Unable to add company");
    }
  }

  async function onDeleteWatchlist(id: string) {
    if (!token) return;
    try {
      await deleteWatchlistCompany(token, id);
      const updated = await listWatchlist(token);
      setWatchlist(updated.items);
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : "Unable to delete company");
    }
  }

  async function onSaveApplication() {
    if (!token || !jobIdInput.trim()) return;
    try {
      await upsertApplication(token, {
        external_job_id: jobIdInput.trim(),
        status: jobStatusInput,
        notes: notesInput,
      });
      const updated = await listApplications(token);
      setApplications(updated.items);
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : "Unable to save application");
    }
  }

  async function onDeleteApplication(id: string) {
    if (!token) return;
    try {
      await deleteApplication(token, id);
      const updated = await listApplications(token);
      setApplications(updated.items);
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : "Unable to delete application");
    }
  }

  async function onRefreshBenchmark() {
    if (!token) return;
    try {
      const updated = await getSalaryBenchmark(token, benchmarkRole, benchmarkLocation);
      setBenchmark(updated);
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : "Unable to refresh benchmark");
    }
  }

  if (!token) {
    return (
      <div className="mx-auto w-full max-w-5xl px-6 py-10">
        <h1 className="text-2xl font-semibold text-zinc-900 dark:text-zinc-100">Growth Features</h1>
        <p className="mt-4 text-sm text-zinc-600 dark:text-zinc-300">Please sign in to use Phase 10 modules.</p>
      </div>
    );
  }

  return (
    <div className="mx-auto w-full max-w-5xl px-6 py-10">
      <h1 className="text-2xl font-semibold text-zinc-900 dark:text-zinc-100">Growth Features</h1>
      {loading ? <p className="mt-3 text-sm text-zinc-600 dark:text-zinc-300">Loading...</p> : null}
      {error ? <p className="mt-3 text-sm text-red-600">{error}</p> : null}

      <section className="mt-6 rounded-xl border border-zinc-200 p-4 dark:border-zinc-800">
        <h2 className="text-base font-semibold text-zinc-900 dark:text-zinc-100">Company Watchlist</h2>
        <div className="mt-3 flex gap-2">
          <input
            className="w-full rounded-lg border border-zinc-300 px-3 py-2 text-zinc-900 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-100"
            onChange={(event) => setCompanyInput(event.target.value)}
            placeholder="Company name"
            value={companyInput}
          />
          <button
            className="rounded-lg bg-zinc-900 px-3 py-2 text-sm text-white dark:bg-zinc-100 dark:text-zinc-900"
            onClick={onAddWatchlist}
            type="button"
          >
            Add
          </button>
        </div>
        <ul className="mt-3 space-y-2">
          {watchlist.map((item) => (
            <li key={item.id} className="flex items-center justify-between rounded border border-zinc-200 px-3 py-2 text-sm dark:border-zinc-700">
              <span>{item.company_name}</span>
              <button
                className="rounded border border-zinc-300 px-2 py-1 text-xs dark:border-zinc-700"
                onClick={() => onDeleteWatchlist(item.id)}
                type="button"
              >
                Remove
              </button>
            </li>
          ))}
        </ul>
      </section>

      <section className="mt-6 rounded-xl border border-zinc-200 p-4 dark:border-zinc-800">
        <h2 className="text-base font-semibold text-zinc-900 dark:text-zinc-100">Application Tracker</h2>
        <div className="mt-3 grid gap-2 md:grid-cols-3">
          <input
            className="rounded-lg border border-zinc-300 px-3 py-2 text-zinc-900 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-100"
            onChange={(event) => setJobIdInput(event.target.value)}
            placeholder="external_job_id"
            value={jobIdInput}
          />
          <select
            className="rounded-lg border border-zinc-300 px-3 py-2 text-zinc-900 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-100"
            onChange={(event) => setJobStatusInput(event.target.value as ApplicationStatus)}
            value={jobStatusInput}
          >
            {APPLICATION_STATUSES.map((status) => (
              <option key={status} value={status}>
                {status}
              </option>
            ))}
          </select>
          <input
            className="rounded-lg border border-zinc-300 px-3 py-2 text-zinc-900 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-100"
            onChange={(event) => setNotesInput(event.target.value)}
            placeholder="notes"
            value={notesInput}
          />
        </div>
        <button
          className="mt-2 rounded-lg bg-zinc-900 px-3 py-2 text-sm text-white dark:bg-zinc-100 dark:text-zinc-900"
          onClick={onSaveApplication}
          type="button"
        >
          Save application
        </button>
        <ul className="mt-3 space-y-2">
          {applications.map((item) => (
            <li key={item.id} className="flex items-center justify-between rounded border border-zinc-200 px-3 py-2 text-sm dark:border-zinc-700">
              <span>
                {item.title} ({item.external_job_id}) — {item.status}
              </span>
              <button
                className="rounded border border-zinc-300 px-2 py-1 text-xs dark:border-zinc-700"
                onClick={() => onDeleteApplication(item.id)}
                type="button"
              >
                Delete
              </button>
            </li>
          ))}
        </ul>
      </section>

      <section className="mt-6 rounded-xl border border-zinc-200 p-4 dark:border-zinc-800">
        <h2 className="text-base font-semibold text-zinc-900 dark:text-zinc-100">Salary Benchmarking</h2>
        <div className="mt-3 grid gap-2 md:grid-cols-3">
          <input
            className="rounded-lg border border-zinc-300 px-3 py-2 text-zinc-900 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-100"
            onChange={(event) => setBenchmarkRole(event.target.value)}
            placeholder="Role filter"
            value={benchmarkRole}
          />
          <input
            className="rounded-lg border border-zinc-300 px-3 py-2 text-zinc-900 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-100"
            onChange={(event) => setBenchmarkLocation(event.target.value)}
            placeholder="Location filter"
            value={benchmarkLocation}
          />
          <button
            className="rounded-lg bg-zinc-900 px-3 py-2 text-sm text-white dark:bg-zinc-100 dark:text-zinc-900"
            onClick={onRefreshBenchmark}
            type="button"
          >
            Refresh benchmark
          </button>
        </div>
        {benchmark ? (
          <div className="mt-3 text-sm text-zinc-700 dark:text-zinc-200">
            <p>Samples: {benchmark.count}</p>
            <p>Median salary min: {benchmark.median_salary_min ?? "n/a"}</p>
            <p>Average salary min: {benchmark.average_salary_min ?? "n/a"}</p>
          </div>
        ) : null}
      </section>
    </div>
  );
}
