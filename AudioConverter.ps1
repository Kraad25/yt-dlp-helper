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

    $arguments = @(
        "-i", "-t", "mp3",
        "--add-metadata",
        "--no-warnings", "--quiet",
        "-o", "$outDir\%(title)s.%(ext)s"
    )
    $arguments += $url
    $arg2 ="--extractor-args", "youtube:player_js_version=actual"
    $arg3 = "--extractor-args", "youtube:player_client=default,web_safari;player_js_version=actual"

    if(-not(Start-RunYtDlp($arguments))){
        Write-Error "Base argument did not execute successfully, trying next arguments!"
        $arguments += $arg2
        if(-not(Start-RunYtDlp($arguments))){
            Write-Error "Argument set 2 did not execute successfully, trying next arguments!"
            $arguments = $arguments | Where-Object { $arg2 -notcontains $_ }
            $arguments += $arg3
            if(-not(Start-RunYtDlp($arguments))){
                Write-Error "Close it and go home nothing working!"
            }
        }
    }
}
