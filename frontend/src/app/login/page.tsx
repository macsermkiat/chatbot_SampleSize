import type { Metadata } from "next";
import LoginClient from "./LoginClient";

export const metadata: Metadata = {
  title: "Sign In - Rexearch",
  description: "Sign in to Rexearch",
};

export default function LoginPage() {
  return <LoginClient />;
}
