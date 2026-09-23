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

Chaque source est analysée selon plusieurs dimensions indépendantes.

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

# 4. Statuts du tableau maître

| Statut                        | Signification                                                                                                                |
| ----------------------------- | ---------------------------------------------------------------------------------------------------------------------------- |
| 🟢 **Connecteur à étudier**   | Source suffisamment intéressante et exploitable pour que son intégration technique soit étudiée.                             |
| 🟣 **Partenariat nécessaire** | Source intéressante, mais une autorisation, une approbation, une licence ou un partenariat est nécessaire avant intégration. |
| 🔵 **À étudier plus tard**    | Source pertinente mais non prioritaire pour le MVP.                                                                          |
| 🟡 **À surveiller**           | Source potentiellement intéressante, mais informations insuffisantes ou situation susceptible d'évoluer.                     |
| 🔴 **À exclure**              | Source incompatible, non pertinente, interdite ou nécessitant un contournement des protections.                              |

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

> **Convention :**
>
> * `Non vérifié` = l'information provient de la recherche initiale mais n'a pas encore été confirmée par une source primaire.
> * `À vérifier` = une information existe mais nécessite une vérification avant décision finale.
> * `Non identifié` = aucun mécanisme n'a été identifié lors de cette recherche.
> * `N/A` = la notion ne s'applique pas réellement à la source.

