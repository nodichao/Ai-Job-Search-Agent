# Shortlist persistante (Task 9)

## Modèle et responsabilités

La shortlist représente les choix de l'utilisateur, après et indépendamment du
traitement de recherche. `ShortlistEntry` contient un identifiant d'entrée,
un snapshot JSON du seul `JobOffer`, un statut utilisateur, ainsi que les
horodatages `createdAt` et `updatedAt`. Le snapshot conserve l'offre et ses
informations canoniques d'identité et de provenance même si la source ne la
renvoie plus. Scores, dimensions de matching, explication, recommandation et
rang ne sont pas stockés.

`ShortlistService` applique les opérations métier et dépend du protocole
`ShortlistRepository`. `SQLiteShortlistRepository` réalise les opérations
atomiques avec `sqlite3`, sans dépendance ORM supplémentaire. La table est
créée de manière idempotente à la première opération ; aucune migration n'est
nécessaire pour cette première version. Les erreurs SQLite sont converties en
erreur applicative sans transmettre le chemin ou le détail de connexion à
l'API.

Le MVP ne comporte pas d'authentification. Il existe donc une seule shortlist
locale partagée par les appels à cette instance backend. Aucun cloisonnement
utilisateur simulé n'est ajouté.

## Statuts

- `SAVED` : sauvegardée, pas encore examinée (statut initial).
- `INTERESTED` : l'utilisateur indique son intérêt.
- `APPLYING` : candidature en préparation.
- `APPLIED` : l'utilisateur déclare avoir postulé ; ce statut n'est pas une
  preuve et ne déclenche aucune candidature.
- `REJECTED` : l'utilisateur indique un refus ou écarte l'offre.
- `ARCHIVED` : l'utilisateur archive l'entrée.

Tous les statuts peuvent être définis via `PATCH`; aucune transition
automatique n'est appliquée.

## API REST

L'ajout accepte directement un `JobOffer` canonique, tel qu'un objet de
`results` renvoyé par `POST /api/search`.

| Méthode et route | Résultat |
|---|---|
| `POST /api/shortlist` | Crée une entrée `SAVED` et renvoie `201`. |
| `GET /api/shortlist` | Liste les entrées, les plus récentes en premier. |
| `GET /api/shortlist/{id}` | Renvoie une entrée ou `404`. |
| `PATCH /api/shortlist/{id}` | Accepte `{"status":"INTERESTED"}` ou un autre statut déclaré ; `404` si absente, `422` si valeur invalide. |
| `DELETE /api/shortlist/{id}` | Supprime l'entrée et renvoie `204`, ou `404` si absente. |

Les erreurs de stockage renvoient `503` avec un message générique.

## Identité et doublons

Le titre seul n'est jamais utilisé comme identité. L'ordre de préférence est
`source.name + identity.sourceId`, puis `identity.offerUrl`, puis
`source.name + identity.slug`, puis `source.name + identity.id`. Les clés
secondaires source-ID, identifiant canonique, URL et slug disponibles sont
aussi protégées par des contraintes d'unicité SQLite. L'URL est normalisée sur le schéma et l'hôte,
ses paramètres de requête sont triés et son fragment est ignoré.

Une deuxième sauvegarde de la même identité renvoie `409 Conflict`; elle ne
crée pas une autre entrée et ne réinitialise pas le statut existant. Une offre
sans source-ID, URL d'offre, slug ou identifiant canonique est rejetée en
`422`. Les conflits uniques sont garantis en base dans une transaction
`BEGIN IMMEDIATE`, y compris lorsque deux ajouts arrivent en concurrence.

## Persistance et limites

Le dépôt utilise `DATABASE_URL`; le format pris en charge pour cette
implémentation est un chemin SQLite fichier, par exemple
`sqlite:///./job_agent.db`. Le chemin relatif est résolu depuis le répertoire
de travail du backend. Les URLs de base distante et SQLite `:memory:` ne sont
pas prises en charge car la shortlist doit survivre aux redémarrages.

La sauvegarde dépend des permissions d'écriture du chemin configuré. Les
tests utilisent des bases temporaires. Le backend n'a pas d'authentification,
de séparation multi-utilisateur, de synchronisation entre instances ou de
migrations versionnées. `APPLIED` reste une déclaration de l'utilisateur ;
aucun système de candidature, notification ou suivi externe n'est déclenché.
