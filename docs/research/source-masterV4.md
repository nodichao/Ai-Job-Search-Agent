# Job Agent — Sources Master

> **Version : V4 — 19 septembre 2026**
>
> Ce document constitue le registre central des sources d'offres d'emploi étudiées pour le projet Job Agent.
>
> Il ne constitue ni une liste de connecteurs opérationnels, ni une autorisation juridique d'utilisation des données.
>
> Les informations contractuelles, techniques et d'accès doivent être vérifiées auprès des sources primaires avant toute intégration.

---

# 1. Objectif

Le projet Job Agent doit pouvoir rechercher des offres d'emploi provenant de différentes sources, notamment :

* Dakar ;
* Sénégal ;
* Afrique de l'Ouest ;
* Afrique ;
* international ;
* remote.

L'objectif n'est pas de devenir un simple scraper de plateformes d'emploi.

Le projet cherche à identifier des sources :

1. pertinentes pour les utilisateurs ;
2. techniquement accessibles ;
3. compatibles avec une utilisation autorisée ;
4. suffisamment riches en données ;
5. suffisamment fraîches ;
6. intégrables dans une architecture d'agent ;
7. maintenables dans le temps.

---

# 2. Principe fondamental : source ≠ connecteur

Une **source** est l'endroit où se trouvent les offres.

Un **connecteur** est le mécanisme technique utilisé par Job Agent pour accéder à cette source.

Exemple :

```text
Greenhouse
    ↓
Job Board API
    ↓
Connecteur Job Agent
    ↓
JobOffer normalisé
```

Une même source peut proposer plusieurs méthodes d'accès :

```text
PLATEFORME
    ├── API
    ├── RSS
    ├── Feed partenaire
    ├── HTML public
    └── autre méthode autorisée
```

Le `sources-master.md` décrit principalement **la source et ses possibilités**.

Le `connectors.md` décrit ensuite **l'implémentation technique retenue**.

---

# 3. Principe d'autorisation

L'accessibilité technique ne signifie pas automatiquement que l'utilisation est autorisée.

Il faut distinguer :

```text
Donnée accessible
        ≠
Donnée réutilisable
        ≠
Donnée stockable
        ≠
Donnée redistribuable
        ≠
Donnée utilisable commercialement
```

Pour chaque source, il faut donc examiner séparément :

* lecture ;
* extraction ;
* stockage ;
* cache ;
* affichage ;
* redistribution ;
* attribution ;
* liens vers la source ;
* liens profonds ;
* utilisation commerciale ;
* conservation ;
* candidature ;
* automatisation.

---

# 4. Autorisation utilisateur ≠ autorisation de plateforme

Le consentement de l'utilisateur permet à Job Agent d'utiliser les données ou informations fournies par cet utilisateur.

Il ne donne pas automatiquement le droit d'extraire ou de redistribuer les données d'une plateforme tierce.

Exemple :

```text
Utilisateur autorise Job Agent
        ↓
Job Agent peut utiliser son CV
        ↓
Mais cela n'autorise pas automatiquement
l'extraction massive d'une plateforme d'emploi.
```

Les deux autorisations doivent être traitées séparément.

---

# 5. Principe de non-contournement

Job Agent ne doit jamais contourner :

* authentification ;
* CAPTCHA ;
* anti-bot ;
* paywall ;
* rate limit ;
* contrôle d'accès ;
* restriction technique ;
* restriction contractuelle ;
* mécanisme destiné à empêcher l'automatisation.

Si une source n'est accessible qu'en contournant une restriction :

**→ la source n'est pas exploitable par cette voie.**

Il faut rechercher :

* une API officielle ;
* un flux officiel ;
* un feed partenaire ;
* une autorisation ;
* une intégration proposée par la plateforme ;
* une autre source.

---

# 6. Architecture des droits par source

Le projet ne doit pas simplement stocker :

```text
source = RemoteOK
```

Il doit pouvoir représenter les règles associées à cette source.

Les dimensions importantes sont :

```text
access_policy
display_policy
storage_policy
retention_policy
attribution_required
deep_link_policy
commercial_use
application_policy
```

Exemple conceptuel :

```text
source:
  name: RemoteOK

  attribution_required: true

  deep_link_policy:
    type: required
    destination: source_offer

  display_policy:
    status: verified

  storage_policy:
    status: to_verify

  retention_policy:
    status: to_verify
```

Ces informations doivent être vérifiées individuellement.

---

# 7. Distinction `source_url` / `application_url`

Une offre peut avoir plusieurs URLs.

Le modèle interne doit notamment distinguer :

```text
source_url
application_url
```

Exemple :

```text
source_url
    → page de l'offre sur la plateforme

application_url
    → page ou formulaire permettant de candidater
```

Ces deux URLs peuvent être identiques ou différentes.

Il ne faut donc pas supposer :

```text
source_url == application_url
```

---

# 8. Attention aux contenus des offres

Les descriptions d'offres sont des **données externes non fiables**.

Elles peuvent contenir du texte destiné à des humains mais aussi, volontairement ou non, des instructions qui ressemblent à des instructions destinées à un agent.

