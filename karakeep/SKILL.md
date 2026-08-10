---
name: karakeep
description: Rechercher, lire, ajouter, enrichir et organiser des bookmarks, listes et tags dans Karakeep via le serveur MCP karakeep. Utiliser pour toute demande concernant Karakeep, notamment l’ajout d’URL ou de notes, la recherche avancée, la génération de résumés et de tags, l’archivage, les favoris et la gestion de listes ou de tags.
---

# Karakeep

Utiliser prioritairement et directement les outils fournis par le serveur MCP
`karakeep`.

Ne pas appeler l’API Karakeep, le CLI Karakeep ou un script Python lorsque le
MCP fournit l’opération nécessaire.

Si le serveur ou les outils MCP Karakeep ne sont pas disponibles :

1. ne pas tenter de les remplacer silencieusement par un autre mécanisme ;
2. demander à l’utilisateur de vérifier `/mcp` et la configuration du serveur ;
3. n’utiliser une solution de secours que si l’utilisateur l’autorise
   explicitement.

Ne **JAMAIS** demander, afficher ou journaliser la clé API Karakeep.

Dans Karakeep, un bookmark peut être un lien (URL), un media (ex: une image ou un pdf) ou un texte (une note rapide, un paragraphe copié, etc). Il peut être associé à des tags et à des listes, et enrichis de métadonnées comme un résumé ou des notes.

## Principes généraux

Avant toute opération :

1. déterminer si la demande est une lecture ou une modification ;
2. identifier précisément les bookmarks, listes ou tags concernés ;
3. consulter leur état actuel lorsque cela évite une modification incorrecte ;
4. utiliser seulement les paramètres réellement exposés par les outils MCP ;
5. vérifier le résultat retourné avant d’annoncer un succès.

Effectuer directement les lectures demandées.

Pour une écriture explicitement demandée, effectuer l’opération dans le périmètre
indiqué. Demander une précision si la cible ou l’effet attendu reste ambigu.

Ne jamais supprimer un bookmark, une liste ou un tag sans demande explicite.

## Recherche

Utiliser `search-bookmarks` pour rechercher des bookmarks.

Pour une recherche simple, transmettre les termes utiles sans complexifier
inutilement la requête.

Pour une recherche utilisant des filtres, des dates, des tags, des listes ou des
opérateurs booléens, lire `references/search-syntax.md` avant de construire la
requête.

Une recherche sur `url:` est une recherche par correspondance et ne constitue pas
toujours une vérification exacte de l’URL.

Utiliser `get-bookmark` pour récupérer les métadonnées d’un résultat précis.

Utiliser `get-bookmark-content` lorsque la demande nécessite le contenu archivé
ou textuel du bookmark, et pas seulement ses métadonnées.

## Ajout d’une ressource

Lorsqu’un utilisateur demande d’ajouter une URL ou une ressource :

1. identifier le type de ressource ;
2. obtenir suffisamment de contenu pour comprendre réellement la ressource ;
3. produire un résumé fidèle si le contenu permet d'en produire un utile ;
4. déterminer des tags pertinents avec le skill `tagging` ;
5. créer le bookmark avec `create-bookmark` ;
6. ajouter les informations supplémentaires avec `update-bookmark` uniquement
   lorsque l’outil et son schéma le permettent ;
7. attacher les tags définitifs avec `attach-tag-to-bookmark`, qu’ils existent déjà ou qu’ils doivent être créés automatiquement ;
8. vérifier le résultat final.
9. informer succinctement l'utilisateur du résultat.

Préférer fournir dès la création le titre, la note ou le résumé lorsque ces
champs sont acceptés par `create-bookmark`. Sinon, utiliser `update-bookmark`
après la création.

Ne jamais inventer un paramètre que le schéma MCP courant n’expose pas.
Ne pas choisir les tags uniquement à partir du titre lorsqu'un contenu plus complet peut être obtenu.

## Bookmark existant et idempotence

La création d’une URL déjà présente peut retourner le bookmark existant.

Si le résultat indique que le bookmark existait déjà :

1. ne pas annoncer qu’un nouveau bookmark a été créé ;
2. ne pas remplacer automatiquement son titre, son résumé, sa note ou ses tags ;
3. informer l’utilisateur que la ressource était déjà enregistrée ;
4. modifier le bookmark seulement si la demande autorise clairement
   l’enrichissement d’un élément existant.

Ne pas utiliser une recherche approximative comme preuve qu’une URL exacte
existe déjà.

## Résumés

