# Skill Karakeep

Skill permettant à un agent d'ajouter, enrichir, rechercher et gérer des bookmarks dans une instance Karakeep.

Elle combine :

* l'analyse du contenu par l'agent ;
* la skill `tagging` pour la classification ;
* la skill `youtube` lorsqu'une ressource est une vidéo YouTube ;
* `scripts/karakeep.py` pour les opérations déterministes sur l'API Karakeep.

## Structure

```text
karakeep/
├── README.md
├── SKILL.md
└── scripts/
    ├── .env.example
    ├── .env
    └── karakeep.py
```

Le fichier `.env` est local et ignoré par Git.

## Principe

Le script `karakeep.py` est volontairement limité aux opérations Karakeep.

Il ne décide pas lui-même :

* comment résumer une ressource ;
* quels tags lui attribuer ;
* comment extraire le contenu d'une vidéo ou d'un article.

Ces tâches appartiennent à l'agent et aux autres skills.

Le workflow général est donc :

```text
ressource
   ↓
agent
   ├── récupère le contenu
   ├── comprend la ressource
   ├── produit un résumé
   └── appelle la skill tagging
   ↓
karakeep.py
   ├── crée le bookmark
   ├── transmet le résumé
   └── attache les tags
```

## Workflow YouTube

Pour une vidéo YouTube :

```text
URL
 ↓
skill youtube
 ├── transcription
 └── métadonnées
 ↓
résumé
 ↓
skill tagging
 ↓
karakeep.py add
 ↓
Karakeep
```

Cela évite de déterminer le résumé ou les tags uniquement à partir du titre de la vidéo.

## Prérequis

* Python 3 ;
* accès réseau à l'instance Karakeep ;
* clé API Karakeep valide.

Le script utilise uniquement la bibliothèque standard Python.

Aucun `pip install` n'est nécessaire.

## Configuration

Depuis `karakeep/scripts/`, copier :

```text
.env.example
```

vers :

```text
.env
```

Sous PowerShell :

```powershell
Copy-Item .env.example .env
```

Sous Linux/macOS :

```bash
cp .env.example .env
```

Renseigner ensuite :

```dotenv
KARAKEEP_URL=https://karakeep.example.com
KARAKEEP_API_KEY=xxxxxxxx
```

Le script cherche automatiquement :

```text
karakeep/scripts/.env
```

Les variables déjà présentes dans l'environnement du processus restent prioritaires sur celles du fichier.

Le format `.env` est interprété directement par le script sans `python-dotenv`.

## Secrets

`KARAKEEP_API_KEY` est un secret.

Ne jamais :

* versionner `.env` ;
* afficher la clé dans les logs ;
* inclure la clé dans un résumé ;
* inclure la clé dans un prompt ou un fichier de sortie.

Le `.gitignore` du dépôt ignore les fichiers `.env` tout en autorisant `.env.example`.

## Utilisation du CLI

Les exemples suivants supposent une exécution depuis la racine du dépôt.

### Vérifier une URL

```bash
python karakeep/scripts/karakeep.py check "https://example.com/article"
```

Cette commande vérifie l'existence exacte de l'URL.

### Ajouter un bookmark

```bash
python karakeep/scripts/karakeep.py add "https://example.com/article"
```

### Ajouter un résumé et des tags

```bash
python karakeep/scripts/karakeep.py add \
  "https://example.com/article" \
  --summary-file summary.md \
  --tag tech \
  --tag devops
```

Les tags transmis au script ne comportent pas le caractère `#`.

Ainsi :

```text
#tech #devops #docker
```

devient :

```text
--tag tech --tag devops --tag docker
```

### Recherche

```bash
python karakeep/scripts/karakeep.py search "traefik docker"
```

La recherche plein texte sert à retrouver des bookmarks selon leur contenu.

Elle ne remplace pas une vérification exacte d'URL.

### Modifier un résumé

```bash
python karakeep/scripts/karakeep.py set-summary \
  BOOKMARK_ID \
  --summary-file summary.md
```

Par défaut, un résumé existant est protégé.

Pour demander explicitement son remplacement :

```bash
python karakeep/scripts/karakeep.py set-summary \
  BOOKMARK_ID \
  --summary-file summary.md \
  --replace
```

## Idempotence

L'opération `add` est conçue pour être idempotente.

Le script distingue notamment :

### `created`

Le bookmark vient d'être créé.

### `already_exists`

L'URL existait déjà.

Le bookmark existant n'est pas modifié automatiquement.

### `partially_created`

Le bookmark a été créé mais une étape ultérieure, par exemple l'ajout de tags, a échoué.

L'agent ne doit pas annoncer un succès complet dans ce cas.

## Résumés

Lorsqu'un résumé est transmis avec :

```text
--summary-file
```

le fichier doit contenir uniquement le Markdown destiné au champ `Summary`.

Un fichier temporaire est généralement utilisé par l'agent puis supprimé après l'opération.

Le résumé doit être produit à partir du contenu réel de la ressource, et non simplement de son titre ou des connaissances générales du modèle.

Pour une vidéo YouTube, les règles de résumé de la skill `youtube` s'appliquent.

## Tags

Les tags sont déterminés par la skill `tagging`.

La taxonomie n'est volontairement pas dupliquée dans la skill Karakeep.

Cela permet d'utiliser les mêmes conventions pour :

* Karakeep ;
* Obsidian ;
* d'autres systèmes de gestion de connaissances.

## Sorties JSON

Le CLI retourne des résultats structurés en JSON.

Ce choix permet à l'agent de distinguer précisément :

* création réussie ;
* ressource déjà existante ;
* création partielle ;
* erreur.

L'agent n'a donc pas besoin d'analyser du texte destiné à un humain.

## Sandbox et accès réseau

L'accès à une instance Karakeep peut être bloqué par le sandbox même si l'instance est accessible depuis la machine hôte.

Il faut alors distinguer :

* problème réel de connexion ;
* mauvaise URL ;
* clé API invalide ;
* restriction réseau du sandbox.

Pour un environnement personnel maîtrisé, une règle Codex ciblée peut autoriser uniquement le script Karakeep.

Exemple sous Windows :

```python
prefix_rule(
    pattern = [
        "python",
        "C:\\Users\\<UTILISATEUR>\\.agents\\skills\\karakeep\\scripts\\karakeep.py",
    ],
    decision = "allow",
    justification = "Autorise le script Karakeep personnel à accéder à l'API Karakeep.",
)
```

Cette configuration est propre à la machine et ne doit pas être versionnée dans le dépôt.

## API utilisées

Le script utilise notamment les opérations Karakeep nécessaires à :

* la vérification d'une URL ;
* la création d'un bookmark ;
* la recherche ;
* la lecture d'un bookmark ;
* la modification du résumé ;
* l'ajout de tags.

L'authentification utilise une clé API transmise avec un en-tête Bearer.

## Philosophie

La skill suit une séparation volontaire des responsabilités :

```text
agent
→ comprend et orchestre

youtube / lecture Web
→ récupère le contenu

tagging
→ classifie

karakeep.py
→ applique les modifications déterministes via l'API
```

Cette modularité permet de réutiliser chaque skill indépendamment et évite de créer des scripts spécialisés pour chaque combinaison de workflow.
