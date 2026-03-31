"use client";

import { useRouter } from "next/navigation";
import { FormEvent, useMemo, useState } from "react";

import { getToken, markOnboardingCompleted } from "@/lib/auth";
import { saveOnboarding } from "@/lib/api";
import type { WorkType } from "@/lib/types";

const WORK_TYPES: WorkType[] = ["remote", "hybrid", "onsite"];

export default function OnboardingPage() {
  const router = useRouter();
  const [targetRoles, setTargetRoles] = useState("Software Engineer");
  const [preferredLocations, setPreferredLocations] = useState("Toronto");
  const [workTypes, setWorkTypes] = useState<WorkType[]>(["remote"]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const selectedWorkTypes = useMemo(() => new Set(workTypes), [workTypes]);

  function toggleWorkType(type: WorkType) {
    setWorkTypes((current) =>
      current.includes(type) ? current.filter((entry) => entry !== type) : [...current, type],
    );
  }

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const token = getToken();
    if (!token) {
      router.push("/login");
      return;
    }

    if (workTypes.length === 0) {
      setError("Select at least one work type preference");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      await saveOnboarding(token, {
        target_roles: targetRoles.split(",").map((value) => value.trim()).filter(Boolean),
        preferred_locations: preferredLocations.split(",").map((value) => value.trim()).filter(Boolean),
        work_type_preferences: workTypes,
      });
      markOnboardingCompleted();
      router.push("/upload-resume");
    } catch (submissionError) {
      const message = submissionError instanceof Error ? submissionError.message : "Unable to save onboarding";
      setError(message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="mx-auto flex min-h-screen w-full max-w-2xl items-center px-6 py-10">
      <main className="w-full rounded-2xl border border-zinc-200 bg-white p-8 shadow-sm dark:border-zinc-800 dark:bg-zinc-950">
        <h1 className="text-2xl font-semibold text-zinc-900 dark:text-zinc-100">Onboarding</h1>
        <p className="mt-2 text-sm text-zinc-600 dark:text-zinc-300">Set your target roles, preferred locations, and work type preferences.</p>

        <form className="mt-6 space-y-5" onSubmit={onSubmit}>
          <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-200">
            Target roles (comma separated)
            <input
              className="mt-1 w-full rounded-lg border border-zinc-300 px-3 py-2 text-zinc-900 outline-none ring-zinc-400 focus:ring-2 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-100"
              onChange={(event) => setTargetRoles(event.target.value)}
              required
              value={targetRoles}
            />
          </label>

          <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-200">
            Preferred locations (comma separated)
            <input
              className="mt-1 w-full rounded-lg border border-zinc-300 px-3 py-2 text-zinc-900 outline-none ring-zinc-400 focus:ring-2 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-100"
              onChange={(event) => setPreferredLocations(event.target.value)}
              required
              value={preferredLocations}
            />
          </label>

          <fieldset>
            <legend className="text-sm font-medium text-zinc-700 dark:text-zinc-200">Work type preferences</legend>
            <div className="mt-2 flex flex-wrap gap-3">
              {WORK_TYPES.map((type) => (
                <label key={type} className="inline-flex items-center gap-2 text-sm text-zinc-700 dark:text-zinc-200">
                  <input
                    checked={selectedWorkTypes.has(type)}
                    onChange={() => toggleWorkType(type)}
                    type="checkbox"
                  />
                  {type}
                </label>
              ))}
            </div>
          </fieldset>

          {error ? <p className="text-sm text-red-600">{error}</p> : null}

          <button
            className="w-full rounded-lg bg-zinc-900 px-4 py-2 text-sm font-medium text-white hover:bg-zinc-700 disabled:cursor-not-allowed disabled:opacity-60 dark:bg-zinc-100 dark:text-zinc-900"
            disabled={loading}
            type="submit"
          >
            {loading ? "Saving..." : "Continue to Resume Upload"}
          </button>
        </form>
      </main>
    </div>
  );
}
