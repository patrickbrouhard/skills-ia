# YouTube Transcript CLI

Ce script Python extrait les métadonnées et le transcript d'une vidéo YouTube et renvoie le résultat sous forme de JSON structuré.

Il utilise uniquement la bibliothèque standard de Python.

La seule dépendance externe est l'exécutable **yt-dlp**. Le script peut utiliser soit un binaire placé directement à côté du script, soit une installation disponible dans le `PATH`.

## Prérequis

* Python 3
* `yt-dlp`
* une connexion Internet

Aucun paquet Python externe n'est nécessaire : il n'y a pas de `requests`, de module Python `yt_dlp`, ni de `requirements.txt` à installer.

## Recherche de yt-dlp

Le script recherche `yt-dlp` dans cet ordre :

1. un binaire situé dans le même répertoire que `youtube_transcript.py` :

   * `yt-dlp.exe` sous Windows ;
   * `yt-dlp` sous Linux/macOS ;
2. à défaut, un exécutable `yt-dlp` disponible dans le `PATH`.

Structure recommandée pour une installation autonome de la skill :

```text
youtube/
├── SKILL.md
├── README.md
├── references/
│   └── summarize-transcript.md
└── scripts/
    ├── youtube_transcript.py
    └── yt-dlp.exe
```

Sous Linux ou macOS, le binaire local peut être nommé :

```text
scripts/yt-dlp
```

et doit disposer du droit d'exécution.

Cette organisation permet notamment d'éviter de dépendre de l'emplacement choisi par un gestionnaire de paquets ou par l'environnement d'exécution.

Si aucun binaire local n'est trouvé, le script utilise :

```text
yt-dlp
```

depuis le `PATH`.

## Vérification des prérequis

Python :

```powershell
python --version
```

Si `yt-dlp` est installé globalement :

```powershell
yt-dlp --version
```

Sous Windows :

```powershell
where.exe yt-dlp
```

Ces commandes vérifient uniquement l'installation globale. Si un binaire `yt-dlp.exe` est placé dans `scripts/`, c'est celui-ci qui sera utilisé en priorité par `youtube_transcript.py`.

## Utilisation

Depuis le répertoire `scripts` :

```powershell
python youtube_transcript.py "https://www.youtube.com/watch?v=VIDEO_ID"
```

Ou avec un chemin explicite :

```powershell
python "C:\chemin\vers\youtube\scripts\youtube_transcript.py" "https://www.youtube.com/watch?v=VIDEO_ID"
```

La sortie est écrite sur la sortie standard (`stdout`) sous forme de JSON.

Pour obtenir un JSON indenté et plus lisible :

```powershell
python youtube_transcript.py "https://www.youtube.com/watch?v=VIDEO_ID" --pretty
```

### Options

| Option                        | Description                                                                    |
| ----------------------------- | ------------------------------------------------------------------------------ |
| `--include-segments`          | Ajoute les segments horodatés du transcript.                                   |
| `--include-description`       | Ajoute la description complète de la vidéo.                                    |
| `--include-tags`              | Ajoute les tags YouTube.                                                       |
| `--include-public-statistics` | Ajoute les nombres de vues, likes et commentaires lorsqu'ils sont disponibles. |
| `--pretty`                    | Indente le JSON pour le rendre plus lisible.                                   |

Exemple avec plusieurs options :

```powershell
python youtube_transcript.py `
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

## Téléchargement des sous-titres

`yt-dlp` est utilisé pour récupérer les métadonnées de la vidéo et identifier la piste de sous-titres appropriée.

L'URL temporaire de la piste `json3` est ensuite téléchargée directement par le script avec `urllib`, qui fait partie de la bibliothèque standard de Python.

Lorsque `yt-dlp` fournit des en-têtes HTTP associés à la piste de sous-titres, le script les réutilise pour effectuer cette requête.

Aucune vidéo n'est téléchargée.

## Répertoire temporaire

Certains environnements sandboxés empêchent `yt-dlp` d'utiliser le répertoire temporaire système habituel.

