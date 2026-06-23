import { useStore } from "./store";
import fr from "./locales/fr.json";
import en from "./locales/en.json";
import ar from "./locales/ar.json";

const STRINGS: Record<string, Record<string, string>> = { fr, en, ar };

export function useT(): (k: string) => string {
  const lang = useStore((s) => s.lang);
  return (k: string) => STRINGS[lang]?.[k] ?? k;
}