Produire un résumé en markdown à partir du contenu réellement consulté.

Le résumé ne doit pas être :

- une simple reformulation du titre ;
- une description générique de la ressource ;
- une explication du travail effectué par l’agent ;
- une extrapolation fondée uniquement sur des connaissances générales.

Adapter la longueur du résumé à la richesse de la ressource. Conserver les idées,
arguments, résultats, nuances et conclusions importants.

Ne pas remplacer un résumé existant sans autorisation explicite.

## Pages Web et articles

Pour enrichir une page Web :

1. consulter son contenu principal ;
2. ignorer autant que possible la navigation, la publicité et les éléments
   périphériques ;
3. produire un résumé fidèle ;
4. utiliser le skill `tagging` à partir du contenu, et non du seul titre ;
5. créer ou enrichir le bookmark selon les règles d’idempotence.

Ne pas utiliser les métadonnées seules lorsqu'il est possible de consulter le contenu principal.
Si le contenu n’est pas accessible, enregistrer l’URL sans prétendre avoir analysé la page.

## Vidéos YouTube

Pour une vidéo YouTube :

1. utiliser le skill `youtube` pour obtenir les métadonnées et la transcription ;
2. produire un résumé à partir de cette transcription conformément aux règles de la skill `youtube` ;
3. enregistrer le résumé dans un fichier temporaire Markdown ;
4. utiliser le skill `tagging` à partir du contenu réel de la vidéo ;
5. créer ou enrichir le bookmark avec les outils MCP Karakeep ;
6. vérifier les informations effectivement enregistrées.

Ne pas résumer une vidéo uniquement depuis son titre ou sa description lorsque
la transcription est disponible.

### Fichiers de transcription

Lors du traitement de vidéos YouTube :

1. faire écrire le JSON de chaque extraction dans un fichier temporaire distinct avec `youtube_transcript.py --output` ;
2. lire le JSON depuis ce fichier sans dépendre de son affichage complet dans la sortie standard ;
3. chaque vidéo ne doit normalement nécessiter qu'un seul appel à `youtube_transcript.py` ;
4. supprimer les fichiers temporaires lorsqu'ils ne sont plus nécessaires.

Une nouvelle extraction n'est justifiée que si l'appel précédent a réellement échoué et qu'une nouvelle tentative est prévue par les règles de la skill `youtube`.

## Tags

Pour générer ou attacher des tags :

1. utiliser le skill `tagging` à partir du contenu réel de la ressource ;
2. normaliser les noms conformément aux conventions de tagging de l’utilisateur ;
3. utiliser `get-tags` lorsque cela aide à réutiliser la taxonomie existante et à éviter des variantes inutilement proches ;
4. utiliser `attach-tag-to-bookmark` avec les noms définitifs des tags.

`attach-tag-to-bookmark` accepte directement les noms de tags, y compris s'ils n'existent pas encore dans Karakeep (ils s'y créent automatiquement).

Préférer les tags existants lorsqu’ils expriment correctement le concept. Créer un nouveau tag uniquement lorsqu’aucun tag existant ne convient.

Utiliser `detach-tag-from-bookmark` seulement lorsque le retrait est demandé.

Ne pas renommer ou supprimer un tag global simplement pour répondre à une demande portant sur un bookmark.

## Listes

Utiliser :

- `get-lists` pour identifier les listes disponibles ;
- `get-list` pour consulter une liste précise ;
- `create-list` pour créer une liste ;
- `update-list` pour modifier ses propriétés ;
- `add-bookmark-to-list` et `remove-bookmark-from-list` pour gérer son contenu.

Vérifier le type de liste avant modification. Une liste intelligente repose sur
une requête et ne doit pas être traitée automatiquement comme une liste manuelle.

Lors de la suppression d’une liste, tenir compte du fait que ses listes enfants
peuvent conserver une référence vers le parent supprimé.

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
- le titre du bookmark lorsqu’il est disponible ;
- les listes et tags effectivement appliqués ;
- les éléments ignorés ou non pris en charge ;
- toute opération partiellement réussie.

Ne pas recopier le résumé complet sauf si l’utilisateur le demande.

Si l’utilisateur demande explicitement un « mode debug », fournir les détails
techniques non sensibles utiles à la compréhension de l’opération, comme les
outils appelés, leurs paramètres non secrets, les fichiers consultés et les
statuts retournés.

Ne jamais afficher les clés API, variables d’environnement secrètes, en-têtes
d’autorisation, jetons, cookies ou autres identifiants sensibles, même en mode
debug.