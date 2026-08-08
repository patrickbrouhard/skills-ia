---
name: youtube
description: Extraire, comprendre ou résumer le contenu d'une vidéo YouTube à partir de son URL et de sa transcription.
---

# YouTube

Utiliser cette skill lorsqu'une tâche nécessite de comprendre le contenu d'une vidéo YouTube à partir de son URL.

Cela comprend notamment :

* récupérer la transcription d'une vidéo ;
* résumer une vidéo ;
* analyser son contenu ;
* extraire les informations nécessaires à une autre tâche, par exemple le tagging ou l'archivage dans un système de gestion de connaissances.

## Source principale

Pour comprendre le contenu d'une vidéo, utiliser :

`scripts/youtube_transcript.py`

Le script retourne un document JSON contenant les métadonnées disponibles ainsi que la transcription de la vidéo.

Ne pas se contenter du titre, de la description ou des métadonnées lorsqu'une transcription exploitable est disponible.

## Workflow

Pour une URL YouTube :

1. exécuter `scripts/youtube_transcript.py` avec l'URL ;
2. vérifier que la commande se termine correctement ;
3. interpréter le JSON retourné ;
4. utiliser la transcription comme source principale pour comprendre le contenu ;
5. utiliser les métadonnées uniquement comme contexte complémentaire ;
6. poursuivre ensuite selon l'objectif de la tâche appelante.

Exécution minimale :

```bash
python scripts/youtube_transcript.py "<URL>"
```

Ne demander des options supplémentaires au script que si elles sont réellement nécessaires à la tâche.

## Résumé

Lorsqu'un résumé de la vidéo est nécessaire, consulter :

`references/summarize-transcript.md`

Produire le résumé principalement à partir de la transcription.

Le titre, les chapitres et les autres métadonnées peuvent aider à comprendre ou structurer le contenu, mais ne doivent pas servir à inventer des informations absentes de la transcription.

## Transcriptions imparfaites

Les sous-titres peuvent être générés automatiquement et contenir :

* des erreurs de transcription ;
* des noms propres incorrects ;
* des mots manquants ;
* des phrases mal segmentées ;
* des passages incompréhensibles.

Interpréter prudemment le contexte lorsqu'une correction est évidente, mais ne pas inventer de contenu pour combler une lacune importante.

Lorsqu'une incertitude affecte substantiellement la tâche demandée, la signaler plutôt que la transformer en fait établi.

## Métadonnées

Utiliser les métadonnées retournées par le script lorsqu'elles sont pertinentes, notamment :

* titre ;
* chaîne ;
* durée ;
* date de publication ;
* langue des sous-titres ;
* chapitres.

Ne pas attribuer à ces métadonnées le même poids qu'au contenu réel de la transcription pour déterminer les sujets principaux.

## Utilisation par d'autres workflows

Lorsqu'une autre tâche utilise cette skill comme étape intermédiaire, retourner ou conserver les informations nécessaires à la suite du workflow, notamment :

* URL canonique ;
* titre ;
* métadonnées utiles ;
* transcription ;
* résumé, s'il a été demandé.

Pour du tagging, utiliser le contenu réel de la vidéo et non uniquement son titre.

## Gestion des erreurs

Si le script échoue :

1. lire le JSON d'erreur écrit sur `stderr` ;
2. identifier la cause lorsqu'elle est disponible ;
3. ne pas continuer comme si une transcription avait été obtenue ;
4. signaler clairement l'échec à la tâche appelante.

Ne pas inventer une transcription à partir du titre ou des connaissances générales du modèle.

## Limites

Le script ne télécharge pas la vidéo elle-même.

Il nécessite notamment :

* Python 3 ;
* `yt-dlp` disponible dans le `PATH` ;
* un accès Internet fonctionnel.

Si ces prérequis ne sont pas disponibles dans l'environnement courant, ne pas prétendre avoir extrait la transcription.

## Dépendances

Le script nécessite l'exécutable `yt-dlp` disponible dans le `PATH`.

Si `yt-dlp` n'est pas disponible :

- ne pas installer automatiquement `yt-dlp` avec `pip`, winget ou un autre gestionnaire de paquets ;
- ne pas créer d'environnement Python temporaire pour contourner le problème ;
- signaler que la dépendance n'est pas accessible dans l'environnement courant et indiquer le diagnostic utile.

La configuration ou l'installation des dépendances doit être effectuée séparément du workflow de traitement d'une vidéo.