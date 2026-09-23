# Job Agent — Research Protocol

## 1. Objectif du document

Ce document définit la méthode de travail à appliquer lorsqu'une IA participe à la recherche, à l'évaluation, à la sélection ou à l'intégration de sources d'offres d'emploi pour le projet Job Agent.

Il constitue le **protocole opérationnel commun** entre :

* `sources-master.md`
* `connectors.md`
* les différentes IA utilisées pour le projet ;
* les personnes participant au projet.

L'objectif est d'éviter que chaque outil IA utilise sa propre méthode de recherche, ses propres critères ou ses propres interprétations.

---

# 2. Documents de référence

Le projet repose sur trois documents complémentaires :

```text
sources-master.md
        │
        │ Référentiel stratégique
        ↓
connectors.md
        │
        │ Référentiel technique
        ↓
research-protocol.md
        │
        │ Méthode de travail
        ↓
IA / équipe
```

### `sources-master.md`

Répond à :

> Avec quelles sources voulons-nous potentiellement travailler ?

### `connectors.md`

Répond à :

> Comment allons-nous techniquement intégrer ces sources ?

### `research-protocol.md`

Répond à :

> Comment devons-nous rechercher, vérifier, décider et documenter ?

---

# 3. Rôle de l'IA

L'IA intervient comme **assistant de recherche et d'analyse**.

Elle peut :

* rechercher des sources ;
* rechercher des API ;
* analyser la documentation ;
* identifier les méthodes d'accès ;
* vérifier les conditions d'utilisation ;
* comparer plusieurs méthodes ;
* identifier les informations manquantes ;
* proposer un statut ;
* préparer une entrée de tableau ;
* analyser un connecteur ;
* identifier les risques techniques ou contractuels.

Elle ne doit pas :

* inventer une API ;
* inventer une permission ;
* considérer une information non vérifiée comme certaine ;
* contourner une protection technique ;
* présenter une hypothèse comme un fait ;
* modifier arbitrairement les règles du projet ;
* considérer qu'une source est exploitable uniquement parce que ses pages sont accessibles.

---

# 4. Principe de séparation des responsabilités

Toujours distinguer :

```text
SOURCE
   ↓
PROVENANCE
   ↓
DONNÉES
   ↓
MÉTHODE D'ACCÈS
   ↓
AUTORISATION
   ↓
CONNECTEUR
   ↓
CAPACITÉS
   ↓
VALEUR POUR LE PROJET
```

Une IA ne doit jamais fusionner ces dimensions.

Exemple :

> « Le site contient beaucoup d'offres »

ne signifie pas :

> « Une API est disponible »

et :

> « Une API est disponible »

ne signifie pas :

> « Notre utilisation est autorisée »

et :

> « Notre utilisation est autorisée »

ne signifie pas :

> « Le connecteur est opérationnel ».

---

# 5. Hiérarchie des sources de vérification

Lorsqu'une information doit être vérifiée, privilégier :

### Niveau 1 — Source primaire

* documentation officielle ;
* documentation développeur ;
* documentation API ;
* conditions d'utilisation ;
* politique officielle ;
* page officielle de la plateforme.

### Niveau 2 — Source secondaire fiable

* documentation technique reconnue ;
* article spécialisé ;
* publication institutionnelle ;
* analyse juridique ou technique crédible.

### Niveau 3 — Sources communautaires

* forums ;
* Reddit ;
* GitHub issues ;
* Stack Overflow ;
* discussions techniques.

Les sources communautaires peuvent servir à découvrir une piste mais ne doivent pas être considérées comme preuve définitive pour les permissions ou conditions d'utilisation.

---

# 6. Règle fondamentale de vérification

Pour toute information importante, distinguer :

### Confirmé

L'information est directement vérifiée auprès d'une source fiable.

### Probable

Plusieurs indices convergent mais la source primaire n'a pas encore confirmé l'information.

### À vérifier

L'information est inconnue ou contradictoire.

### Incompatible

Une source officielle indique clairement que l'utilisation envisagée n'est pas permise.

Ne jamais transformer :

`À vérifier`

en :

`Confirmé`

sans nouvelle vérification.

---

