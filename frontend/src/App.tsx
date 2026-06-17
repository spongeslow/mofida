import { useState } from "react";
import fr from "./locales/fr.json";
import en from "./locales/en.json";

type Lang = "fr" | "en";
const STRINGS: Record<Lang, Record<string, string>> = { fr, en };

// Phase 0 scaffold: a minimal HUD shell. The full dashboard, "Mon Parcours"
// view, voice pipeline, and SSE consumer are built in Phase 4.
export default function App() {
  const [lang, setLang] = useState<Lang>("fr");
  const t = (k: string) => STRINGS[lang][k] ?? k;

  return (
    <main style={{ fontFamily: "system-ui", padding: 24 }}>
      <h1>{t("app_title")}</h1>
      <p>{t("tagline")}</p>
      <button onClick={() => setLang(lang === "fr" ? "en" : "fr")}>
        {t("switch_language")}
      </button>
    </main>
  );
}
