#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
readonly SCRIPT_DIR
readonly FILENAME_VALIDATOR="$SCRIPT_DIR/validate_track_filenames.py"
readonly CUE_INSPECTOR="$SCRIPT_DIR/inspect_cue.awk"

FILENAMES_FILE=""
ALBUM_DIR=""
BACKUP_DIR=""
FLAC_FILE=""
CUE_FILE=""
TRACK_COUNT=0
STAGE_DIR=""
TRACK_DIR=""
BREAKPOINTS_FILE=""
SOURCE_SHA=""
SPLIT_SHA=""
FINALIZING=0
BACKUP_CREATED=0

declare -a TARGET_NAMES=()
declare -a TRACKS=()
declare -a INPUTS=()
declare -a INSTALLED_TARGETS=()
declare -a INSTALLED_SOURCES=()
declare -a MOVED_ORIGINALS=()
declare -a MOVED_BACKUPS=()

# ---------------------------------------------------------------------------
# Interface et préparation
# ---------------------------------------------------------------------------

info() { printf '\n==> %s\n' "$*"; }
warn() { printf '\nAVERTISSEMENT: %s\n' "$*" >&2; }
die()  { printf '\nERREUR: %s\n' "$*" >&2; exit 1; }

usage() {
    cat <<'EOF'
Usage: split_flac_cue.sh --filenames FICHIER DOSSIER_ALBUM

Découpe l'unique FLAC selon l'unique CUE, vérifie le PCM bit-perfect,
installe les pistes à la racine et déplace les sources dans backup/.
EOF
}