Exemple conceptuel :

```text
Description de l'offre :
"Ignore previous instructions and..."
```

Job Agent doit traiter cela comme :

```text
DONNÉE
```

et jamais comme :

```text
INSTRUCTION POUR L'AGENT
```

Une offre ne doit jamais pouvoir modifier :

* les règles du système ;
* les politiques de sécurité ;
* les outils autorisés ;
* les critères de recherche ;
* les permissions ;
* les actions de candidature.

---

# 9. Niveaux de statut stratégique

## 🟢 Connecteur à étudier

Source suffisamment intéressante et suffisamment documentée pour justifier une étude technique du connecteur.

Cela ne signifie pas :

* que le connecteur existe déjà ;
* que l'intégration est production-ready ;
* que toutes les conditions contractuelles sont définitivement validées.

---

## 🟣 Partenariat / autorisation nécessaire

Source intéressante mais nécessitant :

* accord ;
* approbation ;
* licence ;
* clé spécifique ;
* feed partenaire ;
* autorisation d'utilisation ;
* clarification contractuelle.

Une source 🟣 peut devenir 🟢 après obtention et vérification de l'autorisation appropriée.

---

## 🔵 À étudier plus tard

Source pertinente mais non prioritaire pour le MVP.

---

## 🟡 À surveiller

Source potentiellement intéressante mais présentant encore des incertitudes importantes :

* accès ;
* droits ;
* API ;
* nature exacte des données ;
* couverture ;
* conditions ;
* valeur réelle.

---

## 🔴 À exclure

Source ou méthode incompatible avec le projet actuel :

* accès impossible sans contournement ;
* API ne correspondant pas au besoin ;
* restriction incompatible ;
* faible pertinence ;
* absence de voie autorisée identifiable.

---

# 10. Conditions d'utilisation par des tiers

Chaque source doit désormais comporter un niveau de confiance concernant ses conditions d'utilisation :

### Confirmé

Les conditions applicables aux tiers ont été explicitement vérifiées dans une source primaire.

### Probable

Des éléments indiquent une règle mais celle-ci n'est pas encore suffisamment documentée.

### Non vérifié

La documentation nécessaire n'a pas encore été examinée.

Cette distinction est obligatoire avant de considérer une source comme définitivement exploitable.

---

# 11. Master table

