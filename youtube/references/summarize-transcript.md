# Prompt pour résumer une vidéo YouTube à partir de sa transcription

Ton travail consiste à produire, au format markdown, le résumé du contenu d’une vidéo YouTube à partir de sa transcription, sans insérer de commentaires, et sans ajouter d'interprétations personnelles.
Cette transcription est souvent générée automatiquement par Youtube et peut donc contenir des erreurs, des omissions ou des passages incompréhensibles, donc tu devras parfois interpréter le sens général du contenu pour produire un résumé utile et précis.

La longueur et le niveau de détail du résumé doivent s’adapter à la longueur, à la densité et à la structure de la source. Le résumé ne doit pas être artificiellement limité à quelques bullet points lorsque la vidéo est longue ou riche en informations.

Utilise les repères suivants comme ordres de grandeur, sans les appliquer mécaniquement :

* Pour une vidéo courte, d’environ 10 minutes ou moins : généralement 3 à 5 bullet points.
* Pour une vidéo de longueur moyenne, d’environ 10 à 30 minutes : utilise plusieurs sections avec des headings et suffisamment de bullet points pour couvrir les différentes parties importantes.
* Pour une vidéo longue, de plus de 30 minutes : produis un résumé plus développé, organisé en plusieurs sections thématiques ou chronologiques.
* Pour une conférence, un entretien, un débat ou un contenu particulièrement dense : privilégie la couverture des idées importantes plutôt qu’un nombre prédéfini de points.

Passe rapidement à une organisation avec des headings dès que le contenu aborde plusieurs thèmes, étapes, arguments ou parties distinctes. Il n’est pas nécessaire d’attendre d’avoir plus de cinq bullet points.

Les headings doivent décrire clairement le contenu de chaque section. Par exemple :

* `## Contexte`
* `## Thèse principale`
* `## Arguments`
* `## Méthode`
* `## Résultats`
* `## Objections`
* `## Applications`
* `## Conclusion`

Choisis les headings en fonction de la structure réelle de la vidéo. N’utilise pas systématiquement les mêmes.

Règles de rédaction :

* Utilise des bullet points courts, mais suffisamment détaillés pour être compréhensibles sans revoir immédiatement la vidéo.
* Résume les idées principales, les arguments, les explications, les exemples importants, les résultats et les conclusions.
* Conserve les distinctions, nuances et réserves importantes de l’auteur.
* Lorsque la vidéo présente plusieurs étapes, arguments ou positions, résume-les séparément.
* Lorsque le contenu suit un raisonnement, respecte son enchaînement logique.
* N’ajoute aucune information qui ne figure pas dans le contenu fourni.
* Ne transforme pas une hypothèse, une opinion ou une affirmation de l’auteur en fait établi.
* Élimine les introductions promotionnelles, les appels à s’abonner, les sponsors, les répétitions et les digressions sans intérêt.
* Ne mentionne pas qu’il s’agit d’une transcription.
* Ne cherche pas à produire le résumé le plus court possible : cherche à produire le résumé le plus utile proportionnellement à la richesse de la source.
* Ne place à l’intérieur de ce bloc que le résumé, sans commentaire sur ton travail ni formule introductive.

Exemple pour une vidéo courte :

```markdown
- Première idée importante.
- Deuxième idée importante.
- Conclusion principale.
```

Exemple pour une vidéo plus longue ou structurée :

```markdown
## Contexte

- Présentation du problème abordé.
- Éléments nécessaires pour comprendre la discussion.

## Arguments principaux

- Premier argument et sa justification.
- Deuxième argument et l’exemple utilisé pour l’illustrer.
- Limite ou objection reconnue par l’auteur.

## Applications

- Conséquences pratiques présentées dans la vidéo.
- Recommandations ou pistes proposées.

## Conclusion

- Conclusion générale et principal enseignement à retenir.
```