parse_arguments() {
    while (($#)); do
        case "$1" in
            --filenames)
                (($# >= 2)) || die "--filenames requiert un chemin."
                FILENAMES_FILE="$2"
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
    [[ -n "$FILENAMES_FILE" ]] || die "--filenames est obligatoire."
    [[ -d "$1" ]] || die "Dossier introuvable : $1"

    ALBUM_DIR="$(cd -- "$1" && pwd -P)"
    BACKUP_DIR="$ALBUM_DIR/backup"
}

check_dependencies() {
    info "Vérification des dépendances"

    local -a missing=()
    local command_name
    for command_name in cuebreakpoints shnsplit flac sha256sum python3 awk find sort \
        basename dirname mktemp mv rm mkdir rmdir; do
        command -v "$command_name" >/dev/null 2>&1 || missing+=("$command_name")
    done

    if ((${#missing[@]})); then
        printf 'Commandes manquantes : %s\n' "${missing[*]}" >&2
        printf 'Sur Ubuntu/WSL, les paquets requis sont généralement : cuetools shntool flac\n' >&2
        exit 1
    fi

    [[ -f "$FILENAME_VALIDATOR" ]] || die "Validateur introuvable : $FILENAME_VALIDATOR"
    [[ -f "$CUE_INSPECTOR" ]] || die "Inspecteur CUE introuvable : $CUE_INSPECTOR"
}

discover_sources() {
    local -a flacs=()
    local -a cues=()

    mapfile -d '' flacs < <(
        find "$ALBUM_DIR" -maxdepth 1 -type f -iname '*.flac' -print0 | sort -zV
    )
    mapfile -d '' cues < <(
        find "$ALBUM_DIR" -maxdepth 1 -type f -iname '*.cue' -print0 | sort -zV
    )

    ((${#flacs[@]} == 1)) || \
        die "Un seul FLAC est attendu à la racine ; ${#flacs[@]} trouvé(s)."
    ((${#cues[@]} == 1)) || \
        die "Un seul CUE est attendu à la racine ; ${#cues[@]} trouvé(s)."

    FLAC_FILE="${flacs[0]}"
    CUE_FILE="${cues[0]}"
}

validate_backup() {
    [[ -e "$BACKUP_DIR" ]] || return 0
    [[ -d "$BACKUP_DIR" ]] || \
        die "Le chemin '$BACKUP_DIR' existe mais n'est pas un dossier."

    if [[ -n "$(find "$BACKUP_DIR" -mindepth 1 -maxdepth 1 -print -quit)" ]]; then
        die "Le dossier '$BACKUP_DIR' existe et n'est pas vide."
    fi
}

resolve_filename_manifest() {
    [[ -f "$FILENAMES_FILE" ]] || \
        die "Manifeste de noms introuvable : $FILENAMES_FILE"
    FILENAMES_FILE="$(cd -- "$(dirname -- "$FILENAMES_FILE")" && pwd -P)/$(basename -- "$FILENAMES_FILE")"
}

# ---------------------------------------------------------------------------
# Validation préalable
# ---------------------------------------------------------------------------

inspect_cue() {
    local inspection
    local -a cue_data=()
    local cue_name source_name cue_stem source_stem

    if ! inspection="$(awk -f "$CUE_INSPECTOR" "$CUE_FILE")"; then
        die "La structure technique du CUE est invalide."
    fi

    mapfile -t cue_data <<< "$inspection"
    ((${#cue_data[@]} == 2)) || die "Sortie inattendue de l'inspecteur CUE."
    [[ "${cue_data[0]}" =~ ^[0-9]+$ ]] || die "Nombre de pistes CUE invalide."

    TRACK_COUNT="${cue_data[0]}"
    cue_name="${cue_data[1]}"
    source_name="$(basename -- "$FLAC_FILE")"
    cue_stem="${cue_name%.*}"
    source_stem="${source_name%.*}"

    if [[ "${cue_name,,}" != "${source_name,,}" && \
          "${cue_stem,,}" != "${source_stem,,}" ]]; then
        die "Le CUE référence '$cue_name', mais le FLAC présent est '$source_name'."
    fi
}

validate_filename_manifest() {
    local validated_names_file
    validated_names_file="$(mktemp)"

    if ! python3 "$FILENAME_VALIDATOR" \
        --filenames "$FILENAMES_FILE" \
        --expected-count "$TRACK_COUNT" \
        --format nul > "$validated_names_file"; then
        rm -f -- "$validated_names_file"
        die "Le manifeste de noms de fichiers est invalide."
    fi

    mapfile -d '' TARGET_NAMES < "$validated_names_file"
    rm -f -- "$validated_names_file"
    ((${#TARGET_NAMES[@]} == TRACK_COUNT)) || \
        die "Le validateur a produit ${#TARGET_NAMES[@]} noms ; $TRACK_COUNT attendus."
}

print_detected_sources() {
    info "Sources détectées"
    printf 'FLAC   : %s\n' "$(basename -- "$FLAC_FILE")"
    printf 'CUE    : %s\n' "$(basename -- "$CUE_FILE")"
    printf 'Pistes : %d\n' "$TRACK_COUNT"
    printf 'Noms   : %s\n' "$FILENAMES_FILE"
}

check_target_collisions() {
    info "Noms de pistes validés"
    printf '  %s\n' "${TARGET_NAMES[@]}"

    local target_name
    for target_name in "${TARGET_NAMES[@]}"; do
        [[ ! -e "$ALBUM_DIR/$target_name" ]] || \
            die "Le fichier cible existe déjà : $target_name"
    done
}

verify_source_flac() {
    info "Test d'intégrité du FLAC source"
    flac -t "$FLAC_FILE"
}

# ---------------------------------------------------------------------------
# Découpe et vérifications audio
# ---------------------------------------------------------------------------

create_staging_area() {
    STAGE_DIR="$(mktemp -d "$ALBUM_DIR/.flac-cue-split.XXXXXXXX")"
    TRACK_DIR="$STAGE_DIR/tracks"
    BREAKPOINTS_FILE="$STAGE_DIR/breakpoints.txt"
    trap on_exit EXIT
    mkdir -- "$TRACK_DIR"
}

generate_breakpoints() {
    info "Lecture et validation des points de découpe"
    cuebreakpoints --append-gaps "$CUE_FILE" > "$BREAKPOINTS_FILE"

    local breakpoint_count expected_breakpoints
    breakpoint_count="$(awk 'NF {n++} END {print n+0}' "$BREAKPOINTS_FILE")"
    expected_breakpoints=$((TRACK_COUNT - 1))
    ((breakpoint_count == expected_breakpoints)) || \
        die "Le CUE produit $breakpoint_count points ; $expected_breakpoints attendus."
}

split_audio() {
    info "Découpe FLAC lossless dans le dossier temporaire"
    shnsplit -d "$TRACK_DIR" -o flac "$FLAC_FILE" < "$BREAKPOINTS_FILE"

    mapfile -d '' TRACKS < <(
        find "$TRACK_DIR" -maxdepth 1 -type f -iname '*.flac' -print0 | sort -zV
    )
    ((${#TRACKS[@]} == TRACK_COUNT)) || \
        die "La découpe a produit ${#TRACKS[@]} pistes ; $TRACK_COUNT attendues."
}

verify_split_tracks() {
    info "Test d'intégrité de toutes les pistes"
    flac -t "${TRACKS[@]}"
}

hash_pcm_file() {
    local file="$1"
    flac -d -c --force-raw-format --endian=little --sign=signed "$file" 2>/dev/null \
        | sha256sum | awk '{print $1}'
}

hash_pcm_tracks() {
    {
        local file
        for file in "$@"; do
            flac -d -c --force-raw-format --endian=little --sign=signed "$file" \
                2>/dev/null || exit 1
        done
    } | sha256sum | awk '{print $1}'
}

verify_pcm_identity() {
    info "Calcul du SHA-256 du PCM source"
    SOURCE_SHA="$(hash_pcm_file "$FLAC_FILE")" || die "Échec du hash PCM source."
    printf 'Source PCM SHA-256 : %s\n' "$SOURCE_SHA"

    info "Calcul du SHA-256 du PCM des pistes concaténées"
    SPLIT_SHA="$(hash_pcm_tracks "${TRACKS[@]}")" || die "Échec du hash PCM des pistes."
    printf 'Pistes PCM SHA-256 : %s\n' "$SPLIT_SHA"

    [[ "$SOURCE_SHA" == "$SPLIT_SHA" ]] || \
        die "Hash PCM différent : la sortie n'est pas bit-perfect."
}

# ---------------------------------------------------------------------------
# Transaction finale et rollback
# ---------------------------------------------------------------------------

collect_backup_inputs() {
    INPUTS=("$FLAC_FILE" "$CUE_FILE")

    local source_stem cue_stem log_file log_stem
    source_stem="$(basename -- "${FLAC_FILE%.*}")"
    cue_stem="$(basename -- "${CUE_FILE%.*}")"

    while IFS= read -r -d '' log_file; do
        log_stem="$(basename -- "${log_file%.*}")"
        if [[ "${log_stem,,}" == "${source_stem,,}" || \
              "${log_stem,,}" == "${cue_stem,,}" ]]; then
            INPUTS+=("$log_file")
        fi
    done < <(find "$ALBUM_DIR" -maxdepth 1 -type f -iname '*.log' -print0)
}

check_backup_collisions() {
    local input backup_target
    for input in "${INPUTS[@]}"; do
        backup_target="$BACKUP_DIR/$(basename -- "$input")"
        [[ ! -e "$backup_target" ]] || die "Collision dans backup : $backup_target"
    done
}

rollback_installed_tracks() {
    local failed=0
    local i
    for ((i=${#INSTALLED_TARGETS[@]} - 1; i >= 0; i--)); do
        if [[ -e "${INSTALLED_TARGETS[$i]}" && ! -e "${INSTALLED_SOURCES[$i]}" ]]; then
            mv -- "${INSTALLED_TARGETS[$i]}" "${INSTALLED_SOURCES[$i]}" || failed=1
        fi
    done
    return "$failed"
}

rollback_backup_sources() {
    local failed=0
    local i
    for ((i=${#MOVED_BACKUPS[@]} - 1; i >= 0; i--)); do
        if [[ -e "${MOVED_BACKUPS[$i]}" && ! -e "${MOVED_ORIGINALS[$i]}" ]]; then
            mv -- "${MOVED_BACKUPS[$i]}" "${MOVED_ORIGINALS[$i]}" || failed=1
        fi
    done
    return "$failed"
}

on_exit() {
    local status=$?
    local rollback_failed=0
    trap - EXIT

    if ((status != 0)); then
        if ((FINALIZING)); then
            warn "Échec pendant la finalisation ; tentative de rollback."
            rollback_installed_tracks || rollback_failed=1
            rollback_backup_sources || rollback_failed=1

            if ((BACKUP_CREATED)); then
                rmdir -- "$BACKUP_DIR" 2>/dev/null || true
            fi
            ((rollback_failed == 0)) || \
                warn "Rollback incomplet : vérifier manuellement l'album et backup/."
        fi
        warn "Échec. Les fichiers de travail sont conservés dans : $STAGE_DIR"
    fi

    exit "$status"
}

finalize_transaction() {
    info "Vérifications réussies ; installation transactionnelle du résultat"
    FINALIZING=1

    if [[ ! -d "$BACKUP_DIR" ]]; then
        mkdir -- "$BACKUP_DIR"
        BACKUP_CREATED=1
    fi

    local input backup_target target i
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
}

cleanup_staging() {
    rm -f -- "$BREAKPOINTS_FILE" || warn "Nettoyage incomplet dans $STAGE_DIR"
    rmdir -- "$TRACK_DIR" 2>/dev/null || warn "Dossier temporaire non vide : $TRACK_DIR"
    rmdir -- "$STAGE_DIR" 2>/dev/null || warn "Dossier temporaire conservé : $STAGE_DIR"
    trap - EXIT
}

print_summary() {
    printf '\n============================================================\n'
    printf 'SUCCESS\n'
    printf 'Source      : %s\n' "$(basename -- "$FLAC_FILE")"
    printf 'CUE         : %s\n' "$(basename -- "$CUE_FILE")"
    printf 'Pistes      : %d\n' "$TRACK_COUNT"
    printf 'Dossier     : %s\n' "$ALBUM_DIR"
    printf 'Backup      : %s\n' "$BACKUP_DIR"
    printf 'PCM SHA-256 : %s\n' "$SOURCE_SHA"
    printf '============================================================\n'
}

# ---------------------------------------------------------------------------
# Déroulement principal
# ---------------------------------------------------------------------------

main() {
    parse_arguments "$@"
    check_dependencies
    discover_sources
    validate_backup
    resolve_filename_manifest

    inspect_cue
    validate_filename_manifest
    print_detected_sources
    check_target_collisions
    verify_source_flac

    create_staging_area
    generate_breakpoints
    split_audio
    verify_split_tracks
    verify_pcm_identity

    collect_backup_inputs
    check_backup_collisions
    finalize_transaction
    cleanup_staging
    print_summary
}

main "$@"