Pour éviter ce problème, `youtube_transcript.py` crée lui-même un répertoire temporaire dédié à l'exécution de `yt-dlp`.

Le répertoire courant est utilisé en priorité comme emplacement parent lorsqu'il est inscriptible. À défaut, le mécanisme temporaire standard de Python est utilisé.

Les variables d'environnement sont modifiées uniquement pour le sous-processus `yt-dlp` :

* `TEMP` et `TMP` sous Windows ;
* `TMPDIR` sous Linux/macOS.

L'environnement global de la session n'est pas modifié.

Le répertoire temporaire est supprimé automatiquement après l'exécution.

## Données retournées

Le document JSON contient notamment :

* l'identifiant, l'URL et le titre de la vidéo ;
* les informations de chaîne ;
* la durée et la date de publication ;
* le transcript ;
* la langue et le type de sous-titres utilisés ;
* les chapitres lorsqu'ils sont disponibles ;
* quelques statistiques calculées sur le transcript.

Des champs supplémentaires peuvent être activés avec les options de ligne de commande.

## Gestion des erreurs

En cas d'échec, le script écrit un document JSON d'erreur sur la sortie d'erreur (`stderr`) et se termine avec un code de sortie `1`.

Exemples de causes possibles :

* aucun `yt-dlp` local ou disponible dans le `PATH` ;
* binaire local non exécutable sous Linux/macOS ;
* vidéo inaccessible ;
* absence de piste de sous-titres compatible ;
* changement côté YouTube non encore pris en charge par la version utilisée de `yt-dlp` ;
* accès réseau bloqué ;
* erreur réseau lors du téléchargement des métadonnées ou des sous-titres ;
* impossibilité de créer un répertoire temporaire utilisable.

## Utilisation avec Codex sous Windows

### Installation de la skill

Les skills utilisateur peuvent être installées sous :

```text
C:\Users\<UTILISATEUR>\.agents\skills\
```

Par exemple :

```text
C:\Users\<UTILISATEUR>\.agents\skills\youtube\
```

Le script peut alors être exécuté depuis :

```text
C:\Users\<UTILISATEUR>\.agents\skills\youtube\scripts\youtube_transcript.py
```

Placer `yt-dlp.exe` dans le même répertoire permet d'éviter les restrictions que le sandbox Windows peut appliquer à certains emplacements d'installation, notamment ceux utilisés par WinGet ou les alias `WindowsApps`.

### Accès réseau du sandbox

Même avec un `yt-dlp.exe` local et exécutable, le sandbox Codex peut interdire l'accès réseau nécessaire à YouTube.

Le symptôme typique est un échec de connexion vers :

```text
www.youtube.com:443
```

avec une erreur Windows telle que :

```text
WinError 10013
```

Dans ce cas, le problème ne vient ni de Python, ni de `yt-dlp`, ni du `PATH`. Il s'agit d'une restriction réseau du sandbox.

Pour une installation personnelle et maîtrisée, une règle Codex ciblée peut autoriser uniquement `youtube_transcript.py` à s'exécuter avec les permissions nécessaires.

Créer :

```text
C:\Users\<UTILISATEUR>\.codex\rules\default.rules
```

Exemple :

```python
prefix_rule(
    pattern = [
        "python",
        "C:\\Users\\<UTILISATEUR>\\.agents\\skills\\youtube\\scripts\\youtube_transcript.py",
    ],
    decision = "allow",
    justification = "Autorise le script YouTube personnel à accéder au réseau nécessaire à l'extraction des métadonnées et sous-titres.",
)
```

Le chemin doit correspondre à la commande réellement exécutée sur la machine.

Cette règle est volontairement limitée à ce script précis. Il est déconseillé d'autoriser globalement toutes les commandes Python ou tous les scripts d'un répertoire à s'exécuter hors sandbox.

Après création ou modification d'une règle, redémarrer Codex ou l'application utilisant son runtime afin que la configuration soit rechargée.

### Tester une règle Codex

La correspondance d'une règle peut être vérifiée avant utilisation :

