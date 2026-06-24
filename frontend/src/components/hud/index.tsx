import { useT } from "../../i18n";
import { C, T } from "../../theme";
import { ChatPanel } from "./ChatPanel";
import { ReviewCard } from "./ReviewCard";
import { AlertFeed } from "./AlertFeed";
import { WatchTargetsCard } from "./WatchTargetsCard";
import { KbAddCard } from "./KbAddCard";

export function HUD() {
  const t = useT();
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
      <header style={{ marginBottom: 2 }}>
        <p style={{ ...T.eyebrow, color: C.accent, margin: "0 0 4px" }}>{t("tagline_short")}</p>
        <h2 style={{ ...T.h1, margin: 0, color: C.ink }}>{t("nav_hud")}</h2>
      </header>
      <ReviewCard />
      <ChatPanel />
      <AlertFeed />
      <WatchTargetsCard />
      <KbAddCard />
    </div>
  );
}
