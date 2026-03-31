import Link from "next/link";

export default function Home() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-zinc-50 px-6 dark:bg-black">
      <main className="w-full max-w-2xl rounded-2xl border border-zinc-200 bg-white p-10 shadow-sm dark:border-zinc-800 dark:bg-zinc-950">
        <h1 className="text-3xl font-semibold tracking-tight text-zinc-900 dark:text-zinc-100">
          FitMatch
        </h1>
        <p className="mt-4 text-zinc-600 dark:text-zinc-300">
          Start Phase 2 by signing in, completing onboarding, and uploading your resume.
        </p>
        <div className="mt-8 flex gap-3">
          <Link
            className="rounded-lg bg-zinc-900 px-4 py-2 text-sm font-medium text-white hover:bg-zinc-700 dark:bg-zinc-100 dark:text-zinc-900"
            href="/login"
          >
            Get Started
          </Link>
          <Link
            className="rounded-lg border border-zinc-300 px-4 py-2 text-sm font-medium text-zinc-700 hover:bg-zinc-100 dark:border-zinc-700 dark:text-zinc-200 dark:hover:bg-zinc-900"
            href="/dashboard"
          >
            Go to Dashboard
          </Link>
        </div>
      </main>
    </div>
  );
}
