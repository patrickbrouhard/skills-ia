---
name: flac-cue-split
description: Découper un album constitué d'un FLAC unique et d'un CUE en pistes FLAC séparées, vérifier que le PCM concaténé est bit-perfect, puis ranger les sources dans backup. Utiliser pour une découpe d'album locale sous Linux ou Windows avec WSL ; ne pas utiliser pour convertir des formats audio ou traiter plusieurs images-disques à la fois.
---

# FLAC CUE Split

Automatiser la validation et la découpe tout en séparant les responsabilités : l'IA identifie le disque, juge la cohérence des sources et construit les noms finaux ; des scripts déterministes valident ces noms et réalisent les opérations audio. La garantie porte sur l'identité du PCM décodé : `shnsplit -o flac` réencode le flux FLAC sans perte, mais ne modifie aucun échantillon audio.

## Déroulement

1. Effectuer une validation pure, sans modifier le dossier. Il doit contenir exactement un FLAC et un CUE à sa racine ; le chemin `backup` doit être absent ou être un dossier vide. Identifier la release ou le medium désigné par l'utilisateur, puis vérifier la structure du CUE et sa concordance avec cette source. Le nombre de pistes doit correspondre exactement. Comparer souplement les métadonnées éditoriales, mais traiter une TOC exacte comme une preuve beaucoup plus forte. Lire [references/cue-validation.md](references/cue-validation.md) pour les critères, le calcul des secteurs et les conditions d'arrêt.
2. Si une divergence significative ou une ambiguïté subsiste, présenter les éléments concordants et divergents, puis demander à l'utilisateur quoi faire. Ne créer aucun fichier et ne lancer aucune découpe.
3. Si la validation passe, construire directement la liste des noms de fichiers finaux. Les instructions explicites de l'utilisateur et la source qu'il désigne priment pour leur formulation. Les noms doivent déjà inclure leur numéro et l'extension `.flac` (exemple : `01 - Titre.flac`) et ne doivent pas contenir de caractères invalides sur Windows (exemple: `05 - Titre: part I.flac` est invalide, remplacer par `05 - Titre - part I.flac`).
4. Écrire ces noms, un par ligne, dans un manifeste UTF-8 temporaire situé hors du dossier de l'album lorsque c'est possible. Exécuter `validate_track_filenames.py` avec le nombre de pistes attendu. S'il signale des erreurs, corriger les noms et recommencer jusqu'à obtenir `OK` ; ne jamais contourner, nettoyer ou tronquer silencieusement un nom.
5. Présenter brièvement l'identification retenue, le niveau de confiance, les contrôles effectués et les noms finaux. Une demande explicite de « découper », « commencer » ou équivalent autorise l'exécution lorsque la validation est concluante.
6. Exécuter le script adapté à la plateforme en lui passant obligatoirement le manifeste avec `--filenames`. Supprimer le manifeste temporaire après succès ou échec.
7. N'annoncer le succès que si le script affiche `SUCCESS`, le même SHA-256 PCM pour la source et les pistes, et si le dossier final contient les pistes attendues ainsi que `backup`.

Le script Bash revalide le manifeste sans le modifier, prépare les pistes dans un répertoire temporaire du dossier de l'album, teste le FLAC source, valide les points du CUE, teste chaque piste, compare les PCM concaténés, puis effectue la mise en place finale. En cas d'échec avant la finalisation, il ne déplace pas les originaux. En cas d'échec pendant la finalisation, il tente un rollback et conserve le répertoire temporaire pour diagnostic.

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

- Les pistes sont nommées `NN - Titre.flac` à la racine de l'album.
- Le FLAC, le CUE et le LOG de même nom s'il existe sont déplacés dans `backup` seulement après toutes les vérifications. Un dossier `backup` vide peut être réutilisé ; un fichier nommé `backup` ou un dossier non vide doit provoquer un refus.
- Le manifeste temporaire n'est ni déplacé dans `backup`, ni conservé comme élément de l'album.
- Ne pas écraser un fichier, deviner le bon disque MusicBrainz, ni substituer une découpe `ffmpeg -c copy` : la copie de trames n'est pas toujours alignée exactement sur les index du CUE.
- Ne pas promettre l'identité binaire des fichiers FLAC. Promettre l'identité des échantillons PCM, démontrée par le hash, ainsi que l'absence de conversion avec perte.
