param (
    [string]$jsonFile
)

function Confirm-Directory {
    param([string]$path)
    if (-not (Test-Path $path)) {
        New-Item -ItemType Directory -Path $path | Out-Null
    }
}


function Get-YtDlpPath {
    try {
        & yt-dlp --version > $null 2>&1
        return "yt-dlp"
    } catch {
        $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
        $localYt = Join-Path $scriptDir "yt-dlp.exe"

        if (Test-Path $localYt) { return $localYt }
        throw "yt-dlp not found in PATH or local directory."
    }
}

function Start-RunYtDlp {
    param(
        [string[]]$arguments
    )
        try {
            & yt-dlp @arguments
            return $LASTEXITCODE -eq 0
        } catch {
            return $false
        }
    }


function Start-AudioConverter {
    param (
        [string]$url,
        [string]$outDir
    )

    $baseArgument = @(
        "-i", "-t", "mp3",
        "--add-metadata",
        "--no-warnings", "--quiet",
        "-o", "$outDir\%(title)s.%(ext)s"
    )
    $baseArgument += $url

    $retryStages = @(
        @{Name = "PlayerJSVersion"; Args = $baseArgument + @("--extractor-args", "youtube:player_js_version=actual")},
        @{Name = "PlayerClientAndJSVersion"; Args = $baseArgument + @("--extractor-args", "youtube:player_client=default,web_safari;player_js_version=actual")},
        @{Name = "Base"; Args = $baseArgument}
    )

    foreach ($stage in $retryStages) {
        Write-Host "Attempting stage: $($stage.Name)"
        if (Start-RunYtDlp -arguments $stage.Args) {
            Write-Host "Stage $($stage.Name) succeeded."
            return
        } else {
            Write-Warning "Stage $($stage.Name) failed."
        }
    }

    Write-Warning "All stages failed. Unable to download audio."
}




if (-not (Test-Path $jsonFile)) {
    Write-Warning "JSON input file not found: $jsonFile"
    exit 1
}

$jsonContent = Get-Content $jsonFile -Raw | ConvertFrom-Json

$url = $jsonContent.Url
$outDir = $jsonContent.FolderName

Confirm-Directory -path $outDir
Start-AudioConverter -url $url -outDir $outDir