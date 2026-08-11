# Prompt pour résumer une vidéo YouTube à partir de sa transcription

Ton travail consiste à produire, au format Markdown, un résumé clair, fidèle et suffisamment synthétique du contenu d’une vidéo YouTube à partir de sa transcription.

Ne formule aucun commentaire sur ton travail et n'ajoute aucune information, interprétation ou recommandation absente de la vidéo.

La transcription est souvent générée automatiquement par YouTube et peut contenir des erreurs, des omissions ou des passages incompréhensibles. Utilise le contexte pour comprendre le sens lorsqu'il est raisonnablement identifiable, mais ne transforme jamais une reconstruction incertaine en information certaine.

## Principes

* Identifie le sujet, l’idée centrale et les conclusions principales.
* Conserve les arguments, exemples, chiffres et nuances réellement utiles.
* Supprime les répétitions, digressions, éléments promotionnels et détails secondaires.
* N’ajoute aucune information absente de la vidéo.
* Regroupe les idées par thèmes, arguments ou étapes du raisonnement plutôt que minute par minute.
* Hiérarchise les informations : toutes les idées de la vidéo ne méritent pas le même niveau de détail.
* Plus la vidéo est longue ou dense, plus le résumé doit gagner en structure et en hiérarchie — pas simplement en longueur.
* Le résumé doit permettre de comprendre rapidement le contenu sans reproduire la majorité des informations de la vidéo.
* Les sections proposées ci-dessous sont facultatives : il s'agit d'un répertoire de structures possibles, pas d'un gabarit à remplir.
* Utilise uniquement les sections qui apportent une information distincte et utile.
* Évite de répéter la même idée dans plusieurs sections.
* Dans la conclusion, reformuler uniquement les conclusions ou recommandations effectivement soutenues par la vidéo ; ne pas ajouter de généralisation rhétorique pour donner une impression de clôture.

## Structure

### En bref

Commence par 2 à 3 phrases permettant de comprendre immédiatement :

* le sujet de la vidéo ;
* son idée ou objectif principal ;
* sa conclusion principale lorsqu'il y en a une.

### Citation représentative — optionnel

Si une formulation particulièrement forte ou représentative apparaît clairement dans la transcription, tu peux l'ajouter :

> [!quote]
> Auteur, si son identité est établie de manière fiable
> Citation exacte

N'utilise une citation que si sa formulation peut être reproduite avec suffisamment de confiance.
Ne reconstruis, ne corrige et n'améliore jamais une phrase pour en faire une citation.
En cas de doute, omets cette section.

### Points clés

Lorsque cela apporte une vue d'ensemble utile, présente les principales idées sous forme de quelques puces concises.
Cette section doit pouvoir être parcourue rapidement sans lire le résumé détaillé.
Ne répète pas ici mécaniquement tout ce qui sera développé ensuite.

### Résumé détaillé — si nécessaire

Utilise cette section lorsque le contenu est suffisamment riche pour nécessiter davantage qu'une vue d'ensemble.
Organise le contenu en sections avec des titres descriptifs correspondant à la structure réelle de la vidéo.

Exemple :

#### [Thème ou partie]

Résumé des idées, arguments, mécanismes et exemples importants.

#### [Thème ou partie]

Résumé.
Ajoute ou retire librement des sections selon le contenu.
Pour les contenus longs ou complexes, utilise si nécessaire un niveau supplémentaire de sous-sections.

### Faits, chiffres ou exemples importants — optionnel

Utilise cette section uniquement lorsqu'il existe des chiffres, résultats, faits ou exemples concrets qui méritent d'être retrouvés facilement séparément.
Ne répète pas des éléments déjà suffisamment mis en valeur ailleurs.

### Nuances, objections ou limites — optionnel

Utilise cette section lorsque la vidéo contient des réserves, incertitudes, objections, contre-arguments ou limites importantes pour comprendre correctement le propos.
Ne crée pas toi-même d'objection ou de critique absente de la vidéo.

### À retenir — optionnel

Utilise cette section uniquement lorsqu'une courte synthèse finale apporte une réelle valeur après le résumé.
Présente quelques conclusions ou enseignements essentiels.
Ne répète pas simplement `Points clés` avec d'autres mots.

### Ressources mentionnées — optionnel

Inclure uniquement les ressources explicitement mentionnées dans la vidéo et suffisamment identifiables à partir des informations disponibles.

Format :

* `[Titre ou nom de la ressource](URL)` — courte indication de son rôle dans la vidéo.

Ne recherche, n'invente et n'ajoute aucune ressource extérieure.

## Adaptation à la durée et à la densité

La durée est seulement un indicateur. La densité et la nature du contenu doivent déterminer la longueur réelle du résumé.

* **Moins de 10 minutes** : généralement un format compact avec `En bref`, quelques points clés et peu ou pas de sections supplémentaires.
* **10 à 30 minutes** : utiliser plusieurs grandes parties lorsque le contenu les justifie.
* **30 à 90 minutes** : privilégier une structure hiérarchisée avec des sections et éventuellement des sous-sections.
* **Plus de 90 minutes** : commencer par une vue d’ensemble puis organiser les grandes parties séparément lorsque cela facilite la compréhension.

Adapter également la structure au type de contenu :

* interview → thèmes et positions importantes ;
* tutoriel → objectif, prérequis éventuels et étapes essentielles ;
* débat → positions, arguments, objections et réponses ;
* cours → concepts, explications, relations entre concepts et exemples ;
* démonstration technique → objectif, architecture ou méthode, étapes importantes et résultat ;
* actualité ou analyse → contexte, faits principaux, interprétation de l'auteur et conclusions.

## Style

* Utilise du Markdown.
* Utilise des titres descriptifs plutôt que génériques lorsque cela est possible.
* Reste synthétique, précis et naturel.
* Privilégie des formulations informatives plutôt qu'une succession de fragments télégraphiques.
* Évite les répétitions entre les sections.
* Omet toute section non pertinente.
* Ne crée jamais une section uniquement pour respecter le modèle.
* Pour le code, utilise un bloc triple backticks avec le langage indiqué, par exemple `python`.
* Ne mentionne pas la transcription ni le processus utilisé pour produire le résumé.
* Lorsque le résumé est le livrable final demandé par l'utilisateur, ne place
  dans la réponse finale que le résumé.
* Lorsque le résumé constitue une étape intermédiaire d'un autre workflow,
  remettre le résumé à la tâche appelante et respecter le format de réponse
  défini par celle-ci.
