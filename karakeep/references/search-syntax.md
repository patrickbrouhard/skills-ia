# Syntaxe de recherche Karakeep

Lire cette référence lorsqu’une recherche nécessite des filtres, des opérateurs
booléens, des dates, des listes ou des tags.

## Principes

- Les conditions séparées par des espaces sont combinées comme un `AND`.
- Utiliser `and` ou `or` pour rendre la combinaison explicite.
- Utiliser des parenthèses pour grouper les conditions.
- Préfixer un qualificatif avec `-` ou `!` pour le nier.
- Traiter le texte qui n’est pas un qualificatif comme une recherche plein texte.
- Utiliser des guillemets pour les noms ou titres contenant des espaces.

## Qualificatifs

| Qualificatif | Signification | Exemple |
|---|---|---|
| `is:fav` | Bookmarks favoris | `is:fav` |
| `is:archived` | Bookmarks archivés | `-is:archived` |
| `is:tagged` | Bookmarks possédant un tag | `is:tagged` |
| `is:inlist` | Bookmarks appartenant à une liste | `is:inlist` |
| `is:link` | Bookmarks de type lien | `is:link` |
| `is:text` | Notes ou bookmarks texte | `is:text` |
| `is:media` | Images ou PDF | `is:media` |
| `is:broken` | Ressources dont la récupération a échoué | `is:broken` |
| `url:<valeur>` | Correspondance partielle sur l’URL | `url:github.com` |
| `title:<valeur>` | Correspondance sur le titre | `title:"machine learning"` |
| `#<tag>` | Bookmark possédant un tag | `#important` |
| `tag:<tag>` | Variante explicite du filtre par tag | `tag:"à lire"` |
| `list:<nom>` | Bookmark appartenant à une liste | `list:"à étudier"` |
| `after:<date>` | Créé à partir d’une date | `after:2026-01-01` |
| `before:<date>` | Créé à cette date ou avant | `before:2026-07-01` |
| `age:<durée>` | Âge maximal ou minimal | `age:<1w` |
| `feed:<nom>` | Issu d’un flux RSS | `feed:Hackernews` |
| `source:<valeur>` | Filtrer selon la source de capture | `source:rss` |

Les unités acceptées par `age:` sont :

- `d` : jours ;
- `w` : semaines ;
- `m` : mois ;
- `y` : années.

## Exemples

Favoris récents associés à l’IA :

```text
is:fav age:<1m #ia
```

Bookmarks archivés appartenant à une liste ou possédant un tag :

```text
is:archived and (list:"à lire" or #recherche)
```

Bookmarks sans tag ou sans liste :

```text
-is:tagged or -is:inlist
```

Recherche plein texte limitée aux liens actifs :

```text
machine learning is:link -is:archived
```

Contenu importé par RSS durant une période donnée :

```text
source:rss after:2026-01-01 before:2026-06-30
```
