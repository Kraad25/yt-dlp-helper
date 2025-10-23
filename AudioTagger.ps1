param (
    [string]$jsonFile
)

function Get-CleanTitle {
    param (
        [string]$fileName,
        [string]$artist,
        [string]$album
    )
    
    $baseName = [System.IO.Path]::GetFileNameWithoutExtension($fileName)

    $cleaned = $baseName -replace '\[[^\]]*\]', '' -replace '\([^\)]*\)', ''
    $cleaned = $cleaned.Trim()

    $parts = $cleaned -split '\s*[-|]\s*' | ForEach-Object { $_.Trim() }

    $filtered = @()
    foreach ($p in $parts) {
        if (-not [string]::IsNullOrWhiteSpace($p)) {
            $lower = $p.ToLower()
            $isArtist = $false
            $isAlbum = $false

            if ($artist -and ($lower -eq $artist.ToLower())) { $isArtist = $true }
            if ($album -and ($lower -eq $album.ToLower())) { $isAlbum = $true }

            if (-not ($isArtist -or $isAlbum)) {
                $filtered += $p
            }
        }
    }

    if ($filtered.Count -eq 0) {
        return $cleaned.Trim()
    }

    $cleanTitle = $filtered[0].Trim()
    return $cleanTitle
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

    $process = Start-Process -FilePath 'ffmpeg' -ArgumentList $arguments -NoNewWindow -Wait -PassThru

    if ($process.ExitCode -eq 0) {
        Move-Item -Force -Path $tempFile -Destination $filePath
        Write-Host "Metadata updated: $([System.IO.Path]::GetFileName($filePath))"
    }
    else {
        Write-Warning "ffmpeg failed to update: $filePath"
        if (Test-Path $tempFile) { Remove-Item $tempFile -Force }
    }
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