|  # | Plateforme / Source                     | Catégorie                      | Provenance des données                        | Couverture géographique                  | Types d'offres                   | Structure des données                   | Méthode(s) d'accès disponible(s)             | Meilleure méthode identifiée        | Authentification                                       | Autorisation / statut d'accès                        | Conditions / restrictions                                                                                                                                  | Données récupérables                                                                                               | Fraîcheur                        | Volume / diversité                                          | Stockage autorisé ?         | Affichage / redistribution autorisé ?                    | Lien de candidature            | Candidature via API ?                                               | Coût                                   | Complexité d'intégration estimée | Maintenance estimée | Couverture unique                                           | Valeur pour le projet                      | VERDICT | Source de vérification                                                                                                                                             |
| -: | --------------------------------------- | ------------------------------ | --------------------------------------------- | ---------------------------------------- | -------------------------------- | --------------------------------------- | -------------------------------------------- | ----------------------------------- | ------------------------------------------------------ | ---------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------ | -------------------------------- | ----------------------------------------------------------- | --------------------------- | -------------------------------------------------------- | ------------------------------ | ------------------------------------------------------------------- | -------------------------------------- | -------------------------------- | ------------------- | ----------------------------------------------------------- | ------------------------------------------ | ------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
|  1 | **EmploiDakar.com**                     | Job board local                | Plateforme / recruteurs                       | Sénégal / Dakar / sous-région            | CDI, CDD, stages, autres         | Semi-structurée / HTML                  | Page publique                                | À déterminer                        | Aucune pour page publique                              | À vérifier                                           | Conditions d'utilisation et réutilisation à vérifier                                                                                                       | Titre, entreprise, localisation, description, type, date, URL selon page                                           | Régulière                        | Élevé selon données déclarées par la plateforme             | À vérifier                  | À vérifier                                               | Oui, selon offre               | Non identifié                                                       | À vérifier                             | Moyenne                          | Moyenne à élevée    | Forte couverture Sénégal                                    | **Très élevée**                            | 🟡      | Site officiel ; la plateforme indique plus de 2 000 offres actualisées en permanence et plus de 60 000 membres.                                                    |
|  2 | **Senjob**                              | Job board local / régional     | Plateforme / recruteurs                       | Sénégal + Afrique de l'Ouest francophone | Emploi généraliste               | Semi-structurée / HTML                  | Page publique ; automatisation à vérifier    | À vérifier                          | Aucune pour page publique                              | Conditions de réutilisation à vérifier               | Restrictions sur reproduction / usage non personnel à vérifier avant automatisation                                                                        | Titre, entreprise, localisation, contrat, catégorie, expiration, description selon offre                           | Régulière                        | Élevé                                                       | À vérifier                  | À vérifier                                               | Oui                            | Non vérifiée                                                        | À vérifier                             | Moyenne                          | Moyenne             | Forte couverture Afrique de l'Ouest francophone             | **Très élevée**                            | 🟣      | Site officiel et présentation Senjob.                                                                                                                              |
|  3 | **Ligeey.com**                          | Agrégateur / job board         | Plusieurs sources                             | Afrique francophone                      | Emploi / opportunités            | HTML / semi-structurée                  | Pages publiques                              | À vérifier                          | Aucune identifiée                                      | À vérifier                                           | Réutilisation et automatisation à vérifier                                                                                                                 | Titre, entreprise, localisation, type d'opportunité, date selon offre                                              | Actualisation annoncée fréquente | Potentiellement élevé                                       | À vérifier                  | À vérifier                                               | Oui selon source               | Non identifié                                                       | À vérifier                             | Moyenne                          | Moyenne             | Couverture francophone                                      | **Très élevée**                            | 🟡      |                                                                                                                                                                    |
|  4 | **Expat-Dakar Emploi**                  | Site de petites annonces       | Annonceurs / recruteurs                       | Sénégal / Dakar                          | Emploi + petites annonces        | HTML                                    | Page publique                                | À vérifier                          | Aucune pour accès public                               | À vérifier                                           | Conditions de scraping / redistribution à vérifier                                                                                                         | Titre, description, localisation, entreprise / annonceur, date selon annonce                                       | Régulière                        | Moyen à élevé                                               | À vérifier                  | À vérifier                                               | Oui selon annonce              | Non identifié                                                       | À vérifier                             | Moyenne                          | Moyenne             | Forte présence locale                                       | **Élevée**                                 | 🟡      |                                                                                                                                                                    |
|  5 | **TrouvezJob.org**                      | Job board local                | Recruteurs / plateforme                       | Sénégal / Dakar                          | Emploi                           | HTML                                    | Page publique                                | À vérifier                          | Aucune                                                 | À vérifier                                           | Réutilisation à vérifier                                                                                                                                   | Titre, entreprise, localisation, description, type selon offre                                                     | À vérifier                       | Moyen                                                       | À vérifier                  | À vérifier                                               | Oui                            | Non identifié                                                       | À vérifier                             | Moyenne                          | Moyenne             | Source locale supplémentaire                                | **Moyenne**                                | 🟡      |                                                                                                                                                                    |
|  6 | **Emploi-jeune.com**                    | Job board / jeunesse           | Recruteurs / plateforme                       | Sénégal                                  | Emploi jeunes                    | HTML                                    | Page publique                                | À vérifier                          | Aucune                                                 | À vérifier                                           | Réutilisation à vérifier                                                                                                                                   | Titre, entreprise, localisation, description                                                                       | À vérifier                       | Moyen                                                       | À vérifier                  | À vérifier                                               | Oui                            | Non identifié                                                       | À vérifier                             | Moyenne                          | Moyenne             | Segment jeunes                                              | **Moyenne**                                | 🟡      |                                                                                                                                                                    |
|  7 | **DirectEmploi.com**                    | Agrégateur / job board         | Entreprises / agrégateur                      | International, présence Dakar limitée    | Emploi généraliste               | HTML                                    | Page publique                                | Non prioritaire                     | Aucune                                                 | À vérifier                                           | Conditions de réutilisation à vérifier                                                                                                                     | Informations d'offres publiques                                                                                    | Régulière                        | Élevé globalement mais faible valeur Sénégal                | À vérifier                  | À vérifier                                               | Oui                            | Non identifié                                                       | À vérifier                             | Moyenne                          | Moyenne             | Faible couverture cible                                     | **Faible pour MVP**                        | 🔴      | Recherche initiale                                                                                                                                                 |
|  8 | **Greenhouse Job Board API**            | ATS                            | Entreprises utilisant Greenhouse              | International                            | Emploi entreprise                | JSON structuré                          | API publique GET                             | API Job Board                       | Pas d'authentification pour GET                        | Données publiques via GET ; candidature API protégée | API de chaque job board ; utilisation et redistribution à vérifier selon contexte                                                                          | ID, titre, localisation, URL, date, contenu, départements, bureaux, métadonnées exposées                           | Dépend de l'entreprise           | Très élevé à l'échelle des entreprises utilisant Greenhouse | À vérifier selon usage      | À vérifier selon usage                                   | Oui                            | Oui, avec API key pour POST                                         | À vérifier                             | Moyenne                          | Faible à moyenne    | Accès direct aux offres des entreprises Greenhouse          | **Très élevée**                            | 🟢      | Documentation officielle Greenhouse : les GET sont publics ; la soumission d'une candidature nécessite une clé API.                                                |
|  9 | **Lever Postings API**                  | ATS                            | Entreprises utilisant Lever                   | International                            | Emploi entreprise                | JSON / HTML / XML                       | API REST publique pour offres publiées       | API Postings                        | Pas d'authentification pour offres publiées            | Accès aux offres publiées ; candidature API avec clé | L'API est organisée par entreprise/site et ne constitue pas une recherche globale de toutes les offres Lever                                               | ID, titre, localisation, description, catégories, type de contrat, équipe, salaire si publié, URL, apply URL       | Dépend de l'entreprise           | Très élevé via nombreuses entreprises                       | À vérifier                  | À vérifier ; API permet de récupérer les offres publiées | Oui                            | Oui avec API key côté entreprise                                    | À vérifier                             | Moyenne                          | Moyenne             | Accès structuré aux offres Lever                            | **Très élevée**                            | 🟢      | Documentation officielle Lever.                                                                                                                                    |
| 10 | **Ashby Job Postings API**              | ATS                            | Entreprises utilisant Ashby                   | International                            | Emploi entreprise                | JSON structuré                          | API publique                                 | Job Postings API                    | Pas d'authentification identifiée pour endpoint public | Public pour offres publiées                          | Endpoint lié au job board d'une organisation ; pas de moteur global Ashby identifié                                                                        | Titre, localisation, localisations secondaires, département, équipe, type, compensation si publiée, URL            | Dépend de l'entreprise           | Élevé                                                       | À vérifier                  | À vérifier                                               | Oui                            | Non identifié pour candidature générique                            | À vérifier                             | Faible à moyenne                 | Faible à moyenne    | Entreprises utilisant Ashby                                 | **Très élevée**                            | 🟢      | Documentation officielle Ashby.                                                                                                                                    |
| 11 | **Workday Career Sites**                | ATS                            | Entreprises utilisant Workday                 | International                            | Emploi entreprise                | JSON / HTML                             | Endpoints publics variables selon entreprise | À identifier au cas par cas         | Généralement aucune pour pages publiques               | À vérifier par entreprise                            | Pas de standard public universel confirmé pour notre usage                                                                                                 | Titre, localisation, description, requisitions selon site                                                          | Variable                         | Très élevé                                                  | À vérifier                  | À vérifier                                               | Oui                            | Non identifié                                                       | À vérifier                             | Élevée                           | Élevée              | Très forte présence entreprise                              | **Élevée**                                 | 🟡      | Vérification technique encore nécessaire                                                                                                                           |
| 12 | **Recruitee Careers Site API**          | ATS                            | Entreprises utilisant Recruitee               | International                            | Emploi entreprise                | JSON                                    | API Careers Site                             | API avec token                      | Token Careers Site                                     | Autorisation liée au compte / entreprise             | Token nécessaire ; périmètre lié à un compte spécifique                                                                                                    | Offres, détails, candidats selon permissions du token                                                              | Dépend de l'entreprise           | Élevé                                                       | À vérifier                  | À vérifier                                               | Oui                            | Oui pour certaines opérations selon compte                          | À vérifier                             | Moyenne                          | Moyenne             | Accès structuré aux entreprises Recruitee                   | **Élevée**                                 | 🟣      | Documentation officielle Recruitee : token requis et limité au compte concerné.                                                                                    |
| 13 | **Jobvite Jobs API**                    | ATS                            | Entreprises utilisant Jobvite                 | International                            | Emploi entreprise                | JSON / API                              | API / accès via support                      | API si autorisée                    | Clé / accès à confirmer                                | Approbation / accès à confirmer                      | Documentation publique insuffisante pour notre cas                                                                                                         | Offres selon API disponible                                                                                        | À vérifier                       | Élevé                                                       | À vérifier                  | À vérifier                                               | Oui                            | À vérifier                                                          | À vérifier                             | Moyenne à élevée                 | Moyenne             | Entreprises Jobvite                                         | **Moyenne à élevée**                       | 🟣      | Recherche initiale ; accès primaire à confirmer                                                                                                                    |
| 14 | **iCIMS Board Listing API**             | ATS                            | Entreprises utilisant iCIMS                   | International                            | Emploi entreprise                | JSON / API                              | API / accès partenaire selon configuration   | À déterminer                        | À déterminer                                           | Approbation / accès à confirmer                      | Documentation publique limitée                                                                                                                             | Offres selon instance                                                                                              | À vérifier                       | Élevé                                                       | À vérifier                  | À vérifier                                               | Oui                            | À vérifier                                                          | À vérifier                             | Élevée                           | Élevée              | Large base ATS                                              | **Moyenne à élevée**                       | 🟣      | Recherche initiale ; documentation primaire à approfondir                                                                                                          |
| 15 | **LinkedIn Jobs API**                   | Plateforme professionnelle     | Employeurs / LinkedIn                         | International                            | Emploi                           | API structurée                          | APIs partenaires                             | API partenaire                      | OAuth / accès partenaire                               | Approbation LinkedIn nécessaire                      | Accès réservé aux partenaires autorisés ; restrictions contractuelles                                                                                      | Selon produit / partenariat                                                                                        | Variable                         | Très élevé                                                  | Selon contrat               | Selon contrat                                            | Oui                            | Selon partenariat                                                   | Potentiellement élevé                  | Très élevée                      | Élevée              | Couverture LinkedIn                                         | **Très élevée mais non MVP**               | 🟣      | Documentation LinkedIn : accès réservé aux développeurs approuvés ; la page indique actuellement ne pas accepter de nouveaux partenariats pour le Job Posting API. |
| 16 | **Indeed Job Sync API**                 | Agrégateur / plateforme emploi | Employeurs / ATS                              | International                            | Emploi                           | GraphQL                                 | API partenaire                               | Non adaptée à la recherche d'offres | OAuth / partenariat                                    | Partenaire ATS                                       | Cette API sert à créer, mettre à jour et gérer des offres sur Indeed ; ce n'est pas une API de recherche des offres pour notre agent                       | Données d'offres envoyées vers Indeed                                                                              | Variable                         | Très élevé                                                  | Selon contrat               | Selon contrat                                            | Indeed Apply selon intégration | Non pour notre cas de recherche                                     | Partenariat                            | Élevée                           | Élevée              | Accès à l'écosystème Indeed mais mauvaise capacité pour MVP | **Faible pour le besoin actuel**           | 🔴      | Documentation officielle Indeed.                                                                                                                                   |
| 17 | **Glassdoor API**                       | Plateforme professionnelle     | Entreprises / Glassdoor                       | International                            | Emploi                           | API / données propriétaires             | API partenaire fermée                        | Aucune publique                     | Partenariat                                            | Partenariat nécessaire                               | Pas d'API publique identifiée                                                                                                                              | Selon partenariat                                                                                                  | Variable                         | Élevé                                                       | Contrat                     | Contrat                                                  | Oui                            | Selon partenariat                                                   | À négocier                             | Très élevée                      | Élevée              | Forte notoriété / données employeurs                        | **Faible pour MVP**                        | 🔴      | Recherche initiale ; accès officiel à confirmer                                                                                                                    |
| 18 | **Adzuna API**                          | Agrégateur                     | Plusieurs job boards / employeurs             | 50+ pays selon marché                    | Emploi généraliste               | JSON REST                               | API                                          | API officielle                      | `app_id` / `app_key`                                   | Accès soumis aux conditions Adzuna                   | 25 req/min, 250/jour, 1000/semaine, 2500/mois par défaut ; usage commercial continu peut nécessiter une licence ; attribution obligatoire pour publication | Titre, entreprise, localisation, description, salaire, catégorie, date, URL selon endpoint                         | Régulière                        | Très élevé                                                  | Selon licence               | Publication soumise aux conditions / attribution         | Oui, lien source               | Non identifié pour candidature générale                             | Essai / licence selon usage            | Faible à moyenne                 | Moyenne             | Agrégation multi-pays                                       | **Très élevée mais licence à clarifier**   | 🟣      | Conditions officielles Adzuna.                                                                                                                                     |
| 19 | **Jooble API**                          | Agrégateur                     | Plusieurs sources                             | International / par marchés              | Emploi généraliste               | JSON REST                               | API                                          | API officielle                      | Clé API                                                | Accès par clé et domaine régional                    | Une clé par domaine/pays ; quota gratuit indiqué de 500 requêtes à vie par clé ; conditions API à respecter                                                | Mots-clés, localisation, titre, entreprise, salaire, lien, résultats selon API                                     | Régulière                        | Élevé                                                       | À vérifier selon conditions | À vérifier                                               | Oui                            | Non identifié                                                       | Gratuit limité / conditions à vérifier | Faible à moyenne                 | Moyenne             | Agrégation internationale                                   | **Élevée**                                 | 🟢      | Documentation officielle Jooble, mise à jour en août 2026.                                                                                                         |
| 20 | **Devex Job Posting API**               | Plateforme spécialisée         | Organisations internationales / développement | International / Afrique                  | Développement, ONG, humanitaire  | REST / XML                              | API avec accès                               | API si approuvée                    | Clé                                                    | Accès sur demande                                    | Usage et redistribution à vérifier                                                                                                                         | Offres du secteur développement                                                                                    | Régulière                        | Élevé dans son secteur                                      | À vérifier                  | À vérifier                                               | Oui                            | À vérifier                                                          | À négocier                             | Moyenne                          | Moyenne             | Forte couverture développement international                | **Élevée pour secteur ciblé**              | 🟣      |                                                                                                                                                                    |
| 21 | **ReliefWeb Jobs**                      | Portail spécialisé             | ONU / organisations humanitaires              | International / Afrique                  | Humanitaire / ONG                | HTML                                    | Pages publiques / filtres                    | À vérifier                          | Aucune pour pages publiques                            | Réutilisation à vérifier                             | API non identifiée comme méthode principale dans cette recherche                                                                                           | Titre, organisation, localisation, date, description, lien                                                         | Régulière                        | Élevé dans le secteur                                       | À vérifier                  | À vérifier                                               | Oui                            | Non identifié                                                       | À vérifier                             | Moyenne                          | Moyenne             | Forte couverture humanitaire                                | **Élevée pour secteur ciblé**              | 🟡      |                                                                                                                                                                    |
| 22 | **UN Careers**                          | Portail institutionnel         | Organisation des Nations unies                | International                            | Emplois ONU                      | HTML / endpoints variables              | Pages publiques                              | À vérifier                          | Aucune pour pages publiques                            | À vérifier                                           | Endpoints internes/non documentés à ne pas considérer comme API officielle sans confirmation                                                               | Titre, organisation, localisation, niveau, description, date, URL selon offre                                      | Régulière                        | Élevé                                                       | À vérifier                  | À vérifier                                               | Oui                            | Non identifié                                                       | Gratuit côté consultation              | Moyenne à élevée                 | Moyenne             | Forte valeur institutionnelle                               | **Élevée**                                 | 🟡      |                                                                                                                                                                    |
| 23 | **UN Talent**                           | Portail emploi spécialisé      | Système ONU / recrutement international       | International                            | Emploi international             | HTML                                    | Page publique                                | À vérifier                          | Aucune                                                 | À vérifier                                           | API non identifiée                                                                                                                                         | Informations d'offres selon page                                                                                   | Régulière                        | Moyen à élevé                                               | À vérifier                  | À vérifier                                               | Oui                            | Non identifié                                                       | À vérifier                             | Moyenne                          | Moyenne             | Couverture institutionnelle                                 | **Moyenne à élevée**                       | 🟡      |                                                                                                                                                                    |
| 24 | **BrighterMonday**                      | Job board régional             | Recruteurs / plateforme                       | Kenya / Afrique de l'Est                 | Emploi généraliste               | HTML                                    | Page publique                                | Non prioritaire                     | Aucune pour page publique                              | À vérifier                                           | Scraping à éviter sans autorisation                                                                                                                        | Offres publiques selon page                                                                                        | Régulière                        | Élevé régionalement                                         | À vérifier                  | À vérifier                                               | Oui                            | Non identifié                                                       | À vérifier                             | Moyenne                          | Moyenne             | Faible couverture Sénégal                                   | **Faible pour MVP**                        | 🔴      |                                                                                                                                                                    |
| 25 | **Jobberman**                           | Job board régional             | Recruteurs / plateforme                       | Nigeria / Afrique anglophone             | Emploi généraliste               | HTML                                    | Page publique                                | Non prioritaire                     | Aucune                                                 | À vérifier                                           | Scraping à éviter sans autorisation                                                                                                                        | Offres selon page                                                                                                  | Régulière                        | Élevé régionalement                                         | À vérifier                  | À vérifier                                               | Oui                            | Non identifié                                                       | À vérifier                             | Moyenne                          | Moyenne             | Nigeria / Afrique anglophone                                | **Faible pour MVP**                        | 🔴      |                                                                                                                                                                    |
| 26 | **Fuzu**                                | Job board / carrière           | Recruteurs / plateforme                       | Kenya, Nigeria, Ouganda                  | Emploi / carrière                | HTML                                    | Page publique                                | Non prioritaire                     | Aucune                                                 | À vérifier                                           | Scraping / redistribution à vérifier                                                                                                                       | Offres, profils, contenu carrière selon accès                                                                      | Régulière                        | Élevé régionalement                                         | À vérifier                  | À vérifier                                               | Oui                            | Non identifié                                                       | À vérifier                             | Moyenne                          | Moyenne             | Afrique de l'Est                                            | **Faible pour MVP**                        | 🔴      |                                                                                                                                                                    |
| 27 | **ProGigFinder**                        | Job board / flux               | Plateforme / recruteurs                       | Afrique anglophone / international       | Emploi / missions                | XML / JSON                              | Flux public identifié lors de la recherche   | Flux                                | Selon flux                                             | À vérifier                                           | Conditions de réutilisation à vérifier                                                                                                                     | Offres selon feed                                                                                                  | À vérifier                       | Moyen                                                       | À vérifier                  | À vérifier                                               | Oui                            | Non identifié                                                       | À vérifier                             | Moyenne                          | Moyenne             | Couverture anglophone                                       | **Faible pour MVP**                        | 🔴      |                                                                                                                                                                    |
| 28 | **Upwork**                              | Plateforme freelance           | Clients / freelances                          | International                            | Freelance                        | API / plateforme                        | API partenaire                               | API partenaire                      | OAuth / partenariat                                    | Partenariat nécessaire                               | Accès et usages dépendants du programme/API                                                                                                                | Missions selon API disponible                                                                                      | Régulière                        | Très élevé                                                  | Selon conditions            | Selon conditions                                         | Oui                            | Selon API / partenariat                                             | Potentiellement élevé                  | Élevée                           | Élevée              | Freelance international                                     | **Élevée mais hors MVP principal**         | 🟣      |                                                                                                                                                                    |
| 29 | **Fiverr**                              | Plateforme freelance           | Clients / freelances                          | International                            | Freelance                        | HTML / plateforme                       | Pas d'API de recherche pertinente identifiée | Aucune                              | Compte                                                 | À vérifier                                           | Scraping non retenu sans autorisation                                                                                                                      | Données publiques selon pages                                                                                      | Régulière                        | Élevé                                                       | À vérifier                  | À vérifier                                               | Oui                            | Non identifié                                                       | —                                      | Élevée                           | Élevée              | Freelance                                                   | **Faible pour MVP**                        | 🔴      |                                                                                                                                                                    |
| 30 | **Malt**                                | Plateforme freelance           | Clients / freelances                          | Europe / France principalement           | Freelance                        | HTML                                    | Page publique                                | À vérifier                          | Compte selon action                                    | À vérifier                                           | API publique non identifiée                                                                                                                                | Profils / missions selon accès                                                                                     | Régulière                        | Élevé en Europe                                             | À vérifier                  | À vérifier                                               | Oui                            | Non identifié                                                       | —                                      | Moyenne à élevée                 | Élevée              | Marché freelance européen                                   | **Faible pour MVP**                        | 🔴      |                                                                                                                                                                    |
| 31 | **Freelancer.com**                      | Plateforme freelance           | Clients / freelances                          | International                            | Freelance                        | API / plateforme                        | API partenaire                               | API si accès obtenu                 | Clé / compte                                           | Partenariat / accès à vérifier                       | Conditions API à vérifier                                                                                                                                  | Missions / projets selon API                                                                                       | Régulière                        | Élevé                                                       | Selon conditions            | Selon conditions                                         | Oui                            | À vérifier                                                          | À négocier                             | Moyenne à élevée                 | Élevée              | Freelance international                                     | **Moyenne**                                | 🟣      |                                                                                                                                                                    |
| 32 | **France Travail API Offres d'emploi**  | Portail public de l'emploi     | France Travail + partenaires consentants      | France                                   | Emploi généraliste               | REST JSON                               | API officielle                               | API Offres d'emploi                 | Accès / licence selon API                              | Ouvert sous conditions de licence                    | Données de partenaires disponibles uniquement selon consentement ; usage soumis à licence                                                                  | Titre, lieu, entreprise, contrat, secteur, métier, formation, etc.                                                 | Temps réel                       | Très élevé pour France                                      | Selon licence               | Selon licence                                            | Oui                            | À vérifier selon endpoint                                           | Gratuit / conditions de licence        | Moyenne                          | Faible pour Sénégal | Forte couverture France                                     | **Élevée mais hors priorité géographique** | 🔵      | Documentation officielle data.gouv.fr et France Travail.                                                                                                           |
| 33 | **Emploitic**                           | Job board régional             | Recruteurs / plateforme                       | Algérie / Maghreb                        | Emploi généraliste               | HTML / API tierce possible              | Page publique / accès tiers identifié        | À vérifier                          | À déterminer                                           | À vérifier                                           | API tierce ne vaut pas autorisation de la plateforme source                                                                                                | Offres selon accès                                                                                                 | Régulière                        | Élevé au Maghreb                                            | À vérifier                  | À vérifier                                               | Oui                            | Non identifié                                                       | À vérifier                             | Moyenne                          | Moyenne             | Marché algérien                                             | **Moyenne**                                | 🟣      |                                                                                                                                                                    |
| 34 | **Emploi.ma**                           | Job board régional             | Recruteurs / plateforme                       | Maroc                                    | Emploi généraliste               | HTML / API tierce possible              | Page publique / accès tiers identifié        | À vérifier                          | À déterminer                                           | À vérifier                                           | Même prudence concernant les API tierces                                                                                                                   | Offres selon accès                                                                                                 | Régulière                        | Élevé au Maroc                                              | À vérifier                  | À vérifier                                               | Oui                            | Non identifié                                                       | À vérifier                             | Moyenne                          | Moyenne             | Marché marocain                                             | **Moyenne**                                | 🟣      |                                                                                                                                                                    |
| 35 | **Coworkies API**                       | Plateforme emploi / communauté | Entreprises / communauté                      | International / francophone              | Remote / tech / emploi           | REST JSON                               | API                                          | API si disponible                   | Clé                                                    | À vérifier                                           | Conditions d'utilisation à confirmer                                                                                                                       | Offres selon API                                                                                                   | Régulière                        | Moyen                                                       | À vérifier                  | À vérifier                                               | Oui                            | À vérifier                                                          | À vérifier                             | Moyenne                          | Moyenne             | Couverture francophone / remote                             | **Moyenne**                                | 🔵      |                                                                                                                                                                    |
| 36 | **JobBoardly API**                      | Outil de création de job board | Clients de JobBoardly                         | N/A comme source primaire                | Offres hébergées par les clients | REST JSON                               | API                                          | API                                 | Authentification                                       | Dépend du compte client                              | Ce n'est pas une source autonome d'offres pour notre agent                                                                                                 | Offres du job board du client                                                                                      | Dépend du client                 | N/A pour notre objectif                                     | Selon compte                | Selon compte                                             | Selon job board                | Selon compte                                                        | À vérifier                             | Moyenne                          | Moyenne             | Infrastructure plutôt que source d'offres                   | **Faible pour le MVP**                     | 🔴      |                                                                                                                                                                    |
| 37 | **Techmap — Job Postings RSS Feed API** | Agrégateur / feed              | Plusieurs sources                             | International                            | Tech / emploi                    | RSS / JSON via service                  | RSS / API tierce                             | Feed si conditions compatibles      | Token pour service tiers                               | À vérifier                                           | Dépend du fournisseur tiers et des licences des sources                                                                                                    | Offres selon feed                                                                                                  | Régulière                        | Moyen à élevé                                               | À vérifier                  | À vérifier                                               | Oui                            | Non identifié                                                       | Quota / abonnement selon service       | Faible à moyenne                 | Moyenne             | Agrégation tech                                             | **Moyenne**                                | 🟡      |                                                                                                                                                                    |
| 38 | **Ever Jobs**                           | Agrégateur                     | Multiples sources                             | International                            | Emploi généraliste               | REST / GraphQL selon recherche initiale | API                                          | API si officiellement disponible    | À vérifier                                             | À vérifier                                           | Origine et droits des données à clarifier                                                                                                                  | Offres agrégées selon API                                                                                          | À vérifier                       | Potentiellement très élevé                                  | À vérifier                  | À vérifier                                               | Oui selon offre                | À vérifier                                                          | À vérifier                             | Moyenne à élevée                 | Élevée              | Agrégation multi-sources                                    | **Potentiellement très élevée**            | 🟡      |                                                                                                                                                                    |
| 39 | **Dev Global Jobs**                     | Job board spécialisé           | Entreprises / recruteurs                      | International / remote                   | Développement / tech             | API / RSS                               | API ou RSS                                   | API si officiellement confirmée     | Aucune selon recherche initiale                        | À vérifier                                           | Conditions de redistribution à confirmer                                                                                                                   | Titre, entreprise, localisation, description, URL, catégories selon feed                                           | Régulière                        | Moyen                                                       | À vérifier                  | À vérifier                                               | Oui                            | Non identifié                                                       | À vérifier                             | Faible à moyenne                 | Faible à moyenne    | Tech / remote                                               | **Moyenne à élevée**                       | 🟢      |                                                                                                                                                                    |
| 40 | **We Work Remotely**                    | Job board remote               | Entreprises / recruteurs                      | International / remote                   | Remote                           | RSS                                     | RSS public                                   | RSS officiel                        | Aucune                                                 | Autorisé sous conditions d'attribution               | Attribution et liens vers WWR demandés                                                                                                                     | Offres, titre, entreprise, catégorie, URL, contenu selon RSS                                                       | Régulière                        | Élevé                                                       | À vérifier                  | Oui sous conditions                                      | Oui                            | Non identifié                                                       | Gratuit pour feed                      | Faible                           | Faible à moyenne    | Remote international                                        | **Élevée**                                 | 🟢      | Feed RSS officiel public ; WWR demande l'attribution des liens.                                                                                                    |
| 41 | **Remote OK**                           | Job board remote               | Entreprises / recruteurs                      | International / remote                   | Remote                           | JSON / RSS                              | API JSON + RSS                               | JSON API                            | Aucune                                                 | Public sous conditions d'attribution                 | Crédit Remote OK et lien vers l'offre originale demandés pour agrégation/publication                                                                       | Titre, entreprise, localisation, tags, salaire si publié, URL, etc.                                                | Régulière                        | Élevé                                                       | À vérifier selon conditions | Oui sous conditions                                      | Oui                            | Non identifié                                                       | Gratuit                                | Faible                           | Faible à moyenne    | Remote international                                        | **Élevée**                                 | 🟢      | FAQ officielle Remote OK : JSON et RSS publics sans authentification, avec attribution et lien vers l'offre originale.                                             |
| 42 | **Himalayas**                           | Job board remote               | Entreprises / recruteurs                      | International / remote                   | Remote                           | JSON / RSS / MCP                        | API JSON + RSS + MCP                         | API JSON                            | Aucune pour données publiques                          | Public sous conditions d'attribution                 | API publique ; données actualisées quotidiennement ; attribution requise ; restrictions notamment sur soumission à certains tiers                          | Titre, entreprise, localisation, type, salaire, description, restrictions géographiques, timezone, catégories, URL | Quotidienne                      | Élevé                                                       | À vérifier selon usage      | Attribution + restrictions de redistribution             | Oui                            | Pas nécessaire pour MVP ; MCP propose des fonctions supplémentaires | Gratuit pour données publiques         | Faible                           | Faible à moyenne    | API pensée notamment pour outils et agents IA               | **Très élevée**                            | 🟢      | Documentation officielle Himalayas : API JSON, RSS et MCP publics ; attribution et restrictions détaillées.                                                        |
| 43 | **Arbeitnow**                           | Job board / agrégateur         | Entreprises / recruteurs                      | Europe / remote                          | Emploi généraliste / tech        | JSON                                    | API publique                                 | API JSON                            | Aucune                                                 | À vérifier                                           | Couverture principalement européenne ; intérêt limité pour priorité Sénégal/Afrique                                                                        | Offres selon API                                                                                                   | Régulière                        | Moyen                                                       | À vérifier                  | À vérifier                                               | Oui                            | Non identifié                                                       | Gratuit selon recherche initiale       | Faible                           | Faible à moyenne    | Europe / remote                                             | **Faible pour MVP**                        | 🔴      |                                                                                                                                                                    |
| 44 | **AI Dev Jobs**                         | Job board spécialisé           | Entreprises / recruteurs                      | International / remote                   | IA / développement               | REST / MCP                              | API / MCP                                    | API ou MCP après vérification       | Aucune selon recherche initiale                        | À vérifier                                           | Documentation et conditions à confirmer avant intégration                                                                                                  | Offres tech/IA selon API                                                                                           | Régulière                        | Moyen                                                       | À vérifier                  | À vérifier                                               | Oui                            | À vérifier                                                          | À vérifier                             | Moyenne                          | Moyenne             | Spécialisation IA / développement                           | **Moyenne à élevée**                       | 🟢      |                                                                                                                                                                    |

