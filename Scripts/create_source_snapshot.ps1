param(
    [string]$OutputPath = "docs/SOURCE_SNAPSHOT.sha256.csv"
)

$ErrorActionPreference = "Stop"
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$roots = @("Art", "Mat", "Scripts", "AssetsDatabase", "Content", "Config", "CozySettlement.uproject")
$rows = foreach ($entry in $roots) {
    $candidate = Join-Path $repoRoot $entry
    if (Test-Path -LiteralPath $candidate -PathType Leaf) {
        $file = Get-Item -LiteralPath $candidate
        [PSCustomObject]@{
            Path = $entry.Replace("\\", "/")
            Bytes = $file.Length
            SHA256 = (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash
        }
        continue
    }

    Get-ChildItem -LiteralPath $candidate -Recurse -File | ForEach-Object {
        [PSCustomObject]@{
            Path = $_.FullName.Substring($repoRoot.Length + 1).Replace("\\", "/")
            Bytes = $_.Length
            SHA256 = (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash
        }
    }
}

$destination = Join-Path $repoRoot $OutputPath
$destinationDirectory = Split-Path -Parent $destination
New-Item -ItemType Directory -Path $destinationDirectory -Force | Out-Null
$rows | Sort-Object Path | Export-Csv -LiteralPath $destination -NoTypeInformation -Encoding utf8

$totalBytes = ($rows | Measure-Object -Property Bytes -Sum).Sum
Write-Host "SOURCE_SNAPSHOT files=$($rows.Count) bytes=$totalBytes path=$destination"
