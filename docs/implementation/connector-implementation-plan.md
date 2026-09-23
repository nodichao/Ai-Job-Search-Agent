# Connector Implementation Plan --- Job Agent

> **Statut du document :** référentiel technique d'implémentation\
> **Périmètre :** premier cycle de 8 sources\
> **Sources :** RemoteOK, Himalayas, We Work Remotely, Greenhouse,
> Lever, Ashby, Recruitee, ReliefWeb\
> **Principe :** ce document décrit comment organiser et implémenter les
> connecteurs. Il ne remplace ni `sources-master.md`, ni
> `research-protocol.md`, ni `connectors.md`.

------------------------------------------------------------------------

## 1. Objectif

Construire une architecture de connecteurs réutilisable permettant à Job
Agent de récupérer des offres depuis plusieurs sources hétérogènes et de
les transformer vers un modèle interne commun `JobOffer`.

Le système doit :

-   isoler les spécificités de chaque source ;
-   mutualiser au maximum l'infrastructure technique ;
-   éviter de réécrire le même code de transport pour chaque source ;
-   gérer authentification, pagination, limites, erreurs et retries
    lorsque nécessaire ;
-   parser et normaliser les données ;
-   produire des `JobOffer` ;
-   permettre la déduplication au niveau source et au niveau global ;
-   rester maintenable lorsque les sources évoluent.

L'architecture de référence du projet est :

``` text
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

------------------------------------------------------------------------

## 2. Rôle des documents de référence

Les responsabilités doivent rester séparées :

``` text
sources-master.md
        =
QUELLES SOURCES ?

research-protocol.md
        =
COMMENT DÉCIDER ET VÉRIFIER ?

connectors.md
        =
COMMENT LES INTÉGRER ?

connector-implementation-plan.md
        =
COMMENT ORGANISER L'IMPLÉMENTATION ?
```

Ce fichier sert donc de **plan directeur technique** pour un développeur
ou un outil d'implémentation.

Il ne doit pas être utilisé pour inventer ou confirmer une autorisation,
un endpoint, une limite ou une capacité qui n'est pas vérifiée dans les
documents de référence ou dans la documentation officielle de la source.

------------------------------------------------------------------------

## 3. Principes impératifs

### 3.1 Ne jamais inventer

L'implémentation ne doit jamais inventer :

-   un endpoint ;
-   une méthode d'authentification ;
-   une permission ;
-   une limite ;
-   une pagination ;
-   une capacité de candidature ;
-   une licence ;
-   une condition d'utilisation.

Lorsqu'une information n'est pas suffisamment vérifiée :

``` text
À vérifier
```

doit rester la valeur de référence.

### 3.2 Ne pas confondre accès et autorisation

``` text
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

L'existence d'un endpoint public ne constitue donc pas, à elle seule,
une autorisation générale d'utilisation.

### 3.3 Aucun contournement

Le système ne doit pas contourner :

-   authentification ;
-   CAPTCHA ;
-   anti-bot ;
-   rate limiting ;
-   restrictions d'accès ;
-   paywall ;
-   mécanismes destinés à empêcher l'automatisation ;
-   restrictions contractuelles.

Un retry ne doit jamais servir à contourner une restriction.

### 3.4 Données externes non fiables

Les descriptions d'offres et autres champs récupérés depuis une source
externe sont des **données**, pas des instructions pour l'agent.

Une donnée provenant d'une offre ne doit jamais devenir une instruction
système ou une instruction de contrôle de l'agent.

------------------------------------------------------------------------

## 4. Architecture technique cible

### 4.1 Vue générale

``` text
                         CONNECTOR SYSTEM
                                │
                 ┌──────────────┴──────────────┐
                 │                             │
           HTTP / JSON                    RSS / XML
                 │                             │
          HttpJsonFetcher                  RssFetcher
                 │                             │
       ┌─────────┼──────────────┐             │
       │         │              │             │
    RemoteOK  Himalayas      ATS/API          WWR
                              │
                  ┌───────────┼───────────┐
                  │           │           │
              Greenhouse    Lever      Ashby
                  │           │           │
              Recruitee    ReliefWeb      │
                  │           │           │
                  └───────────┴───────────┘
                              │
                       Source Parser
                              │
                        Transformation
                              │
                         Normalization
                              │
                         Deduplication
                              │
                           JobOffer
```

La représentation ci-dessus est une **architecture de travail**. Elle ne
signifie pas que les sept sources JSON disposent des mêmes
fonctionnalités métier.

------------------------------------------------------------------------

## 5. Mutualisation du code

### 5.1 Transport

