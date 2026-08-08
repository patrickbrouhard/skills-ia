---
name: karakeep
description: Ajouter, enrichir, rechercher ou gérer des bookmarks dans Karakeep, notamment en produisant automatiquement résumés et tags à partir du contenu d'une ressource.
---

# Karakeep

Utiliser cette skill lorsqu'une tâche concerne l'ajout, l'enrichissement, la recherche ou la gestion de contenus dans Karakeep.

L'objectif principal est de permettre à l'utilisateur de fournir une ressource, généralement une URL, et de l'enregistrer dans Karakeep avec des métadonnées utiles telles qu'un résumé et des tags pertinents.

## Outil Karakeep

Pour les opérations sur Karakeep, utiliser :

`scripts/karakeep.py`

Le script communique avec l'API Karakeep et retourne ses résultats sous forme de JSON.

Ne pas effectuer directement les appels HTTP à l'API lorsque le script fournit déjà l'opération nécessaire.

## Principe général

Lorsqu'un utilisateur demande d'ajouter une ressource à Karakeep :

1. identifier le type de ressource ;
2. obtenir suffisamment de contenu pour comprendre réellement la ressource ;
3. produire un résumé si le contenu permet d'en produire un utile ;
4. déterminer les tags pertinents à partir du contenu ;
5. ajouter la ressource à Karakeep avec son résumé et ses tags ;
6. interpréter le JSON retourné par le script ;
7. informer succinctement l'utilisateur du résultat.

Ne pas choisir les tags uniquement à partir du titre lorsqu'un contenu plus complet peut être obtenu.

## Workflow pour une vidéo YouTube

Lorsqu'une URL pointe vers une vidéo YouTube :

1. utiliser la skill `youtube` pour récupérer la transcription et les métadonnées ;
2. produire un résumé à partir de cette transcription conformément aux règles de la skill `youtube` ;
3. utiliser la skill `tagging` pour choisir les tags à partir du contenu réel de la vidéo ;
4. enregistrer le résumé dans un fichier temporaire Markdown ;
5. appeler `scripts/karakeep.py add` avec :

   * l'URL ;
   * le fichier contenant le résumé ;
   * chacun des tags sélectionnés ;
6. lire le JSON retourné et vérifier l'état de l'opération.

Exemple conceptuel :

```bash
python scripts/karakeep.py add "<URL>" \
  --summary-file "<SUMMARY_FILE>" \
  --tag tech \
  --tag ia \
  --tag llm
```

Les tags transmis au CLI ne doivent pas inclure le caractère `#`.

## Workflow pour un article ou une page Web

Lorsqu'une URL pointe vers un article ou une page dont le contenu est accessible :

1. récupérer et lire le contenu pertinent de la page ;
2. identifier le contenu principal en ignorant autant que possible navigation, publicité et éléments périphériques ;
3. produire un résumé fidèle au contenu ;
4. utiliser la skill `tagging` pour choisir les tags ;
5. ajouter l'URL à Karakeep avec le résumé et les tags.

Ne pas utiliser les métadonnées seules lorsqu'il est possible de consulter le contenu principal.

## Tagging

Pour toute génération de tags, appliquer la skill `tagging`.

Ne pas reproduire ici sa taxonomie.

Les tags doivent être déterminés à partir du contenu analysé et respecter les conventions définies par cette skill.

Avant de les transmettre à `karakeep.py`, supprimer uniquement le préfixe `#`.

Exemple :

```text
#tech #dev #python
```

devient :

```bash
--tag tech --tag dev --tag python
```

## Résumé

Le champ `Summary` doit contenir un résumé utile du contenu, et non :

* une simple reformulation du titre ;
* une description générique de la ressource ;
* une explication du travail effectué par l'IA ;
* des informations inventées à partir des connaissances générales du modèle.

Pour YouTube, suivre les règles de résumé de la skill `youtube`.

Pour les autres ressources, adapter la longueur et la structure du résumé à la richesse du contenu en conservant les idées, arguments, résultats, nuances et conclusions réellement importants.

Utiliser Markdown lorsque cela améliore la lisibilité.

## Création du bookmark

Pour créer un bookmark enrichi :

```bash
python scripts/karakeep.py add "<URL>" \
  --summary-file "<SUMMARY_FILE>" \
  --tag <TAG>
```

Répéter `--tag` pour chaque tag.

Préférer une seule opération `add` contenant dès le départ le résumé et les tags plutôt qu'une succession d'opérations séparées lorsque toutes les informations sont déjà disponibles.

## Idempotence et bookmarks existants

L'opération `add` est idempotente.

Interpréter notamment les états suivants :

### `created`

Le bookmark vient d'être créé.

Vérifier que :

* le résumé a été inclus lorsqu'il était demandé ;
* les tags ont été correctement attachés.

### `already_exists`

Le bookmark existait déjà.

Ne pas modifier automatiquement son résumé ou ses tags.

Informer l'utilisateur que la ressource était déjà présente.

Une modification d'un bookmark existant doit être explicitement demandée ou clairement autorisée par la tâche.

### `partially_created`

Le bookmark a été créé, mais une étape ultérieure, par exemple l'ajout des tags, a échoué.

Ne pas annoncer un succès complet.

Préciser quelle partie de l'opération a réussi et laquelle a échoué.

## Modification du résumé

Lorsqu'un résumé doit être ajouté à un bookmark existant :

```bash
python scripts/karakeep.py set-summary "<BOOKMARK_ID>" \
  --summary-file "<SUMMARY_FILE>"
```

Ne pas remplacer automatiquement un résumé existant.

Utiliser `--replace` uniquement lorsque l'utilisateur a explicitement demandé ou autorisé son remplacement.

## Vérification d'une URL

Utiliser :

```bash
python scripts/karakeep.py check "<URL>"
```

lorsqu'une vérification explicite de l'existence du bookmark est nécessaire avant une autre décision.

Il n'est pas nécessaire d'effectuer systématiquement cette vérification avant `add`, puisque `add` est lui-même idempotent.

## Recherche

Utiliser :

```bash
python scripts/karakeep.py search "<REQUÊTE>"
```

pour rechercher des bookmarks existants.

Une recherche approximative ne remplace pas une vérification exacte d'URL.

## Fichiers temporaires

Lorsqu'un résumé doit être transmis à `karakeep.py` :

* utiliser un fichier temporaire dédié ;
* y écrire uniquement le contenu destiné au champ `Summary` ;
* ne pas y inclure de commentaires techniques ou de raisonnement interne ;
* supprimer le fichier temporaire après utilisation lorsque l'environnement et le workflow le permettent.

## Gestion des erreurs

Toujours interpréter le code de sortie et le JSON retourné par `karakeep.py`.

En cas d'erreur :

* ne pas prétendre que le bookmark a été créé ;
* conserver la distinction entre création échouée et création partielle ;
* présenter à l'utilisateur la cause utile de l'échec ;
* ne pas relancer automatiquement une opération susceptible de modifier des données si son état est incertain.

## Secrets

Ne jamais :

* afficher la clé API Karakeep ;
* copier la clé dans un prompt, un résumé ou un fichier de sortie ;
* ajouter le fichier `.env` au dépôt ;
* inclure les secrets dans les logs destinés à l'utilisateur.

Utiliser la configuration déjà prévue par le script.

## Réponse à l'utilisateur

Après une opération réussie, rester concis.

Indiquer au minimum :

* si le bookmark a été créé ou existait déjà ;
* le titre de la ressource s'il est disponible ;
* les tags effectivement utilisés.

Ne recopier le résumé complet que si l'utilisateur le demande.
