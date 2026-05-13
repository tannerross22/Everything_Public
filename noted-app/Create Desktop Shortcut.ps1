$appDir   = $PSScriptRoot
$vbsPath  = Join-Path $appDir "start-noted.vbs"
$desktop  = [System.Environment]::GetFolderPath("Desktop")
$lnkPath  = Join-Path $desktop "Noted.lnk"

$shell     = New-Object -ComObject WScript.Shell
$shortcut  = $shell.CreateShortcut($lnkPath)

$shortcut.TargetPath       = "wscript.exe"
$shortcut.Arguments        = """$vbsPath"""
$shortcut.WorkingDirectory = $appDir
$shortcut.Description      = "Launch Noted"

# Use the Electron binary as the icon if node_modules are present
$electronExe = Join-Path $appDir "node_modules\electron\dist\electron.exe"
if (Test-Path $electronExe) {
    $shortcut.IconLocation = "$electronExe,0"
}

$shortcut.Save()
Write-Host "Shortcut created: $lnkPath" -ForegroundColor Green