| #  | Source                       | Catégorie                        | Couverture                        | Méthode identifiée              | Auth.               | Statut | Conditions tiers                | Données                             | Candidature                            | Valeur MVP                  | Dernière vérification |
| -- | ---------------------------- | -------------------------------- | --------------------------------- | ------------------------------- | ------------------- | ------ | ------------------------------- | ----------------------------------- | -------------------------------------- | --------------------------- | --------------------- |
| 1  | EmploiDakar                  | Job board local                  | Sénégal / Dakar                   | HTML public                     | Non vérifiée        | 🟣     | Confirmées, restrictives        | Offres publiques                    | Formulaire / lien                      | Haute si accord             | 2026-09-19            |
| 2  | Senjob                       | Job board                        | Sénégal / Afrique francophone     | HTML ; RSS à vérifier           | Non vérifiée        | 🟣     | Confirmées, restrictives        | Offres                              | Candidature via plateforme             | Haute si accord             | 2026-09-19            |
| 3  | Ligeey.com                   | Agrégateur / job board           | Afrique francophone               | À vérifier                      | À vérifier          | 🟡     | Non vérifiées                   | À vérifier                          | À vérifier                             | Moyenne                     | 2026-09-19            |
| 4  | Expat-Dakar Emploi           | Classifieds / emploi             | Sénégal                           | HTML public                     | À vérifier          | 🟣     | Confirmées, restrictives        | Offres / annonces                   | À vérifier                             | Faible à moyenne            | 2026-09-19            |
| 5  | Offre-emploi.sn              | Job board / agrégateur potentiel | Sénégal                           | HTML public                     | À vérifier          | 🟡     | Non vérifiées                   | Offres récentes                     | À vérifier                             | Moyenne                     | 2026-09-19            |
| 6  | emploisenegal.com            | Job board                        | Sénégal                           | HTML public                     | À vérifier          | 🟡     | Non vérifiées                   | Offres récentes                     | À vérifier                             | Moyenne à haute             | 2026-09-19            |
| 7  | Talent2Africa                | Recrutement                      | Afrique / francophone             | Web                             | À vérifier          | 🟡     | Non vérifiées                   | Mandats clients                     | À vérifier                             | Moyenne à haute             | 2026-09-19            |
| 8  | Greenhouse Job Board API     | ATS                              | International / employeurs ciblés | API publique GET                | Non pour lecture    | 🟢     | Non vérifiées complètement      | Offres                              | API candidature réservée à l'employeur | Haute                       | 2026-09-19            |
| 9  | Lever Postings API           | ATS                              | International / employeurs ciblés | API publique                    | Non pour lecture    | 🟢     | Non vérifiées complètement      | Offres                              | API candidature employeur              | Haute                       | 2026-09-19            |
| 10 | Ashby Job Posting API        | ATS                              | International / employeurs ciblés | API publique                    | Non pour lecture    | 🟢     | Non vérifiées complètement      | Offres                              | Flux / candidature employeur           | Haute                       | 2026-09-19            |
| 11 | Ashby Partner Feeds          | Feed partenaire ATS              | Employeurs opt-in                 | JSON / XML                      | Accord / activation | 🟣     | À confirmer selon accord        | Offres                              | À vérifier                             | Haute                       | 2026-09-19            |
| 12 | Recruitee Careers Site API   | ATS                              | Employeurs ciblés                 | API publique de lecture         | Non pour lecture    | 🟢     | Non vérifiées complètement      | Offres                              | API ATS employeur                      | Haute                       | 2026-09-19            |
| 13 | Workday Career Sites         | ATS                              | International                     | Endpoints variables             | À vérifier          | 🟡     | Non vérifiées                   | Offres                              | À vérifier                             | Haute si standardisable     | 2026-09-19            |
| 14 | Jobvite                      | ATS                              | International                     | API / accès à vérifier          | À vérifier          | 🟣     | Non vérifiées                   | Offres                              | À vérifier                             | Moyenne                     | 2026-09-19            |
| 15 | iCIMS                        | ATS                              | International                     | API / accès partenaire          | À vérifier          | 🟣     | Non vérifiées                   | Offres                              | À vérifier                             | Moyenne à haute             | 2026-09-19            |
| 16 | SmartRecruiters              | ATS                              | International                     | À vérifier                      | À vérifier          | 🟡     | Non vérifiées                   | Offres                              | À vérifier                             | Haute potentielle           | 2026-09-19            |
| 17 | Personio                     | ATS / HR platform                | Europe / international            | À vérifier                      | À vérifier          | 🟡     | Non vérifiées                   | Offres                              | À vérifier                             | Moyenne                     | 2026-09-19            |
| 18 | Teamtailor                   | ATS                              | International                     | À vérifier                      | À vérifier          | 🟡     | Non vérifiées                   | Offres                              | À vérifier                             | Moyenne à haute             | 2026-09-19            |
| 19 | LinkedIn Jobs API            | Plateforme professionnelle       | International                     | API publication                 | Approbation         | 🔴     | Lecture non disponible          | Publication, pas recherche          | Non adaptée                            | Faible pour MVP             | 2026-09-19            |
| 20 | Indeed Job Sync API          | Job board                        | International                     | API publication/synchronisation | Partenaire          | 🔴     | Non adaptée au besoin           | Gestion d'offres                    | Non adaptée                            | Faible                      | 2026-09-19            |
| 21 | Glassdoor API                | Job board                        | International                     | Accès partenaire                | À vérifier          | 🔴     | Lecture publique non identifiée | À vérifier                          | À vérifier                             | Faible                      | 2026-09-19            |
| 22 | Adzuna API                   | Agrégateur                       | International                     | API REST                        | App ID / clé        | 🟣     | Partiellement confirmées        | Offres                              | À vérifier                             | Moyenne                     | 2026-09-19            |
| 23 | Jooble API                   | Agrégateur                       | International                     | API REST                        | Clé / approbation   | 🟣     | Partiellement vérifiées         | Résultats d'emploi                  | À vérifier                             | Moyenne                     | 2026-09-19            |
| 24 | Devex                        | Job board spécialisé             | Développement / ONG               | API / accès sur demande         | Clé                 | 🟣     | À vérifier                      | Offres spécialisées                 | À vérifier                             | Haute pour ONG              | 2026-09-19            |
| 25 | ReliefWeb Jobs               | Humanitaire / ONU                | International / Afrique           | API officielle                  | Appname approuvé    | 🟣     | API confirmée, contenu tiers    | Offres                              | Lien vers source                       | Haute                       | 2026-09-19            |
| 26 | UN Careers                   | Institutionnel                   | International                     | Portail public                  | À vérifier          | 🟡     | À vérifier                      | Offres ONU                          | Lien                                   | Haute pour certains profils | 2026-09-19            |
| 27 | UN Talent                    | Institutionnel / agrégateur      | International                     | Web                             | À vérifier          | 🟡     | À vérifier                      | Offres                              | Lien                                   | Moyenne                     | 2026-09-19            |
| 28 | RemoteOK                     | Job board remote                 | International                     | JSON / RSS                      | Non                 | 🟢     | Partiellement confirmées        | Offres remote                       | Lien RemoteOK                          | Haute                       | 2026-09-19            |
| 29 | Himalayas                    | Job board remote                 | International                     | JSON / RSS / MCP                | Non                 | 🟢     | Partiellement confirmées        | Offres + restrictions géographiques | Lien Himalayas                         | Haute                       | 2026-09-19            |
| 30 | We Work Remotely             | Job board remote                 | International                     | RSS                             | Non                 | 🟢     | Partiellement vérifiées         | Offres remote                       | Lien WWR                               | Haute                       | 2026-09-19            |
| 31 | Remotive                     | Job board remote                 | International                     | API publique                    | Non                 | 🔵     | Conditions à vérifier           | Offres remote                       | À vérifier                             | Moyenne                     | 2026-09-19            |
| 32 | Dev Global Jobs              | Job board / agrégateur           | Tech / remote                     | API/RSS à vérifier              | À vérifier          | 🟡     | Non vérifiées                   | Offres tech                         | À vérifier                             | Moyenne                     | 2026-09-19            |
| 33 | AI Dev Jobs                  | Job board spécialisé             | IA / tech                         | API/MCP à vérifier              | À vérifier          | 🟡     | Non vérifiées                   | Offres IA/tech                      | À vérifier                             | Moyenne                     | 2026-09-19            |
| 34 | Techmap Job Postings         | Agrégateur / feed                | International                     | RSS / API à vérifier            | À vérifier          | 🟡     | Non vérifiées                   | Offres tech                         | À vérifier                             | Moyenne                     | 2026-09-19            |
| 35 | Ever Jobs                    | Agrégateur                       | International                     | API à vérifier                  | À vérifier          | 🟡     | Non vérifiées                   | Agrégées                            | À vérifier                             | Faible à moyenne            | 2026-09-19            |
| 36 | Upwork                       | Freelance                        | International                     | API partenaire                  | Approbation         | 🟣     | À vérifier                      | Missions freelance                  | API / plateforme                       | Moyenne                     | 2026-09-19            |
| 37 | Freelancer.com               | Freelance                        | International                     | API partenaire                  | Approbation         | 🟣     | À vérifier                      | Missions freelance                  | API                                    | Moyenne                     | 2026-09-19            |
| 38 | Fiverr                       | Freelance                        | International                     | Pas de voie adaptée identifiée  | —                   | 🔴     | À vérifier                      | Missions freelance                  | —                                      | Faible                      | 2026-09-19            |
| 39 | Malt                         | Freelance                        | Europe / international            | Pas d'API publique identifiée   | —                   | 🔴     | À vérifier                      | Missions freelance                  | —                                      | Faible pour MVP             | 2026-09-19            |
| 40 | France Travail API           | Institutionnel                   | France                            | REST / OAuth                    | OAuth               | 🔵     | API officielle                  | Offres France                       | À vérifier                             | Faible pour Dakar           | 2026-09-19            |
| 41 | Emploitic                    | Job board                        | Algérie                           | API tierce potentielle          | À vérifier          | 🟣     | À vérifier                      | Offres                              | À vérifier                             | Moyenne                     | 2026-09-19            |
| 42 | Emploi.ma                    | Job board                        | Maroc                             | API tierce potentielle          | À vérifier          | 🟣     | À vérifier                      | Offres                              | À vérifier                             | Moyenne                     | 2026-09-19            |
| 43 | Coworkies                    | Job board                        | International / francophone       | API à vérifier                  | À vérifier          | 🔵     | À vérifier                      | Offres                              | À vérifier                             | Faible à moyenne            | 2026-09-19            |
| 44 | Arbeitnow                    | Job board remote / Europe        | Europe                            | API / RSS à vérifier            | À vérifier          | 🔵     | Non vérifiées                   | Offres                              | À vérifier                             | Faible pour MVP             | 2026-09-19            |
| 45 | BrighterMonday               | Job board                        | Afrique de l'Est                  | Web                             | À vérifier          | 🔴     | Non vérifiées                   | Offres                              | À vérifier                             | Faible pour MVP             | 2026-09-19            |
| 46 | Jobberman                    | Job board                        | Nigeria                           | Web                             | À vérifier          | 🔴     | Non vérifiées                   | Offres                              | À vérifier                             | Faible pour MVP             | 2026-09-19            |
| 47 | Fuzu                         | Job board                        | Afrique de l'Est                  | Web                             | À vérifier          | 🔴     | Non vérifiées                   | Offres                              | À vérifier                             | Faible pour MVP             | 2026-09-19            |
| 48 | ProGigFinder                 | Job board                        | International                     | Web                             | À vérifier          | 🔴     | Non vérifiées                   | Offres                              | À vérifier                             | Faible                      | 2026-09-19            |
| 49 | BurkinaEmploi / FasoEmploi   | Job board local                  | Burkina Faso                      | HTML                            | À vérifier          | 🔵     | À vérifier                      | Offres                              | À vérifier                             | Secondaire                  | 2026-09-19            |
| 50 | GalsenDev / communautés tech | Communauté                       | Sénégal                           | À identifier                    | À vérifier          | 🟡     | À vérifier                      | Opportunités communautaires         | Variable                               | Potentiellement haute       | 2026-09-19            |

