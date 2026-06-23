/**
 * PlanSectionView — axis-aware renderer for plan_section content.
 * Used in both CreationFlow proposal cards and PlanDocument sections.
 */
import type React from "react";
import { createContext, useContext } from "react";
import { C, F } from "../theme";
import { useT } from "../i18n";

// Inline-citation context (§25): renderers turn "[n]" markers in text into
// clickable superscript links to the matching citation. Degrades gracefully —
// if the LLM emits no markers, text renders unchanged.
const CitationsCtx = createContext<Citation[]>([]);

function CitedText({ text }: { text: string }): React.ReactNode {
  const citations = useContext(CitationsCtx);
  if (!citations.length || !/\[\d+\]/.test(text)) return text;
  const parts = text.split(/(\[\d+\])/g);
  return parts.map((part, i) => {
    const m = /^\[(\d+)\]$/.exec(part);
    if (m) {
      const n = parseInt(m[1], 10);
      const c = citations[n - 1];
      if (c && (c.url || c.title)) {
        return (
          <sup key={i}>
            <a
              href={c.url || undefined}
              title={c.title}
              onClick={(e) => { e.preventDefault(); if (c.url) void openUrl(c.url); }}
              style={{ color: C.accent, textDecoration: "none", cursor: c.url ? "pointer" : "default", fontWeight: 700 }}
            >
              [{n}]
            </a>
          </sup>
        );
      }
    }
    return part;
  });
}

interface Props {
  axis: string;
  content: Record<string, unknown>;
}

interface Citation {
  title: string;
  url: string;
  provider?: string;
  source?: string;
}

async function openUrl(url: string) {
  if (!url) return;
  try {
    const { invoke } = await import("@tauri-apps/api/core");
    await invoke("open_url", { url });
  } catch {
    window.open(url, "_blank", "noopener");
  }
}

function asCitations(v: unknown): Citation[] {
  if (!Array.isArray(v)) return [];
  return v
    .filter((c): c is Record<string, unknown> => typeof c === "object" && c !== null)
    .map((c) => ({
      title: String(c.title ?? ""),
      url: String(c.url ?? ""),
      provider: c.provider ? String(c.provider) : "",
      source: c.source ? String(c.source) : "",
    }))
    .filter((c) => c.title || c.url);
}

function Citations({ items }: { items: Citation[] }) {
  const t = useT();
  if (!items.length) return null;
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 6, marginTop: 4 }}>
      <Label>{t("evidence_sources")}</Label>
      <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
        {items.map((c, i) => (
          <div key={i} style={{ display: "flex", alignItems: "baseline", gap: 6, fontSize: 12, fontFamily: F.body }}>
            <span style={{
              fontSize: 10, color: C.muted, border: `1px solid ${C.muted}55`,
              borderRadius: 4, padding: "1px 5px", textTransform: "uppercase", letterSpacing: 0.5,
            }}>
              {c.source === "web" ? t("source_web") : t("source_kb")}
            </span>
            {c.url ? (
              <a
                href={c.url}
                onClick={(e) => { e.preventDefault(); void openUrl(c.url); }}
                style={{ color: C.accent, textDecoration: "none", cursor: "pointer" }}
              >
                {c.title || c.url}
              </a>
            ) : (
              <span style={{ color: C.text }}>{c.title}</span>
            )}
            {c.provider && <span style={{ color: C.muted }}>— {c.provider}</span>}
          </div>
        ))}
      </div>
    </div>
  );
}

// Safe helpers to narrow unknown → typed values for rendering
const str  = (v: unknown): string    => (v != null ? String(v) : "");
const arr  = (v: unknown): unknown[] => (Array.isArray(v) ? v : []);
const recs = (v: unknown): Record<string, unknown>[] =>
  Array.isArray(v)
    ? (v as unknown[]).filter((i): i is Record<string, unknown> => typeof i === "object" && i !== null)
    : [];
const has  = (v: unknown): boolean =>
  v !== null && v !== undefined && v !== "" && !(Array.isArray(v) && v.length === 0);

