/**
 * KnowledgeBase — browse the curated resources Moufida draws on (analysis §23).
 * Reads the new `/kb/resources` endpoint (disk-backed, taxonomy included) and
 * lets the founder filter by stage / type / sector and read each resource inline.
 */
import { useEffect, useMemo, useState } from "react";
import { useT } from "../../i18n";
import { getKbResources, getProjectDocuments } from "../../api";
import type { KbResource, ProjectDocument } from "../../api";
import { useStore } from "../../store";
import { C, F, card, btn } from "../../theme";
import { PageHeader } from "../shared/PageHeader";
import { IconBook, IconFiles, IconDoc, IconLink, IconChevron } from "../shared/icons";

async function openUrl(url: string) {
  try {
    const { invoke } = await import("@tauri-apps/api/core");
    await invoke("open_url", { url });
  } catch { window.open(url, "_blank", "noopener"); }
}

function uniq(values: (string | null)[]): string[] {
  return [...new Set(values.filter((v): v is string => !!v))].sort();
}

function FilterRow({ label, options, value, onChange }: {
  label: string; options: string[]; value: string; onChange: (v: string) => void;
}) {
  const t = useT();
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap" }}>
      <span style={{ fontSize: 11, color: C.muted, textTransform: "uppercase", letterSpacing: 1, minWidth: 56 }}>
        {label}
      </span>
      <button onClick={() => onChange("")} style={{ ...btn(value === ""), fontSize: 12 }}>{t("kb_all")}</button>
      {options.map((o) => (
        <button key={o} onClick={() => onChange(o)} style={{ ...btn(value === o), fontSize: 12 }}>
          {o.replace(/[-_]/g, " ")}
        </button>
      ))}
    </div>
  );
}

function ResourceCard({ r }: { r: KbResource }) {
  const t = useT();
  const [open, setOpen] = useState(false);
  return (
    <div style={{ ...card, padding: 16 }} className="mf-card-hover">
      <div style={{ display: "flex", alignItems: "baseline", gap: 8, marginBottom: 4 }}>
        <h3 style={{ margin: 0, flex: 1, color: C.text, fontFamily: F.heading, fontSize: 15 }}>{r.title}</h3>
        {r.type && (
          <span style={{ fontSize: 10, color: C.accent, background: `${C.accent}14`, borderRadius: 20, padding: "2px 8px", whiteSpace: "nowrap" }}>
            {r.type.replace(/[-_]/g, " ")}
          </span>
        )}
      </div>
      {r.provider && <p style={{ margin: "0 0 6px", fontSize: 12, color: C.muted, fontFamily: F.body }}>{r.provider}</p>}
      <p style={{ margin: "0 0 8px", fontSize: 13, color: C.text, lineHeight: 1.55, fontFamily: F.body }}>
        {open ? r.body : r.summary}
      </p>
      <div style={{ display: "flex", alignItems: "center", gap: 10, flexWrap: "wrap" }}>
        {r.body && r.body !== r.summary && (
          <button onClick={() => setOpen((o) => !o)} className="mf-press" style={{ ...btn(false), fontSize: 12, display: "inline-flex", alignItems: "center", gap: 6 }}>
            <IconChevron open={open} size={13} /> {t("kb_read_more")}
          </button>
        )}
        {r.url && (
          <a href={r.url} onClick={(e) => { e.preventDefault(); void openUrl(r.url!); }}
            style={{ color: C.accent, fontSize: 12, textDecoration: "none", cursor: "pointer", display: "inline-flex", alignItems: "center", gap: 5 }}>
            <IconLink size={13} /> {t("kb_open_source")}
          </a>
        )}
        {(r.stage ?? []).map((s) => (
          <span key={s} style={{ fontSize: 10, color: C.muted, border: `1px solid ${C.border}`, borderRadius: 4, padding: "1px 6px" }}>{s.replace(/_/g, " ")}</span>
        ))}
        {r.last_verified && (
          <span style={{ fontSize: 11, color: C.muted, marginLeft: "auto" }}>
            {t("kb_verified")}: {r.last_verified}
          </span>
        )}
      </div>
    </div>
  );
}

/**
 * UploadedDocs — the founder's own documents (PDFs dropped on Moufida, file
 * uploads). Re-fetches whenever `kbRefreshNonce` bumps so a freshly ingested PDF
 * appears without a manual reload.
 */
