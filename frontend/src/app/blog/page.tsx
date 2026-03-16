import type { Metadata } from "next";
import BlogClient from "./BlogClient";

export const metadata: Metadata = {
  title: "Blog - Rexearch",
  description:
    "Insights on medical research methodology, biostatistics, and AI-assisted study planning.",
};

export default function BlogPage() {
  return <BlogClient />;
}
