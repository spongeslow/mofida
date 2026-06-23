// derive.go — translate a project profile into concrete watcher targets.
//
// Every function here is pure (no I/O): it maps profile fields to lists of
// URLs, keywords, or search terms so each watcher's tick() remains thin.
package watchers

import (
	"strings"
	"unicode"
)

// --- News / RSS feeds ------------------------------------------------------

// sectorNewsFeeds returns sector-appropriate RSS news feeds.
// All sectors always include Wamda (Tunisia/MENA startup) and TechNewsAfrica.
func sectorNewsFeeds(sector string) []string {
	feeds := []string{
		"https://www.wamda.com/feed",
		"https://technewsafrica.com/feed",
	}
	switch sector {
	case "agri-food":
		return append(feeds,
			"https://www.agenceecofin.com/rss",
		)
	case "digital-tech":
		return append(feeds,
			"https://techcrunch.com/feed",
			"https://disrupt-africa.com/feed",
		)
	case "industry":
		return append(feeds,
			"https://www.agenceecofin.com/rss",
			"https://www.africanews.com/rss",
		)
	default: // cross-sector
		return append(feeds,
			"https://www.africanews.com/rss",
			"https://africarena.com/feed",
		)
	}
}

// --- Legal sources ---------------------------------------------------------

type legalSource struct{ name, url string }

// sectorLegalSources returns the regulatory sources to monitor for the sector.
// JORT (Tunisian Official Journal) is universal; sector-specific bodies are added.
func sectorLegalSources(sector string) []legalSource {
	base := []legalSource{
		{"JORT", "http://www.iort.gov.tn/WD120AWP/WD120Awp.exe/CONNECT/IORT_INTERNET"},
	}
	switch sector {
	case "agri-food":
		return append(base,
			legalSource{"MARHP", "http://www.agriculture.tn.gov/"},
			legalSource{"ONAGRI", "http://www.onagri.nat.tn/"},
		)
	case "digital-tech":
		return append(base,
			legalSource{"EUR-Lex GDPR", "https://eur-lex.europa.eu/legal-content/FR/LSU/?uri=CELEX:32016R0679"},
			legalSource{"INNORPI", "https://www.innorpi.tn"},
		)
	case "industry":
		return append(base,
			legalSource{"INNORPI", "https://www.innorpi.tn"},
			legalSource{"CETIME", "https://www.cetime.ind.tn"},
		)
	default: // cross-sector
		return append(base,
			legalSource{"EUR-Lex GDPR", "https://eur-lex.europa.eu/legal-content/FR/LSU/?uri=CELEX:32016R0679"},
			legalSource{"INNORPI", "https://www.innorpi.tn"},
		)
	}
}

// mergeLegalSources unions sector-seed legal sources with LLM-derived ones,
// deduping by URL while preserving order (seeds first).
func mergeLegalSources(seeds, extra []legalSource) []legalSource {
	seen := make(map[string]bool, len(seeds)+len(extra))
	out := make([]legalSource, 0, len(seeds)+len(extra))
	for _, s := range append(append([]legalSource{}, seeds...), extra...) {
		if s.url == "" || seen[s.url] {
			continue
		}
		seen[s.url] = true
		out = append(out, s)
	}
	return out
}

// deriveLegalKeywords builds a watch-keyword set from the profile's sector and
// actual compliance state (fields in the legal block drive targeted monitoring).
func deriveLegalKeywords(profile map[string]any) []string {
	sector, _ := profile["sector"].(string)

	// Universal baseline
	kws := []string{
		"Startup Act", "loi investissement", "protection des données",
	}

	switch sector {
	case "agri-food":
		kws = append(kws,
			"MARHP", "ONAGRI", "normes alimentaires", "certification bio",
			"traçabilité", "chaîne alimentaire", "label agriculture",
		)
	case "digital-tech":
		kws = append(kws,
			"GDPR", "RGPD", "AI Act", "cybersécurité", "données personnelles",
			"propriété intellectuelle", "logiciel", "souveraineté numérique",
		)
	case "industry":
		kws = append(kws,
			"INNORPI", "CETIME", "propriété industrielle", "brevet invention",
			"certification ISO", "normes industrielles",
		)
	default:
		kws = append(kws,
			"GDPR", "AI Act", "loi organique", "financement startup",
			"propriété intellectuelle",
		)
	}

	// Compliance gaps drive targeted keyword additions.
	if legal, ok := profile["legal"].(map[string]any); ok {
		if boolField(legal, "ai_act_applicable") {
			kws = append(kws, "AI Act", "systèmes IA", "haute risque IA", "conformité IA")
		}
		if !boolField(legal, "gdpr_policy_exists") {
			// GDPR policy missing → watch for enforcement and guidance updates.
			kws = append(kws, "CNIL", "amende RGPD", "violation données")
		}
		if !boolField(legal, "ip_registered") {
			// IP not yet registered → watch IP registration news.
			kws = append(kws, "dépôt brevet", "enregistrement marque", "protection logiciel")
		}
		if !boolField(legal, "tunisia_data_law_compliant") {
			kws = append(kws, "loi 2004-63", "INPDP", "données personnelles Tunisie")
		}
	}

	return dedup(kws)
}

