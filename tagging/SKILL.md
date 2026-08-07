---
name: tagging
description: Produire, suggérer, normaliser ou corriger des tags destinés à Obsidian, Karakeep ou un système similaire.
---

# Tagging

## Méthode de classification

Pour chaque sujet important du contenu :

1. identifier le ou les domaines racines auxquels il appartient ;
2. identifier les sous-domaines pertinents ;
3. descendre jusqu'au niveau de précision réellement utile ;
4. conserver les différentes branches lorsque le contenu se situe à leur intersection ;
5. éliminer les tags correspondant uniquement à des mentions secondaires.

### Exemple

Un contenu consacré à l'utilisation de Python pour entraîner un modèle de machine learning appartient à la fois au développement logiciel et à l'intelligence artificielle : `#tech #dev #ia #python #machine-learning`

## Règles fondamentales

* Attribuer uniquement les tags correspondant à des sujets centraux ou réellement développés.
* Ne pas attribuer de tag pour un concept, une personne, une technologie ou un domaine seulement mentionné en passant.
* Utiliser les tags canoniques définis dans la taxonomie lorsqu'ils existent.
* Ne pas créer de synonyme ou de variante inutile d'un tag existant.
* Utiliser des tags en minuscules.
* Utiliser de préférence des tags en français (avec accents) sauf lorsqu'un terme anglais est consacré par l'usage ou constitue le nom courant du concept.
* Préférer les noms au singulier lorsque cela est naturel.
* Ordonner les tags du plus général au plus spécifique.
* Respecter les relations parent/enfant explicitement définies.
* Conserver plusieurs branches lorsque le contenu appartient réellement à plusieurs ensembles.
* En règle générale, produire entre 1 et 5 tags.
* Dépasser 5 tags uniquement lorsque le contenu développe réellement plusieurs sujets importants.

## Tags parents

Lorsqu'un tag possède un parent canonique, inclure également ce parent ainsi que ses propres parents jusqu'au domaine racine pertinent.
Les relations parent/enfant explicitement définies dans cette skill ou dans les fichiers de taxonomie sont canoniques.
Pour les concepts courants dont l'appartenance à une branche est évidente, une relation peut être déduite sans consulter la taxonomie spécialisée.
Ne pas déduire une relation lorsqu'elle est ambiguë ou dépend d'une convention propre à la taxonomie.

### Exemples

`#tech #dev #python`
`#tech #ia #llm`
`#religion #christianisme #orthodoxie`
`#philosophie #épistémologie`

## Croisements

Un contenu peut appartenir à plusieurs branches simultanément.
Ne pas forcer artificiellement un sujet dans une branche unique.

### Exemples

IA utilisée pour programmer : `#tech #ia #dev`
Épistémologie religieuse : `#religion #philosophie #épistémologie`
Régulation de l'intelligence artificielle : `#tech #ia #politique #droit`
Analyse économique d'une entreprise : `#économie #business`

## Tags de sujet et tags transversaux

Distinguer les tags décrivant le sujet du contenu des tags décrivant son angle, son format ou son traitement éditorial.

### Exemple

`#politique #ia #actualité` : `#politique` et `#ia` décrivent le sujet, `#actualité` décrit la nature éditoriale du contenu, par exemple pour un article de presse sur la régulation de l'intelligence artificielle.
`#tech #devops #terraform #tutoriel` : `#tech` et `#devops` décrivent le sujet, `#tutoriel` décrit le format du contenu.

Les tags transversaux ne remplacent pas les tags de sujet.

## Niveau de précision

Ne pas produire une liste exhaustive de tous les concepts présents dans le contenu.
Ajouter un tag spécifique lorsqu'il apporte une information réellement utile pour retrouver ou distinguer le contenu.
Ne pas ajouter un tag simplement parce qu'il serait techniquement exact.

## Tags spécifiques et nouveaux tags

Un tag spécifique évident peut être utilisé directement lorsqu'il correspond
au nom naturel et non ambigu d'un sujet central.

Exemples : `#rust`, `#postgresql`, `#kubernetes`.

Ne pas créer de variante ou de synonyme lorsqu'un tag canonique connu existe.

Lorsqu'un concept ne possède pas de tag évident ou que plusieurs formulations
sont possibles, consulter la taxonomie spécialisée avant de créer un nouveau tag.

## Taxonomie courante

Les relations suivantes sont canoniques et peuvent être utilisées sans consulter les fichiers de taxonomie spécialisés :

- `#tech`
  - `#dev` : développement logiciel, programmation, langages
  - `#devops` : déploiement, CI/CD, conteneurisation, infrastructure automatisée
  - `#ia` : intelligence artificielle, machine learning, LLM
  - `#cybersécurité` : vulnérabilités, attaques, défense et sécurité informatique
- `#philosophie`
- `#business`
- `#économie`
- `#politique`
- `#religion`
- `#science`

Cette liste n'est pas exhaustive.

Un concept spécifique dont l'appartenance à une branche est évidente peut être utilisé directement sans consulter la taxonomie spécialisée.

Exemple : Rust est un langage de programmation ; un contenu consacré à Rust peut donc être classé `#tech #dev #rust` sans consulter `taxonomy/dev.md`.

Ne consulter `taxonomy/<branche>.md` que lorsqu'une information nécessaire à la classification n'est pas suffisamment déterminée par cette skill ou par les connaissances générales non ambiguës du modèle, notamment pour :

- vérifier un tag canonique ou une relation non évidente ;
- départager plusieurs tags proches ;
- connaître une sous-taxonomie spécialisée ;
- résoudre une ambiguïté ;
- vérifier une convention propre à un domaine.

En cas de conflit entre cette skill et un fichier de taxonomie spécialisé, le fichier de taxonomie prévaut.

### Références spécialisées

- `#tech` → `taxonomy/tech.md`
- `#dev` → `taxonomy/dev.md`
- `#devops` → `taxonomy/devops.md`
- `#ia` → `taxonomy/ia.md`
- `#cybersécurité` → `taxonomy/cybersécurité.md`
- `#philosophie` → `taxonomy/philosophie.md`
- `#religion` → `taxonomy/religion.md`
- `#politique` → `taxonomy/politique.md`
- `#business` → `taxonomy/business.md`

## Format de sortie

Sauf instruction contraire de la tâche appelante, retourner uniquement les tags, séparés par des espaces.

### Exemple

`#tech #dev #python #ia #llm`
