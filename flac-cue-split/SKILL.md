---
name: flac-cue-split
description: Découper un album mono-disque ou multi-disques constitué d'une image FLAC et d'un CUE par disque, vérifier que chaque PCM concaténé est bit-perfect, puis ranger les sources dans backup. Utiliser pour une découpe d'album locale sous Linux ou Windows avec WSL ; ne pas utiliser pour convertir des formats audio ou traiter plusieurs images dans un même dossier de disque.
---

# FLAC CUE Split

Automatiser la validation et la découpe tout en séparant les responsabilités : l'IA identifie la release et ses mediums, juge la cohérence des sources et construit les noms finaux ; des scripts déterministes valident ces noms et réalisent les opérations audio, un dossier de disque à la fois. La garantie porte sur l'identité du PCM décodé : `shnsplit -o flac` réencode le flux FLAC sans perte, mais ne modifie aucun échantillon audio.

## Déroulement

1. Effectuer une validation pure, sans modifier les dossiers. Déterminer si le chemin demandé désigne un dossier disque contenant exactement un FLAC et un CUE à sa racine, ou un album multi-disques dont chaque medium possède son propre dossier conforme. Dans chaque dossier disque, le chemin `backup` doit être absent ou être un dossier vide. Lire [references/multi-disc.md](references/multi-disc.md) seulement lorsque plusieurs images-disques appartiennent à la même release.
2. Identifier la release ou le medium désigné par l'utilisateur, puis vérifier chaque CUE et sa concordance avec cette source. Le nombre de pistes doit correspondre exactement pour chaque medium. Comparer souplement les métadonnées éditoriales, mais traiter une TOC exacte comme une preuve beaucoup plus forte. Lire [references/cue-validation.md](references/cue-validation.md) pour les critères, le calcul des secteurs et les conditions d'arrêt.
3. Si une divergence significative ou une ambiguïté subsiste, présenter les éléments concordants et divergents, puis demander à l'utilisateur quoi faire. Pour un album multi-disques, valider et apparier tous les mediums avant de créer un manifeste ou de lancer une découpe.
4. Si la validation passe, construire directement une liste de noms de fichiers finaux par disque. Les instructions explicites de l'utilisateur et la source qu'il désigne priment pour leur formulation. Les noms doivent déjà inclure leur numéro, recommençant à `01` dans chaque dossier disque, et l'extension `.flac` (exemple : `01 - Titre.flac`) ; ils ne doivent pas contenir de caractères invalides sur Windows (exemple: `05 - Titre: part I.flac` est invalide, remplacer par `05 - Titre - part I.flac`).
5. Pour chaque disque, écrire ces noms, un par ligne, dans un manifeste UTF-8 temporaire situé hors de l'album lorsque c'est possible. Exécuter `validate_track_filenames.py` avec le nombre de pistes de ce disque. S'il signale des erreurs, corriger les noms et recommencer jusqu'à obtenir `OK` ; ne jamais contourner, nettoyer ou tronquer silencieusement un nom.
6. Présenter brièvement l'identification retenue, l'association entre dossiers et mediums, le niveau de confiance, les contrôles effectués et les noms finaux. Une demande explicite de « découper », « commencer » ou équivalent autorise l'exécution lorsque la validation de tous les disques concernés est concluante.
7. Exécuter le script adapté à la plateforme séparément pour chaque dossier disque, en lui passant obligatoirement son manifeste avec `--filenames`. Traiter les disques dans l'ordre des mediums de la source. Supprimer chaque manifeste temporaire après succès ou échec.
8. Arrêter au premier échec et ne pas commencer les disques suivants. Les transactions étant indépendantes, ne pas annuler un disque déjà terminé ; signaler explicitement ce succès partiel. N'annoncer le succès global que si chaque invocation affiche `SUCCESS`, le même SHA-256 PCM pour sa source et ses pistes, et si chaque dossier final contient ses pistes attendues ainsi que `backup`.

Le script Bash reste volontairement mono-disque. Il revalide le manifeste sans le modifier, prépare les pistes dans un répertoire temporaire du dossier du disque, teste le FLAC source, valide les points du CUE, teste chaque piste, compare les PCM concaténés, puis effectue la mise en place finale. En cas d'échec avant la finalisation, il ne déplace pas les originaux. En cas d'échec pendant la finalisation, il tente un rollback et conserve le répertoire temporaire pour diagnostic. Il n'existe pas de transaction ni de rollback couvrant plusieurs disques.

## Validation des noms avant exécution

```bash
python3 <skill-dir>/scripts/validate_track_filenames.py \
  --filenames /chemin/noms-finaux.txt \
  --expected-count 21
```

Le validateur doit afficher `OK`. Il ne corrige jamais les noms : il signale toutes les violations avec leur numéro de ligne.

## Exécution

Sous Linux :

```bash
bash <skill-dir>/scripts/split_flac_cue.sh --filenames /chemin/noms-finaux.txt /chemin/album
```

Sous Windows, utiliser PowerShell 7 et le pont WSL :

```powershell
& '<skill-dir>\scripts\Invoke-FlacCueSplit.ps1' -AlbumPath '<dossier>' -FilenamesPath '<noms-finaux>' -Distro 'Ubuntu-24.04'
```

`--filenames` et `-FilenamesPath` sont obligatoires. Le manifeste contient des noms finaux, pas des titres à transformer. Le wrapper accepte un dossier Windows ou un chemin UNC `\\wsl.localhost\<distribution>\...` appartenant à la distribution indiquée.

Les commandes Linux requises sont `cuebreakpoints`, `shnsplit`, `flac`, `sha256sum`, `python3` et les utilitaires GNU usuels. Sur Ubuntu/WSL, elles proviennent normalement de `cuetools`, `shntool` et `flac`. Vérifier leur présence, mais ne pas installer de paquet sans demande ou autorisation explicite de l'utilisateur.

## Résultat et limites

- Les pistes sont nommées `NN - Titre.flac` à la racine de chaque dossier disque.
- Le FLAC, le CUE et le LOG de même nom s'il existe sont déplacés dans `backup` seulement après toutes les vérifications. Un dossier `backup` vide peut être réutilisé ; un fichier nommé `backup` ou un dossier non vide doit provoquer un refus.
- Le manifeste temporaire n'est ni déplacé dans `backup`, ni conservé comme élément de l'album.
- Les dossiers sans paire FLAC/CUE, par exemple `Covers`, restent inchangés.
- Ne pas écraser un fichier, deviner le bon disque MusicBrainz, ni substituer une découpe `ffmpeg -c copy` : la copie de trames n'est pas toujours alignée exactement sur les index du CUE.
- Ne pas promettre l'identité binaire des fichiers FLAC. Promettre l'identité des échantillons PCM, démontrée par le hash, ainsi que l'absence de conversion avec perte.
