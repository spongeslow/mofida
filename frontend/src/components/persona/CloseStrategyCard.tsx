/** CloseStrategyCard — how to close the current persona (H3). */
import { useT } from "../../i18n";
import { C, F } from "../../theme";
import type { CloseStrategy } from "../../types";

export function CloseStrategyCard({ strategy }: { strategy: CloseStrategy }) {
  const t = useT();
  return (
    <div className="mf-anim-scale" style={{
      background: C.surfaceHigh, border: `1px solid ${C.accent}`, borderRadius: 12, padding: 14,
    }}>
      <h4 style={{ margin: "0 0 8px", color: C.text, fontFamily: F.heading, fontSize: 14 }}>
        {t("persona_close_title")}
      </h4>
      <p style={{ margin: "0 0 10px", color: C.text, fontSize: 13, lineHeight: 1.5 }}>{strategy.strategy}</p>
      {strategy.key_triggers?.length > 0 && (
        <div style={{ marginBottom: 8 }}>
          <span style={{ fontSize: 11.5, color: C.muted, fontWeight: 600 }}>{t("persona_triggers")}</span>
          <ul style={{ margin: "4px 0 0", paddingLeft: 18, color: C.text, fontSize: 12.5, lineHeight: 1.6 }}>
            {strategy.key_triggers.map((x, i) => <li key={i}>{x}</li>)}
          </ul>
        </div>
      )}
      {strategy.objections_to_address?.length > 0 && (
        <div>
          <span style={{ fontSize: 11.5, color: C.muted, fontWeight: 600 }}>{t("persona_objections_addr")}</span>
          <ul style={{ margin: "4px 0 0", paddingLeft: 18, color: C.text, fontSize: 12.5, lineHeight: 1.6 }}>
            {strategy.objections_to_address.map((x, i) => <li key={i}>{x}</li>)}
          </ul>
        </div>
      )}
    </div>
  );
}
