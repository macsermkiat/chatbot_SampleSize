import type { Metadata } from "next";
import LoginClient from "./LoginClient";

export const metadata: Metadata = {
  title: "Sign In - Research Assistant",
  description: "Sign in to DAB Research Assistant",
};

export default function LoginPage() {
  return <LoginClient />;
}
