# Job Agent — Sources Master

## 1. Objectif du document

Ce document constitue le **référentiel principal des sources d'offres d'emploi** du projet Job Agent.

Il permet de :

* recenser les plateformes et sources potentielles ;
* comprendre la provenance des offres ;
* identifier les méthodes d'accès aux données ;
* évaluer les conditions d'utilisation ;
* mesurer l'intérêt de chaque source pour le projet ;
* décider quelles sources doivent faire l'objet d'une intégration technique ;
* conserver les sources écartées ou différées afin d'éviter de refaire inutilement les mêmes recherches.

Ce tableau constitue une **source de vérité stratégique** pour la sélection des sources.

Il ne constitue pas encore une spécification technique des connecteurs.

---

# 2. Principe fondamental

Une **source** et un **connecteur** sont deux choses différentes.

Une source représente :

> « Où se trouvent les offres d'emploi et quelle est leur valeur pour notre projet ? »

Un connecteur représente :

> « Comment notre système va-t-il techniquement récupérer et exploiter ces offres ? »

Une source peut donc exister dans ce tableau sans avoir encore de connecteur.

---

# 3. Dimensions d'analyse

Chaque source doit être analysée selon plusieurs dimensions indépendantes.

### 3.1 Provenance

Qui produit ou publie les données ?

Exemples :

* Job board ;
* entreprise ;
* ATS ;
* agence de recrutement ;
* organisme public ;
* agrégateur ;
* communauté ;
* plateforme freelance ;
* université / école ;
* autre.

### 3.2 Structure des données

Les données peuvent être :

* structurées ;
* semi-structurées ;
* non structurées.

### 3.3 Méthode d'accès

Exemples :

* API publique ;
* API avec clé ;
* OAuth ;
* API nécessitant une approbation ;
* RSS / Atom ;
* webhook ;
* export ;
* flux partenaire ;
* page publique ;
* page nécessitant un compte ;
* scraping ;
* crawling ;
* browser automation.

### 3.4 Autorisation

L'accès doit être évalué indépendamment de la possibilité technique.

Catégories possibles :

* explicitement autorisé ;
* autorisé sous conditions ;
* approbation nécessaire ;
* partenariat nécessaire ;
* à vérifier ;
* non autorisé ;
* impossible sans contournement.

Une donnée techniquement accessible n'est pas automatiquement une donnée que le projet peut légalement ou contractuellement exploiter.

---

# 4. Statuts définitifs du tableau maître

| Statut                        | Signification                                                                                                   |
| ----------------------------- | --------------------------------------------------------------------------------------------------------------- |
| 🟢 **Connecteur à étudier**   | Source suffisamment intéressante et exploitable pour que son intégration technique soit étudiée.                |
| 🟣 **Partenariat nécessaire** | Source intéressante, mais une autorisation, une approbation ou un partenariat est nécessaire avant intégration. |
| 🔵 **À étudier plus tard**    | Source pertinente mais non prioritaire pour le MVP.                                                             |
| 🟡 **À surveiller**           | Source potentiellement intéressante, mais informations insuffisantes ou situation susceptible d'évoluer.        |
| 🔴 **À exclure**              | Source incompatible, non pertinente, interdite ou nécessitant un contournement des protections.                 |

### Règle de transition

Une source :

`🟣 Partenariat nécessaire`

peut devenir :

`🟢 Connecteur à étudier`

après obtention et vérification de l'autorisation nécessaire.

Le statut du tableau maître est une **décision stratégique**.

Il ne signifie pas que le connecteur est techniquement opérationnel.

---

# 5. Tableau maître

| # | Plateforme / Source | Catégorie | Provenance des données | Couverture géographique | Types d'offres | Structure des données | Méthode(s) d'accès disponible(s) | Meilleure méthode identifiée | Authentification | Autorisation / statut d'accès | Conditions / restrictions | Données récupérables | Fraîcheur | Volume / diversité | Stockage autorisé ? | Affichage / redistribution autorisé ? | Lien de candidature | Candidature via API ? | Coût | Complexité d'intégration estimée | Maintenance estimée | Couverture unique | Valeur pour le projet | VERDICT | Source de vérification |
| - | ------------------- | --------- | ---------------------- | ----------------------- | -------------- | --------------------- | -------------------------------- | ---------------------------- | ---------------- | ----------------------------- | ------------------------- | -------------------- | --------- | ------------------ | ------------------- | ------------------------------------- | ------------------- | --------------------- | ---- | -------------------------------- | ------------------- | ----------------- | --------------------- | ------- | ---------------------- |

---

# 6. Règles de remplissage

## Plateforme / Source

Nom officiel de la plateforme ou de la source.

Ne pas créer de doublons pour une même source.

## Catégorie

Utiliser une catégorie cohérente avec la classification du projet :

