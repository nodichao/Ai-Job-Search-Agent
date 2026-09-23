# Connector Implementation Guide --- Job Agent

> **Nature du document :** référentiel générique d'implémentation\
> **Périmètre :** architecture, conventions et méthodes communes pour
> construire les connecteurs de Job Agent\
> **Relation avec les autres documents :** ce guide ne liste pas les
> sources retenues et ne remplace pas `sources-master.md`,
> `research-protocol.md` ou `connectors.md`.

------------------------------------------------------------------------

## 1. Objectif

Ce document définit le **socle générique** à utiliser pour implémenter
les connecteurs de Job Agent.

Il doit permettre à un développeur ou à un outil d'implémentation de
comprendre :

-   comment un connecteur doit être structuré ;
-   quelles responsabilités doivent être mutualisées ;
-   quelles responsabilités doivent rester spécifiques à chaque source ;
-   comment récupérer les données ;
-   comment les parser ;
-   comment les normaliser ;
-   comment les dédupliquer ;
-   comment gérer les erreurs, retries, limites et authentification ;
-   comment tester un connecteur ;
-   à quelles conditions un connecteur peut être considéré comme
    opérationnel.

Le guide est volontairement indépendant d'une source particulière.

------------------------------------------------------------------------

## 2. Position dans la documentation du projet

Les documents ont des responsabilités différentes :

``` text
sources-master.md
    ↓
Référentiel stratégique des sources

research-protocol.md
    ↓
Méthode de recherche, vérification et qualification

connectors.md
    ↓
Référentiel des connecteurs et de leur état

connector-implementation-guide.md
    ↓
Référentiel générique d'implémentation

connector-implementation-plan.md
    ↓
Plan concret d'implémentation d'un lot de sources
```

Le présent document décrit donc le **comment construire un connecteur**,
indépendamment de la source.

------------------------------------------------------------------------

# 3. Principe fondamental

Un connecteur est une **couche d'adaptation** entre une source externe
et le modèle interne de Job Agent.

Architecture :

``` text
Source externe
      ↓
Accès / Fetch
      ↓
Données brutes
      ↓
Parsing
      ↓
Transformation
      ↓
Normalisation
      ↓
Déduplication
      ↓
JobOffer
```

Le reste du système ne doit pas avoir besoin de connaître les
particularités internes de chaque source.

------------------------------------------------------------------------

# 4. Ne pas confondre les niveaux

Un connecteur doit distinguer :

``` text
Transport
    ↓
Récupération
    ↓
Parsing
    ↓
Transformation
    ↓
Normalisation
    ↓
Déduplication
```

Ces responsabilités ne doivent pas être mélangées inutilement.

Exemple :

``` text
HttpJsonFetcher
```

ne doit pas connaître les règles métier propres à une source.

À l'inverse :

``` text
SourceParser
```

ne doit pas réimplémenter la gestion générique des timeouts et retries.

------------------------------------------------------------------------

# 5. Les grandes familles de transport

Le premier niveau d'abstraction porte sur le transport.

À ce stade, deux grandes familles sont utilisées comme modèles de
référence :

``` text
HTTP → JSON
HTTP → RSS/XML
```

## 5.1 HTTP → JSON

Créer un composant générique :

``` text
HttpJsonFetcher
```

Responsabilités :

-   effectuer les requêtes HTTP ;
-   gérer les headers ;
-   gérer le timeout ;
-   récupérer la réponse ;
-   vérifier le statut HTTP ;
-   exposer la réponse JSON au niveau supérieur ;
-   appliquer la politique de retry ;
-   appliquer les règles de rate limiting lorsque définies.

Le fetcher ne doit pas interpréter les champs métier de l'offre.

------------------------------------------------------------------------

## 5.2 HTTP → RSS/XML

Créer un composant générique :

``` text
RssFetcher
```

Responsabilités :

