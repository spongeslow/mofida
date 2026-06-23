import { useT } from "../../i18n";
import { C } from "../../theme";
import { ChatPanel } from "./ChatPanel";
import { ReviewCard } from "./ReviewCard";
import { AlertFeed } from "./AlertFeed";
import { WatchTargetsCard } from "./WatchTargetsCard";
import { KbAddCard } from "./KbAddCard";

export function HUD() {
  const t = useT();
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
      <h2 style={{ margin: 0, color: C.text, fontSize: 20 }}>{t("nav_hud")}</h2>
      <ReviewCard />
      <ChatPanel />
      <AlertFeed />
      <WatchTargetsCard />
      <KbAddCard />
    </div>
  );
}
