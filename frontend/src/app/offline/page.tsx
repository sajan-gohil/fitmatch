export default function OfflinePage() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-zinc-50 px-6 dark:bg-black">
      <main className="w-full max-w-xl rounded-2xl border border-zinc-200 bg-white p-8 shadow-sm dark:border-zinc-800 dark:bg-zinc-950">
        <h1 className="text-2xl font-semibold text-zinc-900 dark:text-zinc-100">You&apos;re offline</h1>
        <p className="mt-3 text-sm text-zinc-600 dark:text-zinc-300">
          FitMatch is in offline mode right now. Reconnect to refresh live matches and alerts.
        </p>
      </main>
    </div>
  );
}