function Label({ children }: { children: React.ReactNode }) {
  return (
    <p style={{
      margin: "0 0 6px", fontSize: 11, color: C.muted,
      textTransform: "uppercase", letterSpacing: 1, fontFamily: F.body,
    }}>
      {children}
    </p>
  );
}

function TextBlock({ text }: { text: string }) {
  return (
    <p style={{ margin: 0, fontSize: 13, color: C.text, lineHeight: 1.65, fontFamily: F.body }}>
      <CitedText text={text} />
    </p>
  );
}

function BulletList({ items }: { items: unknown[] }) {
  if (!items.length) return null;
  return (
    <ul style={{ margin: 0, paddingLeft: 20 }}>
      {items.map((item, i) => (
        <li key={i} style={{ fontSize: 13, color: C.text, marginBottom: 4, lineHeight: 1.5, fontFamily: F.body }}>
          {typeof item === "string" ? <CitedText text={item} /> : JSON.stringify(item)}
        </li>
      ))}
    </ul>
  );
}

function Chip({ label, value }: { label: string; value: string }) {
  return (
    <span style={{
      display: "inline-flex", alignItems: "center", gap: 4,
      background: `${C.accent}14`, borderRadius: 20,
      padding: "3px 12px", fontSize: 12, color: C.accent,
      fontFamily: F.body, fontWeight: 500,
    }}>
      <span style={{ color: C.muted, fontSize: 11 }}>{label}:</span>
      {value}
    </span>
  );
}

function Sect({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
      <Label>{title}</Label>
      {children}
    </div>
  );
}

// ── Per-axis renderers ──────────────────────────────────────────────────

function IdeationView({ c }: { c: Record<string, unknown> }) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
      {has(c.refined_idea) && (
        <Sect title="Idée raffinée"><TextBlock text={str(c.refined_idea)} /></Sect>
      )}
      {arr(c.unique_value_props).length > 0 && (
        <Sect title="Propositions de valeur uniques">
          <BulletList items={arr(c.unique_value_props)} />
        </Sect>
      )}
      {arr(c.target_personas).length > 0 && (
        <Sect title="Personas cibles">
          <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
            {arr(c.target_personas).map((p, i) => (
              <Chip key={i} label="persona" value={str(p)} />
            ))}
          </div>
        </Sect>
      )}
      {arr(c.risks).length > 0 && (
        <Sect title="Risques identifiés"><BulletList items={arr(c.risks)} /></Sect>
      )}
    </div>
  );
}

function MarketView({ c }: { c: Record<string, unknown> }) {
  const competitors = recs(c.competitors);
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
      {has(c.tam) && <Sect title="TAM"><TextBlock text={str(c.tam)} /></Sect>}
      {has(c.sam) && <Sect title="SAM"><TextBlock text={str(c.sam)} /></Sect>}
      {has(c.som) && <Sect title="SOM"><TextBlock text={str(c.som)} /></Sect>}
      {competitors.length > 0 && (
        <Sect title="Compétiteurs">
          <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
            {competitors.map((comp, i) => (
              <div key={i} style={{
                background: C.surfaceHigh, borderRadius: 8, padding: "8px 12px",
                fontSize: 13, color: C.text, fontFamily: F.body,
              }}>
                <strong>{str(comp.name)}</strong>
                {has(comp.differentiation) && (
                  <span style={{ color: C.muted }}> — {str(comp.differentiation)}</span>
                )}
              </div>
            ))}
          </div>
        </Sect>
      )}
      {arr(c.trends).length > 0 && (
        <Sect title="Tendances marché"><BulletList items={arr(c.trends)} /></Sect>
      )}
    </div>
  );
}

