# Validation du CUE et identification du disque

Utiliser cette procédure pendant la phase de validation pure. Le CUE fournit la géométrie de découpe et des indices éditoriaux ; la source désignée par l'utilisateur définit la release ou le medium de référence.

## Conditions structurelles obligatoires

- Exactement un FLAC et un CUE à la racine du dossier.
- Le chemin `backup` est absent ou désigne un dossier vide.
- Le CUE référence une seule image audio cohérente avec le FLAC présent.
- Les pistes `AUDIO` ont des numéros uniques et ordonnés.
- Chaque piste possède un `INDEX 01` valide ; les positions sont strictement croissantes.
- Le nombre de pistes `AUDIO` correspond exactement au nombre de pistes de la source de référence.

Un échec sur une de ces conditions bloque la découpe. Présenter le problème à l'utilisateur au lieu de choisir silencieusement une autre release ou d'ignorer une piste.

## Hiérarchie des preuves d'identité

1. **TOC complète exacte** : tous les offsets `INDEX 01` correspondent en secteurs et le lead-out dérivé du FLAC correspond aussi.
2. **Offsets exacts** : tous les débuts de pistes correspondent, mais le lead-out ne peut pas être vérifié.
3. **Structure et durées concordantes** : nombre, ordre et durées sont compatibles dans une tolérance raisonnable.
4. **Métadonnées concordantes** : artiste, album, œuvres et mouvements désignent sémantiquement le même contenu.

Une TOC exacte est plus probante qu'une ressemblance textuelle. Un FreeDB Disc ID identique constitue un indice supplémentaire, mais ne remplace pas la comparaison des offsets car il peut avoir des collisions.

## Comparaison MusicBrainz en secteurs CD

Un CD audio contient 75 secteurs par seconde. Pour un `INDEX 01` au format `MM:SS:FF`, calculer l'offset MusicBrainz attendu ainsi :

```text
offset = ((MM × 60 + SS) × 75 + FF) + 150
```

Les 150 secteurs ajoutés représentent le lead-in de deux secondes. Comparer uniquement les `INDEX 01` aux offsets de pistes de la TOC. Les `INDEX 00` décrivent notamment des pregaps et ne sont pas les débuts de pistes utilisés par le Disc ID.

Une TOC complète contient aussi le lead-out. Pour une image CDDA standard à 44 100 Hz dont la première piste commence à `00:00:00`, un secteur contient 588 trames d'échantillons par canal :

```text
lead-out = 150 + total_samples / 588
```

Utiliser le nombre total d'échantillons et la fréquence fournis par FLAC, par exemple avec `metaflac`. N'affirmer une correspondance complète que si la fréquence vaut 44 100 Hz, si le nombre d'échantillons est divisible par 588 et si le contexte du CUE ne comporte pas de particularité telle qu'une piste cachée avant la piste 1. Sinon, qualifier la correspondance des offsets de très forte sans prétendre avoir vérifié le lead-out.

## Comparaison éditoriale souple

Comparer le sens plutôt que les chaînes littérales. Accepter notamment les différences de capitalisation, ponctuation, apostrophes, langue, préfixes ou formulation plus complète.

Pour la musique classique, privilégier les éléments discriminants : compositeur, numéro de catalogue, numéro ou tonalité du concerto, numéro du mouvement, indication de tempo et ordre des œuvres. Une différence sur un numéro RV/BWV/K., un mouvement, l'ordre ou l'œuvre est significative ; une différence comme `L'Estate` contre `L’Estate`, ou l'ajout d'un numéro d'opus cohérent, est éditoriale.

## Contrôle approximatif par les durées

Lorsque la TOC n'est pas disponible, calculer les durées intermédiaires par différence entre deux `INDEX 01`. Calculer la dernière depuis la durée du FLAC. Tenir compte des arrondis et des pregaps ; utiliser les durées comme preuve de cohérence, pas comme identité exacte.

## Décision et compte rendu

Avant l'exécution, résumer :

- la release ou le medium retenu et la source utilisée ;
- le nombre de pistes et leur ordre ;
- le niveau de preuve atteint : TOC complète, offsets exacts, durées ou métadonnées ;
- les différences éditoriales acceptées ;
- toute divergence non résolue.

Si une divergence peut changer les points de découpe, l'ordre ou l'identité du disque, arrêter et demander à l'utilisateur quoi faire.
