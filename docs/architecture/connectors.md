# Job Agent — Connectors

## 1. Objectif du document

Ce document constitue le **référentiel technique des connecteurs** du projet Job Agent.

Il permet de décrire comment chaque source sélectionnée dans `sources-master.md` sera techniquement intégrée au système.

Il sert à :

* spécifier les méthodes d'accès ;
* identifier les endpoints et flux ;
* documenter l'authentification ;
* définir les données récupérées ;
* préparer la normalisation ;
* préparer la déduplication ;
* définir les stratégies d'erreur et de retry ;
* suivre l'état de développement ;
* vérifier qu'un connecteur est réellement utilisable par l'agent.

Ce document constitue une **source de vérité technique** pour les intégrations.

---

# 2. Relation avec le tableau maître

Le fichier `sources-master.md` répond à la question :

> **« Avec quelles sources voulons-nous travailler ? »**

Le présent fichier répond à :

> **« Comment allons-nous techniquement travailler avec ces sources ? »**

Le passage est :

```text
Recherche
    ↓
Sources Master
    ↓
🟢 Connecteur à étudier
    ↓
Spécification
    ↓
Développement
    ↓
Tests
    ↓
🟢 Opérationnel
    ↓
Utilisation par l'agent
```

---

# 3. Statuts définitifs des connecteurs

| Statut                        | Signification                                                                     |
| ----------------------------- | --------------------------------------------------------------------------------- |
| ⚪ **À étudier**               | La méthode d'intégration n'a pas encore été suffisamment analysée.                |
| 🔵 **Spécification en cours** | L'architecture et le fonctionnement du connecteur sont en cours de définition.    |
| 🟣 **En attente d'accès**     | Une clé API, des identifiants, une approbation ou un partenariat est nécessaire.  |
| 🟠 **En développement**       | Le connecteur est actuellement en cours d'implémentation.                         |
| 🟢 **Opérationnel**           | Le connecteur fonctionne, a été testé et peut être utilisé par l'agent.           |
| 🟡 **À corriger / instable**  | Le connecteur fonctionne mais présente des problèmes nécessitant une correction.  |
| 🟤 **Maintenance requise**    | Le connecteur nécessite une intervention ou une mise à jour.                      |
| 🔴 **Bloqué**                 | Le connecteur ne peut actuellement pas fonctionner.                               |
| ⚫ **Abandonné**               | Le connecteur n'est plus maintenu ou la décision est prise de ne plus l'utiliser. |

---

# 4. Règle fondamentale du statut 🟢 Opérationnel

Un connecteur ne doit pas être considéré comme **🟢 Opérationnel** simplement parce que :

* l'API existe ;
* la documentation existe ;
* une requête fonctionne ponctuellement ;
* du code a été écrit.

Pour être 🟢 Opérationnel, il doit au minimum être vérifié que :

1. l'accès fonctionne ;
2. l'authentification fonctionne si nécessaire ;
3. les données sont effectivement récupérées ;
4. les données nécessaires sont suffisamment complètes ;
5. le parsing fonctionne ;
6. la normalisation fonctionne ;
7. les principales erreurs sont gérées ;
8. les limites d'utilisation sont respectées ;
9. les conditions d'utilisation sont compatibles avec l'usage prévu ;
10. le connecteur peut alimenter le modèle interne `JobOffer`.

---

# 5. Tableau des connecteurs

| # | Source | Statut maître | Méthode sélectionnée | Type de connecteur | Endpoint / URL / Feed | Authentification | Identifiants nécessaires | Documentation | Format des données | Champs disponibles | Pagination | Rate limit | Fréquence de collecte | Filtrage possible à la source | Transformation / parsing | Normalisation | Déduplication | Gestion des erreurs | Retry | Stockage | Conditions d'utilisation | Candidature possible | Méthode de candidature | Coût technique | Complexité réelle | Maintenance réelle | Dernière vérification | CONNECTOR STATUS |
| - | ------ | ------------- | -------------------- | ------------------ | --------------------- | ---------------- | ------------------------ | ------------- | ------------------ | ------------------ | ---------- | ---------- | --------------------- | ----------------------------- | ------------------------ | ------------- | ------------- | ------------------- | ----- | -------- | ------------------------ | -------------------- | ---------------------- | -------------- | ----------------- | ------------------ | --------------------- | ---------------- |

---

