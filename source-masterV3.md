# Job Agent — Sources Master

> Registre central des sources d'offres d'emploi étudiées pour le projet Job Agent.
>
> **Version : V3**
>
> Cette version consolide :
>
> * la recherche initiale ;
> * la contre-analyse Gemini ;
> * les vérifications effectuées auprès des sources officielles ;
> * les corrections de portée, d'accès et d'autorisation.
>
> **Principe :** une source peut être techniquement accessible sans être librement exploitable pour notre projet. L'accès technique, l'autorisation d'utilisation et la valeur stratégique sont évalués séparément.

---

# 1. Objectif

Le Job Agent doit rechercher, filtrer, normaliser, dédupliquer, analyser et recommander des offres d'emploi pertinentes pour un utilisateur.

La priorité géographique est :

1. Dakar
2. Sénégal
3. Afrique de l'Ouest
4. Afrique
5. International / Remote

Le projet privilégie les sources :

* accessibles légalement ;
* suffisamment structurées ;
* maintenables ;
* pertinentes géographiquement ;
* compatibles avec un usage d'agent ;
* permettant de renvoyer l'utilisateur vers la source ou la candidature originale.

---

# 2. Principe fondamental : source ≠ connecteur

Une **source** est un endroit où existent des offres.

Un **connecteur** est une intégration technique permettant au Job Agent d'accéder à cette source.

Exemple :

```text
Greenhouse
    ↓
Source d'offres

API Job Board
    ↓
Méthode d'accès

Connector
    ↓
Job Agent
```

Une source peut donc être :

* intéressante mais non accessible ;
* accessible mais soumise à autorisation ;
* accessible mais peu pertinente ;
* techniquement exploitable mais juridiquement/contractuellement incompatible ;
* ou réellement prête à devenir un connecteur.

---

# 3. Dimensions d'analyse

Chaque source est évaluée selon :

1. Plateforme / source
2. Catégorie
3. Provenance des données
4. Couverture géographique
5. Types d'offres
6. Structure des données
7. Méthodes d'accès
8. Meilleure méthode identifiée
9. Authentification
10. Autorisation
11. Conditions / restrictions
12. Données récupérables
13. Fraîcheur
14. Volume / diversité
15. Stockage
16. Affichage / redistribution
17. Lien de candidature
18. Candidature via API
19. Coût
20. Complexité d'intégration
21. Maintenance
22. Couverture unique
23. Valeur pour le projet
24. Verdict
25. Source de vérification
26. Date de vérification

---

# 4. Statuts stratégiques

### 🟢 Connecteur à étudier

La source est suffisamment intéressante et exploitable pour passer à l'étude technique du connecteur.

Cela ne signifie pas que le connecteur est déjà développé.

### 🟣 Partenariat nécessaire

La source est intéressante, mais son utilisation par le Job Agent nécessite une autorisation, un accord, une licence ou une clarification contractuelle.

### 🔵 À étudier plus tard

Source pertinente mais non prioritaire pour le MVP.

### 🟡 À surveiller

Source potentiellement intéressante, mais des informations importantes restent à vérifier.

### 🔴 À exclure

Source incompatible avec le périmètre, insuffisamment pertinente ou nécessitant un contournement non acceptable.

> Une source 🟣 peut devenir 🟢 après obtention et vérification de l'autorisation nécessaire.

---

# 5. Sources vérifiées et prioritaires

## 5.1 EmploiDakar

**Catégorie :** Job board local
**Couverture :** Sénégal / Dakar
**Méthode identifiée :** pages Web publiques
**API officielle publique :** non identifiée
**Flux structuré officiel :** non identifié

### Autorisation

Les CGU d'EmploiDakar indiquent notamment que l'utilisation ou l'extraction, même partielle, des bases de données utilisées par le site nécessite une autorisation expresse écrite préalable lorsqu'elle n'est pas couverte par les usages autorisés.

### Évaluation

* Pertinence Sénégal : **très élevée**
* Données publiques : oui
* API publique : non identifiée
* Extraction libre : non
* Partenariat : à envisager
* Valeur MVP : élevée

**VERDICT : 🟣 Partenariat nécessaire**

---

## 5.2 Senjob

**Catégorie :** Job board régional
**Couverture :** Sénégal + Afrique francophone
**Méthode identifiée :** pages Web publiques
**API officielle publique :** non identifiée
**RSS :** endpoint identifié mais contenu/fonctionnement à confirmer

### Évaluation

* Pertinence Sénégal : très élevée
* Pertinence Afrique francophone : élevée
* API publique confirmée : non
* RSS exploitable : non confirmé
* Conditions d'utilisation pour notre cas : à approfondir
* Valeur MVP : très élevée

