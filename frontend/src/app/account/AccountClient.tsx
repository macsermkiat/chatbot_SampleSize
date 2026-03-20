"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { createClient } from "@/lib/supabase/client";
import {
  getSubscription,
  getUsage,
  getProfile,
  updateProfile,
  type UserProfile,
} from "@/lib/api";
import type { User } from "@supabase/supabase-js";

interface SubscriptionInfo {
  tier: string;
  status?: string;
  billing_cycle?: string;
  renews_at?: string;
  ends_at?: string;
  urls?: { customer_portal?: string; update_payment_method?: string };
}

interface UsageInfo {
  tier: string;
  query_count: number;
  query_limit: number | null;
  period_start?: string;
  period_end?: string;
  is_allowed: boolean;
  project_count?: number;
  project_limit?: number | null;
  can_create_project?: boolean;
}

const TIER_LABELS: Record<string, string> = {
  free: "Free",
  researcher: "Researcher",
  researcher_annual: "Researcher",
  pro: "Pro",
  pro_monthly: "Pro",
  pro_annual: "Pro",
  institutional: "Institutional",
};

const STATUS_LABELS: Record<string, { label: string; className: string }> = {
  active: { label: "Active", className: "bg-green-100 text-green-700" },
  past_due: { label: "Past Due", className: "bg-yellow-100 text-yellow-700" },
  cancelled: { label: "Cancelled", className: "bg-red-100 text-red-700" },
  paused: { label: "Paused", className: "bg-parchment-200 text-parchment-700" },
};

const ROLE_LABELS: Record<string, string> = {
  medical_student: "Medical Student",
  resident_fellow: "Resident / Fellow",
  junior_faculty: "Junior Faculty",
  senior_faculty: "Senior Faculty",
  phd_student: "PhD Student",
  cro_staff: "CRO Staff",
  other: "Other",
};

const RESEARCH_AREA_LABELS: Record<string, string> = {
  clinical_medicine: "Clinical Medicine",
  surgery: "Surgery",
  public_health: "Public Health",
  epidemiology: "Epidemiology",
  nursing: "Nursing",
  pharmacy: "Pharmacy",
  other: "Other",
};