-   effectuer la requête HTTP ;
-   gérer le timeout ;
-   récupérer le flux ;
-   vérifier le statut HTTP ;
-   fournir le document XML/RSS au parser ;
-   appliquer les politiques communes de réseau.

Le parsing RSS reste séparé du transport.

------------------------------------------------------------------------

# 6. Architecture modulaire

Architecture cible :

``` text
                     Connector
                         │
          ┌──────────────┼──────────────┐
          │              │              │
        Fetch          Parse        Normalize
          │              │              │
      Fetcher         Parser       Normalizer
          │              │              │
          └──────────────┴──────────────┘
                         │
                    Deduplicator
                         │
                      JobOffer
```

Le connecteur orchestre les composants.

------------------------------------------------------------------------

# 7. Interface conceptuelle du connecteur

Chaque connecteur doit présenter une interface cohérente.

Conceptuellement :

``` text
Connector
├── fetch()
├── parse()
├── normalize()
└── deduplicate()
```

Une implémentation concrète peut utiliser une organisation interne
différente, mais son comportement doit rester compatible avec le
pipeline commun.

------------------------------------------------------------------------

# 8. Fetcher

Le fetcher est responsable uniquement de l'accès technique aux données.

Exemples :

``` text
HttpJsonFetcher
RssFetcher
```

Il doit gérer les aspects génériques :

``` text
Request
  ↓
HTTP
  ↓
Response
  ↓
Validation transport
  ↓
Raw payload
```

Il ne doit pas :

-   décider si une offre est pertinente ;
-   interpréter une compétence ;
-   transformer une offre en `JobOffer` ;
-   décider si une source est stratégiquement retenue.

------------------------------------------------------------------------

# 9. Authentification

Prévoir une abstraction générique :

``` text
AuthStrategy
├── NoAuth
├── ApiKey
├── BearerToken
└── PartnerCredentials
```

La stratégie réellement utilisée doit être déterminée par la
documentation vérifiée de la source.

### Règles

Ne jamais :

-   mettre une clé API dans Git ;
-   mettre un token dans un fichier de configuration versionné ;
-   mettre un mot de passe dans le code ;
-   copier des cookies de session dans le dépôt.

Utiliser des mécanismes de gestion de secrets adaptés à l'environnement
d'exécution.

------------------------------------------------------------------------

# 10. Accès ≠ autorisation

Une architecture technique ne doit jamais transformer automatiquement :

``` text
Endpoint public
```

en :

``` text
Autorisation d'utilisation
```

Il faut distinguer :

``` text
Accessibilité technique
        ≠
Autorisation contractuelle
```

Les questions d'autorisation, de conditions d'utilisation, de stockage,
de redistribution et de candidature doivent être traitées conformément
au référentiel de recherche et au référentiel des connecteurs.

------------------------------------------------------------------------

# 11. Pagination

Prévoir une abstraction :

``` text
Paginator
├── NoPagination
├── CursorPaginator
└── PagePaginator
```

Le connecteur choisit la stratégie correspondant à la source.

### Règle

Ne jamais supposer qu'une API possède une pagination parce qu'une autre
en possède une.

La stratégie doit être déterminée à partir de la documentation ou d'une
observation vérifiée.

### Exemple conceptuel

``` text
CursorPaginator

request(cursor)
      ↓
response
      ↓
items
      ↓
next_cursor
      ↓
request(next_cursor)
```

------------------------------------------------------------------------

# 12. Rate limiting

Prévoir un composant générique :

``` text
RateLimiter
```

Il doit permettre de respecter les limites connues d'une source.

Architecture :

``` text
Connector
   ↓
RateLimiter
   ↓
Fetcher
   ↓
Source
```

Le rate limiter ne doit jamais être utilisé pour contourner une limite.

Si la source répond par un mécanisme de limitation :

``` text
429 / rate limit
       ↓
respecter la politique de la source
       ↓
retry selon les règles autorisées
```

------------------------------------------------------------------------

# 13. Retry

Prévoir :

