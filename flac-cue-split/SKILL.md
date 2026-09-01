---
name: flac-cue-split
description: Découper un album constitué d'un FLAC unique et d'un CUE en pistes FLAC séparées, vérifier que le PCM concaténé est bit-perfect, puis ranger les sources dans backup. Utiliser pour une découpe d'album locale sous Linux ou Windows avec WSL ; ne pas utiliser pour convertir des formats audio ou traiter plusieurs images-disques à la fois.
---

# FLAC CUE Split

Automatiser la découpe tout en séparant la résolution éditoriale, confiée à l'IA, des opérations audio et des noms de fichiers, confiés à des scripts déterministes. La garantie porte sur l'identité du PCM décodé : `shnsplit -o flac` réencode le flux FLAC sans perte, mais ne modifie aucun échantillon audio.

Le CUE est la source de vérité technique pour les pistes et leurs index de découpe. Ses champs éditoriaux comme `TITLE` et `PERFORMER` ne sont que des indices : ils ne déterminent jamais automatiquement les noms de sortie.

## Déroulement

1. Inspecter le dossier demandé sans le modifier. Il doit contenir exactement un FLAC et un CUE à sa racine, au moins deux pistes `AUDIO` présentes dans le CUE, aucun dossier `backup` contenant des fichiers, et aucun nom de piste cible déjà présent.
2. Déterminer les titres des pistes selon cette hiérarchie :
   - les instructions explicites de l'utilisateur priment toujours pour les informations éditoriales. Si l'utilisateur fournit les titres, une tracklist ou une source précise, les titres doivent en provenir ;
   - un lien vers une release MusicBrainz désigne cette release comme source de référence. Pour une release multi-disques, identifier le bon medium à l'aide du nombre de pistes, de leur ordre, des durées déduites des index du CUE et des autres indices disponibles ; signaler toute ambiguïté réelle ;
   - sans source imposée, identifier l'album ou la release à partir du nom du dossier, du nom du FLAC, des métadonnées et titres du CUE, puis recouper les titres lorsqu'une source fiable est accessible ;
   - les `TITLE` du CUE peuvent servir d'indices et de solution de repli lorsqu'ils sont complets et cohérents, mais une anomalie, une troncature ou une divergence doit être résolue avant la découpe ;
   - ne jamais inventer ni corriger silencieusement un titre. Si la résolution reste incertaine, présenter la tracklist proposée, préciser ses sources et demander confirmation à l'utilisateur.
3. Présenter brièvement le FLAC, le CUE, le nombre de pistes, la tracklist résolue et sa provenance. Une demande explicite de « découper », « commencer » ou équivalent autorise l'exécution lorsque la résolution est suffisamment certaine ; une ambiguïté réelle nécessite une confirmation. Une simple demande d'analyse ou de faisabilité reste en lecture seule.
4. Écrire les titres résolus, un par ligne, dans une tracklist UTF-8 temporaire située hors du dossier de l'album lorsque c'est possible. La transmettre obligatoirement au script avec `--tracklist`, puis supprimer ce fichier temporaire après succès ou échec. Ne jamais rechercher automatiquement un fichier conventionnel dans le dossier de l'album.
5. Exécuter le script adapté à la plateforme.
6. N'annoncer le succès que si le script affiche `SUCCESS`, le même SHA-256 PCM pour la source et les pistes, et si le dossier final contient les pistes attendues ainsi que `backup`.

Le script prépare les pistes dans un répertoire temporaire du dossier de l'album. Il teste le FLAC source, valide les points du CUE, teste chaque piste, compare les PCM concaténés, nettoie les noms pour Windows et Linux, puis effectue la mise en place finale. En cas d'échec avant la finalisation, il ne déplace pas les originaux. En cas d'échec pendant la finalisation, il tente un rollback et conserve le répertoire temporaire pour diagnostic.

## Exécution

Sous Linux :

```bash
bash <skill-dir>/scripts/split_flac_cue.sh --tracklist /chemin/tracklist-temporaire.txt /chemin/album
```

Sous Windows, utiliser PowerShell 7 et le pont WSL :

```powershell
& '<skill-dir>\scripts\Invoke-FlacCueSplit.ps1' -AlbumPath '<dossier>' -TracklistPath '<tracklist-temporaire>' -Distro 'Ubuntu-24.04'
```

`--tracklist` et `-TracklistPath` sont obligatoires. La tracklist est une interface technique entre l'IA et les scripts, pas un fichier utilisateur conventionnel. Le wrapper accepte un dossier Windows ou un chemin UNC `\\wsl.localhost\<distribution>\...` appartenant à la distribution indiquée.

Les commandes Linux requises sont `cuebreakpoints`, `shnsplit`, `flac`, `sha256sum`, `python3` et les utilitaires GNU usuels. Sur Ubuntu/WSL, elles proviennent normalement de `cuetools`, `shntool` et `flac`. Vérifier leur présence, mais ne pas installer de paquet sans demande ou autorisation explicite de l'utilisateur.

## Résultat et limites

- Les pistes sont nommées `NN - Titre.flac` à la racine de l'album.
- Le FLAC, le CUE et le LOG de même nom s'il existe sont déplacés dans `backup` seulement après toutes les vérifications. Un dossier `backup` vide peut être réutilisé ; un fichier nommé `backup` ou un dossier non vide doit provoquer un refus.
- La tracklist technique n'est ni déplacée dans `backup`, ni conservée comme élément de l'album.
- Ne pas écraser un fichier, deviner le bon disque MusicBrainz, ni substituer une découpe `ffmpeg -c copy` : la copie de trames n'est pas toujours alignée exactement sur les index du CUE.
- Ne pas promettre l'identité binaire des fichiers FLAC. Promettre l'identité des échantillons PCM, démontrée par le hash, ainsi que l'absence de conversion avec perte.