function ProductView({ c }: { c: Record<string, unknown> }) {
  const features = recs(c.mvp_features);
  const stack    = recs(c.tech_stack);
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
      {features.length > 0 && (
        <Sect title="Features MVP">
          <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
            {features.map((f, i) => (
              <div key={i} style={{ background: C.surfaceHigh, borderRadius: 8, padding: "8px 12px" }}>
                <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                  <span style={{
                    fontSize: 10, background: C.accent, color: "#fff",
                    borderRadius: 4, padding: "2px 6px", fontWeight: 700,
                  }}>
                    {str(f.priority || "must").toUpperCase()}
                  </span>
                  <span style={{ fontSize: 13, color: C.text, fontFamily: F.body, fontWeight: 600 }}>
                    {str(f.feature)}
                  </span>
                </div>
                {has(f.rationale) && (
                  <p style={{ margin: "4px 0 0", fontSize: 12, color: C.muted, fontFamily: F.body }}>
                    {str(f.rationale)}
                  </p>
                )}
              </div>
            ))}
          </div>
        </Sect>
      )}
      {stack.length > 0 && (
        <Sect title="Stack technique">
          <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
            {stack.map((s, i) => (
              <Chip key={i} label={str(s.layer)} value={str(s.choice)} />
            ))}
          </div>
        </Sect>
      )}
      {arr(c.user_stories).length > 0 && (
        <Sect title="User stories">
          <BulletList items={arr(c.user_stories).slice(0, 3)} />
        </Sect>
      )}
    </div>
  );
}

function BrandView({ c }: { c: Record<string, unknown> }) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
      {has(c.brand_name)     && <Sect title="Nom de marque"><TextBlock text={str(c.brand_name)} /></Sect>}
      {has(c.brand_voice)    && <Sect title="Ton de marque"><TextBlock text={str(c.brand_voice)} /></Sect>}
      {has(c.visual_identity) && <Sect title="Identité visuelle"><TextBlock text={str(c.visual_identity)} /></Sect>}
      {arr(c.differentiators).length > 0 && (
        <Sect title="Différenciateurs"><BulletList items={arr(c.differentiators)} /></Sect>
      )}
    </div>
  );
}

function BusinessModelView({ c }: { c: Record<string, unknown> }) {
  const streams = recs(c.revenue_streams);
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
      {has(c.model_type) && <Sect title="Type de modèle"><TextBlock text={str(c.model_type)} /></Sect>}
      {streams.length > 0 && (
        <Sect title="Sources de revenus">
          <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
            {streams.map((s, i) => (
              <div key={i} style={{ fontSize: 13, color: C.text, fontFamily: F.body }}>
                <strong>{str(s.stream)}</strong>
                {has(s.pricing) && <span style={{ color: C.muted }}> — {str(s.pricing)}</span>}
              </div>
            ))}
          </div>
        </Sect>
      )}
      {has(c.unit_economics) && (
        <Sect title="Économie unitaire"><TextBlock text={str(c.unit_economics)} /></Sect>
      )}
    </div>
  );
}

function LegalView({ c }: { c: Record<string, unknown> }) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
      {has(c.legal_structure) && (
        <Sect title="Structure juridique"><TextBlock text={str(c.legal_structure)} /></Sect>
      )}
      {arr(c.ip_assets).length > 0 && (
        <Sect title="Propriété intellectuelle"><BulletList items={arr(c.ip_assets)} /></Sect>
      )}
      {arr(c.compliance_requirements).length > 0 && (
        <Sect title="Exigences de conformité">
          <BulletList items={arr(c.compliance_requirements)} />
        </Sect>
      )}
      {arr(c.green_initiatives).length > 0 && (
        <Sect title="Initiatives vertes"><BulletList items={arr(c.green_initiatives)} /></Sect>
      )}
    </div>
  );
}

function OperationsView({ c }: { c: Record<string, unknown> }) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
      {arr(c.key_processes).length > 0 && (
        <Sect title="Processus clés"><BulletList items={arr(c.key_processes)} /></Sect>
      )}
      {has(c.team_structure) && (
        <Sect title="Structure d'équipe"><TextBlock text={str(c.team_structure)} /></Sect>
      )}
      {arr(c.tools_and_infra).length > 0 && (
        <Sect title="Outils & infrastructure"><BulletList items={arr(c.tools_and_infra)} /></Sect>
      )}
      {has(c.burn_rate) && (
        <Sect title="Burn rate estimé"><TextBlock text={str(c.burn_rate)} /></Sect>
      )}
    </div>
  );
}

