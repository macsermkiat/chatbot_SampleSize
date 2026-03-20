"use client";

import { useSearchParams, useRouter } from "next/navigation";
import { useState, useEffect, Suspense, useMemo } from "react";
import Image from "next/image";
import Link from "next/link";
import { createClient } from "@/lib/supabase/client";
import { PASSWORD_CHECKS } from "@/lib/password-validation";
import { login, signup, resetPassword } from "./actions";

type Mode = "signin" | "signup" | "forgot";

function safeDecode(value: string): string {
  try {
    return decodeURIComponent(value);
  } catch {
    return value;
  }
}

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

function LoginForm() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const error = searchParams.get("error");
  const message = searchParams.get("message");
  const [mode, setMode] = useState<Mode>("signin");
  const [loading, setLoading] = useState(false);
  const [oauthError, setOauthError] = useState<string | null>(null);
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [confirmTouched, setConfirmTouched] = useState(false);
  const [validationError, setValidationError] = useState<string | null>(null);

  const allChecksPassed = useMemo(
    () => PASSWORD_CHECKS.every((check) => check.test(password)),
    [password],
  );

  const passwordsMatch = password === confirmPassword;

  // Reset loading state after server-action redirect lands back with error/message
  useEffect(() => {
    if (error || message) {
      setLoading(false);
    }
  }, [error, message]);

  // Clear URL params and local errors when switching modes
  function switchMode(newMode: Mode) {
    setMode(newMode);
    setPassword("");
    setConfirmPassword("");
    setConfirmTouched(false);
    setValidationError(null);
    setOauthError(null);
    if (error || message) {
      router.replace("/login");
    }
  }

  async function handleGoogleLogin() {
    setLoading(true);
    setOauthError(null);
    try {
      const supabase = createClient();
      const { data, error: oauthErr } = await supabase.auth.signInWithOAuth({
        provider: "google",
        options: {
          redirectTo: `${window.location.origin}/auth/callback`,
        },
      });
      if (oauthErr) {
        setOauthError(oauthErr.message);
        setLoading(false);
      } else if (!data?.url) {
        setOauthError("No redirect URL returned. Check Supabase configuration.");
        setLoading(false);
      } else {
        setTimeout(() => {
          setLoading(false);
          setOauthError("Redirect timed out. Please try again.");
        }, 5000);
      }
    } catch (err) {
      setOauthError(err instanceof Error ? err.message : "Unexpected error");
      setLoading(false);
    }
  }

  function handleSubmit(formData: FormData) {
    setValidationError(null);

    if (mode === "forgot") {
      setLoading(true);
      resetPassword(formData);
      return;
    }

    if (mode === "signup") {
      if (!allChecksPassed) {
        setValidationError("Password does not meet all requirements.");
        return;
      }
      if (!passwordsMatch) {
        setValidationError("Passwords do not match.");
        return;
      }
    }

    setLoading(true);
    if (mode === "signup") {
      signup(formData);
    } else {
      login(formData);
    }
  }

  const heading =
    mode === "forgot"
      ? "Reset Password"
      : mode === "signup"
        ? "Create Account"
        : "Welcome Back";

  const subtitle =
    mode === "forgot"
      ? "Enter your email and we'll send you a reset link"
      : mode === "signup"
        ? "Get started for free"
        : "Sign in to continue your research";

  const cardBorderClass =
    mode === "signup"
      ? "border-gold-300"
      : "border-parchment-200";

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
        <div className={`bg-parchment-50/80 border ${cardBorderClass} rounded-xl p-6 sm:p-8 shadow-sm transition-colors`}>
          <div className="text-center mb-6">
            <h2 className="font-display text-display-md font-semibold text-ink-800">
              {heading}
            </h2>
            <p className="text-body-sm text-ink-400 font-body mt-1">
              {subtitle}
            </p>
          </div>

          {error && (
            <div role="alert" className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
              {safeDecode(error)}
            </div>
          )}

          {message && (
            <div role="status" className="mb-4 p-3 bg-green-50 border border-green-200 rounded-lg text-green-700 text-sm">
              {safeDecode(message)}
            </div>
          )}

          {oauthError && (
            <div role="alert" className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
              {oauthError}
            </div>
          )}

          {validationError && (
            <div role="alert" className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
              {validationError}
            </div>
          )}

          {/* Google OAuth — only on signin/signup */}
          {mode !== "forgot" && (
            <>
              <button
                onClick={handleGoogleLogin}
                disabled={loading}
                className="w-full flex items-center justify-center gap-3 px-4 py-2.5 border border-parchment-200 rounded-xl bg-white hover:bg-parchment-50 transition-colors text-body-sm font-body font-medium text-ink-700 disabled:opacity-50"
              >
                <svg className="w-5 h-5" viewBox="0 0 24 24">
                  <path
                    d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 01-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z"
                    fill="#4285F4"
                  />
                  <path
                    d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                    fill="#34A853"
                  />
                  <path
                    d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                    fill="#FBBC05"
                  />
                  <path
                    d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                    fill="#EA4335"
                  />
                </svg>
                Continue with Google
              </button>

              <div className="flex items-center my-6">
                <div className="flex-1 border-t border-parchment-200" />
                <span className="px-4 text-xs text-parchment-500 uppercase tracking-wider">
                  or
                </span>
                <div className="flex-1 border-t border-parchment-200" />
              </div>
            </>
          )}

          {/* Form */}
          <form action={handleSubmit} className="space-y-4">
            <div>
              <label
                htmlFor="email"
                className="block text-body-sm font-body font-medium text-ink-700 mb-1"
              >
                Email
              </label>
              <input
                id="email"
                name="email"
                type="email"
                required
                className="w-full px-3 py-2.5 border border-parchment-200 rounded-xl bg-white text-ink-900 text-body-sm font-body focus:outline-none focus:border-gold-400 focus:shadow-[0_0_0_3px_oklch(0.85_0.12_85/0.15)] transition-all"
                placeholder="you@institution.edu"
              />
            </div>

            {/* Password field — signin and signup only */}
            {mode !== "forgot" && (
              <div>
                <div className="flex items-center justify-between mb-1">
                  <label
                    htmlFor="password"
                    className="block text-body-sm font-body font-medium text-ink-700"
                  >
                    Password
                  </label>
                  {mode === "signin" && (
                    <button
                      type="button"
                      onClick={() => switchMode("forgot")}
                      className="text-xs text-ink-500 hover:text-ink-700 font-body hover:underline"
                    >
                      Forgot password?
                    </button>
                  )}
                </div>
                <input
                  id="password"
                  name="password"
                  type="password"
                  required
                  minLength={mode === "signup" ? 8 : 6}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full px-3 py-2.5 border border-parchment-200 rounded-xl bg-white text-ink-900 text-body-sm font-body focus:outline-none focus:border-gold-400 focus:shadow-[0_0_0_3px_oklch(0.85_0.12_85/0.15)] transition-all"
                  placeholder={mode === "signup" ? "Min 8 characters" : ""}
                />
                {mode === "signup" && <PasswordStrength password={password} />}
              </div>
            )}

            {/* Confirm password — signup only */}
            {mode === "signup" && (
              <div>
                <label
                  htmlFor="confirmPassword"
                  className="block text-body-sm font-body font-medium text-ink-700 mb-1"
                >
                  Confirm Password
                </label>
                <input
                  id="confirmPassword"
                  name="confirmPassword"
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
            )}

            <button
              type="submit"
              disabled={loading}
              className={`w-full py-2.5 rounded-xl text-body-sm font-display font-medium transition-colors disabled:opacity-50 ${
                mode === "signup"
                  ? "bg-gold-600 text-white hover:bg-gold-700"
                  : "bg-ink-900 text-parchment-100 hover:bg-ink-800"
              }`}
            >
              {loading
                ? "Please wait..."
                : mode === "forgot"
                  ? "Send Reset Link"
                  : mode === "signup"
                    ? "Create Account"
                    : "Sign In"}
            </button>
          </form>

          {/* Mode toggles */}
          <div className="mt-6 text-center space-y-2">
            {mode === "forgot" ? (
              <p className="text-body-sm text-ink-500 font-body">
                Remember your password?{" "}
                <button
                  onClick={() => switchMode("signin")}
                  className="text-ink-800 font-medium hover:underline"
                >
                  Sign in
                </button>
              </p>
            ) : (
              <p className="text-body-sm text-ink-500 font-body">
                {mode === "signup" ? "Already have an account?" : "Don't have an account?"}{" "}
                <button
                  onClick={() => switchMode(mode === "signup" ? "signin" : "signup")}
                  className="text-ink-800 font-medium hover:underline"
                >
                  {mode === "signup" ? "Sign in" : "Create one"}
                </button>
              </p>
            )}
          </div>
        </div>

        {/* Footer */}
        <p className="mt-6 text-center text-caption text-ink-400 font-display">
          By continuing, you agree to our terms of service.
        </p>
      </div>
    </div>
  );
}

export default function LoginClient() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen bg-parchment-100 flex items-center justify-center">
          <p className="text-parchment-600">Loading...</p>
        </div>
      }
    >
      <LoginForm />
    </Suspense>
  );
}
