import type { Metadata } from "next";
import ProjectsClient from "./ProjectsClient";

export const metadata: Metadata = {
  title: "My Projects - ProtoCol",
  description:
    "View, search, and resume your saved research sessions.",
};

export default function ProjectsPage() {
  return <ProjectsClient />;
}