---

# 6. Lecture stratégique du premier inventaire

Le premier inventaire fait apparaître plusieurs familles de sources.

## 6.1 Sources locales prioritaires

Les sources locales sont particulièrement importantes pour le projet car une stratégie reposant uniquement sur les grands job boards internationaux risquerait de mal couvrir le marché sénégalais.

Sources à approfondir :

* EmploiDakar ;
* Senjob ;
* Ligeey ;
* Expat-Dakar Emploi ;
* TrouvezJob ;
* Emploi-jeune.

Leur intérêt stratégique est élevé, mais plusieurs nécessitent encore une **vérification spécifique de leurs conditions d'accès et de réutilisation**.

---

## 6.2 ATS : stratégie importante pour obtenir des offres directement auprès des entreprises

Les ATS représentent une catégorie particulièrement intéressante.

Les offres publiées par une entreprise sur un ATS peuvent être accessibles de manière structurée sans devoir construire un scraper spécifique pour chaque site carrière.

Sources importantes :

* Greenhouse ;
* Lever ;
* Ashby ;
* Workday ;
* Recruitee ;
* Jobvite ;
* iCIMS.

Cependant, il faut distinguer :

> **« l'ATS possède une API »**

de :

> **« notre agent peut rechercher toutes les offres de cet ATS avec cette API »**.

