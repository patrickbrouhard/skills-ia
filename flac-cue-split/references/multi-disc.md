# Albums multi-disques

Utiliser cette procédure lorsqu'une même release est répartie entre plusieurs images FLAC/CUE. Le moteur de découpe reste mono-disque : l'IA découvre, apparie et valide les mediums, puis orchestre une invocation indépendante par dossier disque.

## Découverte sans modification

Un dossier disque contient à sa racine exactement un FLAC et un CUE. Son chemin `backup` est absent ou désigne un dossier vide. Un LOG homonyme est facultatif.

À partir du chemin indiqué par l'utilisateur :

- reconnaître directement les sous-dossiers disques d'un conteneur d'album ;
- si le chemin est un répertoire parent, ne descendre vers un conteneur que lorsque l'album cohérent à traiter est unique ou explicitement désigné ;
- ne jamais agréger récursivement toutes les paires FLAC/CUE d'une arborescence, car elles peuvent appartenir à plusieurs releases ;
- laisser inchangés les sous-dossiers sans FLAC ni CUE, comme `Covers` ;
- traiter comme une anomalie un sous-dossier censé représenter un medium mais contenant seulement un FLAC ou seulement un CUE ;
- respecter toute exclusion explicite de l'utilisateur.

Si plusieurs conteneurs d'album sont possibles, demander lequel traiter avant toute création de fichier.

## Association des dossiers aux mediums

Établir une correspondance univoque entre chaque dossier disque local et un medium de la source de référence. Utiliser d'abord les TOC ou offsets exacts, puis le nombre de pistes, le nom ou la position du medium, les durées et les métadonnées éditoriales.

Ne pas se fier uniquement à des noms comme `CD 1` : les numéros peuvent manquer ou être incorrects. Une différence entre le nombre de mediums locaux et ceux de la release doit être signalée. Ne traiter un sous-ensemble que si l'utilisateur l'a explicitement demandé ou confirmé.

Présenter l'association retenue avant l'exécution, par exemple :

```text
CD 1 - Y      -> medium 1 « Y »      -> 8 pistes
CD 2 - Earth  -> medium 2 « Earth »  -> 7 pistes
```

Une ambiguïté sur l'association bloque tout le lot.

## Validation et exécution du lot

Valider avant toute mutation :

1. tous les dossiers disques et leurs `backup` ;
2. la structure de tous les CUE ;
3. l'association de tous les mediums avec la source ;
4. un manifeste distinct par disque avec une numérotation repartant de `01` ;
5. l'absence de collisions pour tous les noms finaux.

Après cette validation globale, appeler le moteur mono-disque dans l'ordre des mediums. Attendre le résultat de chaque invocation avant de lancer la suivante.

Si une invocation échoue, arrêter le lot. Chaque disque dispose de sa propre transaction : les disques déjà terminés restent finalisés et les suivants restent intacts. Présenter alors un bilan par disque et qualifier le résultat de succès partiel, jamais de succès global.