# 7. Recherche d'une nouvelle source

Lorsqu'une nouvelle plateforme est découverte, suivre les étapes suivantes.

## Étape 1 — Identifier la source

Déterminer :

* nom ;
* URL officielle ;
* pays / zone ;
* catégorie ;
* provenance des offres ;
* public cible.

---

## Étape 2 — Identifier la couverture

Déterminer :

* Dakar ;
* Sénégal ;
* Afrique de l'Ouest ;
* Afrique ;
* international ;
* remote.

Identifier également les pays réellement couverts.

Ne pas déduire la couverture géographique à partir du nom de la plateforme.

---

## Étape 3 — Identifier les types d'offres

Rechercher notamment :

* CDI ;
* CDD ;
* stage ;
* alternance ;
* freelance ;
* mission ;
* temps partiel ;
* remote ;
* international ;
* autres types pertinents.

---

# 8. Recherche des méthodes d'accès

Toujours rechercher les méthodes dans cet ordre :

```text
API officielle
      ↓
RSS / Atom
      ↓
Webhook
      ↓
Export officiel
      ↓
Flux partenaire
      ↓
Page publique
      ↓
Scraping / crawling
      ↓
Browser automation
```

Cet ordre n'est pas une obligation absolue.

Il représente une **préférence générale pour les méthodes officiellement prévues par la source**.

Une méthode plus basse dans cette liste ne doit être envisagée que si elle est techniquement et contractuellement compatible avec le projet.

---

# 9. Pour les API

Lorsqu'une API est identifiée, vérifier :

* existence réelle ;
* documentation officielle ;
* endpoints disponibles ;
* méthode d'authentification ;
* nécessité d'une clé ;
* nécessité d'un compte ;
* nécessité d'une approbation ;
* limites ;
* pagination ;
* champs disponibles ;
* filtres ;
* fréquence autorisée ;
* coût ;
* conditions commerciales ;
* stockage ;
* redistribution ;
* utilisation commerciale ;
* candidature ;
* restrictions éventuelles.

Ne jamais écrire simplement :

> API disponible

sans déterminer au minimum :

> quelle API, pour quelles données et sous quelles conditions.

---

# 10. Pour le scraping

Le scraping ne doit jamais être considéré comme :

> « Le site est public donc nous pouvons le scraper. »

Lorsqu'un scraping est envisagé, vérifier séparément :

1. accessibilité technique ;
2. robots.txt lorsqu'il est pertinent ;
3. conditions d'utilisation ;
4. restrictions anti-bot ;
5. fréquence des requêtes ;
6. données personnelles ;
7. stockage ;
8. redistribution ;
9. utilisation commerciale ;
10. mécanismes de protection.

Si le scraping nécessite de contourner une protection :

**ne pas poursuivre cette méthode.**

---

# 11. Pour les plateformes nécessitant un compte

Distinguer :

### Compte utilisateur

Le compte appartient à l'utilisateur final.

### Compte développeur

Le compte permet à l'application d'utiliser une API.

### Compte partenaire

L'accès est fourni après accord commercial ou institutionnel.

### Compte employeur

Permet à une entreprise de publier ou gérer ses offres.

La présence d'un compte ne signifie pas automatiquement que l'application peut accéder aux données.

---

# 12. Autorisation

Toujours distinguer :

### Autorisation de l'utilisateur

L'utilisateur autorise notre application à accéder à certaines de ses données.

Exemple :

OAuth permettant à l'application d'accéder au compte de l'utilisateur.

### Autorisation de la plateforme

La plateforme autorise notre application à utiliser son API ou ses données.

### Autorisation contractuelle

Un contrat ou partenariat donne des droits spécifiques.

Ces trois niveaux ne doivent jamais être confondus.

---

# 13. Évaluation de la source

Après la recherche, évaluer la source selon :

### Pertinence

La source contient-elle des offres réellement intéressantes pour nos utilisateurs ?

### Couverture

La source apporte-t-elle une couverture géographique ou sectorielle utile ?

### Volume

Le nombre d'offres est-il suffisamment important ?

### Diversité

La source complète-t-elle les autres sources ?

### Fraîcheur

Les offres sont-elles suffisamment récentes ?

