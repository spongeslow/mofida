import { useStore } from "../../store";
import { useT } from "../../i18n";
import { C, severityColor, severityIcon, card } from "../../theme";
import type { Blocker } from "../../types";

function BlockerRow({ blocker }: { blocker: Blocker }) {
  const t = useT();
  const color = severityColor(blocker.severity);
  return (
    <li style={{
      display: "flex",
      flexDirection: "column",
      gap: 4,
      padding: "10px 0",
      borderBottom: `1px solid ${C.border}`,
    }}>
      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
        <span>{severityIcon(blocker.severity)}</span>
        <span style={{
          background: color + "22",
          color,
          fontSize: 11,
          padding: "2px 8px",
          borderRadius: 10,
          fontWeight: 600,
          textTransform: "uppercase",
          letterSpacing: 0.5,
        }}>
          {t(blocker.severity)}
        </span>
        {(blocker.axis ?? blocker.domain) && (
          <span style={{ color: C.muted, fontSize: 11 }}>
            {t("axis")}: {blocker.axis ?? blocker.domain}
          </span>
        )}
      </div>
      <p style={{ margin: 0, color: C.text, fontSize: 14 }}>{blocker.description}</p>
    </li>
  );
}

export function BlockerList() {
  const t = useT();
  const blockers = useStore((s) => s.blockers);

  return (
    <div style={card}>
      <p style={{ color: C.muted, fontSize: 12, margin: "0 0 12px", textTransform: "uppercase", letterSpacing: 1 }}>
        {t("blockers_critical")}
      </p>
      {blockers.length === 0 ? (
        <p style={{ color: C.muted, margin: 0 }}>{t("blockers_none")}</p>
      ) : (
        <ul style={{ margin: 0, padding: 0, listStyle: "none" }}>
          {blockers.map((b, i) => <BlockerRow key={i} blocker={b} />)}
        </ul>
      )}
    </div>
  );
}
