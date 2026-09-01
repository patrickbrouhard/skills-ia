---
name: karakeep
description: Rechercher, lire, ajouter, enrichir et organiser des bookmarks, listes et tags dans Karakeep via le serveur MCP karakeep. Utiliser pour toute demande concernant Karakeep, notamment l’ajout d’URL ou de notes, la recherche avancée, la génération de résumés et de tags, l’archivage, les favoris et la gestion de listes ou de tags.
---

# Karakeep

Utiliser prioritairement et directement les outils fournis par le serveur MCP `karakeep`.

Ne pas appeler l’API Karakeep, le CLI Karakeep ou un script Python lorsque le MCP fournit l’opération nécessaire.

Si le serveur ou les outils MCP Karakeep ne sont pas disponibles :

1. ne pas tenter de les remplacer silencieusement par un autre mécanisme ;
2. demander à l’utilisateur de vérifier `/mcp` et la configuration du serveur ;
3. n’utiliser une solution de secours que si l’utilisateur l’autorise explicitement.

Ne **JAMAIS** demander, afficher ou journaliser la clé API Karakeep.

## Principes généraux

Avant toute opération :

1. déterminer si la demande est une lecture ou une modification ;
2. identifier précisément les bookmarks, listes ou tags concernés ;
3. consulter leur état actuel lorsque cela évite une modification incorrecte ;
4. utiliser seulement les paramètres réellement exposés par les outils MCP ;
5. vérifier le résultat retourné avant d’annoncer un succès.

Effectuer directement les lectures demandées.

Pour une écriture explicitement demandée, effectuer l’opération dans le périmètre indiqué. Demander une précision si la cible ou l’effet attendu reste ambigu.
Ne jamais supprimer un bookmark, une liste ou un tag sans demande explicite.

## Chargement conditionnel

- Pour créer ou enrichir un bookmark, produire son résumé ou déterminer ses tags, lire `references/enrichment.md` avant l'opération.
- Pour une recherche avec des filtres, dates, tags, listes ou opérateurs booléens, lire `references/search-syntax.md` avant de construire la requête.

Ne pas charger ces références pour une opération qui n'en a pas besoin.

## Recherche

Utiliser `search_bookmarks` pour rechercher des bookmarks.
Pour une recherche simple, transmettre les termes utiles sans complexifier inutilement la requête.
Pour une recherche exhaustive, suivre chaque `nextCursor` jusqu'à l'absence de page suivante.
Exploiter directement les champs présents dans les résultats de recherche ; ne pas appeler `get_bookmark` pour chaque résultat si ces champs suffisent.
Une recherche sur `url:` est une recherche par correspondance et ne constitue pas toujours une vérification exacte de l’URL.
Utiliser `get_bookmark` pour récupérer les métadonnées d’un résultat précis.
Utiliser `get_bookmark_content` lorsque la demande nécessite le contenu archivé ou textuel du bookmark, et pas seulement ses métadonnées.

## Ajout et enrichissement

Appliquer `references/enrichment.md`, puis les règles d'idempotence ci-dessous.

## Bookmark existant et idempotence

La création d’une URL déjà présente peut retourner le bookmark existant.

Si le résultat indique que le bookmark existait déjà :

1. ne pas annoncer qu’un nouveau bookmark a été créé ;
2. ne pas remplacer automatiquement son titre, son résumé, sa note ou ses tags ;
3. informer l’utilisateur que la ressource était déjà enregistrée ;
4. modifier le bookmark seulement si la demande autorise clairement l’enrichissement d’un élément existant.

Ne pas utiliser une recherche approximative comme preuve qu’une URL exacte existe déjà.

## Listes

Utiliser :

- `get_lists` pour identifier les listes disponibles ;
- `get_list` pour consulter une liste précise ;
- `get_list_bookmarks` pour énumérer les bookmarks d’une liste et vérifier son contenu ;
- `get_bookmark_lists` pour vérifier les listes auxquelles appartient un bookmark ;
- `create_list` pour créer une liste ;
- `update_list` pour modifier ses propriétés ;
- `add_bookmark_to_list` et `remove_bookmark_from_list` pour gérer son contenu.

Vérifier le type de liste avant modification. Une liste intelligente repose sur une requête et ne doit pas être traitée automatiquement comme une liste manuelle.

Lors de la suppression d’une liste avec `delete_list`, ses bookmarks ne sont pas supprimés et ses listes enfants deviennent des listes racines : leur `parentId` est mis à `null`. Si cet aplatissement n’est pas souhaité, déplacer ou rattacher les listes enfants avant la suppression.

## Modifications et suppressions

Avant une modification importante :

1. lire l’état actuel de la ressource ;
2. distinguer les champs à conserver de ceux à modifier ;
3. limiter l’écriture aux champs explicitement concernés ;
4. vérifier le résultat.

Avant une suppression :

1. résoudre l’identifiant exact ;
2. rappeler brièvement l’objet qui sera supprimé si une ambiguïté subsiste ;
3. utiliser l’outil de suppression seulement après une demande explicite ;
4. ne pas répéter automatiquement l’opération si son résultat est incertain.

## Erreurs et opérations partielles

Toujours interpréter le résultat des outils MCP.

En cas d’échec :

- distinguer une lecture échouée d’une écriture échouée ;
- distinguer un échec complet d’une opération partiellement réussie ;
- indiquer les éléments réellement créés ou modifiés ;
- ne pas relancer une écriture lorsque son état final est incertain ;
- proposer une vérification en lecture avant une nouvelle tentative.

## Réponse à l’utilisateur

Après une opération, indiquer succinctement :

- ce qui a été trouvé, créé ou modifié ;
- pour chaque bookmark concerné, son titre lorsqu’il est disponible, l’action effectuée et les tags effectivement appliqués ;
- les listes créées ou modifiées et, lorsqu’un rattachement multiple était demandé, le nombre de bookmarks effectivement présents ;
- les éléments ignorés ou non pris en charge, avec une raison concise ;
- toute opération partiellement réussie.

Pour un lot, ne jamais remplacer ce détail par un simple total global. Fournir une ligne par bookmark avec son titre, son résultat, ses tags et les propriétés explicitement demandées, puis éventuellement un total récapitulatif.

Si l’utilisateur demande explicitement un « mode debug », fournir les détails techniques non sensibles utiles à la compréhension de l’opération, comme les outils appelés, leurs paramètres non secrets, les fichiers consultés et les statuts retournés.

Ne jamais afficher les clés API, variables d’environnement secrètes, en-têtes d’autorisation, jetons, cookies ou autres identifiants sensibles, même en mode debug.
