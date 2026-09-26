# Task 5 — Vérification documentaire et opérationnelle des connecteurs

**Date de vérification documentaire : 2026-09-26**  
**Périmètre :** RemoteOK, Greenhouse Job Board API et Lever Postings API.  
**Méthode :** examen des documents du dépôt et des pages officielles liées ci-dessous. Les endpoints API n'ont pas été appelés directement pendant cette vérification. Les exemples et tests locaux du dépôt sont des fixtures, pas des observations de service en direct.

## Résumé exécutif

Les pages officielles consultées permettent maintenant d'identifier les endpoints de lecture RemoteOK et Greenhouse et de préciser les contrats de lecture RemoteOK, Greenhouse et Lever. Elles ne suffisent pas à établir toutes les conditions de réutilisation des offres par un agrégateur tiers, notamment stockage, durée de conservation et redistribution. Aucune source n'a été testée contre son API réelle.

Le code demeure un prototype de collecte, pas une intégration opérationnelle. Greenhouse a une frontière configurable sans parseur de production. Le normalizer Lever n'utilise qu'une partie des champs publiés officiellement. Le backend n'instancie aucun des trois connecteurs et les routes de recherche restent en `501 Not Implemented`.

## 1. Documents et sources consultés

### Documents du dépôt

- `AGENTS.md`
- `ENGINE-IMPLEMENTATION-SPEC.md`
- `docs/architecture/project-context.md`
- `docs/architecture/connectors.md`
- `docs/architecture/connector-implementation-guide.md`
- `docs/architecture/search-criteria-and-source-capabilities.md`
- `docs/architecture/job-offer-model.md`
- `docs/implementation/connector-implementation-plan.md`
- `docs/research/research-protocol.md`
- `docs/research/source-masterV4.md`
- Code et tests sous `backend/app/connectors/`, `backend/app/core/`, `backend/app/services/` et `backend/tests/`.

Les documents de référence exigent de séparer accès technique et autorisation, de vérifier les conditions auprès de sources primaires, et de ne pas attribuer le statut opérationnel sur la seule base de tests simulés.

### Sources officielles consultées

