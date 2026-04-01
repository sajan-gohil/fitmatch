import type {
  ApplicationStatus,
  ApplicationTrackerResponse,
  BillingEntitlementsResponse,
  MatchDetailResponse,
  MatchesResponse,
  NotificationFeedResponse,
  OnboardingPayload,
  ResumeIntelligenceResponse,
  ResumeUploadResponse,
  SalaryBenchmarkResponse,
  WatchlistResponse,
} from "@/lib/types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api";

function buildHeaders(token?: string): HeadersInit {
  return token ? { Authorization: `Bearer ${token}` } : {};
}

export async function login(email: string, provider: "magic_link" | "google") {
  const response = await fetch(`${API_BASE_URL}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, provider }),
  });

  if (!response.ok) {
    throw new Error("Unable to sign in");
  }

  return response.json() as Promise<{ token: string; provider: string }>;
}

export async function saveOnboarding(token: string, payload: OnboardingPayload) {
  const response = await fetch(`${API_BASE_URL}/onboarding`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...buildHeaders(token),
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    throw new Error("Unable to save onboarding details");
  }

  return response.json() as Promise<{ completed: boolean }>;
}

export async function uploadResume(token: string, file: File) {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${API_BASE_URL}/resume/upload`, {
    method: "POST",
    headers: buildHeaders(token),
    body: formData,
  });

  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    throw new Error(payload.detail ?? "Unable to upload resume");
  }

  return response.json() as Promise<ResumeUploadResponse>;
}

export async function listMatches(token: string, limit = 10) {
  const response = await fetch(`${API_BASE_URL}/matches?limit=${limit}`, {
    method: "GET",
    headers: buildHeaders(token),
  });

  if (!response.ok) {
    throw new Error("Unable to load matches");
  }

  return response.json() as Promise<MatchesResponse>;
}

export async function getMatchDetail(token: string, externalJobId: string) {
  const response = await fetch(`${API_BASE_URL}/jobs/${encodeURIComponent(externalJobId)}/match-detail`, {
    method: "GET",
    headers: buildHeaders(token),
  });

  if (!response.ok) {
    if (response.status === 402) {
      throw new Error("Upgrade required");
    }
    throw new Error("Unable to load match detail");
  }

  return response.json() as Promise<MatchDetailResponse>;
}

export async function getResumeIntelligence(token: string, externalJobId: string) {
  const response = await fetch(`${API_BASE_URL}/resume-intelligence/jobs/${encodeURIComponent(externalJobId)}/analysis`, {
    method: "GET",
    headers: buildHeaders(token),
  });

  if (!response.ok) {
    throw new Error("Unable to load resume intelligence");
  }

  return response.json() as Promise<ResumeIntelligenceResponse>;
}

export async function getBillingEntitlements(token: string) {
  const response = await fetch(`${API_BASE_URL}/billing/entitlements`, {
    method: "GET",
    headers: buildHeaders(token),
  });
  if (!response.ok) {
    throw new Error("Unable to load billing entitlements");
  }
  return response.json() as Promise<BillingEntitlementsResponse>;
}

export async function createCheckoutSession(token: string, plan: "pro" | "lifetime") {
  const response = await fetch(`${API_BASE_URL}/billing/checkout-session`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...buildHeaders(token),
    },
    body: JSON.stringify({ plan }),
  });
  if (!response.ok) {
    throw new Error("Unable to create checkout session");
  }
  return response.json() as Promise<{ id: string; url: string; price_id: string; plan: string }>;
}

export async function createPortalSession(token: string) {
  const response = await fetch(`${API_BASE_URL}/billing/portal-session`, {
    method: "POST",
    headers: buildHeaders(token),
  });
  if (!response.ok) {
    throw new Error("Unable to open billing portal");
  }
  return response.json() as Promise<{ url: string }>;
}

export async function listNotifications(token: string, unreadOnly = false) {
  const response = await fetch(`${API_BASE_URL}/notifications?unread_only=${unreadOnly ? "true" : "false"}`, {
    method: "GET",
    headers: buildHeaders(token),
  });
  if (!response.ok) {
    throw new Error("Unable to load notifications");
  }
  return response.json() as Promise<NotificationFeedResponse>;
}

export async function markNotificationRead(token: string, notificationId: string, read: boolean) {
  const response = await fetch(`${API_BASE_URL}/notifications/${encodeURIComponent(notificationId)}`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
      ...buildHeaders(token),
    },
    body: JSON.stringify({ read }),
  });
  if (!response.ok) {
    throw new Error("Unable to update notification");
  }
  return response.json() as Promise<{ id: string; read: boolean }>;
}

export async function listWatchlist(token: string) {
  const response = await fetch(`${API_BASE_URL}/growth/watchlist`, {
    method: "GET",
    headers: buildHeaders(token),
  });
  if (!response.ok) {
    throw new Error("Unable to load watchlist");
  }
  return response.json() as Promise<WatchlistResponse>;
}

export async function addWatchlistCompany(token: string, companyName: string) {
  const response = await fetch(`${API_BASE_URL}/growth/watchlist`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...buildHeaders(token),
    },
    body: JSON.stringify({ company_name: companyName }),
  });
  if (!response.ok) {
    throw new Error("Unable to add watchlist company");
  }
  return response.json() as Promise<{ id: string; company_name: string; created_at: string }>;
}

export async function deleteWatchlistCompany(token: string, watchlistId: string) {
  const response = await fetch(`${API_BASE_URL}/growth/watchlist/${encodeURIComponent(watchlistId)}`, {
    method: "DELETE",
    headers: buildHeaders(token),
  });
  if (!response.ok) {
    throw new Error("Unable to delete watchlist company");
  }
  return response.json() as Promise<{ deleted: boolean }>;
}

export async function listApplications(token: string) {
  const response = await fetch(`${API_BASE_URL}/growth/applications`, {
    method: "GET",
    headers: buildHeaders(token),
  });
  if (!response.ok) {
    throw new Error("Unable to load application tracker");
  }
  return response.json() as Promise<ApplicationTrackerResponse>;
}

export async function upsertApplication(
  token: string,
  payload: { external_job_id: string; status: ApplicationStatus; notes?: string; applied_at?: string },
) {
  const response = await fetch(`${API_BASE_URL}/growth/applications`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
      ...buildHeaders(token),
    },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    throw new Error("Unable to save application entry");
  }
  return response.json() as Promise<{
    id: string;
    external_job_id: string;
    status: ApplicationStatus;
    notes: string;
    applied_at: string | null;
  }>;
}

export async function deleteApplication(token: string, applicationId: string) {
  const response = await fetch(`${API_BASE_URL}/growth/applications/${encodeURIComponent(applicationId)}`, {
    method: "DELETE",
    headers: buildHeaders(token),
  });
  if (!response.ok) {
    throw new Error("Unable to delete application entry");
  }
  return response.json() as Promise<{ deleted: boolean }>;
}

export async function getSalaryBenchmark(token: string, role?: string, location?: string) {
  const params = new URLSearchParams();
  if (role) params.set("role", role);
  if (location) params.set("location", location);
  const suffix = params.toString() ? `?${params.toString()}` : "";
  const response = await fetch(`${API_BASE_URL}/growth/salary-benchmark${suffix}`, {
    method: "GET",
    headers: buildHeaders(token),
  });
  if (!response.ok) {
    throw new Error("Unable to load salary benchmark");
  }
  return response.json() as Promise<SalaryBenchmarkResponse>;
}
