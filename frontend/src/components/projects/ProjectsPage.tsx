/**
 * ProjectsPage — the founder's project portfolio (reachable any time from the
 * sidebar, not just the landing screen). Lists projects with explicit Open /
 * Diagnose / Update-profile actions, daemon-focus toggle, delete, JSON import,
 * and a "new project" entry. Navigation is delegated to the parent so App stays
 * the single router.
 */
import { useEffect, useRef, useState } from "react";
import type React from "react";
import { useStore } from "../../store";
import { useT } from "../../i18n";
import {
  createProject, deleteProject, getDaemonControl, getRecentProjects,
  patchProfile, setDaemonFocus,
} from "../../api";
import { C, F, T, card, btn, setAccent } from "../../theme";
import { SkeletonCard } from "../shared/SkeletonCard";
import { IconBolt, IconEdit, IconEye, IconTrash } from "../shared/icons";
import type { Project } from "../../types";

interface Props {
  onOpen: (id: string) => void;
  onDiagnose: (id: string) => void;
  onUpdateProfile: (id: string) => void;
  onNewProject: () => void;
}

export function ProjectsPage({ onOpen, onDiagnose, onUpdateProfile, onNewProject }: Props) {
  const t = useT();
  const lang = useStore((s) => s.lang);
  const daemonFocusProjectId = useStore((s) => s.daemonFocusProjectId);
  const applyDaemonStatus    = useStore((s) => s.applyDaemonStatus);
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading]   = useState(true);
  const [importErr, setImportErr] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [confirmingId, setConfirmingId] = useState<string | null>(null);
  const [focusingId, setFocusingId] = useState<string | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  const reload = () => {
    setLoading(true);
    getRecentProjects()
      .then((r) => setProjects(r.projects))
      .catch(() => setProjects([]))
      .finally(() => setLoading(false));
  };

  useEffect(() => { reload(); }, []);
  useEffect(() => { getDaemonControl().then(applyDaemonStatus).catch(() => {}); }, [applyDaemonStatus]);

  const handleFocus = async (e: React.MouseEvent, projectId: string) => {
    e.stopPropagation();
    const next = daemonFocusProjectId === projectId ? null : projectId;
    setFocusingId(projectId);
    try {
      applyDaemonStatus(await setDaemonFocus(next));
    } catch (err) {
      console.warn("[daemon-focus]", err);
    } finally {
      setFocusingId(null);
    }
  };

  const handleFile = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setImportErr(null);
    try {
      const parsed = JSON.parse(await file.text()) as Record<string, unknown>;
      const profile = (parsed.profile && typeof parsed.profile === "object" ? parsed.profile : parsed) as Record<string, unknown>;
      const sector =
        typeof parsed.sector === "string" ? parsed.sector
        : typeof profile.sector === "string" ? profile.sector
        : "cross-sector";
      const { project_id } = await createProject(sector, lang);
      await patchProfile(project_id, profile);
      onOpen(project_id);
    } catch (err) {
      setImportErr(err instanceof Error ? err.message : String(err));
    } finally {
      if (fileRef.current) fileRef.current.value = "";
    }
  };

  const handleDelete = async (e: React.MouseEvent, projectId: string) => {
    e.stopPropagation();
    setConfirmingId(null);
    setDeletingId(projectId);
    try {
      await deleteProject(projectId);
      reload();
    } catch (err) {
      console.warn("[delete-project]", err);
    } finally {
      setDeletingId(null);
    }
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
      <div style={{ display: "flex", alignItems: "flex-end", gap: 12, flexWrap: "wrap" }}>
        <div style={{ flex: 1, minWidth: 220 }}>
          <p style={{ ...T.eyebrow, color: C.accent, margin: "0 0 4px" }}>{t("tagline_short")}</p>
          <h2 style={{ ...T.h1, margin: 0, color: C.ink }}>{t("nav_projects")}</h2>
          <p style={{ ...T.small, margin: "6px 0 0", color: C.muted }}>{t("projects_subtitle")}</p>
        </div>
        <input ref={fileRef} type="file" accept="application/json,.json"
          onChange={(e) => { void handleFile(e); }} style={{ display: "none" }} />
        <button onClick={() => fileRef.current?.click()} className="mf-btn-ghost">
          {t("import_project")}
        </button>
        <button onClick={onNewProject} className="mf-btn-accent">
          ＋ {t("projects_new")}
        </button>
      </div>

      {importErr && <p style={{ color: C.error, fontSize: 12, margin: 0 }}>{t("import_error")}: {importErr}</p>}
      {loading && (
        <div style={{ display: "flex", flexDirection: "column", gap: 10 }} aria-busy="true">
          {Array.from({ length: 3 }).map((_, i) => (
            <SkeletonCard key={i} rows={1} title />
          ))}
        </div>
      )}

      {!loading && projects.length === 0 && (
        <div style={{ ...card, textAlign: "center", padding: "28px 24px" }}>
          <p style={{ color: C.muted, fontSize: 14, margin: 0, fontFamily: F.body }}>{t("landing_no_recent")}</p>
        </div>
      )}

      <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
        {projects.map((p) => {
          const focused = daemonFocusProjectId === p.project_id;
          return (
            <div key={p.project_id} className="mf-card-hover" style={{
              ...card, padding: "14px 18px",
              display: "flex", alignItems: "center", gap: 12, flexWrap: "wrap",
            }}>
              <div style={{ flex: 1, minWidth: 180 }}>
                <p style={{ margin: 0, fontSize: 15, color: C.text, fontFamily: F.body, fontWeight: 600 }}>
                  {p.name ?? p.sector}
                </p>
                <div style={{ display: "flex", alignItems: "center", gap: 8, marginTop: 4 }}>
                  <span style={{ fontSize: 12, color: C.muted, fontFamily: F.body }}>
                    {new Date(p.created_at).toLocaleDateString()}
                  </span>
                  <span style={{
                    background: p.mode === "creation" ? `${C.accent}22` : `${C.success}22`,
                    color: p.mode === "creation" ? C.accent : C.success,
                    borderRadius: 20, padding: "2px 9px", fontSize: 10, fontWeight: 600,
                  }}>
                    {p.mode === "creation" ? t("mode_creation") : t("mode_diagnosis")}
                  </span>
                  {p.maturity_stage && (
                    <span style={{ background: C.accent, color: "#fff", borderRadius: 20, padding: "2px 9px", fontSize: 10, fontWeight: 600 }}>
                      {p.maturity_stage}
                    </span>
                  )}
                </div>
              </div>

              <div style={{ display: "flex", alignItems: "center", gap: 6, flexWrap: "wrap" }}>
                <button onClick={() => { setAccent(p.sector); onOpen(p.project_id); }} className="mf-press" style={btn(true)}>
                  {t("projects_open")}
                </button>
                <button onClick={() => { setAccent(p.sector); onDiagnose(p.project_id); }} className="mf-press"
                  style={{ ...btn(false), border: `1.5px solid ${C.accent}`, color: C.accent, display: "inline-flex", alignItems: "center", gap: 6 }}>
                  <IconBolt size={13} /> {t("projects_diagnose")}
                </button>
                <button onClick={() => onUpdateProfile(p.project_id)} className="mf-press" style={{ ...btn(false), fontSize: 12, display: "inline-flex", alignItems: "center", gap: 6 }}>
                  <IconEdit size={13} /> {t("projects_update_profile")}
                </button>
                <button onClick={(e) => { void handleFocus(e, p.project_id); }} disabled={focusingId === p.project_id}
                  title={focused ? t("daemon_unfocus") : t("daemon_focus")}
                  className="mf-icon-btn"
                  style={{ background: focused ? `${C.accent}22` : undefined, border: focused ? `1px solid ${C.accent}` : "1px solid transparent",
                    color: focused ? C.accent : C.muted, width: 32, height: 32 }}>
                  {focusingId === p.project_id ? "…" : <IconEye size={16} />}
                </button>
                {deletingId === p.project_id ? (
                  <span style={{ color: C.muted, fontSize: 15, padding: "4px 7px", lineHeight: 1 }}>…</span>
                ) : confirmingId === p.project_id ? (
                  <span style={{ display: "inline-flex", alignItems: "center", gap: 4 }}>
                    <button onClick={(e) => { void handleDelete(e, p.project_id); }}
                      title={t("delete_project_confirm")}
                      style={{ background: `${C.error}1A`, border: `1px solid ${C.error}`, cursor: "pointer",
                        color: C.error, fontSize: 12, fontWeight: 600, fontFamily: F.body,
                        padding: "4px 9px", borderRadius: 6, lineHeight: 1 }}>
                      {t("delete_confirm_yes")}
                    </button>
                    <button onClick={(e) => { e.stopPropagation(); setConfirmingId(null); }}
                      style={{ background: "none", border: "none", cursor: "pointer", color: C.muted,
                        fontSize: 15, padding: "4px 6px", borderRadius: 6, lineHeight: 1 }}>
                      ✕
                    </button>
                  </span>
                ) : (
                  <button onClick={(e) => { e.stopPropagation(); setConfirmingId(p.project_id); }}
                    title={t("delete_project")} className="mf-icon-btn"
                    style={{ color: C.muted, width: 32, height: 32 }}>
                    <IconTrash size={15} />
                  </button>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