---

# 12. Sources prioritaires pour le MVP

Le MVP doit commencer avec un nombre limité de sources.

## Groupe A — Remote immédiatement exploitable

### RemoteOK 🟢

Méthodes identifiées :

* JSON ;
* RSS.

Points importants :

* pas d'authentification pour le flux public ;
* attribution requise ;
* lien vers RemoteOK requis ;
* `apply_url` peut également pointer vers RemoteOK ;
* les données de localisation peuvent être incomplètes.

**Point architectural :**

Ne jamais considérer une offre remote comme automatiquement accessible depuis Dakar.

L'éligibilité géographique doit être analysée séparément.

---

### Himalayas 🟢

Méthodes identifiées :

* JSON ;
* RSS ;
* MCP.

Caractéristiques identifiées :

* données structurées ;
* pagination par curseur ;
* restrictions géographiques disponibles ;
* mises à jour régulières ;
* attribution requise.

Himalayas est particulièrement intéressant pour le matching géographique car les restrictions de localisation peuvent être structurées.

---

### We Work Remotely 🟢

Méthode identifiée :

* RSS public.

Points importants :

* flux par catégorie ;
* attribution / liens demandés ;
* l'API évoquée par la plateforme concerne la publication d'offres et non une API générale de recherche adaptée au MVP.

