import type { Metadata } from "next";

type Params = {
  role: string;
  city: string;
};

const KNOWN_TERMS: Record<string, string> = {
  sql: "SQL",
  ios: "iOS",
  ux: "UX",
  ui: "UI",
};

function prettySlug(value: string): string {
  return value
    .split("-")
    .filter(Boolean)
    .map((item) => {
      const lower = item.toLowerCase();
      if (KNOWN_TERMS[lower]) {
        return KNOWN_TERMS[lower];
      }
      return item.length <= 3 ? item.toUpperCase() : item[0].toUpperCase() + item.slice(1);
    })
    .join(" ");
}

export async function generateMetadata({ params }: { params: Promise<Params> }): Promise<Metadata> {
  const { role, city } = await params;
  const roleText = prettySlug(role);
  const cityText = prettySlug(city);
  return {
    title: `${roleText} jobs in ${cityText} | FitMatch`,
    description: `Explore personalized ${roleText} opportunities in ${cityText} with FitMatch.`,
  };
}

export default async function ProgrammaticSeoPage({ params }: { params: Promise<Params> }) {
  const { role, city } = await params;
  const roleText = prettySlug(role);
  const cityText = prettySlug(city);

  return (
    <div className="mx-auto w-full max-w-3xl px-6 py-10">
      <h1 className="text-3xl font-semibold text-zinc-900 dark:text-zinc-100">
        {roleText} jobs in {cityText}
      </h1>
      <p className="mt-3 text-sm text-zinc-600 dark:text-zinc-300">
        This SEO landing page is generated from role/location combinations to scale organic discovery.
      </p>
      <section className="mt-6 rounded-xl border border-zinc-200 p-4 dark:border-zinc-800">
        <h2 className="text-base font-semibold text-zinc-900 dark:text-zinc-100">How FitMatch helps</h2>
        <ul className="mt-3 list-disc space-y-1 pl-5 text-sm text-zinc-700 dark:text-zinc-200">
          <li>Aggregates jobs from multiple ATS sources</li>
          <li>Ranks opportunities against your resume</li>
          <li>Tracks applications and watchlist companies</li>
        </ul>
      </section>
    </div>
  );
}