### Qualité

Les données sont-elles suffisamment complètes et fiables ?

### Accessibilité

Pouvons-nous techniquement récupérer les données ?

### Autorisation

Notre utilisation envisagée est-elle compatible avec les règles de la source ?

### Coût

L'intégration et l'utilisation sont-elles économiquement raisonnables ?

### Maintenance

La solution risque-t-elle d'être fragile ou coûteuse à maintenir ?

---

# 14. Attribution du statut du tableau maître

Après l'analyse, attribuer **un seul** statut.

### 🟢 Connecteur à étudier

Utiliser lorsque :

* la source est pertinente ;
* une méthode d'accès viable est identifiée ;
* aucune restriction bloquante n'a été identifiée ;
* une étude technique est justifiée.

### 🟣 Partenariat nécessaire

Utiliser lorsque :

* la source est intéressante ;
* mais l'intégration nécessite une autorisation, une approbation ou un partenariat.

### 🔵 À étudier plus tard

Utiliser lorsque :

* la source est pertinente ;
* mais son intégration n'est pas prioritaire pour le MVP.

### 🟡 À surveiller

Utiliser lorsque :

* la source semble intéressante ;
* mais les informations sont insuffisantes, incertaines ou susceptibles d'évoluer.

### 🔴 À exclure

Utiliser lorsque :

* la source est incompatible avec le projet ;
* l'utilisation envisagée est interdite ;
* elle nécessite un contournement ;
* elle n'apporte pas de valeur suffisante ;
* ou une contrainte fondamentale empêche son utilisation.

---

# 15. Ne pas confondre intérêt et faisabilité

Une source peut être :

> très intéressante mais difficile à intégrer.

Elle peut alors être :

**🟣 Partenariat nécessaire**

ou

**🔵 À étudier plus tard**

et non automatiquement :

**🟢 Connecteur à étudier**.

L'intérêt produit et la faisabilité technique doivent rester deux dimensions distinctes.

---

# 16. Passage vers le tableau des connecteurs

Une source peut passer vers l'étude du connecteur lorsqu'elle est :

**🟢 Connecteur à étudier**

ou lorsque les conditions nécessaires d'une source :

**🟣 Partenariat nécessaire**

ont été obtenues.

À ce moment :

1. identifier la méthode retenue ;
2. identifier les endpoints ou flux ;
3. définir l'authentification ;
4. définir les champs ;
5. définir le parsing ;
6. définir la normalisation ;
7. définir la déduplication ;
8. définir les erreurs ;
9. définir les retries ;
10. définir la fréquence de collecte ;
11. définir les conditions de stockage ;
12. définir les possibilités de candidature.

---

# 17. Analyse d'un connecteur

Lorsqu'un connecteur est étudié, suivre ce processus :

```text
Documentation
      ↓
Accès
      ↓
Authentification
      ↓
Test de récupération
      ↓
Analyse des données
      ↓
Parsing
      ↓
Normalisation
      ↓
Déduplication
      ↓
Gestion des erreurs
      ↓
Tests
      ↓
Validation
```

---

# 18. Attribution du statut du connecteur

### ⚪ À étudier

Aucune analyse technique suffisante.

### 🔵 Spécification en cours

La solution technique est en cours de conception.

### 🟣 En attente d'accès

Une autorisation, une clé ou un accès est nécessaire.

### 🟠 En développement

Le connecteur est en cours d'implémentation.

### 🟢 Opérationnel

Le connecteur est suffisamment testé et peut alimenter l'agent.

### 🟡 À corriger / instable

Le connecteur fonctionne mais présente des problèmes.

### 🟤 Maintenance requise

Une intervention est nécessaire.

### 🔴 Bloqué

Le connecteur ne peut actuellement pas fonctionner.

### ⚫ Abandonné

Le connecteur n'est plus utilisé ou maintenu.

---

# 19. Conditions minimales pour 🟢 Opérationnel

Un connecteur ne peut être déclaré opérationnel que si :