À documenter davantage avant implémentation.

---

# 13. ATS : stratégie spécifique

Les ATS ne constituent pas une seule source globale.

Le modèle est plutôt :

```text
ATS
  ↓
Entreprise A
  ↓
Job board de l'entreprise

ATS
  ↓
Entreprise B
  ↓
Job board de l'entreprise
```

Ainsi :

```text
Greenhouse ≠ moteur global de recherche
Lever ≠ moteur global de recherche
Ashby ≠ moteur global de recherche
```

Il faut donc développer une stratégie de **découverte des employeurs**.

Sources possibles :

* liste d'entreprises ciblées ;
* employeurs fournis par l'utilisateur ;
* flux partenaires ;
* domaines d'entreprises connus ;
* sources secondaires permettant d'identifier les entreprises ;
* recherche ciblée.

---

# 14. Greenhouse 🟢

API officielle de lecture des Job Boards.

Lecture publique possible pour les offres d'un employeur.

La candidature via API nécessite des credentials liés à l'employeur.

Pour Job Agent :

```text
Lecture : exploitable
Matching : exploitable
Lien candidature : exploitable
Candidature automatique via API : non sans accès employeur
```

Le statut 🟢 concerne donc principalement **la lecture**.

Les conditions d'utilisation pour les tiers doivent encore être vérifiées complètement.

---

# 15. Lever 🟢

API Postings publique pour les offres d'un employeur.

Même principe architectural que Greenhouse :

```text
Entreprise ciblée
      ↓
Job board Lever
      ↓
API publique
      ↓
Job Agent
```

La candidature automatisée via API nécessite des credentials associés au compte employeur.

Pour le MVP :

```text
lecture → oui
matching → oui
redirection → oui
soumission automatique → non sans accès employeur
```

---

# 16. Ashby 🟢

API publique de Job Postings pour les organisations.

Point important :

Certaines offres peuvent être configurées pour être accessibles uniquement par lien direct.

Il faut donc respecter les indicateurs de visibilité fournis par Ashby.

### Ashby Partner Feeds

Ashby propose également un mécanisme officiel de flux partenaires opt-in.

Le partage est activé par les organisations participantes et les flux peuvent être fournis sous forme JSON ou XML.

Cette voie est particulièrement intéressante pour une architecture d'agrégation autorisée.

Elle doit être traitée comme une **voie d'intégration distincte** de l'API publique.

---

# 17. Recruitee 🟢

La Careers Site API permet la lecture publique des offres d'une entreprise sans authentification.

Elle est donc conceptuellement proche de :

* Greenhouse ;
* Lever ;
* Ashby.

Attention :

L'API ATS destinée à la gestion du compte employeur est différente et nécessite des credentials.

Pour Job Agent :

```text
lecture publique des offres → exploitable
gestion ATS → non nécessaire
candidature automatique → non disponible sans accès employeur
```

---

# 18. ReliefWeb 🟣

ReliefWeb est particulièrement intéressant pour :

* ONG ;
* humanitaire ;
* développement international ;
* organisations internationales ;
* postes potentiellement pertinents pour Dakar.

Une API officielle existe.

Cependant, depuis novembre 2025, l'utilisation de l'API nécessite un `appname` préalablement approuvé.

La voie correcte est donc :

```text
Demande officielle
      ↓
Approbation
      ↓
appname
      ↓
API
      ↓
Connecteur
```

Ne pas utiliser de scraper prétendant contourner cette exigence.

---

# 19. Sources sénégalaises

Le volet sénégalais est stratégique mais présente actuellement un problème :

```text
Pertinence locale élevée
        +
Accès / droits insuffisamment établis
```

Il ne faut donc pas considérer les sources locales comme directement exploitables tant que leurs conditions ne sont pas clarifiées.

---

## EmploiDakar 🟣

Source fortement pertinente pour Dakar.

Les CGU vérifiées indiquent notamment :

* consultation personnelle et privée ;
* restrictions sur la diffusion ;
* interdiction de liens profonds ;
* interdiction d'extraction de bases ;
* accord écrit préalable pour d'autres usages.

Conséquence :

L'accord éventuel doit couvrir explicitement :

```text
extraction
stockage
affichage
redistribution
liens profonds
utilisation par Job Agent
```

