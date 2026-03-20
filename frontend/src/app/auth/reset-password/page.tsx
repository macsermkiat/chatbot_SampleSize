import type { Metadata } from "next";
import ResetPasswordClient from "./ResetPasswordClient";

export const metadata: Metadata = {
  title: "Reset Password | Protocol",
  description: "Set a new password for your Protocol account.",
};

export default function ResetPasswordPage() {
  return <ResetPasswordClient />;
}
