"use client";

import { useState } from "react";
import { completeOnboarding, type ProfileUpdate } from "@/lib/api";

const ROLE_OPTIONS = [
  { value: "medical_student", label: "Medical Student" },
  { value: "resident_fellow", label: "Resident / Fellow" },
  { value: "junior_faculty", label: "Junior Faculty" },
  { value: "senior_faculty", label: "Senior Faculty" },
  { value: "phd_student", label: "PhD Student" },
  { value: "cro_staff", label: "CRO Staff" },
  { value: "other", label: "Other" },
] as const;

const RESEARCH_AREA_OPTIONS = [
  { value: "clinical_medicine", label: "Clinical Medicine" },
  { value: "surgery", label: "Surgery" },
  { value: "public_health", label: "Public Health" },
  { value: "epidemiology", label: "Epidemiology" },
  { value: "nursing", label: "Nursing" },
  { value: "pharmacy", label: "Pharmacy" },
  { value: "other", label: "Other" },
] as const;

interface OnboardingModalProps {
  onComplete: () => void;
}

export default function OnboardingModal({ onComplete }: OnboardingModalProps) {
  const [fullName, setFullName] = useState("");
  const [role, setRole] = useState("");
  const [institution, setInstitution] = useState("");
  const [researchArea, setResearchArea] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    setError(null);

    const data: ProfileUpdate = {};
    if (fullName.trim()) data.full_name = fullName.trim();
    if (role) data.role = role;
    if (institution.trim()) data.institution = institution.trim();
    if (researchArea) data.research_area = researchArea;

    try {
      await completeOnboarding(data);
      onComplete();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save profile");
      setSaving(false);
    }
  }

  function handleSkip() {
    // Mark onboarding complete with empty data
    setSaving(true);
    completeOnboarding({})
      .then(() => onComplete())
      .catch(() => onComplete());
  }

  const selectClasses =
    "w-full px-3 py-2.5 border border-parchment-200 rounded-xl bg-white text-ink-900 text-body-sm font-body focus:outline-none focus:border-gold-400 focus:shadow-[0_0_0_3px_oklch(0.85_0.12_85/0.15)] transition-all appearance-none";
  const inputClasses = selectClasses;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-ink-900/40 backdrop-blur-sm px-4">
      <div className="w-full max-w-lg bg-parchment-50 border border-parchment-200 rounded-2xl shadow-xl p-6 sm:p-8">
        <div className="text-center mb-6">
          <h2 className="font-display text-display-md font-semibold text-ink-900">
            Welcome to Protocol
          </h2>
          <p className="text-body-sm text-ink-500 font-body mt-1">
            Tell us a bit about yourself to personalize your experience.
          </p>
        </div>

        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label
              htmlFor="onb-name"
              className="block text-body-sm font-body font-medium text-ink-700 mb-1"
            >
              Full Name
            </label>
            <input
              id="onb-name"
              type="text"
              maxLength={200}
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              className={inputClasses}
              placeholder="Dr. Jane Smith"
            />
            <p className="mt-0.5 text-xs text-ink-400 font-body">
              Used on exported protocol documents
            </p>
          </div>

          <div>
            <label
              htmlFor="onb-role"
              className="block text-body-sm font-body font-medium text-ink-700 mb-1"
            >
              Role
            </label>
            <select
              id="onb-role"
              value={role}
              onChange={(e) => setRole(e.target.value)}
              className={selectClasses}
            >
              <option value="">Select your role...</option>
              {ROLE_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label
              htmlFor="onb-institution"
              className="block text-body-sm font-body font-medium text-ink-700 mb-1"
            >
              Institution
            </label>
            <input
              id="onb-institution"
              type="text"
              maxLength={300}
              value={institution}
              onChange={(e) => setInstitution(e.target.value)}
              className={inputClasses}
              placeholder="Mahidol University"
            />
          </div>

          <div>
            <label
              htmlFor="onb-area"
              className="block text-body-sm font-body font-medium text-ink-700 mb-1"
            >
              Research Area
            </label>
            <select
              id="onb-area"
              value={researchArea}
              onChange={(e) => setResearchArea(e.target.value)}
              className={selectClasses}
            >
              <option value="">Select your research area...</option>
              {RESEARCH_AREA_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
          </div>

          <div className="flex items-center gap-3 pt-2">
            <button
              type="submit"
              disabled={saving}
              className="flex-1 py-2.5 rounded-xl bg-ink-900 text-parchment-100 text-body-sm font-display font-medium hover:bg-ink-800 transition-colors disabled:opacity-50"
            >
              {saving ? "Saving..." : "Continue"}
            </button>
            <button
              type="button"
              onClick={handleSkip}
              disabled={saving}
              className="px-4 py-2.5 rounded-xl border border-parchment-200 text-ink-500 text-body-sm font-body hover:bg-parchment-100 transition-colors disabled:opacity-50"
            >
              Skip for now
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
