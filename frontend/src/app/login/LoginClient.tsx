"use client";

import { useSearchParams } from "next/navigation";
import { useState, useEffect, Suspense } from "react";
import Link from "next/link";
import { createClient } from "@/lib/supabase/client";
import { login, signup } from "./actions";

function LoginForm() {
  const searchParams = useSearchParams();
  const error = searchParams.get("error");
  const message = searchParams.get("message");
  const [isSignUp, setIsSignUp] = useState(false);
  const [loading, setLoading] = useState(false);

  // Reset loading state after server-action redirect lands back with error/message
  useEffect(() => {
    if (error || message) {
      setLoading(false);
    }
  }, [error, message]);

  async function handleGoogleLogin() {
    setLoading(true);
    const supabase = createClient();
    const { error } = await supabase.auth.signInWithOAuth({
      provider: "google",
      options: {
        redirectTo: `${window.location.origin}/auth/callback`,
      },
    });
    if (error) {
      setLoading(false);
    }
  }

  function handleSubmit(formData: FormData) {
    setLoading(true);
    if (isSignUp) {
      signup(formData);
    } else {
      login(formData);
    }
  }

  return (
    <div className="min-h-screen bg-parchment-100 flex items-center justify-center px-4">
      <div className="w-full max-w-md">
        {/* Header */}
        <div className="text-center mb-8">
          <Link href="/" className="font-display text-display-lg font-semibold text-ink-900 mb-2 inline-block hover:text-gold-700 transition-colors">
            ProtoCol
          </Link>
          <p className="text-body-sm text-ink-500 font-body">
            AI-powered medical research methodology assistant
          </p>
        </div>

        {/* Card */}
        <div className="bg-parchment-50/80 border border-parchment-200 rounded-xl p-6 sm:p-8 shadow-sm">
          <h2 className="font-display text-display-md font-semibold text-ink-800 mb-6 text-center">
            {isSignUp ? "Create Account" : "Sign In"}
          </h2>

          {error && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
              {decodeURIComponent(error)}
            </div>
          )}

          {message && (
            <div className="mb-4 p-3 bg-green-50 border border-green-200 rounded-lg text-green-700 text-sm">
              {decodeURIComponent(message)}
            </div>
          )}

          {/* Google OAuth */}
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

          {/* Email/Password form */}
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

            <div>
              <label
                htmlFor="password"
                className="block text-body-sm font-body font-medium text-ink-700 mb-1"
              >
                Password
              </label>
              <input
                id="password"
                name="password"
                type="password"
                required
                minLength={6}
                className="w-full px-3 py-2.5 border border-parchment-200 rounded-xl bg-white text-ink-900 text-body-sm font-body focus:outline-none focus:border-gold-400 focus:shadow-[0_0_0_3px_oklch(0.85_0.12_85/0.15)] transition-all"
                placeholder={isSignUp ? "Min 6 characters" : ""}
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-2.5 bg-ink-900 text-parchment-100 rounded-xl text-body-sm font-display font-medium hover:bg-ink-800 transition-colors disabled:opacity-50"
            >
              {loading
                ? "Please wait..."
                : isSignUp
                  ? "Create Account"
                  : "Sign In"}
            </button>
          </form>

          {/* Toggle sign in / sign up */}
          <p className="mt-6 text-center text-body-sm text-ink-500 font-body">
            {isSignUp ? "Already have an account?" : "Don't have an account?"}{" "}
            <button
              onClick={() => setIsSignUp(!isSignUp)}
              className="text-ink-800 font-medium hover:underline"
            >
              {isSignUp ? "Sign in" : "Create one"}
            </button>
          </p>
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