Créer un socle commun de transport :

``` text
HttpJsonFetcher
RssFetcher
```

Responsabilités communes :

-   requête HTTP ;
-   timeout ;
-   headers ;
-   gestion de réponse ;
-   gestion des erreurs réseau ;
-   logging ;
-   retry selon politique ;
-   respect des limites.

### 5.2 Pagination

Prévoir une abstraction de pagination :

``` text
Paginator
├── NoPagination
├── CursorPaginator
└── PagePaginator
```

Ne sélectionner une stratégie pour une source que lorsque sa
documentation permet de la confirmer.

### 5.3 Authentification

Prévoir une abstraction :

``` text
AuthStrategy
├── NoAuth
├── ApiKey
├── BearerToken
└── PartnerCredentials
```

Ne jamais stocker de secrets dans les fichiers de documentation ou dans
le code source.

Les valeurs réelles doivent rester dans un gestionnaire de secrets ou
dans des variables d'environnement.

### 5.4 Retry

Prévoir une politique de retry centralisée :

``` text
RetryPolicy
```

Elle doit distinguer :

``` text
Erreur temporaire
    → retry possible

Refus d'autorisation
    → pas de retry automatique pour contourner

Rate limit
    → respecter la règle de la source

CAPTCHA / anti-bot
    → aucun contournement
```

------------------------------------------------------------------------

## 6. Contrat conceptuel d'un connecteur

Chaque connecteur doit présenter une interface homogène au reste du
système.

Conceptuellement :

``` text
Connector
├── fetch()
├── parse()
├── normalize()
└── deduplicate()
```

Le détail interne peut varier selon la source.

Exemple :

``` text
RemoteOKConnector
      ↓
HttpJsonFetcher
      ↓
RemoteOKParser
      ↓
JobOfferNormalizer
      ↓
Deduplication
```

et :

``` text
WWRConnector
      ↓
RssFetcher
      ↓
WWRParser
      ↓
JobOfferNormalizer
      ↓
Deduplication
```

------------------------------------------------------------------------

## 7. Matrice technique des 8 sources

  ------------------------------------------------------------------------------------------------------------------
  Source       Famille   Format    Méthode      Authentification   Pagination   Particularité   Parser
               de fetch            étudiée                                                      
  ------------ --------- --------- ------------ ------------------ ------------ --------------- --------------------
  RemoteOK     HTTP JSON JSON      GET          À confirmer selon  À vérifier   Feed global     `RemoteOKParser`
                                                usage                           d'offres        

  Himalayas    HTTP JSON JSON      GET          Accès public       Curseur      Filtres         `HimalayasParser`
                                                identifié ; usage               disponibles     
                                                à clarifier                                     

  We Work      HTTP RSS  RSS/XML   GET          RSS public         Pas de       Feed RSS        `WWRParser`
  Remotely                                                         pagination                   
                                                                   API                          
                                                                   classique                    

  Greenhouse   HTTP JSON JSON      GET          Public pour Job    À vérifier   Par employeur / `GreenhouseParser`
                                                Board              selon        board           
                                                                   endpoint                     

  Lever        HTTP JSON JSON      GET          Public pour        À vérifier   Par entreprise  `LeverParser`
                                                postings                                        

  Ashby        HTTP JSON JSON      GET / flux   Selon méthode /    À définir    Par             `AshbyParser`
                                   partenaire   partenaire         selon feed   organisation /  
                                   selon accès                                  Partner Feed    

  Recruitee    HTTP JSON JSON      GET          Token à intégrer   À vérifier   Par site        `RecruiteeParser`
                                                                                carrière /      
                                                                                entreprise      

  ReliefWeb    HTTP JSON JSON      GET          `appname` /        Pagination   API V2, filtres `ReliefWebParser`
                                                approbation        API          riches          
  ------------------------------------------------------------------------------------------------------------------

**Important :** les valeurs `À vérifier`, `À confirmer` et `selon accès`
ne doivent pas être remplacées par des hypothèses pendant
l'implémentation.

------------------------------------------------------------------------

## 8. Statut actuel des connecteurs

À l'issue de l'étude actuelle :

``` text
🔵 Spécification en cours
├── RemoteOK
├── Greenhouse
└── Lever

🟣 En attente d'accès
├── Himalayas
├── We Work Remotely
├── Ashby
├── Recruitee
└── ReliefWeb
```

Aucun des huit connecteurs n'est actuellement considéré comme :

``` text
🟢 Opérationnel
```

Un connecteur ne doit passer en opérationnel qu'après validation réelle
des critères définis dans `connectors.md`.

