"use client";

import { useState, useEffect, useRef } from "react";
import { createClient } from "@/lib/supabase/client";
import type { User } from "@supabase/supabase-js";

export default function UserMenu() {
  const [user, setUser] = useState<User | null>(null);
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const supabase = createClient();
    supabase.auth.getUser().then(({ data }) => setUser(data.user));

    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, session) => {
      setUser(session?.user ?? null);
    });

    return () => subscription.unsubscribe();
  }, []);

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  if (!user) return null;

  const initials = (user.email ?? "U")
    .split("@")[0]
    .slice(0, 2)
    .toUpperCase();

  async function handleSignOut() {
    const supabase = createClient();
    await supabase.auth.signOut();
    window.location.href = "/login";
  }

  return (
    <div ref={ref} className="relative">
      <button
        onClick={() => setOpen(!open)}
        className="w-8 h-8 rounded-full bg-parchment-700 text-white text-xs font-medium flex items-center justify-center hover:bg-parchment-800 transition-colors"
        title={user.email ?? "Account"}
      >
        {initials}
      </button>

      {open && (
        <div className="absolute right-0 mt-2 w-56 bg-white border border-parchment-200 rounded-lg shadow-lg py-1 z-50">
          <div className="px-4 py-2 border-b border-parchment-100">
            <p className="text-sm font-medium text-parchment-800 truncate">
              {user.email}
            </p>
          </div>
          <a
            href="/account"
            className="block px-4 py-2 text-sm text-parchment-700 hover:bg-parchment-50"
          >
            Account & Billing
          </a>
          <a
            href="/pricing"
            className="block px-4 py-2 text-sm text-parchment-700 hover:bg-parchment-50"
          >
            Pricing
          </a>
          <button
            onClick={handleSignOut}
            className="w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-red-50"
          >
            Sign Out
          </button>
        </div>
      )}
    </div>
  );
}
