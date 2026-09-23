# Project Context — AI Job Search Agent

> Document de référence décrivant le projet, ses objectifs, son périmètre, ses contraintes et ses principes fondamentaux.
>
> **Rôle de ce document :** expliquer **CE QUE NOUS CONSTRUISONS et POURQUOI**.
>
> Ce document ne définit pas la méthodologie détaillée de recherche. Celle-ci est décrite dans `research-protocol.md`.

---

# 1. Vue d'ensemble du projet

Nous concevons un **agent IA de recherche et de recommandation d'offres d'emploi**.

L'objectif est de réduire la friction rencontrée par un utilisateur lorsqu'il cherche des opportunités professionnelles pertinentes sur plusieurs sources.

L'agent doit pouvoir :

1. comprendre le profil et les préférences de l'utilisateur ;
2. rechercher des offres sur différentes sources autorisées ;
3. récupérer et normaliser les données ;
4. éliminer les doublons ;
5. filtrer les offres selon des critères explicites ;
6. évaluer leur correspondance avec le profil ;
7. expliquer pourquoi une offre est pertinente ;
8. recommander les offres pertinentes à l'utilisateur ;
9. permettre à l'utilisateur de valider ou non les recommandations ;
10. éventuellement préparer ou effectuer certaines étapes de candidature lorsque cela est techniquement et juridiquement possible.

Le projet doit privilégier une approche **progressive, vérifiable et human-in-the-loop**, plutôt qu'une automatisation totale dès le départ.

---

# 2. Problème à résoudre

La recherche d'emploi implique souvent :

* la consultation de nombreuses plateformes ;
* la répétition des mêmes recherches ;
* des critères de recherche difficiles à maintenir ;
* des offres dispersées entre plusieurs sources ;
* des doublons ;
* des descriptions incomplètes ou hétérogènes ;
* des offres peu pertinentes ;
* une difficulté à comparer rapidement plusieurs opportunités ;
* une perte de temps dans la préparation des candidatures.

Le projet cherche donc à transformer une recherche dispersée et répétitive en un processus plus structuré :

```text
Profil utilisateur
       ↓
Recherche multi-sources
       ↓
Collecte des offres
       ↓
Normalisation
       ↓
Déduplication
       ↓
Filtrage
       ↓
Matching
       ↓
Explication
       ↓
Recommandation
       ↓
Validation humaine
       ↓
Candidature éventuelle
```

---

# 3. Principe fondamental du produit

L'agent ne doit pas simplement être un moteur de recherche.

Sa valeur principale doit venir de sa capacité à :

> **chercher, comprendre, comparer et expliquer les opportunités pertinentes pour un utilisateur donné.**

Le système doit donc progressivement passer de :

```text
"Voici des offres trouvées"
```

à :

```text
"Voici les offres qui correspondent le mieux à votre profil,
voici pourquoi elles sont pertinentes,
et voici les éventuels points d'attention."
```

L'objectif n'est pas de remplacer le jugement de l'utilisateur, mais de **réduire le travail répétitif nécessaire pour prendre une décision**.

---

# 4. Human-in-the-loop

Le projet repose sur un principe de **human-in-the-loop**.

L'utilisateur doit conserver le contrôle sur les décisions importantes, notamment lorsqu'une action peut avoir une conséquence externe.

Exemples :

* accepter ou modifier son profil ;
* définir ses préférences ;
* valider les critères de recherche ;
* consulter les offres recommandées ;
* valider une candidature ;
* modifier une lettre ou un CV généré ;
* autoriser l'envoi d'une candidature.

Le système ne doit pas considérer que l'autorisation donnée à l'agent implique automatiquement l'autorisation d'effectuer toutes les actions possibles.

---

# 5. Niveaux d'autonomie

L'autonomie de l'agent est considérée comme progressive.

| Niveau | Capacité                             |
| ------ | ------------------------------------ |
| 1      | Observer / rechercher                |
| 2      | Filtrer                              |
| 3      | Évaluer la correspondance            |
| 4      | Recommander                          |
| 5      | Préparer une candidature             |
| 6      | Soumettre après validation explicite |
| 7      | Soumettre automatiquement            |

## Priorité MVP

Le MVP doit principalement couvrir les niveaux :

**1 → 4**

c'est-à-dire :

```text
Search
→ Filter
→ Match
→ Recommend
```

