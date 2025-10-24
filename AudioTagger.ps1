param (
    [string]$jsonFile
)

function Remove-BracketedContent {
    param([string]$Text)
    if (-not $Text) { return $null }

    $Text -replace '\[[^\]]*\]', '' -replace '\([^\)]*\)', '' | ForEach-Object { $_.Trim() }
}

function Split-TitleByParts {
    param([string]$Title)
    if (-not $Title) { return @() } 

    # Split by dash or pipe and trim whitespace
    return ($Title -split '\s*[-|]\s*' | Where-Object { -not [string]::IsNullOrWhiteSpace($_) })
}

function Remove-NamePart {
    param(
        [string]$Part,
        [string]$NameToRemove
    )
    if (-not $NameToRemove) { return $Part }

    # Case-insensitive exact match
    if ($Part.Trim().ToLower() -eq $NameToRemove.Trim().ToLower()) {
        return $null
    }

    return $Part
}

function Start-FFmpegProcess {
    param([string[]]$Arguments)

    $process = Start-Process -FilePath 'ffmpeg' -ArgumentList $Arguments `
        -NoNewWindow -Wait -PassThru

    return $process
}

function Use-FFmpegResult {
    param(
        [System.Diagnostics.Process]$Process,
        [string]$TempFile,
        [string]$OriginalFile
    )

    if ($Process.ExitCode -eq 0) {
        Move-Item -Force -Path $TempFile -Destination $OriginalFile
        Write-Host "Metadata updated: $([System.IO.Path]::GetFileName($OriginalFile))"
    }
    else {
        Write-Warning "ffmpeg failed for: $OriginalFile (exit code $($Process.ExitCode))"
        if (Test-Path $TempFile) { Remove-Item $TempFile -Force }
    }
}

function Get-CleanTitle {
    param (
        [string]$fileName,
        [string]$artist,
        [string]$album
    )
    
    $baseName = [System.IO.Path]::GetFileNameWithoutExtension($fileName)

    $cleanName = Remove-BracketedContent -Text $baseName
    $parts = Split-TitleByParts -Title $cleanName
    $filteredParts = foreach ($part in $parts) {
        $p = Remove-NamePart $part $Artist
        $p = Remove-NamePart $p $Album
        if ($p) { $p }  # keep non-empty parts
    }

    if (-not $filteredParts -or $filteredParts.Count -eq 0) {
        return $cleanName.Trim()
    }
    return ($filteredParts -join ' - ').Trim()
}

function Update-Metadata {
    param (
        [string]$filePath,
        [string]$title,
        [string]$artist,
        [string]$album
    )

    $tempFile = [System.IO.Path]::ChangeExtension($filePath, ".tmp.mp3")

    $metaArgs = @()
    if ($title)  { $metaArgs += '-metadata'; $metaArgs += "title=`"$title`"" }
    if ($artist) { $metaArgs += '-metadata'; $metaArgs += "artist=`"$artist`"" }
    if ($album)  { $metaArgs += '-metadata'; $metaArgs += "album=`"$album`"" }

    $arguments = @('-i', "`"$filePath`"", '-y', '-id3v2_version', '3', '-write_id3v1', '1') + $metaArgs + @('-codec', 'copy', "`"$tempFile`"")

    $process =Start-FFmpegProcess -Arguments $arguments
    Use-FFmpegResult -Process $process -TempFile $tempFile -OriginalFile $filePath
}



if (-not (Test-Path $jsonFile)) {
    Write-Error "JSON input file not found: $jsonFile"
    exit 1
}

$jsonContent = Get-Content $jsonFile -Raw | ConvertFrom-Json
$outDir = $jsonContent.FolderName
$artist = $jsonContent.Artist
$album = $jsonContent.Album

if (-not (Test-Path $outDir)) {
    Write-Error "Target folder not found: $outDir"
    exit 1
}

$mp3Files = Get-ChildItem -Path $outDir -Filter "*.mp3" -File
if ($mp3Files.Count -eq 0) {
    Write-Warning "No MP3 files found in $outDir"
    exit 0
}

foreach ($file in $mp3Files) {
    $cleanTitle = Get-CleanTitle -fileName $file.Name -artist $artist -album $album

    if ($artist) {
        $songName = "$cleanTitle - $artist"
    }
    elseif ($album) {
        $songName = "$cleanTitle - $album"
    }
    else {
        $songName = $cleanTitle
    }

    Write-Host "Processing: $($file.Name)"
    Write-Host " → Title: $cleanTitle"
    Write-Host " → Artist: $artist"
    Write-Host " → Album: $album"
    Write-Host " → Song Name: $songName"

    Update-Metadata -filePath $file.FullName -title $cleanTitle -artist $artist -album $album

    $newPath = Join-Path $file.DirectoryName "$songName.mp3"
    if ($file.FullName -ne $newPath) {
        try {
            Rename-Item -Path $file.FullName -NewName "$songName.mp3" -ErrorAction Stop
            Write-Host "Renamed → $songName.mp3"
        }
        catch {
            Write-Warning "Could not rename: $($file.Name)"
        }
    }
}

Write-Host "Tagging complete via ffmpeg!"