Il faut également clarifier l'identité de l'entité juridique concernée avant toute démarche.

---

## Senjob 🟣

Les conditions publiées contiennent notamment des restrictions concernant :

* reproduction ;
* usage hors cadre personnel ;
* liens vers le site sans autorisation.

Un flux `/rss/` a été identifié mais son contenu n'a pas encore été suffisamment vérifié pour être considéré comme un flux d'offres exploitable.

Une autorisation spécifique devrait être étudiée.

---

## Expat-Dakar 🟣

Les conditions publiées comportent des restrictions concernant notamment :

* reproduction ;
* redistribution à des tiers ;
* œuvres dérivées ;
* réutilisation des informations.

La présence d'annonces pouvant contenir des informations personnelles renforce également la nécessité d'une analyse spécifique.

Priorité MVP basse tant qu'une autorisation n'est pas obtenue.

---

## Talent2Africa 🟡

Talent2Africa est principalement un acteur du recrutement.

Ses offres peuvent correspondre à des mandats de recrutement pour ses clients.

Aucune API publique suffisamment vérifiée n'a été identifiée.

Il faut donc déterminer :

```text
qui produit l'offre ?
qui possède les données ?
qui autorise leur réutilisation ?
quelle méthode d'accès est prévue ?
```

---

## Offre-emploi.sn 🟡

Le site est actif et publie des offres au Sénégal.

La nature exacte de la source reste à déterminer :

```text
source primaire ?
agrégateur ?
republication ?
```

Les conditions de réutilisation doivent être étudiées avant toute intégration.

---

## emploisenegal.com 🟡

Source présentant un intérêt potentiel pour le marché sénégalais.

Des offres récentes ont été observées.

Les CGU/CGV et les modalités de réutilisation doivent encore être vérifiées.

---

# 20. Adzuna 🟣

API REST officielle.

Accès via :

* `app_id` ;
* `app_key`.

Les quotas par défaut identifiés sont :

* 25 requêtes/minute ;
* 250/jour ;
* 1000/semaine ;
* 2500/mois.

Des règles d'attribution s'appliquent.

L'utilisation commerciale et certains usages dépassant la recherche personnelle nécessitent une licence ou un accord approprié.

La couverture exacte du Sénégal doit être confirmée dans la documentation primaire.

---

# 21. Jooble 🟣

API officielle avec clé obtenue via une procédure d'approbation.

Les conditions exactes concernant :

* quotas ;
* couverture Sénégal ;
* stockage ;
* redistribution ;
* utilisation commerciale ;

doivent encore être vérifiées dans les sources primaires.

Ne pas reprendre comme fait le quota de 500 requêtes précédemment mentionné par des sources secondaires tant qu'il n'est pas confirmé officiellement.

---

# 22. LinkedIn 🔴 pour la recherche d'offres

L'API d'emploi documentée concerne la **publication et la gestion d'offres pour des partenaires approuvés**.

Elle ne constitue pas une API publique de recherche permettant à Job Agent de récupérer librement les offres LinkedIn.

Elle ne doit donc pas être considérée comme une source de lecture exploitable pour le MVP.

Le projet ne doit pas utiliser le scraping ou l'automatisation non autorisée pour remplacer cette absence d'API.

---

# 23. Indeed 🔴 pour le besoin actuel

L'API Job Sync étudiée est destinée à la synchronisation / gestion des offres avec Indeed.

Elle ne constitue pas une API générale permettant à Job Agent de rechercher et récupérer les offres Indeed comme moteur de recherche.

Elle ne répond donc pas au besoin principal du MVP.

---

# 24. Remotive 🔵

Source intéressante dans la catégorie remote.

Une API publique existe avec des limites d'utilisation.

Cependant :

* les conditions d'utilisation doivent être vérifiées ;
* certaines restrictions concernent l'affichage et la collecte d'inscriptions ;
* l'API privée / commerciale suit un autre régime.

Remotive est à étudier après les trois premières sources remote.

---

# 25. Déduplication

Une même offre peut apparaître sur plusieurs sources.

Exemple :

```text
Employeur
   ↓
Ashby
   ↓
Agrégateur
   ↓
Site local
```

Job Agent doit éviter de considérer ces annonces comme quatre offres différentes.

La priorité doit être donnée à l'identifiant de la source primaire lorsque celui-ci est disponible.

Le système doit pouvoir conserver :

```text
primary_source
secondary_sources[]
source_ids[]
```

Les droits applicables doivent également être déterminés selon la source réellement utilisée.

---

# 26. Matching géographique

Le terme `remote` ne suffit pas.

Une offre peut être :

```text
Remote — USA only
Remote — Europe only
Remote — South Africa
Remote — Worldwide
Remote — Africa
Remote — Senegal
```

Le moteur de matching doit donc analyser :

```text
candidate_location
allowed_locations
location_restrictions
remote_policy
```

Exemple :

```text
Utilisateur :
Dakar, Sénégal

Offre :
Remote
USA only

Résultat :
NON ÉLIGIBLE
```

L'éligibilité géographique est donc un **critère de filtrage**, pas seulement un facteur de classement.