Par exemple, l'API publique Lever est organisée autour du job board d'une entreprise et permet de récupérer ses offres publiées ; elle ne constitue pas un moteur de recherche global de toutes les offres Lever.

La même logique s'applique à Greenhouse et Ashby : l'accès public concerne essentiellement les offres publiées par une organisation donnée.

---

## 6.3 Agrégateurs

Les agrégateurs peuvent fournir rapidement un volume important :

* Adzuna ;
* Jooble ;
* Ever Jobs ;
* Techmap ;
* autres agrégateurs à identifier.

Ils sont intéressants pour augmenter la couverture mais introduisent une question importante :

> **Quelle est la provenance réelle de l'offre et avons-nous le droit de la stocker, de l'afficher et de la redistribuer ?**

Cette question doit être traitée avant l'intégration.

Adzuna constitue un exemple important : son API est accessible, mais ses conditions distinguent notamment la recherche personnelle, la publication d'annonces et l'usage commercial continu, qui peut nécessiter une licence.

---

## 6.4 Remote

Pour la partie internationale/remote, plusieurs sources disposent déjà d'interfaces machine-readable intéressantes :

* We Work Remotely ;
* Remote OK ;
* Himalayas.

We Work Remotely fournit officiellement un RSS public et demande simplement l'attribution des liens.