Les niveaux 5 et 6 pourront être étudiés ultérieurement.

Le niveau 7 ne doit jamais être considéré comme une capacité par défaut. Il dépend notamment :

* des règles de la plateforme ;
* des conditions d'utilisation ;
* des mécanismes d'accès disponibles ;
* des possibilités techniques ;
* du consentement de l'utilisateur ;
* des contraintes légales et contractuelles.

---

# 6. Périmètre géographique

La recherche doit accorder une attention particulière aux opportunités accessibles depuis l'Afrique.

Priorité géographique :

1. Dakar
2. Sénégal
3. Afrique de l'Ouest
4. Afrique
5. International
6. Remote international

Le système ne doit donc pas être conçu uniquement autour des grandes plateformes internationales.

Les sources locales, régionales et spécialisées doivent être activement recherchées.

---

# 7. Types de sources à étudier

La recherche doit couvrir différentes catégories de sources.

### Job boards généralistes

Exemples de catégories :

* plateformes nationales ;
* plateformes internationales ;
* agrégateurs d'offres.

### Job boards locaux

Particulièrement :

* Sénégal ;
* Afrique de l'Ouest ;
* Afrique francophone ;
* autres marchés africains pertinents.

### Plateformes professionnelles

Exemples :

* réseaux professionnels ;
* communautés professionnelles ;
* plateformes spécialisées.

### Career pages des entreprises

Les entreprises peuvent publier directement leurs offres sur leur propre site.

### ATS / Recruitment Platforms

Exemples de catégories :

* Greenhouse ;
* Lever ;
* Workable ;
* autres ATS disposant de mécanismes d'accès publics ou officiels.

### Portails publics

Exemples :

* agences publiques pour l'emploi ;
* portails gouvernementaux ;
* portails universitaires.

### Agences de recrutement

### Plateformes spécialisées

Par secteur :

* technologie ;
* finance ;
* santé ;
* ingénierie ;
* éducation ;
* ONG ;
* etc.

### Stage / alternance / premier emploi

### Freelance

### Communautés et réseaux

À étudier uniquement lorsque l'accès aux données est compatible avec les règles applicables.

---

# 8. Sources et méthodes d'accès

Une source et sa méthode d'accès doivent être considérées comme deux éléments distincts.

Une même plateforme peut proposer plusieurs moyens d'accès :

```text
PLATFORM
│
├── Official API
├── RSS / Atom
├── Webhook
├── Partner feed
├── Export
├── Public webpage
└── Other authorized mechanism
```

Le projet doit identifier, pour chaque source :

* quelles méthodes existent ;
* laquelle est officiellement documentée ;
* laquelle est autorisée ;
* quelles données elle permet d'obtenir ;
* quelles restrictions s'appliquent ;
* quelle méthode est techniquement la plus adaptée.

---

# 9. Hiérarchie des méthodes d'accès

Lorsque plusieurs méthodes sont disponibles, privilégier généralement :

1. API officielle ;
2. feed officiel ;
3. webhook officiel ;
4. partner feed / accès partenaire ;
5. export officiel ;
6. API tierce autorisée ;
7. données fournies directement par l'utilisateur ;
8. page publique, lorsque son utilisation est compatible avec les conditions applicables ;
9. autres méthodes uniquement après vérification.

Le projet ne doit pas devenir dépendant d'un scraping fragile lorsqu'une méthode officielle et durable existe.

---

# 10. Principe d'autorisation

La disponibilité technique d'une donnée ne signifie pas automatiquement que son utilisation est autorisée.

Il faut distinguer :

```text
Data visible
≠
Data accessible
≠
Data exploitable
≠
Data redistribuable
≠
Data utilisable pour une candidature automatisée
```

Pour chaque source, il faut donc étudier séparément :

* l'accès ;
* la collecte ;
* le stockage ;
* la transformation ;
* l'affichage ;
* la redistribution ;
* la création d'un produit concurrent ;
* l'utilisation pour une candidature ;
* l'automatisation.

Les conditions d'utilisation, la documentation officielle, les licences et autres documents contractuels pertinents doivent être considérés comme des sources prioritaires pour ces questions.

---

# 11. Autorisation utilisateur ≠ autorisation de plateforme

Le consentement de l'utilisateur ne donne pas automatiquement au système le droit d'effectuer une action sur une plateforme tierce.

