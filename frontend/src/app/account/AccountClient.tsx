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
import { useTranslation } from "@/lib/i18n";

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

const TIER_KEYS: Record<string, string> = {
  free: "tier_free",
  researcher: "tier_researcher",
  researcher_annual: "tier_researcher",
  pro: "tier_pro",
  pro_monthly: "tier_pro",
  pro_annual: "tier_pro",
  institutional: "tier_institutional",
};

const STATUS_KEYS: Record<string, { key: string; className: string }> = {
  active: { key: "active", className: "bg-green-100 text-green-700" },
  past_due: { key: "past_due", className: "bg-yellow-100 text-yellow-700" },
  cancelled: { key: "cancelled", className: "bg-red-100 text-red-700" },
  paused: { key: "paused", className: "bg-parchment-200 text-parchment-700" },
};

const ROLE_KEYS = [
  { value: "medical_student", key: "role_medical_student" },
  { value: "resident_fellow", key: "role_resident_fellow" },
  { value: "junior_faculty", key: "role_junior_faculty" },
  { value: "senior_faculty", key: "role_senior_faculty" },
  { value: "phd_student", key: "role_phd_student" },
  { value: "cro_staff", key: "role_cro_staff" },
  { value: "other", key: "role_other" },
] as const;

const AREA_KEYS = [
  { value: "clinical_medicine", key: "area_clinical_medicine" },
  { value: "surgery", key: "area_surgery" },
  { value: "public_health", key: "area_public_health" },
  { value: "epidemiology", key: "area_epidemiology" },
  { value: "nursing", key: "area_nursing" },
  { value: "pharmacy", key: "area_pharmacy" },
  { value: "other", key: "area_other" },
] as const;