Remote OK fournit officiellement des flux JSON et RSS publics sans authentification et demande l'attribution ainsi qu'un lien vers l'offre originale.

Himalayas va encore plus loin avec :

* JSON API ;
* RSS ;
* MCP.

Son API publique permet de parcourir les offres avec pagination et filtres, sans clé API. La plateforme précise également les conditions d'attribution et certaines restrictions de redistribution.

---

# 7. Première segmentation stratégique

À ce stade, le tableau permet de dégager une première segmentation.

### 🟢 Connecteurs à étudier

* Greenhouse
* Lever
* Ashby
* Jooble
* We Work Remotely
* Remote OK
* Himalayas
* Dev Global Jobs
* AI Dev Jobs
* éventuellement Senjob après clarification des conditions

### 🟣 Partenariat / autorisation à obtenir

* Senjob
* Recruitee
* Jobvite
* iCIMS
* LinkedIn
* Devex
* Adzuna pour usage commercial continu selon le cas
* Upwork
* Freelancer.com
* Emploitic
* Emploi.ma

### 🟡 À surveiller / vérifier

* EmploiDakar
* Ligeey
* Expat-Dakar
* TrouvezJob
* Emploi-jeune
* Workday
* ReliefWeb
* UN Careers
* UN Talent
* Techmap
* Ever Jobs

