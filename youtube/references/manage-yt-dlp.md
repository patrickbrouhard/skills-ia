# Gestion de yt-dlp

Consulter ce fichier uniquement lorsqu'une tâche concerne directement la maintenance de `yt-dlp` ou lorsqu'un échec de l'extraction justifie d'examiner cette dépendance.

Utiliser :

`scripts/manage_yt_dlp.py`

Ce script gère uniquement le binaire `yt-dlp` local situé dans `scripts/`. Il ne doit pas modifier une installation globale de `yt-dlp`.

## Commandes

État local, sans vérification réseau :

```bash
python scripts/manage_yt_dlp.py status
```

Vérification de la dernière version stable officielle :

```bash
python scripts/manage_yt_dlp.py check
```

Installation locale :

```bash
python scripts/manage_yt_dlp.py install
```

Mise à jour du binaire local :

```bash
python scripts/manage_yt_dlp.py update
```

## Choix de la commande

### Version installée

Si l'utilisateur demande uniquement quelle version est installée, utiliser `status`.

Ne pas effectuer de recherche Web supplémentaire.

### Vérification des mises à jour

Si l'utilisateur demande si `yt-dlp` est à jour, utiliser `check`.

Par défaut, `check` compare la version locale à la dernière release officielle du canal `stable`.

Ne pas effectuer une recherche Web séparée si `check` réussit.

Un autre canal peut être vérifié explicitement :

```bash
python scripts/manage_yt_dlp.py check --channel nightly
python scripts/manage_yt_dlp.py check --channel master
```

### Installation

Si l'utilisateur demande d'installer `yt-dlp`, ou si `youtube_transcript.py` indique qu'aucun `yt-dlp` local ni dans le `PATH` n'est disponible :

1. exécuter `manage_yt_dlp.py install` ;
2. ne pas installer de paquet Python et ne pas modifier une installation système ;
3. si l'installation automatique faisait suite à une extraction, relancer cette extraction une seule fois ;
4. si l'installation échoue, arrêter le workflow et signaler l'erreur.

`install` utilise le canal `stable` par défaut.

Pour remplacer explicitement un binaire local existant :

```bash
python scripts/manage_yt_dlp.py install --force
```

Ne pas utiliser `--force` sans raison.

### Mise à jour explicite

Si l'utilisateur demande de mettre à jour `yt-dlp`, utiliser :

```bash
python scripts/manage_yt_dlp.py update
```

Sans canal explicite, la commande conserve le canal courant du binaire.

Si l'utilisateur demande explicitement un changement de canal :

```bash
python scripts/manage_yt_dlp.py update --channel stable
python scripts/manage_yt_dlp.py update --channel nightly
python scripts/manage_yt_dlp.py update --channel master
```

## Mise à jour automatique après un échec

Une mise à jour automatique peut être tentée uniquement lorsque l'erreur indique vraisemblablement :

- une incompatibilité entre la version actuelle de `yt-dlp` et YouTube ;
- une erreur de l'extracteur YouTube susceptible d'avoir été corrigée dans une version plus récente ;
- un changement côté YouTube rendant l'extraction impossible avec la version installée.

Dans ce cas :

1. exécuter `manage_yt_dlp.py check` ;
2. si une mise à jour stable est disponible, exécuter `manage_yt_dlp.py update` ;
3. si la mise à jour réussit, relancer une seule fois l'extraction initiale ;
4. si aucune mise à jour n'est disponible ou si l'extraction échoue encore, arrêter le workflow et signaler l'erreur.

Ne pas tenter de mise à jour automatique pour une erreur clairement liée à :

- une URL invalide ;
- une erreur de passage d'arguments ;
- l'absence de sous-titres compatibles ;
- une vidéo privée, supprimée ou inaccessible ;
- un problème réseau ;
- un blocage du sandbox ;
- un problème de permissions ;
- un problème de `PATH` ;
- un répertoire temporaire inaccessible ;
- une erreur manifestement indépendante de `yt-dlp`.

Ne pas entrer dans une boucle de mises à jour et de nouvelles tentatives.

## Canaux

Canaux pris en charge :

- `stable` ;
- `nightly` ;
- `master`.

Le canal `stable` est utilisé par défaut pour les installations et les vérifications.

Ne pas passer automatiquement de `stable` à `nightly` ou `master`.

Un changement de canal doit être explicitement demandé par l'utilisateur ou décidé dans le cadre d'un diagnostic spécifique.

## Sandbox et réseau

`status` n'a pas besoin d'accéder au réseau.

`check`, `install` et `update` nécessitent un accès réseau.

Le script configure lui-même un répertoire temporaire accessible pour les processus `yt-dlp`, afin d'éviter de dépendre du TEMP/TMP utilisateur lorsque celui-ci est inaccessible dans un sandbox.

Si une commande échoue malgré cela, distinguer notamment :

- dépendance absente ;
- problème de permissions ;
- refus d'exécution du binaire ;
- restriction réseau du sandbox ;
- erreur de l'API ou du téléchargement.

Lorsqu'une autorisation ciblée existe déjà pour `manage_yt_dlp.py`, l'utiliser.

Ne pas réinstaller ou déplacer une dépendance uniquement pour contourner une restriction du sandbox.
