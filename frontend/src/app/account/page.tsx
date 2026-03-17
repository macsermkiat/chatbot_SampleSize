import type { Metadata } from "next";
import AccountClient from "./AccountClient";

export const metadata: Metadata = {
  title: "Account & Billing - ProtoCol",
  description: "Manage your subscription, usage, and account settings.",
};

export default function AccountPage() {
  return <AccountClient />;
}
