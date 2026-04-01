export type WorkType = "remote" | "hybrid" | "onsite";

export type OnboardingPayload = {
  target_roles: string[];
  preferred_locations: string[];
  work_type_preferences: WorkType[];
};

export type ParsedResume = {
  source_file: string;
  format: string;
  summary: string;
  skills: string[];
  target_role: string;
};

export type ResumeUploadResponse = {
  id: string;
  owner: string;
  file_name: string;
  file_size: number;
  content_type: string;
  parsed: ParsedResume;
};

export type Match = {
  job: Record<string, unknown>;
  score: number;
  breakdown: {
    title: number;
    skills: number;
    experience: number;
    education: number;
  };
};

export type MatchesResponse = {
  matches: Match[];
  total: number;
  tier: "free" | "pro" | "lifetime";
  enforced_limit: number | null;
};

export type MatchDetailResponse = Match;

export type ResumeScoring = {
  clarity_formatting: number;
  quantification: number;
  keyword_density: number;
  experience_narrative: number;
  skills_coverage: number;
  overall: number;
};

export type SkillGap = {
  required_skills: string[];
  matched_skills: string[];
  missing_skills: string[];
};

export type RewriteSuggestion = {
  id: string;
  resume_id: string;
  original: string;
  suggested: string;
  state: "pending" | "accepted" | "dismissed" | "edited";
};

export type ResumeIntelligenceResponse = {
  tier: "free" | "pro" | "lifetime";
  is_preview: boolean;
  skill_gap: SkillGap;
  fit_report: {
    summary: string;
    suggestions: string[];
  };
  resume_scoring: ResumeScoring;
  rewrite_suggestions: RewriteSuggestion[];
};

export type BillingEntitlementsResponse = {
  plan: "free" | "pro" | "lifetime";
  status: string;
  is_paid: boolean;
};

export type NotificationItem = {
  id: string;
  trigger: "high_match" | "watchlist" | "salary_threshold" | "freshness" | "deadline";
  title: string;
  body: string;
  channels: ("email" | "in_app" | "sms")[];
  metadata: Record<string, unknown>;
  read: boolean;
  created_at: string;
  read_at: string | null;
};

export type NotificationFeedResponse = {
  items: NotificationItem[];
  total: number;
  unread_count: number;
};