---

# 27. Modèle interne minimal `JobOffer`

Le modèle interne devra progressivement pouvoir représenter :

```text
JobOffer

id
source
source_offer_id

title
company
description

location
location_restrictions
remote_policy

employment_type
experience_level
salary

skills
technologies

published_at
updated_at

source_url
application_url

retrieved_at

attribution_required
deep_link_policy
display_policy
storage_policy
retention_policy

primary_source
secondary_sources[]

raw_data
normalized_data
```

Le modèle évoluera après étude des connecteurs.

---

# 28. Qualité des données

Pour chaque source, il faut examiner :

* fraîcheur ;
* complétude ;
* structure ;
* stabilité ;
* pagination ;
* filtres ;
* identifiants ;
* dates ;
* localisation ;
* salaire ;
* entreprise ;
* URL ;
* candidature ;
* doublons.

Une source avec beaucoup d'offres mais peu de données structurées peut être moins utile qu'une source plus petite mais mieux structurée.

---

# 29. Règle concernant les API de candidature

Le fait qu'une plateforme possède une API de candidature ne signifie pas que Job Agent peut l'utiliser.

Les API de candidature des ATS étudiés sont généralement liées au compte employeur.

Pour le MVP :

```text
Recherche
      ↓
Matching
      ↓
Recommandation
      ↓
Utilisateur valide
      ↓
Ouverture de la candidature
```

La soumission automatique ne doit être envisagée que lorsqu'une méthode officiellement autorisée est disponible.

---

# 30. Priorité géographique

Ordre de priorité :

```text
1. Dakar
2. Sénégal
3. Afrique de l'Ouest
4. Afrique
5. International
6. Remote international
```

Cependant, une source internationale peut être intégrée avant une source locale si :

* son accès est clairement autorisé ;
* son intégration est simple ;
* sa valeur MVP est élevée.

L'objectif est donc :

```text
pertinence × accessibilité × autorisation × qualité
```

et non simplement :

```text
nombre d'offres
```

---

# 31. Sources à étudier en priorité

## Priorité technique immédiate

```text
RemoteOK
Himalayas
We Work Remotely
Greenhouse
Lever
Ashby
Recruitee
```

## Priorité autorisation / partenariat

```text
ReliefWeb
EmploiDakar
Senjob
Jooble
Adzuna
```

## Priorité investigation locale

```text
Talent2Africa
Offre-emploi.sn
emploisenegal.com
Ligeey
GalsenDev / communautés tech
```

## Priorité secondaire

```text
Remotive
SmartRecruiters
Workday
Personio
Teamtailor
Devex
UN Careers
UN Talent
```

---

# 32. Démarches parallèles recommandées

Le projet ne doit pas attendre la fin de toutes les vérifications.

Trois pistes peuvent avancer en parallèle.

### Piste A — connecteurs publics

```text
RemoteOK
Himalayas
WWR
Greenhouse
Lever
Ashby
Recruitee
```

### Piste B — autorisations

```text
ReliefWeb
EmploiDakar
Senjob
Jooble
Adzuna
```

### Piste C — investigation Sénégal

```text
Talent2Africa
Offre-emploi.sn
emploisenegal.com
Ligeey
```

Cela permet de travailler sur l'architecture pendant que les démarches d'accès avancent.

---

# 33. Quand une source peut passer dans `connectors.md`

Une source ne doit être ajoutée à `connectors.md` qu'après avoir suffisamment déterminé :

1. méthode d'accès ;
2. endpoint/feed ;
3. authentification ;
4. autorisation ;
5. données disponibles ;
6. pagination ;
7. fréquence ;
8. limites ;
9. conditions d'utilisation ;
10. méthode de candidature ;
11. règles d'attribution ;
12. règles de stockage ;
13. règles d'affichage.

Ensuite seulement :

```text
sources-master.md
        ↓
source validée
        ↓
connectors.md
        ↓
implémentation
```

---

# 34. Fiche de vérification par source

Chaque source importante doit disposer d'une fiche de vérification.

```text
SOURCE :
CATÉGORIE :
DATE DE VÉRIFICATION :

1. API officielle ?
2. Documentation officielle ?
3. Authentification ?
4. Données accessibles ?
5. Pagination ?
6. Rate limit ?
7. Stockage autorisé ?
8. Affichage autorisé ?
9. Redistribution autorisée ?
10. Utilisation commerciale ?
11. Attribution requise ?
12. Deep links autorisés ?
13. Conservation / rétention ?
14. Lien de candidature ?
15. API de candidature ?
16. Restrictions ?
17. Couverture géographique ?
18. Fraîcheur ?
19. Valeur pour Job Agent ?

CONDITIONS TIERS :
Confirmé / Probable / Non vérifié

SOURCES PRIMAIRES :
-

SOURCES SECONDAIRES :
-

INFORMATIONS INCERTAINES :
-

VERDICT :
🟢 / 🟣 / 🔵 / 🟡 / 🔴
```

---

# 35. Règle de vérification

Les sources primaires sont prioritaires :

