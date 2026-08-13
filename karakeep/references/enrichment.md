# Ajouter ou enrichir une ressource dans Karakeep

Consulter cette référence uniquement pour créer ou enrichir un bookmark, en produire le résumé ou en déterminer les tags.

## Capacités du MCP

`create_bookmark` permet de créer des bookmarks de type `link` ou `text`. Le MCP ne fournit pas d'outil de téléversement pour créer un bookmark `media` ; ne pas prétendre avoir ajouté un fichier lorsque cette capacité n'est pas exposée.

Le titre peut être fourni à la création. Le schéma actuel de `create_bookmark` n'accepte pas la note ni le résumé : utiliser `update_bookmark` après la création pour ces champs.

## Workflow

1. Identifier le type de ressource et obtenir assez de contenu pour la comprendre réellement.
2. Produire un résumé fidèle lorsque le contenu permet d'en produire un utile.
3. Déterminer les tags avec le skill `tagging` à partir du contenu réel.
4. Créer le bookmark avec `create_bookmark`, en fournissant le titre lorsqu'il est disponible.
5. Après obtention de l'identifiant du bookmark et application des règles d'idempotence, effectuer les enrichissements autorisés :
   - ajouter le résumé ou la note avec `update_bookmark` lorsque son schéma le permet ;
   - attacher les tags avec `attach_tag_to_bookmark`.
   Lorsque les deux opérations sont nécessaires, les lancer en parallèle : elles sont indépendantes à ce stade.
6. Attendre et interpréter le résultat de chaque enrichissement, puis vérifier le résumé, les tags et les propriétés explicitement demandées effectivement enregistrés.

Appliquer les règles d'idempotence du skill principal si la ressource existe déjà. Ne jamais inventer un paramètre absent du schéma MCP courant.

## Résumés

Produire le résumé en Markdown à partir du contenu réellement consulté. Adapter sa longueur à la richesse de la ressource et conserver les idées, arguments, résultats, nuances et conclusions importants.

Un résumé ne doit pas être une simple reformulation du titre, une description générique, une explication du travail de l'agent ni une extrapolation fondée sur ses connaissances générales. Ne pas remplacer un résumé existant sans autorisation explicite.

## Pages Web et articles

Consulter le contenu principal en écartant autant que possible la navigation, la publicité et les éléments périphériques. Résumer et taguer ce contenu, pas seulement le titre ou les métadonnées.

Si le contenu n'est pas accessible, l'URL peut être enregistrée, mais ne pas prétendre avoir analysé la page.

## Vidéos YouTube

Utiliser le skill `youtube` pour obtenir le document d'extraction et appliquer ses règles de résumé. Utiliser ensuite le skill `tagging` sur le contenu réel de la vidéo, puis créer ou enrichir le bookmark avec les outils MCP Karakeep.

Le skill `youtube` est responsable du format et du cycle de vie de ses fichiers temporaires. Ne pas reproduire ici une lecture ou une transformation du JSON.
Ne pas résumer une vidéo depuis son seul titre ou sa description lorsqu'une transcription est disponible.

Pour un lot, appliquer la stratégie de lecture définie par le skill `youtube`. Après chaque transcription, préparer une fiche compacte contenant le titre, l'URL canonique, le résumé et les tags ; utiliser ensuite ces fiches pour les opérations MCP parallélisables.

## Adaptation des tags à Karakeep

La taxonomie du skill `tagging` est la source de vérité. Sa sortie canonique contient des tags préfixés par `#` ; avant l'appel MCP :

1. séparer les tags ;
2. retirer exactement le `#` initial de chacun ;
3. construire le tableau `tagsToAttach` ;
4. appeler `attach_tag_to_bookmark` avec ces noms sans `#`.

Exemple : `#tech #ia #llm` devient `["tech", "ia", "llm"]`.

`attach_tag_to_bookmark` accepte les noms qui n'existent pas encore et crée les tags correspondants. Utiliser `get_tags` seulement pour vérifier un nom ou éviter une variante, sans remplacer la taxonomie par l'état existant de
Karakeep.

Utiliser `detach_tag_from_bookmark` seulement si le retrait est demandé. Ne pas renommer ou supprimer un tag global pour répondre à une demande portant sur un bookmark.
