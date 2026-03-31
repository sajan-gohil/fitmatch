"use client";

import { useRouter } from "next/navigation";
import { ChangeEvent, useMemo, useState } from "react";

import { getToken } from "@/lib/auth";
import { uploadResume } from "@/lib/api";
import type { ResumeUploadResponse } from "@/lib/types";

const ACCEPTED_FORMATS = ["application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "application/msword"];
const MAX_BYTES = 10 * 1024 * 1024;
const DASHBOARD_REDIRECT_DELAY_MS = 600;

export default function UploadResumePage() {
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadedResume, setUploadedResume] = useState<ResumeUploadResponse | null>(null);

  const acceptedList = useMemo(() => ".pdf,.docx,.doc", []);

  async function onFileChange(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file) {
      return;
    }

    const token = getToken();
    if (!token) {
      router.push("/login");
      return;
    }

    if (!ACCEPTED_FORMATS.includes(file.type)) {
      setError("Only PDF or DOCX/DOC files are allowed");
      return;
    }

    if (file.size > MAX_BYTES) {
      setError("File exceeds 10MB limit");
      return;
    }

    setUploading(true);
    setError(null);

    try {
      const response = await uploadResume(token, file);
      setUploadedResume(response);
      setTimeout(() => router.push("/dashboard"), DASHBOARD_REDIRECT_DELAY_MS);
    } catch (uploadError) {
      const message = uploadError instanceof Error ? uploadError.message : "Upload failed";
      setError(message);
    } finally {
      setUploading(false);
    }
  }

  return (
    <div className="mx-auto flex min-h-screen w-full max-w-2xl items-center px-6 py-10">
      <main className="w-full rounded-2xl border border-zinc-200 bg-white p-8 shadow-sm dark:border-zinc-800 dark:bg-zinc-950">
        <h1 className="text-2xl font-semibold text-zinc-900 dark:text-zinc-100">Upload Resume</h1>
        <p className="mt-2 text-sm text-zinc-600 dark:text-zinc-300">Upload a PDF or DOCX file (max 10MB). Your resume is parsed and normalized immediately.</p>

        <label className="mt-6 block rounded-xl border border-dashed border-zinc-300 p-6 text-center text-sm text-zinc-700 dark:border-zinc-700 dark:text-zinc-200">
          <span className="block">Choose resume file</span>
          <input
            accept={acceptedList}
            className="mt-4 block w-full text-sm"
            onChange={onFileChange}
            type="file"
          />
        </label>

        {uploading ? <p className="mt-4 text-sm text-zinc-600 dark:text-zinc-300">Uploading and parsing...</p> : null}
        {error ? <p className="mt-4 text-sm text-red-600">{error}</p> : null}

        {uploadedResume ? (
          <section className="mt-6 rounded-lg border border-zinc-200 p-4 text-sm dark:border-zinc-800">
            <h2 className="font-medium text-zinc-900 dark:text-zinc-100">Parsed Resume</h2>
            <p className="mt-2 text-zinc-700 dark:text-zinc-200">Target role: {uploadedResume.parsed.target_role}</p>
            <p className="mt-1 text-zinc-700 dark:text-zinc-200">Skills: {uploadedResume.parsed.skills.join(", ")}</p>
            <p className="mt-3 text-zinc-500 dark:text-zinc-400">Redirecting to dashboard...</p>
          </section>
        ) : null}
      </main>
    </div>
  );
}
