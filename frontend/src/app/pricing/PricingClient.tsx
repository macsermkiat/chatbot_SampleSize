"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { createCheckout, getSubscription } from "@/lib/api";
import { createClient } from "@/lib/supabase/client";
import SubscriptionActionModal from "@/components/SubscriptionActionModal";
import { useTranslation } from "@/lib/i18n";

interface TierConfig {
  id: string;
  nameKey: string;
  descKey: string;
  featureKeys: string[];
  price: string;
  annual: string;
  ctaKey: string;
  highlighted?: boolean;
  variantId?: { monthly: string; annual: string };
}

const TIERS: TierConfig[] = [
  {
    id: "free",
    nameKey: "free_name",
    price: "$0",
    annual: "$0",
    descKey: "free_desc",
    featureKeys: ["free_f1", "free_f2", "free_f3"],
    ctaKey: "get_started",
  },
  {
    id: "researcher",
    nameKey: "researcher_name",
    price: "$15",
    annual: "$12",
    descKey: "researcher_desc",
    featureKeys: ["researcher_f1", "researcher_f2", "researcher_f3", "researcher_f4", "researcher_f5"],
    ctaKey: "subscribe",
    highlighted: true,
    variantId: { monthly: "1417266", annual: "1417333" },
  },
  {
    id: "pro",
    nameKey: "pro_name",
    price: "$29",
    annual: "$23",
    descKey: "pro_desc",
    featureKeys: ["pro_f1", "pro_f2", "pro_f3", "pro_f4", "pro_f5"],
    ctaKey: "subscribe",
    variantId: { monthly: "1417323", annual: "1417270" },
  },
  {
    id: "institutional",
    nameKey: "institutional_name",
    price: "$49-99",
    annual: "Contact us",
    descKey: "institutional_desc",
    featureKeys: ["institutional_f1", "institutional_f2", "institutional_f3", "institutional_f4", "institutional_f5", "institutional_f6"],
    ctaKey: "contact_sales",
  },
];

// Mirrors backend TIER_RANKS in services/billing.py
const TIER_RANKS: Record<string, number> = {
  free: 0,
  researcher: 1,
  pro: 2,
  institutional: 3,
};

interface SubscriptionInfo {
  tier: string;
  status?: string;
  variant_id?: string;
  renews_at?: string;
  urls?: { customer_portal?: string; update_payment_method?: string };
}

type ModalInfo = {
  mode: "upgrade" | "downgrade" | "cancel";
  tier: TierConfig;
};

