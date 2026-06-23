import { useT } from "../../i18n";
import { C } from "../../theme";
import { ScoreChart } from "./ScoreChart";
import { HistoryList } from "./HistoryList";
import { CompletedActions } from "./CompletedActions";
import { CompareDiagnostics } from "./CompareDiagnostics";
import { AchievementsCard } from "./AchievementsCard";

export function MonParcours() {
  const t = useT();
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
      <h2 style={{ margin: 0, color: C.text, fontSize: 20 }}>{t("history")}</h2>
      <AchievementsCard />
      <ScoreChart />
      <CompareDiagnostics />
      <CompletedActions />
      <HistoryList />
    </div>
  );
}
