# Fondation multi-utilisateur et préparation de la base (Phase 1.2.1)

## Contexte

La phase 1.2.1 prépare les fondations de la base de données pour supporter
plusieurs utilisateurs, sans casser les fonctionnalités existantes du MVP
(un seul utilisateur, sans authentification opérationnelle).

Le moteur de matching, le pipeline de recherche et les repositories
fonctionnels existants restent inchangés sur leur logique métier.

## Tables créées par la migration 0002

### `users`

Table de fondation uniquement. Aucun champ de credential n'est introduit :
le hachage des mots de passe et la génération JWT sont reportés aux phases
ultérieures.

- `id` : identifiant technique (texte), clé primaire.
- `email` : adresse normalisée avant stockage, unique.
- `is_active` : booléen, activé par défaut.
- `created_at` / `updated_at` : horodatages.

### `auth_sessions`

Structure future, purement préparatoire :

- `id`, `user_id` (clé étrangère vers `users.id`, nommée
  `fk_auth_sessions_user_id_users`), `token_hash` (jamais de refresh token en
  clair), `created_at`, `expires_at`, `revoked_at`, `last_used_at`.
- Index sur `user_id`, sur `token_hash` et sur `expires_at`.

Aucun mécanisme JWT, rotation ou validation n'est implémenté dans cette phase.

### `user_settings`

Évolution vers la clé logique `(user_id, setting_key)` :

- `user_id` : référence vers `users.id`, nullable pour les données historiques.
- `setting_key` : `profile` ou `preferences` (contrainte de vérification).
- `payload_json` : payload sérialisé.
- `updated_at`.
- Clé primaire composite `(user_id, setting_key)`.

Plusieurs utilisateurs peuvent donc définir la même clé logique
(`profile` ou `preferences`).

### `shortlist_entries`

Évolution vers des clés uniques par propriétaire :

- `user_id` : référence vers `users.id`, nullable pour les données historiques.
- `identity_key`, `source_identity`, `canonical_identity`, `offer_url`,
  `source_slug` : identités normalisées, uniques **par utilisateur**.
- `offer_json`, `status`, `created_at`, `updated_at`.

Deux utilisateurs peuvent sauvegarder la même offre ; un même utilisateur ne
peut pas créer deux sauvegardes du même identité pour ce propriétaire.

## Migration Alembic 0002

- Revision `0002`, base `0001`.
- Fonctionne sur une base vierge et sur une base historique.
- Reconstruit les tables concernées (SQLite ne permettant pas une évolution
  directe des clés) en table temporaire, copie des données, remplacement.
- `downgrade` : restaure les formes précédentes. Il refuse de s'exécuter
  lorsque des données utilisateurs ou des données attribuées à un utilisateur
  seraient perdues.

## Stratégie de conservation des données historiques

Les données existantes (écrites avant l'arrivée des utilisateurs) conservent
`user_id = NULL` : aucune attribution automatique n'est faite au premier
utilisateur inscrit.

Le rattachement ultérieur au propriétaire initial doit passer par une procédure
contrôlée (provisionnement explicite), jamais automatique.

## Provisionnement futur du propriétaire initial

Les phases ultérieures devront gérer l'inscription et la session ; la migration
0002 autorise un `user_id` nullable afin de supporter ce report sans perte.

## Limites connues

- Le `user_settings` et `shortlist_entries` repositent encore une portée
  "non attribuée" (`user_id IS NULL`) correspondant au MVP mono-utilisateur
  actuel.
- Les catalogues globaux (`job_offers`), suggestions, candidatures, empreintes
  et gestion du cycle de vie des offres arrivent dans les phases ultérieures.

## Tests réalisés

- Nouvelle base : exécution de la migration jusqu'à `head`, présence et forme
  des tables, colonnes, clés et index attendus.
- Base historique : adoption de `0001`, conservation des données, aucune
  attribution arbitraire.
- Contraintes multi-utilisateurs : unicité d'email, unicité composite des
  clés par propriétaire, partage d'une même offre entre deux utilisateurs.
- Intégrité référentielle : session liée à un utilisateur existant, refus de
  référence invalide, comportement de suppression.
- Downgrade : restauration de la forme précédente, refus explicite en cas de
  données utilisateurs.
- Non-régression : moteur de matching, pipeline, repositories, APIs inchangés
  sur leur logique métier.

## Procédure de migration sur une base temporaire

```bash
# base vierge
alembic upgrade head

# base historique (schéma 0001 + données)
alembic upgrade 0001
# ... données existantes ...
alembic upgrade head
alembic downgrade 0001
```
