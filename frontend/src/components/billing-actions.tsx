"use client";

import { useState } from "react";

import { createCheckoutSession, createPortalSession } from "@/lib/api";
import { getToken } from "@/lib/auth";

type BillingActionsProps = {
  showUpgrade?: boolean;
};

export function BillingActions({ showUpgrade = true }: BillingActionsProps) {
  const [loading, setLoading] = useState<null | "pro" | "lifetime" | "portal">(null);
  const [error, setError] = useState<string | null>(null);

  async function openCheckout(plan: "pro" | "lifetime") {
    const token = getToken();
    if (!token) {
      setError("Please sign in to manage billing.");
      return;
    }
    setLoading(plan);
    setError(null);
    try {
      const session = await createCheckoutSession(token, plan);
      window.location.href = session.url;
    } catch (checkoutError) {
      const message = checkoutError instanceof Error ? checkoutError.message : "Unable to open checkout";
      setError(message);
    } finally {
      setLoading(null);
    }
  }

  async function openPortal() {
    const token = getToken();
    if (!token) {
      setError("Please sign in to manage billing.");
      return;
    }
    setLoading("portal");
    setError(null);
    try {
      const session = await createPortalSession(token);
      window.location.href = session.url;
    } catch (portalError) {
      const message = portalError instanceof Error ? portalError.message : "Unable to open billing portal";
      setError(message);
    } finally {
      setLoading(null);
    }
  }

  return (
    <div className="mt-4 flex flex-wrap gap-2">
      {showUpgrade ? (
        <>
          <button
            className="rounded-lg bg-zinc-900 px-3 py-2 text-xs font-medium text-white hover:bg-zinc-700 dark:bg-zinc-100 dark:text-zinc-900"
            disabled={loading !== null}
            onClick={() => openCheckout("pro")}
            type="button"
          >
            {loading === "pro" ? "Opening..." : "Upgrade to Pro"}
          </button>
          <button
            className="rounded-lg border border-zinc-300 px-3 py-2 text-xs font-medium text-zinc-700 hover:bg-zinc-100 dark:border-zinc-700 dark:text-zinc-200 dark:hover:bg-zinc-900"
            disabled={loading !== null}
            onClick={() => openCheckout("lifetime")}
            type="button"
          >
            {loading === "lifetime" ? "Opening..." : "Buy Lifetime"}
          </button>
        </>
      ) : null}
      <button
        className="rounded-lg border border-zinc-300 px-3 py-2 text-xs font-medium text-zinc-700 hover:bg-zinc-100 dark:border-zinc-700 dark:text-zinc-200 dark:hover:bg-zinc-900"
        disabled={loading !== null}
        onClick={openPortal}
        type="button"
      >
        {loading === "portal" ? "Opening..." : "Manage billing"}
      </button>
      {error ? <p className="basis-full text-xs text-red-600">{error}</p> : null}
    </div>
  );
}
