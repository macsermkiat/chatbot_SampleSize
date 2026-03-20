"use server";

import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";
import { createClient } from "@/lib/supabase/server";
import { isPasswordStrong } from "@/lib/password-validation";

function getFormString(formData: FormData, key: string): string | null {
  const value = formData.get(key);
  return typeof value === "string" ? value : null;
}

export async function login(formData: FormData) {
  const supabase = await createClient();
  if (!supabase) {
    redirect("/login?error=Authentication+service+not+configured");
  }

  const email = getFormString(formData, "email");
  const password = getFormString(formData, "password");
  if (!email || !password) {
    redirect("/login?error=Email+and+password+are+required");
  }

  const { error } = await supabase.auth.signInWithPassword({
    email,
    password,
  });

  if (error) {
    redirect("/login?error=Invalid+email+or+password");
  }

  revalidatePath("/", "layout");
  redirect("/app");
}

export async function signup(formData: FormData) {
  const supabase = await createClient();
  if (!supabase) {
    redirect("/login?error=Authentication+service+not+configured");
  }

  const email = getFormString(formData, "email");
  const password = getFormString(formData, "password");
  if (!email || !password) {
    redirect("/login?error=Email+and+password+are+required");
  }

  if (!isPasswordStrong(password)) {
    redirect("/login?error=Password+does+not+meet+requirements");
  }

  const { error } = await supabase.auth.signUp({
    email,
    password,
  });

  if (error) {
    redirect(`/login?error=${encodeURIComponent(error.message)}`);
  }

  revalidatePath("/", "layout");
  redirect("/login?message=Check+your+email+to+confirm+your+account");
}

export async function resetPassword(formData: FormData) {
  const supabase = await createClient();
  if (!supabase) {
    redirect("/login?error=Authentication+service+not+configured");
  }

  const email = getFormString(formData, "email");
  if (!email) {
    redirect("/login?error=Email+is+required");
  }

  const { error } = await supabase.auth.resetPasswordForEmail(email, {
    redirectTo: `${process.env.NEXT_PUBLIC_SITE_URL || "http://localhost:3000"}/auth/callback?next=/auth/reset-password`,
  });

  if (error) {
    redirect(`/login?error=${encodeURIComponent(error.message)}`);
  }

  redirect("/login?message=Check+your+email+for+a+password+reset+link");
}

export async function signOut() {
  const supabase = await createClient();
  if (supabase) {
    await supabase.auth.signOut();
  }
  revalidatePath("/", "layout");
  redirect("/login");
}