function UploadedDocs() {
  const t = useT();
  const projectId = useStore((s) => s.projectId);
  const refreshNonce = useStore((s) => s.kbRefreshNonce);
  const [docs, setDocs] = useState<ProjectDocument[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!projectId) { setDocs([]); setLoading(false); return; }
    let cancelled = false;
    setLoading(true);
    getProjectDocuments(projectId)
      .then((r) => { if (!cancelled) setDocs(r.documents); })
      .catch(() => { if (!cancelled) setDocs([]); })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [projectId, refreshNonce]);

  if (!projectId) return null;

  return (
    <div style={{ ...card, display: "flex", flexDirection: "column", gap: 10 }}>
      <div>
        <h3 style={{ margin: 0, color: C.text, fontFamily: F.heading, fontSize: 15, display: "flex", alignItems: "center", gap: 8 }}>
          <span style={{ color: C.accent }}><IconFiles size={16} /></span> {t("kb_uploaded_title")}
        </h3>
        <p style={{ margin: "4px 0 0", fontSize: 12, color: C.muted, fontFamily: F.body }}>
          {t("kb_uploaded_hint")}
        </p>
      </div>
      {loading ? (
        <div style={{ height: 36 }} className="mf-skeleton" />
      ) : docs.length === 0 ? (
        <p style={{ margin: 0, fontSize: 13, color: C.muted }}>{t("kb_uploaded_empty")}</p>
      ) : (
        <ul style={{ margin: 0, padding: 0, listStyle: "none", display: "flex", flexDirection: "column", gap: 6 }}>
          {docs.map((d) => (
            <li key={d.id} style={{
              display: "flex", alignItems: "baseline", gap: 8,
              fontSize: 13, color: C.text, fontFamily: F.body,
              borderBottom: `1px solid ${C.border}`, paddingBottom: 6,
            }}>
              <span style={{ flex: 1, display: "inline-flex", alignItems: "center", gap: 7 }}>
                <span style={{ color: C.muted, flexShrink: 0 }}><IconDoc size={14} /></span>
                {d.title || "document"}
              </span>
              <span style={{ fontSize: 11, color: C.muted, whiteSpace: "nowrap" }}>
                {d.char_count.toLocaleString()} {t("kb_chars")}
              </span>
              {d.created_at && (
                <span style={{ fontSize: 11, color: C.muted, whiteSpace: "nowrap" }}>
                  {new Date(d.created_at).toLocaleDateString()}
                </span>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export function KnowledgeBase() {
  const t = useT();
  const [resources, setResources] = useState<KbResource[]>([]);
  const [loading, setLoading] = useState(true);
  const [stage, setStage] = useState("");
  const [type, setType] = useState("");
  const [sector, setSector] = useState("");

  useEffect(() => {
    let cancelled = false;
    getKbResources()
      .then((r) => { if (!cancelled) setResources(r.resources); })
      .catch(() => { if (!cancelled) setResources([]); })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, []);

  const stages  = useMemo(() => uniq(resources.flatMap((r) => r.stage ?? [])),  [resources]);
  const types   = useMemo(() => uniq(resources.map((r) => r.type)),             [resources]);
  const sectors = useMemo(() => uniq(resources.flatMap((r) => r.sector ?? [])), [resources]);

  const filtered = resources.filter((r) =>
    (!stage  || (r.stage ?? []).includes(stage)) &&
    (!type   || r.type === type) &&
    (!sector || (r.sector ?? []).includes(sector)));

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
      <PageHeader title={t("nav_kb")} subtitle={t("kb_subtitle")} icon={<IconBook size={22} />} />

      <UploadedDocs />

      <div style={{ ...card, display: "flex", flexDirection: "column", gap: 10 }}>
        <FilterRow label={t("kb_filter_stage")}  options={stages}  value={stage}  onChange={setStage} />
        <FilterRow label={t("kb_filter_type")}   options={types}   value={type}   onChange={setType} />
        <FilterRow label={t("kb_filter_sector")} options={sectors} value={sector} onChange={setSector} />
        <p style={{ margin: 0, fontSize: 12, color: C.muted }}>{filtered.length} {t("kb_count")}</p>
      </div>

      {loading ? (
        <div style={{ ...card }} className="mf-skeleton" />
      ) : filtered.length === 0 ? (
        <p style={{ color: C.muted, fontSize: 13 }}>{t("kb_none")}</p>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          {filtered.map((r) => <ResourceCard key={r.id} r={r} />)}
        </div>
      )}
    </div>
  );
}