Exemple :

```text
Utilisateur
    ↓ autorise
Notre agent
    ↓
Plateforme tierce
```

L'autorisation de l'utilisateur concerne notre système.

La plateforme tierce possède ses propres règles d'accès et d'utilisation.

Les deux doivent être respectées indépendamment.

---

# 12. Principe de non-contournement

Le projet ne doit pas chercher à contourner les mécanismes de protection ou de contrôle d'accès.

Ne pas contourner notamment :

* authentification ;
* CAPTCHA ;
* paywall ;
* anti-bot ;
* rate limiting ;
* restrictions d'accès ;
* mécanismes techniques destinés à empêcher l'automatisation ;
* restrictions contractuelles.

Lorsqu'une source n'est pas accessible de manière compatible avec le projet, elle doit être classée comme telle plutôt que contournée.

---

# 13. Objectif du modèle de données

Les différentes sources utilisent des structures différentes.

Le système doit donc transformer les données récupérées vers un modèle interne commun.

Exemple conceptuel :

```text
Source A
Source B
Source C
Source D
   ↓
Normalization Layer
   ↓
Internal JobOffer Model
```

L'objectif est de permettre au reste du système de fonctionner indépendamment de la source originale.

---

# 14. Modèle interne JobOffer

Le modèle interne pourra notamment contenir :

```text
JobOffer
├── id
├── source
├── source_offer_id
├── title
├── company
├── description
├── location
├── remote_type
├── contract_type
├── experience_level
├── salary
├── skills
├── sector
├── publication_date
├── application_deadline
├── application_url
├── source_url
├── retrieved_at
└── other relevant metadata
```

Ce modèle est évolutif.

Une source peut fournir davantage ou moins d'informations.

L'absence d'un champ ne doit donc pas être interprétée automatiquement comme une erreur.

---

# 15. Normalisation

La normalisation doit permettre de comparer des offres provenant de sources différentes.

Exemples :

```text
"Remote"
"100% remote"
"Work from home"
"À distance"
```

peuvent correspondre à une même catégorie interne.

De même :

```text
"CDI"
"Permanent"
"Full-time permanent"
```

peuvent nécessiter une normalisation selon le contexte.

La normalisation doit conserver autant que possible l'information originale afin d'éviter une perte d'information.

---

# 16. Déduplication

Une même offre peut être publiée :

* sur plusieurs job boards ;
* sur le site de l'entreprise ;
* via un ATS ;
* par une agence de recrutement ;
* sur plusieurs plateformes.

Le système doit donc identifier les offres potentiellement identiques.

La déduplication pourra utiliser plusieurs signaux :

* identifiant source ;
* URL ;
* entreprise ;
* titre ;
* localisation ;
* date ;
* contenu ;
* similarité sémantique.

La déduplication ne doit pas supprimer automatiquement des offres simplement parce qu'elles sont similaires.

---

# 17. Matching

Le matching consiste à comparer une offre avec le profil et les préférences de l'utilisateur.

Les critères peuvent inclure :

### Profil

* compétences ;
* expérience ;
* formation ;
* domaine ;
* niveau de séniorité.

### Préférences

* localisation ;
* remote ;
* type de contrat ;
* salaire ;
* secteur ;
* technologies ;
* langue ;
* disponibilité.

### Contraintes

* niveau d'expérience minimal ;
* localisation obligatoire ;
* compétences indispensables ;
* type de contrat exclu ;
* etc.

Le matching doit pouvoir distinguer :

```text
Critères obligatoires
vs
Critères préférés
```

---

# 18. Explainability

Le système ne doit pas seulement dire :

> "Cette offre correspond à votre profil."

Il doit être capable d'expliquer cette correspondance.

Exemple :

```text
Correspondances :
✓ React
✓ Node.js
✓ JavaScript
✓ 2 ans d'expérience demandés
✓ Remote

Points d'attention :
⚠ Anglais professionnel demandé
⚠ Expérience AWS souhaitée
```

L'objectif est de rendre la recommandation compréhensible et vérifiable par l'utilisateur.

---

# 19. Qualité des recommandations

La qualité ne doit pas être mesurée uniquement par le nombre d'offres récupérées.

Les dimensions importantes comprennent notamment :

