function issue(message) {
    print message > "/dev/stderr"
    invalid = 1
}

function finish_track() {
    if (have_audio_track && index01_count != 1) {
        issue("Piste " track_label " : " index01_count " INDEX 01 trouvé(s), 1 attendu.")
    }
}

function extract_file_reference(source_line, line, closing_quote, fields) {
    line = source_line
    sub(/^[[:space:]]*[^[:space:]]+[[:space:]]+/, "", line)

    if (substr(line, 1, 1) == "\"") {
        line = substr(line, 2)
        closing_quote = index(line, "\"")
        if (closing_quote == 0) {
            return ""
        }
        return substr(line, 1, closing_quote - 1)
    }

    split(line, fields, /[[:space:]]+/)
    return fields[1]
}

{
    sub(/\r$/, "")
    keyword = toupper($1)

    if (keyword == "FILE") {
        file_count++
        parsed_reference = (NF >= 2) ? extract_file_reference($0) : ""
        if (parsed_reference == "") {
            issue("Déclaration FILE invalide ou vide.")
        } else if (file_count == 1) {
            file_reference = parsed_reference
        }
    }

    if (keyword == "TRACK") {
        finish_track()
        total_track_count++
        have_audio_track = 0

        if (toupper($3) != "AUDIO") {
            next
        }

        audio_track_count++
        track_label = $2
        index01_count = 0

        if ($2 !~ /^[0-9]+$/) {
            issue("Numéro de piste AUDIO invalide : " $2)
        } else if (($2 + 0) != audio_track_count) {
            issue("Piste AUDIO " $2 " : numéro " audio_track_count " attendu.")
        }

        have_audio_track = 1
        next
    }

    if (keyword == "INDEX" && have_audio_track && $2 == "01") {
        index01_count++
        position = $3

        if (position !~ /^[0-9]+:[0-5][0-9]:[0-7][0-9]$/) {
            issue("Piste " track_label " : INDEX 01 invalide : " position)
            next
        }

        split(position, parts, ":")
        sectors = ((parts[1] * 60 + parts[2]) * 75) + parts[3]
        if (have_previous_index && sectors <= previous_sectors) {
            issue("Piste " track_label " : INDEX 01 non strictement croissant.")
        }
        previous_sectors = sectors
        have_previous_index = 1
    }
}

END {
    finish_track()

    if (audio_track_count < 2) {
        issue("Le CUE doit déclarer au moins deux pistes AUDIO ; " audio_track_count " trouvée(s).")
    }
    if (total_track_count != audio_track_count) {
        issue("Les CUE mixtes AUDIO/DATA ne sont pas pris en charge.")
    }
    if (file_count != 1) {
        issue("Le CUE doit contenir exactement une déclaration FILE ; " file_count " trouvée(s).")
    }

    if (invalid) {
        exit 1
    }

    print audio_track_count
    print file_reference
}