# 6. Règles de remplissage

## Source

La source doit correspondre à une entrée existante dans :

`sources-master.md`

Ne pas créer un connecteur pour une source qui n'existe pas dans le tableau maître.

## Statut maître

Reporter le statut actuel de la source.

Le connecteur doit être cohérent avec ce statut.

Une source :

**🟢 Connecteur à étudier**

peut normalement entrer dans le processus de spécification.

Une source :

**🟣 Partenariat nécessaire**

doit rester bloquée tant que l'accès nécessaire n'est pas obtenu.

## Méthode sélectionnée

Indiquer la méthode effectivement retenue.

Exemples :

* API REST ;
* API GraphQL ;
* RSS ;
* Atom ;
* webhook ;
* export JSON ;
* export CSV ;
* flux partenaire ;
* crawling ;
* scraping ;
* browser automation.

La méthode sélectionnée doit être justifiée par rapport aux alternatives disponibles.

## Type de connecteur

Exemples :

* REST API connector ;
* RSS connector ;
* scraper ;
* crawler ;
* browser automation connector ;
* file importer ;
* webhook receiver ;
* partner feed connector.

## Endpoint / URL / Feed

Indiquer le point d'entrée réellement utilisé.

Ne pas inventer d'endpoint.

Si l'information n'est pas encore vérifiée :

`À vérifier`

## Authentification

Indiquer précisément :

* aucune ;
* API key ;
* Bearer token ;
* OAuth 2.0 ;
* Basic Auth ;
* cookie/session ;
* credentials partenaires ;
* autre.

Ne jamais placer de secret réel dans ce document.

## Identifiants nécessaires

Documenter le type de credentials nécessaire, jamais leur valeur.

Exemple :

```text
JOBBOARD_API_KEY
JOBBOARD_CLIENT_ID
JOBBOARD_CLIENT_SECRET
```

Les secrets doivent rester dans un gestionnaire de secrets ou dans des variables d'environnement.

---

# 7. Données et normalisation

Le connecteur ne doit pas simplement récupérer des données.

Il doit permettre leur transformation vers le modèle interne du projet.

Exemple de modèle conceptuel :

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

Le modèle réel pourra évoluer.

Le connecteur doit donc être conçu comme une couche d'adaptation :

```text
SOURCE EXTERNE
      ↓
CONNECTEUR
      ↓
PARSING
      ↓
TRANSFORMATION
      ↓
NORMALISATION
      ↓
JobOffer
```

---

# 8. Déduplication

La récupération de plusieurs sources peut produire plusieurs représentations de la même offre.

La déduplication doit donc être pensée au niveau global du système.

Signaux possibles :

* identifiant officiel de l'offre ;
* URL canonique ;
* combinaison entreprise + titre + localisation ;
* similarité de contenu ;
* date ;
* autres caractéristiques.

La stratégie exacte de déduplication sera définie lors de l'implémentation.

---

# 9. Gestion des erreurs

Chaque connecteur doit prévoir au minimum les catégories suivantes :

* erreur réseau ;
* timeout ;
* erreur d'authentification ;
* erreur de permission ;
* rate limit ;
* réponse invalide ;
* changement de structure ;
* données manquantes ;
* endpoint indisponible ;
* source temporairement indisponible.

Le comportement attendu doit être documenté.

---

# 10. Retry

Un mécanisme de retry peut être utilisé pour les erreurs temporaires.

Il ne doit pas être utilisé pour contourner :

* un refus d'autorisation ;
* une restriction d'accès ;
* un rate limit sans respecter les règles de la plateforme ;
* un CAPTCHA ;
* une protection anti-bot.

Les retries doivent respecter les limites et recommandations de la source.

---

# 11. Fréquence de collecte

La fréquence doit dépendre :

* de la fraîcheur souhaitée ;
* du volume ;
* des rate limits ;
* du coût ;
* des conditions d'utilisation ;
* de la fréquence de publication de la source.

Exemples :

```text
Toutes les 15 minutes
Toutes les heures
Toutes les 6 heures
Une fois par jour
À la demande
Webhook
```

La fréquence ne doit jamais être choisie uniquement pour maximiser le volume de données.

---

# 12. Candidature

Il faut distinguer :

### A. Redirection

L'agent fournit :

`application_url`

L'utilisateur est redirigé vers la plateforme.

### B. Préparation

L'agent prépare :