* pertinence ;
* fraîcheur ;
* qualité des données ;
* couverture géographique ;
* diversité des sources ;
* précision du matching ;
* faible taux de doublons ;
* complétude ;
* capacité à expliquer la recommandation.

Une grande quantité d'offres peu pertinentes n'est pas nécessairement une amélioration du produit.

---

# 20. Workflow de candidature

À terme, le système pourra assister l'utilisateur dans la candidature.

Workflow cible :

```text
Offre pertinente
      ↓
Validation utilisateur
      ↓
Analyse de l'offre
      ↓
Préparation des éléments
      ↓
CV / lettre / réponses
      ↓
Validation utilisateur
      ↓
Soumission si autorisée
```

La soumission ne doit être possible que lorsque :

1. le mécanisme technique le permet ;
2. les règles de la plateforme l'autorisent ;
3. les informations nécessaires sont disponibles ;
4. l'utilisateur a donné l'autorisation appropriée.

---

# 21. Objectif de la recherche des sources

La recherche des sources ne consiste pas simplement à construire une longue liste de plateformes.

Elle doit permettre de répondre à la question :

> **Cette source est-elle suffisamment intéressante, accessible et exploitable pour justifier son intégration dans notre système ?**

Chaque source doit donc être évaluée selon plusieurs dimensions :

* couverture géographique ;
* volume ;
* diversité ;
* pertinence ;
* fraîcheur ;
* qualité des données ;
* accessibilité ;
* autorisation ;
* coût ;
* complexité d'intégration ;
* maintenance ;
* valeur stratégique ;
* possibilité de candidature.

---

# 22. Philosophie de sélection des sources

Une source peut être :

* très intéressante mais difficilement accessible ;
* facilement accessible mais peu pertinente ;
* très riche mais coûteuse ;
* locale mais peu structurée ;
* techniquement simple mais juridiquement restrictive.

La sélection doit donc être multidimensionnelle.

Il ne faut pas confondre :

```text
"facile à connecter"
```

avec :

```text
"bonne source pour le produit"
```

---

# 23. Statuts stratégiques des sources

Les sources étudiées peuvent recevoir l'un des statuts suivants :

### 🟢 Connecteur à étudier

La source présente un intérêt suffisant et semble disposer d'un mode d'accès compatible avec une future intégration.

### 🟣 Partenariat nécessaire

La source présente un intérêt mais nécessite une autorisation, un accord ou un accès particulier.

### 🔵 À étudier plus tard

La source est intéressante mais n'est pas prioritaire pour le MVP.

### 🟡 À surveiller

La source pourrait être intéressante mais des informations importantes restent à vérifier.

### 🔴 À exclure

La source est incompatible avec les objectifs, les contraintes ou les conditions du projet.

Le statut stratégique est différent du statut technique du connecteur.

---

# 24. Connecteurs

Un connecteur est responsable de la communication avec une source donnée.

Architecture conceptuelle :

```text
Source
  ↓
Connector
  ↓
Raw Data
  ↓
Parsing
  ↓
Normalization
  ↓
Deduplication
  ↓
JobOffer
```

Un connecteur doit isoler les spécificités de la source afin que le reste du système puisse utiliser un modèle commun.

---

# 25. Objectif des connecteurs

Un connecteur opérationnel doit notamment pouvoir :

* accéder à la source ;
* gérer l'authentification si nécessaire ;
* récupérer les données ;
* gérer la pagination ;
* respecter les limites ;
* gérer les erreurs ;
* effectuer les retries nécessaires ;
* parser les données ;
* normaliser les champs ;
* produire des `JobOffer`.

Le connecteur doit également être suffisamment documenté pour pouvoir être maintenu.

---

# 26. Statuts techniques des connecteurs

Les connecteurs peuvent avoir les statuts :

* ⚪ À étudier
* 🔵 Spécification en cours
* 🟣 En attente d'accès
* 🟠 En développement
* 🟢 Opérationnel
* 🟡 À corriger / instable
* 🟤 Maintenance requise
* 🔴 Bloqué
* ⚫ Abandonné

Un connecteur ne doit être considéré comme **opérationnel** qu'après vérification réelle.

---

# 27. Critères d'un connecteur opérationnel

Un connecteur peut être considéré comme opérationnel lorsque :

