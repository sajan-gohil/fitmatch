import type {
  MatchDetailResponse,
  MatchesResponse,
  OnboardingPayload,
  ResumeUploadResponse,
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
    throw new Error("Unable to load match detail");
  }

  return response.json() as Promise<MatchDetailResponse>;
}
