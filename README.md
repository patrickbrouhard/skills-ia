# Skills IA

Collection personnelle de skills pour agents IA, conçues pour automatiser des workflows récurrents tout en séparant clairement :

* les opérations déterministes, confiées à des scripts ;
* l'interprétation et l'orchestration, confiées à l'agent ;
* les instructions spécialisées, chargées uniquement lorsqu'elles sont nécessaires.

Les skills sont principalement destinées à être utilisées avec Codex et un environnement compatible avec les skills placées dans `~/.agents/skills`.

## Skills disponibles

### `youtube`

Extrait et analyse le contenu d'une vidéo YouTube à partir de sa transcription.

Principales capacités :

* récupération des métadonnées ;
* extraction des sous-titres ;
* normalisation de la transcription ;
* résumé du contenu ;
* maintenance locale de `yt-dlp`.

La skill utilise `yt-dlp` pour obtenir les métadonnées et identifier la piste de sous-titres, mais ne télécharge pas la vidéo.

Voir : [`youtube/README.md`](youtube/README.md)

### `tagging`

Produit des tags cohérents à partir du contenu réel d'une ressource.

La classification repose sur une taxonomie hiérarchique avec :

* domaines racines ;
* relations parent/enfant ;
* croisements entre plusieurs domaines ;
* tags spécialisés ;
* tags transversaux comme `actualité` ou `tutoriel`.

Les taxonomies détaillées sont chargées uniquement lorsqu'elles sont nécessaires.

Exemples :

```text
#tech #dev #python
#tech #devops #docker
#tech #ia #llm
#religion #christianisme #orthodoxie
#philosophie #épistémologie
```

### `karakeep`

Ajoute, enrichit, recherche et gère des bookmarks dans une instance Karakeep.

Lorsqu'une ressource est ajoutée, la skill peut orchestrer d'autres skills afin de :

1. récupérer le contenu réel ;
2. le comprendre ;
3. produire un résumé ;
4. produire les tags avec `tagging` ;
5. créer le bookmark enrichi dans Karakeep.

Pour une vidéo YouTube, elle s'appuie notamment sur la skill `youtube`.

Voir : [`karakeep/README.md`](karakeep/README.md)

## Architecture

Le dépôt suit autant que possible le principe suivant :

```text
agent
├── comprend la demande
├── choisit le workflow
├── interprète le contenu
└── orchestre les outils

scripts
├── effectuent les opérations déterministes
├── communiquent avec les API
├── manipulent les données
└── retournent des résultats structurés

references
└── contiennent les instructions spécialisées chargées uniquement si nécessaire
```

Une skill peut donc contenir :

```text
skill/
├── SKILL.md
├── README.md
├── references/
└── scripts/
```

`SKILL.md` contient les instructions nécessaires au fonctionnement de l'agent.

Les fichiers placés dans `references/` permettent de conserver les instructions spécialisées hors du chemin normal d'exécution. Ils ne doivent être consultés que lorsqu'ils sont pertinents pour la tâche.

Les scripts privilégient les sorties structurées, notamment JSON, afin que l'agent puisse interpréter leur résultat sans analyser du texte destiné à un humain.

## Structure actuelle

```text
skills-ia/
├── README.md
├── tagging/
│   ├── SKILL.md
│   └── taxonomy/
├── youtube/
│   ├── README.md
│   ├── SKILL.md
│   ├── references/
│   │   ├── manage-yt-dlp.md
│   │   └── summarize-transcript.md
│   └── scripts/
│       ├── manage_yt_dlp.py
│       └── youtube_transcript.py
└── karakeep/
    ├── README.md
    ├── SKILL.md
    └── scripts/
        ├── .env.example
        └── karakeep.py
```

Certains fichiers nécessaires localement sont volontairement ignorés par Git, notamment :

```text
youtube/scripts/yt-dlp.exe
youtube/scripts/yt-dlp
karakeep/scripts/.env
```

## Installation

### Installation directe comme dépôt de travail

Le dépôt peut être cloné directement dans le répertoire des skills utilisateur :

```powershell
git clone https://github.com/patrickbrouhard/skills-ia.git "$HOME\.agents\skills"
```

Cette organisation permet d'utiliser directement le même répertoire :

* comme dépôt Git ;
* comme répertoire de travail dans VS Code ;
* comme installation active des skills.

Les modifications apportées aux fichiers sont ainsi immédiatement visibles par l'agent.

Sous Linux ou macOS, le principe est identique :

```bash
git clone https://github.com/patrickbrouhard/skills-ia.git ~/.agents/skills
```

## Dépendances

Les scripts du dépôt privilégient la bibliothèque standard Python afin de limiter les dépendances et les problèmes d'environnement.

Prérequis généraux :

* Python 3 ;
* accès réseau lorsque l'opération le nécessite.

Certaines skills ont leurs propres dépendances :

* `youtube` : `yt-dlp`, de préférence installé localement à la skill ;
* `karakeep` : URL de l'instance et clé API Karakeep.

Voir les README spécifiques pour leur installation.

## Secrets et fichiers locaux

Les secrets ne doivent jamais être versionnés.

Le `.gitignore` exclut notamment :

```text
.env
.env.*
*.key
*.pem
credentials.json
secrets.json
```

tout en autorisant les modèles :

```text
.env.example
```

Le binaire local `yt-dlp` est également ignoré afin de ne pas versionner un exécutable spécifique à la plateforme.

## Sandbox et permissions

Certains environnements d'agents exécutent les commandes dans un sandbox pouvant restreindre :

* l'accès réseau ;
* certains chemins du système ;
* l'exécution de programmes ;
* les répertoires temporaires.

Les scripts du projet doivent autant que possible distinguer :

* une dépendance absente ;
* un problème de `PATH` ;
* une erreur de permissions ;
* un blocage du sandbox ;
* une erreur réseau réelle.

Les règles d'autorisation propres à une machine, comme les règles Codex de `~/.codex/rules/default.rules`, ne sont pas versionnées dans ce dépôt.

Lorsqu'une règle est nécessaire, elle doit être aussi ciblée que possible sur le script concerné.

## Principes du projet

Quelques principes guident le développement des skills :

* ne pas dupliquer dans l'agent une opération qu'un script peut effectuer de manière déterministe ;
* ne pas installer automatiquement une dépendance système pour contourner un problème de sandbox ou de `PATH` ;
* ne charger les références spécialisées que lorsqu'elles sont réellement nécessaires ;
* préférer une sortie JSON pour les scripts destinés principalement à être consommés par un agent ;
* préserver l'idempotence lorsqu'une opération peut modifier des données ;
* ne jamais exposer de secrets dans les prompts, logs ou sorties ;
* garder les skills modulaires afin qu'elles puissent être combinées dans différents workflows.

## Licence

Projet personnel.

Aucune licence particulière n'est actuellement définie.
