[CmdletBinding()]
param(
    [Parameter(Mandatory = $true, Position = 0)]
    [string] $AlbumPath,

    [Parameter(Mandatory = $true)]
    [ValidateNotNullOrEmpty()]
    [string] $FilenamesPath,

    [string] $Distro = 'Ubuntu-24.04'
)

$ErrorActionPreference = 'Stop'

function Convert-ToWslPath {
    param(
        [Parameter(Mandatory = $true)]
        [string] $LiteralPath,

        [Parameter(Mandatory = $true)]
        [string] $Distribution
    )

    $resolved = (Resolve-Path -LiteralPath $LiteralPath).ProviderPath
    $uncPattern = '^\\\\wsl(?:\.localhost|\$)\\(?<distro>[^\\]+)\\(?<rest>.*)$'
    if ($resolved -match $uncPattern) {
        if ($Matches.distro -ne $Distribution) {
            throw "Le chemin appartient à '$($Matches.distro)', pas à '$Distribution'."
        }
        return '/' + ($Matches.rest -replace '\\', '/')
    }

    $converted = & wsl.exe --distribution $Distribution --exec wslpath -a -u $resolved
    if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($converted)) {
        throw "Impossible de convertir le chemin Windows pour WSL : $resolved"
    }
    return $converted.Trim()
}

$bashScript = Join-Path -Path $PSScriptRoot -ChildPath 'split_flac_cue.sh'
$wslScript = Convert-ToWslPath -LiteralPath $bashScript -Distribution $Distro
$wslAlbum = Convert-ToWslPath -LiteralPath $AlbumPath -Distribution $Distro

$wslFilenames = Convert-ToWslPath -LiteralPath $FilenamesPath -Distribution $Distro
$wslArguments = @(
    '--distribution', $Distro,
    '--exec', 'bash', $wslScript,
    '--filenames', $wslFilenames,
    $wslAlbum
)

& wsl.exe @wslArguments
if ($LASTEXITCODE -ne 0) {
    throw "La découpe FLAC/CUE a échoué (code $LASTEXITCODE)."
}
