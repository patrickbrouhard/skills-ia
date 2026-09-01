#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
NAME_HELPER="$SCRIPT_DIR/build_track_filenames.py"
TRACKLIST=""

info() { printf '\n==> %s\n' "$*"; }
warn() { printf '\nAVERTISSEMENT: %s\n' "$*" >&2; }
die()  { printf '\nERREUR: %s\n' "$*" >&2; exit 1; }

usage() {
    cat <<'EOF'
Usage: split_flac_cue.sh --tracklist FICHIER DOSSIER_ALBUM

Découpe l'unique FLAC selon l'unique CUE, vérifie le PCM bit-perfect,
installe les pistes à la racine et déplace les sources dans backup/.
EOF
}

while (($#)); do
    case "$1" in
        --tracklist)
            (($# >= 2)) || die "--tracklist requiert un chemin."
            TRACKLIST="$2"
            shift 2
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        --)
            shift
            break
            ;;
        -*)
            die "Option inconnue : $1"
            ;;
        *)
            break
            ;;
    esac
done

(($# == 1)) || { usage >&2; exit 2; }
[[ -n "$TRACKLIST" ]] || die "--tracklist est obligatoire."
ALBUM_ARG="$1"
[[ -d "$ALBUM_ARG" ]] || die "Dossier introuvable : $ALBUM_ARG"
ALBUM_DIR="$(cd -- "$ALBUM_ARG" && pwd -P)"
BACKUP_DIR="$ALBUM_DIR/backup"

info "Vérification des dépendances"
missing=()
for cmd in cuebreakpoints shnsplit flac sha256sum python3 awk find sort sed basename dirname mktemp mv; do
    command -v "$cmd" >/dev/null 2>&1 || missing+=("$cmd")
done
if ((${#missing[@]})); then
    printf 'Commandes manquantes : %s\n' "${missing[*]}" >&2
    printf 'Sur Ubuntu/WSL, les paquets requis sont généralement : cuetools shntool flac\n' >&2
    exit 1
fi
[[ -f "$NAME_HELPER" ]] || die "Helper introuvable : $NAME_HELPER"

mapfile -d '' FLACS < <(find "$ALBUM_DIR" -maxdepth 1 -type f -iname '*.flac' -print0 | sort -zV)
mapfile -d '' CUES  < <(find "$ALBUM_DIR" -maxdepth 1 -type f -iname '*.cue'  -print0 | sort -zV)
((${#FLACS[@]} == 1)) || die "Un seul FLAC est attendu à la racine ; ${#FLACS[@]} trouvé(s)."
((${#CUES[@]} == 1))  || die "Un seul CUE est attendu à la racine ; ${#CUES[@]} trouvé(s)."
BACKUP_CREATED=0
if [[ -e "$BACKUP_DIR" ]]; then
    [[ -d "$BACKUP_DIR" ]] || die "Le chemin '$BACKUP_DIR' existe mais n'est pas un dossier."
    if [[ -n "$(find "$BACKUP_DIR" -mindepth 1 -maxdepth 1 -print -quit)" ]]; then
        die "Le dossier '$BACKUP_DIR' existe et n'est pas vide."
    fi
fi

FLAC_FILE="${FLACS[0]}"
CUE_FILE="${CUES[0]}"
[[ -f "$TRACKLIST" ]] || die "Tracklist introuvable : $TRACKLIST"
TRACKLIST="$(cd -- "$(dirname -- "$TRACKLIST")" && pwd -P)/$(basename -- "$TRACKLIST")"

TRACK_COUNT="$(awk '{sub(/\r$/, "")} toupper($1)=="TRACK" && toupper($3)=="AUDIO" {n++} END {print n+0}' "$CUE_FILE")"
((TRACK_COUNT >= 2)) || die "Le CUE doit déclarer au moins deux pistes AUDIO ; $TRACK_COUNT trouvée(s)."
TOTAL_TRACK_COUNT="$(awk '{sub(/\r$/, "")} toupper($1)=="TRACK" {n++} END {print n+0}' "$CUE_FILE")"
((TOTAL_TRACK_COUNT == TRACK_COUNT)) || die "Les CUE mixtes AUDIO/DATA ne sont pas pris en charge."

mapfile -t CUE_REFERENCES < <(sed -nE 's/^[[:space:]]*FILE[[:space:]]+"([^"]+)".*/\1/p' "$CUE_FILE")
if ((${#CUE_REFERENCES[@]} > 1)); then
    die "Les CUE multi-fichiers ne sont pas pris en charge."
fi
if ((${#CUE_REFERENCES[@]} == 1)); then
    cue_name="${CUE_REFERENCES[0]%$'\r'}"
    source_name="$(basename -- "$FLAC_FILE")"
    cue_stem="${cue_name%.*}"
    source_stem="${source_name%.*}"
    if [[ "${cue_name,,}" != "${source_name,,}" && "${cue_stem,,}" != "${source_stem,,}" ]]; then
        die "Le CUE référence '$cue_name', mais le FLAC présent est '$source_name'."
    fi
fi

info "Sources détectées"
printf 'FLAC   : %s\n' "$(basename -- "$FLAC_FILE")"
printf 'CUE    : %s\n' "$(basename -- "$CUE_FILE")"
printf 'Pistes : %d\n' "$TRACK_COUNT"
printf 'Titres : %s\n' "$TRACKLIST"

info "Test d'intégrité du FLAC source"
flac -t "$FLAC_FILE"

STAGE_DIR="$(mktemp -d "$ALBUM_DIR/.flac-cue-split.XXXXXXXX")"
TRACK_DIR="$STAGE_DIR/tracks"
BREAKPOINTS_FILE="$STAGE_DIR/breakpoints.txt"
MANIFEST_FILE="$STAGE_DIR/names.nul"
mkdir -- "$TRACK_DIR"

FINALIZING=0
declare -a INSTALLED_TARGETS=()
declare -a INSTALLED_SOURCES=()
declare -a MOVED_ORIGINALS=()
declare -a MOVED_BACKUPS=()

on_exit() {
    status=$?
    trap - EXIT
    if ((status != 0)); then
        if ((FINALIZING)); then
            warn "Échec pendant la finalisation ; tentative de rollback."
            rollback_failed=0
            for ((i=${#INSTALLED_TARGETS[@]}-1; i>=0; i--)); do
                if [[ -e "${INSTALLED_TARGETS[$i]}" && ! -e "${INSTALLED_SOURCES[$i]}" ]]; then
                    mv -- "${INSTALLED_TARGETS[$i]}" "${INSTALLED_SOURCES[$i]}" || rollback_failed=1
                fi
            done
            for ((i=${#MOVED_BACKUPS[@]}-1; i>=0; i--)); do
                if [[ -e "${MOVED_BACKUPS[$i]}" && ! -e "${MOVED_ORIGINALS[$i]}" ]]; then
                    mv -- "${MOVED_BACKUPS[$i]}" "${MOVED_ORIGINALS[$i]}" || rollback_failed=1
                fi
            done
            if ((BACKUP_CREATED)); then
                rmdir -- "$BACKUP_DIR" 2>/dev/null || true
            fi
            ((rollback_failed == 0)) || warn "Rollback incomplet : vérifier manuellement l'album et backup/."
        fi
        warn "Échec. Les fichiers de travail sont conservés dans : $STAGE_DIR"
    fi
    exit "$status"
}
trap on_exit EXIT

python3 "$NAME_HELPER" --cue "$CUE_FILE" --tracklist "$TRACKLIST" > "$MANIFEST_FILE"
mapfile -d '' TARGET_NAMES < "$MANIFEST_FILE"
((${#TARGET_NAMES[@]} == TRACK_COUNT)) || die "Le helper a produit ${#TARGET_NAMES[@]} noms ; $TRACK_COUNT attendus."

info "Noms de pistes prévus"
printf '  %s\n' "${TARGET_NAMES[@]}"
for target_name in "${TARGET_NAMES[@]}"; do
    [[ ! -e "$ALBUM_DIR/$target_name" ]] || die "Le fichier cible existe déjà : $target_name"
done

info "Lecture et validation des points de découpe"
cuebreakpoints --append-gaps "$CUE_FILE" > "$BREAKPOINTS_FILE"
BREAKPOINT_COUNT="$(awk 'NF {n++} END {print n+0}' "$BREAKPOINTS_FILE")"
EXPECTED_BREAKPOINTS=$((TRACK_COUNT - 1))
((BREAKPOINT_COUNT == EXPECTED_BREAKPOINTS)) || \
    die "Le CUE produit $BREAKPOINT_COUNT points ; $EXPECTED_BREAKPOINTS attendus."

info "Découpe FLAC lossless dans le dossier temporaire"
shnsplit -d "$TRACK_DIR" -o flac "$FLAC_FILE" < "$BREAKPOINTS_FILE"
mapfile -d '' TRACKS < <(find "$TRACK_DIR" -maxdepth 1 -type f -iname '*.flac' -print0 | sort -zV)
((${#TRACKS[@]} == TRACK_COUNT)) || \
    die "La découpe a produit ${#TRACKS[@]} pistes ; $TRACK_COUNT attendues."

info "Test d'intégrité de toutes les pistes"
flac -t "${TRACKS[@]}"

hash_pcm_file() {
    local file="$1"
    flac -d -c --force-raw-format --endian=little --sign=signed "$file" 2>/dev/null \
        | sha256sum | awk '{print $1}'
}

hash_pcm_tracks() {
    {
        local file
        for file in "$@"; do
            flac -d -c --force-raw-format --endian=little --sign=signed "$file" 2>/dev/null || exit 1
        done
    } | sha256sum | awk '{print $1}'
}

info "Calcul du SHA-256 du PCM source"
SOURCE_SHA="$(hash_pcm_file "$FLAC_FILE")" || die "Échec du hash PCM source."
printf 'Source PCM SHA-256 : %s\n' "$SOURCE_SHA"

info "Calcul du SHA-256 du PCM des pistes concaténées"
SPLIT_SHA="$(hash_pcm_tracks "${TRACKS[@]}")" || die "Échec du hash PCM des pistes."
printf 'Pistes PCM SHA-256 : %s\n' "$SPLIT_SHA"
[[ "$SOURCE_SHA" == "$SPLIT_SHA" ]] || die "Hash PCM différent : la sortie n'est pas bit-perfect."

declare -a INPUTS=("$FLAC_FILE" "$CUE_FILE")
source_stem="$(basename -- "${FLAC_FILE%.*}")"
cue_stem="$(basename -- "${CUE_FILE%.*}")"
while IFS= read -r -d '' log_file; do
    log_stem="$(basename -- "${log_file%.*}")"
    if [[ "${log_stem,,}" == "${source_stem,,}" || "${log_stem,,}" == "${cue_stem,,}" ]]; then
        INPUTS+=("$log_file")
    fi
done < <(find "$ALBUM_DIR" -maxdepth 1 -type f -iname '*.log' -print0)

for input in "${INPUTS[@]}"; do
    backup_target="$BACKUP_DIR/$(basename -- "$input")"
    [[ ! -e "$backup_target" ]] || die "Collision dans backup : $backup_target"
done

info "Vérifications réussies ; installation transactionnelle du résultat"
FINALIZING=1
if [[ ! -d "$BACKUP_DIR" ]]; then
    mkdir -- "$BACKUP_DIR"
    BACKUP_CREATED=1
fi
for input in "${INPUTS[@]}"; do
    backup_target="$BACKUP_DIR/$(basename -- "$input")"
    mv -- "$input" "$backup_target"
    MOVED_ORIGINALS+=("$input")
    MOVED_BACKUPS+=("$backup_target")
done

for ((i=0; i<TRACK_COUNT; i++)); do
    target="$ALBUM_DIR/${TARGET_NAMES[$i]}"
    mv -- "${TRACKS[$i]}" "$target"
    INSTALLED_SOURCES+=("${TRACKS[$i]}")
    INSTALLED_TARGETS+=("$target")
done
FINALIZING=0

rm -f -- "$BREAKPOINTS_FILE" "$MANIFEST_FILE" || warn "Nettoyage incomplet dans $STAGE_DIR"
rmdir -- "$TRACK_DIR" 2>/dev/null || warn "Dossier temporaire non vide : $TRACK_DIR"
rmdir -- "$STAGE_DIR" 2>/dev/null || warn "Dossier temporaire conservé : $STAGE_DIR"
trap - EXIT

printf '\n============================================================\n'
printf 'SUCCESS\n'
printf 'Source      : %s\n' "$(basename -- "$FLAC_FILE")"
printf 'CUE         : %s\n' "$(basename -- "$CUE_FILE")"
printf 'Pistes      : %d\n' "$TRACK_COUNT"
printf 'Dossier     : %s\n' "$ALBUM_DIR"
printf 'Backup      : %s\n' "$BACKUP_DIR"
printf 'PCM SHA-256 : %s\n' "$SOURCE_SHA"
printf '============================================================\n'
