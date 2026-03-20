"use client";

import { useState, useMemo, useEffect } from "react";
import { useRouter } from "next/navigation";
import Image from "next/image";
import Link from "next/link";
import { createClient } from "@/lib/supabase/client";
import { PASSWORD_CHECKS, isPasswordStrong } from "@/lib/password-validation";

function PasswordStrength({ password }: { password: string }) {
  if (!password) return null;

  return (
    <ul className="mt-2 space-y-1">
      {PASSWORD_CHECKS.map((check) => {
        const passed = check.test(password);
        return (
          <li
            key={check.label}
            className={`text-xs font-body flex items-center gap-1.5 ${
              passed ? "text-green-600" : "text-ink-400"
            }`}
          >
            <span className="w-3.5 text-center">{passed ? "\u2713" : "\u2022"}</span>
            {check.label}
          </li>
        );
      })}
    </ul>
  );
}

export default function ResetPasswordClient() {
  const router = useRouter();
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [confirmTouched, setConfirmTouched] = useState(false);
  const [loading, setLoading] = useState(false);
  const [checking, setChecking] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const allChecksPassed = useMemo(
    () => isPasswordStrong(password),
    [password],
  );

  const passwordsMatch = password === confirmPassword;

  // Verify the user has a valid session (set by the callback route)
  useEffect(() => {
    const supabase = createClient();
    supabase.auth.getSession().then(({ data: { session } }) => {
      if (!session) {
        router.replace("/login?error=Invalid+or+expired+reset+link");
      } else {
        setChecking(false);
      }
    });
  }, [router]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);

    if (!allChecksPassed) {
      setError("Password does not meet all requirements.");
      return;
    }
    if (!passwordsMatch) {
      setError("Passwords do not match.");
      return;
    }

    setLoading(true);
    try {
      const supabase = createClient();
      const { error: updateError } = await supabase.auth.updateUser({
        password,
      });

      if (updateError) {
        setError(updateError.message);
        setLoading(false);
        return;
      }

      setSuccess(true);
      setPassword("");
      setConfirmPassword("");
      setTimeout(() => {
        router.push("/app");
      }, 2000);
    } catch {
      setError("An unexpected error occurred. Please try again.");
      setLoading(false);
    }
  }

  if (checking) {
    return (
      <div className="min-h-screen bg-parchment-100 flex items-center justify-center">
        <p className="text-parchment-600">Verifying reset link...</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-parchment-100 flex items-center justify-center px-4">
      <div className="w-full max-w-md">
        {/* Header */}
        <div className="text-center mb-8">
          <Link href="/" className="inline-flex items-center gap-2.5 hover:opacity-80 transition-opacity mb-2">
            <Image src="/logo_protocol.png" alt="Protocol" width={36} height={36} className="h-9 w-auto" />
            <span className="font-display text-display-lg font-semibold text-ink-900">Protocol</span>
          </Link>
          <p className="text-body-sm text-ink-500 font-body">
            AI-powered medical research methodology assistant
          </p>
        </div>

        {/* Card */}
        <div className="bg-parchment-50/80 border border-parchment-200 rounded-xl p-6 sm:p-8 shadow-sm">
          <div className="text-center mb-6">
            <h2 className="font-display text-display-md font-semibold text-ink-800">
              Set New Password
            </h2>
            <p className="text-body-sm text-ink-400 font-body mt-1">
              Choose a strong password for your account
            </p>
          </div>

          {error && (
            <div role="alert" className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
              {error}
            </div>
          )}

          {success ? (
            <div role="status" className="mb-4 p-3 bg-green-50 border border-green-200 rounded-lg text-green-700 text-sm">
              Password updated successfully. Redirecting...
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label
                  htmlFor="password"
                  className="block text-body-sm font-body font-medium text-ink-700 mb-1"
                >
                  New Password
                </label>
                <input
                  id="password"
                  type="password"
                  required
                  minLength={8}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full px-3 py-2.5 border border-parchment-200 rounded-xl bg-white text-ink-900 text-body-sm font-body focus:outline-none focus:border-gold-400 focus:shadow-[0_0_0_3px_oklch(0.85_0.12_85/0.15)] transition-all"
                  placeholder="Min 8 characters"
                />
                <PasswordStrength password={password} />
              </div>

              <div>
                <label
                  htmlFor="confirmPassword"
                  className="block text-body-sm font-body font-medium text-ink-700 mb-1"
                >
                  Confirm New Password
                </label>
                <input
                  id="confirmPassword"
                  type="password"
                  required
                  value={confirmPassword}
                  onChange={(e) => {
                    setConfirmPassword(e.target.value);
                    setConfirmTouched(true);
                  }}
                  className={`w-full px-3 py-2.5 border rounded-xl bg-white text-ink-900 text-body-sm font-body focus:outline-none focus:border-gold-400 focus:shadow-[0_0_0_3px_oklch(0.85_0.12_85/0.15)] transition-all ${
                    confirmTouched && !passwordsMatch
                      ? "border-red-300"
                      : "border-parchment-200"
                  }`}
                  placeholder="Re-enter your password"
                />
                {confirmTouched && !passwordsMatch && (
                  <p className="mt-1 text-xs text-red-500 font-body">
                    Passwords do not match
                  </p>
                )}
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full py-2.5 bg-ink-900 text-parchment-100 rounded-xl text-body-sm font-display font-medium hover:bg-ink-800 transition-colors disabled:opacity-50"
              >
                {loading ? "Updating..." : "Update Password"}
              </button>
            </form>
          )}

          <p className="mt-6 text-center text-body-sm text-ink-500 font-body">
            <Link href="/login" className="text-ink-800 font-medium hover:underline">
              Back to sign in
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