1. l'accès fonctionne ;
2. l'authentification fonctionne si nécessaire ;
3. les données sont effectivement récupérées ;
4. les données sont suffisamment complètes ;
5. le parsing fonctionne ;
6. la normalisation fonctionne ;
7. les principales erreurs sont gérées ;
8. les retries nécessaires sont définis ;
9. les limites d'utilisation sont respectées ;
10. les conditions d'utilisation sont compatibles ;
11. les données peuvent alimenter le modèle `JobOffer` ;
12. des tests de base ont été effectués.

---

# 28. Stratégie de recherche géographique

La recherche des sources doit éviter un biais excessivement centré sur les plateformes internationales.

Pour chaque catégorie, rechercher notamment :

```text
Global
  ↓
Africa
  ↓
West Africa
  ↓
Francophone Africa
  ↓
Senegal
  ↓
Dakar
```

Une recherche pertinente doit donc combiner :

* sources internationales ;
* sources africaines ;
* sources régionales ;
* sources sénégalaises ;
* sources locales spécialisées.

---

# 29. Stratégie linguistique de recherche

La recherche documentaire doit être **multilingue lorsque cela améliore la couverture**.

Les recherches peuvent être effectuées notamment en :

* français ;
* anglais ;
* langues locales pertinentes lorsque nécessaire.

Exemple :

```text
"job API Senegal"
"API offres emploi Sénégal"
"Senegal job board API"
"emploi Sénégal RSS"
"Senegal recruitment platform API"
```

Pour les questions techniques ou contractuelles, les documents officiels doivent être consultés dans leur langue originale lorsque cela est possible.

**L'anglais ne doit pas être considéré comme la seule langue de recherche.**

---

# 30. Qualité des recherches

Les recherches doivent distinguer :

### Source primaire

Exemples :

* documentation officielle ;
* API documentation ;
* Terms of Service ;
* Developer Agreement ;
* licence ;
* documentation juridique ;
* page officielle de la plateforme.

### Source secondaire

Exemples :

* articles ;
* blogs ;
* comparateurs ;
* forums ;
* vidéos ;
* discussions communautaires.

Les sources secondaires peuvent servir à découvrir une information.

Les informations importantes concernant :

* accès ;
* API ;
* restrictions ;
* licences ;
* tarification ;
* automatisation ;
* redistribution ;

doivent être vérifiées autant que possible auprès d'une source primaire.

---

# 31. Recherche multi-IA

Plusieurs systèmes d'IA peuvent être utilisés pour accélérer la recherche.

Exemple de workflow :

```text
Perplexity
    +
Gemini
    +
ChatGPT
    ↓
Liste consolidée
    ↓
Déduplication
    ↓
Vérification des sources primaires
    ↓
Master table
    ↓
Audit critique
    ↓
Claude / autre agent de vérification
```

Chaque IA doit être considérée comme un outil de recherche et d'analyse, et non comme une source de vérité.

Deux IA qui donnent la même information ne constituent pas nécessairement deux preuves indépendantes.

Elles peuvent avoir utilisé la même source primaire ou secondaire.

---

# 32. Reproductibilité de la recherche

Une information importante doit pouvoir être retrouvée et vérifiée.

Pour chaque source étudiée, conserver autant que possible :

* URL ;
* date de vérification ;
* document consulté ;
* méthode d'accès ;
* conditions importantes ;
* éléments justifiant la conclusion.

Le résultat de la recherche doit être enregistré dans :

```text
sources-master.md
```

et les détails d'intégration dans :

```text
connectors.md
```

---

# 33. Vérification temporelle

Les informations relatives aux :

* API ;
* tarifs ;
* conditions d'utilisation ;
* endpoints ;
* limites ;
* programmes partenaires ;
* accès développeur ;

peuvent changer.

Une information ancienne ne doit donc pas être présentée comme actuelle sans vérification.

Chaque information importante doit être considérée avec son contexte temporel.

---

# 34. Séparation des responsabilités documentaires

Le projet utilise plusieurs documents complémentaires.

```text
project-context.md
        ↓
    QUOI ?
    Pourquoi ?
    Périmètre ?
    Principes ?

research-protocol.md
        ↓
    COMMENT CHERCHER ?
    Comment vérifier ?
    Comment comparer ?

sources-master.md
        ↓
    QU'AVONS-NOUS TROUVÉ ?
    Quelles sources ?
    Quel statut ?

connectors.md
        ↓
    COMMENT INTÉGRER ?
    Quelle API ?
    Quelle auth ?
    Quel parsing ?
```