------------------------------------------------------------------------

## 9. Spécificités par source

### 9.1 RemoteOK

Famille :

``` text
HTTP → JSON
```

Composants :

``` text
HttpJsonFetcher
RemoteOKParser
JobOfferNormalizer
Deduplication
```

Le parsing doit notamment tenir compte des données externes pouvant
contenir du HTML.

Les règles d'attribution, de deep link, de stockage et de rétention
doivent rester conformes aux informations vérifiées dans le référentiel
des connecteurs.

------------------------------------------------------------------------

### 9.2 Himalayas

Famille :

``` text
HTTP → JSON
```

Composants :

``` text
HttpJsonFetcher
CursorPaginator
HimalayasParser
JobOfferNormalizer
Deduplication
```

La pagination par curseur doit être implémentée uniquement selon la
documentation vérifiée.

Les conditions d'utilisation et l'autorisation correspondant à
l'utilisation envisagée par Job Agent doivent être résolues avant de
considérer le connecteur comme opérationnel.

------------------------------------------------------------------------

### 9.3 We Work Remotely

Famille :

``` text
HTTP → RSS/XML
```

Composants :

``` text
RssFetcher
WWRParser
JobOfferNormalizer
Deduplication
```

Le RSS doit être traité comme une méthode distincte du transport JSON.

L'existence d'un RSS public ne doit pas être interprétée automatiquement
comme une autorisation générale pour un service d'agrégation.

------------------------------------------------------------------------

### 9.4 Greenhouse

Famille :

``` text
HTTP → JSON
```

Composants :

``` text
HttpJsonFetcher
GreenhouseParser
JobOfferNormalizer
Deduplication
```

Particularité :

``` text
Job Board API
      ↓
Employer / Board
      ↓
Jobs
```

Ce n'est pas à traiter comme un moteur global de recherche Greenhouse.

L'architecture doit donc pouvoir gérer l'identification des
boards/employeurs si cette voie est retenue.

------------------------------------------------------------------------

### 9.5 Lever

Famille :

``` text
HTTP → JSON
```

Composants :

``` text
HttpJsonFetcher
LeverParser
JobOfferNormalizer
Deduplication
```

Particularité :

``` text
Entreprise
   ↓
Postings
   ↓
Offers
```

L'API de postings doit être distinguée des éventuelles capacités de
candidature côté employeur.

------------------------------------------------------------------------

### 9.6 Ashby

Famille :

``` text
HTTP → JSON
```

Voies identifiées :

``` text
Job Posting API
ou
Partner Job Feed
```

Pour une agrégation multi-employeurs, le flux partenaire doit être
traité comme une voie nécessitant l'accès approprié.

Composants possibles :

``` text
HttpJsonFetcher
AshbyParser
JobOfferNormalizer
Deduplication
```

La méthode finale dépendra de l'accès effectivement obtenu.

------------------------------------------------------------------------

### 9.7 Recruitee

Famille :

``` text
HTTP → JSON
```

Composants :

``` text
HttpJsonFetcher
RecruiteeParser
JobOfferNormalizer
Deduplication
```

Particularité :

``` text
Career Site
   ↓
Company / Site
   ↓
Jobs
```

L'authentification/token et les conditions d'accès doivent être
implémentés selon la documentation actuelle vérifiée.

------------------------------------------------------------------------

### 9.8 ReliefWeb

Famille :

``` text
HTTP → JSON
```

Composants :

``` text
HttpJsonFetcher
Paginator
ReliefWebParser
JobOfferNormalizer
Deduplication
```

Particularités :

-   API V2 ;
-   filtres ;
-   pagination ;
-   mécanisme `appname` / approbation à prendre en compte ;
-   droits sur les contenus tiers à considérer séparément.

L'accès à l'API ne doit pas être assimilé automatiquement à un droit
général de redistribution de tous les contenus récupérés.

------------------------------------------------------------------------

## 10. Modèle interne `JobOffer`

Le connecteur doit produire un modèle commun.

Modèle conceptuel :

``` text
JobOffer
├── id
├── source
├── source_offer_id
├── title
├── company
├── location
├── country
├── description
├── contract_type
├── employment_type
├── salary
├── experience_level
├── skills
├── posted_at
├── application_url
├── source_url
└── retrieved_at
```

Le modèle réel pourra évoluer.

Une source peut fournir plus ou moins de champs. L'absence d'un champ ne
doit pas être considérée automatiquement comme une erreur.

------------------------------------------------------------------------

## 11. Normalisation

La normalisation permet au reste du Job Agent de fonctionner
indépendamment de la source.