* l'accès fonctionne ;
* l'authentification fonctionne si nécessaire ;
* les données sont récupérées ;
* les données nécessaires sont disponibles ;
* le parsing fonctionne ;
* la normalisation fonctionne ;
* les erreurs principales sont gérées ;
* les limites sont respectées ;
* les conditions d'utilisation sont compatibles ;
* le connecteur produit des objets compatibles avec `JobOffer`.

---

# 20. Modèle interne

Tous les connecteurs doivent tendre vers un modèle commun.

Exemple :

```text
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

Les champs pourront évoluer.

L'objectif est que l'agent n'ait pas besoin de connaître la structure interne de chaque plateforme.

---

# 21. Principe d'abstraction

L'agent doit pouvoir fonctionner ainsi :

```text
Source A ──┐
Source B ──┤
Source C ──┼──→ Connecteurs ──→ JobOffer ──→ Agent
Source D ──┤
Source E ──┘
```

L'agent ne doit pas dépendre directement des spécificités de chaque plateforme.

Les différences doivent être absorbées par les connecteurs.

---

# 22. Recherche multi-IA

Plusieurs IA peuvent participer au même travail.

Exemple :

```text
Perplexity
    ↓
Découverte

Gemini
    ↓
Recherche complémentaire

ChatGPT
    ↓
Consolidation / structuration

Claude
    ↓
Audit critique

Sources officielles
    ↓
Vérification finale
```

Une IA ne doit pas considérer la réponse d'une autre IA comme une source primaire.

Le consensus entre plusieurs IA n'est pas une preuve.

Elles peuvent toutes avoir repris la même information erronée.

---

# 23. Déduplication des recherches

Avant d'ajouter une source :

1. rechercher si elle existe déjà dans `sources-master.md` ;
2. vérifier les variantes du nom ;
3. vérifier le domaine officiel ;
4. vérifier si elle existe déjà sous une autre catégorie.

Ne pas créer plusieurs entrées pour une même plateforme.

---

# 24. Mise à jour d'une source existante

Lorsqu'une nouvelle recherche apporte des informations concernant une source déjà présente :

* ne pas créer une nouvelle ligne ;
* compléter ou corriger l'entrée existante ;
* conserver la trace de la nouvelle vérification ;
* signaler les contradictions importantes ;
* mettre à jour le statut si nécessaire.

---

# 25. Gestion des informations contradictoires

Si deux sources donnent des informations différentes :

1. identifier précisément la contradiction ;
2. rechercher la documentation officielle ;
3. vérifier la date de chaque information ;
4. déterminer si les règles ont changé ;
5. conserver l'information la plus récente et la mieux sourcée ;
6. signaler l'incertitude si elle persiste.

Ne jamais choisir arbitrairement une information.

---

# 26. Recherche temporelle

Les informations techniques et contractuelles peuvent changer.

Toujours vérifier la date lorsque cela est pertinent.

Une ancienne documentation peut ne plus représenter :

* l'API actuelle ;
* les conditions actuelles ;
* les limites actuelles ;
* les possibilités commerciales actuelles.

Pour les informations importantes, conserver :

`Dernière vérification : YYYY-MM-DD`

---

# 27. Format attendu des résultats d'une IA

Lorsqu'une IA recherche de nouvelles sources, elle doit idéalement retourner :

```text
SOURCE
- Nom :
- URL officielle :
- Catégorie :
- Provenance :
- Couverture :
- Types d'offres :

ACCÈS
- Méthodes disponibles :
- Méthode recommandée :
- Authentification :
- Autorisation :

DONNÉES
- Champs disponibles :
- Fraîcheur :
- Volume :
- Diversité :

UTILISATION
- Stockage :
- Redistribution :
- Candidature :
- Coût :

ANALYSE
- Avantages :
- Limites :
- Risques :
- Valeur pour le projet :

VERDICT
- Statut proposé :

SOURCES DE VÉRIFICATION
- Documentation :
- Conditions :
- Autres sources :

DATE DE VÉRIFICATION :
```

Ce format facilite ensuite la transformation en ligne du tableau maître.

---

# 28. Format attendu pour l'analyse d'un connecteur

```text
SOURCE
- Nom :

CONNECTEUR
- Méthode :
- Type :
- Endpoint :
- Authentification :
- Credentials nécessaires :

