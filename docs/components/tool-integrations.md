# Tool Integrations

**Location:** `moufida-tools/` | **Stack:** Python 3.12 package

Tool integrations serve two purposes: pulling real data to upgrade evidence tiers (T3 = daemon-observed = 1.2× weight), and pushing diagnostic results back into the founder's existing workflow.

---

## ToolManager Facade

Called by the orchestrator at two points in every diagnostic:

**`enrich_profile(pool, profile)`** — before scoring: all enabled pull tools run, merging their data into the profile. Evidence tiers are upgraded, never downgraded. A field at T2 can reach T3 from a tool, but cannot go back to T1.

**`dispatch_diagnostic(pool, diagnostic)`** — after scoring: all enabled push tools receive the full diagnostic result (scores, blockers, maturity, roadmap).

**`dispatch_alert()`** — when a score drops significantly: push tools post the alert.

---

## The Six Tools

| Tool | Type | Evidence upgrades | What it reads/writes |
|---|---|---|---|
| **GitHub** | Pull | `ops.engineering_velocity` → T3, `innovation.technical_depth` → T3, `product.mvp_existence` → T3 | Commit frequency, PR activity, repo metadata |
| **Notion** | Pull | product, ideation, market fields → T2/T3 | Spec documents, customer interview notes, business plan pages |
| **Google Sheets** | Pull + Push | finance fields → T2/T3 | Revenue, expenses, customer metrics; pushes score summary rows |
| **Google Analytics** | Pull | `market.customer_count`, `sales.conversion_evidence`, `marketing.channel_identification` → T3 | MAU, conversion rate, acquisition channels |
| **Slack** | Push | — | Posts diagnostic briefings and score alerts to configured channels |
| **Composio** | Bidirectional gateway | Any of the above via managed OAuth | OAuth handshake + inbound trigger relay |

---

## Evidence Tier Economics

The same profile field value scores higher when backed by real tool data:

```
Field "mvp_existence" with value 0.8:
  T1 (self-declared):         contribution = weight × 0.8 × 0.6
  T2 (from pitch deck upload): contribution = weight × 0.8 × 1.0
  T3 (GitHub: repo + commits): contribution = weight × 0.8 × 1.2
```

This creates a concrete incentive for founders to connect their tools. A connected GitHub making `product.mvp_existence` T3 increases its score contribution by 100% over the self-reported T1 baseline.

---

## Composio — The Bidirectional Gateway

**Manual-token tools** require pasting credentials. **Composio tools** use managed OAuth — click Connect, authorise in a browser popup, no credentials stored client-side.

**Inbound triggers:** when something changes in a connected tool (Notion page updated, GitHub commit pushed), Composio sends a webhook to the orchestrator. This arrives as a `tool_signals` row and triggers dependency-aware axis re-runs → appears in the Event Feed with a field-level diff.

**NAT-friendly polling:** desktop apps behind home routers cannot receive inbound webhooks. The Go daemon polls `POST /integrations/poll` every ~5 minutes. The Composio API key stays server-side in the orchestrator.

**The one local-first exception:** Composio's OAuth popup and trigger broker are hosted by Composio. The entire diagnostic/scoring/RAG pipeline stays local. Leave `COMPOSIO_API_KEY` empty and all Composio tools report "unavailable" while manual-token tools keep working.

---

## Adding a New Tool

1. Create a class inheriting `BaseTool` (or `PullTool`/`PushTool`) in `moufida-tools/src/`
2. Implement `test_connection(config)`, `enrich_profile()`, and/or `on_diagnostic_complete()`
3. Register in `REGISTERED_TOOLS`
4. Add a DB migration to seed the `tool_integrations` row

No orchestrator changes required — `ToolManager` discovers tools via the registry.