Exemples conceptuels :

``` text
Remote
100% remote
Work from home
À distance
```

→ catégorie interne commune.

Et :

``` text
CDI
Permanent
Full-time permanent
```

→ catégorie interne commune lorsque le contexte le permet.

La normalisation doit rester prudente : elle ne doit pas créer une
information qui n'existe pas dans la source.

------------------------------------------------------------------------

## 12. Déduplication

La déduplication doit être conçue à deux niveaux :

``` text
Source-level deduplication
          ↓
Cross-source deduplication
```

Signaux possibles :

-   identifiant officiel de l'offre ;
-   URL canonique ;
-   entreprise + titre + localisation ;
-   similarité de contenu ;
-   date ;
-   autres caractéristiques pertinentes.

La stratégie exacte sera définie lors de l'implémentation.

------------------------------------------------------------------------

## 13. Gestion des erreurs

Chaque connecteur doit prévoir au minimum :

``` text
Network error
Timeout
Authentication error
Permission error
Rate limit
Invalid response
Schema change
Missing data
Endpoint unavailable
Temporary source unavailable
```

Le comportement doit être documenté par connecteur.

------------------------------------------------------------------------

## 14. Fréquence de collecte

La fréquence ne doit pas être déterminée uniquement pour maximiser le
nombre d'offres.

Elle dépend notamment :

-   de la fraîcheur souhaitée ;
-   du volume ;
-   des rate limits ;
-   du coût ;
-   des conditions d'utilisation ;
-   de la fréquence de publication de la source.

Exemples de fréquences possibles :

``` text
15 minutes
1 heure
6 heures
1 jour
À la demande
```

La fréquence réelle doit être définie après validation des contraintes
de chaque source.

------------------------------------------------------------------------

## 15. Stockage

Le pipeline doit distinguer conceptuellement :

``` text
Raw data
    ↓
Parsed data
    ↓
Normalized JobOffer
```

Le stockage de données brutes ne doit pas être activé automatiquement
lorsqu'une politique de stockage ou de rétention reste à vérifier.

Les règles de conservation doivent respecter les conditions applicables
à la source.

------------------------------------------------------------------------

## 16. Candidature

Les connecteurs de recherche d'offres ne doivent pas être conçus comme
des connecteurs de candidature par défaut.

Trois niveaux sont distincts :

### Niveau 1 --- Redirection

``` text
application_url
      ↓
Utilisateur
      ↓
Plateforme source
```

### Niveau 2 --- Préparation

``` text
Agent
  ↓
CV / lettre / réponses
  ↓
Validation humaine
```

### Niveau 3 --- Soumission

``` text
Agent
  ↓
Plateforme
  ↓
Candidature
```

Le niveau 3 nécessite une analyse spécifique des permissions et
conditions de la plateforme.

La présence d'un `application_url` ne signifie pas qu'une API de
candidature existe.

------------------------------------------------------------------------

## 17. Plan d'implémentation recommandé

### Phase 0 --- Préparation

-   créer l'infrastructure commune ;
-   définir l'interface `Connector` ;
-   définir `JobOffer` ;
-   définir les interfaces `Fetcher`, `Paginator`, `AuthStrategy`,
    `RetryPolicy` ;
-   définir logging et gestion des erreurs ;
-   définir les tests communs.

### Phase 1 --- Premier connecteur

Commencer par une source dont la spécification est suffisamment avancée
:

``` text
RemoteOK
```

Objectif :

``` text
HTTP
 ↓
JSON
 ↓
Parsing
 ↓
Normalization
 ↓
Deduplication
 ↓
JobOffer
```

### Phase 2 --- Réutilisation

Réutiliser le socle HTTP/JSON pour :

``` text
Greenhouse
Lever
```

Ne pas copier le code de transport.

Créer uniquement les composants spécifiques nécessaires.

### Phase 3 --- Sources nécessitant un accès

Après obtention/clarification des accès :

``` text
Himalayas
We Work Remotely
Ashby
Recruitee
ReliefWeb
```

### Phase 4 --- Tests

Pour chaque connecteur :

``` text
Connectivity test
      ↓
Authentication test
      ↓
Retrieval test
      ↓
Pagination test
      ↓
Parsing test
      ↓
Normalization test
      ↓
Error handling test
      ↓
Rate-limit behavior test
      ↓
Deduplication test
      ↓
JobOffer validation
```

### Phase 5 --- Passage en production

Un connecteur ne passe à :

``` text
🟢 Opérationnel
```

qu'après satisfaction des critères définis dans `connectors.md`.

------------------------------------------------------------------------

