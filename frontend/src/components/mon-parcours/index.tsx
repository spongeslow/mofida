import { useT } from "../../i18n";
import { ScoreChart } from "./ScoreChart";
import { HistoryList } from "./HistoryList";
import { CompletedActions } from "./CompletedActions";
import { CompareDiagnostics } from "./CompareDiagnostics";
import { AchievementsCard } from "./AchievementsCard";
import { PageHeader } from "../shared/PageHeader";
import { IconChart } from "../shared/icons";

export function MonParcours() {
  const t = useT();
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
      <PageHeader title={t("history")} icon={<IconChart size={22} />} />
      <AchievementsCard />
      <ScoreChart />
      <CompareDiagnostics />
      <CompletedActions />
      <HistoryList />
    </div>
  );
}
