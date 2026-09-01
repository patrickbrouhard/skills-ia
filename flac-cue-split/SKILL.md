---
name: flac-cue-split
description: Découper un album constitué d'un FLAC unique et d'un CUE en pistes FLAC séparées, vérifier que le PCM concaténé est bit-perfect, puis ranger les sources dans backup. Utiliser pour une découpe d'album locale sous Linux ou Windows avec WSL ; ne pas utiliser pour convertir des formats audio ou traiter plusieurs images-disques à la fois.
---

# FLAC CUE Split

Automatiser la découpe tout en laissant les opérations audio et les noms de fichiers à des scripts déterministes. La garantie porte sur l'identité du PCM décodé : `shnsplit -o flac` réencode le flux FLAC sans perte, mais ne modifie aucun échantillon audio.

## Déroulement

1. Inspecter le dossier demandé sans le modifier. Il doit contenir exactement un FLAC et un CUE à sa racine, au moins deux pistes `AUDIO`, aucun dossier `backup`, et aucun nom de piste cible déjà présent.
2. Choisir la source des titres :
   - utiliser les `TITLE` de chaque piste du CUE par défaut ;
   - utiliser un `tracks.txt` présent à la racine s'il existe ;
   - si l'utilisateur fournit une release MusicBrainz ou demande une vérification en ligne, relever les titres de cette release, sélectionner le bon disque grâce au nombre de pistes et aux indications du CUE, signaler toute ambiguïté, puis écrire une tracklist UTF-8 temporaire et la passer avec `--tracklist` ;
   - ne jamais inventer un titre manquant. Demander une source fiable si le CUE et la tracklist ne suffisent pas.
3. Montrer brièvement les fichiers source, le nombre de pistes et la source des titres. Une demande explicite de « découper », « commencer » ou équivalent autorise l'exécution complète ; une simple demande d'analyse ou de faisabilité reste en lecture seule.
4. Exécuter le script adapté à la plateforme.
5. N'annoncer le succès que si le script affiche `SUCCESS`, le même SHA-256 PCM pour la source et les pistes, et si le dossier final contient les pistes attendues ainsi que `backup`.

Le script prépare les pistes dans un répertoire temporaire du dossier de l'album. Il teste le FLAC source, valide les points du CUE, teste chaque piste, compare les PCM concaténés, nettoie les noms pour Windows et Linux, puis effectue la mise en place finale. En cas d'échec avant la finalisation, il ne déplace pas les originaux. En cas d'échec pendant la finalisation, il tente un rollback et conserve le répertoire temporaire pour diagnostic.

## Exécution

Sous Linux :

```bash
bash <skill-dir>/scripts/split_flac_cue.sh [--tracklist /chemin/tracks.txt] /chemin/album
```

Sous Windows, utiliser PowerShell 7 et le pont WSL :

```powershell
& '<skill-dir>\scripts\Invoke-FlacCueSplit.ps1' -AlbumPath '<dossier>' -Distro 'Ubuntu-24.04'
```

Ajouter `-TracklistPath '<fichier>'` lorsqu'une tracklist contrôlée doit remplacer les titres du CUE. Le wrapper accepte un dossier Windows ou un chemin UNC `\\wsl.localhost\<distribution>\...` appartenant à la distribution indiquée.

Les commandes Linux requises sont `cuebreakpoints`, `shnsplit`, `flac`, `sha256sum`, `python3` et les utilitaires GNU usuels. Sur Ubuntu/WSL, elles proviennent normalement de `cuetools`, `shntool` et `flac`. Vérifier leur présence, mais ne pas installer de paquet sans demande ou autorisation explicite de l'utilisateur.

## Résultat et limites

- Les pistes sont nommées `NN - Titre.flac` à la racine de l'album.
- Le FLAC, le CUE, le LOG de même nom s'il existe, et un éventuel `tracks.txt` utilisé depuis la racine sont déplacés dans `backup` seulement après toutes les vérifications.
- Ne pas écraser un fichier, réutiliser un `backup` existant, deviner le bon disque MusicBrainz, ni substituer une découpe `ffmpeg -c copy` : la copie de trames n'est pas toujours alignée exactement sur les index du CUE.
- Ne pas promettre l'identité binaire des fichiers FLAC. Promettre l'identité des échantillons PCM, démontrée par le hash, ainsi que l'absence de conversion avec perte.