Cette séparation doit être conservée afin d'éviter de transformer un seul document en document monolithique.

---

# 35. Priorité du MVP

Le MVP doit rester volontairement limité.

### Priorité

```text
Recherche
↓
Collecte
↓
Normalisation
↓
Déduplication
↓
Filtrage
↓
Matching
↓
Explication
↓
Recommandation
```

### Hors priorité initiale

* automatisation complète des candidatures ;
* soumission automatique généralisée ;
* intégration de dizaines de plateformes avant validation du cœur produit ;
* scraping massif ;
* architecture inutilement complexe ;
* multiplication des agents sans besoin réel.

Le projet doit d'abord démontrer que :

> **la combinaison recherche multi-source + filtrage + matching + recommandation apporte une réelle valeur à l'utilisateur.**

---

# 36. Principe d'architecture

L'architecture doit séparer les responsabilités.

Conceptuellement :

```text
                    USER
                     │
                     ▼
              USER PROFILE
                     │
                     ▼
             SEARCH / AGENT
                     │
          ┌──────────┼──────────┐
          ▼          ▼          ▼
      SOURCE A   SOURCE B   SOURCE C
          │          │          │
          ▼          ▼          ▼
      CONNECTOR   CONNECTOR   CONNECTOR
          │          │          │
          └──────────┼──────────┘
                     ▼
              RAW JOB DATA
                     │
                     ▼
                NORMALIZER
                     │
                     ▼
               DEDUPLICATOR
                     │
                     ▼
               JOB OFFER DB
                     │
                     ▼
                 MATCHING
                     │
                     ▼
               EXPLANATION
                     │
                     ▼
             RECOMMENDATIONS
                     │
                     ▼
               USER REVIEW
                     │
                     ▼
          APPLICATION WORKFLOW
```

L'agent ne doit pas nécessairement être responsable de tout.

Il doit principalement orchestrer les étapes qui nécessitent :

* décision ;
* raisonnement ;
* sélection ;
* adaptation ;
* interaction avec l'utilisateur.

Les opérations déterministes doivent autant que possible rester dans des composants classiques.

---

# 37. Principes fondamentaux du projet

Le projet doit respecter les principes suivants :

### 1. Value before complexity

Construire d'abord une solution utile avant d'ajouter des mécanismes complexes d'IA.

### 2. Human control

L'utilisateur conserve le contrôle des décisions importantes.

### 3. Authorized access

Utiliser des mécanismes d'accès compatibles avec les règles des sources.

### 4. No bypass

Ne pas contourner les protections ou restrictions.

### 5. Primary-source verification

Vérifier les informations importantes auprès des sources officielles.

### 6. Source independence

Ne pas dépendre d'une seule plateforme lorsque cela peut être évité.

### 7. Data quality

La qualité et la pertinence des offres sont plus importantes que leur simple quantité.

### 8. Explainability

Les recommandations doivent être compréhensibles.

### 9. Modularity

Chaque source doit pouvoir être intégrée via un connecteur indépendant.

### 10. Incremental autonomy

L'autonomie doit augmenter progressivement.

### 11. Maintainability

Les solutions doivent rester maintenables lorsque les sources évoluent.

### 12. Reproducibility

Les décisions importantes doivent pouvoir être vérifiées et reproduites.

---

# 38. Résultat attendu de la phase de recherche

À la fin de la phase de recherche, nous devons disposer de :

1. une liste consolidée de sources pertinentes ;
2. une évaluation de leur intérêt ;
3. une identification de leurs méthodes d'accès ;
4. une vérification de leurs conditions d'utilisation ;
5. une estimation de leur complexité d'intégration ;
6. une sélection des sources prioritaires ;
7. une liste des sources nécessitant un partenariat ;
8. une liste des sources à reporter ;
9. une liste des sources à exclure ;
10. une spécification initiale des connecteurs ;
11. un modèle commun `JobOffer`.

Le résultat attendu n'est donc pas :

> "Nous avons trouvé beaucoup de plateformes."

Mais plutôt :

> "Nous savons quelles sources nous pouvons utiliser, comment nous pouvons les utiliser, sous quelles conditions, et lesquelles justifient une intégration."

