import { useState } from "react";
import fr from "./locales/fr.json";
import ar from "./locales/ar.json";

type Lang = "fr" | "ar";
const STRINGS: Record<Lang, Record<string, string>> = { fr, ar };

// Phase 0 scaffold: a minimal HUD shell. The full dashboard, "Mon Parcours"
// view, voice pipeline, and SSE consumer are built in Phase 4.
export default function App() {
  const [lang, setLang] = useState<Lang>("fr");
  const t = (k: string) => STRINGS[lang][k] ?? k;

  return (
    <main dir={lang === "ar" ? "rtl" : "ltr"} style={{ fontFamily: "system-ui", padding: 24 }}>
      <h1>{t("app_title")}</h1>
      <p>{t("tagline")}</p>
      <button onClick={() => setLang(lang === "fr" ? "ar" : "fr")}>
        {t("switch_language")}
      </button>
    </main>
  );
}