```powershell
codex execpolicy check --pretty `
  --rules "$HOME\.codex\rules\default.rules" `
  -- python "C:\Users\<UTILISATEUR>\.agents\skills\youtube\scripts\youtube_transcript.py" "https://www.youtube.com/watch?v=test"
```

Le résultat attendu contient notamment :

```json
{
  "decision": "allow"
}
```

## Installation et mise à jour de yt-dlp

Deux modes peuvent être utilisés.

### Binaire local à la skill

C'est le mode privilégié lorsque la skill doit être autonome ou fonctionner dans un environnement sandboxé :

```text
youtube/scripts/yt-dlp.exe
```

Le binaire doit alors être maintenu à jour séparément.

Pour un exécutable officiel téléchargé directement depuis les releases de yt-dlp, la commande intégrée de mise à jour peut être utilisée :

```powershell
.\yt-dlp.exe -U
```

Le binaire n'a pas nécessairement vocation à être versionné dans le dépôt Git de la skill. Il peut être installé ou mis à jour séparément lors du déploiement de la skill.

### Installation globale

Le fallback vers le `PATH` permet également d'utiliser une installation globale.

Sous Windows avec WinGet :

```powershell
winget install yt-dlp
```

Mise à jour :

```powershell
winget upgrade yt-dlp
```

Vérification :

```powershell
yt-dlp --version
```

Une installation gérée par un gestionnaire de paquets doit de préférence être mise à jour avec ce même gestionnaire.

### À propos de `yt-dlp -U`

`yt-dlp` possède une commande de mise à jour intégrée :

```powershell
yt-dlp -U
```

Elle est particulièrement adaptée aux binaires officiels installés directement.

Lorsqu'une installation est gérée par WinGet, Scoop, Chocolatey, pip ou un autre gestionnaire de paquets, utiliser de préférence le mécanisme de mise à jour de ce gestionnaire.

## Si YouTube casse soudainement l'extraction

Commencer par vérifier la version réellement utilisée.

Si la skill utilise son binaire local :

```powershell
C:\Users\<UTILISATEUR>\.agents\skills\youtube\scripts\yt-dlp.exe --version
```

S'il n'existe pas et que le fallback `PATH` est utilisé :

```powershell
yt-dlp --version
```

Mettre ensuite `yt-dlp` à jour selon son mode d'installation, puis relancer :

```powershell
python youtube_transcript.py "https://www.youtube.com/watch?v=VIDEO_ID"
```

Le projet yt-dlp propose plusieurs canaux de publication, notamment `stable`, `nightly` et `master`. En cas de régression ou de changement récent côté YouTube, une version plus récente peut contenir un correctif qui n'est pas encore présent dans la version stable.

Ne pas mélanger inutilement plusieurs mécanismes d'installation ou de mise à jour.

## Architecture des dépendances

Le script est volontairement conçu pour ne dépendre d'aucune bibliothèque Python tierce :

```text
Python 3
└── bibliothèque standard uniquement
    ├── argparse
    ├── dataclasses
    ├── datetime
    ├── json
    ├── os
    ├── pathlib
    ├── re
    ├── shutil
    ├── subprocess
    ├── sys
    ├── tempfile
    ├── urllib
    └── typing

Dépendance externe
└── yt-dlp
    ├── binaire local à côté du script — prioritaire
    └── exécutable dans le PATH — fallback
```

Cette séparation évite les problèmes liés à `pip`, aux environnements virtuels et aux dépendances installées dans un autre interpréteur Python que celui utilisé pour exécuter le script.

Elle permet également de conserver un script Python autonome et portable tout en isolant clairement la dépendance native nécessaire à l'interaction avec YouTube.

## Notes

Le script utilise `yt-dlp` uniquement pour récupérer les métadonnées nécessaires à l'identification de la vidéo et de ses sous-titres.

Il ne télécharge pas la vidéo elle-même.

Les URL temporaires des pistes de sous-titres fournies par YouTube sont ensuite téléchargées directement avec la bibliothèque standard Python.