export default function AccountClient() {
  const [user, setUser] = useState<User | null>(null);
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [subscription, setSubscription] = useState<SubscriptionInfo | null>(null);
  const [usage, setUsage] = useState<UsageInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [editForm, setEditForm] = useState({
    full_name: "",
    role: "",
    institution: "",
    research_area: "",
  });

  useEffect(() => {
    async function load() {
      const supabase = createClient();
      const { data } = await supabase.auth.getUser();

      if (!data.user) {
        window.location.href = "/login";
        return;
      }

      setUser(data.user);

      const [sub, usg, prof] = await Promise.all([
        getSubscription().catch(() => ({ tier: "free" } as SubscriptionInfo)),
        getUsage().catch(
          () =>
            ({
              tier: "free",
              query_count: 0,
              query_limit: 5,
              is_allowed: true,
            }) as UsageInfo,
        ),
        getProfile().catch(() => null),
      ]);

      setSubscription(sub);
      setUsage(usg);
      if (prof) {
        setProfile(prof);
        setEditForm({
          full_name: prof.full_name ?? "",
          role: prof.role ?? "",
          institution: prof.institution ?? "",
          research_area: prof.research_area ?? "",
        });
      }
      setLoading(false);
    }

    load();
  }, []);

  async function handleSaveProfile() {
    setSaving(true);
    try {
      const data: Record<string, string> = {};
      if (editForm.full_name.trim()) data.full_name = editForm.full_name.trim();
      if (editForm.role) data.role = editForm.role;
      if (editForm.institution.trim()) data.institution = editForm.institution.trim();
      if (editForm.research_area) data.research_area = editForm.research_area;

      if (Object.keys(data).length === 0) {
        setEditing(false);
        setSaving(false);
        return;
      }

      const updated = await updateProfile(data);
      setProfile(updated);
      setEditing(false);
    } catch {
      // Keep editing open on error
    } finally {
      setSaving(false);
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-parchment-100 flex items-center justify-center">
        <p className="text-parchment-500 font-display">Loading...</p>
      </div>
    );
  }

  const tierLabel = TIER_LABELS[subscription?.tier ?? "free"] ?? subscription?.tier ?? "Free";
  const statusInfo = STATUS_LABELS[subscription?.status ?? ""] ?? null;
  const usagePercent =
    usage?.query_limit && usage.query_limit > 0
      ? Math.min(100, Math.round((usage.query_count / usage.query_limit) * 100))
      : null;

  const inputClasses =
    "w-full px-3 py-2 border border-parchment-200 rounded-xl bg-white text-ink-900 text-body-sm font-body focus:outline-none focus:border-gold-400 focus:shadow-[0_0_0_3px_oklch(0.85_0.12_85/0.15)] transition-all";

  return (
    <div className="min-h-screen bg-parchment-100 py-10 sm:py-16 px-4 sm:px-6">
      <div className="max-w-2xl mx-auto space-y-6 sm:space-y-8">
        {/* Back link */}
        <Link
          href="/app"
          className="text-body-sm text-ink-500 hover:text-ink-800 font-body inline-block transition-colors"
        >
          &larr; Back to app
        </Link>

        <h1 className="font-display text-display-lg font-semibold text-ink-900">
          Account & Billing
        </h1>

        {/* Profile */}
        <section className="bg-parchment-50/80 border border-parchment-200 rounded-xl p-5 sm:p-6">
          <div className="flex items-center justify-between mb-3">
            <h2 className="font-display text-lg font-semibold text-ink-800">
              Profile
            </h2>
            {!editing && (
              <button
                onClick={() => setEditing(true)}
                className="text-xs text-ink-500 hover:text-ink-700 font-body hover:underline"
              >
                Edit
              </button>
            )}
          </div>

          {editing ? (
            <div className="space-y-3">
              <div>
                <label className="block text-xs text-ink-400 font-body mb-1">Full Name</label>
                <input
                  type="text"
                  maxLength={200}
                  value={editForm.full_name}
                  onChange={(e) => setEditForm({ ...editForm, full_name: e.target.value })}
                  className={inputClasses}
                  placeholder="Dr. Jane Smith"
                />
              </div>
              <div>
                <label className="block text-xs text-ink-400 font-body mb-1">Role</label>
                <select
                  value={editForm.role}
                  onChange={(e) => setEditForm({ ...editForm, role: e.target.value })}
                  className={inputClasses}
                >
                  <option value="">Select role...</option>
                  {Object.entries(ROLE_LABELS).map(([value, label]) => (
                    <option key={value} value={value}>{label}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-xs text-ink-400 font-body mb-1">Institution</label>
                <input
                  type="text"
                  maxLength={300}
                  value={editForm.institution}
                  onChange={(e) => setEditForm({ ...editForm, institution: e.target.value })}
                  className={inputClasses}
                  placeholder="Mahidol University"
                />
              </div>
              <div>
                <label className="block text-xs text-ink-400 font-body mb-1">Research Area</label>
                <select
                  value={editForm.research_area}
                  onChange={(e) => setEditForm({ ...editForm, research_area: e.target.value })}
                  className={inputClasses}
                >
                  <option value="">Select research area...</option>
                  {Object.entries(RESEARCH_AREA_LABELS).map(([value, label]) => (
                    <option key={value} value={value}>{label}</option>
                  ))}
                </select>
              </div>
              <div className="flex gap-2 pt-1">
                <button
                  onClick={handleSaveProfile}
                  disabled={saving}
                  className="px-4 py-2 bg-ink-900 text-parchment-100 text-body-sm font-display rounded-xl hover:bg-ink-800 transition-colors disabled:opacity-50"
                >
                  {saving ? "Saving..." : "Save"}
                </button>
                <button
                  onClick={() => {
                    setEditing(false);
                    if (profile) {
                      setEditForm({
                        full_name: profile.full_name ?? "",
                        role: profile.role ?? "",
                        institution: profile.institution ?? "",
                        research_area: profile.research_area ?? "",
                      });
                    }
                  }}
                  className="px-4 py-2 border border-parchment-200 text-ink-500 text-body-sm font-body rounded-xl hover:bg-parchment-100 transition-colors"
                >
                  Cancel
                </button>
              </div>
            </div>
          ) : (
            <dl className="space-y-2 text-sm">
              <div className="flex justify-between">
                <dt className="text-ink-400 font-body">Email</dt>
                <dd className="text-ink-800 font-medium">{user?.email}</dd>
              </div>
              {profile?.full_name && (
                <div className="flex justify-between">
                  <dt className="text-ink-400 font-body">Name</dt>
                  <dd className="text-ink-800 font-medium">{profile.full_name}</dd>
                </div>
              )}
              {profile?.role && (
                <div className="flex justify-between">
                  <dt className="text-ink-400 font-body">Role</dt>
                  <dd className="text-ink-800 font-medium">
                    {ROLE_LABELS[profile.role] ?? profile.role}
                  </dd>
                </div>
              )}
              {profile?.institution && (
                <div className="flex justify-between">
                  <dt className="text-ink-400 font-body">Institution</dt>
                  <dd className="text-ink-800 font-medium">{profile.institution}</dd>
                </div>
              )}
              {profile?.research_area && (
                <div className="flex justify-between">
                  <dt className="text-ink-400 font-body">Research Area</dt>
                  <dd className="text-ink-800 font-medium">
                    {RESEARCH_AREA_LABELS[profile.research_area] ?? profile.research_area}
                  </dd>
                </div>
              )}
              <div className="flex justify-between">
                <dt className="text-ink-400 font-body">User ID</dt>
                <dd className="text-ink-600 font-mono text-xs">
                  {user?.id.slice(0, 12)}...
                </dd>
              </div>
            </dl>
          )}
        </section>

        {/* Subscription */}
        <section className="bg-parchment-50/80 border border-parchment-200 rounded-xl p-5 sm:p-6">
          <h2 className="font-display text-lg font-semibold text-ink-800 mb-3">
            Subscription
          </h2>
          <div className="flex items-center gap-3 mb-4">
            <span className="text-xl font-semibold text-ink-900">
              {tierLabel}
            </span>
            {subscription?.billing_cycle && subscription.tier !== "free" && (
              <span className="text-xs px-2 py-0.5 rounded-full font-medium bg-parchment-200 text-parchment-700 capitalize">
                {subscription.billing_cycle}
              </span>
            )}
            {statusInfo && (
              <span
                className={`text-xs px-2 py-0.5 rounded-full font-medium ${statusInfo.className}`}
              >
                {statusInfo.label}
              </span>
            )}
          </div>

          {subscription?.renews_at && (
            <p className="text-sm text-parchment-600 mb-2">
              Renews:{" "}
              {new Date(subscription.renews_at).toLocaleDateString("en-US", {
                year: "numeric",
                month: "long",
                day: "numeric",
              })}
            </p>
          )}

          {subscription?.ends_at && (
            <p className="text-sm text-red-600 mb-2">
              Ends:{" "}
              {new Date(subscription.ends_at).toLocaleDateString("en-US", {
                year: "numeric",
                month: "long",
                day: "numeric",
              })}
            </p>
          )}

          <div className="flex gap-3 mt-4">
            {subscription?.tier === "free" ? (
              <Link
                href="/pricing"
                className="px-4 py-2 bg-ink-900 text-parchment-100 text-body-sm font-display rounded-xl hover:bg-ink-800 transition-colors"
              >
                Upgrade Plan
              </Link>
            ) : (
              <>
                {subscription?.urls?.customer_portal && (
                  <a
                    href={subscription.urls.customer_portal}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="px-4 py-2 bg-ink-900 text-parchment-100 text-body-sm font-display rounded-xl hover:bg-ink-800 transition-colors"
                  >
                    Manage Subscription
                  </a>
                )}
                {subscription?.urls?.update_payment_method && (
                  <a
                    href={subscription.urls.update_payment_method}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="px-4 py-2 border border-parchment-200 text-ink-700 text-body-sm font-display rounded-xl hover:bg-parchment-100 transition-colors"
                  >
                    Update Payment
                  </a>
                )}
              </>
            )}
          </div>
        </section>

        {/* Usage */}
        <section className="bg-parchment-50/80 border border-parchment-200 rounded-xl p-5 sm:p-6">
          <h2 className="font-display text-lg font-semibold text-ink-800 mb-3">
            Usage This Period
          </h2>
          <div className="flex items-baseline gap-2 mb-3">
            <span className="text-2xl font-semibold text-ink-900">
              {usage?.query_count ?? 0}
            </span>
            <span className="text-parchment-500 text-sm">
              / {usage?.query_limit ?? "unlimited"} queries
            </span>
          </div>

          {usagePercent !== null && (
            <div className="w-full bg-parchment-200 rounded-full h-2 mb-2">
              <div
                className={`h-2 rounded-full transition-all ${
                  usagePercent >= 90
                    ? "bg-red-500"
                    : usagePercent >= 70
                      ? "bg-yellow-500"
                      : "bg-green-500"
                }`}
                style={{ width: `${usagePercent}%` }}
              />
            </div>
          )}

          {usage?.period_end && (
            <p className="text-xs text-parchment-500">
              Resets:{" "}
              {new Date(usage.period_end).toLocaleDateString("en-US", {
                year: "numeric",
                month: "long",
                day: "numeric",
              })}
            </p>
          )}

          {!usage?.is_allowed && (
            <div className="mt-3 p-3 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-sm text-red-700">
                You have reached your query limit.{" "}
                <Link
                  href="/pricing"
                  className="font-medium underline hover:text-red-800"
                >
                  Upgrade your plan
                </Link>{" "}
                for more queries.
              </p>
            </div>
          )}
        </section>

        {/* Sign Out */}
        <section className="text-center">
          <button
            onClick={async () => {
              const supabase = createClient();
              await supabase.auth.signOut();
              window.location.href = "/login";
            }}
            className="text-sm text-red-600 hover:text-red-700 font-medium"
          >
            Sign Out
          </button>
        </section>
      </div>
    </div>
  );
}
