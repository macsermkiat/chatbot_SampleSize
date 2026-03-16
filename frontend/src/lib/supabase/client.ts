import { createBrowserClient } from "@supabase/ssr";

const SUPABASE_URL = process.env.NEXT_PUBLIC_SUPABASE_URL ?? "";
const SUPABASE_ANON_KEY = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY ?? "";

// Use a placeholder URL when env vars are missing so createBrowserClient
// doesn't throw during initialization. The middleware already skips auth
// when Supabase is not configured, so API calls will simply return
// unauthenticated results.
const PLACEHOLDER_URL = "https://placeholder.supabase.co";
const PLACEHOLDER_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.placeholder";

export function createClient() {
  return createBrowserClient(
    SUPABASE_URL || PLACEHOLDER_URL,
    SUPABASE_ANON_KEY || PLACEHOLDER_KEY,
  );
}