### 🔵 À étudier plus tard

* Coworkies
* France Travail
* autres sources pertinentes mais moins prioritaires géographiquement

### 🔴 À exclure du MVP

* DirectEmploi
* BrighterMonday
* Jobberman
* Fuzu
* ProGigFinder
* Fiverr
* Malt
* Indeed Job Sync API pour le besoin de recherche actuel
* Glassdoor
* JobBoardly
* Arbeitnow

**Attention :** `🔴 À exclure` signifie **exclure du périmètre actuel du MVP**, et non nécessairement « plateforme mauvaise » ou « plateforme inutilisable dans tous les contextes ».

---

# 8. Point particulièrement important pour le projet

Le tableau fait apparaître une distinction qui devra probablement être conservée dans l'architecture du Job Agent :

```text
SOURCE
   ↓
MÉTHODE D'ACCÈS
   ↓
AUTORISATION
   ↓
CAPACITÉS RÉELLES
   ↓
DONNÉES RÉCUPÉRABLES
   ↓
STOCKAGE
   ↓
AFFICHAGE
   ↓
CANDIDATURE
```

La présence d'une API ne signifie donc pas automatiquement :

```text
API
=
droit de tout récupérer
=
droit de tout stocker
=
droit de tout republier
=
droit de candidater automatiquement
```