---

# 39. Instruction pour les IA utilisées dans la recherche

Toute IA participant à la recherche sur ce projet doit :

1. comprendre le contexte décrit dans ce document avant de commencer ;
2. respecter le périmètre géographique du projet ;
3. rechercher des sources internationales **et** locales ;
4. effectuer des recherches en français et en anglais lorsque pertinent ;
5. rechercher les méthodes d'accès officielles ;
6. distinguer clairement accès technique et autorisation ;
7. rechercher les conditions d'utilisation pertinentes ;
8. privilégier les sources primaires ;
9. indiquer lorsqu'une information n'a pas pu être vérifiée ;
10. ne pas présenter une hypothèse comme un fait ;
11. ne pas supposer qu'une API existe sans preuve ;
12. ne pas supposer qu'une donnée peut être redistribuée simplement parce qu'elle est publique ;
13. ne pas recommander de contournement technique ;
14. identifier les incertitudes ;
15. fournir les sources permettant de vérifier les affirmations importantes ;
16. éviter les doublons avec les recherches déjà présentes dans `sources-master.md` ;
17. proposer de nouvelles sources uniquement lorsqu'elles apportent une valeur identifiable.

---

# 40. Relation avec les autres documents du projet

Ce document constitue le **contexte de référence du projet**.

Les autres documents doivent s'y conformer.

```text
                    PROJECT
                       │
                       ▼
              project-context.md
                       │
          ┌────────────┼────────────┐
          ▼            ▼            ▼
 research-protocol  sources-master  connectors
      HOW             FINDINGS      INTEGRATION
```

### `project-context.md`

Définit :

* le problème ;
* le produit ;
* le périmètre ;
* les principes ;
* les contraintes ;
* les objectifs.

### `research-protocol.md`

Définit :

* comment rechercher ;
* comment vérifier ;
* comment comparer ;
* comment documenter.

### `sources-master.md`

Contient :

* les sources étudiées ;
* leurs caractéristiques ;
* leur statut ;
* les résultats de recherche.

### `connectors.md`

Contient :

* les méthodes d'intégration ;
* les endpoints ;
* l'authentification ;
* les transformations ;
* les détails techniques.

---

# 41. Boucle d'amélioration du projet

Le projet doit fonctionner selon une boucle d'apprentissage continue :

```text
Project Context
      ↓
Research Protocol
      ↓
Research
      ↓
Sources Master
      ↓
Connector Development
      ↓
Technical Feedback
      ↓
Product Feedback
      ↓
Improved Research / Architecture
      ↓
Updated Documentation
```

`project-context.md` ne doit pas être modifié à chaque nouvelle recherche.

Il doit évoluer uniquement lorsque :

* le produit change ;
* le périmètre change ;
* les priorités changent ;
* une contrainte fondamentale change ;
* un principe architectural important évolue.

Les résultats de recherche ordinaires doivent plutôt être enregistrés dans `sources-master.md`.

Les détails techniques doivent être enregistrés dans `connectors.md`.

La méthodologie doit être améliorée dans `research-protocol.md` lorsque l'expérience montre qu'elle doit évoluer.

---

# 42. Vision finale

Le système doit progressivement devenir une couche intelligente située entre :

```text
UTILISATEUR
     │
     ▼
SON PROFIL ET SES OBJECTIFS
     │
     ▼
       AI JOB SEARCH AGENT
     │
     ├── Recherche
     ├── Filtrage
     ├── Matching
     ├── Explication
     ├── Recommandation
     └── Assistance à la candidature
     │
     ▼
MULTIPLES SOURCES D'EMPLOI
```

La valeur du produit ne repose donc pas uniquement sur l'utilisation d'un LLM.

Elle repose sur la combinaison de :

```text
Sources fiables
+
Accès autorisés
+
Collecte structurée
+
Normalisation
+
Déduplication
+
Matching pertinent
+
Explications
+
Orchestration par agent
+
Contrôle humain
```

L'IA est un moyen permettant de rendre le processus plus intelligent.

Elle ne constitue pas à elle seule le produit.

---

# 43. Règle directrice

> **Construire un agent capable de trouver les bonnes opportunités, de comprendre leur pertinence et d'aider l'utilisateur à agir, tout en respectant les règles des sources et en conservant l'humain dans la boucle.**