- Remote OK : [FAQ — feeds JSON/RSS et agrégateurs](https://remoteok.com/faq), [Terms of Service](https://remoteok.com/legal).
- Greenhouse : [Job Board API](https://docs.greenhouse.io/job-board.html), [présentation des APIs](https://www.greenhouse.com/api), [Master Subscription Agreement](https://www.greenhouse.com/master-subscription-agreement), [Legal Center](https://www.greenhouse.com/legal).
- Lever : [Postings API — documentation officielle du dépôt `lever/postings-api`](https://github.com/lever/postings-api), [FAQ API Lever](https://hire.lever.co/developer/support), [conditions de service Lever](https://www.lever.co/legal/terms-of-service).

Les pages peuvent évoluer. Les constats ci-dessous sont datés et ne remplacent pas une vérification avant mise en production.

## 2. RemoteOK

### Preuves documentaires

La FAQ officielle indique le feed JSON exact `https://remoteok.com/api`, le feed RSS, l'absence d'authentification pour ces feeds, et les paramètres de filtre `tag` et `tags` avec des exemples. Elle demande aux personnes qui construisent un agrégateur ou partagent le feed publiquement de créditer Remote OK et de créer un lien vers chaque offre originale. Les conditions officielles demandent aussi un lien vers Remote OK sur la page ou l'écran applicatif utilisant les données de son API ou de son site.

La FAQ consultée ne documente pas le schéma/enveloppe JSON, la pagination, un quota de requêtes, un comportement d'erreur API, une durée de rétention, ni une autorisation générale de stockage ou de redistribution commerciale. Les conditions de stockage et de réutilisation au-delà des indications d'attribution sont donc **non vérifiées**. La présence d'une consigne pour les agrégateurs ne précise pas toutes les permissions d'exploitation.

### Confrontation au code

- `RemoteOKConnector` exige toujours l'injection d'un endpoint ; il ne possède pas de valeur par défaut. La valeur officielle est maintenant documentée, mais le backend ne configure pas le connecteur.
- Le connecteur ne transmet aucun paramètre. Il n'exploite donc pas les filtres `tag`/`tags` documentés par Remote OK. C'est prudent : la correspondance entre les critères génériques et ces paramètres de tags n'est pas définie dans le code ou les documents du projet.
- Il suppose une réponse JSON de type liste d'objets. Cette hypothèse est exercée par des fixtures uniquement ; elle n'a pas été confirmée par un appel au feed et n'est pas donnée dans la FAQ.
- Le normalizer mappe les champs observés dans les documents du projet, mais ces noms de champs ne sont pas confirmés par la FAQ officielle consultée. La propriété `remote` reste `None`, ce qui évite de déduire l'éligibilité d'une offre depuis le périmètre général de Remote OK.
- La provenance contient les exigences d'attribution et de lien comme métadonnées. Le backend actuel n'affiche pas les offres et ne réalise pas les liens d'attribution. La présence de ces drapeaux ne démontre donc pas que l'exigence d'affichage est satisfaite.
- Les retries communs sont bornés ; cependant, Remote OK ne publie pas de quota dans la FAQ consultée. Le respect d'une limite non publiée ne peut pas être attesté ici.

### Conditions et inconnues

| Sujet | Résultat |
|---|---|
| Endpoint et méthode | `GET https://remoteok.com/api` documenté dans la FAQ. |
| Authentification | La FAQ dit que les feeds ne nécessitent pas d'authentification. |
| Filtres | `tag` et `tags` documentés ; aucune adaptation des critères génériques n'est décidée. |
| Format / champs / enveloppe | Endpoint JSON documenté ; schéma détaillé et enveloppe non vérifiés par les pages consultées. |
| Pagination / quota / erreurs | Non documentés dans les pages consultées. |
| Agrégation publique | FAQ demande crédit Remote OK et lien par offre ; cela ne tranche pas le stockage ou tous les usages commerciaux. |
| Stockage / rétention / redistribution | Non vérifiés. |
| Appel de l'API pendant Task 5 | Non effectué. |

### Statut proposé : `development`

Le feed et les conditions minimales d'attribution pour un agrégateur sont documentés, mais le schéma réel, le comportement en direct, les limites et les règles de stockage/rétention ne sont pas établis. Le code n'est pas intégré au backend et l'affichage requis n'existe pas.

## 3. Greenhouse

### Preuves documentaires

La documentation officielle du Job Board API donne l'endpoint de liste :

```text
GET https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs
```

Elle indique que les GET Job Board ne requièrent pas d'authentification. La réponse de liste documentée est un objet JSON avec `jobs` et `meta.total`. L'exemple de base expose notamment `id`, `internal_job_id`, `title`, `updated_at`, `requisition_id`, `location.name`, `absolute_url`, `language` et `metadata`. `?content=true` ajoute notamment la description `content`, `departments` et `offices`. Les données présentées sont celles d'un board employeur identifié par son `board_token`.

La section « List jobs » ne documente pas de pagination ni de paramètre de page. La documentation décrit des paramètres `page` pour des endpoints d'éducation distincts ; ils ne peuvent pas être transposés à `/jobs`. Ni limite/quota, ni convention d'erreur du endpoint de liste ne sont spécifiés dans les éléments consultés.

La soumission est une opération différente : `POST https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs/{id}` nécessite une clé API avec Basic Auth. Le présent audit ne recommande ni n'implémente cette opération. La présentation Greenhouse décrit ses APIs comme destinées aux clients et partenaires. Son MSA client stipule que les limites/frais API peuvent être fixés dans l'Order Form et que l'usage par un tiers agissant comme agent ou sur instruction d'un client compte comme usage du client ; il impose aussi une clause de fair use à ce client. Cela ne permet pas de connaître les limites du endpoint public Job Board pour un tiers indépendant, ni de conclure que l'accord d'un employeur suffit à autoriser l'agrégation, le stockage ou la redistribution par Job Agent.

### Confrontation au code

- `GreenhouseConnector` ne construit pas l'endpoint officiel à partir du board token. Il exige un endpoint absolu fourni par l'appelant, un `GreenhouseBoardContext` et un parseur injecté.
- Le parseur actuel des tests est synthétique ; il enveloppe le contenu d'une fixture opaque. Il ne valide pas la réponse officielle `jobs` / `meta`.
- Aucun normalizer Greenhouse n'existe. À la lumière du schéma officiel, un parseur et un normalizer ciblés sont techniquement possibles pour les champs documentés, mais restent à implémenter et tester avant d'en tirer des `JobOffer`.
- La provenance conserve le board token et la configuration, mais une valeur de contexte n'atteste ni l'autorisation de l'employeur ni la compatibilité des conditions applicables.
- Un endpoint arbitraire injecté peut ne pas correspondre au board token enregistré dans le contexte ; le code ne vérifie pas cette relation.

### Conditions et inconnues

| Sujet | Résultat |
|---|---|
| Endpoint/méthode | `GET .../v1/boards/{board_token}/jobs` documenté. |
| Authentification GET | Non requise selon la documentation officielle. |
| Réponse | Enveloppe `jobs`, `meta.total`; champs listés ci-dessus. `content=true` enrichit les entrées. |
| Pagination / quota / erreurs | Pagination et limites du endpoint de liste non documentées dans la page consultée ; erreurs non spécifiées. |
| API de candidature | Endpoint POST séparé, Basic Auth ; hors périmètre. |
| Conditions tiers / stockage / affichage / redistribution | Non vérifiés pour un agrégateur tiers. MSA et accès API client ne suffisent pas à établir ces droits pour Job Agent. |
| Appel de l'API pendant Task 5 | Non effectué ; aucun board employeur précis n'a été fourni. |

### Statut proposé : `access pending`

L'accès de lecture et son schéma sont documentés. Il manque un board explicite, une validation de la configuration de l'endpoint, un parseur/normalizer réel et une clarification des conditions applicables à l'usage tiers envisagé.

## 4. Lever

### Preuves documentaires

La documentation officielle Postings API documente les instances globales et EU. Pour le global :

```text
GET https://api.lever.co/v0/postings/{SITE}?skip={X}&limit={Y}&mode=json
```

La variante EU utilise `https://api.eu.lever.co`. Le SITE nomme le board d'une entreprise. Le endpoint de liste sert les offres publiées. `skip` ignore N résultats et `limit` borne le nombre de résultats renvoyés. Aucun mécanisme de fin de pagination explicite n'est défini dans cette documentation ; elle n'établit pas que page courte ou page vide constitue la convention officielle d'arrêt. Aucun quota de lecture n'a été trouvé. La limite de 2 requêtes/seconde documentée concerne les POST d'application, pas les GET de postings.

Les paramètres documentés comprennent `mode`, `skip`, `limit`, `location`, `commitment`, `team`, `department`, `level` et `group` (ce dernier regroupe la sortie). La documentation exclut la recherche full-text globale. Les critères génériques ne doivent pas être transmis sans adaptation décidée et justifiée.

Les champs documentés pour chaque posting JSON incluent `id`, `text`, `categories`, `country`, plusieurs variantes de description, `hostedUrl`, `applyUrl`, `workplaceType` et `salaryRange` (`currency`, `interval`, `min`, `max`) ainsi que d'autres champs facultatifs. Le détail exact évolue et doit être relu à la prochaine modification du connecteur.

La documentation distingue les GET de postings de la soumission via POST avec clé API. La FAQ Lever décrit le Postings API comme publiquement accessible pour les postings publiés ; la documentation indique aussi que ces offres peuvent être récupérées par des tiers. Ces indications d'accès ne précisent pas à elles seules les droits de stockage, de redistribution, de rétention ou d'usage commercial. Les conditions Lever consultées sont des conditions de service client/commande et ne résolvent pas explicitement ces droits pour un agrégateur tiers indépendant.

### Confrontation au code

- `LeverConnector` exige le SITE, mais construit uniquement l'origine globale `api.lever.co`. La documentation officielle cite aussi l'instance EU ; aucun choix de région n'est représenté dans `LeverSiteContext`.
- Le connecteur envoie `skip`, `limit`, `mode=json`, applique un cap, et rejette une page qui dépasse le `limit` demandé. Il arrête la pagination sur une page vide ou courte. Cette dernière convention est une décision locale, pas une convention de fin attestée par la documentation Lever.
- Le `page_size=20` par défaut n'est pas prescrit par la documentation officielle consultée. Le test d'intégration simule des pages et ne confirme donc ni ce défaut, ni le comportement du serveur.
- Le normalizer utilise `id`, `text` et les catégories `location`, `allLocations`, `commitment`, `team`, `department`. Il ignore plusieurs champs disponibles documentés, dont `country`, les descriptions, `hostedUrl`, `applyUrl`, `workplaceType` et `salaryRange`. Par conséquent, le mapping testé est partiel et ne reflète pas toute l'information disponible.
- Les URLs d'offre et de candidature, les dates, la compensation et le remote restent inconnus dans le modèle produit actuel ; cela évite les inventions, mais perd des champs Lever documentés qu'une évolution ultérieure pourrait mapper explicitement.
- Le code ne fait aucun POST candidature, conformément au périmètre.

### Conditions et inconnues

| Sujet | Résultat |
|---|---|
| Endpoint global/EU | Documentés officiellement. |
| SITE, méthode, mode | SITE requis ; GET ; JSON sélectionnable par `mode=json` ou `Accept`. |
| Paramètres de recherche | Paramètres documentés ci-dessus ; pas de full-text global. |
| Champs de réponse | Liste riche documentée ; le normalizer actuel n'en couvre qu'une partie. |
| Pagination | `skip`/`limit` documentés ; terminaison exacte, limite par défaut/max et page size recommandée non établies. |
| Limites d'accès | Quota GET non trouvé. La limite POST documentée ne concerne pas la collecte. |
| Authentification GET | Le Postings API est décrit comme publiquement accessible pour les offres publiées ; aucune clé n'est utilisée par ce connecteur. |
| Stockage / redistribution / rétention | Non vérifiés pour l'agrégation tierce. |
| Appel de l'API pendant Task 5 | Non effectué ; aucun SITE employeur n'a été sélectionné. |

### Statut proposé : `access pending`

Le contrat de lecture est documenté, mais aucun SITE précis n'est configuré pour le produit. L'instance régionale doit être choisie, la terminaison de pagination et la taille de page doivent être vérifiées, le normalizer est incomplet et les droits d'exploitation tierce ne sont pas établis.

## 5. Tableau comparatif

| Source | Accès lecture documenté | Pagination | Conditions tiers | Écart principal du code | Statut proposé |
|---|---|---|---|---|---|
| RemoteOK | Oui : `GET https://remoteok.com/api`, sans auth selon FAQ ; tag(s) disponibles. | Non documentée dans les pages consultées. | Attribution Remote OK et lien vers chaque offre demandés ; stockage et autres droits inconnus. | Endpoint injecté, enveloppe non confirmée, aucune attribution d'affichage réellement intégrée. | `development` |
| Greenhouse | Oui : GET public par `board_token`, schéma `jobs`/`meta` documenté. | Aucune pagination documentée pour List jobs. | Conditions tiers/stockage/redistribution non établies. | Endpoint et parseur obligatoirement injectés ; parseur de test synthétique ; aucun normalizer. | `access pending` |
| Lever | Oui : GET par SITE sur hôtes global et EU, postings publiés. | `skip`/`limit` documentés, arrêt non précisé. | Postings accessibles/publics ne donnent pas une permission complète de réutilisation. | Origine globale fixe, arrêt court/vide supposé, page size arbitraire, normalizer partiel. | `access pending` |

## 6. État opérationnel et actions préalables

La documentation ne permet pas de déclarer un connecteur opérationnel. Aucun appel live n'a été réalisé : pour RemoteOK, les limites de requête ne sont pas établies ; pour Greenhouse et Lever, le contexte employeur/site et les conditions d'utilisation tierce restent à clarifier. Ce choix respecte la consigne de ne pas effectuer d'appel lorsque les conditions et limites ne sont pas suffisamment vérifiées.

Avant toute collecte réelle ou mise en production :

1. obtenir une décision documentée sur stockage, rétention, affichage et redistribution des données de chaque source, et une autorisation employeur/partenaire si nécessaire ;
2. confirmer l'enveloppe RemoteOK et ses champs depuis sa documentation officielle ou une validation autorisée, puis définir comment les exigences de lien et crédit seront rendues dans l'interface ;
3. sélectionner un board Greenhouse précis, faire correspondre le token à l'endpoint officiel et implémenter un parseur/normalizer à partir du schéma officiel ; ne pas extrapoler la pagination ;
4. sélectionner un SITE et une région Lever, compléter les mappings canoniques uniquement pour les champs désirés et établir une convention de fin de pagination vérifiée ;
5. vérifier les limites GET applicables auprès des sources lorsque les pages consultées ne les spécifient pas ;
6. configurer les connecteurs dans la composition applicative : aujourd'hui `main.py` n'en construit aucun et les routes `/api/search` retournent `501` ; les drapeaux `REMOTEOK_ENABLED` et `LEVER_ENABLED` seuls ne rendent donc pas la recherche active.

## 7. Modifications de code et tests dans Task 5

Aucune modification de code n'a été nécessaire pour produire cet audit documentaire. Aucun test n'a été ajouté. La suite existante a été relancée indépendamment depuis `backend/` : **67 tests passés, 0 échec**. Elle utilise des fixtures et des transports simulés ; elle ne prouve aucun accès réel ni droit d'utilisation.

## 8. Informations explicitement non vérifiées

- Les feeds/APIs n'ont pas été appelés ; aucune réponse live ni disponibilité actuelle n'a été observée.
- Aucune autorisation écrite d'un employeur, board ou plateforme pour Job Agent n'a été examinée.
- Les droits de conservation, cache, stockage, redistribution et usage commercial des offres restent inconnus, sauf les consignes d'attribution/lien RemoteOK mentionnées plus haut.
- Les quotas GET de RemoteOK, Greenhouse et Lever ne sont pas établis dans les documents officiels consultés.
- Le schéma JSON réel actuel du feed RemoteOK n'est pas confirmé par la FAQ officielle.
- La convention d'arrêt de pagination Lever n'est pas publiée dans le document Postings API consulté.
- L'absence de documentation d'une limite ou d'une permission n'est pas une preuve que cette limite ou permission n'existe pas.
