"use client";

import { useCallback, useRef, useState } from "react";
import { updateProject, exportProtocol, type ProjectListItem } from "@/lib/api";

const PHASE_LABELS: Record<string, string> = {
  orchestrator: "Started",
  research_gap: "Research Gap",
  methodology: "Methodology",
  biostatistics: "Biostatistics",
};

interface ProjectCardProps {
  project: ProjectListItem;
  onResume: (sessionId: string) => void;
  onDelete: (sessionId: string) => void;
  onUpdated: () => void;
}

export default function ProjectCard({
  project,
  onResume,
  onDelete,
  onUpdated,
}: ProjectCardProps) {
  const [editing, setEditing] = useState(false);
  const [nameValue, setNameValue] = useState(project.name ?? "");
  const [saving, setSaving] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const displayName = project.name || "Untitled Research";
  const phaseLabel = PHASE_LABELS[project.current_phase] ?? project.current_phase;
  const createdDate = new Date(project.created_at).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });

  const handleSaveName = useCallback(async () => {
    const trimmed = nameValue.trim();
    if (!trimmed || trimmed === project.name) {
      setEditing(false);
      setNameValue(project.name ?? "");
      return;
    }
    setSaving(true);
    try {
      await updateProject(project.session_id, trimmed, project.description);
      setEditing(false);
      onUpdated();
    } catch {
      setNameValue(project.name ?? "");
      setEditing(false);
    } finally {
      setSaving(false);
    }
  }, [nameValue, project, onUpdated]);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === "Enter") {
        e.preventDefault();
        handleSaveName();
      } else if (e.key === "Escape") {
        setEditing(false);
        setNameValue(project.name ?? "");
      }
    },
    [handleSaveName, project.name],
  );

  const handleExport = useCallback(
    async (e: React.MouseEvent) => {
      e.stopPropagation();
      try {
        await exportProtocol(project.session_id);
      } catch (err) {
        alert(err instanceof Error ? err.message : "Export failed. Please try again.");
      }
    },
    [project.session_id],
  );

  return (
    <div className="
      group flex items-start gap-4 p-4 rounded-xl
      bg-white border border-parchment-200
      hover:border-gold-300 hover:shadow-sm
      transition-all duration-200
    ">
      <div className="flex-1 min-w-0">
        {/* Name (editable) */}
        {editing ? (
          <input
            ref={inputRef}
            value={nameValue}
            onChange={(e) => setNameValue(e.target.value)}
            onBlur={handleSaveName}
            onKeyDown={handleKeyDown}
            disabled={saving}
            autoFocus
            maxLength={200}
            className="
              w-full text-body-md font-display font-medium text-ink-900
              bg-parchment-50 border border-gold-300 rounded-lg px-2 py-1
              focus:outline-none focus:border-gold-400
            "
          />
        ) : (
          <button
            onClick={() => {
              setNameValue(project.name ?? "");
              setEditing(true);
            }}
            className="
              text-left text-body-md font-display font-medium text-ink-900
              hover:text-gold-700 transition-colors cursor-text
              truncate block w-full
            "
            title="Click to rename"
          >
            {displayName}
          </button>
        )}

        {/* Metadata row */}
        <div className="flex items-center gap-3 mt-1.5">
          <span className="
            text-caption font-display px-2 py-0.5 rounded-full
            bg-parchment-100 text-ink-500
          ">
            {phaseLabel}
          </span>
          <span className="text-caption text-ink-400 font-body">
            {createdDate}
          </span>
        </div>

        {/* Description preview */}
        {project.description && (
          <p className="mt-2 text-body-sm text-ink-500 font-body line-clamp-2">
            {project.description}
          </p>
        )}
      </div>

      {/* Actions */}
      <div className="flex items-center gap-2 flex-none opacity-0 group-hover:opacity-100 group-focus-within:opacity-100 transition-opacity">
        <button
          onClick={() => onResume(project.session_id)}
          className="
            text-caption font-display px-3 py-1.5 rounded-lg
            bg-ink-900 text-parchment-100
            hover:bg-ink-800
            transition-colors duration-200
          "
        >
          Resume
        </button>
        <button
          onClick={handleExport}
          className="
            text-caption font-display px-3 py-1.5 rounded-lg
            border border-parchment-300
            text-ink-600 hover:text-ink-800 hover:border-parchment-400
            transition-colors duration-200
          "
          title="Export protocol"
        >
          Export
        </button>
        <button
          onClick={(e) => {
            e.stopPropagation();
            onDelete(project.session_id);
          }}
          className="
            text-caption font-display px-2 py-1.5 rounded-lg
            text-red-400 hover:text-red-600 hover:bg-red-50
            transition-colors duration-200
          "
          title="Delete project"
        >
          <svg className="w-4 h-4" viewBox="0 0 16 16" fill="currentColor">
            <path d="M5.5 5.5A.5.5 0 016 6v6a.5.5 0 01-1 0V6a.5.5 0 01.5-.5zm2.5 0a.5.5 0 01.5.5v6a.5.5 0 01-1 0V6a.5.5 0 01.5-.5zm3 .5a.5.5 0 00-1 0v6a.5.5 0 001 0V6z" />
            <path fillRule="evenodd" d="M14.5 3a1 1 0 01-1 1H13v9a2 2 0 01-2 2H5a2 2 0 01-2-2V4h-.5a1 1 0 01-1-1V2a1 1 0 011-1H5a1 1 0 011-1h4a1 1 0 011 1h2.5a1 1 0 011 1v1zM4.118 4L4 4.059V13a1 1 0 001 1h6a1 1 0 001-1V4.059L11.882 4H4.118zM2.5 3V2h11v1h-11z" />
          </svg>
        </button>
      </div>
    </div>
  );
}
