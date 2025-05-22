Import-Module PnP.PowerShell

# Config
$sourceFolder = "D:\salesforcedownload_code\salesforce_document_folder_downloads\SalesForceProjectsDownload_2025-05-12_09-08"
# $siteUrl = ""https://lendlease.sharepoint.com/sites/BAULD_TEST""
$siteUrl = "https://lendlease.sharepoint.com/sites/ProjectProteus"
$libraryName = "Shared Documents"

$spRootFolder = "$libraryName/ani_salesforce_uplaod_demo"

$timestampTag = Get-Date -Format "yyyy-MM-dd_HHmm"
$uploadLogPath = "upload_log_$timestampTag.txt"
$errorLogPath  = "error_log_$timestampTag.txt"




# Start timer
$startTime = Get-Date
$totalSize = 0

# Connect to SharePoint
Connect-PnPOnline -Url $siteUrl -Interactive -ClientId "a907eb35-5fdd-41ea-8666-dd45affa1944"

# Get all files recursively
$Files = Get-ChildItem -Path $sourceFolder -Recurse -File

foreach ($File in $Files) {
    try {
        $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        $relativePath = $File.FullName.Substring($sourceFolder.Length).TrimStart('\')
        $relativeFolder = Split-Path $relativePath -Parent

        if ([string]::IsNullOrEmpty($relativeFolder)) {
            $spFolderPath = $spRootFolder
        } else {
            $spFolderPath = "$spRootFolder/$relativeFolder" -replace '\\','/'
        }

        Write-Host "Uploading $($File.Name) to $spFolderPath"
        Add-PnPFile -Path $File.FullName -Folder $spFolderPath



        # Track uploaded file size
        $totalSize += $File.Length

        # Log success with timestamp
        "[$timestamp] File uploaded: $($File.FullName) to $spFolderPath" | Out-File -Append -FilePath $uploadLogPath
    }
    catch {
        $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        $errorMessage = "[$timestamp] ERROR: Failed to upload $($File.FullName) - $($_.Exception.Message)"
        Write-Host $errorMessage -ForegroundColor Red
        $errorMessage | Out-File -Append -FilePath $errorLogPath
    }
}

# End timer
$endTime = Get-Date
$duration = $endTime - $startTime

# Size conversions
$sizeMB = [math]::Round($totalSize / 1MB, 2)
$sizeGB = [math]::Round($totalSize / 1GB, 2)

# Output summary
Write-Host "`nUpload completed in $($duration.TotalMinutes.ToString("0.00")) minutes ($duration)." -ForegroundColor Cyan
Write-Host "Total uploaded size: $sizeMB MB ($sizeGB GB)" -ForegroundColor Cyan

# Log summary with timestamp
$summaryTimestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
@"
======== Summary ========
[$summaryTimestamp]
Completed at: $endTime
Duration     : $duration
Total Size   : $sizeMB MB ($sizeGB GB)
"@ | Out-File -Append -FilePath $uploadLogPath
