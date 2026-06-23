#!/usr/bin/env python3
"""Generate the multilingual, per-axis knowledge-base resources for Moufida RAG.

These resources differ from scripts/generate_kb.py in two ways:
  1. Each carries a ``collection`` field naming the axis-specific Qdrant
     collection it belongs to (market, legal, product, ...). The RAG ingest
     creates these collections on demand; creation-mode /generate calls query
     the matching axis collection for grounded evidence.
  2. They are authored across three languages (fr / en / ar) so Arabic- and
     English-speaking founders get relevant hits (embedded with bge-m3).

Run from the project root:
    python scripts/generate_kb_axis.py
Then (re)ingest into Qdrant:
    ./scripts/ingest-kb.sh
"""
from __future__ import annotations

import json
import pathlib

# Resolve the resources dir relative to the repo root, regardless of CWD.
OUT = pathlib.Path(__file__).resolve().parents[1] / "backend" / "rag" / "knowledge-base" / "resources"
OUT.mkdir(parents=True, exist_ok=True)

RESOURCES: list[dict] = [
    # ── MARKET ────────────────────────────────────────────────────────────────
    {
        "id": "market-tam-sam-som-methode",
        "collection": "market",
        "language": "fr",
        "title": "Méthode TAM/SAM/SOM pour startups tunisiennes",
        "type": "training_coaching",
        "stage": ["market_validation"],
        "sector": ["cross-sector"],
        "score_dimensions": ["market"],
        "provider": "Smart Capital / Startup Tunisia",
        "url": "https://www.startup.gov.tn",
        "last_verified": "2026-06-01",
        "body": (
            "Le dimensionnement de marché TAM/SAM/SOM est exigé par la plupart des investisseurs tunisiens "
            "(Smart Capital, SICAR, business angels). Le TAM (Total Addressable Market) représente la demande "
            "totale ; le SAM (Serviceable Available Market) la portion atteignable par votre modèle ; le SOM "
            "(Serviceable Obtainable Market) la part réaliste captable en 12-24 mois.\n\n"
            "Pour une startup tunisienne, estimez le SOM à partir de données réelles : taille de la cible en "
            "Tunisie (INS, données ouvertes), taux de pénétration observable, et capacité commerciale. Évitez "
            "les pourcentages arbitraires du TAM ('1% d'un grand marché') — les comités d'investissement les "
            "rejettent systématiquement.\n\n"
            "Documentez chaque hypothèse avec une source. Un dossier marché crédible cite l'Institut National "
            "de la Statistique, des rapports sectoriels, et au moins 10 entretiens clients qualifiés."
        ),
    },
    {
        "id": "market-competitor-analysis-ar",
        "collection": "market",
        "language": "ar",
        "title": "تحليل المنافسين للشركات الناشئة",
        "type": "training_coaching",
        "stage": ["market_validation"],
        "sector": ["cross-sector"],
        "score_dimensions": ["market"],
        "provider": "Startup Tunisia",
        "url": "https://www.startup.gov.tn",
        "last_verified": "2026-06-01",
        "body": (
            "يُعدّ تحليل المنافسين ركيزة أساسية في دراسة السوق. حدّد المنافسين المباشرين (نفس الحل) وغير "
            "المباشرين (حلول بديلة لنفس المشكلة)، ثمّ قارن بينهم على أساس السعر، الميزات، شريحة العملاء، "
            "ونقاط القوة والضعف.\n\n"
            "بالنسبة للسوق التونسي، ادرس أيضًا المنافسين الإقليميين (المغرب، مصر) الذين قد يدخلون السوق "
            "المحلي. استعمل جدول مقارنة واضحًا يُبرز عامل التمايز الخاص بك (Differentiation) بشكل لا لبس فيه.\n\n"
            "المستثمرون يبحثون عن ميزة تنافسية قابلة للدفاع: تكنولوجيا، شبكة شراكات، أو نفاذ مبكّر للسوق. "
            "وثّق مصادرك واذكر بيانات حقيقية كلما أمكن."
        ),
    },
    # ── LEGAL ─────────────────────────────────────────────────────────────────
    {
        "id": "legal-startup-act-label",
        "collection": "legal",
        "language": "fr",
        "title": "Label Startup Act : conditions et avantages juridiques",
        "type": "legal_regulatory",
        "stage": ["structuration"],
        "sector": ["cross-sector"],
        "score_dimensions": ["green"],
        "provider": "Startup Tunisia (Smart Capital)",
        "url": "https://www.startup.gov.tn",
        "last_verified": "2026-06-01",
        "body": (
            "Le Startup Act tunisien (loi n°2018-20) accorde le label 'Startup' aux jeunes entreprises "
            "innovantes de moins de 8 ans. Le label ouvre droit à : exonération d'impôt sur les sociétés, "
            "prise en charge des cotisations sociales du fondateur, bourse de startup, et droit au congé "
            "pour création d'entreprise.\n\n"
            "Conditions principales : être une personne morale de droit tunisien, moins de 8 ans d'existence, "
            "majorité du capital détenue par des personnes physiques ou des fonds d'investissement, et un "
            "caractère innovant + potentiel de croissance (scalabilité).\n\n"
            "La demande se fait en ligne sur startup.gov.tn ; le Collège de labellisation statue par cycles. "
            "Préparez votre pitch, votre dossier d'innovation et vos états financiers prévisionnels."
        ),
    },
    {
        "id": "legal-data-protection-inpdp-ar",
        "collection": "legal",
        "language": "ar",
        "title": "حماية البيانات الشخصية والامتثال (INPDP)",
        "type": "legal_regulatory",
        "stage": ["structuration"],
        "sector": ["digital-tech"],
        "score_dimensions": ["green"],
        "provider": "الهيئة الوطنية لحماية المعطيات الشخصية",
        "url": "https://www.inpdp.nat.tn",
        "last_verified": "2026-06-01",
        "body": (
            "تخضع معالجة البيانات الشخصية في تونس للقانون الأساسي عدد 63 لسنة 2004 وتشرف عليه الهيئة "
            "الوطنية لحماية المعطيات الشخصية (INPDP). يجب على كل شركة ناشئة تجمع بيانات المستخدمين "
            "التصريح المسبق لدى الهيئة.\n\n"
            "إذا كنت تستهدف السوق الأوروبية، فالامتثال للائحة العامة لحماية البيانات (GDPR) ضروري: موافقة "
            "صريحة، حق الوصول والحذف، وتأمين التخزين. وثّق سياسة الخصوصية بثلاث لغات إن أمكن.\n\n"
            "عدم الامتثال يُعدّ خطرًا قانونيًا (Red flag) يرفضه المستثمرون في مرحلة العناية الواجبة "
            "(Due Diligence)."
        ),
    },
    # ── PRODUCT ───────────────────────────────────────────────────────────────
    {
        "id": "product-mvp-prioritization",
        "collection": "product",
        "language": "en",
        "title": "MVP feature prioritization with MoSCoW and RICE",
        "type": "training_coaching",
        "stage": ["ideation", "market_validation"],
        "sector": ["digital-tech"],
        "score_dimensions": ["commercial_offer"],
        "provider": "Flat6Labs Tunis",
        "url": "https://www.flat6labs.com",
        "last_verified": "2026-06-01",
        "body": (
            "A Minimum Viable Product should validate one core hypothesis with the least build effort. Use "
            "MoSCoW (Must / Should / Could / Won't) to ruthlessly cut scope: ship only the 'Must' features "
            "that prove your value proposition.\n\n"
            "For harder trade-offs, score features with RICE (Reach x Impact x Confidence / Effort). This "
            "forces evidence-based prioritization and gives investors a defensible product roadmap rather "
            "than a wish list.\n\n"
            "Measure the MVP against a single success metric (activation, retention, or willingness to pay). "
            "Tunisian accelerators like Flat6Labs expect a working MVP with real user feedback before seed "
            "investment."
        ),
    },
    {
        "id": "product-value-prop-canvas-fr",
        "collection": "product",
        "language": "fr",
        "title": "Value Proposition Canvas : aligner produit et besoins",
        "type": "training_coaching",
        "stage": ["ideation"],
        "sector": ["cross-sector"],
        "score_dimensions": ["commercial_offer"],
        "provider": "B@Labs",
        "url": "https://www.startup.gov.tn",
        "last_verified": "2026-06-01",
        "body": (
            "Le Value Proposition Canvas relie les caractéristiques de votre produit aux besoins réels du "
            "client. Côté client : décrivez les tâches à accomplir (jobs), les frustrations (pains) et les "
            "bénéfices attendus (gains). Côté produit : les créateurs de gains et les soulageurs de douleurs.\n\n"
            "Une proposition de valeur forte répond à une douleur intense et fréquente, validée par des "
            "entretiens. Si vos features ne correspondent à aucun 'pain' prioritaire, vous construisez une "
            "solution en quête de problème.\n\n"
            "Testez la formulation de votre proposition de valeur sur une landing page (Typeform, Carrd) et "
            "mesurez le taux de conversion avant d'investir dans le développement complet."
        ),
    },
    # ── BRAND ─────────────────────────────────────────────────────────────────
    {
        "id": "brand-innovation-ip-innorpi",
        "collection": "brand",
        "language": "fr",
        "title": "Protéger l'innovation : marque et brevets via l'INNORPI",
        "type": "legal_regulatory",
        "stage": ["structuration"],
        "sector": ["cross-sector"],
        "score_dimensions": ["innovation"],
        "provider": "INNORPI",
        "url": "https://www.innorpi.tn",
        "last_verified": "2026-06-01",
        "body": (
            "L'INNORPI (Institut National de la Normalisation et de la Propriété Industrielle) gère en Tunisie "
            "l'enregistrement des marques, brevets et dessins industriels. Déposer votre marque protège votre "
            "identité et rassure les investisseurs sur la défendabilité de votre actif immatériel.\n\n"
            "Pour une marque : vérifiez la disponibilité, déposez la classe Nice pertinente, et budgétez le "
            "renouvellement décennal. Pour une innovation technique brevetable, un dépôt prioritaire en Tunisie "
            "ouvre 12 mois pour étendre à l'international (PCT).\n\n"
            "Même sans brevet, documentez votre avantage d'innovation : savoir-faire, données propriétaires, "
            "effets de réseau. Les comités d'innovation du Startup Act évaluent ce caractère innovant."
        ),
    },
    {
        "id": "brand-positioning-storytelling-en",
        "collection": "brand",
        "language": "en",
        "title": "Brand positioning and storytelling for early-stage startups",
        "type": "training_coaching",
        "stage": ["market_validation"],
        "sector": ["cross-sector"],
        "score_dimensions": ["innovation"],
        "provider": "Startup Tunisia",
        "url": "https://www.startup.gov.tn",
        "last_verified": "2026-06-01",
        "body": (
            "Positioning is the single idea you want to own in your customer's mind. Define it with a one-line "
            "statement: for [target] who [need], [brand] is the [category] that [unique benefit], unlike "
            "[alternative].\n\n"
            "Strong early-stage brands lead with a narrative: the problem, why now, and the change you create. "
            "Consistency across name, voice, and visual identity builds trust faster than a large marketing "
            "budget.\n\n"
            "For Tunisian startups expanding regionally, design a brand that travels: avoid local-only idioms, "
            "and test the name for meaning across Arabic, French and English to avoid costly rebrands."
        ),
    },
    # ── BUSINESS-MODEL ────────────────────────────────────────────────────────
    {
        "id": "bm-unit-economics-cac-ltv",
        "collection": "business-model",
        "language": "en",
        "title": "Unit economics: CAC, LTV and payback for fundraising",
        "type": "financing",
        "stage": ["fundraising"],
        "sector": ["cross-sector"],
        "score_dimensions": ["scalability"],
        "provider": "AfricInvest / Smart Capital",
        "url": "https://www.startup.gov.tn",
        "last_verified": "2026-06-01",
        "body": (
            "Investors assess scalability through unit economics. Customer Acquisition Cost (CAC) is total "
            "sales and marketing spend divided by new customers in a period. Lifetime Value (LTV) is the gross "
            "margin a customer generates over their lifetime.\n\n"
            "A healthy SaaS benchmark is LTV/CAC above 3 and a CAC payback under 12 months. Track these from "
            "day one — even rough numbers show financial literacy and de-risk the investment.\n\n"
            "For Tunisian startups, present both TND and hard-currency figures if you target export revenue, "
            "and explain how unit economics improve with scale (lower CAC via referrals, higher LTV via upsell)."
        ),
    },
    {
        "id": "bm-revenue-models-ar",
        "collection": "business-model",
        "language": "ar",
        "title": "نماذج تحقيق الإيرادات للشركات الناشئة",
        "type": "training_coaching",
        "stage": ["structuration"],
        "sector": ["cross-sector"],
        "score_dimensions": ["scalability"],
        "provider": "Startup Tunisia",
        "url": "https://www.startup.gov.tn",
        "last_verified": "2026-06-01",
        "body": (
            "اختيار نموذج الإيرادات المناسب يحدّد قابلية التوسّع. من النماذج الشائعة: الاشتراك الشهري "
            "(Subscription)، العمولة على المعاملات (Marketplace)، الترخيص (Licensing)، والنموذج المجاني "
            "المدعوم بالترقية (Freemium).\n\n"
            "بالنسبة للسوق التونسي، راعِ ضعف ثقافة الدفع الإلكتروني وقدّم وسائل دفع محلية (e-Dinar، تحويل "
            "بنكي، الدفع عند الاستلام). نموذج الاشتراك يوفّر إيرادات متكرّرة يقدّرها المستثمرون.\n\n"
            "احسب الهامش الإجمالي لكل نموذج وتأكّد من أنّ تكلفة الخدمة تنخفض مع التوسّع. الإيرادات المتكرّرة "
            "والهامش المرتفع يرفعان تقييم الشركة."
        ),
    },
    # ── OPERATIONS ────────────────────────────────────────────────────────────
    {
        "id": "ops-hiring-cnss-first-hire",
        "collection": "operations",
        "language": "fr",
        "title": "Premier recrutement : CNSS, contrats et aides",
        "type": "legal_regulatory",
        "stage": ["structuration"],
        "sector": ["cross-sector"],
        "score_dimensions": ["scalability"],
        "provider": "CNSS / Startup Act",
        "url": "https://www.cnss.tn",
        "last_verified": "2026-06-01",
        "body": (
            "Le premier recrutement structure vos opérations. En Tunisie, tout salarié doit être déclaré à la "
            "CNSS (Caisse Nationale de Sécurité Sociale) dès l'embauche ; l'affiliation est obligatoire et son "
            "absence constitue un risque social majeur.\n\n"
            "Le Startup Act prend en charge les cotisations sociales patronales et salariales des fondateurs "
            "labellisés, ce qui allège la masse salariale en phase d'amorçage. Choisissez le bon contrat "
            "(CDD, CDI, SIVP pour les jeunes diplômés via l'ANETI).\n\n"
            "Formalisez dès le départ : fiches de poste, organigramme, et processus clés documentés. Une "
            "équipe structurée et conforme rassure investisseurs et partenaires."
        ),
    },
    {
        "id": "ops-cloud-infrastructure-en",
        "collection": "operations",
        "language": "en",
        "title": "Lean cloud infrastructure and free startup credits",
        "type": "technical_infrastructure",
        "stage": ["launch_planning", "growth"],
        "sector": ["digital-tech"],
        "score_dimensions": ["scalability"],
        "provider": "Google for Startups / AWS Activate",
        "url": "https://cloud.google.com/startup",
        "last_verified": "2026-06-01",
        "body": (
            "Operational scalability depends on infrastructure that grows without manual rework. Start with "
            "managed services (databases, queues, object storage) to avoid running your own servers, and "
            "automate deployments with CI/CD from the first release.\n\n"
            "Most cloud providers offer free credits to early-stage startups: Google for Startups, AWS "
            "Activate, and Microsoft for Startups each provide thousands of dollars in credits — valuable for "
            "Tunisian teams managing hard-currency costs.\n\n"
            "Design for observability early: logging, metrics and alerts. Investors view a reliable, monitored "
            "stack as a sign of operational maturity and reduced execution risk."
        ),
    },
    # ── MARKETING ─────────────────────────────────────────────────────────────
    {
        "id": "marketing-digital-acquisition-fr",
        "collection": "marketing",
        "language": "fr",
        "title": "Canaux d'acquisition digitale à budget maîtrisé",
        "type": "training_coaching",
        "stage": ["launch_planning", "growth"],
        "sector": ["cross-sector"],
        "score_dimensions": ["commercial_offer"],
        "provider": "Startup Tunisia",
        "url": "https://www.startup.gov.tn",
        "last_verified": "2026-06-01",
        "body": (
            "En phase de lancement, concentrez le budget marketing sur 1 ou 2 canaux mesurables plutôt que de "
            "vous disperser. Pour le marché tunisien, Facebook et Instagram dominent l'acquisition B2C ; "
            "LinkedIn et le content marketing fonctionnent pour le B2B.\n\n"
            "Mesurez chaque canal par son coût d'acquisition (CAC) et son taux de conversion. Privilégiez les "
            "canaux organiques au départ (contenu, communauté, bouche-à-oreille) qui offrent le meilleur "
            "retour avant d'investir en publicité payante.\n\n"
            "Mettez en place un suivi analytique (Google Analytics, pixel Meta) dès le premier jour pour "
            "décider sur la base de données réelles et non d'intuitions."
        ),
    },
    {
        "id": "marketing-content-strategy-ar",
        "collection": "marketing",
        "language": "ar",
        "title": "استراتيجية المحتوى لاكتساب العملاء",
        "type": "training_coaching",
        "stage": ["growth"],
        "sector": ["cross-sector"],
        "score_dimensions": ["commercial_offer"],
        "provider": "Startup Tunisia",
        "url": "https://www.startup.gov.tn",
        "last_verified": "2026-06-01",
        "body": (
            "استراتيجية المحتوى وسيلة منخفضة التكلفة لاكتساب العملاء وبناء الثقة. أنشئ محتوى يجيب عن أسئلة "
            "جمهورك الحقيقية (مدوّنات، فيديوهات قصيرة، دراسات حالة) ووزّعه عبر القنوات التي يستعملها فعلاً.\n\n"
            "في السوق التونسي والمغاربي، المحتوى باللهجة المحلية أو العربية الفصحى المبسّطة يحقّق تفاعلًا "
            "أعلى. حافظ على وتيرة نشر منتظمة وقِس الأداء عبر معدّل التفاعل والتحويل.\n\n"
            "اربط المحتوى بمسار التحويل: وعي ← اهتمام ← قرار. المحتوى الجيّد يخفّض تكلفة اكتساب العميل (CAC) "
            "ويعزّز العلامة التجارية."
        ),
    },
    # ── SALES ─────────────────────────────────────────────────────────────────
    {
        "id": "sales-b2b-pipeline-en",
        "collection": "sales",
        "language": "en",
        "title": "Building a B2B sales pipeline and closing first pilots",
        "type": "training_coaching",
        "stage": ["market_validation", "launch_planning"],
        "sector": ["cross-sector"],
        "score_dimensions": ["commercial_offer"],
        "provider": "Flat6Labs / CONECT",
        "url": "https://www.startup.gov.tn",
        "last_verified": "2026-06-01",
        "body": (
            "A B2B pipeline turns prospects into paying customers through defined stages: lead, qualified, "
            "demo, proposal, and closed. Track conversion at each stage to find bottlenecks and forecast "
            "revenue.\n\n"
            "For early traction, prioritize paid pilots over free trials: a customer who pays — even a small "
            "amount — validates willingness to pay, the strongest market signal for investors. In Tunisia, "
            "leverage networks like CONECT and UTICA to reach corporate buyers.\n\n"
            "Document every pilot's success criteria up front and convert pilots into references and case "
            "studies. Three paying pilots with measurable outcomes de-risk your seed round significantly."
        ),
    },
    {
        "id": "sales-partnerships-distribution-fr",
        "collection": "sales",
        "language": "fr",
        "title": "Partenariats de distribution pour accélérer les ventes",
        "type": "networking_ecosystem",
        "stage": ["growth"],
        "sector": ["cross-sector"],
        "score_dimensions": ["commercial_offer"],
        "provider": "CONECT / UTICA",
        "url": "https://www.conect.org.tn",
        "last_verified": "2026-06-01",
        "body": (
            "Les partenariats de distribution permettent d'atteindre des clients sans construire toute la "
            "force de vente. Identifiez des partenaires dont les clients correspondent à votre cible : "
            "revendeurs, intégrateurs, ou plateformes complémentaires.\n\n"
            "En Tunisie, les fédérations professionnelles (CONECT, UTICA) et les grandes entreprises "
            "partenaires des incubateurs ouvrent des portes B2B. Structurez l'accord : marge partenaire, "
            "exclusivité éventuelle, objectifs de volume et durée.\n\n"
            "Mesurez la contribution de chaque partenaire au chiffre d'affaires. Un réseau de distribution "
            "actif est un actif stratégique valorisé lors des levées de fonds."
        ),
    },
    # ── IDEATION ──────────────────────────────────────────────────────────────
    {
        "id": "ideation-problem-solution-fit-fr",
        "collection": "ideation",
        "language": "fr",
        "title": "Atteindre le Problem-Solution Fit avant de construire",
        "type": "training_coaching",
        "stage": ["ideation"],
        "sector": ["cross-sector"],
        "score_dimensions": ["market"],
        "provider": "Startup Tunisia",
        "url": "https://www.startup.gov.tn",
        "last_verified": "2026-06-01",
        "body": (
            "Le Problem-Solution Fit précède le Product-Market Fit : il s'agit de prouver que le problème "
            "ciblé est réel, intense et fréquent, et que votre solution y répond. Conduisez au moins 10 à 15 "
            "entretiens problème selon la méthode 'The Mom Test' — posez des questions sur le passé et les "
            "comportements réels, jamais sur des intentions hypothétiques.\n\n"
            "Formulez clairement : qui a le problème, à quelle fréquence, quelles solutions de contournement "
            "existent aujourd'hui, et combien cela leur coûte. Si les gens ne cherchent pas activement une "
            "solution, le problème n'est pas assez douloureux.\n\n"
            "Documentez les preuves (verbatims, données) avant d'écrire une ligne de code. Cette discipline "
            "distingue les fondateurs crédibles aux yeux des incubateurs tunisiens."
        ),
    },
    {
        "id": "ideation-maturity-stages-ar",
        "collection": "ideation",
        "language": "ar",
        "title": "مراحل نضج الشركة الناشئة وتقييم الجاهزية",
        "type": "training_coaching",
        "stage": ["ideation"],
        "sector": ["cross-sector"],
        "score_dimensions": ["market"],
        "provider": "Startup Tunisia",
        "url": "https://www.startup.gov.tn",
        "last_verified": "2026-06-01",
        "body": (
            "تمرّ الشركة الناشئة بمراحل نضج متتابعة: الفكرة، التحقّق من السوق، الهيكلة، جمع التمويل، التخطيط "
            "للإطلاق، ثمّ النمو. تحديد مرحلتك بدقّة يساعدك على اختيار الأولويات المناسبة وتجنّب الحرق المبكّر "
            "للموارد.\n\n"
            "في مرحلة الفكرة، ركّز على فهم المشكلة والعميل لا على بناء المنتج الكامل. كل مرحلة لها مؤشّرات "
            "جاهزية: مقابلات العملاء، المنتج الأوّلي (MVP)، أولى الإيرادات، ثمّ النمو القابل للتوسّع.\n\n"
            "برنامج Startup Act التونسي يدعم الشركات الناشئة المبتكرة عبر مراحلها المختلفة. قيّم جاهزيتك بصدق "
            "فالمستثمرون يكشفون المبالغة بسرعة."
        ),
    },
]


def write_resources(resources: list[dict]) -> int:
    count = 0
    for r in resources:
        path = OUT / f"{r['id']}.json"
        path.write_text(json.dumps(r, ensure_ascii=False, indent=2))
        count += 1
    return count


if __name__ == "__main__":
    n = write_resources(RESOURCES)
    from collections import Counter
    by_coll = Counter(r["collection"] for r in RESOURCES)
    by_lang = Counter(r["language"] for r in RESOURCES)
    print(f"Generated {n} per-axis resource files in {OUT}")
    print(f"  by collection: {dict(by_coll)}")
    print(f"  by language:   {dict(by_lang)}")