export default function PricingClient() {
  const { t } = useTranslation("pricing");
  const [annual, setAnnual] = useState(false);
  const [loading, setLoading] = useState<string | null>(null);
  const [subscription, setSubscription] = useState<SubscriptionInfo | null>(null);
  const [subLoading, setSubLoading] = useState(true);
  const [modal, setModal] = useState<ModalInfo | null>(null);
  const router = useRouter();

  // Fetch subscription for authenticated users
  useEffect(() => {
    const supabase = createClient();
    supabase.auth.getSession().then(({ data }) => {
      if (!data.session) {
        setSubLoading(false);
        return;
      }
      getSubscription()
        .then(setSubscription)
        .catch(() => setSubscription(null))
        .finally(() => setSubLoading(false));
    });
  }, []);

  async function handleSubscribe(tier: TierConfig) {
    if (!tier.variantId) {
      if (tier.id === "free") {
        router.push("/app");
      }
      return;
    }

    // Check auth before attempting checkout
    const supabase = createClient();
    const { data } = await supabase.auth.getSession();
    if (!data.session) {
      router.push(`/login?next=/pricing`);
      return;
    }

    const variantId = annual ? tier.variantId.annual : tier.variantId.monthly;
    setLoading(tier.id);
    try {
      const { checkout_url } = await createCheckout(variantId);
      window.location.href = checkout_url;
    } catch (err) {
      const message = err instanceof Error ? err.message : "Checkout failed";
      alert(message);
      setLoading(null);
    }
  }

  function getButtonConfig(tier: TierConfig): {
    label: string;
    disabled: boolean;
    style: "primary" | "secondary";
    onClick: () => void;
  } {
    // Not logged in or still loading -- use original checkout flow
    if (!subscription || subLoading) {
      return {
        label: t(tier.ctaKey),
        disabled: subLoading || loading === tier.id,
        style: tier.highlighted ? "primary" : "secondary",
        onClick: () => handleSubscribe(tier),
      };
    }

    const currentRank = TIER_RANKS[subscription.tier] ?? 0;
    const tierRank = TIER_RANKS[tier.id] ?? 0;

    // Current plan -- disabled
    if (tierRank === currentRank) {
      return {
        label: t("current_plan"),
        disabled: true,
        style: "secondary",
        onClick: () => {},
      };
    }

    // Free tier = cancellation
    if (tier.id === "free") {
      return {
        label: t("cancel_plan"),
        disabled: false,
        style: "secondary",
        onClick: () => setModal({ mode: "cancel", tier }),
      };
    }

    // Institutional -- no variant, keep original CTA
    if (!tier.variantId) {
      return {
        label: t(tier.ctaKey),
        disabled: false,
        style: "secondary",
        onClick: () => handleSubscribe(tier),
      };
    }

    // Free -> paid = checkout (no existing subscription to upgrade)
    if (subscription.tier === "free") {
      return {
        label: t("upgrade"),
        disabled: loading === tier.id,
        style: "primary",
        onClick: () => handleSubscribe(tier),
      };
    }

    // Paid -> higher paid = upgrade (modify existing subscription)
    if (tierRank > currentRank) {
      return {
        label: t("upgrade"),
        disabled: loading === tier.id,
        style: "primary",
        onClick: () => setModal({ mode: "upgrade", tier }),
      };
    }

    // Lower paid tier = downgrade (via portal)
    return {
      label: t("downgrade"),
      disabled: false,
      style: "secondary",
      onClick: () => setModal({ mode: "downgrade", tier }),
    };
  }

  return (
    <div className="min-h-screen bg-parchment-100 py-12 sm:py-16 px-4 sm:px-6">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="text-center mb-10 sm:mb-12">
          <Link
            href="/app"
            className="text-body-sm text-ink-500 hover:text-ink-800 font-body mb-4 inline-block transition-colors"
          >
            {t("back")}
          </Link>
          <h1 className="font-display text-display-lg font-semibold text-ink-900 mb-3">
            {t("title")}
          </h1>
          <p className="text-body-md text-ink-500 font-body max-w-xl mx-auto">
            {t("subtitle")}
          </p>
        </div>

        {/* Annual toggle */}
        <div className="flex items-center justify-center gap-3 mb-8 sm:mb-10">
          <span
            className={`text-body-sm font-body transition-colors ${!annual ? "text-ink-900 font-medium" : "text-ink-400"}`}
          >
            {t("monthly")}
          </span>
          <button
            onClick={() => setAnnual(!annual)}
            aria-pressed={annual}
            className={`relative w-12 h-7 rounded-full transition-colors ${
              annual ? "bg-ink-700" : "bg-ink-400"
            }`}
          >
            <span
              className={`absolute top-1 left-1 w-5 h-5 bg-white rounded-full shadow-sm transition-transform duration-200 ${
                annual ? "translate-x-5" : "translate-x-0"
              }`}
            />
          </button>
          <span
            className={`text-body-sm font-body transition-colors ${annual ? "text-ink-900 font-medium" : "text-ink-400"}`}
          >
            {t("annual")}{" "}
            <span className="text-green-700 font-medium">{t("save_20")}</span>
          </span>
        </div>

        {/* Pricing cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6">
          {TIERS.map((tier) => {
            const btn = getButtonConfig(tier);
            const tierName = t(tier.nameKey);
            return (
              <div
                key={tier.nameKey}
                className={`
                  bg-parchment-50/80 border rounded-xl p-5 sm:p-6 flex flex-col
                  ${tier.highlighted
                    ? "border-gold-500 ring-2 ring-gold-400/20 order-first md:order-none"
                    : "border-parchment-200"
                  }
                `}
              >
                {tier.highlighted && (
                  <span className="inline-block text-caption font-display font-medium bg-gold-500 text-parchment-50 px-2.5 py-0.5 rounded-full self-start mb-3 tracking-wide uppercase">
                    {t("most_popular")}
                  </span>
                )}
                <h3 className="font-display text-display-md font-semibold text-ink-800">
                  {tierName}
                </h3>
                <div className="mt-2 mb-1">
                  <span className="text-3xl font-semibold text-ink-900 font-display">
                    {annual ? tier.annual : tier.price}
                  </span>
                  {tier.price !== "$0" && tier.id !== "institutional" && (
                    <span className="text-ink-400 text-body-sm font-body">
                      {t("per_month")}
                    </span>
                  )}
                </div>
                <p className="text-ink-500 text-body-sm font-body mb-5 sm:mb-6">
                  {t(tier.descKey)}
                </p>

                <ul className="space-y-2.5 flex-1 mb-5 sm:mb-6">
                  {tier.featureKeys.map((fKey) => (
                    <li
                      key={fKey}
                      className="flex items-start gap-2 text-body-sm font-body text-ink-700"
                    >
                      <svg
                        className="w-4 h-4 text-green-700 mt-0.5 shrink-0"
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                        strokeWidth={2}
                        aria-hidden="true"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          d="M5 13l4 4L19 7"
                        />
                      </svg>
                      {t(fKey)}
                    </li>
                  ))}
                </ul>

                <button
                  onClick={btn.onClick}
                  disabled={btn.disabled}
                  className={`
                    w-full py-2.5 rounded-xl text-body-sm font-display font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed
                    ${btn.style === "primary"
                      ? "bg-ink-900 text-parchment-100 hover:bg-ink-800"
                      : "bg-parchment-100 text-ink-800 hover:bg-parchment-200 border border-parchment-300"
                    }
                  `}
                >
                  {loading === tier.id ? t("loading") : btn.label}
                </button>
              </div>
            );
          })}
        </div>

        {/* Comparison note */}
        <div className="mt-10 sm:mt-12 text-center">
          <p className="text-body-sm text-ink-400 font-body">
            {t("comparison_note")}
          </p>
        </div>
      </div>

      {/* Subscription action modal */}
      {modal && (
        <SubscriptionActionModal
          open={true}
          mode={modal.mode}
          fromTier={subscription?.tier ?? "free"}
          toTier={modal.tier.id}
          targetVariantId={
            modal.tier.variantId
              ? annual
                ? modal.tier.variantId.annual
                : modal.tier.variantId.monthly
              : ""
          }
          renewsAt={subscription?.renews_at ?? null}
          customerPortalUrl={subscription?.urls?.customer_portal ?? ""}
          onClose={() => setModal(null)}
          onComplete={() => {
            setModal(null);
            getSubscription()
              .then(setSubscription)
              .catch(() => {});
          }}
        />
      )}
    </div>
  );
}