``` text
RetryPolicy
```

Le retry doit être utilisé pour les erreurs réellement temporaires.

Exemples conceptuels :

``` text
Timeout temporaire
→ retry possible

Erreur réseau temporaire
→ retry possible

Service temporairement indisponible
→ retry possible
```

En revanche :

``` text
401 / 403
→ vérifier authentification / autorisation

CAPTCHA
→ ne pas contourner

Anti-bot
→ ne pas contourner

Restriction contractuelle
→ ne pas contourner
```

Le retry doit donc être **contrôlé et explicable**.

------------------------------------------------------------------------

# 14. Parsing

Le parser transforme le payload externe en représentation interne
intermédiaire.

Exemples :

``` text
RemoteSourceParser
GreenhouseParser
GenericRssParser
```

Responsabilité :

``` text
Raw payload
    ↓
Parsed offer
```

Le parser doit gérer :

-   champs absents ;
-   champs optionnels ;
-   structures imbriquées ;
-   formats de date ;
-   HTML lorsqu'il est présent ;
-   variations raisonnables du payload ;
-   erreurs de schéma.

Il ne doit pas inventer des valeurs absentes.

------------------------------------------------------------------------

# 15. Transformation

La transformation convertit les structures propres à la source vers une
structure intermédiaire commune.

Exemple conceptuel :

``` text
source.position
        ↓
title

source.company_name
        ↓
company
```

Les mappings doivent être documentés lorsqu'ils ne sont pas évidents.

------------------------------------------------------------------------

# 16. Normalisation

Le normalizer transforme les différentes représentations en valeurs
communes.

Exemple conceptuel :

``` text
"Full-time"
"Full time"
"FULL_TIME"
```

peuvent être normalisés vers une représentation interne commune lorsque
l'équivalence est suffisamment certaine.

Même principe pour :

-   type de contrat ;
-   type d'emploi ;
-   localisation ;
-   niveau d'expérience ;
-   compétences ;
-   télétravail.

### Règle importante

La normalisation ne doit pas fabriquer une information.

``` text
Information absente
        ↓
null / unknown / non renseigné
```

et non une valeur supposée.

------------------------------------------------------------------------

# 17. Déduplication

Prévoir une couche dédiée :

``` text
Deduplicator
```

Deux niveaux sont possibles :

``` text
Source-level deduplication
        ↓
Cross-source deduplication
```

Signaux potentiels :

-   identifiant officiel ;
-   URL canonique ;
-   combinaison entreprise + titre + localisation ;
-   similarité de contenu ;
-   date ;
-   autres signaux vérifiables.

La déduplication doit être conçue comme une responsabilité indépendante
du parser.

------------------------------------------------------------------------

# 18. Modèle `JobOffer`

Tous les connecteurs doivent converger vers un modèle commun.

Structure conceptuelle :

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

Ce modèle est conceptuel et peut évoluer avec le projet.

### Règle

Une source ne doit pas être forcée à fournir tous les champs.

``` text
Champ disponible
→ mapper

Champ absent
→ null / unknown

Champ ambigu
→ ne pas inventer
```

------------------------------------------------------------------------

# 19. Provenance

Chaque offre doit conserver suffisamment d'informations pour savoir :

``` text
D'où vient cette offre ?
Quand a-t-elle été récupérée ?
Quel identifiant possède-t-elle chez la source ?
Quelle URL permet de revenir à la source ?
```

La provenance est essentielle pour :

-   vérification ;
-   déduplication ;
-   mise à jour ;
-   traçabilité ;
-   affichage ;
-   redirection vers la candidature.

------------------------------------------------------------------------

# 20. Gestion des erreurs

Les erreurs doivent être distinguées.

Catégories minimales :

``` text
NetworkError
TimeoutError
AuthenticationError
AuthorizationError
RateLimitError
ParseError
SchemaError
ValidationError
SourceUnavailableError
```

Chaque erreur doit permettre de déterminer :

