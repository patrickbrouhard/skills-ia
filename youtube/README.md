# YouTube Transcript CLI

Ce script Python extrait les métadonnées et le transcript d'une vidéo YouTube et renvoie le résultat sous forme de JSON structuré.

Il utilise uniquement la bibliothèque standard de Python. L'unique dépendance externe est l'exécutable **yt-dlp**, qui doit être installé séparément et accessible dans le `PATH`.

## Prérequis

- Python 3
- `yt-dlp` disponible dans le `PATH`
- Une connexion Internet

Aucun paquet Python externe n'est nécessaire : il n'y a pas de `requests`, de module Python `yt_dlp`, ni de `requirements.txt` à installer.

Pour vérifier les prérequis :

```powershell
python --version
yt-dlp --version
```

Sous Windows, il est également possible de vérifier quel exécutable sera utilisé :

```powershell
where.exe yt-dlp
```

## Installation de yt-dlp sous Windows avec winget

Une façon simple d'installer `yt-dlp` sous Windows 11 est d'utiliser choco ou winget :

```powershell
winget install yt-dlp
```

Après l'installation, vérifier que la commande est accessible :

```powershell
yt-dlp --version
```

Le script recherche `yt-dlp` dans le `PATH` et échoue avec un message explicite si l'exécutable n'est pas trouvé.

## Utilisation

Utilisation minimale :

```powershell
python youtube_transcript_cli_ytdlp.py "https://www.youtube.com/watch?v=VIDEO_ID"
```

La sortie est écrite sur la sortie standard (`stdout`) sous forme de JSON.

Pour obtenir un JSON indenté et plus lisible :

```powershell
python youtube_transcript_cli_ytdlp.py "https://www.youtube.com/watch?v=VIDEO_ID" --pretty
```

### Options

| Option | Description |
| --- | --- |
| `--include-segments` | Ajoute les segments horodatés du transcript. |
| `--include-description` | Ajoute la description complète de la vidéo. |
| `--include-tags` | Ajoute les tags YouTube. |
| `--include-public-statistics` | Ajoute les nombres de vues, likes et commentaires lorsqu'ils sont disponibles. |
| `--pretty` | Indente le JSON pour le rendre plus lisible. |

Exemple avec plusieurs options :

```powershell
python youtube_transcript_cli_ytdlp.py `
  "https://www.youtube.com/watch?v=VIDEO_ID" `
  --include-description `
  --include-public-statistics `
  --pretty
```

## Sélection des sous-titres

Le script applique les règles suivantes :

1. s'il existe exactement une piste de sous-titres manuels et qu'elle est en français ou en anglais, cette piste est utilisée ;
2. dans les autres cas, le script recherche la piste automatique correspondant à la langue originale, identifiée par un code YouTube se terminant par `-orig` ;
3. le format de sous-titres utilisé est `json3`.

Le transcript retourné est normalisé en texte continu. Les retours à la ligne propres à l'affichage des sous-titres YouTube ne sont pas conservés comme structure logique du texte.

## Données retournées

Le document JSON contient notamment :

- l'identifiant, l'URL et le titre de la vidéo ;
- les informations de chaîne ;
- la durée et la date de publication ;
- le transcript ;
- la langue et le type de sous-titres utilisés ;
- les chapitres lorsqu'ils sont disponibles ;
- quelques statistiques calculées sur le transcript.

Des champs supplémentaires peuvent être activés avec les options de ligne de commande.

## Gestion des erreurs

En cas d'échec, le script écrit un document JSON d'erreur sur la sortie d'erreur (`stderr`) et se termine avec un code de sortie `1`.

Exemples de causes possibles :

- `yt-dlp` absent du `PATH` ;
- vidéo inaccessible ;
- absence de piste de sous-titres compatible ;
- changement côté YouTube non encore pris en charge par la version installée de `yt-dlp` ;
- erreur réseau lors du téléchargement de la piste de sous-titres.

## Mise à jour de yt-dlp

`yt-dlp` doit être maintenu à jour. YouTube modifie régulièrement son fonctionnement et une version qui fonctionnait auparavant peut temporairement cesser d'extraire certaines informations jusqu'à ce qu'une correction soit publiée.

### Installation gérée par winget

Si `yt-dlp` a été installé avec winget, utiliser **winget pour le mettre à jour** :

```powershell
winget upgrade yt-dlp
```

Puis vérifier la version active :

```powershell
yt-dlp --version
```

On peut également vérifier l'installation connue de winget avec :

```powershell
winget list yt-dlp
```

Cette méthode est préférable à `yt-dlp -U` pour une installation gérée par winget, car winget reste alors la source d'installation et de mise à jour du programme.

### À propos de `yt-dlp -U`

`yt-dlp` possède bien une commande de mise à jour intégrée :

```powershell
yt-dlp -U
```

Cependant, cette commande est prévue pour les **binaires de release installés directement** depuis yt-dlp. Lorsqu'un gestionnaire de paquets tiers comme winget, Scoop, Chocolatey ou pip a été utilisé, il est recommandé de mettre `yt-dlp` à jour avec ce même gestionnaire.

En pratique, pour l'installation Windows décrite dans ce README :

```powershell
winget upgrade yt-dlp
```

est la commande à privilégier.

### Si YouTube casse soudainement l'extraction

Commencer par mettre `yt-dlp` à jour :

```powershell
winget upgrade yt-dlp
```

Puis relancer :

```powershell
yt-dlp --version
python youtube_transcript_cli_ytdlp.py "https://www.youtube.com/watch?v=VIDEO_ID"
```

Le projet yt-dlp publie plusieurs canaux (`stable`, `nightly` et `master`). Sa documentation indique que le canal `nightly` reçoit les correctifs plus rapidement et le recommande aux utilisateurs confrontés à un problème encore présent dans `stable`.

Une installation gérée par winget doit néanmoins continuer à être mise à jour avec winget. Si un besoin réel apparaît de passer au canal `nightly`, il vaut mieux choisir explicitement une méthode d'installation prenant ce canal en charge plutôt que de mélanger les mécanismes de mise à jour.

## Architecture des dépendances

Le script est volontairement conçu pour ne dépendre d'aucune bibliothèque Python tierce :

```text
Python 3
└── bibliothèque standard uniquement
    ├── argparse
    ├── json
    ├── pathlib / stdlib associée
    ├── shutil
    ├── subprocess
    ├── urllib
    └── autres modules standard

Dépendance externe
└── yt-dlp (exécutable dans le PATH)
```

Cette séparation évite les problèmes de `pip`, d'environnement virtuel et de dépendances installées dans un autre interpréteur Python que celui utilisé pour exécuter le script.

## Notes

Le script utilise `yt-dlp` uniquement pour récupérer les métadonnées nécessaires. Il ne télécharge pas la vidéo elle-même.

Les URL temporaires des pistes de sous-titres fournies par YouTube sont ensuite téléchargées directement avec `urllib`, qui fait partie de la bibliothèque standard de Python.
