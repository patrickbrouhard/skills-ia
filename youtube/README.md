# Skill YouTube

Skill permettant à un agent d'extraire, comprendre et résumer le contenu d'une vidéo YouTube à partir de ses sous-titres.

Elle s'appuie sur deux scripts Python :

```text
scripts/youtube_transcript.py
scripts/manage_yt_dlp.py
```

et sur deux références spécialisées :

```text
references/summarize-transcript.md
references/manage-yt-dlp.md
```

## Structure

```text
youtube/
├── README.md
├── SKILL.md
├── references/
│   ├── manage-yt-dlp.md
│   └── summarize-transcript.md
└── scripts/
    ├── manage_yt_dlp.py
    ├── youtube_transcript.py
    └── yt-dlp.exe
```

Sous Linux ou macOS, le binaire local peut être nommé :

```text
scripts/yt-dlp
```

Le binaire `yt-dlp` est volontairement ignoré par Git.

## Fonctionnement

Le workflow normal est :

```text
URL YouTube
   ↓
youtube_transcript.py
   ↓
yt-dlp
   ├── métadonnées
   └── identification des sous-titres
   ↓
téléchargement JSON3 avec urllib
   ↓
document de sortie
   ├── Markdown pour l'agent
   └── JSON pour les usages programmatiques
   ↓
agent
   ├── compréhension
   ├── résumé
   └── utilisation par un autre workflow
```

Aucune vidéo n'est téléchargée.

`yt-dlp` sert principalement à récupérer les métadonnées de la vidéo et à identifier la piste de sous-titres appropriée.

Le fichier de sous-titres `json3` est ensuite téléchargé directement avec `urllib`.

## Prérequis

* Python 3 ;
* `yt-dlp` ;
* accès Internet.

Aucune bibliothèque Python externe n'est nécessaire.

Il n'y a notamment pas de dépendance à :

* `requests` ;
* `yt_dlp` comme module Python ;
* `python-dotenv`.

## Recherche de yt-dlp

`youtube_transcript.py` recherche `yt-dlp` dans cet ordre :

1. le binaire placé dans `scripts/` ;
2. à défaut, `yt-dlp` disponible dans le `PATH`.

Binaire local sous Windows :

```text
scripts/yt-dlp.exe
```

Binaire local sous Linux/macOS :

```text
scripts/yt-dlp
```

L'installation locale est recommandée lorsque la skill fonctionne dans un environnement sandboxé.

## Extraction d'une vidéo

Pour produire le document destiné à un agent :

```bash
python scripts/youtube_transcript.py \
  "https://www.youtube.com/watch?v=VIDEO_ID" \
  --agent-output video.md
```

Le Markdown contient directement les métadonnées utiles, les chapitres et la
transcription. C'est la sortie recommandée pour les workflows des agents.

Pour obtenir le JSON sur `stdout` :

```bash
python scripts/youtube_transcript.py "https://www.youtube.com/watch?v=VIDEO_ID"
```

Pour une sortie indentée :

```bash
python scripts/youtube_transcript.py "https://www.youtube.com/watch?v=VIDEO_ID" --pretty
```

### Options

| Option                        | Description                                   |
| ----------------------------- | --------------------------------------------- |
| `--include-segments`          | Ajoute les segments horodatés                 |
| `--include-description`       | Ajoute la description complète                |
| `--include-tags`              | Ajoute les tags YouTube                       |
| `--include-public-statistics` | Ajoute les statistiques publiques disponibles |
| `--pretty`                    | Indente le JSON                               |
| `--output FICHIER`            | Écrit le JSON dans un fichier UTF-8           |
| `--agent-output FICHIER`      | Écrit le document Markdown pour l'agent       |

Exemple :

```bash
python scripts/youtube_transcript.py \
  "https://www.youtube.com/watch?v=VIDEO_ID" \
  --include-description \
  --include-public-statistics \
  --pretty
```

## Sélection des sous-titres

Le script applique les règles suivantes :

1. s'il existe exactement une piste manuelle en français ou en anglais, elle est utilisée ;
2. sinon, le script recherche la piste automatique correspondant à la langue originale, généralement identifiée par un code se terminant par `-orig` ;
3. le format utilisé est `json3`.

Le transcript est ensuite normalisé en texte continu.

## Données retournées

Le Markdown pour agent et le JSON peuvent notamment contenir :

* identifiant de la vidéo ;
* URL canonique ;
* titre ;
* chaîne ;
* durée ;
* date de publication ;
* langue des sous-titres ;
* type de sous-titres ;
* transcription ;
* chapitres ;
* statistiques calculées sur le transcript.

Des champs supplémentaires peuvent être demandés avec les options de ligne de
commande. `--output` et `--agent-output` sont mutuellement exclusifs.

## Résumé

Lorsqu'un agent doit résumer la vidéo, les instructions spécialisées se trouvent dans :

```text
references/summarize-transcript.md
```

Ce fichier définit notamment :

* la fidélité attendue à la transcription ;
* le niveau de condensation ;
* la structure éventuelle du résumé ;
* la gestion des exemples, chiffres et nuances ;
* les informations à ne pas inventer.

Il n'est chargé que lorsqu'un résumé est nécessaire.

## Gestion locale de yt-dlp

La maintenance du binaire local est assurée par :

