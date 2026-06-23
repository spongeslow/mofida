#!/usr/bin/env python3
"""Generate all 65 knowledge-base resource JSON files for the Moufida RAG system.

Output goes to backend/rag/knowledge-base/resources/ regardless of CWD.

    python scripts/generate_kb.py
"""
from __future__ import annotations
import json, pathlib

OUT = pathlib.Path(__file__).resolve().parents[1] / "backend" / "rag" / "knowledge-base" / "resources"
OUT.mkdir(parents=True, exist_ok=True)

RESOURCES: list[dict] = [
    # ── IDEATION ──────────────────────────────────────────────────────────────
    {
        "id": "apii-innovation-grant",
        "title": "APII — Prime à l'Innovation Technologique",
        "type": "financing",
        "stage": ["ideation", "market_validation"],
        "sector": ["cross-sector", "digital-tech", "industry"],
        "score_dimensions": ["commercial_offer", "innovation"],
        "url": "https://www.apii.tn/apii/programme-innovation",
        "language": "fr",
        "last_verified": "2026-06-01",
        "provider": "APII — Agence de Promotion de l'Industrie et de l'Innovation",
        "body": (
            "L'APII propose une Prime à l'Innovation Technologique (PIT) destinée aux porteurs de projets "
            "innovants en phase d'idéation ou de validation. Le dispositif couvre jusqu'à 70 % des dépenses "
            "éligibles (études de faisabilité, prototypage, conseil en PI) dans la limite de 50 000 TND.\n\n"
            "Pour être éligible, le porteur doit déposer un dossier incluant un business plan préliminaire, "
            "une description technique de l'innovation et un justificatif d'inscription au Registre National "
            "des Entreprises (RNE) ou une attestation de dépôt de marque INNORPI. L'instruction dure "
            "généralement 4 à 6 semaines.\n\n"
            "Ce mécanisme est cumulable avec le statut Startup Act. Les startups labellisées peuvent bénéficier "
            "d'une prime majorée et d'une procédure accélérée via le guichet unique de l'APII à Tunis. "
            "Le paiement est effectué en deux tranches : 40 % à l'approbation, 60 % à la réception des livrables."
        ),
    },
    {
        "id": "bts-micro-credit-ideation",
        "title": "BTS — Micro-crédit pour porteurs de projet",
        "type": "financing",
        "stage": ["ideation", "market_validation"],
        "sector": ["cross-sector"],
        "score_dimensions": ["scalability"],
        "url": "https://www.bts.com.tn/fr/micro-entreprises",
        "language": "fr",
        "last_verified": "2026-06-01",
        "provider": "Banque Tunisienne de Solidarité (BTS)",
        "body": (
            "La Banque Tunisienne de Solidarité (BTS) propose des micro-crédits sans garantie réelle allant de "
            "1 000 à 100 000 TND pour les porteurs de projets à la phase d'idéation ou de démarrage. "
            "Le taux d'intérêt est bonifié à 5 % l'an avec une période de grâce de 6 mois.\n\n"
            "L'accès est conditionné par un profil socio-économique éligible et un business plan simplifié. "
            "La BTS dispose de 24 agences régionales couvrant l'ensemble du territoire tunisien. "
            "Les associations de microcrédit (Enda Tamweel, Advans Tunisie) complètent ce dispositif "
            "pour les montants inférieurs à 20 000 TND.\n\n"
            "Le dossier doit inclure : CNI, attestation de résidence, projet détaillé, et dans certains cas "
            "une lettre de soutien d'un organisme d'appui (centre d'affaires, incubateur). "
            "Le délai de traitement est de 3 à 4 semaines. Ce financement est particulièrement adapté aux "
            "micro-entrepreneurs en dehors des grandes métropoles."
        ),
    },
    {
        "id": "startup-act-label",
        "title": "Startup Act — Labellisation et avantages fiscaux",
        "type": "legal_regulatory",
        "stage": ["ideation", "market_validation", "structuration", "fundraising"],
        "sector": ["cross-sector"],
        "score_dimensions": ["scalability", "green"],
        "url": "https://startup.gov.tn/fr/startup-act",
        "language": "fr",
        "last_verified": "2026-06-01",
        "provider": "Ministère des Technologies de la Communication — Startup Tunisia",
        "body": (
            "La loi Startup Act (Décret-loi n°2018-20) offre un cadre juridique et fiscal préférentiel aux "
            "jeunes entreprises innovantes tunisiennes. La labellisation Startup Act confère une exonération "
            "totale de l'impôt sur les bénéfices pendant 8 ans, une couverture sociale des fondateurs prise "
            "en charge par l'État pendant 3 ans, et un accès facilité aux aides publiques.\n\n"
            "Conditions d'éligibilité : entreprise créée depuis moins de 8 ans, caractère innovant du produit "
            "ou service (évalué par le comité), présence d'au moins un fondateur tunisien, capital inférieur "
            "à 15 millions TND. La startup doit démontrer un potentiel de croissance et une dimension "
            "numérique ou technologique.\n\n"
            "La procédure se fait entièrement en ligne via startup.gov.tn. Le comité se réunit tous les "
            "deux mois. Le label est renouvelable annuellement. En 2025, plus de 2 500 startups tunisiennes "
            "étaient labellisées Startup Act, dont 30 % dans le secteur fintech et 25 % dans la healthtech."
        ),
    },
    {
        "id": "rne-creation-entreprise",
        "title": "RNE — Création d'entreprise en ligne",
        "type": "legal_regulatory",
        "stage": ["ideation", "structuration"],
        "sector": ["cross-sector"],
        "score_dimensions": ["green"],
        "url": "https://www.registre-entreprises.tn",
        "language": "fr",
        "last_verified": "2026-06-01",
        "provider": "Registre National des Entreprises (RNE)",
        "body": (
            "Le Registre National des Entreprises (RNE) centralise l'immatriculation de toutes les personnes "
            "physiques et morales exerçant une activité économique en Tunisie. La création d'entreprise via "
            "le guichet unique RNE permet d'immatriculer une société en moins de 24 heures.\n\n"
            "Formes juridiques disponibles : Entreprise Individuelle (EI), SARL, SUARL, SA, SNC, SCS. "
            "La SUARL (Société Unipersonnelle à Responsabilité Limitée) est particulièrement adaptée aux "
            "fondateurs solo avec un capital minimum de 1 000 TND. La SARL standard requiert 1 à 50 associés "
            "et un capital minimum de 1 000 TND.\n\n"
            "Documents requis pour une SARL : statuts notariés, liste des gérants, attestation de dépôt de "
            "capital auprès d'une banque, copies CNI des associés. Le RNE délivre un Identifiant Unique (IU) "
            "servant d'identifiant fiscal et social. L'inscription à la CNSS est automatique pour les employeurs."
        ),
    },
    {
        "id": "esprit-incubator-ideation",
        "title": "Esprit Incubator — Accompagnement idéation",
        "type": "training_coaching",
        "stage": ["ideation"],
        "sector": ["digital-tech", "cross-sector"],
        "score_dimensions": ["commercial_offer", "innovation"],
        "url": "https://incubateur.esprit.tn",
        "language": "fr",
        "last_verified": "2026-06-01",
        "provider": "ESPRIT School of Engineering — Incubateur",
        "body": (
            "L'incubateur ESPRIT offre un programme d'accompagnement de 6 mois pour les porteurs de projets "
            "tech en phase d'idéation. Le programme comprend des ateliers hebdomadaires (design thinking, "
            "lean startup, validation client), un mentorat individuel avec des entrepreneurs expérimentés, "
            "et un accès aux laboratoires et infrastructure numérique de l'école.\n\n"
            "Les cohortes accueillent 15 à 20 projets par an. La sélection se base sur l'originalité de "
            "l'idée, la compétence technique de l'équipe et le potentiel de marché. Les startups sélectionnées "
            "bénéficient d'un espace de travail, d'une adresse domiciliataire, et d'un accès au réseau "
            "d'investisseurs partenaires.\n\n"
            "Le programme aboutit à un Demo Day devant investisseurs et partenaires institutionnels. "
            "Les startups les plus prometteuses sont recommandées pour une labellisation Startup Act et "
            "mises en contact avec les fonds d'amorçage Smart Capital et BFPME."
        ),
    },
    {
        "id": "beta-essid-training",
        "title": "Beta ESSID — Formation Entrepreneuriat et Business Planning",
        "type": "training_coaching",
        "stage": ["ideation", "market_validation"],
        "sector": ["cross-sector"],
        "score_dimensions": ["market", "commercial_offer"],
        "url": "https://beta.org.tn",
        "language": "fr",
        "last_verified": "2026-06-01",
        "provider": "BETA — Bureau Études et Travaux pour l'Animation",
        "body": (
            "BETA est un centre de formation entrepreneuriale reconnu par le Ministère de l'Emploi, proposant "
            "des modules certifiants en création d'entreprise, élaboration de business plan, et gestion de "
            "projet. Les formations durent 3 à 5 jours et sont subventionnées à 80 % pour les demandeurs "
            "d'emploi via le CNFCPP.\n\n"
            "Les modules les plus pertinents pour les startups en idéation incluent : Validation d'idée et "
            "étude de marché (2 jours), Élaboration d'un business plan financier (3 jours), Présentation "
            "aux investisseurs (1 jour). Les formations sont dispensées en arabe et en français.\n\n"
            "BETA collabore avec l'ANPE, les centres d'affaires régionaux et le réseau Enterprise Europe "
            "Network (EEN) Tunisia. L'organisme propose aussi un service d'accompagnement post-formation "
            "pour le montage des dossiers de financement APII et BTS."
        ),
    },
    {
        "id": "orange-fab-tunisia",
        "title": "Orange Fab Tunisia — Accélérateur de startups",
        "type": "networking_ecosystem",
        "stage": ["ideation", "market_validation", "structuration"],
        "sector": ["digital-tech", "cross-sector"],
        "score_dimensions": ["market", "commercial_offer"],
        "url": "https://www.orangefab.com/africa",
        "language": "fr",
        "last_verified": "2026-06-01",
        "provider": "Orange Tunisie",
        "body": (
            "Orange Fab Tunisia est le programme d'accélération de startups tech d'Orange Tunisie, organisé "
            "en deux cohortes annuelles de 10 startups chacune. Les startups sélectionnées bénéficient d'un "
            "soutien de 25 000 EUR en equity-free, d'un accès aux APIs d'Orange, et d'un mentorat par les "
            "équipes Orange Tunisie et Africa.\n\n"
            "Le programme dure 4 mois et inclut des ateliers thématiques (product-market fit, growth hacking, "
            "pitch investors), des sessions avec des experts Orange Consulting, et des opportunités de "
            "déploiement commercial avec Orange Business Tunisie. Les startups sont hébergées dans les "
            "locaux d'Orange à Tunis.\n\n"
            "Le programme est particulièrement adapté aux startups B2B tech, fintech, e-health et "
            "smart-city. Des partenariats existent avec les autres accélérateurs Orange Fab en Afrique "
            "(Maroc, Sénégal, Côte d'Ivoire) pour les startups ayant une ambition panafricaine."
        ),
    },
    {
        "id": "flat6labs-tunis",
        "title": "Flat6Labs Tunis — Accélérateur d'innovation",
        "type": "networking_ecosystem",
        "stage": ["ideation", "market_validation", "fundraising"],
        "sector": ["cross-sector"],
        "score_dimensions": ["market", "scalability"],
        "url": "https://www.flat6labs.com/cities/tunis/",
        "language": "fr",
        "last_verified": "2026-06-01",
        "provider": "Flat6Labs",
        "body": (
            "Flat6Labs Tunis est une antenne du réseau panafricain et moyen-oriental Flat6Labs, opérant depuis "
            "2014 à Tunis. Le programme d'accélération de 4 mois soutient 15 startups early-stage par cohorte "
            "avec un investissement initial de 25 000 USD contre 8-10 % de participation.\n\n"
            "Le programme comprend un curriculum structuré (lean startup, go-to-market, fundraising), "
            "un accès au réseau de 300+ mentors régionaux, et un Demo Day devant 100+ investisseurs "
            "locaux et internationaux. Flat6Labs Tunis a accompagné plus de 100 startups depuis sa création.\n\n"
            "Les secteurs prioritaires sont le fintech, l'edtech, la healthtech, l'agritech et le retail-tech. "
            "Les startups les plus avancées peuvent accéder au programme de suivi post-accélération et "
            "aux introductions aux LPs du fonds (Flat6Labs Fund II, cofondateurs régionaux)."
        ),
    },
    {
        "id": "afi-infrastructure-numerique",
        "title": "AFI — Infrastructure Numérique et Hébergement",
        "type": "technical_infrastructure",
        "stage": ["ideation", "market_validation", "structuration"],
        "sector": ["digital-tech", "cross-sector"],
        "score_dimensions": ["commercial_offer", "scalability"],
        "url": "https://www.afi.tn",
        "language": "fr",
        "last_verified": "2026-06-01",
        "provider": "Agence de Fonds d'Investissement (AFI)",
        "body": (
            "L'Agence de Fonds d'Investissement (AFI) met à disposition des startups tunisiennes une "
            "infrastructure cloud souveraine hébergée en Tunisie, conforme aux exigences de la loi 2004-63 "
            "sur la protection des données personnelles. Les serveurs sont localisés au Technoparc d'El Ghazala "
            "et à Borj Cedria.\n\n"
            "Les startups labellisées Startup Act bénéficient d'un accès préférentiel aux ressources cloud "
            "AFI : machines virtuelles, stockage objet, CDN, et services de messagerie sécurisée. "
            "Des plans spéciaux d'hébergement existent pour les éditeurs de logiciels SaaS.\n\n"
            "AFI propose également un accompagnement technique pour la migration vers le cloud et la "
            "sécurisation des données. Ce dispositif est particulièrement pertinent pour les startups "
            "traitant des données de santé, financières ou gouvernementales soumises à la localisation "
            "des données en Tunisie."
        ),
    },
    {
        "id": "open-data-tunisie",
        "title": "Portail Open Data Tunisie — Données publiques ouvertes",
        "type": "technical_infrastructure",
        "stage": ["ideation", "market_validation"],
        "sector": ["cross-sector", "agri-food", "digital-tech"],
        "score_dimensions": ["market", "innovation"],
        "url": "https://data.gov.tn",
        "language": "fr",
        "last_verified": "2026-06-01",
        "provider": "Présidence du Gouvernement Tunisien",
        "body": (
            "Le portail Open Data Tunisie (data.gov.tn) publie plus de 500 jeux de données publiques "
            "couvrant l'agriculture, la démographie, l'économie, l'éducation, la santé et le transport. "
            "Ces données sont gratuitement accessibles sous licence ouverte (CC-BY) et téléchargeables "
            "en format CSV, JSON et GeoJSON.\n\n"
            "Pour les startups en idéation, les datasets les plus utiles incluent : les données de recensement "
            "par gouvernorat, les statistiques d'exportation du CEPEX, les données cadastrales pour l'agritech, "
            "les indicateurs de santé du Ministère de la Santé, et les flux routiers. "
            "Des APIs REST sont disponibles pour les données à mise à jour fréquente.\n\n"
            "La plateforme est administrée par l'Unité de l'Administration Électronique (UAE). "
            "Des hackathons open data sont organisés deux fois par an, offrant aux startups l'opportunité "
            "de construire des POC sur des données gouvernementales et de pitcher devant des acteurs publics."
        ),
    },
    # ── MARKET_VALIDATION ─────────────────────────────────────────────────────
    {
        "id": "apii-etude-marche",
        "title": "APII — Subvention pour études de marché et faisabilité",
        "type": "financing",
        "stage": ["market_validation"],
        "sector": ["cross-sector"],
        "score_dimensions": ["market"],
        "url": "https://www.apii.tn/apii/faisabilite",
        "language": "fr",
        "last_verified": "2026-06-01",
        "provider": "APII — Agence de Promotion de l'Industrie et de l'Innovation",
        "body": (
            "L'APII finance jusqu'à 70 % du coût des études de marché et de faisabilité technique pour "
            "les projets innovants, dans la limite de 30 000 TND. Ce dispositif est accessible aux "
            "porteurs de projet individuels, aux startups en phase de validation et aux PME souhaitant "
            "explorer de nouveaux marchés.\n\n"
            "Les études éligibles couvrent : analyse de la demande et segmentation client, benchmark "
            "concurrentiel, faisabilité technique et prototypage, analyse réglementaire et juridique, "
            "et évaluation financière préliminaire. Les prestataires doivent être agréés par l'APII.\n\n"
            "La procédure de dépôt se fait en ligne. Un dossier type comprend : description du projet, "
            "termes de référence de l'étude, devis du prestataire, et CV du porteur. "
            "Le paiement est effectué directement au prestataire après validation des livrables."
        ),
    },
    {
        "id": "eu4innovation-seed",
        "title": "EU4Innovation — Soutien amorçage startups tunisiennes",
        "type": "financing",
        "stage": ["market_validation", "structuration", "fundraising"],
        "sector": ["cross-sector"],
        "score_dimensions": ["market", "innovation"],
        "url": "https://www.eu4innovation.tn",
        "language": "fr",
        "last_verified": "2026-06-01",
        "provider": "Union Européenne / ENPI",
        "body": (
            "Le programme EU4Innovation est un programme de l'Union Européenne visant à soutenir "
            "l'écosystème d'innovation tunisien. Il cofinance des programmes d'incubation, d'accélération "
            "et fournit des subventions directes aux startups tunisiennes en phase de validation ou de "
            "croissance, via ses opérateurs partenaires (incubateurs, centres d'affaires, APII).\n\n"
            "Les thématiques prioritaires financées incluent : économie verte, transformation numérique, "
            "économie circulaire, inclusion financière et emploi des jeunes. Les montants de subvention "
            "varient de 20 000 à 150 000 EUR selon la maturité du projet et le programme partenaire.\n\n"
            "Les startups tunisiennes peuvent accéder au programme via les appels à candidatures publiés "
            "sur le portail de la Délégation de l'UE en Tunisie. Un accompagnement au montage de dossier "
            "est fourni par le réseau Enterprise Europe Network (EEN) Tunisie."
        ),
    },
    {
        "id": "innorpi-depot-marque",
        "title": "INNORPI — Dépôt de marque et propriété intellectuelle",
        "type": "legal_regulatory",
        "stage": ["market_validation", "structuration", "launch_planning"],
        "sector": ["cross-sector"],
        "score_dimensions": ["innovation", "green"],
        "url": "https://www.innorpi.tn",
        "language": "fr",
        "last_verified": "2026-06-01",
        "provider": "Institut National de la Normalisation et de la Propriété Industrielle (INNORPI)",
        "body": (
            "L'INNORPI est l'organisme tunisien compétent pour l'enregistrement des marques, brevets, "
            "dessins et modèles industriels, et appellations d'origine. Le dépôt d'une marque nationale "
            "coûte 270 TND pour une classe de produits/services (+ 120 TND par classe supplémentaire) "
            "et confère une protection pour 10 ans renouvelable.\n\n"
            "La procédure de dépôt comprend : formulaire de dépôt, reproduction de la marque, liste des "
            "produits/services par classe internationale (classification de Nice), et paiement des taxes. "
            "Une recherche d'antériorité préalable est fortement recommandée pour éviter les conflits. "
            "Le délai d'enregistrement est d'environ 6 à 12 mois.\n\n"
            "La Tunisie est membre de l'OMPI et partie à l'Arrangement de Madrid, permettant l'extension "
            "internationale via le système de Madrid à 130+ pays. Pour les brevets d'invention, l'INNORPI "
            "collabore avec l'OAPI (Organisation Africaine de la Propriété Intellectuelle) pour la "
            "protection en Afrique francophone."
        ),
    },
    {
        "id": "code-protection-consommateur",
        "title": "Code de Protection du Consommateur — Conformité commerciale",
        "type": "legal_regulatory",
        "stage": ["market_validation", "launch_planning"],
        "sector": ["cross-sector"],
        "score_dimensions": ["green"],
        "url": "https://www.commerce.gov.tn/legislation",
        "language": "fr",
        "last_verified": "2026-06-01",
        "provider": "Ministère du Commerce et du Développement des Exportations",
        "body": (
            "La loi n°92-117 du 7 décembre 1992 relative à la protection du consommateur et ses textes "
            "d'application régissent les pratiques commerciales, la publicité et les garanties "
            "au consommateur en Tunisie. Les startups e-commerce et B2C doivent s'y conformer avant "
            "le lancement commercial.\n\n"
            "Obligations clés pour les startups : affichage obligatoire des prix TTC, mention des délais "
            "de livraison, droit de rétractation pour la vente à distance (7 jours), conditions générales "
            "de vente (CGV) conformes, et traitement des réclamations. Le Décret n°2011-4861 régit "
            "spécifiquement le commerce électronique.\n\n"
            "La Direction Générale du Commerce Intérieur (DGCI) est l'autorité de contrôle. "
            "Les sanctions pour non-conformité incluent des amendes allant de 500 à 50 000 TND. "
            "Pour les startups digital-tech, la conformité avec la loi 2004-63 sur la protection des "
            "données personnelles est également requise dès la collecte de données clients."
        ),
    },
    {
        "id": "business-model-canvas-formation",
        "title": "Formation Business Model Canvas et Lean Startup",
        "type": "training_coaching",
        "stage": ["ideation", "market_validation"],
        "sector": ["cross-sector"],
        "score_dimensions": ["market", "commercial_offer"],
        "url": "https://www.startuptn.tn/formation",
        "language": "fr",
        "last_verified": "2026-06-01",
        "provider": "StartupTn — Ministère des Technologies",
        "body": (
            "StartupTn propose des ateliers certifiants sur le Business Model Canvas (BMC) et les méthodes "
            "Lean Startup adaptées au contexte tunisien. Ces formations de 2 jours couvrent : value "
            "proposition design, identification des segments clients, cartographie des canaux de distribution, "
            "et modèles de revenus adaptés au marché MENA.\n\n"
            "La méthodologie Lean Startup (Build-Measure-Learn) est enseignée avec des cas d'usage "
            "de startups tunisiennes réussies. Les participants repartent avec un BMC complet, une "
            "proposition de valeur testée et un plan d'interviews clients structuré.\n\n"
            "Ces formations sont gratuites pour les startups labellisées Startup Act et leurs équipes. "
            "Des sessions avancées sur le Product-Market Fit (PMF) et le Customer Development sont "
            "organisées trimestriellement en partenariat avec des startups à succès (Paymee, Instadeep, "
            "Telnet) qui partagent leur expérience de validation marché."
        ),
    },
    {
        "id": "lean-startup-validation-marche",
        "title": "Ateliers Validation Marché — Interviews clients et MVP",
        "type": "training_coaching",
        "stage": ["market_validation"],
        "sector": ["cross-sector"],
        "score_dimensions": ["market", "commercial_offer"],
        "url": "https://www.tanit-incubateur.tn",
        "language": "fr",
        "last_verified": "2026-06-01",
        "provider": "TANIT Incubateur",
        "body": (
            "TANIT Incubateur propose un programme intensif de validation marché comprenant : techniques "
            "d'interview client (Jobs-to-be-Done, Five Whys), construction d'un MVP (Minimum Viable Product) "
            "en 2 semaines, et mesure quantitative du Product-Market Fit via des enquêtes NPS et entretiens "
            "de feedback.\n\n"
            "Le programme est conçu pour les startups ayant une hypothèse de valeur à valider avant d'investir "
            "dans le développement produit complet. Les outils enseignés incluent : Google Forms pour les "
            "sondages, Typeform pour les landing pages de test, et Notion pour la gestion des insights.\n\n"
            "TANIT collabore avec 15 grandes entreprises tunisiennes comme partenaires de test pour "
            "les startups B2B. Ce réseau permet aux startups d'accéder à des prospects qualifiés pour "
            "leurs interviews client et leurs pilotes. Les startups ayant complété ce programme ont en "
            "moyenne 3x plus de chances d'être acceptées dans les programmes d'accélération."
        ),
    },
    {
        "id": "reseau-entreprendre-tunisie",
        "title": "Réseau Entreprendre Tunisie — Mentorat et réseau",
        "type": "networking_ecosystem",
        "stage": ["market_validation", "structuration", "launch_planning"],
        "sector": ["cross-sector"],
        "score_dimensions": ["market", "scalability"],
        "url": "https://www.reseau-entreprendre.org/tunisie",
        "language": "fr",
        "last_verified": "2026-06-01",
        "provider": "Réseau Entreprendre Tunisie",
        "body": (
            "Réseau Entreprendre Tunisie est l'antenne locale du réseau international, regroupant "
            "100+ chefs d'entreprise bénévoles qui accompagnent des entrepreneurs dans leur développement. "
            "L'accompagnement est personnalisé, couvre 18 mois et est totalement gratuit.\n\n"
            "Chaque entrepreneur accompagné bénéficie d'un mentor dédié (chef d'entreprise expérimenté "
            "du même secteur), d'un accès au réseau des membres (partenariats commerciaux, introductions "
            "clients et investisseurs), et des ateliers thématiques mensuels. Le programme est accessible "
            "aux projets ayant un potentiel de création d'emplois.\n\n"
            "Le Réseau Entreprendre collabore avec le BFPME pour faciliter l'accès au financement de ses "
            "membres accompagnés. Les statistiques 2024 montrent que 85 % des entrepreneurs accompagnés "
            "sont encore en activité après 3 ans, vs 50 % pour la moyenne nationale."
        ),
    },
    {
        "id": "startuptn-ecosystem",
        "title": "StartupTn — Portail de l'écosystème startup tunisien",
        "type": "networking_ecosystem",
        "stage": ["market_validation", "structuration", "fundraising"],
        "sector": ["cross-sector"],
        "score_dimensions": ["market"],
        "url": "https://www.startuptn.tn",
        "language": "fr",
        "last_verified": "2026-06-01",
        "provider": "StartupTn — Ministère des Technologies de la Communication",
        "body": (
            "StartupTn est la plateforme officielle de l'écosystème startup tunisien. Elle répertorie "
            "l'ensemble des acteurs de l'écosystème : 50+ incubateurs et accélérateurs, 30+ fonds "
            "d'investissement, 200+ mentors, 1200+ startups actives. Le portail centralise les appels "
            "à candidatures et les opportunités de financement.\n\n"
            "Pour les startups en phase de validation marché, StartupTn offre : une base de données des "
            "acheteurs publics potentiels (marchés publics pour les startups), un outil de mise en "
            "relation avec des partenaires commerciaux, et un agenda des événements networking "
            "(conférences, hackathons, pitchs). Le portail est disponible en arabe, français et anglais.\n\n"
            "StartupTn administre également le label Startup Act et publie les statistiques de "
            "l'écosystème. En 2025, l'écosystème tunisien a enregistré 120M USD de levées de fonds, "
            "avec une concentration dans les secteurs fintech, agritech et edtech."
        ),
    },
    {
        "id": "google-for-startups-credits",
        "title": "Google for Startups — Crédits Cloud et IA",
        "type": "technical_infrastructure",
        "stage": ["market_validation", "structuration"],
        "sector": ["digital-tech", "cross-sector"],
        "score_dimensions": ["commercial_offer", "scalability"],
        "url": "https://cloud.google.com/startup",
        "language": "en",
        "last_verified": "2026-06-01",
        "provider": "Google",
        "body": (
            "Google for Startups Cloud Program provides up to $350,000 USD in Google Cloud credits "
            "over 2 years for eligible startups. Access includes GCP compute, BigQuery, Vertex AI, "
            "Firebase, and all Google Cloud services. Technical support includes one-on-one sessions "
            "with Google engineers and access to Google Workspace business tools.\n\n"
            "Tunisian startups can apply through the Google for Startups program or through partner "
            "accelerators (Flat6Labs, Orange Fab) that have direct referral access. Eligibility "
            "criteria: less than 10 years old, not yet Series B, working on technology products. "
            "AI startups may qualify for Google AI Startup Program with additional Vertex AI credits.\n\n"
            "The program also includes networking events, Demo Days, and introductions to Google's "
            "enterprise sales team for B2B startups. Google maintains a dedicated Startup Success "
            "team in EMEA (including the MENA region) that provides hands-on technical guidance "
            "for architecture, ML/AI implementation, and scaling."
        ),
    },
    {
        "id": "aws-activate",
        "title": "AWS Activate — Infrastructure cloud pour startups",
        "type": "technical_infrastructure",
        "stage": ["market_validation", "structuration", "launch_planning"],
        "sector": ["digital-tech", "cross-sector"],
        "score_dimensions": ["commercial_offer", "scalability"],
        "url": "https://aws.amazon.com/activate/",
        "language": "en",
        "last_verified": "2026-06-01",
        "provider": "Amazon Web Services (AWS)",
        "body": (
            "AWS Activate provides startups with up to $100,000 in AWS credits, technical support, "
            "and training. Tunisian startups can access the program through portfolio accelerators "
            "(Flat6Labs, BICT, Orange Fab) or via direct application. The program includes access "
            "to AWS Activate Console, business support plan, and 1:1 architectural sessions.\n\n"
            "Key services available include EC2 (compute), S3 (storage), RDS (managed databases), "
            "Lambda (serverless), SageMaker (ML), and Amazon Bedrock (foundation models). "
            "AWS has data centers in the Middle East (UAE) region which can serve Tunisian startups "
            "with low latency while meeting data residency requirements.\n\n"
            "For Tunisian B2B startups, AWS Marketplace listing is a growth channel to reach "
            "enterprise customers globally. AWS has a partner network in North Africa through "
            "resellers like MedConf and Alphatek that provide localized billing in TND."
        ),
    },
    # ── STRUCTURATION ─────────────────────────────────────────────────────────
    {
        "id": "bfpme-pme-loan",
        "title": "BFPME — Financement PME et startups en croissance",
        "type": "financing",
        "stage": ["structuration", "fundraising", "growth"],
        "sector": ["cross-sector"],
        "score_dimensions": ["scalability"],
        "url": "https://www.bfpme.com.tn",
        "language": "fr",
        "last_verified": "2026-06-01",
        "provider": "Banque de Financement des Petites et Moyennes Entreprises (BFPME)",
        "body": (
            "La BFPME est une banque publique spécialisée dans le financement des PME et startups "
            "tunisiennes. Elle propose des crédits d'investissement à moyen et long terme allant de "
            "100 000 à 5 millions TND, avec des taux bonifiés (TMM + 3 % à 5 %) et des garanties "
            "publiques via le SOTUGAR.\n\n"
            "Produits disponibles : crédit d'investissement (équipements, immobilier d'exploitation), "
            "crédit de fonctionnement (BFR), crédit-bail (leasing), et prise de participation en "
            "fonds propres (SICAR affiliées BFPME). La durée de remboursement peut aller jusqu'à "
            "15 ans pour l'immobilier et 7 ans pour les équipements.\n\n"
            "Les startups labellisées Startup Act bénéficient d'une procédure accélérée et d'un "
            "interlocuteur dédié. La BFPME dispose d'agences régionales à Tunis, Sfax, Sousse, "
            "Bizerte et Gafsa. Le délai moyen de traitement d'un dossier est de 6 à 8 semaines."
        ),
    },
    {
        "id": "sicar-capital-risque",
        "title": "SICAR — Sociétés d'Investissement à Capital Risque",
        "type": "financing",
        "stage": ["structuration", "fundraising"],
        "sector": ["cross-sector"],
        "score_dimensions": ["scalability"],
        "url": "https://www.cmf.org.tn/sicar",
        "language": "fr",
        "last_verified": "2026-06-01",
        "provider": "Conseil du Marché Financier (CMF) Tunisie",
        "body": (
            "Les SICAR (Sociétés d'Investissement à Capital Risque) sont des véhicules d'investissement "
            "tunisiens agréés par le Conseil du Marché Financier (CMF). Elles investissent en fonds "
            "propres dans des PME et startups tunisiennes, typiquement pour des montants de 200 000 à "
            "2 millions TND contre des participations de 15 % à 40 %.\n\n"
            "Les principales SICAR actives en Tunisie incluent : Tuninvest/AfricInvest, Investia, "
            "Siparex Maghreb, BNA Capital, Amen Invest et UIB Capital. La plupart ont des mandats "
            "sectoriels (agritech, fintech, industrie) et des critères d'investissement différenciés.\n\n"
            "Les SICAR bénéficient d'avantages fiscaux substantiels (déductibilité des investissements "
            "à 65 %) ce qui attire les investisseurs privés tunisiens. Pour la startup, l'entrée d'une "
            "SICAR au capital est un signal fort pour les partenaires bancaires et les clients B2B. "
            "Les sorties se font généralement par cession à 5-7 ans."
        ),
    },
    {
        "id": "startup-act-avantages-fiscaux",
        "title": "Startup Act — Détail des avantages sociaux et fiscaux",
        "type": "legal_regulatory",
        "stage": ["structuration", "fundraising"],
        "sector": ["cross-sector"],
        "score_dimensions": ["scalability", "green"],
        "url": "https://startup.gov.tn/fr/avantages",
        "language": "fr",
        "last_verified": "2026-06-01",
        "provider": "Ministère des Technologies de la Communication — Startup Tunisia",
        "body": (
            "Le Startup Act confère aux startups labellisées un ensemble d'avantages fiscaux et sociaux "
            "exceptionnels en Tunisie. Sur le plan fiscal : exonération totale de l'impôt sur les "
            "sociétés (IS) pendant 8 ans, exonération de la TVA sur les services rendus à l'étranger, "
            "et droits d'enregistrement réduits pour les augmentations de capital.\n\n"
            "Sur le plan social : prise en charge par l'État des cotisations patronales CNSS pendant "
            "3 ans pour les fondateurs salariés de leur startup, et maintien des droits à l'assurance "
            "chômage pour les salariés qui quittent un CDI pour créer une startup.\n\n"
            "Avantages financiers additionnels : accès prioritaire aux marchés publics (30 % des marchés "
            "innovants réservés aux startups), possibilité d'ouverture de comptes en devises étrangères "
            "(USD, EUR) sans autorisation de la BCT, et transfert libre de dividendes pour les actionnaires "
            "étrangers. Ces avantages s'appliquent pendant toute la durée de validité du label."
        ),
    },
    {
        "id": "loi-2004-63-donnees-personnelles",
        "title": "Loi Organique 2004-63 — Protection des données personnelles",
        "type": "legal_regulatory",
        "stage": ["structuration", "launch_planning", "growth"],
        "sector": ["digital-tech", "cross-sector"],
        "score_dimensions": ["green"],
        "url": "https://www.inpdp.nat.tn/legislation",
        "language": "fr",
        "last_verified": "2026-06-01",
        "provider": "Instance Nationale de Protection des Données Personnelles (INPDP)",
        "body": (
            "La loi organique tunisienne n°2004-63 du 27 juillet 2004 constitue le cadre juridique de "
            "référence pour la protection des données personnelles en Tunisie. Toute application "
            "collectant des données d'utilisateurs tunisiens doit déclarer ses traitements auprès de "
            "l'INPDP (Instance Nationale de Protection des Données Personnelles).\n\n"
            "Obligations principales : déclaration préalable des traitements de données, information "
            "des personnes concernées, droit d'accès et de rectification, sécurisation des données "
            "(mesures techniques et organisationnelles), et localisation des données sensibles en Tunisie. "
            "Les transferts de données vers des pays tiers nécessitent une autorisation de l'INPDP.\n\n"
            "Pour les startups digital-tech, la conformité inclut : politique de confidentialité "
            "publiée sur le site/application, consentement explicite pour la collecte, journalisation "
            "des accès aux données personnelles, et nomination d'un DPO si le traitement est à grande "
            "échelle. Les sanctions pour violation vont de 1 000 à 10 000 TND d'amende."
        ),
    },
    {
        "id": "iace-formation-gestion",
        "title": "IACE — Formation Gestion et Finance d'Entreprise",
        "type": "training_coaching",
        "stage": ["structuration", "fundraising"],
        "sector": ["cross-sector"],
        "score_dimensions": ["scalability"],
        "url": "https://www.iace.tn/formation",
        "language": "fr",
        "last_verified": "2026-06-01",
        "provider": "Institut Arabe des Chefs d'Entreprises (IACE)",
        "body": (
            "L'IACE propose des programmes de formation certifiants pour les dirigeants de PME et startups "
            "tunisiennes. Les modules les plus pertinents pour les startups en phase de structuration : "
            "Finance d'entreprise pour non-financiers (2 jours), Contrôle de gestion et tableaux de bord "
            "(3 jours), et Levée de fonds et relations investisseurs (1 jour).\n\n"
            "La formation en finance d'entreprise couvre : lecture des états financiers, analyse du "
            "cash-flow, construction d'un budget prévisionnel, et indicateurs clés (CAC, LTV, churn rate). "
            "Ces compétences sont indispensables pour les fondateurs non financiers avant de rencontrer "
            "des investisseurs ou des banquiers.\n\n"
            "Les formations sont éligibles aux financements de la CNFCPP (Centre National de Formation "
            "Continue et de Promotion Professionnelle) qui peut rembourser jusqu'à 80 % des frais. "
            "L'IACE organise également des conférences annuelles (Journées de l'Entreprise) qui sont "
            "des événements networking incontournables de l'écosystème business tunisien."
        ),
    },
    {
        "id": "cgpme-management-training",
        "title": "CGPME Tunisie — Programme Management et Leadership PME",
        "type": "training_coaching",
        "stage": ["structuration", "growth"],
        "sector": ["cross-sector"],
        "score_dimensions": ["scalability"],
        "url": "https://www.cgpme.tn/formation",
        "language": "fr",
        "last_verified": "2026-06-01",
        "provider": "Confédération Générale des Petites et Moyennes Entreprises (CGPME)",
        "body": (
            "La CGPME Tunisie propose des programmes de développement managérial adaptés aux besoins "
            "des dirigeants de PME et de startups en croissance. Le programme Executive Leadership "
            "PME (6 modules de 2 jours) couvre : leadership situationnel, gestion d'équipes, pilotage "
            "de la performance, et transition vers une organisation scalable.\n\n"
            "Pour les startups qui recrutent leurs premières équipes, le module Recrutement et intégration "
            "est particulièrement utile : définition des fiches de poste, processus d'entretien structuré, "
            "onboarding, et conformité avec le Code du Travail tunisien.\n\n"
            "La CGPME organise également des petits-déjeuners networking mensuels réunissant 50-100 "
            "dirigeants de PME par wilaya. Ces événements sont des opportunités de génération de leads "
            "B2B pour les startups en phase de lancement. La CGPME dispose d'antennes dans 18 wilayas."
        ),
    },
    {
        "id": "conect-reseau-entreprises",
        "title": "CONECT — Confédération des Entreprises Citoyennes de Tunisie",
        "type": "networking_ecosystem",
        "stage": ["structuration", "launch_planning", "growth"],
        "sector": ["cross-sector"],
        "score_dimensions": ["market", "scalability"],
        "url": "https://www.conect.org.tn",
        "language": "fr",
        "last_verified": "2026-06-01",
        "provider": "CONECT — Confédération des Entreprises Citoyennes de Tunisie",
        "body": (
            "CONECT est la première organisation patronale à orientation RSE en Tunisie, regroupant "
            "1 500+ entreprises membres, dont une part croissante de startups et PME innovantes. "
            "L'adhésion coûte 500 à 2 000 TND/an selon la taille de l'entreprise.\n\n"
            "Les bénéfices pour les startups membres incluent : accès à la base de données des membres "
            "pour du business development B2B, représentation auprès des instances gouvernementales, "
            "participation aux délégations commerciales à l'international, et accès à des contrats "
            "cadres d'achats collectifs (assurances, logiciels, services).\n\n"
            "CONECT organise des rencontres d'affaires B2B intersectorielles deux fois par an "
            "(600+ participants) et des missions économiques vers la France, l'Allemagne et les pays "
            "du Golfe. Pour les startups B2B cherchant leurs premiers grands comptes tunisiens, "
            "le réseau CONECT est une voie d'accès privilégiée."
        ),
    },
    {
        "id": "chambre-commerce-tunisie",
        "title": "Chambre de Commerce et d'Industrie de Tunisie",
        "type": "networking_ecosystem",
        "stage": ["structuration", "launch_planning", "growth"],
        "sector": ["cross-sector", "industry"],
        "score_dimensions": ["market"],
        "url": "https://www.ccit.tn",
        "language": "fr",
        "last_verified": "2026-06-01",
        "provider": "Chambre de Commerce et d'Industrie de Tunisie (CCIT)",
        "body": (
            "La Chambre de Commerce et d'Industrie de Tunisie (CCIT) fédère 24 chambres régionales "
            "et représente plus de 150 000 entreprises. Elle fournit des services essentiels pour les "
            "startups : légalisation de documents commerciaux, certificats d'origine, attestations "
            "d'affiliation, et accès à la base de données des entreprises tunisiennes.\n\n"
            "Services spécifiques aux startups : accompagnement à l'export (formation, missions), "
            "médiation commerciale, arbitrage commercial, et mise en relation avec les chambres "
            "bilatérales (franco-tunisienne, germano-tunisienne, italo-tunisienne). La CCIT édite "
            "un répertoire des importateurs/distributeurs par secteur.\n\n"
            "La CCIT dispose d'un Centre de Formation et d'Information qui propose des sessions sur "
            "le droit commercial tunisien, la facturation internationale et les Incoterms. Pour les "
            "startups visant l'export, une adhésion à la chambre bilatérale correspondant au marché "
            "cible est recommandée."
        ),
    },
    {
        "id": "innorpi-brevet-invention",
        "title": "INNORPI — Brevet d'invention et protection logicielle",
        "type": "technical_infrastructure",
        "stage": ["structuration", "fundraising"],
        "sector": ["cross-sector", "digital-tech"],
        "score_dimensions": ["innovation"],
        "url": "https://www.innorpi.tn/brevets",
        "language": "fr",
        "last_verified": "2026-06-01",
        "provider": "INNORPI",
        "body": (
            "L'INNORPI gère le système des brevets d'invention en Tunisie. Le dépôt d'un brevet "
            "national coûte 450 TND et confère une protection de 20 ans. Les logiciels sont protégés "
            "en Tunisie via le droit d'auteur (OTDAV) plutôt que par le brevet, mais les procédés "
            "techniques associés à un logiciel peuvent être brevetés.\n\n"
            "L'INNORPI propose un service d'assistance au dépôt pour les inventeurs individuels et "
            "les startups : recherche préalable de brevetabilité, rédaction des revendications, "
            "et accompagnement pendant l'examen. Un brevet provisoire (dépôt prioritaire) peut être "
            "obtenu en 24h pour 150 TND, fixant la date de priorité avant la divulgation.\n\n"
            "La Tunisie est membre du Traité de Coopération en matière de Brevets (PCT), permettant "
            "une protection internationale via une procédure unifiée. Pour les startups avec des "
            "innovations brevetables, le dépôt PCT doit être initié dans les 12 mois suivant le "
            "dépôt national pour préserver les droits à l'international."
        ),
    },
    {
        "id": "cetime-certification-industrie",
        "title": "CETIME — Centre Technique des Industries Mécaniques et Électriques",
        "type": "technical_infrastructure",
        "stage": ["structuration", "launch_planning"],
        "sector": ["industry", "cross-sector"],
        "score_dimensions": ["innovation", "green"],
        "url": "https://www.cetime.ind.tn",
        "language": "fr",
        "last_verified": "2026-06-01",
        "provider": "CETIME",
        "body": (
            "Le CETIME est le centre technique sectoriel spécialisé dans les industries mécaniques, "
            "électriques et électroniques en Tunisie. Il propose des services de certification, "
            "d'essais et de métrologie pour les startups deep-tech et industrielles.\n\n"
            "Services clés pour les startups : certification de conformité CE (obligatoire pour l'export "
            "vers l'UE), essais de performance et de durabilité des équipements, étalonnage des "
            "instruments de mesure, et assistance à la mise en place d'un système qualité ISO 9001.\n\n"
            "Le CETIME dispose d'un laboratoire accrédité TUNAC permettant d'émettre des rapports "
            "d'essai reconnus internationalement. Pour les startups hardware et IoT, l'obtention "
            "des certifications CE et RoHS via le CETIME est souvent moins coûteuse que de passer "
            "par des laboratoires européens."
        ),
    },
    # ── FUNDRAISING ───────────────────────────────────────────────────────────
    {
        "id": "smart-capital-cdc",
        "title": "Smart Capital / CDC Tunisie — Capital-risque public",
        "type": "financing",
        "stage": ["fundraising", "growth"],
        "sector": ["cross-sector"],
        "score_dimensions": ["scalability"],
        "url": "https://smartcapital.tn",
        "language": "fr",
        "last_verified": "2026-06-01",
        "provider": "Smart Capital — Caisse des Dépôts et Consignations Tunisie",
        "body": (
            "Smart Capital est le fonds de capital-risque public tunisien géré par la Caisse des Dépôts "
            "et Consignations (CDC). Il investit en equity dans des startups et scale-ups tunisiennes "
            "avec des tickets allant de 500 000 à 5 millions TND, en co-investissement avec des fonds "
            "privés (minimum 1:1 co-investissement).\n\n"
            "Smart Capital gère plusieurs fonds thématiques : Fonds d'Amorçage Startup Act (FASA) pour "
            "les startups labellisées en amorçage (200K-1M TND), et le Fonds de Fonds qui co-investit "
            "avec des fonds VC privés tunisiens et régionaux. Les conditions d'investissement sont "
            "alignées avec les standards du marché (term sheet, tag-along, drag-along).\n\n"
            "Pour accéder à Smart Capital, la startup doit être labellisée Startup Act, avoir 2+ années "
            "d'existence, et présenter un plan de croissance documenté. Le processus d'instruction "
            "dure 3 à 4 mois. Smart Capital peut octroyer un avis de principe pour faciliter les "
            "négociations avec les co-investisseurs privés."
        ),
    },
    {
        "id": "africinvest-fonds",
        "title": "AfricInvest — Fonds d'investissement MENA et Afrique",
        "type": "financing",
        "stage": ["fundraising", "growth"],
        "sector": ["cross-sector"],
        "score_dimensions": ["scalability"],
        "url": "https://www.africinvest.com",
        "language": "fr",
        "last_verified": "2026-06-01",
        "provider": "AfricInvest Group",
        "body": (
            "AfricInvest est un gestionnaire de fonds d'investissement panafricain basé à Tunis, gérant "
            "2+ milliards USD dans 9 fonds actifs couvrant l'Afrique et le Moyen-Orient. Il représente "
            "l'un des principaux fonds de private equity/VC accessibles aux startups tunisiennes en "
            "phase de scale.\n\n"
            "AfricInvest réalise des investissements en capital de croissance (tickets 2-20M USD) dans "
            "des PME et startups à fort potentiel dans les secteurs : fintech, santé, éducation, agri-food, "
            "industrie et services financiers. Les critères d'investissement incluent : revenus récurrents "
            "démontrés, équipe de management expérimentée, et potentiel d'expansion régionale.\n\n"
            "Pour accéder à AfricInvest, les startups doivent être introduites par des partenaires de "
            "l'écosystème (incubateurs, accélérateurs, conseils M&A) ou répondre aux appels à projets "
            "sectoriels. AfricInvest dispose d'équipes sectorielles à Tunis, Abidjan, Nairobi et Casablanca."
        ),
    },
    {
        "id": "loi-investissement-2016",
        "title": "Loi d'Investissement 2016 — Cadre et incitations",
        "type": "legal_regulatory",
        "stage": ["fundraising", "structuration"],
        "sector": ["cross-sector"],
        "score_dimensions": ["scalability", "green"],
        "url": "https://www.investintunisia.tn/legislation",
        "language": "fr",
        "last_verified": "2026-06-01",
        "provider": "Agence de Promotion de l'Investissement Extérieur (FIPA)",
        "body": (
            "La loi n°2016-71 du 30 septembre 2016 constitue le cadre fondamental de l'investissement "
            "en Tunisie. Elle prévoit des incitations fiscales substantielles pour les investissements "
            "dans les secteurs prioritaires et les zones de développement régional.\n\n"
            "Incitations principales : déduction de 35 % des revenus/bénéfices investis (Prime Investissement), "
            "prise en charge par l'État d'une partie des dépenses d'infrastructure (jusqu'à 25 % du coût), "
            "et exonération des droits de douane sur les équipements importés. Des incitations additionnelles "
            "s'appliquent dans les zones de développement régional (Gafsa, Kasserine, Sidi Bouzid).\n\n"
            "Pour les startups cherchant à lever des fonds étrangers, la loi facilite les investissements "
            "directs étrangers (IDE) avec rapatriement libre des bénéfices et du capital. Les investissements "
            "dans les secteurs de haute technologie bénéficient d'incitations renforcées. La FIPA "
            "(Foreign Investment Promotion Agency) accompagne gratuitement les investisseurs étrangers "
            "dans leurs démarches administratives."
        ),
    },
    {
        "id": "startup-act-fonds-amorçage",
        "title": "Startup Act — Fonds d'amorçage et accès au financement public",
        "type": "legal_regulatory",
        "stage": ["fundraising"],
        "sector": ["cross-sector"],
        "score_dimensions": ["scalability"],
        "url": "https://startup.gov.tn/fr/financement",
        "language": "fr",
        "last_verified": "2026-06-01",
        "provider": "Startup Tunisia",
        "body": (
            "Le Startup Act prévoit un mécanisme de fonds d'amorçage public (FASA — Fonds d'Amorçage "
            "Startup Act) géré par Smart Capital/CDC. Ce fonds investit entre 200 000 et 1 million TND "
            "en equity dans des startups labellisées en amorçage, avec des conditions préférentielles "
            "(valorisation sans haircut, clause anti-dilution pour les fondateurs).\n\n"
            "Le processus d'accès au FASA comprend : dossier de candidature via startup.gov.tn, "
            "présentation devant le comité d'investissement Smart Capital, et signature du pacte "
            "d'actionnaires standardisé Startup Act. Le délai d'instruction est de 2 à 3 mois.\n\n"
            "Avantage additionnel : les investisseurs privés co-investissant avec le FASA bénéficient "
            "d'une réduction fiscale de 65 % sur leur investissement. Cela incite les SICAR et business "
            "angels tunisiens à co-investir dans les rondes d'amorçage des startups labellisées."
        ),
    },
    {
        "id": "formation-pitch-investisseurs",
        "title": "Formation Pitch Investisseurs et Préparation Levée de Fonds",
        "type": "training_coaching",
        "stage": ["fundraising"],
        "sector": ["cross-sector"],
        "score_dimensions": ["scalability", "market"],
        "url": "https://www.tn-angels.com/formation",
        "language": "fr",
        "last_verified": "2026-06-01",
        "provider": "Carthage Business Angels / TN Angels",
        "body": (
            "Les associations de business angels tunisiennes (Carthage Business Angels, TN Angels) "
            "proposent des workshops intensifs de préparation aux levées de fonds : construction du "
            "pitch deck (12 slides), préparation aux questions investisseurs difficiles, négociation "
            "des term sheets, et due diligence documentaire.\n\n"
            "Le curriculum couvre les 12 slides clés du pitch deck investisseur : problème, solution, "
            "marché (TAM/SAM/SOM), business model, traction, équipe, compétition, plan financier "
            "(P&L 3 ans, cash-burn, runway), besoin de financement et utilisation des fonds. "
            "Des sessions de pitch simulé devant de vrais investisseurs sont organisées.\n\n"
            "Pour la due diligence, la formation porte sur la constitution de la data room : cap table, "
            "contrats clients, PI (brevets, marques), état financier audité, et contrats de travail "
            "des fondateurs. Les participants qui réussissent le programme accèdent au réseau d'investisseurs "
            "des associations partenaires."
        ),
    },
    {
        "id": "modelisation-financiere",
        "title": "Formation Modélisation Financière et Valorisation Startup",
        "type": "training_coaching",
        "stage": ["fundraising", "structuration"],
        "sector": ["cross-sector"],
        "score_dimensions": ["scalability"],
        "url": "https://www.iace.tn/finance-startup",
        "language": "fr",
        "last_verified": "2026-06-01",
        "provider": "IACE",
        "body": (
            "L'IACE propose un module avancé de modélisation financière pour startups couvrant : "
            "construction d'un modèle financier SaaS sur 3 ans (revenus récurrents ARR/MRR, churn, "
            "expansion), calcul des métriques clés (CAC, LTV, LTV/CAC ratio, payback period), "
            "et méthodes de valorisation (DCF, multiple de revenus, comparable transactions).\n\n"
            "La formation inclut des exercices pratiques sur Excel/Google Sheets avec des templates "
            "pré-construits pour les principaux modèles de revenus (SaaS, marketplace, e-commerce, "
            "hardware+services). Les participants apprennent à construire des scénarios (bear/base/bull) "
            "et à les défendre devant investisseurs.\n\n"
            "Le module Valorisation couvre les benchmarks de multiples tunisiens et africains, "
            "la négociation de la pre-money valuation, et les mécanismes anti-dilution (ratchets, "
            "préférences de liquidation). Ce module est indispensable avant toute levée de fonds auprès "
            "de SICAR, de Smart Capital ou d'investisseurs internationaux."
        ),
    },
    {
        "id": "tunisia-startup-summit",
        "title": "Tunisia Startup Summit — Rencontre Investisseurs et Startups",
        "type": "networking_ecosystem",
        "stage": ["fundraising", "growth"],
        "sector": ["cross-sector"],
        "score_dimensions": ["market", "scalability"],
        "url": "https://www.tunisia-startup-summit.tn",
        "language": "fr",
        "last_verified": "2026-06-01",
        "provider": "Tunisia Startup Summit Organizing Committee",
        "body": (
            "Le Tunisia Startup Summit est le principal événement annuel de l'écosystème startup tunisien, "
            "réunissant 2 000+ participants dont 200+ investisseurs (VC, PE, business angels, fonds "
            "souverains), 500+ startups et 100+ partenaires corporates. L'événement se tient à Tunis "
            "chaque année en novembre.\n\n"
            "Format de l'événement : conférences keynote par des entrepreneurs et investisseurs de "
            "renommée internationale, sessions de pitch compétition (prix de 50 000 TND), rencontres "
            "B2B structurées entre startups et investisseurs (30 min chacune), et workshop tracks "
            "thématiques. Les startups participantes doivent s'inscrire 3 mois à l'avance.\n\n"
            "Le TSS est une vitrine incontournable pour les startups en phase de fundraising. "
            "Les startups sélectionnées pour pitcher accèdent à une couverture média dans les "
            "journaux économiques tunisiens (L'Economiste Maghrébin, La Presse Economique) et "
            "les médias spécialisés régionaux (Wamda, Disrupt Africa)."
        ),
    },
    {
        "id": "africarena-tunis",
        "title": "AfricArena Tunis — Réseau investisseurs panafricain",
        "type": "networking_ecosystem",
        "stage": ["fundraising", "growth"],
        "sector": ["cross-sector"],
        "score_dimensions": ["market", "scalability"],
        "url": "https://www.africarena.com/tunis",
        "language": "en",
        "last_verified": "2026-06-01",
        "provider": "AfricArena",
        "body": (
            "AfricArena is a pan-African tech and startup platform connecting African startups with "
            "global investors. The annual Tunis edition brings together 500+ participants including "
            "investors from Europe, Middle East, and North America specifically interested in the "
            "North African startup ecosystem.\n\n"
            "The event features a startup competition (10 selected to pitch), investor roundtables, "
            "and 1:1 meetings organized by the AfricArena team. Winners gain visibility in the "
            "AfricArena global startup database (used by 200+ VC funds) and media coverage across "
            "AfricArena's platform (300,000+ monthly visitors).\n\n"
            "AfricArena has facilitated over $500M USD in investments across African startups since 2018. "
            "Tunisian alumni include Instadeep (acquired by BioNTech), Expensya, and Paymee. "
            "For Tunisian startups targeting international expansion, AfricArena's network in "
            "South Africa, Kenya, and Côte d'Ivoire provides warm introductions to regional investors."
        ),
    },
    {
        "id": "virtual-data-room",
        "title": "Virtual Data Room — Outils de due diligence investisseurs",
        "type": "technical_infrastructure",
        "stage": ["fundraising"],
        "sector": ["cross-sector"],
        "score_dimensions": ["scalability", "green"],
        "url": "https://www.notion.so/fundraising-templates",
        "language": "fr",
        "last_verified": "2026-06-01",
        "provider": "Notion / Docsend / Caplinked",
        "body": (
            "Une Virtual Data Room (VDR) est l'outil indispensable pour les startups en levée de fonds. "
            "Elle centralise tous les documents requis par les investisseurs lors de la due diligence : "
            "cap table, contrats fondateurs (SHA, term sheets), états financiers (3 ans si disponibles), "
            "liste des brevets et marques, contrats clients clés, et prévisions financières.\n\n"
            "Outils recommandés par ordre de coût croissant : Notion (gratuit, moins sécurisé), "
            "Docsend (99 USD/mois, analytics de lecture), Caplinked (149 USD/mois, VDR professionnel), "
            "et Intralinks ou Datasite pour les séries B+. Pour les rondes seed, un Notion bien organisé "
            "avec partage par lien contrôlé suffit généralement.\n\n"
            "Structure recommandée de la data room pour une levée seed tunisienne : (1) Pitch deck, "
            "(2) Modèle financier, (3) Statuts et RNE, (4) Cap table, (5) Pipeline commercial (CRM export), "
            "(6) PI (brevets/marques INNORPI), (7) Conformité INPDP, (8) Contrats clés, (9) CVs fondateurs."
        ),
    },
    {
        "id": "cap-table-management",
        "title": "Gestion Cap Table — Outils pour startups tunisiennes",
        "type": "technical_infrastructure",
        "stage": ["fundraising", "structuration"],
        "sector": ["cross-sector"],
        "score_dimensions": ["scalability"],
        "url": "https://carta.com/startups",
        "language": "fr",
        "last_verified": "2026-06-01",
        "provider": "Carta / Pulley / Spreadsheet template",
        "body": (
            "La gestion du cap table (tableau de capitalisation) est critique pour les startups en "
            "phase de levée de fonds. Elle doit refléter précisément la structure actionnariale : "
            "fondateurs, investisseurs, ESOP pool, et convertibles en circulation.\n\n"
            "Outils disponibles : Carta (leader mondial, 2 000 USD/an pour les startups, gère les "
            "BSPCEs et options), Pulley (moins cher, bon pour les startups early-stage), ou un "
            "template Excel/Google Sheets standard (gratuit, suffisant jusqu'à la série A). "
            "Pour les startups tunisiennes, un template adapté au droit tunisien des sociétés "
            "(SARL/SA) est disponible via le réseau Startup Act.\n\n"
            "Les éléments à documenter : nombre total d'actions émises, prix par action à chaque "
            "tour, participation de chaque actionnaire en %, droits préférentiels (liquidation "
            "preference, anti-dilution), et réserve pour le plan d'options salariés (ESOP). "
            "Une cap table non à jour est un red flag majeur lors d'une due diligence investisseur."
        ),
    },
    # ── LAUNCH_PLANNING ───────────────────────────────────────────────────────
    {
        "id": "apii-export-support",
        "title": "APII — Programme de soutien à l'export et à l'internationalisation",
        "type": "financing",
        "stage": ["launch_planning", "growth"],
        "sector": ["cross-sector"],
        "score_dimensions": ["market", "scalability"],
        "url": "https://www.apii.tn/apii/export",
        "language": "fr",
        "last_verified": "2026-06-01",
        "provider": "APII",
        "body": (
            "L'APII cofinance les activités d'internationalisation des startups et PME tunisiennes via "
            "plusieurs dispositifs : Prime à la Participation aux Foires Internationales (jusqu'à "
            "5 000 TND/an), Prime au Développement de Sites Web en Langues Étrangères (70 %), et "
            "soutien aux études de marchés étrangers (70 %).\n\n"
            "Le dispositif Exportateurs Confirmés soutient les startups SaaS qui génèrent plus de "
            "50 % de leurs revenus à l'export : accès au régime offshore, transfert libre de devises, "
            "et exonération de TVA sur les exportations de services. Pour les startups digital-tech, "
            "les services exportés (SaaS, APIs, consulting IT) sont automatiquement exonérés de TVA.\n\n"
            "L'APII coordonne avec le CEPEX pour les missions de prospection à l'étranger. "
            "Les marchés prioritaires pour les startups tunisiennes en 2025-2026 sont : France, "
            "Allemagne, Pays du Golfe (EAU, Arabie Saoudite) et Afrique Sub-Saharienne francophone."
        ),
    },
    {
        "id": "foprodi-expansion",
        "title": "FOPRODI — Fonds de Promotion et de Décentralisation Industrielle",
        "type": "financing",
        "stage": ["launch_planning", "structuration"],
        "sector": ["industry", "agri-food", "cross-sector"],
        "score_dimensions": ["scalability"],
        "url": "https://www.apii.tn/apii/foprodi",
        "language": "fr",
        "last_verified": "2026-06-01",
        "provider": "APII",
        "body": (
            "Le FOPRODI (Fonds de Promotion et de Décentralisation Industrielle) est un fonds de "
            "capital-risque public géré par l'APII, dédié aux primo-créateurs et porteurs de projets "
            "en dehors du Grand Tunis. Il participe en fonds propres à hauteur de 30-40 % du capital "
            "d'une SARL nouvellement créée, pour des projets de 50 000 à 1 million TND.\n\n"
            "Conditions d'éligibilité : porteur de projet primo-créateur (sans expérience entrepreneuriale "
            "antérieure significative), projet dans un secteur productif (industrie, artisanat, services "
            "à l'industrie), localisation hors Grand Tunis de préférence. Le FOPRODI peut compléter un "
            "financement BTS/BFPME pour atteindre le montage financier complet.\n\n"
            "La sortie du FOPRODI du capital est prévue entre 3 et 7 ans, par rachat préférentiel par "
            "les fondateurs à une valeur conventionnée. Ce mécanisme est particulièrement adapté aux "
            "startups industrielles et agritech des régions intérieures de la Tunisie."
        ),
    },
    {
        "id": "cnss-premier-recrutement",
        "title": "CNSS — Obligations sociales pour le premier recrutement",
        "type": "legal_regulatory",
        "stage": ["launch_planning", "structuration"],
        "sector": ["cross-sector"],
        "score_dimensions": ["scalability", "green"],
        "url": "https://www.cnss.tn",
        "language": "fr",
        "last_verified": "2026-06-01",
        "provider": "Caisse Nationale de Sécurité Sociale (CNSS)",
        "body": (
            "La Caisse Nationale de Sécurité Sociale (CNSS) gère l'affiliation et le recouvrement "
            "des cotisations sociales pour les employeurs tunisiens. Dès le premier recrutement, "
            "l'employeur doit s'affilier à la CNSS et déclarer chaque salarié dans les 7 jours "
            "suivant l'embauche.\n\n"
            "Taux de cotisations sociales (2025) : cotisation patronale 16,57 % du salaire brut, "
            "cotisation salariale 9,18 %. Pour les startups Startup Act, la cotisation patronale "
            "des fondateurs salariés est prise en charge par l'État pendant 3 ans. "
            "Des exonérations partielles existent pour les primo-recruteurs dans les zones de "
            "développement régional.\n\n"
            "La CNSS offre un portail e-déclaration (CNSSDATI) pour les déclarations mensuelles "
            "en ligne. Les pénalités de retard sont de 0,75 % par mois. Pour les startups en "
            "forte croissance, un tableau de bord de suivi des obligations sociales est recommandé "
            "pour éviter les contentieux CNSS qui peuvent bloquer les appels d'offres publics."
        ),
    },
    {
        "id": "code-travail-tunisien",
        "title": "Code du Travail Tunisien — Guide de conformité RH pour startups",
        "type": "legal_regulatory",
        "stage": ["launch_planning", "structuration", "growth"],
        "sector": ["cross-sector"],
        "score_dimensions": ["scalability", "green"],
        "url": "https://www.emploi.gov.tn/legislation",
        "language": "fr",
        "last_verified": "2026-06-01",
        "provider": "Ministère de l'Emploi et de la Formation Professionnelle",
        "body": (
            "Le Code du Travail tunisien (Loi n°66-27 du 30 avril 1966, modifié en 2021) régit les "
            "relations de travail entre employeurs et salariés. Pour les startups qui recrutent pour "
            "la première fois, les points essentiels à maîtriser sont : types de contrats (CDI, CDD, "
            "CIVP), SMIG (salaire minimum 2025 : 425 TND/mois pour 48h), congés payés (1 jour/mois), "
            "et procédures de licenciement.\n\n"
            "Le Contrat d'Insertion des Diplômés de l'Enseignement Supérieur (CIVP) permet aux "
            "startups d'embaucher des jeunes diplômés sur 12 mois avec prise en charge partielle "
            "du salaire par l'État (150 TND/mois) et exonération des cotisations patronales. "
            "C'est un mécanisme très utilisé par les startups tech pour recruter des développeurs.\n\n"
            "La période d'essai légale est de 3 mois pour les cadres et 1 mois pour les exécutants "
            "(renouvelable une fois). Le préavis de licenciement varie de 1 à 3 mois selon l'ancienneté. "
            "L'Inspection du Travail est l'autorité de contrôle ; les amendes pour infraction varient "
            "de 200 à 2 000 TND par infraction."
        ),
    },
    {
        "id": "gtm-strategy-workshop",
        "title": "Atelier Stratégie Go-to-Market pour startups B2B",
        "type": "training_coaching",
        "stage": ["launch_planning"],
        "sector": ["digital-tech", "cross-sector"],
        "score_dimensions": ["market", "commercial_offer"],
        "url": "https://www.hub-startup.tn/workshops",
        "language": "fr",
        "last_verified": "2026-06-01",
        "provider": "HUB Tunisia",
        "body": (
            "HUB Tunisia organise des workshops intensifs sur la stratégie Go-to-Market (GTM) adaptés "
            "aux startups B2B tunisiennes. Le programme de 2 jours couvre : segmentation et ciblage "
            "(ICP — Ideal Customer Profile), canaux d'acquisition (outbound, partnerships, contenus), "
            "pricing et positionnement, et plan de déploiement commercial sur 90 jours.\n\n"
            "Le workshop inclut des études de cas de startups tunisiennes B2B qui ont réussi leur "
            "GTM : Paymee (fintech B2B), Telnet (IT services), et Vermeg (logiciels bancaires). "
            "Les participants repartent avec un GTM Canvas complété et un pipeline de 20 prospects "
            "qualifiés identifiés via LinkedIn Sales Navigator.\n\n"
            "Des sessions de suivi hebdomadaires sont organisées pendant 8 semaines après le workshop "
            "pour aider les équipes à exécuter leur plan GTM. HUB Tunisia met à disposition une base "
            "de données des 500 plus grandes entreprises tunisiennes classées par secteur et chiffre "
            "d'affaires, utilisable pour la prospection outbound."
        ),
    },
    {
        "id": "digital-marketing-formation",
        "title": "Formation Marketing Digital pour Startups Tunisiennes",
        "type": "training_coaching",
        "stage": ["launch_planning", "growth"],
        "sector": ["digital-tech", "cross-sector"],
        "score_dimensions": ["market", "commercial_offer"],
        "url": "https://www.godigitaltn.tn",
        "language": "fr",
        "last_verified": "2026-06-01",
        "provider": "GoDigital Tunisie — Programme national de formation digitale",
        "body": (
            "Le programme GoDigital Tunisie propose des formations certifiantes en marketing digital "
            "subventionnées à 80 % pour les entrepreneurs et PME. Les modules incluent : SEO et "
            "référencement arabe/français, publicité sur Facebook et Instagram (Meta Ads), campagnes "
            "Google Ads, et email marketing adapté au marché tunisien.\n\n"
            "Le cours avancé couvre les spécificités du marché tunisien : taux d'utilisation mobile "
            "élevé (90 % des accès internet via mobile), préférence pour WhatsApp Business pour le "
            "service client, rôle de Facebook comme canal e-commerce majeur, et croissance rapide "
            "de TikTok comme canal d'acquisition pour la Gen Z.\n\n"
            "GoDigital collabore avec Google, Meta, et les agences digitales tunisiennes pour assurer "
            "la pertinence des contenus pédagogiques. Les participants obtiennent une certification "
            "reconnue par le Ministère du Commerce. Des ateliers de création de campagnes réelles "
            "avec un budget test de 100 TND sont inclus."
        ),
    },
    {
        "id": "carthage-business-angels",
        "title": "Carthage Business Angels — Réseau d'investisseurs providentiel",
        "type": "networking_ecosystem",
        "stage": ["launch_planning", "fundraising"],
        "sector": ["cross-sector"],
        "score_dimensions": ["scalability", "market"],
        "url": "https://www.cba.tn",
        "language": "fr",
        "last_verified": "2026-06-01",
        "provider": "Carthage Business Angels (CBA)",
        "body": (
            "Carthage Business Angels est le principal réseau de business angels tunisiens, comptant "
            "60+ membres actifs qui investissent collectivement 1 à 5 millions TND par an dans des "
            "startups tunisiennes. Le ticket moyen par deal est de 50 000 à 300 000 TND pour une "
            "participation de 10-20 %.\n\n"
            "Le processus d'investissement CBA : candidature en ligne, pré-sélection par le bureau "
            "exécutif, pitch devant les membres (30 min + Q&A), due diligence (4 semaines), et "
            "closing avec signature du pacte d'actionnaires. Le délai total est de 2 à 3 mois.\n\n"
            "La valeur ajoutée des CBA va au-delà du capital : accès au réseau des membres (dirigeants "
            "de grandes entreprises tunisiennes), ouvertures commerciales B2B, et expertise sectorielle "
            "pour les startups en phase de lancement. CBA organise des Pitch Days trimestriels ouverts "
            "à toutes les startups via candidature en ligne sur cba.tn."
        ),
    },
    {
        "id": "hub-startup-events",
        "title": "HUB Tunisia — Événements Networking Startups",
        "type": "networking_ecosystem",
        "stage": ["launch_planning", "structuration", "growth"],
        "sector": ["cross-sector"],
        "score_dimensions": ["market"],
        "url": "https://www.hub-startup.tn",
        "language": "fr",
        "last_verified": "2026-06-01",
        "provider": "HUB Tunisia",
        "body": (
            "HUB Tunisia organise des événements networking mensuels pour l'écosystème startup : "
            "meetups thématiques (fintech, healthtech, agritech, edtech), sessions de speed-dating "
            "startups/grandes entreprises, et workshops pratiques. Ces événements réunissent "
            "100 à 300 participants par session.\n\n"
            "Le format 'Startup Unplugged' mensuel permet à 3 startups de présenter leur produit "
            "devant 100+ professionnels du secteur et de recueillir des feedbacks en direct. "
            "C'est un excellent canal pour trouver des premiers clients et des partenaires commerciaux "
            "B2B dans le marché tunisien.\n\n"
            "HUB Tunisia tient un calendrier de tous les événements de l'écosystème startup tunisien "
            "(startuptn.tn/agenda) et produit le 'State of Startups Tunisia' annuel, référence pour "
            "comprendre les tendances de l'écosystème. L'adhésion au HUB (200 TND/an) donne accès "
            "à tous les événements et à l'espace de coworking."
        ),
    },
    {
        "id": "hubspot-startups",
        "title": "HubSpot for Startups — CRM et Marketing Automation gratuit",
        "type": "technical_infrastructure",
        "stage": ["launch_planning", "growth"],
        "sector": ["digital-tech", "cross-sector"],
        "score_dimensions": ["commercial_offer", "scalability"],
        "url": "https://www.hubspot.com/startups",
        "language": "en",
        "last_verified": "2026-06-01",
        "provider": "HubSpot",
        "body": (
            "HubSpot for Startups provides up to 90% discount on HubSpot's CRM, Marketing Hub, "
            "Sales Hub, and Service Hub for eligible startups. Tunisian startups can access the "
            "program through partner accelerators (Flat6Labs, Orange Fab) or via direct application "
            "if they have less than $2M in funding.\n\n"
            "Key features for B2B startups: contact management (unlimited in free tier), email "
            "marketing (2,000 emails/month free), deal pipeline tracking, meeting scheduler, "
            "live chat, and basic reporting. The Sales Hub Professional includes sequences for "
            "automated prospecting outreach — valuable for Tunisian startups targeting European clients.\n\n"
            "HubSpot supports Arabic interface (for customer-facing teams) and integrates with "
            "WhatsApp Business, Facebook Messenger, and Zoho Books (for Tunisian accounting). "
            "The free CRM tier is sufficient for most pre-revenue startups. The Professional tiers "
            "(Starting at $400/month with startup discount) add automation and advanced analytics."
        ),
    },
    {
        "id": "paiement-en-ligne-integration",
        "title": "Paiement en ligne en Tunisie — Intégration et conformité BCT",
        "type": "technical_infrastructure",
        "stage": ["launch_planning"],
        "sector": ["digital-tech", "cross-sector"],
        "score_dimensions": ["commercial_offer", "scalability"],
        "url": "https://www.paymee.tn/developpeurs",
        "language": "fr",
        "last_verified": "2026-06-01",
        "provider": "Paymee / Konnect / Flouci",
        "body": (
            "L'intégration du paiement en ligne en Tunisie requiert une conformité avec la Banque "
            "Centrale de Tunisie (BCT). Les prestataires de paiement agréés incluent : Paymee "
            "(commission 1.5-2.5 %), Konnect by Amen Bank (1.5 %), et Flouci by WafaCash (mobile-first). "
            "L'intégration se fait via API REST avec des SDKs JavaScript, PHP et Python.\n\n"
            "La réglementation BCT impose que les paiements en ligne en TND transitent par un "
            "établissement de paiement agréé en Tunisie. Les cartes Visa/Mastercard émises en Tunisie "
            "ne peuvent effectuer des paiements en devises étrangères qu'avec une carte Visa International "
            "spéciale. Pour les clients internationaux, Stripe et PayPal restent les solutions standard.\n\n"
            "Pour les startups e-commerce B2C en Tunisie, la solution recommandée est Konnect ou Paymee "
            "pour les paiements TND + Stripe Atlas pour les clients internationaux. Le wallet Flouci "
            "est pertinent pour les marketplaces ciblant les particuliers sans carte bancaire "
            "(50 % des Tunisiens non-bancarisés)."
        ),
    },
    # ── GROWTH ────────────────────────────────────────────────────────────────
    {
        "id": "bfpme-credit-croissance",
        "title": "BFPME — Crédit d'investissement pour la phase de croissance",
        "type": "financing",
        "stage": ["growth"],
        "sector": ["cross-sector"],
        "score_dimensions": ["scalability"],
        "url": "https://www.bfpme.com.tn/credit-croissance",
        "language": "fr",
        "last_verified": "2026-06-01",
        "provider": "BFPME",
        "body": (
            "La BFPME propose des crédits d'investissement spécifiques pour les startups et PME en "
            "phase de croissance nécessitant des investissements importants : extension de capacité "
            "de production, internationalisation, digitalisation, ou acquisition d'actifs stratégiques. "
            "Les montants vont de 500 000 à 5 millions TND.\n\n"
            "Critères d'éligibilité pour le crédit croissance : 3+ années d'activité, bilan positif "
            "sur les 2 derniers exercices, plan de développement documenté, et ratio dette/fonds propres "
            "inférieur à 3:1. La garantie est apportée par le SOTUGAR (Société Tunisienne de Garantie) "
            "qui couvre jusqu'à 75 % du risque de crédit.\n\n"
            "Le dossier de crédit croissance comprend : bilan des 3 dernières années, plan d'affaires "
            "sur 3 ans, justificatif de l'investissement (devis, contrats), et attestation d'affiliation "
            "CNSS/RNE. Une lettre de soutien d'un programme d'accélération ou d'une SICAR partenaire "
            "renforce significativement le dossier."
        ),
    },
    {
        "id": "horizon-europe-tunisie",
        "title": "Horizon Europe — Partenariats R&D et Innovation Tunisie-UE",
        "type": "financing",
        "stage": ["growth"],
        "sector": ["digital-tech", "industry", "agri-food"],
        "score_dimensions": ["innovation", "green"],
        "url": "https://ec.europa.eu/info/funding-tenders/opportunities/portal/screen/programmes/horizon",
        "language": "fr",
        "last_verified": "2026-06-01",
        "provider": "Commission Européenne",
        "body": (
            "Horizon Europe est le programme-cadre de R&D de l'UE (2021-2027) doté de 95,5 milliards EUR. "
            "La Tunisie est pays associé à Horizon Europe, permettant aux entreprises tunisiennes de "
            "participer en tant que partenaires à parts égales dans les consortiums européens, avec "
            "accès aux mêmes conditions de financement que les entités européennes.\n\n"
            "Instruments pertinents pour les startups tunisiennes : EIC Accelerator (jusqu'à "
            "2,5M EUR + equity pour innovations de rupture), Marie Skłodowska-Curie Actions (mobilité "
            "chercheurs), et Partenariats Thématiques (Deep Tech, Industrie Verte, Alimentation). "
            "Les taux de financement vont de 70 % à 100 % des coûts éligibles selon l'instrument.\n\n"
            "Le NCP Tunisie (National Contact Point, géré par le MRSIT) offre un accompagnement gratuit "
            "pour le montage de consortiums européens. Les startups deep-tech tunisiennes ayant un "
            "partenariat avec un laboratoire universitaire européen ont un avantage concurrentiel "
            "significatif dans ces appels à propositions."
        ),
    },
    {
        "id": "cepex-promotion-export",
        "title": "CEPEX — Centre de Promotion des Exportations Tunisiennes",
        "type": "legal_regulatory",
        "stage": ["growth", "launch_planning"],
        "sector": ["cross-sector"],
        "score_dimensions": ["market", "scalability"],
        "url": "https://www.cepex.nat.tn",
        "language": "fr",
        "last_verified": "2026-06-01",
        "provider": "CEPEX — Centre de Promotion des Exportations",
        "body": (
            "Le CEPEX est l'agence gouvernementale tunisienne dédiée à la promotion des exportations. "
            "Il soutient les startups et PME tunisiennes dans leur développement export via : "
            "subventions aux participations aux foires internationales (50-70 % du coût), organisation "
            "de missions de prospection collectives à l'étranger, et mise à disposition d'études de "
            "marché sectorielles gratuites.\n\n"
            "Services clés : Répertoire des exportateurs tunisiens (référencement gratuit), certification "
            "d'origine pour les produits exportés, veille sur les réglementations douanières des pays "
            "cibles, et accompagnement à la certification CE et aux normes d'import des marchés cibles "
            "(UE, USA, Golfe). Le CEPEX dispose d'attachés commerciaux dans 25 pays.\n\n"
            "Pour les startups exportant des services (SaaS, conseil IT, design), le CEPEX accompagne "
            "l'obtention du statut d'exportateur de services, permettant le bénéfice du taux de change "
            "préférentiel pour les revenus en devises et les avantages fiscaux de l'APII."
        ),
    },
    {
        "id": "loi-concurrence-prix",
        "title": "Loi sur la Concurrence et les Prix — Conformité pour la croissance",
        "type": "legal_regulatory",
        "stage": ["growth"],
        "sector": ["cross-sector"],
        "score_dimensions": ["green"],
        "url": "https://www.commerce.gov.tn/concurrence",
        "language": "fr",
        "last_verified": "2026-06-01",
        "provider": "Ministère du Commerce — Conseil de la Concurrence",
        "body": (
            "La loi n°91-64 du 29 juillet 1991 (modifiée) régissant la concurrence et les prix "
            "en Tunisie s'applique aux startups dès qu'elles atteignent une position significative "
            "sur leur marché. Le Conseil de la Concurrence surveille les pratiques anticoncurrentielles "
            "et les concentrations d'entreprises.\n\n"
            "Points de vigilance pour les startups en croissance : ententes illicites entre concurrents "
            "(prix, zones, clients), abus de position dominante (impossible de refuser de vendre "
            "à des conditions raisonnables), et pratiques discriminatoires tarifaires. "
            "Les plateformes digitales (marketplaces, agrégateurs) doivent être particulièrement "
            "vigilantes sur leur modèle de commission et leurs clauses d'exclusivité.\n\n"
            "Pour les fusions-acquisitions, toute opération dépassant un seuil de chiffre d'affaires "
            "cumulé de 50 millions TND doit être notifiée préalablement au Conseil de la Concurrence. "
            "Le délai d'instruction est de 30 jours (ou 90 jours si enquête approfondie)."
        ),
    },
    {
        "id": "scaleup-kaizen-formation",
        "title": "Formation Scale-Up — Processus et Kaizen Opérationnel",
        "type": "training_coaching",
        "stage": ["growth"],
        "sector": ["cross-sector"],
        "score_dimensions": ["scalability"],
        "url": "https://www.iace.tn/scale-up",
        "language": "fr",
        "last_verified": "2026-06-01",
        "provider": "IACE / TANIT Incubateur",
        "body": (
            "Ce programme de formation intensive de 5 jours accompagne les startups en phase de "
            "scale-up (revenue > 1M TND, équipe > 10 personnes) dans la structuration de leurs "
            "opérations : mise en place d'OKRs (Objectives and Key Results), design organisationnel "
            "pour la croissance, et méthodes d'amélioration continue (Kaizen, Lean Management).\n\n"
            "Le module Kaizen opérationnel couvre : cartographie des flux de valeur (VSM), réduction "
            "du temps de cycle pour les processus clés, standardisation des SOPs (procédures "
            "opérationnelles), et mise en place de tableaux de bord opérationnels (Daily Stand-ups, "
            "Weekly Business Review). Ces méthodes permettent d'augmenter la capacité sans augmenter "
            "proportionnellement les coûts.\n\n"
            "Le module Leadership couvre la transition du mode fondateur (tout faire soi-même) au "
            "mode dirigeant (déléguer et contrôler). Des ateliers sur la construction de l'équipe "
            "de direction (C-suite), la gestion des conflits d'actionnaires, et la communication "
            "avec le conseil d'administration sont inclus."
        ),
    },
    {
        "id": "cepex-formation-export",
        "title": "CEPEX — Programmes de Formation à l'Export",
        "type": "training_coaching",
        "stage": ["growth", "launch_planning"],
        "sector": ["cross-sector"],
        "score_dimensions": ["market"],
        "url": "https://www.cepex.nat.tn/formation",
        "language": "fr",
        "last_verified": "2026-06-01",
        "provider": "CEPEX",
        "body": (
            "Le CEPEX propose des formations pratiques sur les techniques de commerce international : "
            "techniques de négociation interculturelle avec acheteurs européens et du Golfe, "
            "Incoterms 2020 et logistique internationale, financement du commerce international "
            "(crédit documentaire, SBLC), et réglementation douanière tunisienne.\n\n"
            "La formation Prospection Export Digitale couvre les outils numériques pour identifier "
            "des prospects internationaux : LinkedIn Sales Navigator, Kompass, Alibaba B2B, "
            "et les bases de données d'importateurs par pays (UNTRNS, Panjiva). "
            "Ces outils permettent aux startups de cibler des distributeurs et partenaires commerciaux "
            "à l'international sans coût de prospection physique élevé.\n\n"
            "Le CEPEX organise 4 à 6 missions de prospection collectives par an dans les marchés "
            "prioritaires (France, Italie, Allemagne, EAU, Arabie Saoudite). Les participants "
            "bénéficient d'une prise en charge partielle des frais de déplacement et d'une "
            "organisation de rendez-vous B2B pré-qualifiés sur place."
        ),
    },
    {
        "id": "utica-federation-industrie",
        "title": "UTICA — Union Tunisienne de l'Industrie, du Commerce et de l'Artisanat",
        "type": "networking_ecosystem",
        "stage": ["growth"],
        "sector": ["industry", "cross-sector"],
        "score_dimensions": ["market", "scalability"],
        "url": "https://www.utica.org.tn",
        "language": "fr",
        "last_verified": "2026-06-01",
        "provider": "UTICA",
        "body": (
            "L'UTICA est la principale organisation patronale tunisienne, regroupant 23 fédérations "
            "sectorielles et 47 unions régionales. Pour les startups en croissance, l'adhésion à "
            "la fédération sectorielle concernée (numérique, industries mécaniques, agroalimentaire) "
            "ouvre des portes importantes dans les négociations avec les grands groupes industriels.\n\n"
            "Avantages de l'adhésion UTICA : représentation dans les négociations tripartites "
            "(gouvernement, UGTT, patronat), accès aux accords de branche (conventions collectives), "
            "participation aux délégations commerciales officielles, et accès au réseau des "
            "2 000+ membres fédéraux (potentiels clients, fournisseurs, partenaires).\n\n"
            "Pour les startups tech B2B, la Fédération Nationale des Éditeurs de Logiciels (FNEL) "
            "est le sous-réseau le plus pertinent. La FNEL représente 150+ éditeurs tunisiens et "
            "organise le Salon TIE (Technologies de l'Information et de l'Édition) annuellement."
        ),
    },
    {
        "id": "ifc-world-bank-tunisie",
        "title": "IFC / Banque Mondiale — Programmes d'appui au secteur privé tunisien",
        "type": "networking_ecosystem",
        "stage": ["growth"],
        "sector": ["cross-sector"],
        "score_dimensions": ["scalability", "green"],
        "url": "https://www.ifc.org/mena",
        "language": "fr",
        "last_verified": "2026-06-01",
        "provider": "International Finance Corporation (IFC) / Groupe Banque Mondiale",
        "body": (
            "L'IFC (International Finance Corporation), membre du Groupe Banque Mondiale, investit "
            "dans le secteur privé tunisien via des prêts et participations (tickets 3-50M USD). "
            "Elle finance également des programmes de développement des PME via ses partenaires "
            "bancaires locaux (BIAT, Amen Bank, UIB) à des conditions préférentielles.\n\n"
            "Le programme IFC Women Entrepreneurs (pour les startups fondées ou co-fondées par des "
            "femmes), le fonds IFC Africa Tech (pour les scale-ups tech) et les facilités de "
            "financement climatique IFC sont accessibles aux entreprises tunisiennes. "
            "Le ticket minimum IFC direct est élevé (3M USD) mais les lignes de crédit via banques "
            "partenaires sont accessibles à partir de 100 000 USD.\n\n"
            "La Banque Mondiale dispose d'un bureau pays à Tunis proposant des ressources gratuites : "
            "études de marché sectorielles, rapports doing business, et accès aux experts techniques "
            "pour les startups développant des solutions à impact social ou environnemental."
        ),
    },
    {
        "id": "technopole-el-ghazala",
        "title": "Technopôle El Ghazala — Centre d'Excellence Numérique Tunisien",
        "type": "technical_infrastructure",
        "stage": ["growth", "structuration"],
        "sector": ["digital-tech", "cross-sector"],
        "score_dimensions": ["innovation", "scalability"],
        "url": "https://www.elghazala.tn",
        "language": "fr",
        "last_verified": "2026-06-01",
        "provider": "Technopôle El Ghazala",
        "body": (
            "Le Technopôle El Ghazala est le premier parc technologique tunisien, hébergeant 200+ "
            "entreprises tech dont les filiales R&D de Huawei, Microsoft, Vermeg, et 50+ startups. "
            "Il offre des espaces de bureau et laboratoires à des tarifs préférentiels pour les "
            "startups labellisées.\n\n"
            "Infrastructure mise à disposition : datacenter certifié TIER 3, laboratoire IoT et "
            "embarqué, espace de fabrication (FabLab avec imprimantes 3D et découpe laser), et "
            "salle de démonstration AR/VR. Les startups résidentes bénéficient d'un statut de "
            "société offshore simplifié et d'une exonération de TVA sur leurs services exportés.\n\n"
            "El Ghazala abrite le cluster numérique TN Cluster qui facilite les partenariats "
            "R&D entre startups et laboratoires universitaires (ENIT, SUP'COM, École Polytechnique). "
            "Pour les startups deep-tech cherchant à valider des technologies, la co-localisation "
            "avec les laboratoires universitaires partenaires est un avantage décisif."
        ),
    },
    {
        "id": "cloud-infrastructure-croissance",
        "title": "Infrastructure Cloud Scalable — Architecture pour la croissance",
        "type": "technical_infrastructure",
        "stage": ["growth"],
        "sector": ["digital-tech", "cross-sector"],
        "score_dimensions": ["scalability", "commercial_offer"],
        "url": "https://aws.amazon.com/solutions/startup",
        "language": "fr",
        "last_verified": "2026-06-01",
        "provider": "AWS / GCP / Azure",
        "body": (
            "Pour les startups tunisiennes en phase de croissance, la migration vers une architecture "
            "cloud scalable est incontournable. L'architecture recommandée pour les startups SaaS B2B "
            "comprend : load balancer managé, auto-scaling des instances de calcul, base de données "
            "managée (RDS/Cloud SQL), CDN pour les assets statiques, et monitoring/alerting (Datadog, "
            "Grafana Cloud).\n\n"
            "Coûts typiques pour une startup early-growth (10K users actifs) : 800-2 000 USD/mois sur "
            "AWS (région Europe Paris ou Middle East UAE pour la conformité données). Le passage à une "
            "architecture multi-région nécessite une planification rigoureuse (DNS, réplication de données, "
            "cohérence transactionnelle) et représente généralement le saut technique le plus complexe.\n\n"
            "Les programmes de crédit cloud (AWS Activate, GCP Startup, Azure for Startups) permettent "
            "de différer ces coûts de 12 à 24 mois. Les entreprises tunisiennes peuvent facturer en EUR "
            "ou USD via AWS Marketplace pour les clients internationaux, simplifiant la gestion des "
            "devises avec la BCT."
        ),
    },
    # ── SECTOR-SPECIFIC ───────────────────────────────────────────────────────
    {
        "id": "onagri-certification-agrifood",
        "title": "ONAGRI — Normes et certifications agro-alimentaires tunisiennes",
        "type": "legal_regulatory",
        "stage": ["structuration", "launch_planning", "growth"],
        "sector": ["agri-food"],
        "score_dimensions": ["green", "commercial_offer"],
        "url": "http://www.onagri.nat.tn",
        "language": "fr",
        "last_verified": "2026-06-01",
        "provider": "ONAGRI — Observatoire National de l'Agriculture",
        "body": (
            "L'ONAGRI publie les statistiques agricoles de référence et les normes réglementaires "
            "pour le secteur agro-alimentaire tunisien. Pour les startups agritech et food-tech, "
            "l'ONAGRI est la source de données primaire pour les études de marché sectorielles : "
            "productions par culture, prix de gros, imports/exports, et surfaces cultivées par région.\n\n"
            "Normes obligatoires pour l'agro-alimentaire tunisien : Normes INNORPI alimentaires "
            "(NT 11.19 pour l'huile d'olive, NT 11.06 pour les conserves), certifications HACCP "
            "pour les unités de transformation, et conformité avec le Code de la Santé Animale "
            "et Végétale pour les intrants agricoles.\n\n"
            "Pour l'export agro-alimentaire vers l'UE, les certifications complémentaires requises "
            "incluent : ISO 22000 (management de la sécurité alimentaire), GlobalG.A.P. (bonnes "
            "pratiques agricoles), et bio (certification CCAB pour les produits biologiques). "
            "L'UTAP (Union Tunisienne de l'Agriculture et de la Pêche) accompagne les coopératives "
            "et startups agritech dans l'obtention de ces certifications."
        ),
    },
    {
        "id": "startup-act-agrifood",
        "title": "Startup Act Agri-Food — Dispositifs spécifiques au secteur",
        "type": "financing",
        "stage": ["ideation", "market_validation", "structuration"],
        "sector": ["agri-food"],
        "score_dimensions": ["innovation", "green", "scalability"],
        "url": "https://startup.gov.tn/fr/agritech",
        "language": "fr",
        "last_verified": "2026-06-01",
        "provider": "Startup Tunisia / APII",
        "body": (
            "Le Startup Act prévoit des incitations renforcées pour les startups des secteurs "
            "agricole et agroalimentaire, en cohérence avec la Stratégie Nationale Agricole 2035. "
            "Les startups agritech et food-tech labellisées bénéficient d'une prime supplémentaire "
            "de 20 000 TND via l'APII et d'un accès prioritaire aux terres domaniales pour les "
            "projets agricoles pilotes.\n\n"
            "Les programmes de cofinancement sectoriels incluent : le fonds FOSEL (Fonds Spécial "
            "pour le Secteur de l'Eau et des Énergies Renouvelables) pour les agritechs à composante "
            "eau, le PNUD Tunisie pour les projets d'agriculture durable, et le GEF (Global "
            "Environment Facility) pour les projets agroécologiques.\n\n"
            "Le Ministère de l'Agriculture dispose d'un programme d'accompagnement des startups "
            "agritech (Agri-Labs) qui facilite les pilotes dans des périmètres irrigués étatiques. "
            "L'accès à ces pilotes est particulièrement précieux pour valider les solutions de "
            "precision farming et d'irrigation connectée avant déploiement commercial."
        ),
    },
    {
        "id": "chaine-valeur-agrifood",
        "title": "Chaîne de Valeur Agri-Food Tunisie — Cartographie et acteurs",
        "type": "networking_ecosystem",
        "stage": ["market_validation", "structuration", "launch_planning"],
        "sector": ["agri-food"],
        "score_dimensions": ["market", "commercial_offer"],
        "url": "https://www.utap.org.tn",
        "language": "fr",
        "last_verified": "2026-06-01",
        "provider": "UTAP — Union Tunisienne de l'Agriculture et de la Pêche",
        "body": (
            "La chaîne de valeur agro-alimentaire tunisienne est composée de 500 000+ exploitations "
            "agricoles, 3 000+ unités de transformation (IAA), et 200+ exportateurs référencés CEPEX. "
            "Pour les startups agritech, comprendre les acteurs clés et leurs points de douleur est "
            "essentiel à la validation marché.\n\n"
            "Points de douleur identifiés dans la chaîne de valeur tunisienne (ONAGRI 2024) : "
            "pertes post-récolte élevées (30 % pour les fruits et légumes), financement des "
            "agriculteurs limité (seulement 40 % bancarisés), manque de traçabilité pour l'export, "
            "et dépendance aux intermédiaires informels (marchands de grosses et collecteurs).\n\n"
            "L'UTAP dispose d'un réseau de 500+ coopératives agricoles régionales, qui sont les "
            "principaux clients potentiels pour les solutions agritech B2B (plateformes de mise en "
            "marché, capteurs IoT, solutions phytosanitaires digitales). Une introduction via l'UTAP "
            "accélère significativement l'accès aux pilotes dans les coopératives cibles."
        ),
    },
    {
        "id": "innorpi-logiciel-digital",
        "title": "INNORPI — Protection des logiciels et PI pour startups digitales",
        "type": "legal_regulatory",
        "stage": ["structuration", "fundraising"],
        "sector": ["digital-tech"],
        "score_dimensions": ["innovation", "green"],
        "url": "https://www.innorpi.tn/logiciels",
        "language": "fr",
        "last_verified": "2026-06-01",
        "provider": "INNORPI / OTDAV",
        "body": (
            "En Tunisie, la protection juridique des logiciels relève du droit d'auteur (copyright) "
            "géré par l'OTDAV (Office Tunisien des Droits d'Auteur et des Droits Voisins), non du "
            "droit des brevets. Le dépôt d'un logiciel auprès de l'OTDAV coûte 150 TND et crée "
            "une présomption légale de propriété avec date certaine.\n\n"
            "Pour les startups digital-tech, les mécanismes de protection recommandés sont : "
            "(1) dépôt OTDAV du code source, (2) dépôt de marque INNORPI pour le nom du logiciel, "
            "(3) clauses de confidentialité (NDA) avec les clients et partenaires, et (4) politique "
            "open-source documentée si utilisation de licences copyleft (GPL, AGPL).\n\n"
            "Un point de vigilance majeur pour les startups IA : les modèles d'IA entraînés sur "
            "des données propriétaires peuvent bénéficier d'une protection mixte (secret commercial "
            "pour les poids du modèle + droit d'auteur pour le code d'entraînement). "
            "L'INNORPI et l'OMPI publient des guides spécifiques sur la PI dans l'IA en 2024-2025."
        ),
    },
    {
        "id": "cetic-certification-industrie-4",
        "title": "CETIC — Certification et Industrie 4.0 pour startups industrielles",
        "type": "technical_infrastructure",
        "stage": ["structuration", "launch_planning", "growth"],
        "sector": ["industry"],
        "score_dimensions": ["innovation", "scalability", "green"],
        "url": "https://www.cetic.ind.tn/industrie-40",
        "language": "fr",
        "last_verified": "2026-06-01",
        "provider": "CETIME / CETIC",
        "body": (
            "Le CETIC (Centre d'Études et de Compétences pour les Industries Chimiques) et le CETIME "
            "accompagnent les startups industrielles tunisiennes dans leur transition vers l'Industrie 4.0 : "
            "intégration de systèmes MES (Manufacturing Execution Systems), robotique collaborative, "
            "jumeaux numériques, et maintenance prédictive via IIoT.\n\n"
            "Services proposés pour les startups : audit de maturité digitale industrielle, "
            "accompagnement à la certification ISO 50001 (gestion de l'énergie), essais de conformité "
            "EMC pour les équipements connectés, et mise en relation avec les intégrateurs industriels "
            "certifiés Siemens et Rockwell présents en Tunisie.\n\n"
            "Le CETIC dispose d'un showroom Industrie 4.0 (Tunis et Sfax) permettant aux startups "
            "de démontrer leurs solutions dans un environnement industriel réel. Ce setting est "
            "particulièrement valorisé par les prospects industriels lors de la phase de pilote. "
            "Des subventions APII peuvent couvrir 50 % des coûts de mise en conformité pour les "
            "startups hardware industrielles."
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
    print(f"Generated {n} resource files in {OUT}")
