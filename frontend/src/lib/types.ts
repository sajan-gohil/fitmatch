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
