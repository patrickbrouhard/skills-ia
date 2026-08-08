# Karakeep pour Codex

Karakeep fournit notamment ces opérations :

* `GET /api/v1/bookmarks/check-url?url=...` pour vérifier un doublon exact ;
* `POST /api/v1/bookmarks` pour ajouter une URL ;
* `GET /api/v1/bookmarks/search?q=...` pour faire une recherche plein texte ;
* `PATCH /api/v1/bookmarks/:bookmarkId` pour modifier un résumé ;
* `POST /api/v1/bookmarks/:bookmarkId/tags` pour attacher des tags.

L’ajout est idempotent : une création renvoie `201`. Si l’URL existe déjà,
Karakeep renvoie le bookmark existant avec un statut `200`, sans le modifier.

Ceci est un script minimal utilisable directement par Codex.

## Installation

Aucune bibliothèque Python externe n'est nécessaire.

Le script utilise uniquement la bibliothèque standard de Python, notamment
`urllib.request` pour les appels HTTP. Il ne dépend donc ni de `requests`,
ni de `python-dotenv`, et aucun `pip install` n'est requis.

Prérequis :

* Python 3 ;
* un accès réseau à l'instance Karakeep ;
* une clé API Karakeep valide.

Configuration :

```bash
cp .env.example .env
```

Sous PowerShell, tu peux aussi simplement copier le fichier :

```powershell
Copy-Item .env.example .env
```

Renseigne ensuite `KARAKEEP_URL` et `KARAKEEP_API_KEY` dans `.env`.

Le script charge lui-même ce fichier `.env` sans dépendance externe. Les
variables d'environnement déjà définies dans le système restent prioritaires
sur les valeurs du fichier.

Le format `.env` pris en charge couvre les cas simples utilisés ici, par
exemple :

```dotenv
KARAKEEP_URL=https://karakeep.example.com
KARAKEEP_API_KEY=xxxxxxxx
```

Le fichier `.env` contient un secret et ne doit pas être ajouté au dépôt Git.

Utilisation :

```bash
python karakeep.py check "https://example.com/article"
python karakeep.py add "https://example.com/article"
python karakeep.py search "traefik docker"
```

Ajouter une URL avec un résumé Markdown et des tags :

```bash
python karakeep.py add "https://www.youtube.com/watch?v=VIDEO_ID" \
  --summary-file summary.md \
  --tag ia \
  --tag llm
```

`--summary-file -` lit le résumé depuis l’entrée standard. Les tags ne sont
attachés qu’après une création réussie. Si le bookmark existe déjà, le script
renvoie ses données et indique si un résumé est présent, sans rien modifier.

Ajouter un résumé à un bookmark existant :

```bash
python karakeep.py set-summary BOOKMARK_ID --summary-file summary.md
```

Un résumé existant est protégé par défaut. Son remplacement doit être demandé
explicitement :

```bash
python karakeep.py set-summary BOOKMARK_ID \
  --summary-file summary.md \
  --replace
```

Le format JSON en sortie est volontaire : Codex pourra facilement interpréter le résultat sans parser du texte destiné à un humain.

Pour éviter qu’une recherche approximative ne remplace à tort la vérification des doublons, je séparerais clairement les deux mécanismes :

1. `check-url` décide si **cette URL précise** existe déjà ;
2. `search` permet à Codex de repérer des contenus similaires ou une autre URL traitant du même sujet ;
3. `add` s’appuie directement sur l’idempotence du `POST` et distingue les
   statuts HTTP `200` et `201`.

L’API utilise une authentification Bearer dans l’en-tête `Authorization`. Tu peux créer une clé dédiée dans les paramètres de Karakeep et lui donner uniquement les droits de lecture et de création de bookmarks, si ta version propose les scopes granulaires.

Dans les instructions de ton dépôt, tu peux ensuite écrire quelque chose comme :

```markdown
Pour toute opération Karakeep, utilise uniquement :

- `python karakeep/karakeep.py add "<URL>"`
- `python karakeep/karakeep.py set-summary "<ID>" --summary-file "<FICHIER>"`
- `python karakeep/karakeep.py search "<requête>"`
- `python karakeep/karakeep.py check "<URL>"`

Avant tout ajout :

1. utilise `check` lorsque l’utilisateur demande une vérification explicite ;
2. utilise directement `add` pour un ajout idempotent ;
3. ne modifie jamais automatiquement un bookmark renvoyé avec le statut
   `already_exists`.
```

La clé ne doit pas être placée dans le dépôt. Une variable d’environnement ou le trousseau du système suffit pour ce niveau de besoin, tout en gardant à l’esprit que Codex exécuté avec ton compte utilisateur pourra théoriquement y accéder.

[Search bookmarks \| Karakeep Docs](https://docs.karakeep.app/api/search-bookmarks)
[Karakeep API \| Karakeep Docs](https://docs.karakeep.app/api/karakeep-api/)