``` text
Que s'est-il passé ?
Est-ce temporaire ?
Peut-on réessayer ?
Faut-il intervenir ?
```

------------------------------------------------------------------------

# 21. Observabilité

Chaque connecteur devrait produire des informations permettant de suivre
:

``` text
Nombre de requêtes
Nombre de réponses valides
Nombre d'erreurs
Temps de réponse
Nombre d'offres récupérées
Nombre d'offres parsées
Nombre d'offres rejetées
Nombre d'offres normalisées
Nombre de doublons
Dernière collecte
```

Les logs ne doivent pas exposer :

-   API keys ;
-   tokens ;
-   mots de passe ;
-   cookies ;
-   données sensibles inutiles.

------------------------------------------------------------------------

# 22. Tests

Chaque connecteur doit avoir plusieurs niveaux de tests.

## 22.1 Tests du fetcher

``` text
GET réussi
GET échoué
timeout
réponse invalide
rate limit
retry
```

## 22.2 Tests du parser

Utiliser des payloads représentatifs :

``` text
payload normal
payload incomplet
payload avec champs optionnels absents
payload avec structure inattendue
```

## 22.3 Tests du normalizer

Vérifier :

``` text
Mapping correct
Valeurs inconnues
Dates
Localisation
Contrat
Télétravail
```

## 22.4 Tests de déduplication

Tester :

``` text
Même ID
Même URL
Même offre provenant de plusieurs sources
Offres différentes mais titres proches
```

## 22.5 Test end-to-end

``` text
Source
 ↓
Fetch
 ↓
Parse
 ↓
Normalize
 ↓
Deduplicate
 ↓
JobOffer
```

------------------------------------------------------------------------

# 23. Configuration

Les paramètres variables doivent être externalisés.

Exemples :

``` text
SOURCE_BASE_URL
API_KEY
API_TOKEN
REQUEST_TIMEOUT
MAX_RETRIES
RATE_LIMIT
COLLECTION_FREQUENCY
```

Les secrets ne doivent jamais être committés.

------------------------------------------------------------------------

# 24. Sécurité

Le système doit respecter au minimum :

-   secrets hors dépôt ;
-   validation des réponses externes ;
-   timeout réseau ;
-   limites de taille lorsque pertinentes ;
-   logs sans secrets ;
-   séparation des données et instructions ;
-   aucun contournement des protections ;
-   contrôle des URLs externes lorsque nécessaire.

Les contenus d'offres sont des **données non fiables**.

------------------------------------------------------------------------

# 25. Stockage

Le pipeline doit distinguer :

``` text
Raw data
    ↓
Parsed representation
    ↓
Normalized JobOffer
```

La conservation des données brutes ou leur redistribution doit être
décidée en fonction des contraintes applicables à la source.

L'architecture ne doit pas présumer qu'une donnée récupérable peut être
conservée indéfiniment.

------------------------------------------------------------------------

# 26. Candidature

Le connecteur de collecte ne doit pas supposer qu'il peut soumettre une
candidature.

Trois niveaux sont à distinguer :

``` text
Niveau 1
Redirection vers application_url

Niveau 2
Préparation de candidature

Niveau 3
Soumission de candidature
```

Le niveau 3 nécessite une analyse distincte des permissions et capacités
de la plateforme.

``` text
application_url
≠
API de candidature
```

------------------------------------------------------------------------

# 27. Pattern générique recommandé

Le pattern cible est :

``` text
                   SourceConnector
                         │
          ┌──────────────┼──────────────┐
          ↓              ↓              ↓
       Fetcher        Parser        Config
          │              │
          ↓              ↓
       Raw Data     Parsed Offer
          │              │
          └───────┬──────┘
                  ↓
             Transformer
                  ↓
              Normalizer
                  ↓
             Deduplicator
                  ↓
               JobOffer
```

Les composants transverses :

