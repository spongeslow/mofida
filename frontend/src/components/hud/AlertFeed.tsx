import { useStore } from "../../store";
import { useT } from "../../i18n";
import { C, card, severityColor, severityIcon } from "../../theme";

export function AlertFeed() {
  const t            = useT();
  const alerts       = useStore((s) => s.alerts);
  const dismissAlert = useStore((s) => s.dismissAlert);

  const visible = alerts.filter((a) => !a.dismissed);

  return (
    <div style={card}>
      <p style={{ color: C.muted, fontSize: 12, margin: "0 0 12px", textTransform: "uppercase", letterSpacing: 1 }}>
        {t("alerts_title")}
      </p>
      {visible.length === 0 ? (
        <p style={{ color: C.muted, margin: 0, fontSize: 14 }}>{t("no_alerts")}</p>
      ) : (
        <ul style={{ margin: 0, padding: 0, listStyle: "none", maxHeight: 300, overflowY: "auto" }}>
          {visible.map((alert) => {
            const color = severityColor(alert.severity);
            return (
              <li key={alert.id} style={{
                display: "flex",
                alignItems: "flex-start",
                gap: 10,
                padding: "10px 0",
                borderBottom: `1px solid ${C.border}`,
              }}>
                <span style={{ fontSize: 16, marginTop: 1 }}>{severityIcon(alert.severity)}</span>
                <div style={{ flex: 1 }}>
                  <p style={{ margin: "0 0 2px", fontWeight: 600, color, fontSize: 14 }}>{alert.title}</p>
                  <p style={{ margin: "0 0 4px", color: C.muted, fontSize: 13, lineHeight: 1.4 }}>{alert.body}</p>
                  <span style={{ color: C.muted, fontSize: 11 }}>{new Date(alert.timestamp).toLocaleTimeString()}</span>
                </div>
                <button
                  onClick={() => dismissAlert(alert.id)}
                  style={{ background: "none", border: "none", color: C.muted, cursor: "pointer", fontSize: 16, padding: 0 }}
                  title={t("dismiss")}
                >
                  ×
                </button>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