1. documentation officielle ;
2. API officielle ;
3. conditions d'utilisation officielles ;
4. licence officielle ;
5. page développeur officielle ;
6. documentation juridique officielle.

Les sources secondaires servent principalement à :

* découvrir une source ;
* identifier une piste ;
* signaler un changement ;
* trouver un document primaire.

Elles ne doivent pas être utilisées seules pour conclure sur :

* les droits ;
* les quotas ;
* les autorisations ;
* les fonctionnalités officielles.

---

# 36. Règle de prudence

Si une information n'est pas vérifiée :

```text
NE PAS DEVINER
```

Utiliser :

```text
À vérifier
```

ou :

```text
Non vérifié
```

Une information inconnue est préférable à une information inventée.

---

# 37. Historique des corrections V3 → V4

| Source / élément      | V3      | V4        | Motif                                         |
| --------------------- | ------- | --------- | --------------------------------------------- |
| EmploiDakar           | 🟣      | 🟣        | Restrictions CGU précisées                    |
| Senjob                | 🟡      | 🟣        | Restrictions d'utilisation confirmées         |
| Expat-Dakar           | 🟡      | 🟣        | Restrictions de reproduction / redistribution |
| LinkedIn              | 🟣      | 🔴        | Pas d'API de lecture adaptée                  |
| Recruitee             | 🟣      | 🟢        | Careers Site API publique de lecture          |
| ReliefWeb             | 🟡      | 🟣        | API officielle avec appname approuvé          |
| RemoteOK              | 🟢      | 🟢        | Attribution et lien RemoteOK précisés         |
| WWR                   | 🟢      | 🟢        | RSS confirmé ; fiche à compléter              |
| Ashby                 | 🟢      | 🟢        | Programme Partner Feed ajouté                 |
| Adzuna                | 🟣      | 🟣        | Conditions et quotas mieux documentés         |
| Jooble                | 🟣      | 🟣        | Quotas/couverture encore à vérifier           |
| Remotive              | absent  | 🔵        | Nouvelle source remote                        |
| emploisenegal.com     | absent  | 🟡        | Nouvelle piste locale                         |
| Offre-emploi.sn       | 🟡      | 🟡        | Nature de la source encore à déterminer       |
| Workable              | absent  | À étudier | ATS manquant à examiner                       |
| SmartRecruiters       | absent  | 🟡        | ATS à examiner                                |
| Personio              | absent  | 🟡        | ATS à examiner                                |
| Teamtailor            | absent  | 🟡        | ATS à examiner                                |
| Conditions tiers      | absent  | Ajouté    | Nouvelle dimension obligatoire                |
| Dernière vérification | absent  | Ajouté    | Traçabilité                                   |
| Deep link policy      | absent  | Ajouté    | Restrictions variables selon les sources      |
| Attribution           | partiel | Ajouté    | Obligations variables selon les sources       |
| Injection de contenu  | absent  | Ajouté    | Sécurité agent                                |

---

# 38. État actuel du projet

À ce stade, le registre permet de distinguer trois réalités :

```text
                    JOB AGENT
                       │
        ┌──────────────┼──────────────┐
        │              │              │
   Accès public    Autorisation    Investigation
        │              │              │
        ▼              ▼              ▼
 RemoteOK          ReliefWeb      Sénégal
 Himalayas         EmploiDakar    Senjob
 WWR               Adzuna         Talent2Africa
 Greenhouse        Jooble         etc.
 Lever
 Ashby
 Recruitee
```

Le projet peut donc commencer l'étude technique des connecteurs publics tout en poursuivant les démarches d'autorisation et la recherche de sources locales.

---

# 39. Règle directrice

> **Une source n'est pas intéressante uniquement parce qu'elle contient beaucoup d'offres.**
>
> Elle devient intéressante lorsque Job Agent peut obtenir des données pertinentes, suffisamment fraîches et suffisamment structurées, par une méthode techniquement viable et juridiquement/contractuellement compatible avec l'utilisation envisagée.

Et :

> **L'absence d'API publique ne signifie pas automatiquement qu'une source est inutilisable.**
>
> Une autorisation, un flux partenaire, un feed officiel ou une intégration dédiée peut constituer une voie valide.

Enfin :

> **Job Agent doit adapter son architecture aux règles de chaque source, et non supposer que toutes les plateformes fonctionnent de la même manière.**

---

# 40. Prochaine étape

Une fois cette V4 validée, le travail passe de :

```text
RECHERCHE DE SOURCES
```

à :

```text
ÉTUDE DES CONNECTEURS
```

L'ordre recommandé pour le premier cycle est :

```text
1. RemoteOK
2. Himalayas
3. We Work Remotely
4. Greenhouse
5. Lever
6. Ashby
7. Recruitee
8. ReliefWeb
```

Pour chaque source :

```text
source
  ↓
méthode d'accès
  ↓
endpoint/feed
  ↓
authentification
  ↓
données retournées
  ↓
normalisation
  ↓
déduplication
  ↓
gestion des erreurs
  ↓
JobOffer
```

Le résultat de cette étude sera documenté dans `connectors.md`.