Ces dimensions doivent rester indépendantes.

---

# 9. Priorité géographique

Le projet conserve l'ordre de priorité suivant :

1. Dakar ;
2. Sénégal ;
3. Afrique de l'Ouest ;
4. Afrique ;
5. International ;
6. Remote international.

Cette priorité doit être prise en compte lors de l'évaluation de la valeur d'une source.

Une source internationale contenant 100 000 offres n'est donc pas automatiquement plus stratégique qu'une source sénégalaise contenant beaucoup moins d'offres.

---

# 10. Prochaine étape

Ce document constitue maintenant le **premier inventaire stratégique réel** du projet.

Il ne doit pas encore être considéré comme une validation définitive de toutes les sources.

La prochaine étape consiste à effectuer une **vérification primaire approfondie**, en priorité sur :

### Priorité 1 — Sénégal / Afrique de l'Ouest

* EmploiDakar ;
* Senjob ;
* Ligeey ;
* Expat-Dakar ;
* TrouvezJob ;
* Emploi-jeune.

### Priorité 2 — connecteurs machine-readable

* Greenhouse ;
* Lever ;
* Ashby ;
* Jooble ;
* We Work Remotely ;
* Remote OK ;
* Himalayas.

### Priorité 3 — agrégateurs

* Adzuna ;
* Ever Jobs ;
* Techmap.

### Priorité 4 — ATS complémentaires

* Workday ;
* Recruitee ;
* Jobvite ;
* iCIMS.

Après cette vérification, les sources ayant réellement passé le filtre pourront être transférées vers :

`connectors.md`

---

# 11. Historique

### V2 — Premier inventaire renseigné

**Origine principale :**

* recherche initiale multi-source ;
* recherche Perplexity ;
* vérifications ponctuelles auprès de documentation officielle.

**Nombre de sources recensées : 44**

**Statut :**

> Inventaire stratégique initial — vérification primaire encore en cours.

**Règle :**

Aucune source ne doit être considérée comme définitivement intégrée au système tant que ses conditions d'accès, ses droits d'utilisation et son mécanisme technique n'ont pas été vérifiés.

---

# 12. Règle directrice

> **Une source est sélectionnée non pas parce qu'elle est populaire ou techniquement accessible, mais parce qu'elle apporte une valeur réelle au Job Agent et qu'il existe une méthode d'accès compatible avec les conditions d'utilisation du projet.**