**VERDICT : 🟡 À surveiller**

### Prochaine vérification

* vérifier le contenu réel du flux RSS ;
* vérifier les CGU ;
* rechercher un éventuel accès partenaire ;
* ne pas supposer qu'un endpoint RSS implique une autorisation d'agrégation.

---

## 5.3 Expat-Dakar — Emploi

**Catégorie :** Classifieds / emploi
**Couverture :** Sénégal
**Méthode :** pages Web publiques
**API officielle publique :** non identifiée

### Évaluation

* Pertinence locale : élevée
* API : non identifiée
* Conditions d'accès : à approfondir
* Accès automatisé : à vérifier
* Valeur MVP : élevée

**VERDICT : 🟡 À surveiller**

---

## 5.4 Talent2Africa

**Catégorie :** recrutement / talents
**Couverture :** Afrique / Afrique francophone / diaspora
**Méthode :** pages Web publiques
**API publique confirmée :** non identifiée

### Correction par rapport à Gemini

Gemini proposait directement 🟢.

Ce statut était trop affirmatif puisque l'autorisation et l'accès structuré n'étaient pas établis.

**VERDICT : 🟡 À surveiller**

### Intérêt

Très intéressant pour :

* profils qualifiés ;
* Afrique francophone ;
* mobilité africaine ;
* recrutement régional.

Mais pertinence stratégique ≠ connectabilité technique.

---

## 5.5 Offre-emploi.sn

**Catégorie :** Job board local
**Couverture :** Sénégal
**Méthode :** pages Web publiques
**API / RSS :** non confirmé

Une ambiguïté existe dans la dénomination utilisée dans la recherche initiale (« Emploi.sn »). La source doit être enregistrée sous son identité exacte après vérification.

**VERDICT : 🟡 À surveiller**

---

# 6. ATS — sources structurées

## 6.1 Greenhouse Job Board API

**Catégorie :** ATS / infrastructure de recrutement
**Couverture :** entreprises utilisant Greenhouse
**Méthode :** Job Board API
**Lecture des offres publiques :** oui

### Point fondamental

Greenhouse ne fournit pas une base mondiale unique de toutes les offres.

Le modèle est :

```text
Entreprise A
    ↓
Greenhouse Job Board
    ↓
offres A

Entreprise B
    ↓
Greenhouse Job Board
    ↓
offres B
```

### Évaluation

* Données structurées : oui
* API : oui
* Lecture des offres publiées : oui
* Recherche mondiale Greenhouse : non
* Candidature : mécanisme distinct
* Valeur technique : élevée

**VERDICT : 🟢 Connecteur à étudier**

### Conséquence architecturale

Il faudra ultérieurement construire une stratégie de **découverte des entreprises utilisant Greenhouse**.

---

## 6.2 Lever Postings API

**Catégorie :** ATS
**Couverture :** entreprises utilisant Lever
**Méthode :** REST API
**Format :** JSON / HTML

La documentation officielle indique que l'API permet notamment de récupérer les offres publiées d'une entreprise, avec pagination et filtres par localisation, équipe, département, type d'engagement, etc.

Elle précise également que l'API ne permet pas d'effectuer une recherche full-text globale sur toutes les offres Lever.

### Candidature

Une API de candidature existe, mais elle nécessite une clé API liée au compte et possède des limites de débit. Lever recommande de rediriger les candidats vers son formulaire hébergé lorsque l'on ne souhaite pas gérer soi-même les mécanismes de file d'attente et de retry.

### Évaluation

**VERDICT : 🟢 Connecteur à étudier**

Pour le MVP :

> lecture des offres : oui
> candidature automatique : non prioritaire

---

## 6.3 Ashby Job Postings API

**Catégorie :** ATS
**Couverture :** entreprises utilisant Ashby
**Méthode :** API Job Posting publique

L'API publique permet de récupérer les offres publiées d'un job board d'organisation.

### Limitation

Comme Greenhouse et Lever :

> ce n'est pas un moteur mondial de recherche d'offres Ashby.

Le connecteur devra donc connaître ou découvrir les organisations utilisant Ashby.

**VERDICT : 🟢 Connecteur à étudier**

---

# 7. Plateformes Remote structurées

## 7.1 RemoteOK

**Catégorie :** job board remote
**Couverture :** internationale / remote
**Méthodes :**

* JSON
* RSS

RemoteOK indique officiellement que ses flux sont publics, gratuits et sans authentification. Les intégrations ou agrégateurs doivent créditer RemoteOK et renvoyer vers l'URL originale de chaque offre.

### Évaluation

* API/JSON : oui
* RSS : oui
* Authentification : non
* Données structurées : oui
* Attribution : obligatoire
* Lien original : obligatoire
* Valeur remote : élevée

