"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import Image from "next/image";
import Link from "next/link";
import { createClient } from "@/lib/supabase/client";
import type { User } from "@supabase/supabase-js";
import ProjectCard from "@/components/ProjectCard";
import UserMenu from "@/components/UserMenu";
import {
  getProjects,
  getUsage,
  deleteProject,
  type ProjectListItem,
} from "@/lib/api";

function useDebounce(value: string, delay: number): string {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const timer = setTimeout(() => setDebounced(value), delay);
    return () => clearTimeout(timer);
  }, [value, delay]);
  return debounced;
}

export default function ProjectsClient() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [authChecked, setAuthChecked] = useState(false);
  const [projects, setProjects] = useState<ProjectListItem[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const debouncedSearch = useDebounce(search, 300);
  const [error, setError] = useState<string | null>(null);
  const [canCreateProject, setCanCreateProject] = useState(true);
  const [projectCount, setProjectCount] = useState(0);
  const [projectLimit, setProjectLimit] = useState<number | null>(1);
  const fetchedRef = useRef(false);

  // Auth check
  useEffect(() => {
    const supabase = createClient();
    supabase.auth.getUser().then(({ data }) => {
      setUser(data.user);
      setAuthChecked(true);
      if (!data.user) {
        router.replace("/login");
      }
    });
  }, [router]);

  // Fetch projects and usage info
  const fetchProjects = useCallback(
    async (q?: string) => {
      if (!user) return;
      setLoading(true);
      setError(null);
      try {
        const [result, usageResult] = await Promise.allSettled([
          getProjects(q || undefined),
          getUsage(),
        ]);
        if (usageResult.status === "fulfilled") {
          const usage = usageResult.value;
          setCanCreateProject(usage.can_create_project);
          setProjectCount(usage.project_count);
          setProjectLimit(usage.project_limit);
        }
        if (result.status === "fulfilled") {
          setProjects(result.value.items);
          setTotal(result.value.total);
        } else {
          throw result.reason;
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load projects");
      } finally {
        setLoading(false);
      }
    },
    [user],
  );

  useEffect(() => {
    if (user && !fetchedRef.current) {
      fetchedRef.current = true;
      fetchProjects();
    }
  }, [user, fetchProjects]);

  // Re-fetch when search changes
  useEffect(() => {
    if (user && fetchedRef.current) {
      fetchProjects(debouncedSearch);
    }
  }, [debouncedSearch, user, fetchProjects]);

  const handleResume = useCallback(
    (sessionId: string) => {
      router.push(`/app?session=${sessionId}`);
    },
    [router],
  );

  const handleDelete = useCallback(
    async (sessionId: string) => {
      const confirmed = window.confirm(
        "Are you sure you want to delete this project? This cannot be undone.",
      );
      if (!confirmed) return;
      try {
        await deleteProject(sessionId);
        setProjects((prev) => prev.filter((p) => p.session_id !== sessionId));
        setTotal((prev) => prev - 1);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to delete project");
      }
    },
    [],
  );

  if (!authChecked) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <p className="text-ink-500 font-display">Loading...</p>
      </div>
    );
  }

  if (!user) return null;

  return (
    <div className="flex flex-col min-h-screen bg-parchment-50">
      {/* Header */}
      <header className="border-b border-parchment-200 bg-parchment-100/80 backdrop-blur-sm">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link href="/" className="flex items-center gap-2 hover:opacity-80 transition-opacity">
              <Image src="/logo_protocol.png" alt="Protocol" width={28} height={28} className="h-7 w-auto" />
              <span className="font-display text-body-md font-semibold text-ink-900 tracking-tight">Protocol</span>
            </Link>
            <span className="text-ink-300">/</span>
            <h1 className="font-display text-body-lg font-medium text-ink-700">
              My Projects
            </h1>
          </div>
          <div className="flex items-center gap-3">
            {canCreateProject ? (
              <Link
                href="/app"
                className="
                  text-caption font-display px-3 py-1.5 rounded-full
                  border border-gold-300 bg-gold-50
                  text-gold-700 hover:bg-gold-100
                  transition-all duration-200
                "
              >
                New Research
              </Link>
            ) : (
              <span
                title="Project limit reached. Upgrade your plan to create more."
                className="
                  text-caption font-display px-3 py-1.5 rounded-full
                  border border-parchment-300 bg-parchment-100
                  text-ink-400 cursor-not-allowed
                "
              >
                New Research
              </span>
            )}
            <UserMenu />
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="flex-1 max-w-4xl mx-auto px-4 sm:px-6 py-6 sm:py-8 w-full">
        {/* Search bar */}
        <div className="mb-6">
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search projects..."
            className="
              w-full px-4 py-2.5 rounded-xl
              bg-white border border-parchment-200
              text-body-md text-ink-800
              placeholder:text-ink-400
              focus:outline-none focus:border-gold-400
              focus:shadow-[0_0_0_3px_oklch(0.85_0.12_85/0.15)]
              transition-all duration-200
              font-body
            "
          />
        </div>

        {/* Project limit indicator */}
        {!loading && (
          <div className="mb-4 flex items-center justify-between">
            <p className="text-caption text-ink-500 font-display">
              {projectLimit === null
                ? `${projectCount} projects`
                : `${projectCount} / ${projectLimit} projects`}
            </p>
            {!canCreateProject && (
              <Link
                href="/account"
                className="text-caption text-gold-700 hover:text-gold-800 font-display underline"
              >
                Upgrade plan
              </Link>
            )}
          </div>
        )}

        {/* Error state */}
        {error && (
          <div className="mb-4 px-4 py-3 rounded-xl bg-red-50 border border-red-200 text-red-700 text-body-sm">
            {error}
          </div>
        )}

        {/* Loading state */}
        {loading && (
          <div className="flex items-center justify-center py-16">
            <p className="text-ink-500 font-display">Loading projects...</p>
          </div>
        )}

        {/* Empty state */}
        {!loading && projects.length === 0 && (
          <div className="flex flex-col items-center justify-center py-16 text-center">
            <svg
              className="w-12 h-12 text-ink-300 mb-4"
              viewBox="0 0 48 48"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.5"
            >
              <rect x="6" y="10" width="36" height="28" rx="3" />
              <line x1="6" y1="18" x2="42" y2="18" />
              <line x1="14" y1="10" x2="14" y2="18" />
            </svg>
            <p className="text-body-lg text-ink-600 font-display mb-2">
              No research projects yet
            </p>
            <p className="text-body-sm text-ink-400 font-body mb-6">
              Start a new conversation to begin your research.
            </p>
            {canCreateProject ? (
              <Link
                href="/app"
                className="
                  px-4 py-2 rounded-xl
                  bg-ink-900 text-parchment-100
                  hover:bg-ink-800
                  transition-colors duration-200
                  font-display text-body-sm
                "
              >
                Start New Research
              </Link>
            ) : (
              <Link
                href="/account"
                className="
                  px-4 py-2 rounded-xl
                  bg-gold-600 text-white
                  hover:bg-gold-700
                  transition-colors duration-200
                  font-display text-body-sm
                "
              >
                Upgrade to Create More Projects
              </Link>
            )}
          </div>
        )}

        {/* Project list */}
        {!loading && projects.length > 0 && (
          <div className="space-y-3">
            {projects.map((project) => (
              <ProjectCard
                key={project.session_id}
                project={project}
                onResume={handleResume}
                onDelete={handleDelete}
                onUpdated={() => fetchProjects(debouncedSearch)}
              />
            ))}

            {total > projects.length && (
              <p className="text-center text-caption text-ink-400 font-display pt-4">
                Showing {projects.length} of {total} projects
              </p>
            )}
          </div>
        )}
      </main>
    </div>
  );
}
