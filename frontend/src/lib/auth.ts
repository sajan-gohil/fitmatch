export const AUTH_TOKEN_KEY = "fitmatch.session.token";
export const ONBOARDING_COMPLETED_KEY = "fitmatch.onboarding.completed";
export const MATCH_FILTER_ROLE_KEY = "fitmatch.matches.filter.role";
export const MATCH_FILTER_LOCATION_KEY = "fitmatch.matches.filter.location";

export function saveToken(token: string) {
  if (typeof window !== "undefined") {
    window.localStorage.setItem(AUTH_TOKEN_KEY, token);
  }
}

export function getToken() {
  if (typeof window === "undefined") {
    return null;
  }

  return window.localStorage.getItem(AUTH_TOKEN_KEY);
}

export function markOnboardingCompleted() {
  if (typeof window !== "undefined") {
    window.localStorage.setItem(ONBOARDING_COMPLETED_KEY, "true");
  }
}

export function isOnboardingCompleted() {
  if (typeof window === "undefined") {
    return false;
  }

  return window.localStorage.getItem(ONBOARDING_COMPLETED_KEY) === "true";
}

export function saveMatchFilters(role: string, location: string) {
  if (typeof window !== "undefined") {
    window.localStorage.setItem(MATCH_FILTER_ROLE_KEY, role);
    window.localStorage.setItem(MATCH_FILTER_LOCATION_KEY, location);
  }
}

export function getMatchFilters() {
  if (typeof window === "undefined") {
    return { role: "", location: "" };
  }
  return {
    role: window.localStorage.getItem(MATCH_FILTER_ROLE_KEY) ?? "",
    location: window.localStorage.getItem(MATCH_FILTER_LOCATION_KEY) ?? "",
  };
}