DONNÉES
- Format :
- Champs :
- Pagination :
- Rate limit :

TRAITEMENT
- Parsing :
- Transformation :
- Normalisation :
- Déduplication :

ROBUSTESSE
- Erreurs :
- Retry :

UTILISATION
- Stockage :
- Candidature :

ÉTAT
- Statut :
- Problèmes :
- Actions restantes :

DATE DE VÉRIFICATION :
```

---

# 29. Règles de modification des tableaux

Une IA ne doit pas modifier silencieusement les tableaux.

Lorsqu'elle propose une modification importante, elle doit être capable d'indiquer :

* ce qui a changé ;
* pourquoi ;
* sur quelle source l'information repose ;
* à quelle date elle a été vérifiée.

Exemple :

```text
Modification :
Statut changé de 🟡 À surveiller vers 🟢 Connecteur à étudier.

Raison :
Une API officielle a été identifiée et sa documentation confirme
l'accès aux offres nécessaires.

Vérification :
Documentation officielle de l'API.
Date : 2026-09-19
```

---

# 30. Ce que l'IA ne doit jamais faire

L'IA ne doit jamais :

* inventer un endpoint ;
* inventer une API ;
* inventer une permission ;
* inventer une limite ;
* inventer un tarif ;
* inventer une capacité de candidature ;
* déclarer une intégration opérationnelle sans test ;
* considérer une page publique comme une autorisation générale ;
* contourner CAPTCHA ou anti-bot ;
* contourner une authentification ;
* contourner un rate limit ;
* exposer des credentials ;
* supprimer une source sans justification ;
* créer un doublon ;
* transformer une hypothèse en fait.

---

# 31. Principe de prudence

Lorsque l'information n'est pas connue :

> dire qu'elle n'est pas connue.

Il est préférable d'avoir :

`À vérifier`

plutôt qu'une information inventée ou insuffisamment vérifiée.

---

# 32. Priorité du projet

Le projet commence par maximiser :

1. pertinence des offres ;
2. couverture géographique ;
3. qualité des données ;
4. fraîcheur ;
5. diversité des sources ;
6. stabilité ;
7. conformité ;
8. coût ;
9. facilité d'intégration.

La complexité technique ne doit pas être recherchée pour elle-même.

Une solution simple et autorisée doit être privilégiée lorsqu'elle répond correctement au besoin.

---

# 33. Philosophie générale du projet

L'objectif n'est pas de connecter le plus grand nombre possible de plateformes.

L'objectif est de construire un système capable de fournir aux utilisateurs :

* des offres pertinentes ;
* provenant de sources suffisamment diverses ;
* avec des données fiables ;
* de manière régulière ;
* dans le respect des conditions d'accès ;
* avec une architecture maintenable.

La quantité de connecteurs n'est donc pas une fin en soi.

---

# 34. Workflow global

Le workflow de référence est :

```text
                    RECHERCHE
                       │
                       ↓
              Identification source
                       │
                       ↓
              Vérification primaire
                       │
                       ↓
             Analyse des méthodes
                       │
                       ↓
            Analyse autorisations
                       │
                       ↓
             Évaluation stratégique
                       │
                       ↓
              SOURCES-MASTER
                       │
            ┌──────────┴──────────┐
            │                     │
            ↓                     ↓
       🟢 À étudier         🟣 Partenariat
            │                     │
            │              obtention accord
            │                     │
            └──────────┬──────────┘
                       ↓
              CONNECTORS
                       │
                       ↓
                 Spécification
                       │
                       ↓
                 Développement
                       │
                       ↓
                     Tests
                       │
                       ↓
                🟢 Opérationnel
                       │
                       ↓
                 JOB OFFER
                       │
                       ↓
                     AGENT
```

---

# 35. Règle finale

Les trois documents ont chacun une responsabilité précise :

```text
sources-master.md
        =
QUELLES SOURCES ?

connectors.md
        =
COMMENT LES INTÉGRER ?

research-protocol.md
        =
COMMENT DÉCIDER ET TRAVAILLER ?
```

Aucun des trois documents ne doit remplacer les deux autres.

Ensemble, ils constituent le **référentiel de travail du Job Agent**.
