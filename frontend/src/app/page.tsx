export default function Home() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-zinc-50 px-6 dark:bg-black">
      <main className="w-full max-w-2xl rounded-2xl border border-zinc-200 bg-white p-10 shadow-sm dark:border-zinc-800 dark:bg-zinc-950">
        <h1 className="text-3xl font-semibold tracking-tight text-zinc-900 dark:text-zinc-100">
          FitMatch Frontend Scaffold
        </h1>
        <p className="mt-4 text-zinc-600 dark:text-zinc-300">
          Phase 1 foundation is ready. Connect this app to the FastAPI backend at
          <span className="ml-1 font-mono text-sm">/api</span>.
        </p>
      </main>
    </div>
  );
}