// --- Trend keywords --------------------------------------------------------

// deriveTrendKeywords extracts meaningful search keywords from the project
// profile. It combines sector identity with terms from offer/innovation text
// fields so the trend scanner monitors what actually matters to the founder.
func deriveTrendKeywords(profile map[string]any) []string {
	var kws []string

	// Sector as a search term (not "cross-sector" — too generic).
	if s, _ := profile["sector"].(string); s != "" && s != "cross-sector" {
		kws = append(kws, s)
	}

	// Offer text fields — extract meaningful terms.
	if offer, ok := profile["offer"].(map[string]any); ok {
		kws = append(kws, extractTerms(strField(offer, "value_prop_text"), 6)...)
		kws = append(kws, extractTerms(strField(offer, "differentiation_text"), 4)...)
	}

	// Innovation text.
	if innov, ok := profile["innovation"].(map[string]any); ok {
		kws = append(kws, extractTerms(strField(innov, "novelty_text"), 4)...)
	}

	// Fallback: universal Tunisia startup terms.
	if len(kws) == 0 {
		kws = append(kws, "startup", "tunisie", "innovation", "numérique")
	}

	return dedup(kws)
}

// --- Competitor search terms -----------------------------------------------

// deriveCompetitorSearchTerms returns lowercase names to look for in news feeds.
func deriveCompetitorSearchTerms(profile map[string]any) []string {
	var terms []string
	market, _ := profile["market"].(map[string]any)
	if market == nil {
		return nil
	}

	if names, ok := market["competitor_names"].([]any); ok {
		for _, n := range names {
			if s, ok := n.(string); ok && s != "" {
				terms = append(terms, strings.ToLower(s))
			}
		}
	}
	if competitors, ok := market["competitors"].([]any); ok {
		for _, c := range competitors {
			if comp, ok := c.(map[string]any); ok {
				if name, ok := comp["name"].(string); ok && name != "" {
					terms = append(terms, strings.ToLower(name))
				}
			}
		}
	}
	return dedup(terms)
}

// --- Helpers ---------------------------------------------------------------

// extractTerms tokenizes text, strips stop-words and short tokens, and returns
// at most max meaningful words. Used to turn free-text fields into trend terms.
func extractTerms(text string, max int) []string {
	words := strings.FieldsFunc(text, func(r rune) bool {
		return !unicode.IsLetter(r) && !unicode.IsDigit(r)
	})
	seen := make(map[string]bool)
	var out []string
	for _, w := range words {
		w = strings.ToLower(strings.TrimSpace(w))
		if len(w) < 4 || frStopWords[w] || seen[w] {
			continue
		}
		seen[w] = true
		out = append(out, w)
		if len(out) >= max {
			break
		}
	}
	return out
}

// frStopWords are common French/English function words that carry no domain signal.
var frStopWords = map[string]bool{
	// French
	"avec": true, "cette": true, "dans": true, "pour": true, "plus": true,
	"nous": true, "votre": true, "notre": true, "leurs": true, "aussi": true,
	"mais": true, "comme": true, "elle": true, "vous": true, "tout": true,
	"bien": true, "sont": true, "avoir": true, "fait": true, "entre": true,
	"lors": true, "dont": true, "leur": true, "donc": true, "puis": true,
	"même": true, "très": true,
	// English
	"with": true, "that": true, "this": true, "from": true, "have": true,
	"will": true, "your": true, "their": true, "which": true, "been": true,
}

func strField(m map[string]any, key string) string {
	s, _ := m[key].(string)
	return s
}

func boolField(m map[string]any, key string) bool {
	b, _ := m[key].(bool)
	return b
}

// dedup removes duplicate and empty strings while preserving order.
func dedup(ss []string) []string {
	seen := make(map[string]bool, len(ss))
	out := make([]string, 0, len(ss))
	for _, s := range ss {
		if s != "" && !seen[s] {
			seen[s] = true
			out = append(out, s)
		}
	}
	return out
}