export default function AccountClient() {
  const { t } = useTranslation("account");
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
        <p className="text-parchment-500 font-display">{t("loading")}</p>
      </div>
    );
  }

  const tierKey = TIER_KEYS[subscription?.tier ?? "free"];
  const tierLabel = tierKey ? t(tierKey) : (subscription?.tier ?? t("tier_free"));
  const statusInfo = STATUS_KEYS[subscription?.status ?? ""];
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
          {t("back")}
        </Link>

        <h1 className="font-display text-display-lg font-semibold text-ink-900">
          {t("title")}
        </h1>

        {/* Profile */}
        <section className="bg-parchment-50/80 border border-parchment-200 rounded-xl p-5 sm:p-6">
          <div className="flex items-center justify-between mb-3">
            <h2 className="font-display text-lg font-semibold text-ink-800">
              {t("profile")}
            </h2>
            {!editing && (
              <button
                onClick={() => setEditing(true)}
                className="text-xs text-ink-500 hover:text-ink-700 font-body hover:underline"
              >
                {t("edit")}
              </button>
            )}
          </div>

          {editing ? (
            <div className="space-y-3">
              <div>
                <label className="block text-xs text-ink-400 font-body mb-1">{t("full_name")}</label>
                <input
                  type="text"
                  maxLength={200}
                  value={editForm.full_name}
                  onChange={(e) => setEditForm({ ...editForm, full_name: e.target.value })}
                  className={inputClasses}
                  placeholder={t("name_placeholder")}
                />
              </div>
              <div>
                <label className="block text-xs text-ink-400 font-body mb-1">{t("role")}</label>
                <select
                  value={editForm.role}
                  onChange={(e) => setEditForm({ ...editForm, role: e.target.value })}
                  className={inputClasses}
                >
                  <option value="">{t("role_placeholder")}</option>
                  {ROLE_KEYS.map((opt) => (
                    <option key={opt.value} value={opt.value}>{t(opt.key)}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-xs text-ink-400 font-body mb-1">{t("institution")}</label>
                <input
                  type="text"
                  maxLength={300}
                  value={editForm.institution}
                  onChange={(e) => setEditForm({ ...editForm, institution: e.target.value })}
                  className={inputClasses}
                  placeholder={t("institution_placeholder")}
                />
              </div>
              <div>
                <label className="block text-xs text-ink-400 font-body mb-1">{t("research_area")}</label>
                <select
                  value={editForm.research_area}
                  onChange={(e) => setEditForm({ ...editForm, research_area: e.target.value })}
                  className={inputClasses}
                >
                  <option value="">{t("area_placeholder")}</option>
                  {AREA_KEYS.map((opt) => (
                    <option key={opt.value} value={opt.value}>{t(opt.key)}</option>
                  ))}
                </select>
              </div>
              <div className="flex gap-2 pt-1">
                <button
                  onClick={handleSaveProfile}
                  disabled={saving}
                  className="px-4 py-2 bg-ink-900 text-parchment-100 text-body-sm font-display rounded-xl hover:bg-ink-800 transition-colors disabled:opacity-50"
                >
                  {saving ? t("saving") : t("save")}
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
                  {t("cancel")}
                </button>
              </div>
            </div>
          ) : (
            <dl className="space-y-2 text-sm">
              <div className="flex justify-between">
                <dt className="text-ink-400 font-body">{t("email")}</dt>
                <dd className="text-ink-800 font-medium">{user?.email}</dd>
              </div>
              {profile?.full_name && (
                <div className="flex justify-between">
                  <dt className="text-ink-400 font-body">{t("name")}</dt>
                  <dd className="text-ink-800 font-medium">{profile.full_name}</dd>
                </div>
              )}
              {profile?.role && (
                <div className="flex justify-between">
                  <dt className="text-ink-400 font-body">{t("role")}</dt>
                  <dd className="text-ink-800 font-medium">
                    {t(`role_${profile.role}`) !== `account.role_${profile.role}` ? t(`role_${profile.role}`) : profile.role}
                  </dd>
                </div>
              )}
              {profile?.institution && (
                <div className="flex justify-between">
                  <dt className="text-ink-400 font-body">{t("institution")}</dt>
                  <dd className="text-ink-800 font-medium">{profile.institution}</dd>
                </div>
              )}
              {profile?.research_area && (
                <div className="flex justify-between">
                  <dt className="text-ink-400 font-body">{t("research_area")}</dt>
                  <dd className="text-ink-800 font-medium">
                    {t(`area_${profile.research_area}`) !== `account.area_${profile.research_area}` ? t(`area_${profile.research_area}`) : profile.research_area}
                  </dd>
                </div>
              )}
              <div className="flex justify-between">
                <dt className="text-ink-400 font-body">{t("user_id")}</dt>
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
            {t("subscription")}
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
                {t(statusInfo.key)}
              </span>
            )}
          </div>

          {subscription?.renews_at && (
            <p className="text-sm text-parchment-600 mb-2">
              {t("renews")}{" "}
              {new Date(subscription.renews_at).toLocaleDateString("en-US", {
                year: "numeric",
                month: "long",
                day: "numeric",
              })}
            </p>
          )}

          {subscription?.ends_at && (
            <p className="text-sm text-red-600 mb-2">
              {t("ends")}{" "}
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
                {t("upgrade_plan")}
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
                    {t("manage_subscription")}
                  </a>
                )}
                {subscription?.urls?.update_payment_method && (
                  <a
                    href={subscription.urls.update_payment_method}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="px-4 py-2 border border-parchment-200 text-ink-700 text-body-sm font-display rounded-xl hover:bg-parchment-100 transition-colors"
                  >
                    {t("update_payment")}
                  </a>
                )}
              </>
            )}
          </div>
        </section>

        {/* Usage */}
        <section className="bg-parchment-50/80 border border-parchment-200 rounded-xl p-5 sm:p-6">
          <h2 className="font-display text-lg font-semibold text-ink-800 mb-3">
            {t("usage_title")}
          </h2>
          <div className="flex items-baseline gap-2 mb-3">
            <span className="text-2xl font-semibold text-ink-900">
              {usage?.query_count ?? 0}
            </span>
            <span className="text-parchment-500 text-sm">
              / {usage?.query_limit ?? t("unlimited")} {t("queries")}
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
              {t("resets")}{" "}
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
                {t("limit_reached")}{" "}
                <Link
                  href="/pricing"
                  className="font-medium underline hover:text-red-800"
                >
                  {t("upgrade_link")}
                </Link>{" "}
                {t("for_more")}
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
            {t("sign_out")}
          </button>
        </section>
      </div>
    </div>
  );
}