**VERDICT : 🟢 Connecteur à étudier**

---

## 7.2 Himalayas

**Catégorie :** job board remote / source orientée outils AI
**Couverture :** internationale / remote

Méthodes disponibles :

* JSON API
* RSS
* MCP

Himalayas indique que les données publiques de ces trois interfaces ne nécessitent pas de clé API. Le JSON et le RSS sont actualisés quotidiennement et disposent de mécanismes de limitation adaptés à leur usage.

La plateforme fournit également un dictionnaire de données détaillé permettant de connaître les champs disponibles.

### Intérêt particulier pour Job Agent

La présence native de MCP est intéressante pour notre projet, mais cela ne signifie pas que nous devons obligatoirement utiliser MCP.

Pour notre architecture :

```text
Himalayas
    ↓
JSON / RSS
    ↓
Connector
    ↓
JobOffer
```

MCP pourra être étudié séparément.

### Évaluation

**VERDICT : 🟢 Connecteur à étudier**

---

# 8. Agrégateurs nécessitant davantage de clarification

## 8.1 Jooble

**Catégorie :** agrégateur d'emploi
**Méthode :** API REST
**Authentification :** clé API

### Intérêt

Possibilité d'intégration structurée.

### Points à vérifier

* marchés disponibles avec notre compte ;
* quotas ;
* conditions d'utilisation ;
* redistribution ;
* stockage ;
* usage commercial ;
* couverture réelle du Sénégal et de l'Afrique francophone.

**VERDICT : 🟣 Partenariat nécessaire / accès à clarifier**

---

## 8.2 Adzuna

**Catégorie :** agrégateur
**Méthode :** API REST
**Authentification :** `app_id` + `app_key`

### Intérêt

Large couverture internationale et recherche structurée.

### Points critiques

* quotas ;
* attribution ;
* conditions commerciales ;
* licence ;
* stockage ;
* redistribution ;
* utilisation dans un produit commercial.

**VERDICT : 🟣 Partenariat nécessaire / licence à clarifier**

---

# 9. Autres sources du registre V2

Les sources suivantes restent dans le registre, mais ne sont pas prioritaires pour le premier cycle de connecteurs.

|  # | Source                               | Statut V3 |
| -: | ------------------------------------ | --------- |
|  1 | EmploiDakar                          | 🟣        |
|  2 | Senjob                               | 🟡        |
|  3 | Ligeey.com                           | 🟡        |
|  4 | Expat-Dakar Emploi                   | 🟡        |
|  5 | TrouvezJob.org                       | 🟡        |
|  6 | Emploi-jeune.com                     | 🟡        |
|  7 | DirectEmploi.com                     | 🔴        |
|  8 | Greenhouse                           | 🟢        |
|  9 | Lever                                | 🟢        |
| 10 | Ashby                                | 🟢        |
| 11 | Workday Career Sites                 | 🟡        |
| 12 | Recruitee                            | 🟣        |
| 13 | Jobvite                              | 🟣        |
| 14 | iCIMS                                | 🟣        |
| 15 | LinkedIn Jobs API                    | 🟣        |
| 16 | Indeed Job Sync API                  | 🔴        |
| 17 | Glassdoor API                        | 🔴        |
| 18 | Adzuna                               | 🟣        |
| 19 | Jooble                               | 🟣        |
| 20 | Devex                                | 🟣        |
| 21 | ReliefWeb Jobs                       | 🟡        |
| 22 | UN Careers                           | 🟡        |
| 23 | UN Talent                            | 🟡        |
| 24 | BrighterMonday                       | 🔴        |
| 25 | Jobberman                            | 🔴        |
| 26 | Fuzu                                 | 🔴        |
| 27 | ProGigFinder                         | 🔴        |
| 28 | Upwork                               | 🟣        |
| 29 | Fiverr                               | 🔴        |
| 30 | Malt                                 | 🔴        |
| 31 | Freelancer.com                       | 🟣        |
| 32 | France Travail                       | 🔵        |
| 33 | Emploitic                            | 🟣        |
| 34 | Emploi.ma                            | 🟣        |
| 35 | Coworkies                            | 🔵        |
| 36 | JobBoardly                           | 🔴        |
| 37 | Techmap Job Postings                 | 🟡        |
| 38 | Ever Jobs                            | 🟡        |
| 39 | Dev Global Jobs                      | 🟡        |
| 40 | We Work Remotely                     | 🟢        |
| 41 | RemoteOK                             | 🟢        |
| 42 | Himalayas                            | 🟢        |
| 43 | Arbeitnow                            | 🔴        |
| 44 | AI Dev Jobs                          | 🟡        |
| 45 | Talent2Africa                        | 🟡        |
| 46 | Offre-emploi.sn                      | 🟡        |
| 47 | BurkinaEmploi / FasoEmploi           | 🔵        |
| 48 | Communautés tech Sénégal / GalsenDev | 🟡        |