* CV ;
* lettre ;
* réponses ;
* informations nécessaires.

L'utilisateur valide avant l'envoi.

### C. Soumission

Le système effectue effectivement la candidature.

Cette fonctionnalité nécessite une analyse spécifique des permissions, des conditions de la plateforme et du consentement de l'utilisateur.

Un connecteur capable de récupérer des offres n'est pas automatiquement capable de soumettre des candidatures.

---

# 13. Validation d'un connecteur

Avant de passer à :

**🟢 Opérationnel**

effectuer une validation couvrant :

### Accès

* accès disponible ;
* authentification fonctionnelle ;
* permissions suffisantes.

### Données

* offres récupérées ;
* champs nécessaires disponibles ;
* format correctement interprété.

### Transformation

* parsing fonctionnel ;
* normalisation fonctionnelle ;
* modèle `JobOffer` alimenté correctement.

### Robustesse

* erreurs principales gérées ;
* retry approprié ;
* rate limits respectés.

### Produit

* offres réellement exploitables par l'agent ;
* URL de candidature valide lorsque disponible ;
* absence de données inutilisables.

### Conformité

* conditions d'utilisation vérifiées ;
* stockage compatible ;
* affichage / redistribution compatible ;
* méthode d'accès autorisée.

---

# 14. Cycle de vie d'un connecteur

```text
⚪ À étudier
      ↓
🔵 Spécification en cours
      ↓
🟣 En attente d'accès
      ↓
🟠 En développement
      ↓
Tests
      ↓
🟢 Opérationnel
```

Des transitions peuvent également conduire à :

```text
🟡 À corriger / instable
      ↓
🟠 En développement
      ↓
🟢 Opérationnel
```

ou :

```text
🟢 Opérationnel
      ↓
🟤 Maintenance requise
      ↓
🟢 Opérationnel
```

En cas d'impossibilité :

```text
🟠 En développement
      ↓
🔴 Bloqué
```

Un connecteur définitivement abandonné peut devenir :

```text
⚫ Abandonné
```

---

# 15. Règle importante : développement ≠ opérationnel

Le statut :

**🟠 En développement**

signifie :

> Le connecteur est en train d'être implémenté.

Le statut :

**🟢 Opérationnel**

signifie :

> Le connecteur a été suffisamment testé et validé pour être utilisé par l'agent.

Il est donc parfaitement normal de coder un connecteur lorsqu'il est 🟠.

En revanche, le connecteur doit être 🟢 avant de considérer l'intégration comme prête pour une utilisation en production.

---

# 16. Sécurité

Ne jamais stocker dans ce document :

* clés API ;
* mots de passe ;
* tokens ;
* secrets OAuth ;
* cookies de session ;
* credentials personnels.

Le document doit uniquement indiquer **quels credentials sont nécessaires**.

Les valeurs doivent être conservées dans :

* variables d'environnement ;
* secret manager ;
* infrastructure sécurisée.

---

# 17. Principe de séparation

Le système doit conserver trois niveaux distincts :

```text
SOURCE
│
│  Décision stratégique
↓
SOURCES MASTER
│
│  Sélection
↓
CONNECTEUR
│
│  Implémentation technique
↓
AGENT
```

Le tableau maître ne valide pas automatiquement le connecteur.

Le connecteur ne modifie pas automatiquement le statut stratégique de la source.

Les deux référentiels doivent rester indépendants tout en étant reliés par le champ `Source`.

---

# 18. Règle de traçabilité

Chaque connecteur doit pouvoir répondre à quatre questions :

1. Quelle source intégrons-nous ?
2. Par quelle méthode ?
3. Sur quelle base avons-nous choisi cette méthode ?
4. Quand avons-nous vérifié que cette intégration fonctionnait ?

La colonne `Dernière vérification` doit donc être mise à jour lors des validations importantes.

---

# 19. Principe général

Le connecteur est une **couche d'adaptation entre une source externe et le modèle interne du Job Agent**.

```text
Source externe
      ↓
Access method
      ↓
Connector
      ↓
Raw data
      ↓
Parsing
      ↓
Normalization
      ↓
Deduplication
      ↓
JobOffer
      ↓
Agent
```

Le connecteur ne doit pas contenir la logique métier principale de l'agent.

Son rôle principal est de rendre les données externes **accessibles, fiables et compatibles avec le modèle interne**.