## 18. Organisation de code proposée

Structure conceptuelle :

``` text
connectors/
│
├── core/
│   ├── connector
│   ├── fetchers/
│   │   ├── http-json
│   │   └── rss
│   ├── auth/
│   ├── pagination/
│   ├── retry/
│   ├── rate-limit/
│   └── errors/
│
├── sources/
│   ├── remoteok/
│   │   ├── connector
│   │   ├── parser
│   │   └── mapper
│   │
│   ├── himalayas/
│   ├── wwr/
│   ├── greenhouse/
│   ├── lever/
│   ├── ashby/
│   ├── recruitee/
│   └── reliefweb/
│
├── normalization/
│
├── deduplication/
│
└── models/
    └── JobOffer
```

Cette structure est indicative. Le langage, le framework et les
conventions de projet peuvent modifier l'organisation finale.

------------------------------------------------------------------------

## 19. Règle de mutualisation

Avant de créer une fonction spécifique à une source, vérifier :

``` text
Cette logique est-elle commune à plusieurs sources ?
```

Si oui :

``` text
→ infrastructure commune
```

Si non :

``` text
→ logique spécifique du connecteur
```

Exemple :

``` text
HTTP GET
timeout
retry
logging
rate limiting
```

→ commun.

Mais :

``` text
interprétation d'un champ propre à RemoteOK
```

→ `RemoteOKParser`.

L'objectif n'est pas de rendre les sources artificiellement identiques.

L'objectif est :

> **mutualiser l'infrastructure et isoler les différences
> métier/techniques propres à chaque source.**

------------------------------------------------------------------------

## 20. Critères de qualité du code

L'implémentation doit privilégier :

-   séparation des responsabilités ;
-   code réutilisable ;
-   configuration externalisée ;
-   absence de secrets dans le code ;
-   validation des réponses ;
-   logs exploitables ;
-   erreurs explicites ;
-   retries contrôlés ;
-   tests automatisés ;
-   documentation des comportements spécifiques ;
-   possibilité de remplacer un connecteur sans modifier le reste du
    système.

------------------------------------------------------------------------

## 21. Critères de validation finale

Un connecteur peut être déclaré `🟢 Opérationnel` uniquement lorsque les
éléments suivants sont vérifiés :

1.  accès fonctionnel ;
2.  authentification fonctionnelle si nécessaire ;
3.  récupération réelle ;
4.  complétude suffisante ;
5.  parsing fonctionnel ;
6.  normalisation fonctionnelle ;
7.  principales erreurs gérées ;
8.  retries définis ;
9.  limites respectées ;
10. conditions d'utilisation compatibles ;
11. alimentation correcte de `JobOffer` ;
12. tests de base effectués.

------------------------------------------------------------------------

## 22. Référentiels obligatoires

Avant toute implémentation, l'outil ou le développeur doit consulter :

``` text
sources-master.md
research-protocol.md
connectors.md
connector-implementation-plan.md
```

Ordre logique :

``` text
sources-master.md
        ↓
Identifier la source et son statut stratégique
        ↓
research-protocol.md
        ↓
Vérifier les règles de recherche / autorisation
        ↓
connectors.md
        ↓
Vérifier les caractéristiques techniques documentées
        ↓
connector-implementation-plan.md
        ↓
Implémenter selon l'architecture commune
```

Si ces documents contiennent une information contradictoire ou
insuffisante :

``` text
NE PAS DEVINER
        ↓
Marquer À VÉRIFIER
        ↓
Rechercher la documentation officielle
        ↓
Mettre à jour le référentiel approprié
        ↓
Reprendre l'implémentation
```

------------------------------------------------------------------------

## 23. Résumé opérationnel

``` text
                    8 SOURCES
                        │
          ┌─────────────┴─────────────┐
          │                           │
       JSON/API                    RSS/XML
          │                           │
     7 sources                     WWR
          │                           │
   HttpJsonFetcher                RssFetcher
          │                           │
          └─────────────┬─────────────┘
                        ↓
                Source-specific Parser
                        ↓
                  Normalization
                        ↓
                  Deduplication
                        ↓
                     JobOffer
                        ↓
                    Job Agent
```

### État actuel

``` text
🔵 Spécification en cours
RemoteOK
Greenhouse
Lever

🟣 En attente d'accès
Himalayas
We Work Remotely
Ashby
Recruitee
ReliefWeb

🟢 Opérationnel
Aucun
```

Ce document constitue un **plan d'implémentation**, et non une
autorisation d'accès aux sources. Les informations techniques non encore
vérifiées doivent rester explicitement marquées comme telles.