---

# 10. Lecture stratégique V3

La recherche permet maintenant de distinguer trois axes.

## Axe A — Socle remote immédiatement exploitable

```text
RemoteOK
Himalayas
We Work Remotely
```

Ces sources peuvent fournir rapidement des offres structurées.

---

## Axe B — Réseau d'ATS

```text
Greenhouse
Lever
Ashby
```

Ces sources sont techniquement intéressantes, mais leur fonctionnement implique une question supplémentaire :

> Comment découvrir les entreprises utilisant chacun de ces ATS ?

Le problème devient donc :

```text
Job Agent
   ↓
découverte des entreprises
   ↓
ATS détecté
   ↓
API de l'ATS
   ↓
offres
```

Cela constitue une piste importante pour une deuxième phase.

---

## Axe C — Sénégal / Afrique francophone

```text
EmploiDakar
Senjob
Expat-Dakar
Talent2Africa
Offre-emploi.sn
```

C'est l'axe stratégique local.

Mais contrairement aux sources remote structurées, plusieurs de ces plateformes nécessitent encore :

* clarification des droits ;
* partenariat ;
* identification d'un flux structuré ;
* ou confirmation des conditions d'accès.

**Leur importance stratégique ne doit donc pas être confondue avec leur facilité d'intégration.**

---

# 11. Priorité actuelle pour le MVP

À ce stade, le registre conduit à la stratégie suivante :

### Premier groupe — connecteurs à étudier

1. **RemoteOK**
2. **Himalayas**
3. **Greenhouse**
4. **Lever**
5. **Ashby**
6. **We Work Remotely**

### Deuxième groupe — à débloquer

7. **Senjob**
8. **EmploiDakar**
9. **Expat-Dakar**
10. **Talent2Africa**

### Troisième groupe — accès/licence à clarifier

11. **Jooble**
12. **Adzuna**
13. autres agrégateurs/API partenaires

---

# 12. Ce que V3 ne signifie pas

🟢 ne signifie pas :

> « nous pouvons immédiatement utiliser cette source en production ».

Cela signifie :

> « les conditions connues sont suffisamment favorables pour passer à l'étude du connecteur ».

De même :

🟣 ne signifie pas :

> « cette source est inutilisable ».

Cela signifie :

> « l'étape suivante est l'autorisation, le partenariat ou la clarification contractuelle ».

---

# 13. Règle de non-contournement

Le Job Agent ne doit jamais :

* contourner une authentification ;
* contourner un CAPTCHA ;
* contourner une protection anti-bot ;
* contourner une restriction de fréquence ;
* contourner un paywall ;
* utiliser des identifiants obtenus sans autorisation ;
* récupérer des données derrière une restriction d'accès ;
* ignorer les conditions d'utilisation applicables.

Lorsqu'une source n'offre pas d'accès compatible :

```text
API officielle
    ↓
flux officiel
    ↓
partenariat
    ↓
source alternative
    ↓
exclusion
```

et non :

```text
blocage
    ↓
contournement
```

---

# 14. Historique

### V1

Registre initial des sources découvertes.

### V2

Ajout de 44 sources issues notamment de la recherche Perplexity et première qualification stratégique.

### Gemini

Contre-analyse indépendante :

* nouvelles sources locales ;
* Talent2Africa ;
* Emploi.sn / Offre-emploi.sn ;
* vérifications complémentaires ;
* challenge de certains statuts.

### V3

Consolidation :

* vérification de sources primaires ;
* correction de plusieurs statuts ;
* distinction entre accès technique et autorisation ;
* distinction entre ATS et agrégateurs ;
* distinction entre source intéressante et source immédiatement connectable.

---

# 15. Prochaine étape

**Ne pas développer immédiatement les connecteurs.**

La prochaine étape est :

```text
sources-master V3
        ↓
audit critique
        ↓
corrections éventuelles
        ↓
sources-master V4
        ↓
connectors.md
        ↓
implémentation
```

L'audit critique doit notamment rechercher :

* informations insuffisamment vérifiées ;
* erreurs de statut ;
* sources oubliées ;
* contradictions ;
* hypothèses présentées comme des faits ;
* restrictions juridiques ou techniques manquantes ;
* sources 🟢 qui devraient être 🟡 ou 🟣 ;
* sources locales importantes absentes.

**Le master ne doit être considéré comme définitif qu'après cet audit.**