* Job board généraliste ;
* Job board local ;
* plateforme professionnelle ;
* site carrière d'entreprise ;
* ATS ;
* portail public de l'emploi ;
* agence de recrutement ;
* plateforme freelance ;
* plateforme spécialisée ;
* plateforme stage / alternance ;
* portail universitaire ;
* réseau social ;
* communauté ;
* site de petites annonces ;
* newsletter / alerte ;
* agrégateur ;
* autre.

## Provenance des données

Identifier qui publie réellement les offres.

Exemple :

> ATS utilisé par plusieurs entreprises

et non simplement :

> plateforme de recrutement.

## Méthode(s) d'accès disponible(s)

Lister toutes les méthodes pertinentes identifiées.

Exemple :

> API publique + page publique

La colonne suivante doit ensuite identifier la méthode privilégiée.

## Meilleure méthode identifiée

Choisir la méthode présentant le meilleur compromis entre :

* autorisation ;
* stabilité ;
* qualité des données ;
* coût ;
* couverture ;
* complexité ;
* maintenance.

Une API officielle doit généralement être privilégiée lorsqu'elle est disponible et compatible avec l'utilisation prévue.

## Autorisation / statut d'accès

Ne jamais déduire l'autorisation uniquement de l'accessibilité technique.

Une page publique peut être techniquement accessible sans que toutes les utilisations envisagées soient autorisées.

## Conditions / restrictions

Documenter notamment :

* attribution obligatoire ;
* limitation du nombre de requêtes ;
* limitation commerciale ;
* interdiction de redistribution ;
* interdiction de stockage ;
* approbation préalable ;
* restrictions géographiques ;
* restrictions liées aux candidatures ;
* conditions liées aux données personnelles ;
* conditions liées au scraping.

## Données récupérables

Identifier les champs réellement accessibles.

Exemples :

* titre ;
* entreprise ;
* localisation ;
* description ;
* salaire ;
* type de contrat ;
* date de publication ;
* URL ;
* compétences ;
* niveau d'expérience ;
* secteur ;
* identifiant de l'offre.

Ne pas considérer qu'un champ existe simplement parce qu'il apparaît sur l'interface utilisateur.

## Fraîcheur

Évaluer :

* temps réel ;
* quasi temps réel ;
* quotidien ;
* périodique ;
* inconnue.

## Volume / diversité

Évaluer la quantité et la variété des offres accessibles.

## Stockage / affichage / redistribution

Ces trois notions doivent rester distinctes.

Le fait de pouvoir récupérer une donnée ne signifie pas automatiquement :

* que nous pouvons la stocker ;
* que nous pouvons la republier ;
* que nous pouvons la vendre ;
* que nous pouvons la transmettre à un utilisateur.

## Candidature

Distinguer :

1. lien permettant à l'utilisateur de candidater ;
2. formulaire externe ;
3. candidature via API ;
4. candidature automatisée ;
5. absence de mécanisme identifié.

## Valeur pour le projet

Évaluer la source selon :

* pertinence géographique ;
* pertinence des offres ;
* volume ;
* fraîcheur ;
* qualité ;
* diversité ;
* accessibilité ;
* autorisation ;
* coût ;
* complexité ;
* maintenance ;
* couverture unique.

Ne pas réduire la valeur à la popularité de la plateforme.

---

# 7. Règles de recherche et de vérification

Toute information importante doit être vérifiée autant que possible auprès de sources primaires.

Priorité :

1. documentation officielle ;
2. conditions d'utilisation officielles ;
3. documentation API officielle ;
4. documentation développeur ;
5. page officielle de la plateforme ;
6. source secondaire fiable ;
7. discussion ou forum uniquement comme piste de recherche.

Une information trouvée dans une source secondaire ne doit pas être considérée comme définitivement vérifiée lorsqu'elle concerne :

* l'existence d'une API ;
* les permissions ;
* le scraping ;
* le stockage ;
* la redistribution ;
* l'utilisation commerciale ;
* les limites ;
* la candidature automatisée.

---

# 8. Règle de prudence

Le projet ne doit jamais contourner :

* authentification ;
* CAPTCHA ;
* protection anti-bot ;
* contrôle d'accès ;
* limitation volontaire d'une API ;
* mécanisme de sécurité.

Lorsqu'une intégration nécessiterait un contournement, la source doit être classée :

**🔴 À exclure**

ou faire l'objet d'une analyse spécifique si une solution officielle existe.

---

# 9. Relation avec le tableau des connecteurs

Une source peut être sélectionnée pour une étude technique lorsqu'elle obtient :

**🟢 Connecteur à étudier**

Le travail passe alors au fichier :

`connectors.md`

Le statut 🟢 du tableau maître ne signifie donc pas :

> « Le connecteur fonctionne. »

Il signifie :

> « Cette source mérite que nous étudiions son intégration. »

---

# 10. Historique et traçabilité

Lorsqu'une information importante est modifiée, conserver autant que possible :

* la date de vérification ;
* la source utilisée ;
* la raison de la modification ;
* l'ancien statut lorsque cela est pertinent.

Une source ne doit pas être supprimée simplement parce qu'elle n'est pas exploitable actuellement.

Son statut peut évoluer avec le temps.