``` text
AuthStrategy
RetryPolicy
RateLimiter
Paginator
Logger
ErrorHandler
```

doivent être réutilisables.

------------------------------------------------------------------------

# 28. Règle de mutualisation

Avant de créer une logique spécifique à un connecteur :

``` text
Cette logique est-elle commune à plusieurs sources ?
```

Si oui :

``` text
→ couche commune
```

Si elle est propre à la source :

``` text
→ connecteur / parser spécifique
```

Exemples de logique commune :

``` text
HTTP GET
timeout
retry
rate limiting
logging
pagination abstraite
auth abstraite
```

Exemples de logique spécifique :

``` text
mapping d'un champ propre à la source
interprétation d'une structure JSON spécifique
construction d'une requête propre à la source
```

------------------------------------------------------------------------

# 29. Definition of Done

Un connecteur ne doit pas être considéré comme opérationnel simplement
parce qu'un endpoint répond.

La validation doit couvrir :

``` text
☐ Accès fonctionnel
☐ Authentification fonctionnelle si nécessaire
☐ Récupération réelle
☐ Données suffisamment complètes
☐ Parsing
☐ Transformation
☐ Normalisation
☐ Déduplication
☐ Gestion des erreurs
☐ Retry
☐ Respect des limites
☐ Compatibilité avec les conditions applicables
☐ Alimentation correcte de JobOffer
☐ Tests réalisés
```

Le statut `🟢 Opérationnel` doit suivre les critères du référentiel
`connectors.md`.

------------------------------------------------------------------------

# 30. Règles pour un outil d'IA d'implémentation

Un outil d'IA chargé de coder un connecteur doit suivre les règles
suivantes.

### Avant de coder

1.  Lire les documents de référence.
2.  Identifier les informations confirmées.
3.  Identifier les informations `À vérifier`.
4.  Ne pas transformer une hypothèse en implémentation définitive.
5.  Vérifier la documentation officielle lorsque nécessaire.

### Pendant le développement

1.  Réutiliser les composants communs.
2.  Ne pas dupliquer le transport.
3.  Ne pas inventer d'endpoint.
4.  Ne pas inventer d'authentification.
5.  Ne pas contourner les protections.
6.  Conserver la provenance.
7.  Ajouter les tests.
8.  Documenter les comportements spécifiques.

### Après le développement

1.  Exécuter les tests.
2.  Tester une récupération réelle lorsque l'accès le permet.
3.  Vérifier le parsing.
4.  Vérifier la normalisation.
5.  Vérifier la déduplication.
6.  Vérifier les erreurs et retries.
7.  Vérifier les limites.
8.  Ne déclarer `🟢 Opérationnel` qu'après satisfaction de la Definition
    of Done.

------------------------------------------------------------------------

# 31. Ajout futur d'une nouvelle source

Lorsqu'une nouvelle source est ajoutée :

``` text
Nouvelle source
      ↓
Recherche / qualification
      ↓
Identification du mode d'accès
      ↓
Choix du Fetcher
      ↓
Choix AuthStrategy
      ↓
Choix Paginator
      ↓
Parser spécifique
      ↓
Normalisation
      ↓
Déduplication
      ↓
Tests
      ↓
Validation
```

Le guide générique ne doit normalement pas être modifié pour chaque
nouvelle source.

Les informations spécifiques doivent aller dans :

``` text
connectors.md
```

et dans le plan de lot correspondant.

------------------------------------------------------------------------

# 32. Résumé

L'objectif du guide n'est pas de rendre tous les connecteurs identiques.

L'objectif est de rendre **leur architecture cohérente**.

``` text
Même infrastructure
        +
Composants réutilisables
        +
Interfaces communes
        +
Parsers spécifiques
        +
Mappings spécifiques
        =
Connecteurs maintenables
```

Le principe directeur est :

> **Mutualiser ce qui est réellement commun ; isoler ce qui est
> réellement spécifique ; ne jamais inventer ce qui n'est pas vérifié.**