function MarketingView({ c }: { c: Record<string, unknown> }) {
  const channels = recs(c.channels);
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
      {channels.length > 0 && (
        <Sect title="Canaux d'acquisition">
          <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
            {channels.map((ch, i) => (
              <Chip
                key={i}
                label={str(ch.channel)}
                value={`CAC ~${str(ch.estimated_cac || "?")}`}
              />
            ))}
          </div>
        </Sect>
      )}
      {has(c.positioning) && (
        <Sect title="Positionnement"><TextBlock text={str(c.positioning)} /></Sect>
      )}
      {arr(c.content_strategy).length > 0 && (
        <Sect title="Stratégie contenu"><BulletList items={arr(c.content_strategy)} /></Sect>
      )}
    </div>
  );
}

function SalesView({ c }: { c: Record<string, unknown> }) {
  const partners = recs(c.partnerships);
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
      {arr(c.sales_channels).length > 0 && (
        <Sect title="Canaux de vente"><BulletList items={arr(c.sales_channels)} /></Sect>
      )}
      {has(c.pipeline_model) && (
        <Sect title="Modèle pipeline"><TextBlock text={str(c.pipeline_model)} /></Sect>
      )}
      {partners.length > 0 && (
        <Sect title="Partenariats">
          <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
            {partners.map((p, i) => (
              <div key={i} style={{ fontSize: 13, color: C.text, fontFamily: F.body }}>
                <strong>{str(p.partner)}</strong>
                {has(p.type)  && <span style={{ color: C.muted }}> ({str(p.type)})</span>}
                {has(p.value) && <span> — {str(p.value)}</span>}
              </div>
            ))}
          </div>
        </Sect>
      )}
    </div>
  );
}

function RoadmapView({ c }: { c: Record<string, unknown> }) {
  const horizons: Array<[string, string]> = [
    ["immediate", "Immédiat (0–2 sem.)"],
    ["short_term", "Court terme (1–3 mois)"],
    ["medium_term", "Moyen terme (3–12 mois)"],
  ];
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
      {horizons.map(([key, label]) => {
        const items = arr(c[key]);
        if (!items.length) return null;
        return (
          <Sect key={key} title={label}>
            <BulletList items={items.map((a) =>
              typeof a === "object" && a !== null
                ? str((a as Record<string, unknown>).action ?? JSON.stringify(a))
                : str(a)
            )} />
          </Sect>
        );
      })}
    </div>
  );
}

function FallbackView({ content }: { content: Record<string, unknown> }) {
  const entries = Object.entries(content).filter(
    ([k, v]) => v !== null && v !== undefined && !k.startsWith("_"),
  );
  if (!entries.length) return null;
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
      {entries.map(([k, v]) => (
        <div key={k}>
          <Label>{k.replace(/_/g, " ")}</Label>
          {Array.isArray(v) ? (
            <BulletList items={v} />
          ) : (
            <TextBlock text={typeof v === "string" ? v : JSON.stringify(v, null, 2)} />
          )}
        </div>
      ))}
    </div>
  );
}

const KNOWN_AXES = new Set([
  "ideation","market","product","brand","business-model",
  "legal","operations","marketing","sales","roadmap",
]);

// ── Public component ─────────────────────────────────────────────────────

export function PlanSectionView({ axis, content }: Props) {
  const citations = asCitations(content._citations);
  return (
    <CitationsCtx.Provider value={citations}>
    <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
      {axis === "ideation"       && <IdeationView c={content} />}
      {axis === "market"         && <MarketView c={content} />}
      {axis === "product"        && <ProductView c={content} />}
      {axis === "brand"          && <BrandView c={content} />}
      {axis === "business-model" && <BusinessModelView c={content} />}
      {axis === "legal"          && <LegalView c={content} />}
      {axis === "operations"     && <OperationsView c={content} />}
      {axis === "marketing"      && <MarketingView c={content} />}
      {axis === "sales"          && <SalesView c={content} />}
      {axis === "roadmap"        && <RoadmapView c={content} />}
      {!KNOWN_AXES.has(axis)     && <FallbackView content={content} />}
      <Citations items={citations} />
    </div>
    </CitationsCtx.Provider>
  );
}