```text
scripts/manage_yt_dlp.py
```

Les instructions destinées à l'agent sont séparées dans :

```text
references/manage-yt-dlp.md
```

Cette référence n'a pas vocation à être chargée pendant une extraction normale réussie.

### État du binaire

```bash
python scripts/manage_yt_dlp.py status
```

Cette commande ne nécessite pas d'accès réseau.

### Vérifier les mises à jour

```bash
python scripts/manage_yt_dlp.py check
```

Le script compare la version locale à la dernière release officielle du canal stable.

Exemple de résultat :

```json
{
  "status": "up_to_date",
  "channel": "stable",
  "local_version": "2026.07.04",
  "latest_version": "2026.07.04"
}
```

Un autre canal peut être vérifié :

```bash
python scripts/manage_yt_dlp.py check --channel nightly
python scripts/manage_yt_dlp.py check --channel master
```

### Installer yt-dlp

```bash
python scripts/manage_yt_dlp.py install
```

Le canal `stable` est utilisé par défaut.

Autres possibilités :

```bash
python scripts/manage_yt_dlp.py install --channel nightly
python scripts/manage_yt_dlp.py install --channel master
```

Pour remplacer volontairement un binaire existant :

```bash
python scripts/manage_yt_dlp.py install --force
```

L'installation :

1. télécharge l'artefact officiel ;
2. récupère `SHA2-256SUMS` ;
3. vérifie le SHA-256 ;
4. installe le binaire dans `scripts/`.

### Mettre à jour yt-dlp

```bash
python scripts/manage_yt_dlp.py update
```

Sans option supplémentaire, le mécanisme de mise à jour intégré de `yt-dlp` conserve le canal courant.

Pour changer explicitement de canal :

```bash
python scripts/manage_yt_dlp.py update --channel stable
python scripts/manage_yt_dlp.py update --channel nightly
python scripts/manage_yt_dlp.py update --channel master
```

## Répertoires temporaires

Les environnements sandboxés peuvent interdire l'utilisation du répertoire temporaire système habituel.

Les scripts configurent donc un répertoire temporaire accessible pour les processus `yt-dlp`.

Sous Windows, ils définissent pour le sous-processus :

```text
TEMP
TMP
```

Sous Unix :

```text
TMPDIR
```

L'environnement global de la session n'est pas modifié.

## Gestion des erreurs

`youtube_transcript.py` et `manage_yt_dlp.py` utilisent des sorties structurées destinées à être interprétées par l'agent.

En cas d'échec, il faut distinguer notamment :

* absence réelle de `yt-dlp` ;
* erreur de `PATH` ;
* permissions insuffisantes ;
* restriction du sandbox ;
* accès réseau bloqué ;
* vidéo inaccessible ;
* absence de piste de sous-titres compatible ;
* incompatibilité temporaire entre YouTube et la version de `yt-dlp`.

Une mise à jour de `yt-dlp` ne doit pas être utilisée comme solution générique à toutes les erreurs.

## Codex sous Windows

Les skills utilisateur peuvent être installées sous :

```text
C:\Users\<UTILISATEUR>\.agents\skills\
```

Une installation directe du dépôt permet donc d'obtenir :

```text
C:\Users\<UTILISATEUR>\.agents\skills\youtube\
```

### Sandbox

Certains emplacements d'installation Windows, notamment ceux utilisés par WinGet ou certains alias `WindowsApps`, peuvent être accessibles depuis la session utilisateur mais bloqués dans le sandbox.

Placer `yt-dlp.exe` directement dans :

```text
youtube\scripts\
```

permet d'éviter cette dépendance à une installation système.

L'accès réseau peut toutefois lui aussi nécessiter une autorisation.

### Règles ciblées

Pour une machine personnelle et maîtrisée, des règles Codex peuvent être définies dans :

```text
C:\Users\<UTILISATEUR>\.codex\rules\default.rules
```

Exemple pour l'extraction :

```python
prefix_rule(
    pattern = [
        "python",
        "C:\\Users\\<UTILISATEUR>\\.agents\\skills\\youtube\\scripts\\youtube_transcript.py",
    ],
    decision = "allow",
    justification = "Autorise le script YouTube personnel à accéder au réseau nécessaire à l'extraction.",
)
```

Et pour la maintenance :

```python
prefix_rule(
    pattern = [
        "python",
        "C:\\Users\\<UTILISATEUR>\\.agents\\skills\\youtube\\scripts\\manage_yt_dlp.py",
    ],
    decision = "allow",
    justification = "Autorise le gestionnaire yt-dlp à vérifier, installer et mettre à jour le binaire local.",
)
```

Ces règles sont propres à la machine et ne doivent pas être intégrées au dépôt.

Il est préférable d'autoriser précisément les scripts nécessaires plutôt que l'ensemble de Python ou du répertoire des skills.

## Fichiers versionnés et locaux

Versionnés :

```text
SKILL.md
README.md
references/manage-yt-dlp.md
references/summarize-transcript.md
scripts/manage_yt_dlp.py
scripts/youtube_transcript.py
```

Non versionnés :

```text
scripts/yt-dlp.exe
scripts/yt-dlp
```

Le dépôt contient ainsi la logique permettant d'installer et de maintenir la dépendance sans versionner le binaire lui-même.
