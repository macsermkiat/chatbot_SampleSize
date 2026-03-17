import type { Metadata } from "next";
import LoginClient from "./LoginClient";

export const metadata: Metadata = {
  title: "Sign In - ProtoCol",
  description: "Sign in to ProtoCol",
};

export default function LoginPage() {
  return <LoginClient />;
}
